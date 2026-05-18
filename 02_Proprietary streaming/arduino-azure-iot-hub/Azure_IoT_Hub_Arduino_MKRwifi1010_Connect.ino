// Copyright (c) Microsoft Corporation. All rights reserved.
// SPDX-License-Identifier: MIT
//
// Adapted by Luca Fontanella for an Arduino MKR WiFi 1010 + DHT22
// research prototype connecting environmental sensor data to Azure IoT Hub.

/*
  Arduino MKR WiFi 1010 + DHT22 + Azure IoT Hub telemetry example.

  This sketch reads temperature and relative humidity values from a DHT22 sensor
  and sends them as telemetry to Azure IoT Hub.

  Research context:
  This file is part of a proprietary IoT streaming workflow used to test
  device-to-cloud telemetry transmission and subsequent visualization through
  Azure Stream Analytics, Power BI and Autodesk Tandem.

  Important:
  - Do not commit the real iot_configs.h file.
  - Use iot_configs.example.h as a template and create your own local iot_configs.h.
*/

/*--- Libraries ---*/

// Sensor libraries
#include <DHT.h>
#include <DHT_U.h>
#include <math.h>

// C99 libraries
#include <cstdbool>
#include <cstdlib>
#include <cstring>
#include <time.h>

// Libraries for SSL client, MQTT client, and WiFi connection
#include <ArduinoBearSSL.h>
#include <ArduinoMqttClient.h>
#include <WiFiNINA.h>

// Library for SAS token generation
#include <ECCX08.h>

// Azure IoT SDK for C includes
#include <az_core.h>
#include <az_iot.h>

// Local configuration file.
// This file must contain Wi-Fi and Azure IoT Hub credentials.
// Do not commit the real iot_configs.h file to GitHub.
#include "iot_configs.h"

// Logging utility
#include "SerialLogger.h"

/*--- Sensor configuration ---*/

#define DHTPIN 7
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

float temperature;
float humidity;

/*--- Macros ---*/

#define BUFFER_LENGTH_MQTT_CLIENT_ID 256
#define BUFFER_LENGTH_MQTT_PASSWORD 256
#define BUFFER_LENGTH_MQTT_TOPIC 128
#define BUFFER_LENGTH_MQTT_USERNAME 512
#define BUFFER_LENGTH_SAS 32
#define BUFFER_LENGTH_SAS_ENCODED_SIGNED_SIGNATURE 64
#define BUFFER_LENGTH_SAS_SIGNATURE 512
#define BUFFER_LENGTH_DATETIME_STRING 256

#define LED_PIN 2

// Time and time zone
#define SECS_PER_MIN 60
#define SECS_PER_HOUR (SECS_PER_MIN * 60)

#define GMT_OFFSET_SECS (IOT_CONFIG_DAYLIGHT_SAVINGS ? \
                        ((IOT_CONFIG_TIME_ZONE + IOT_CONFIG_TIME_ZONE_DAYLIGHT_SAVINGS_DIFF) * SECS_PER_HOUR) : \
                        (IOT_CONFIG_TIME_ZONE * SECS_PER_HOUR))

// Exit into infinite loop if an error occurs
#define EXIT_LOOP(condition, errorMessage) \
  do { \
    if (condition) { \
      Logger.Error(errorMessage); \
      while (1); \
    } \
  } while (0)

/*--- Static variables ---*/

// Clients for Wi-Fi connection, SSL, MQTT, and Azure IoT SDK for C
static WiFiClient wiFiClient;
static BearSSLClient bearSSLClient(wiFiClient);
static MqttClient mqttClient(bearSSLClient);
static az_iot_hub_client azIoTHubClient;

// MQTT variables
static char mqttClientId[BUFFER_LENGTH_MQTT_CLIENT_ID];
static char mqttUsername[BUFFER_LENGTH_MQTT_USERNAME];
static char mqttPassword[BUFFER_LENGTH_MQTT_PASSWORD];

// Telemetry variables
static char telemetryTopic[BUFFER_LENGTH_MQTT_TOPIC];
static unsigned long telemetryNextSendTimeMs;
static String telemetryPayload;

/*--- Function declarations ---*/

// Initialization and connection functions
void connectToWiFi();
void initializeAzureIoTHubClient();
void initializeMQTTClient();
void connectMQTTClientToAzureIoTHub();

// Telemetry and message-callback functions
void onMessageReceived(int messageSize);
static void sendTelemetry();
static const char* generateTelemetry();

// SAS token related functions
static void generateMQTTPassword();
static void generateSASBase64EncodedSignedSignature(
    uint8_t const* sasSignature,
    size_t const sasSignatureSize,
    uint8_t* encodedSignedSignature,
    size_t encodedSignedSignatureSize,
    size_t* encodedSignedSignatureLength);
static uint64_t getSASTokenExpirationTime(uint32_t minutes);

// Time and error functions
static unsigned long getTime();
static String getFormattedDateTime(unsigned long epochTimeInSeconds);
static String mqttErrorCodeName(int errorCode);

/*---------------------------*/
/*    Main code execution    */
/*---------------------------*/

void setup()
{
  // Start serial communication
  Serial.begin(SERIAL_LOGGER_BAUD_RATE);

  // Wait briefly for Serial Monitor, but do not block forever
  unsigned long serialStartTime = millis();
  while (!Serial && millis() - serialStartTime < 5000) {
    ;
  }

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  Logger.Info("Starting Arduino MKR WiFi 1010 Azure IoT Hub telemetry example.");

  // Initialize DHT22 sensor
  dht.begin();

  // Initialize connections
  connectToWiFi();
  initializeAzureIoTHubClient();
  initializeMQTTClient();
  connectMQTTClientToAzureIoTHub();

  digitalWrite(LED_PIN, LOW);

  telemetryNextSendTimeMs = 0;
}

void loop()
{
  if (WiFi.status() != WL_CONNECTED)
  {
    connectToWiFi();
  }

  if (millis() > telemetryNextSendTimeMs)
  {
    temperature = dht.readTemperature();
    humidity = dht.readHumidity();

    if (isnan(temperature) || isnan(humidity))
    {
      Logger.Error("Failed to read from DHT22 sensor.");
      telemetryNextSendTimeMs = millis() + IOT_CONFIG_TELEMETRY_FREQUENCY_MS;
      return;
    }

    if (!mqttClient.connected())
    {
      connectMQTTClientToAzureIoTHub();
    }

    sendTelemetry();

    telemetryNextSendTimeMs = millis() + IOT_CONFIG_TELEMETRY_FREQUENCY_MS;
  }

  // MQTT loop must be called to process telemetry and Cloud-to-Device messages
  mqttClient.poll();

  delay(50);
}

/*-----------------------------------------------*/
/*    Initialization and connection functions    */
/*-----------------------------------------------*/

void connectToWiFi()
{
  Logger.Info(String("Attempting to connect to Wi-Fi SSID: ") + String(IOT_CONFIG_WIFI_SSID));

  WiFi.begin(IOT_CONFIG_WIFI_SSID, IOT_CONFIG_WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED)
  {
    Serial.print(".");
    delay(IOT_CONFIG_WIFI_CONNECT_RETRY_MS);
  }

  Serial.println();

  Logger.Info(
    String("Wi-Fi connected, IP address: ") +
    String(WiFi.localIP()) +
    String(", Strength (dBm): ") +
    String(WiFi.RSSI())
  );

  Logger.Info("Syncing time.");

  while (getTime() == 0)
  {
    Serial.print(".");
    delay(500);
  }

  Serial.println();
  Logger.Info("Time synced.");
}

void initializeAzureIoTHubClient()
{
  Logger.Info("Initializing Azure IoT Hub client.");

  az_span hostname = AZ_SPAN_FROM_STR(IOT_CONFIG_IOTHUB_FQDN);
  az_span deviceId = AZ_SPAN_FROM_STR(IOT_CONFIG_DEVICE_ID);

  az_iot_hub_client_options options = az_iot_hub_client_options_default();
  options.user_agent = AZ_SPAN_FROM_STR(IOT_CONFIG_AZURE_SDK_CLIENT_USER_AGENT);

  int result = az_iot_hub_client_init(&azIoTHubClient, hostname, deviceId, &options);

  EXIT_LOOP(
    az_result_failed(result),
    String("Failed to initialize Azure IoT Hub client. Return code: ") + String(result)
  );

  Logger.Info(String("Azure IoT Hub hostname: ") + String(IOT_CONFIG_IOTHUB_FQDN));
  Logger.Info("Azure IoT Hub client initialized.");
}

void initializeMQTTClient()
{
  Logger.Info("Initializing MQTT client.");

  int result;

  result = az_iot_hub_client_get_client_id(
      &azIoTHubClient,
      mqttClientId,
      sizeof(mqttClientId),
      NULL);

  EXIT_LOOP(
    az_result_failed(result),
    String("Failed to get MQTT client ID. Return code: ") + String(result)
  );

  result = az_iot_hub_client_get_user_name(
      &azIoTHubClient,
      mqttUsername,
      sizeof(mqttUsername),
      NULL);

  EXIT_LOOP(
    az_result_failed(result),
    String("Failed to get MQTT username. Return code: ") + String(result)
  );

  generateMQTTPassword();

  mqttClient.setId(mqttClientId);
  mqttClient.setUsernamePassword(mqttUsername, mqttPassword);
  mqttClient.onMessage(onMessageReceived);

  Logger.Info(String("MQTT Client ID: ") + String(mqttClientId));
  Logger.Info(String("MQTT Username: ") + String(mqttUsername));
  Logger.Info("MQTT client initialized.");
}

void connectMQTTClientToAzureIoTHub()
{
  Logger.Info("Connecting to Azure IoT Hub.");

  // Set a callback to get the current time used to validate the server certificate
  ArduinoBearSSL.onGetTime(getTime);

  while (!mqttClient.connect(IOT_CONFIG_IOTHUB_FQDN, AZ_IOT_DEFAULT_MQTT_CONNECT_PORT))
  {
    int code = mqttClient.connectError();

    Logger.Error(
      String("Cannot connect to Azure IoT Hub. Reason: ") +
      mqttErrorCodeName(code) +
      String(", Code: ") +
      String(code)
    );

    delay(5000);
  }

  Logger.Info("Connected to Azure IoT Hub.");

  mqttClient.subscribe(AZ_IOT_HUB_CLIENT_C2D_SUBSCRIBE_TOPIC);

  Logger.Info(
    String("Subscribed to MQTT topic: ") +
    String(AZ_IOT_HUB_CLIENT_C2D_SUBSCRIBE_TOPIC)
  );
}

/*------------------------------------------------*/
/*    Telemetry and message-callback functions    */
/*------------------------------------------------*/

void onMessageReceived(int messageSize)
{
  Logger.Info(
    String("Message received. Topic: ") +
    mqttClient.messageTopic() +
    String(", Length: ") +
    String(messageSize)
  );

  Logger.Info("Message content:");

  while (mqttClient.available())
  {
    Serial.print((char)mqttClient.read());
  }

  Serial.println();
}

static void sendTelemetry()
{
  digitalWrite(LED_PIN, HIGH);

  Logger.Info("Arduino MKR WiFi 1010 sending telemetry.");

  int result = az_iot_hub_client_telemetry_get_publish_topic(
      &azIoTHubClient,
      NULL,
      telemetryTopic,
      sizeof(telemetryTopic),
      NULL);

  EXIT_LOOP(
    az_result_failed(result),
    String("Failed to get telemetry publish topic. Return code: ") + String(result)
  );

  mqttClient.beginMessage(telemetryTopic);
  mqttClient.print(generateTelemetry());
  mqttClient.endMessage();

  Logger.Info("Telemetry sent.");

  delay(100);
  digitalWrite(LED_PIN, LOW);
}

static const char* generateTelemetry()
{
  telemetryPayload =
    String("{\"temp\":") +
    String(temperature, 2) +
    String(",\"RH\":") +
    String(humidity, 2) +
    String("}");

  Logger.Info(String("Telemetry payload: ") + telemetryPayload);

  return telemetryPayload.c_str();
}

/*************************************/
/*    SAS token related functions    */
/*************************************/

static void generateMQTTPassword()
{
  int result;

  uint64_t sasTokenDuration = 0;
  uint8_t signature[BUFFER_LENGTH_SAS_SIGNATURE] = {0};
  az_span signatureAzSpan = AZ_SPAN_FROM_BUFFER(signature);
  uint8_t encodedSignedSignature[BUFFER_LENGTH_SAS_ENCODED_SIGNED_SIGNATURE] = {0};
  size_t encodedSignedSignatureLength = 0;

  sasTokenDuration = getSASTokenExpirationTime(IOT_CONFIG_SAS_TOKEN_EXPIRY_MINUTES);

  result = az_iot_hub_client_sas_get_signature(
      &azIoTHubClient,
      sasTokenDuration,
      signatureAzSpan,
      &signatureAzSpan);

  EXIT_LOOP(
    az_result_failed(result),
    String("Could not get the signature for SAS token. Return code: ") + String(result)
  );

  generateSASBase64EncodedSignedSignature(
      az_span_ptr(signatureAzSpan),
      az_span_size(signatureAzSpan),
      encodedSignedSignature,
      sizeof(encodedSignedSignature),
      &encodedSignedSignatureLength);

  az_span encodedSignedSignatureAzSpan =
      az_span_create(encodedSignedSignature, encodedSignedSignatureLength);

  result = az_iot_hub_client_sas_get_password(
      &azIoTHubClient,
      sasTokenDuration,
      encodedSignedSignatureAzSpan,
      AZ_SPAN_EMPTY,
      mqttPassword,
      sizeof(mqttPassword),
      NULL);

  EXIT_LOOP(
    az_result_failed(result),
    String("Could not get the MQTT password. Return code: ") + String(result)
  );
}

static void generateSASBase64EncodedSignedSignature(
    uint8_t const* sasSignature,
    size_t const sasSignatureSize,
    uint8_t* encodedSignedSignature,
    size_t encodedSignedSignatureSize,
    size_t* encodedSignedSignatureLength)
{
  int result;

  unsigned char sasDecodedKey[BUFFER_LENGTH_SAS] = {0};
  az_span sasDecodedKeySpan = AZ_SPAN_FROM_BUFFER(sasDecodedKey);
  int32_t sasDecodedKeyLength = 0;

  uint8_t sasHMAC256SignedSignature[BUFFER_LENGTH_SAS] = {0};

  az_span configDeviceKeySpan =
      az_span_create((uint8_t*)IOT_CONFIG_DEVICE_KEY, sizeof(IOT_CONFIG_DEVICE_KEY) - 1);

  result = az_base64_decode(
      sasDecodedKeySpan,
      configDeviceKeySpan,
      &sasDecodedKeyLength);

  EXIT_LOOP(
    result != AZ_OK,
    String("az_base64_decode failed. Return code: ") + String(result)
  );

  result = ECCX08.begin();
  EXIT_LOOP(!result, "Failed to communicate with ATECC608.");

  result = ECCX08.nonce(sasDecodedKey);
  EXIT_LOOP(!result, "Failed to do nonce.");

  result = ECCX08.beginHMAC(0xFFFF);
  EXIT_LOOP(!result, "Failed to start HMAC operation.");

  result = ECCX08.updateHMAC(sasSignature, sasSignatureSize);
  EXIT_LOOP(!result, "Failed to update HMAC with signature.");

  result = ECCX08.endHMAC(sasHMAC256SignedSignature);
  EXIT_LOOP(!result, "Failed to end HMAC operation.");

  az_span signedSignatureSpan =
      az_span_create(sasHMAC256SignedSignature, sizeof(sasHMAC256SignedSignature));

  az_span encodedSignedSignatureSpan =
      az_span_create(encodedSignedSignature, encodedSignedSignatureSize);

  int32_t encodedLengthInt32 = 0;

  result = az_base64_encode(
      encodedSignedSignatureSpan,
      signedSignatureSpan,
      &encodedLengthInt32);

  EXIT_LOOP(
    result != AZ_OK,
    String("az_base64_encode failed. Return code: ") + String(result)
  );

  *encodedSignedSignatureLength = (size_t)encodedLengthInt32;
}

static uint64_t getSASTokenExpirationTime(uint32_t minutes)
{
  unsigned long now = getTime();
  unsigned long expiryTime = now + (SECS_PER_MIN * minutes);

  unsigned long localNow = now + GMT_OFFSET_SECS;
  unsigned long localExpiryTime = expiryTime + GMT_OFFSET_SECS;

  Logger.Info(
    String("UTC current time: ") +
    getFormattedDateTime(now) +
    String(" (epoch: ") +
    String(now) +
    String(" secs)")
  );

  Logger.Info(
    String("UTC expiry time: ") +
    getFormattedDateTime(expiryTime) +
    String(" (epoch: ") +
    String(expiryTime) +
    String(" secs)")
  );

  Logger.Info(String("Local current time: ") + getFormattedDateTime(localNow));
  Logger.Info(String("Local expiry time: ") + getFormattedDateTime(localExpiryTime));

  return (uint64_t)expiryTime;
}

/**********************************/
/*    Time and error functions    */
/**********************************/

static unsigned long getTime()
{
  return WiFi.getTime();
}

static String getFormattedDateTime(unsigned long epochTimeInSeconds)
{
  char dateTimeString[BUFFER_LENGTH_DATETIME_STRING];

  time_t epochTimeInSecondsAsTimeT = (time_t)epochTimeInSeconds;
  struct tm* timeInfo = localtime(&epochTimeInSecondsAsTimeT);

  strftime(dateTimeString, 20, "%F %T", timeInfo);

  return String(dateTimeString);
}

static String mqttErrorCodeName(int errorCode)
{
  String errorMessage;

  switch (errorCode)
  {
    case MQTT_CONNECTION_REFUSED:
      errorMessage = "MQTT_CONNECTION_REFUSED";
      break;

    case MQTT_CONNECTION_TIMEOUT:
      errorMessage = "MQTT_CONNECTION_TIMEOUT";
      break;

    case MQTT_SUCCESS:
      errorMessage = "MQTT_SUCCESS";
      break;

    case MQTT_UNACCEPTABLE_PROTOCOL_VERSION:
      errorMessage = "MQTT_UNACCEPTABLE_PROTOCOL_VERSION";
      break;

    case MQTT_IDENTIFIER_REJECTED:
      errorMessage = "MQTT_IDENTIFIER_REJECTED";
      break;

    case MQTT_SERVER_UNAVAILABLE:
      errorMessage = "MQTT_SERVER_UNAVAILABLE";
      break;

    case MQTT_BAD_USER_NAME_OR_PASSWORD:
      errorMessage = "MQTT_BAD_USER_NAME_OR_PASSWORD";
      break;

    case MQTT_NOT_AUTHORIZED:
      errorMessage = "MQTT_NOT_AUTHORIZED";
      break;

    default:
      errorMessage = "Unknown";
      break;
  }

  return errorMessage;
}