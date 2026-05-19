# Open Source Streaming Workflow

This folder documents an open-source workflow developed to test the real-time visualization of environmental sensor data in an IFC-based building model using MQTT, Python, Blender and Bonsai / BlenderBIM.

The workflow represents an open alternative to proprietary IoT streaming platforms. It explores how sensor data can be transmitted through MQTT, processed with Python and visualized directly inside a BIM/openBIM environment.

## Workflow overview

The tested workflow is based on the following logic:

```text
Arduino / simulated environmental data
        ↓
MQTT broker
        ↓
Python processing
        ↓
PMV calculation
        ↓
Blender + Bonsai / BlenderBIM
        ↓
IFC model-based visualization
```

The objective is to test how dynamic environmental data can be connected to IFC spaces and visualized in a building model through color coding and textual labels.

## Research context

This folder is part of the digital companion material of a PhD research project on the integration of BIM, openBIM standards and IoT data streams for the monitoring and visualization of building performance data.

In the overall research workflow, this section documents the transition from proprietary cloud-based platforms to an open-source pipeline based on:

- MQTT communication;
- Python data processing;
- PMV-based comfort evaluation;
- Blender / Bonsai visualization;
- IFC model interaction.

## Tools and technologies

The workflow involves:

- MQTT protocol;
- public or local MQTT broker;
- Python;
- `paho-mqtt`;
- Blender;
- Bonsai / BlenderBIM;
- IFC-based building model;
- PMV comfort index calculation.

## Folder structure

```text
03_Open source streaming/
│
├── README.md
│
├── images/
│   ├── mqtt-terminal-blender-overview.jpg
│   └── blender-ifc-pmv-visualization.jpg
│
└── python/
    ├── mqtt_pmv_calculator.py
    └── blender_mqtt_ifc_visualizer.py
```

## Python scripts

### `mqtt_pmv_calculator.py`

This script subscribes to an MQTT topic containing temperature and relative humidity data.

The expected message format is:

```text
temperature
relative_humidity
```

Example:

```text
20.80
52.00
```

The script:

1. receives temperature and relative humidity values;
2. calculates the Predicted Mean Vote, PMV;
3. publishes the PMV value to a dedicated MQTT topic.

The PMV calculation uses fixed assumptions for:

- mean radiant temperature;
- air velocity;
- metabolic rate;
- clothing insulation.

These values can be adapted according to the specific monitoring scenario.

### `blender_mqtt_ifc_visualizer.py`

This script is intended to be executed inside Blender.

It subscribes to MQTT topics containing:

- PMV values;
- temperature and relative humidity values.

The script then:

1. receives the PMV value;
2. assigns a color to selected `IfcSpace` objects according to the PMV range;
3. receives temperature and relative humidity values;
4. updates text objects in the Blender scene.

The visualization is based on the association between environmental data and IFC spaces.

## MQTT topics

The original prototype used the following MQTT topics:

| Topic | Description |
|---|---|
| `temperatura_umidita` | Topic used to transmit temperature and relative humidity values. |
| `PMV` | Topic used to transmit the calculated PMV value. |

For public demonstrations, it is recommended to use more specific topic names in order to avoid conflicts with other users on public MQTT brokers.

Recommended example:

```text
lfontanella/research/temperature_humidity
lfontanella/research/pmv
```

If a public broker is used, topic names should always be considered non-private.

For controlled experiments or real monitoring scenarios, a local or private MQTT broker is recommended.

## PMV-based visualization logic

The PMV value is used to assign colors to IFC spaces.

A possible visualization logic is:

| PMV range | Interpretation | Visualization |
|---|---|---|
| `PMV <= -3` | cold discomfort | blue |
| `-3 < PMV < -1` | cool discomfort | light blue |
| `-1 <= PMV <= 1` | acceptable comfort range | green |
| `1 < PMV <= 3` | warm discomfort | orange |
| `PMV > 3` | hot discomfort | red |

The thresholds and colors are used here as a research visualization prototype and can be adapted according to the specific comfort assessment framework.

## Blender / IFC model visualization

The Blender script applies materials to selected IFC space objects.

In the tested prototype, the script refers to selected objects such as:

```text
IfcSpace/09
IfcSpace/10
IfcSpace/11
IfcSpace/12
IfcSpace/13
IfcSpace/14
IfcSpace/15
```

The script also updates text objects associated with the monitored space, such as:

```text
Text_Temp13
Text_Hum13
```

These object names must be adapted to the IFC model and Blender scene used in each application.

## Configuration note

The Blender script is not fully generic in its current prototype form. It contains object names that refer to the tested Blender/Bonsai scene.

Before using the script with another IFC model, users must update:

- the list of `IfcSpace` objects to be colored;
- the names of the text objects used to display temperature and humidity;
- the MQTT topic names, if different topics are used;
- the PMV thresholds and color rules, if a different visualization logic is required.

In the tested prototype, these names were manually aligned with the IFC spaces and text objects available in the Blender scene.

## How to use the workflow

A simplified execution sequence is:

1. publish temperature and relative humidity values to the selected MQTT topic;
2. run `mqtt_pmv_calculator.py` to receive temperature and humidity data and calculate the PMV value;
3. open the IFC model in Blender with Bonsai / BlenderBIM;
4. run `blender_mqtt_ifc_visualizer.py` inside Blender;
5. verify that the object names in the script match the names of the IFC spaces and text objects in the Blender scene;
6. observe the model-based visualization of environmental and comfort data.

## Requirements

The Python scripts require:

```text
paho-mqtt
```

For the Blender script, the package must be available in the Python environment used by Blender.

Depending on the Blender installation, additional configuration may be required to install external Python packages inside Blender's Python environment.

## Images

The `images` folder includes screenshots documenting:

- MQTT data reception and Blender visualization;
- color-based visualization of environmental and comfort data in the IFC model;
- text labels showing environmental values in the model.

Included screenshots:

```text
images/mqtt-terminal-blender-overview.jpg
images/blender-ifc-pmv-visualization.jpg
```

Before publishing screenshots, local file paths, private usernames or confidential project information should be removed or cropped.

## Role in the research workflow

This open-source workflow was developed to test whether IoT data streams can be visualized in a BIM/openBIM environment without relying on proprietary digital twin platforms.

Compared with the proprietary workflow, this approach provides:

- greater control over the data-processing pipeline;
- direct access to Python-based calculations;
- direct interaction with the IFC model in Blender/Bonsai;
- adaptability to research-specific indicators, such as PMV.

At the same time, the workflow requires manual configuration of scripts, MQTT topics, object names and model associations.

## Data and privacy note

This folder does not include private credentials, access tokens or confidential data.

The demonstrated workflow can use a public MQTT broker for testing purposes, but a local or private broker is recommended for controlled research or real monitoring scenarios.

Do not publish:

- private MQTT credentials;
- real sensor identifiers if sensitive;
- personal data;
- confidential case-study data;
- private local file paths.

## Limitations

This folder documents a research prototype.

It is not intended as:

- a production-ready monitoring system;
- a certified comfort assessment tool;
- a certified facility management system;
- a complete digital twin platform.

The scripts are intended to demonstrate the methodological connection between MQTT data streams, Python processing, PMV calculation and IFC model-based visualization in Blender.
