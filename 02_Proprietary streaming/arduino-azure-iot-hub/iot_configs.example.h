// Example configuration file.
// Copy this file locally as iot_configs.h and replace the placeholder values
// with your own Wi-Fi and Azure IoT Hub credentials.
// Do not commit the real iot_configs.h file to the repository.

// Wifi
#define IOT_CONFIG_WIFI_SSID "<your-wifi-ssid>"
#define IOT_CONFIG_WIFI_PASSWORD "<your-wifi-password>"
#define IOT_CONFIG_WIFI_CONNECT_RETRY_MS 10000

// Azure IoT
#define IOT_CONFIG_IOTHUB_FQDN "<your-iot-hub-name>.azure-devices.net"
#define IOT_CONFIG_DEVICE_ID "<your-device-id>"
#define IOT_CONFIG_DEVICE_KEY "<your-device-primary-key>"

// When developing for your own Arduino-based platform,
// please follow the format '(ard;<platform>)'.
#define IOT_CONFIG_AZURE_SDK_CLIENT_USER_AGENT "c/" AZ_SDK_VERSION_STRING "(ard;mkrwifi1010)"

// Publish 1 message every 2 seconds
#define IOT_CONFIG_TELEMETRY_FREQUENCY_MS 2000

// SAS token validity, in minutes
#define IOT_CONFIG_SAS_TOKEN_EXPIRY_MINUTES 60

// Time Zone Offset
#define IOT_CONFIG_TIME_ZONE 1
#define IOT_CONFIG_TIME_ZONE_DAYLIGHT_SAVINGS_DIFF 1
#define IOT_CONFIG_DAYLIGHT_SAVINGS true