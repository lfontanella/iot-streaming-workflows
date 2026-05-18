# Arduino IDE / Arduino IoT Cloud Prototype

This folder documents the first prototype developed for the acquisition and visualization of environmental data using an Arduino MKR WiFi 1010 board and a DHT22 temperature and humidity sensor.

The objective of this prototype is to test a basic sensor-to-dashboard workflow before moving toward MQTT-based, open-source and BIM/openBIM visualization workflows.

## Prototype overview

The prototype is based on the following workflow:

```text
DHT22 temperature and humidity sensor
        ↓
Arduino MKR WiFi 1010
        ↓
Arduino IoT Cloud
        ↓
Real-time 2D dashboard
