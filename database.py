#!/usr/bin/env python

import os
os.environ['DYLD_LIBRARY_PATH'] = '/Volumes/TigerOutcomes/PostgreSQL/17/lib'

import keyring
import pandas as pd

import sys
sys.path.append('/Volumes/TigerOutcomes/PostgreSQL')

import psycopg2
from psycopg2 import sql
import argparse

import sqlalchemy

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

def create_table_if_not_exists(connection, table_name, df):
    with connection.cursor() as cursor:
        # Generate SQL command for table creation
        columns = ", ".join(
            f"{col} TEXT" for col in df.columns
        )
        create_statement = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns});"
        cursor.execute(create_statement)
        print(f"Table {table_name} created or already exists.")

def load_data_to_postgres(file_path, table_name):
    try:
        # Read Excel file
        df = pd.read_excel(file_path)

        # Create SQLAlchemy engine
        engine = sqlalchemy.create_engine(DATABASE_URL)

        # Load DataFrame into PostgreSQL table, replacing if it exists
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"Data loaded into {table_name} successfully.")
    except Exception as e:
        print(f"Error loading data into {table_name}: {e}")

def main():
    parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        description='Database loading and SMB mounting script'
    )
    parser.add_argument('--load', action='store_true', help='Load data into the database')
    load = parser.parse_args().load

    # Mount SMB share
    mount_smb_share()

    if load:
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
