# HBIM Case Study – Gallerie dell’Accademia di Venezia

This folder documents a case-study application of the IoT/openBIM workflow in an HBIM heritage context.

The workflow was developed to test how environmental monitoring data, threshold-based conservation criteria and IFC/HBIM model visualization can support facility management and preventive conservation processes in a museum environment.

The case study focuses on the Gallerie dell’Accademia di Venezia and explores how sensor-based alerts can be visualized directly inside a Blender/Bonsai model.

## Workflow overview

The tested workflow is based on the following logic:

```text
Environmental sensor data
        ↓
MQTT / Python processing
        ↓
threshold comparison
        ↓
Blender/Bonsai HBIM visualization
        ↓
popup alert in the model
        ↓
CSV log of anomalies
        ↓
support to facility management and conservation-oriented decisions
```

The objective is to test how monitored environmental values can be compared with predefined threshold values and translated into visual alerts inside an HBIM model.

## Research context

This folder is part of the digital companion material of a PhD research project on the integration of BIM, openBIM standards and IoT data streams for the monitoring and visualization of building performance data.

In the overall research workflow, this section represents the heritage-oriented application of the methodology.

The workflow supports:

- environmental monitoring in an HBIM context;
- definition of threshold values for conservation-oriented assessment;
- visualization of anomalies in the IFC/HBIM model;
- popup alerts in Blender/Bonsai;
- logging of threshold exceedances in a CSV file;
- interpretation of localized anomalies by facility managers or conservation staff.

## Folder structure

```text
05_Case study HBIM - Gallerie Accademia Venezia/
│
├── README.md
│
├── images/
│   ├── blender-temperature-threshold-alert.jpg
│   └── blender-material-specific-artwork-alert.jpg
│
├── python/
    └── hbim_conservation_threshold_alerts_template.py
```

## Main components

### Blender/Bonsai HBIM model

The workflow is designed to be executed inside Blender with Bonsai / BlenderBIM, using an IFC/HBIM model previously loaded in the scene.

The public repository does not include the original HBIM model of the case study.

The script must be adapted to the specific object names, IFC spaces, artworks, sensors and text objects available in the local Blender/Bonsai scene.

### Environmental thresholds

The prototype uses predefined threshold values to detect environmental anomalies.

In the research context, these thresholds were defined by considering conservation-oriented references, material sensitivity and environmental requirements for heritage objects.

The thresholds are not intended as universal values. They must be adapted and validated according to:

- the monitored parameter;
- the type of object or material;
- the conservation context;
- the requirements defined by conservators, facility managers or responsible institutions;
- the applicable standards, guidelines or conservation protocols.

### Temperature alert example

One prototype configuration uses a temperature threshold to detect potentially unsafe environmental conditions.

When the measured value exceeds the threshold:

1. the related IFC spaces or monitored objects are visually highlighted;
2. a popup alert is shown inside Blender;
3. the alert condition is displayed in a Blender UI panel;
4. the anomaly is recorded in a CSV log file.

The related screenshot is:

```text
images/blender-temperature-threshold-alert.jpg
```

### Material-specific artwork alert

A more specific use case concerns the association of environmental thresholds with different types of artworks or materials.

For example, different threshold values can be associated with:

- canvas paintings;
- marble sculptures;
- other material categories;
- specific monitored objects;
- specific display areas.

This makes it possible to identify localized anomalies.

For instance, if the threshold is exceeded for canvas paintings located on one side of the room while similar objects on the opposite side remain within acceptable values, the facility manager can interpret the alert as a possible localized environmental problem rather than as a general room-level issue.

The related screenshot is:

```text
images/blender-material-specific-artwork-alert.jpg
```

## Python script

The Python script is provided as a research template:

```text
python/hbim_conservation_threshold_alerts_template.py
```

The script documents the following logic:

1. receive environmental values through MQTT;
2. compare the received value with predefined thresholds;
3. update the color of selected IFC/HBIM objects;
4. update text labels in the Blender scene;
5. show popup alerts in Blender when thresholds are exceeded;
6. display alert status in a side UI panel;
7. write threshold exceedances to a CSV log.

The script must be adapted locally before use.

In particular, users must update:

- MQTT broker settings;
- MQTT topic names;
- threshold values;
- IFC space names;
- artwork or object names;
- text object names;
- material-specific threshold rules;
- CSV output path;
- local Blender/Bonsai scene configuration.

## Alert log

When a threshold is exceeded, the prototype writes an anomaly record to a CSV file.

The log can include information such as:

```text
timestamp, object_or_space, measured_value, alert_type
```

The public repository does not include real alert logs.

The `logs` folder is included only as a placeholder to document where local CSV logs can be generated.

Real CSV logs must not be committed if they contain sensitive monitoring data, object identifiers, room names or case-study information.

## Images

The `images` folder documents the visual behavior of the workflow.

Included images:

| Image | Description |
|---|---|
| `blender-temperature-threshold-alert.jpg` | Example of a temperature threshold exceedance with popup alert in Blender/Bonsai. |
| `blender-material-specific-artwork-alert.jpg` | Example of material-specific threshold visualization for artworks. |

The images are included to document the research workflow and the visual logic of the prototype.

## Data and privacy note

This folder intentionally does not include:

- the original HBIM/IFC model;
- real monitoring datasets;
- real alert logs;
- real CSV output files;
- private MQTT credentials;
- private broker configurations;
- sensitive museum or artwork data;
- confidential conservation data;
- local file paths.

The repository documents the workflow structure and the prototype logic without exposing sensitive case-study information.

## Security note

The prototype may use public MQTT brokers for demonstration and testing purposes.

For real monitoring scenarios, a private and properly secured broker should be used.

The public template should not be used with:

- private credentials hard-coded in the script;
- unsecured operational monitoring data;
- sensitive artwork identifiers;
- confidential museum data;
- production facility management systems without proper validation.

## Role in the research workflow

This folder represents the HBIM heritage case-study application of the broader IoT/openBIM methodology.

It shows how environmental data can be interpreted not only as numerical values, but as spatially and materially meaningful information inside an HBIM model.

The workflow demonstrates the connection between:

- sensor-based monitoring;
- conservation-oriented threshold evaluation;
- IFC/HBIM model visualization;
- localized anomaly detection;
- facility management support;
- preventive conservation decision-making.

## Limitations

This folder documents a research prototype.

It is not intended as:

- a certified conservation monitoring system;
- a production-ready facility management platform;
- a substitute for professional conservation assessment;
- an official environmental control system for museum collections;
- a complete release of the original case-study data.

Thresholds, alert rules and visualization logic must be validated by qualified experts before any operational use.

The script is provided as a sanitized template and must be adapted to authorized datasets, validated thresholds and specific Blender/Bonsai model configurations.
