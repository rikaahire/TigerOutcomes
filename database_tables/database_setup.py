#!/usr/bin/env python
import keyring
import pandas as pd
import os
import sys
import argparse
import dotenv
import sqlalchemy
import sqlalchemy.orm
from sqlalchemy import select, distinct

#-----------------------------------------------------------------------

dotenv.load_dotenv()
DATABASE_URL = ''
#DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://')
engine = sqlalchemy.create_engine(DATABASE_URL)

default_limit = 10

#-----------------------------------------------------------------------

os.environ['DYLD_LIBRARY_PATH'] = '/Volumes/TigerOutcomes/PostgreSQL/17/lib'
sys.path.append('/Volumes/TigerOutcomes/SQL')

# Database and SMB configuration
#DATABASE_URL = 'postgresql://bz5989@localhost:5432/mydb'
server_path = "smb://files/dept/InstResearch/TigerOutcomes"
mount_path = "/Volumes/TigerOutcomes"  # Where the server will be mounted on your Mac

# Excel files and their corresponding Postgres tables
files_to_tables = {
    # "COS333_AcA_Student_Outcomes.xlsx": "pton_student_outcomes",
    # "COS333_Demographics.xlsx": "pton_demographics",
    "COS333_AcA_Student_Outcomes_rand.xlsx": "pton_student_outcomes",
    "COS333_Demographics_rand.xlsx": "pton_demographics",
    # "COS333_NSC_ST_Degrees2.xlsx": "pton_degrees", # not used
    "Occupation Data.xlsx": "onet_occupation_data",
    # "Job Zone Reference.xlsx": "onet_job_zone_reference", # not relevant
    # "Job Zones.xlsx": "onet_job_zones", # not relevant
    "Abilities.xlsx": "onet_abilities",
    "Skills.xlsx": "onet_skills",
    "Knowledge.xlsx": "onet_knowledge",
    "Alternate Titles.xlsx": "onet_alternate_titles",
    "Work Styles.xlsx": "onet_work_styles",
    # "soc_classification_definitions.xlsx": "soc_classification_definitions", # not relevant
    "bls_wage_data_2023.xlsx": "bls_wage_data",
}

#-----------------------------------------------------------------------

# mount share for smb database
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

# load excel into postgres
def load_data_to_postgres(file_path, table_name):
    try:
        # Read Excel file
        df = pd.read_excel(file_path)

        # Load DataFrame into PostgreSQL table, replacing if it exists
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"Data loaded into {table_name} successfully.")
    except Exception as e:
        print(f"Error loading data into {table_name}: {e}")

#-----------------------------------------------------------------------

# get all column names (for use with get_rows for column names)
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

    table = sqlalchemy.Table('onet_work_styles', metadata, autoload_with=engine)
    cols['onet_work_styles'] = [column.name for column in table.columns]

    # table = sqlalchemy.Table('soc_classification_definitions', metadata, autoload_with=engine)
    # cols['soc_classification_definitions'] = [column.name for column in table.columns]

    return cols

#-----------------------------------------------------------------------

# generic when given table, column, and query
def get_rows(table_name, col_name, query, limit=default_limit):
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

# load if desired; otherwise check database structure
#-----------------------------------------------------------------------

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

    rows = get_rows("demographics", 10)
    for row in rows:
        print(row)

if __name__ == '__main__':
    main()
