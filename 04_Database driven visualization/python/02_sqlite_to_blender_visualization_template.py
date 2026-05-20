"""
02_sqlite_to_blender_visualization_template.py

Sanitized template derived from the original research prototype.

Purpose:
- Read a reduced local SQLite database.
- Read query and mapping information from a local Excel middleware file.
- Query selected values using DuckDB.
- Visualize queried values in Blender/Bonsai by coloring IFC-related objects.
- Optionally update text objects in the Blender scene.

Security note:
- The real Excel mapping file is not included in this repository.
- The reduced local SQLite database is not included in this repository.
- The real IFC model is not included in this repository.
- Local paths, sensor mappings and object names must be adapted locally.

Research context:
This script documents the database-driven visualization step of a BIM/openBIM workflow.

Author: Luca Fontanella
"""

import os
import sqlite3
from pathlib import Path

import bpy
import pandas as pd
import duckdb
import matplotlib as mpl


# ---------------------------------------------------------------------------
# LOCAL FILES
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent

# This script is expected to be inside:
# 04_Database driven visualization/python/
WORKFLOW_DIR = SCRIPT_DIR.parent

# Local Excel middleware file.
# The real file is intentionally not included in the public repository.
SETTINGS_FILE_NAME = WORKFLOW_DIR / "excel" / "s_bctinputid.xlsx"

# Local reduced SQLite database.
# The real file is intentionally not included in the public repository.
DATA_FILE_NAME = WORKFLOW_DIR / "local_data" / "data_overall.sql"

# The IFC model is not loaded directly by this public template.
# In the research prototype, the IFC model was already opened in Blender/Bonsai.
IFC_FILE_NAME = "?"


# ---------------------------------------------------------------------------
# TEXT OBJECT MAPPING
# ---------------------------------------------------------------------------

# In the original prototype, selected sensor aliases were associated with specific Blender text objects.
#
# The real mapping is not included here. Add local mappings only in authorized local copies of the script.
#
# Example:
# TEXT_OBJECTS_BY_SENSOR_ALIAS = {
#     "1001": "Text_Value_Example01",
#     "1002": "Text_Value_Example02",
# }
TEXT_OBJECTS_BY_SENSOR_ALIAS = {}


class snsr2bim:
    """
    Class used to connect sensor data to BIM objects in Blender/Bonsai.

    The class name is kept close to the original prototype for consistency with the research workflow.
    """

    def __init__(
        self,
        settings_file_name=SETTINGS_FILE_NAME,
        data_file_name=DATA_FILE_NAME,
        ifc_file_name=IFC_FILE_NAME,
    ):
        print("Initializing database-driven Blender visualization.")

        self.current_dir = WORKFLOW_DIR

        self.settings_file_pathandname = Path(settings_file_name)
        self.data_file_pathandname = Path(data_file_name)

        if not self.settings_file_pathandname.exists():
            raise FileNotFoundError(
                f"Missing Excel middleware file: {self.settings_file_pathandname}\n"
                "The real Excel middleware file is intentionally not included "
                "in the public repository."
            )

        if not self.data_file_pathandname.exists():
            raise FileNotFoundError(
                f"Missing local SQLite database: {self.data_file_pathandname}\n"
                "The reduced local database is intentionally not included "
                "in the public repository."
            )

        self.df_sensors = pd.read_excel(
            self.settings_file_pathandname,
            sheet_name="Sensors",
        )

        self.df_sensors["apartmentnum"] = self.df_sensors["apartmentnum"].astype(str)

        self.df_styles = pd.read_excel(
            self.settings_file_pathandname,
            sheet_name="Styles",
        )

        # Prepare available palettes from the Styles sheet.
        s_palette = set(self.df_styles["Palette"].to_list())
        self.palette_map_dict = {}

        for palette in s_palette:
            self.palette_map_dict[palette] = mpl.colormaps[palette]

        # Read local SQLite data.
        con = sqlite3.connect(self.data_file_pathandname)
        self.df_data = pd.read_sql_query("SELECT * FROM main", con=con)
        con.close()

        # The public template does not import an IFC file directly.
        # The IFC model is expected to be already opened in Blender/Bonsai.
        if ifc_file_name != "?":
            print(
                "IFC file loading is disabled in the public template. "
                "Open the IFC model directly in Blender/Bonsai."
            )

    def inquiry(self, s_query="?"):
        """
        Execute one or more queries and update the corresponding Blender objects.
        """

        s_ifcentity_id = []
        s_value = []
        s_color_rgb = []

        if s_query == "?":
            print("No query provided.")
            return

        for query in s_query:
            df_data = self.df_data

            try:
                df_res = duckdb.query(query).df()
            except Exception as e:
                print(f"Error while executing query: {query}")
                print(e)
                continue

            print(df_res)

            if df_res.empty:
                print("Query returned no results.")
                continue

            s_bctinputid = set(df_res["bctinputid"])

            for bctinputid in s_bctinputid:
                bctinputid_str = str(bctinputid)

                duckdb.register("df_sensors", self.df_sensors)

                try:
                    df_supp = duckdb.query(
                        "SELECT IfcEntity_id, Style_id "
                        "FROM df_sensors "
                        "WHERE CAST(id_alias AS VARCHAR) = '" + bctinputid_str + "'"
                    ).df()
                finally:
                    duckdb.unregister("df_sensors")

                if df_supp.empty:
                    print(f"No IFC mapping found for sensor alias {bctinputid_str}.")
                    continue

                ifcentity_id = df_supp["IfcEntity_id"][0]

                value = duckdb.query(
                    "SELECT value "
                    "FROM df_res "
                    "WHERE CAST(bctinputid AS VARCHAR) = '" + bctinputid_str + "'"
                ).df()

                if value.empty:
                    print(f"No value found for sensor alias {bctinputid_str}.")
                    continue

                value = value["value"][0]
                style_id = df_supp["Style_id"][0]

                duckdb.register("df_styles", self.df_styles)

                try:
                    palette = duckdb.query(
                        "SELECT Palette, Value_Min, Value_Max "
                        "FROM df_styles "
                        "WHERE Code = '" + str(style_id) + "'"
                    ).df()
                finally:
                    duckdb.unregister("df_styles")

                if palette.empty:
                    print(f"No style found for style id {style_id}.")
                    continue

                value_min = palette["Value_Min"][0]
                value_max = palette["Value_Max"][0]

                norm = mpl.colors.Normalize(vmin=value_min, vmax=value_max)
                cmap = mpl.colormaps.get_cmap(palette["Palette"][0])
                mappable = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
                color_rgb = mappable.to_rgba(value)

                s_ifcentity_id.append(ifcentity_id)
                s_value.append(value)
                s_color_rgb.append(color_rgb)

                # Optional text update.
                # The real mapping is not included in this public template.
                if bctinputid_str in TEXT_OBJECTS_BY_SENSOR_ALIAS:
                    text_object_name = TEXT_OBJECTS_BY_SENSOR_ALIAS[bctinputid_str]

                    print(f"Checking text object {text_object_name}...")
                    text_object = bpy.data.objects.get(text_object_name)

                    if text_object:
                        print(f"Object {text_object_name} found. Type: {text_object.type}")

                        if text_object.type == "FONT":
                            try:
                                print(
                                    f"Updating text object {text_object_name} "
                                    f"with value {value:.2f}"
                                )
                                text_object.data.body = f"Value: {value:.2f}"
                            except Exception as e:
                                print(
                                    f"Error while updating text object "
                                    f"{text_object_name}: {e}"
                                )
                        else:
                            print(
                                f"{text_object_name} is not a FONT object. "
                                f"Found type: {text_object.type}"
                            )
                    else:
                        print(f"Text object '{text_object_name}' not found.")

        n_ifcentity_id = -1

        for ifcentity_id in s_ifcentity_id:
            n_ifcentity_id += 1

            print(ifcentity_id)

            obj = bpy.data.objects.get(ifcentity_id)

            if obj:
                material_name = ifcentity_id + "_material"
                print(material_name)

                material = bpy.data.materials.get(material_name)
                print(material)

                if not material:
                    material = bpy.data.materials.new(name=material_name)

                color_rgb = s_color_rgb[n_ifcentity_id]

                material.diffuse_color = color_rgb

                obj.data.materials.clear()
                obj.data.materials.append(material)

            else:
                print(f"Blender object not found: {ifcentity_id}")


sensors = snsr2bim(
    settings_file_name=SETTINGS_FILE_NAME,
    data_file_name=DATA_FILE_NAME,
    ifc_file_name=IFC_FILE_NAME,
)


def run_queries():
    """
    Read queries from the Excel middleware and update the Blender/Bonsai model.
    """

    try:
        obj = sensors

        obj.df_queries = pd.read_excel(
            obj.settings_file_pathandname,
            sheet_name="QUERIES",
            skiprows=2,
        )

        df_sensors = obj.df_sensors
        s_query = []

        for index, row in obj.df_queries.iterrows():
            sensor_type = row["Sensor - Type"]
            sensor_refposition = row["Sensor - Ref. Position"]
            dateandtime_start = row["Date and Time - Start"]
            dateandtime_stop = row["Date and Time - Stop"]

            query = (
                "SELECT id_alias "
                "FROM df_sensors "
                "WHERE title = '"
                + str(sensor_type)
                + "' AND apartmentnum = '"
                + str(sensor_refposition)
                + "'"
            )

            try:
                bctinputid = duckdb.query(query).df()["id_alias"].values.tolist()[0]

                s_query.append(
                    "SELECT bctinputid, AVG(mvarde) AS value "
                    "FROM df_data "
                    "WHERE bctinputid = "
                    + str(bctinputid)
                    + " AND tidpunkt > "
                    + str(dateandtime_start)
                    + " AND tidpunkt <= "
                    + str(dateandtime_stop)
                    + " GROUP BY bctinputid"
                )

            except Exception:
                print("Error in query", query)

        obj.inquiry(s_query=s_query)

        print("Exiting run_queries.")
        return None

    except Exception as e:
        print(e)

    return 1


def timer_callback():
    """
    Blender timer callback.

    The visualization is updated periodically.
    """

    try:
        run_queries()
    except Exception as e:
        print(f"Error in timer callback: {e}")

    return 20.0


# Register the timer.
bpy.app.timers.register(timer_callback)