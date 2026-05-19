# Database-Driven Visualization Workflow

This folder documents a database-driven workflow developed to extract environmental monitoring data from an external database and visualize queried values inside an IFC-based building model using Python, SQLite, Excel and Blender/Bonsai.

The workflow was developed as part of a PhD research project on the integration of BIM, openBIM standards and IoT data streams for the monitoring and visualization of building performance data.

## Workflow overview

The tested workflow is based on the following logic:

```text
KTH database
        ↓
Python data extraction
        ↓
local SQLite database
        ↓
Excel query and mapping middleware
        ↓
Python script in Blender/Bonsai
        ↓
data visualization in IFC spaces
```

The objective is to test how data extracted from an external monitoring database can be queried, processed and visualized in relation to IFC spaces inside a BIM/openBIM environment.

## Research context

This folder documents the database-driven part of the IoT/openBIM workflow.

Compared with real-time MQTT-based streaming, this workflow is based on the interrogation of stored monitoring data. It was developed to test how historical or semi-historical sensor records can be connected to an IFC model through an intermediate query and mapping system.

The workflow supports:

- extraction of sensor records from an external database;
- local storage of selected records in a SQLite database;
- definition of queries through an Excel-based middleware;
- association between sensor identifiers and IFC spaces;
- visualization of queried values in Blender/Bonsai;
- periodic update of model-based visual outputs.

## Folder structure

```text
04_Database driven visualization/
│
├── README.md
│
├── images/
│   ├── kth-sql-to-blender-workflow-diagram.jpg
│   ├── kth-ifc-model-overview.jpg
│   ├── blender-bonsai-database-visualization.jpg
│   └── excel-query-middleware-example.jpg
│
├── python/
│   ├── 01_get_data_from_sql_template.py
│   └── 02_sqlite_to_blender_visualization_template.py
│
└── config/
    └── settings.example.json
```

## Main components

### External monitoring database

The original workflow was designed to query an external monitoring database.

For security and privacy reasons, the real database connection parameters are not included in this repository.

No real database credentials, connection strings, hosts, passwords, access tokens or direct database dumps are published.

### `settings.example.json`

The database connection parameters are intentionally separated from the Python scripts and stored in an external configuration file.

This design choice allows database credentials to be managed only by the network administrator or by the person responsible for data access. Users running the workflow should only access the database if they have been explicitly and consciously authorized by the data manager.

The repository includes only a template file:

```text
config/settings.example.json
```

The real file:

```text
settings.json
```

must be created locally and must never be committed to the repository.

## Reduced local database used for research purposes

In the research prototype, a reduced local SQLite database was generated from the original monitoring database.

This choice was made for research, testing and data-protection reasons. Working on a reduced local database made it possible to:

- test the workflow without repeatedly querying the main database;
- reduce computational load during prototyping;
- work with selected time intervals and selected sensors;
- avoid exposing direct access to the original monitoring database;
- separate the visualization workflow from the administrative management of database credentials.

This does not affect the methodological validity of the workflow. The reduced database is used as an operational research copy of selected records, while the overall process is designed to work with the main monitoring database when access is explicitly authorized by the data manager or network administrator.

In a standard operational scenario, the workflow can be connected directly to the main database, provided that access rights, credentials and data-governance conditions are properly managed.

## Python data extraction script

The first Python script is provided as a template:

```text
python/01_get_data_from_sql_template.py
```

Its role in the workflow is to:

1. read database connection parameters from `settings.json`;
2. connect to the external monitoring database;
3. extract selected sensor records;
4. convert timestamps where needed;
5. save the extracted data into a local SQLite database.

The generated local database is not included in this repository.

## Excel query and mapping middleware

In the original workflow, an Excel file was used as a middleware for defining queries and mapping sensor data to IFC spaces.

The Excel file was used to manage:

- sensor types;
- sensor reference positions;
- time intervals;
- sensor aliases;
- IFC entity identifiers;
- visualization styles.

For security and data-protection reasons, the real Excel file is not included in this repository.

Instead, the repository includes only an image documenting the query structure:

```text
images/excel-query-middleware-example.jpg
```

This image is included to document the logic of the query interface without publishing the original file or the full sensor-to-space mapping.

## Blender/Bonsai visualization script

The second Python script is provided as a template:

```text
python/02_sqlite_to_blender_visualization_template.py
```

Its role in the workflow is to:

1. read the local SQLite database;
2. read query and mapping information from the middleware structure;
3. calculate queried values, such as average sensor values over a selected time interval;
4. associate the queried values with IFC spaces;
5. assign colors to spaces according to predefined visualization styles;
6. update text objects in the Blender/Bonsai scene;
7. repeat the update periodically using a timer.

The script must be adapted to the specific IFC model, Blender scene, object names and local file structure used in each application.

## Images

The `images` folder documents the workflow visually.

Included images:

| Image | Description |
|---|---|
| `kth-sql-to-blender-workflow-diagram.jpg` | Diagram of the database-driven workflow. |
| `kth-ifc-model-overview.jpg` | IFC model overview used to explain the case-study workflow. |
| `blender-bonsai-database-visualization.jpg` | Example of database-driven visualization in Blender/Bonsai. |
| `excel-query-middleware-example.jpg` | Example of the Excel-based query middleware structure. |

Before publishing screenshots, local paths, usernames, database names, credentials or confidential identifiers should be removed or cropped.

## Data and security note

This folder intentionally does not include:

- real database credentials;
- real `settings.json` files;
- real database connection strings;
- generated SQLite databases;
- `data_overall.sql`;
- real Excel middleware files;
- IFC models;
- videos showing local paths, database access or sensitive project information.

The aim is to document the reproducible structure of the workflow without exposing sensitive information related to the original database, building model or case-study data.

The local SQLite database used during the research should be understood as a reduced operational copy created for testing and visualization purposes. It is not a replacement for the original monitoring database, but a controlled research dataset used to avoid unnecessary exposure of the main data infrastructure.

## Files not included

The following files are intentionally excluded from the public repository:

```text
settings.json
data_overall.sql
*.sqlite
*.sqlite3
*.db
*.ifc
*.ifczip
*.mp4
real Excel mapping files
```

This choice is made to avoid the disclosure of credentials, monitoring data, building information, model geometry, sensor mappings or other potentially sensitive case-study information.

## Role in the research workflow

This workflow represents the database-driven component of the research.

It complements the MQTT-based real-time workflow by showing how stored monitoring data can be queried and visualized in a BIM/openBIM environment.

The workflow demonstrates the methodological connection between:

- external monitoring databases;
- local data extraction;
- query definition;
- sensor-to-space mapping;
- IFC-based model visualization;
- periodic data-driven updates in Blender/Bonsai.

## Limitations

This folder documents a research prototype.

It is not intended as:

- a production-ready data platform;
- a certified monitoring system;
- a certified facility management tool;
- a public release of the original KTH database or building model;
- a complete reproducible package with real case-study data.

The scripts are provided as templates and must be adapted to authorized datasets, local file structures and specific IFC/Blender configurations.
