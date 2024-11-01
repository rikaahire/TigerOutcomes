#!/usr/bin/env python

import os
os.environ['DYLD_LIBRARY_PATH'] = '/Volumes/TigerOutcomes/PostgreSQL/17/lib'

import keyring
import pandas as pd
import psycopg2
from psycopg2 import sql
import argparse
import sys

# Database and SMB configuration
DATABASE_URL = 'postgresql://bz5989@localhost:5432/mydb'
server_path = "smb://files/dept/InstResearch/TigerOutcomes"
mount_path = "/Volumes/TigerOutcomes"  # Where the server will be mounted on your Mac

# Excel files and their corresponding Postgres tables
files_to_tables = {
    "COS333_AcA_Student_Outcomes.xlsx": "student_outcomes",
    "COS333_Demographics.xlsx": "demographics",
    "COS333_NSC_ST_Degrees2.xlsx": "st_degrees"
}

def mount_smb_share():
    # Retrieve credentials from Keychain
    username = keyring.get_password("TigerOutcomes_Service", "username_key")
    password = keyring.get_password("TigerOutcomes_Service", "password_key")

    # Mount the server using AppleScript for SMB connection
    if username and password:
        os.system(
            f"osascript -e 'do shell script \"mount volume \\\"{server_path}\\\" "
            f"as user name \\\"{username}\\\" with password \\\"{password}\\\"\"'"
        )
        print("SMB share mounted successfully.")
    else:
        print("Failed to retrieve SMB credentials.")

def load_data_to_postgres(file_path, table_name):
    try:
        # Read Excel file
        df = pd.read_excel(file_path)

        # Convert Excel file to Postgres table
        with psycopg2.connect(DATABASE_URL) as connection:
            cursor = connection.cursor()
            for _, row in df.iterrows():
                columns = list(df.columns)
                values = [row[col] for col in columns]
                insert_statement = sql.SQL(
                    "INSERT INTO {} ({}) VALUES ({})"
                ).format(
                    sql.Identifier(table_name),
                    sql.SQL(', ').join(map(sql.Identifier, columns)),
                    sql.SQL(', ').join(sql.Placeholder() * len(values))
                )
                cursor.execute(insert_statement, values)
            print(f"Data loaded into {table_name}")
    except Exception as e:
        print(f"Error loading data into {table_name}: {e}")

def main():
    parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        description='Database loading and SMB mounting script'
    )
    parser.add_argument('load', help='load data into the database')
    load = parser.parse_args().load

    # Mount SMB share
    mount_smb_share()

    if load is not None:
        for file_name, table_name in files_to_tables.items():
            # Path to Excel file on mounted server
            file_path = f"{mount_path}/{file_name}"
            try:
                load_data_to_postgres(file_path, table_name)
            except FileNotFoundError:
                print(f"File {file_name} not found on SMB share.")
    else:
        print("No data loading")

if __name__ == '__main__':
    main()
