#!/usr/bin/env python
from sqlalchemy.sql import text
import keyring
import pandas as pd
import os
import sys
import argparse
import sqlalchemy
from sqlalchemy import select, distinct

os.environ['DYLD_LIBRARY_PATH'] = '/Volumes/TigerOutcomes/PostgreSQL/17/lib'
sys.path.append('/Volumes/TigerOutcomes/SQL')

# Database and SMB configuration
DATABASE_URL = 'postgresql://bz5989@localhost:5432/mydb'
server_path = "smb://files/dept/InstResearch/TigerOutcomes"
mount_path = "/Volumes/TigerOutcomes-1"  # Where the server will be mounted on your Mac

# Excel files and their corresponding Postgres tables
files_to_tables = {
    "COS333_AcA_Student_Outcomes.xlsx": "pton_student_outcomes",
    "COS333_Demographics.xlsx": "pton_demographics",
    "COS333_NSC_ST_Degrees2.xlsx": "pton_degrees", # not used
    "Occupation Data.xlsx": "onet_occupation_data",
    "Job Zone Reference.xlsx": "onet_job_zone_reference", # not relevant
    "Job Zones.xlsx": "onet_job_zones", # not relevant
    "Abilities.xlsx": "onet_abilities",
    "Skills.xlsx": "onet_skills",
    "Knowledge.xlsx": "onet_knowledge",
    "Alternate Titles.xlsx": "onet_alternate_titles",
    "soc_classification_definitions.xlsx": "soc_classification_definitions", # not relevant
    "bls_wage_data_2023.xlsx": "bls_wage_data",
}

# Create SQLAlchemy engine
engine = sqlalchemy.create_engine(DATABASE_URL)

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

        # Load DataFrame into PostgreSQL table, replacing if it exists
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"Data loaded into {table_name} successfully.")
    except Exception as e:
        print(f"Error loading data into {table_name}: {e}")

def get_cols():
    metadata = sqlalchemy.MetaData()
    cols = {}
    table = sqlalchemy.Table('pton_student_outcomes', metadata, autoload_with=engine)
    cols['pton_student_outcomes'] = [column.name for column in table.columns]

    table = sqlalchemy.Table('pton_demographics', metadata, autoload_with=engine)
    cols['pton_demographics'] = [column.name for column in table.columns]

    # table = sqlalchemy.Table('pton_degrees', metadata, autoload_with=engine)
    # cols['pton_degrees'] = [column.name for column in table.columns]

    table = sqlalchemy.Table('onet_occupation_data', metadata, autoload_with=engine)
    cols['onet_occupation_data'] = [column.name for column in table.columns]

    # table = sqlalchemy.Table('onet_job_zone_reference', metadata, autoload_with=engine)
    # cols['onet_job_zone_reference'] = [column.name for column in table.columns]

    # table = sqlalchemy.Table('onet_job_zones', metadata, autoload_with=engine)
    # cols['onet_job_zones'] = [column.name for column in table.columns]

    table = sqlalchemy.Table('onet_abilities', metadata, autoload_with=engine)
    cols['onet_abilities'] = [column.name for column in table.columns]

    table = sqlalchemy.Table('onet_skills', metadata, autoload_with=engine)
    cols['onet_skills'] = [column.name for column in table.columns]

    table = sqlalchemy.Table('onet_knowledge', metadata, autoload_with=engine)
    cols['onet_knowledge'] = [column.name for column in table.columns]
    
    table = sqlalchemy.Table('onet_alternate_titles', metadata, autoload_with=engine)
    cols['onet_alternate_titles'] = [column.name for column in table.columns]

    # table = sqlalchemy.Table('soc_classification_definitions', metadata, autoload_with=engine)
    # cols['soc_classification_definitions'] = [column.name for column in table.columns]

    table = sqlalchemy.Table('bls_wage_data', metadata, autoload_with=engine)
    cols['bls_wage_data'] = [column.name for column in table.columns]

    return cols

def get_student_by_major(table_name, major, limit=10):
    # deprecated, see get_rows
    metadata = sqlalchemy.MetaData()
    metadata.reflect(engine)

    # Get table
    table = sqlalchemy.Table(table_name, metadata, autoload_with=engine)

    # Create a select query
    stmt = select(table).where(table.columns.AcadPlanDescr == major).limit(limit)

    # Execute the query and fetch the results
    with engine.connect() as conn:
        rows = conn.execute(stmt).fetchall()

    return rows

def get_rows(table_name, col_name, query, limit=10):
    # input: table_name (sqlalchemy.Table): query table , col_name (str): target str, 
    #   query (str): rows we want to match
    #   limit (int): maximum number of rows that we want to return
    # output: finds all rows in table where row.col_name = query

    metadata = sqlalchemy.MetaData()
    metadata.reflect(engine)

    # Get table
    table = sqlalchemy.Table(table_name, metadata, autoload_with=engine)

    # Create a select query
    stmt = select(table).where(table.c[col_name] == query).limit(limit)

    # Execute the query and fetch the results
    with engine.connect() as conn:
        rows = conn.execute(stmt).fetchall()

    return rows


def get_all_instances(table_name, col_name):
    # input: table name and column name
    # output: returns a list of all unique rows within the column

    metadata = sqlalchemy.MetaData()
    metadata.reflect(engine)

    # Get table
    table = sqlalchemy.Table(table_name, metadata, autoload_with=engine)

    # Create a select query
    stmt = select(distinct(table.c[col_name]))

    # Execute the query and fetch the results
    with engine.connect() as conn:
        rows = conn.execute(stmt).fetchall()

    return rows


def get_occupational_data_desc(table_name, title):
    metadata = sqlalchemy.MetaData()
    metadata.reflect(engine)

    # Get table
    table = sqlalchemy.Table(table_name, metadata, autoload_with=engine)

    # Create a select query
    stmt = sqlalchemy.select(table.Description).where(table.columns.Title == title)

    # Execute the query and fetch the results
    with engine.connect() as conn:
        rows = conn.execute(stmt).fetchall()

    return rows

def get_first_rows(table_name, number):
    metadata = sqlalchemy.MetaData()
    metadata.reflect(engine)

    # Get table
    table = sqlalchemy.Table(table_name, metadata, autoload_with=engine)

    # Create a select query
    stmt = sqlalchemy.select(table).limit(number)

    # Execute the query and fetch the results
    with engine.connect() as conn:
        rows = conn.execute(stmt).fetchall()

    return rows


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

    cols = get_cols()
    for key, value in cols.items():
        print(key + ":")
        print(value)
        print("\n")
    # rows = get_rows("demographics", 10)
    # for row in rows:
    #     print(row)

if __name__ == '__main__':
    main()
