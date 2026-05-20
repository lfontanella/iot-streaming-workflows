"""
01_get_data_from_sql_template.py

Sanitized template derived from the original research prototype.

Purpose:
- Connect to an external monitoring database, if authorized.
- Extract selected sensor records.
- Save the selected records into a local SQLite database used by the Blender/Bonsai visualization workflow.

Security note:
- The real settings.json file is not included in this repository.
- The real Excel mapping file is not included in this repository.
- The generated local database is not included in this repository.
- Access to the main database must be explicitly authorized by the data manager or network administrator.

Research context:
This script documents the database extraction step of a database-driven BIM/openBIM visualization workflow.

Author: Luca Fontanella
"""

import json
import os
import sys
import datetime
import time
import sqlite3
from pathlib import Path

import psycopg2
from psycopg2 import sql
import pandas as pd


class lvnglb:
    """
    Local class used to extract selected monitoring records from an external database and store them in a reduced local SQLite database.

    The class name is kept close to the original prototype for consistency with the research workflow.
    """

    def __init__(self):
        if getattr(sys, "frozen", False):
            self.app_path = Path(sys.executable).resolve().parent
        else:
            # This script is expected to be inside:
            # 04_Database driven visualization/python/
            self.app_path = Path(__file__).resolve().parent.parent

        self.settings_file_pathandname = self.app_path / "config" / "settings.json"
        self.sensor_mapping_file_pathandname = self.app_path / "excel" / "s_bctinputid.xlsx"

        # The reduced local database is generated only in authorized local use.
        # It must not be committed to the public repository.
        self.local_data_dir = self.app_path / "local_data"
        self.local_data_dir.mkdir(parents=True, exist_ok=True)

        self.data_overall_file_pathandname = self.local_data_dir / "data_overall.sql"

        self.df = pd.DataFrame()

        # Load existing local SQLite data, if already present.
        try:
            conn_data_overall = sqlite3.connect(self.data_overall_file_pathandname)
            self.df = pd.read_sql_query("SELECT * FROM main", conn_data_overall)
            conn_data_overall.close()
        except Exception:
            self.df = pd.DataFrame(columns=["bctinputid", "tidpunkt", "mvarde"])

        # Load local database settings.
        # The real settings.json file must be created locally from:
        # config/settings.example.json
        if not self.settings_file_pathandname.exists():
            raise FileNotFoundError(
                f"Missing settings file: {self.settings_file_pathandname}\n"
                "Create a local settings.json file from config/settings.example.json."
            )

        with open(self.settings_file_pathandname, "r", encoding="utf-8") as f:
            self.settings = json.load(f)

        required_settings = [
            "database",
            "host",
            "user",
            "password",
            "port",
            "table containing records",
        ]

        missing_settings = [
            key for key in required_settings if key not in self.settings
        ]

        if missing_settings:
            raise KeyError(
                f"Missing required settings in settings.json: {missing_settings}"
            )

        self.conn = psycopg2.connect(
            database=self.settings["database"],
            host=self.settings["host"],
            user=self.settings["user"],
            password=self.settings["password"],
            port=self.settings["port"],
        )

        self.cursor = self.conn.cursor()

    def get_data_1sensor(
        self,
        bctinputid="?",
        bctinputid_alias="?",
        datetime_start="?",
        datetime_end="?",
    ):
        """
        Extract records for one sensor and one selected time interval.

        Parameters
        ----------
        bctinputid : str
            Sensor identifier used in the external database.
        bctinputid_alias : str
            Local alias used in the research workflow.
        datetime_start : datetime.datetime
            Start of the selected time interval.
        datetime_end : datetime.datetime
            End of the selected time interval.
        """

        if bctinputid == "?":
            raise ValueError("Missing bctinputid.")

        if bctinputid_alias == "?":
            bctinputid_alias = bctinputid

        if datetime_start == "?" or datetime_end == "?":
            raise ValueError("Missing datetime_start or datetime_end.")

        table_name = self.settings["table containing records"]

        print(f"Querying sensor {bctinputid_alias}")
        print(f"Time interval: {datetime_start} -> {datetime_end}")

        time_0 = datetime.datetime.now()

        # The table name is inserted through psycopg2.sql.Identifier.
        # Values are passed as parameters.
        query = sql.SQL("""
            SELECT bctinputid, tidpunkt, mvarde
            FROM {table_name}
            WHERE bctinputid = %s
              AND tidpunkt > %s::timestamp without time zone
              AND tidpunkt <= %s::timestamp without time zone
            ORDER BY tidpunkt
        """).format(
            table_name=sql.Identifier(table_name)
        )

        self.cursor.execute(
            query,
            (
                str(bctinputid).replace("{", "").replace("}", "").strip(),
                datetime_start.strftime("%Y-%m-%d %H:%M:%S"),
                datetime_end.strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )

        data = pd.DataFrame(
            self.cursor.fetchall(),
            columns=["bctinputid", "tidpunkt", "mvarde"],
        )

        if data.empty:
            print("No records found for this query.")
            return self.df

        # Replace the original ID with the local alias used in the research workflow.
        data["bctinputid"] = str(bctinputid_alias)

        # Convert timestamps into Unix time to reduce storage size and simplify
        # the following query phase.
        data["tidpunkt"] = data["tidpunkt"].apply(pd.Timestamp.timestamp)

        self.df = pd.concat([self.df, data], axis=0, ignore_index=True)

        time_get_data = datetime.datetime.now() - time_0
        print("time_get_data", time_get_data)
        print(f"Downloaded records: {len(data)}")

        return self.df

    def get_data_s_sensor(
        self,
        s_bctinputid="?",
        s_bctinputid_alias="?",
        s_download_keyword="?",
        download_keyword="?",
        datetime_start_allperiod="?",
        datetime_end_allperiod="?",
        datetime_max_span="?",
    ):
        """
        Extract records for all sensors selected through a download keyword.

        The keyword is read from the local Excel mapping file. The real mapping file is not included in the public repository.
        """

        print("Getting records for selected sensors...")
        print("Database access must be authorized by the data manager.")

        if download_keyword == "?":
            raise ValueError("Missing download_keyword.")

        for n in range(len(s_bctinputid)):
            if s_download_keyword[n] != download_keyword:
                continue

            datetime_start = datetime_start_allperiod
            n_period = 0
            time_prev = datetime.datetime.now()

            while datetime_start < datetime_end_allperiod:
                n_period += 1
                duration = datetime.datetime.now() - time_prev
                time_prev = datetime.datetime.now()

                sys.stdout.write(
                    "\u001b[1000D "
                    + str(n)
                    + " "
                    + str(s_bctinputid[n])
                    + " "
                    + str(s_bctinputid_alias[n])
                    + " - period: "
                    + str(n_period)
                    + " - Duration: "
                    + str(duration)
                )
                sys.stdout.flush()

                time.sleep(1)

                datetime_end = datetime_start + datetime_max_span

                try:
                    self.df = self.get_data_1sensor(
                        bctinputid=s_bctinputid[n],
                        bctinputid_alias=s_bctinputid_alias[n],
                        datetime_start=datetime_start,
                        datetime_end=datetime_end,
                    )

                    conn_res = sqlite3.connect(self.data_overall_file_pathandname)
                    self.df.to_sql(
                        name="main",
                        con=conn_res,
                        if_exists="replace",
                        index=False,
                    )
                    conn_res.close()

                except Exception as e:
                    print(f"\nError while querying sensor {s_bctinputid_alias[n]}: {e}")

                datetime_start = datetime_end

    def CLOSE(self):
        """
        Close the connection to the external database.
        """

        self.conn.close()


if __name__ == "__main__":
    LivingLab = lvnglb()

    if not LivingLab.sensor_mapping_file_pathandname.exists():
        raise FileNotFoundError(
            f"Missing local Excel mapping file: {LivingLab.sensor_mapping_file_pathandname}\n"
            "The real Excel file is intentionally not included in the public repository."
        )

    s_bctinputid_df = pd.read_excel(
        LivingLab.sensor_mapping_file_pathandname,
        sheet_name="Sensors",
    )

    s_bctinputid = s_bctinputid_df["id"].tolist()
    s_bctinputid_alias = s_bctinputid_df["id_alias"].tolist()
    s_download_keyword = s_bctinputid_df["download_keyword"].tolist()

    # Replace this locally with the keyword used in the authorized Excel file.
    download_keyword = "example-download-keyword"

    LivingLab.get_data_s_sensor(
        s_bctinputid=s_bctinputid,
        s_bctinputid_alias=s_bctinputid_alias,
        s_download_keyword=s_download_keyword,
        download_keyword=download_keyword,
        datetime_start_allperiod=datetime.datetime(2023, 1, 1, 0, 0, 0),
        datetime_end_allperiod=datetime.datetime(2023, 1, 2, 0, 0, 0),
        datetime_max_span=datetime.timedelta(minutes=1000),
    )

    LivingLab.CLOSE()