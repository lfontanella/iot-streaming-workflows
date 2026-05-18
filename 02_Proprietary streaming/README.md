# Proprietary Streaming Workflow

This folder documents a proprietary cloud-based workflow developed to test the transmission, processing and visualization of environmental sensor data using Arduino, Microsoft Azure, Power BI and Autodesk Tandem.

The workflow represents an intermediate step between the basic Arduino IoT Cloud prototype and the later open-source BIM/openBIM streaming workflows.

## Workflow overview

The tested workflow is based on the following logic:

```text
DHT22 temperature and humidity sensor
        ↓
Arduino MKR WiFi 1010
        ↓
Azure IoT Hub
        ↓
Azure Stream Analytics
        ↓
Power BI dashboard
        ↓
Autodesk Tandem model-based visualization
```

The objective is to test how environmental data collected from a physical sensor can be transmitted to a cloud platform, processed as a data stream, visualized in a 2D dashboard and associated with elements or spaces in a digital building model.

## Research context

This folder is part of the digital companion material of a PhD research project on the integration of BIM, openBIM standards and IoT data streams for the monitoring and visualization of building performance data.

In the research workflow, this section documents the use of proprietary platforms to explore:

- IoT device-to-cloud communication;
- cloud-based data stream processing;
- 2D dashboard visualization;
- connection between IoT data and digital building models;
- model-based visualization of environmental data in a digital twin-oriented environment.

## Tools and platforms

The workflow involves:

- Arduino MKR WiFi 1010;
- DHT22 temperature and humidity sensor;
- Arduino IDE;
- Microsoft Azure IoT Hub;
- Azure Stream Analytics;
- Microsoft Power BI;
- Autodesk Tandem;
- IFC/BIM-based building model.

## Folder structure

```text
02_Proprietary streaming/
│
├── README.md
│
├── images/
│   ├── azure-iot-hub-stream-analytics.jpg
│   ├── power-bi-dashboard.jpg
│   ├── autodesk-tandem-stream-overview.jpg
│   ├── autodesk-tandem-heatmap.jpg
│   ├── autodesk-tandem-connections.jpg
│   └── autodesk-tandem-floor-view.jpg
│
└── arduino-azure-iot-hub/
    ├── Azure_IoT_Hub_Arduino_MKRwifi1010_Connect.ino
    ├── iot_configs.example.h
    ├── SerialLogger.cpp
    ├── SerialLogger.h
    └── azure-sdk-reference-readme.md
```

## Arduino to Azure IoT Hub

The Arduino MKR WiFi 1010 board is used to collect temperature and relative humidity data from a DHT22 sensor.

The sketch sends telemetry data to Azure IoT Hub. The telemetry payload includes environmental values such as temperature and relative humidity.

The Arduino-related files are stored in:

```text
arduino-azure-iot-hub/
```

Main files:

| File | Description |
|---|---|
| `Azure_IoT_Hub_Arduino_MKRwifi1010_Connect.ino` | Main Arduino sketch for sending sensor telemetry to Azure IoT Hub. |
| `iot_configs.example.h` | Example configuration file for Wi-Fi and Azure IoT Hub parameters. Real credentials must not be committed. |
| `SerialLogger.cpp` | Serial logging utility used by the Arduino sketch. |
| `SerialLogger.h` | Header file for the serial logging utility. |
| `azure-sdk-reference-readme.md` | Reference documentation based on the original Azure SDK sample. |

## Azure Stream Analytics

Azure Stream Analytics is used to process the incoming IoT data stream.

In the tested workflow, the stream receives data from Azure IoT Hub and forwards the processed output to visualization environments.

Example stream logic:

```sql
SELECT
    *
INTO
    output
FROM
    input
```

The screenshot below documents the data stream processing interface:

```text
images/azure-iot-hub-stream-analytics.jpg
```

## Power BI dashboard

Power BI is used to create a 2D dashboard for visualizing the incoming environmental data.

The dashboard includes:

- tabular visualization of incoming telemetry;
- temperature values;
- relative humidity values;
- time-based line chart.

See:

```text
images/power-bi-dashboard.jpg
```

## Autodesk Tandem visualization

Autodesk Tandem is used to test the visualization of IoT streams in relation to a BIM-based building model.

The workflow explores:

- association between sensor streams and model elements;
- visualization of temperature values;
- stream-based heatmap representation;
- connection between IoT data and model spaces or assets.

Example screenshots:

```text
images/autodesk-tandem-stream-overview.jpg
images/autodesk-tandem-heatmap.jpg
images/autodesk-tandem-connections.jpg
images/autodesk-tandem-floor-view.jpg
```

## Role in the research workflow

This proprietary workflow was used to evaluate the potential and limitations of commercial cloud-based platforms for IoT data visualization in building-related digital twin environments.

Compared with the basic Arduino IoT Cloud prototype, this workflow introduces:

- device-to-cloud telemetry transmission;
- cloud-based stream processing;
- dashboard visualization through Power BI;
- model-based visualization through Autodesk Tandem.

Compared with the open-source workflows developed later in the research, this approach depends on proprietary services, cloud accounts and platform-specific configurations.

## Data and privacy note

Real Wi-Fi credentials, Azure device keys, connection strings, access tokens and private account information are not included in this repository.

The file `iot_configs.example.h` is provided only as a template. Users must create their own local configuration file with their own credentials.

Do not commit:

- Wi-Fi passwords;
- Azure IoT Hub device keys;
- connection strings;
- SAS tokens;
- private account information;
- confidential project data.

## Limitations

This folder documents a research prototype and a methodological test workflow.

It is not intended as:

- a production-ready monitoring system;
- a certified digital twin platform;
- a complete facility management system;
- an official Autodesk Tandem or Microsoft Azure implementation guide.

The workflow was developed to support research-oriented comparison between proprietary and open-source approaches for IoT data-stream visualization in BIM/openBIM contexts.

## License and third-party material

The original Azure SDK sample files include Microsoft copyright and MIT license notices. These notices must be preserved in the related source files.

The research documentation and adaptation included in this repository are provided as part of the PhD research companion material.
