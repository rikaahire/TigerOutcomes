#!/usr/bin/env python
import keyring
import pandas as pd
import os
import sys
import argparse
import sqlalchemy
import sqlalchemy.orm
from sqlalchemy import select, distinct
from sqlalchemy.sql import text
import dotenv

#-----------------------------------------------------------------------

dotenv.load_dotenv()
DATABASE_URL = 'postgresql://tigeroutcomesdb_user:CS1c7Vu0hFmPKvOLlSHymCpiHaAOKVjV@dpg-cspdgmrtq21c739rtrrg-a.ohio-postgres.render.com/tigeroutcomesdb'
#DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://')
engine = sqlalchemy.create_engine(DATABASE_URL)

#-----------------------------------------------------------------------

os.environ['DYLD_LIBRARY_PATH'] = '/Volumes/TigerOutcomes/PostgreSQL/17/lib'
sys.path.append('/Volumes/TigerOutcomes/SQL')

# Database and SMB configuration
#DATABASE_URL = 'postgresql://bz5989@localhost:5432/mydb'
server_path = "smb://files/dept/InstResearch/TigerOutcomes"
mount_path = "/Volumes/TigerOutcomes-1"  # Where the server will be mounted on your Mac

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
    # "soc_classification_definitions.xlsx": "soc_classification_definitions", # not relevant
    "bls_wage_data_2023.xlsx": "bls_wage_data",
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

def get_student_by_major(major, limit=10):
    return get_rows("pton_demographics", "AcadPlanDescr", major, limit)

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

def get_occupational_data_full(soc_code):
    metadata = sqlalchemy.MetaData()
    metadata.reflect(engine)

    # Get table
    table_descrip = sqlalchemy.Table("onet_occupation_data", metadata, autoload_with=engine)
    table_skills = sqlalchemy.Table("onet_skills", metadata, autoload_with=engine)
    table_knowledge = sqlalchemy.Table("onet_knowledge", metadata, autoload_with=engine)
    # Create a select query
    stmt_descrip = sqlalchemy.select(table_descrip.c.Description).where(table_descrip.columns["O*NET-SOC Code"] == soc_code)
    stmt_skills = sqlalchemy.select(distinct(table_skills.c['Element Name'])).where(table_skills.columns["O*NET-SOC Code"] == soc_code)
    stmt_knowledge = sqlalchemy.select(distinct(table_knowledge.c['Element Name'])).where(table_knowledge.columns["O*NET-SOC Code"] == soc_code)
    # Execute the query and fetch the results
    with engine.connect() as conn:
        description = conn.execute(stmt_descrip).fetchall()
        skills = conn.execute(stmt_skills).fetchall()
        knowledge = conn.execute(stmt_knowledge).fetchall()

    return {'description': description, 'skills': skills, 'knowledge' :knowledge}



def get_onet_soc_codes_by_acadplandesc(acad_plan_descr):
    metadata = sqlalchemy.MetaData()
    metadata.reflect(engine)
    
    # Get tables
    pton_demographics = sqlalchemy.Table('pton_demographics', metadata, autoload_with=engine)
    pton_student_outcomes = sqlalchemy.Table('pton_student_outcomes', metadata, autoload_with=engine)
    onet_occupation_data = sqlalchemy.Table('onet_occupation_data', metadata, autoload_with=engine)
    
    stmt = (
        sqlalchemy.select(distinct(onet_occupation_data.c["O*NET-SOC Code"]))
        .select_from(
            pton_demographics.join(
                pton_student_outcomes,
                pton_demographics.c["StudyID"] == pton_student_outcomes.c["StudyID"]
            ).join(
                onet_occupation_data,
                pton_student_outcomes.c["Position"] == onet_occupation_data.c["Title"]
            )
        )
        .where(pton_demographics.c["AcadPlanDescr"] == acad_plan_descr)
    )
    
    with engine.connect() as conn:
        results = conn.execute(stmt).fetchall()
    
    onet_soc_codes = [row[0] for row in results]
    
    return onet_soc_codes

from sqlalchemy import func, and_

def get_positions_by_acadplandesc(acad_plan_descr):
    metadata = sqlalchemy.MetaData()
    metadata.reflect(engine)
    
    # Get tables
    pton_demographics = sqlalchemy.Table('pton_demographics', metadata, autoload_with=engine)
    pton_student_outcomes = sqlalchemy.Table('pton_student_outcomes', metadata, autoload_with=engine)
    
    # Build  query
    stmt = (
        sqlalchemy.select(distinct(pton_student_outcomes.c["Position"]))
        .select_from(
            pton_demographics.join(
                pton_student_outcomes,
                pton_demographics.c["StudyID"] == pton_student_outcomes.c["StudyID"]
            )
        )
        .where(
            func.lower(pton_demographics.c["AcadPlanDescr"]) == func.lower(acad_plan_descr)
        )
        .where(
            and_(
                pton_student_outcomes.c["Position"] != None,
                pton_student_outcomes.c["Position"] != ''
            )
        )
        .order_by(pton_student_outcomes.c["Position"])
    )
    

    with engine.connect() as conn:
        results = conn.execute(stmt).fetchall()
    

    positions = [row[0] for row in results]
    
    return positions




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
