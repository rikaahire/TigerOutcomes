#!/usr/bin/env python
import keyring
import pandas as pd
import os
import sys
import argparse
import sqlalchemy
import sqlalchemy.orm
from sqlalchemy import select, distinct, and_, desc, func
from sqlalchemy.exc import SQLAlchemyError
import dotenv

#-----------------------------------------------------------------------

dotenv.load_dotenv()
DATABASE_URL = 'postgresql://tigeroutcomesdb_user:CS1c7Vu0hFmPKvOLlSHymCpiHaAOKVjV@dpg-cspdgmrtq21c739rtrrg-a.ohio-postgres.render.com/tigeroutcomesdb'
#DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://')
engine = sqlalchemy.create_engine(DATABASE_URL)

default_limit = 10
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

#-----------------------------------------------------------------------

# reads from favorites table
def read_favorites(name, soc_code=None, status=None, limit=default_limit):
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('favorites', metadata, autoload_with=engine)
    query = select(table)
    
    # Apply filters if specified
    if name:
        query = query.where(table.c.name == name)
    if soc_code:
        query = query.where(table.c.soc_code == soc_code)
    if status is not None:
        query = query.where(table.c.status == status)
    
    query = query.limit(limit)
    with engine.connect() as conn:    
        # Execute the query and fetch results
        rows = conn.execute(query).fetchall()
    return rows

# writes to favorites table
def write_favorite(name, soc_code, status):
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('favorites', metadata, autoload_with=engine)
    stmt = select(table).where(
                        table.c.name == name).where(
                        table.c.soc_code == soc_code).where(
                        table.c.status == status)
    ret = ''
    with engine.connect() as conn:
        try:
            favorite = conn.execute(stmt).fetchall()
            if favorite:
                new_stmt = table.update().where(
                            table.c.name == name).where(
                            table.c.soc_code == soc_code).where(
                            table.c.status == status).values(
                            status=status)
                conn.execute(new_stmt)
                ret = f"Updated favorite for {name} with SOC {soc_code}."
            else:
                new_stmt = table.insert().values(name=name, soc_code=soc_code, status=status)
                conn.execute(new_stmt)
                ret = f"Added new favorite for {name} with SOC {soc_code}."
            conn.commit()
        except SQLAlchemyError as e:
            ret = f"Error writing favorite: {e}"
            conn.rollback()
    return ret

# delete favorite for user
def clear_favorites(name, status=None, soc_code=None):
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('favorites', metadata, autoload_with=engine)
    stmt = table.delete().where(table.c.name == name)
    if status:
        stmt = stmt.where(table.c.status == status)
    if soc_code:
        stmt = stmt.where(table.c.soc_code == soc_code)
    ret = ''
    with engine.connect() as conn:
        try:
            conn.execute(stmt)
            #ret = f"Deleted all entries for user {name} with {status if status else 'any'} status"
            ret = f"Deleted favorite for user {name} with SOC {soc_code}."
            conn.commit()
        except SQLAlchemyError as e:
            ret = f"Error deleting favorites: {e}"
            conn.rollback()
    return ret

#-----------------------------------------------------------------------

def save_comments(comments):
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('comments', metadata, autoload_with=engine)
    with engine.connect() as conn:
        conn.execute(table.delete())  # Clear existing comments
        for comment in comments:
            conn.execute(table.insert().values(text=comment['text'], replies=comment['replies']))
        conn.commit()

def fetch_comments():
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('comments', metadata, autoload_with=engine)
    with engine.connect() as conn:
        rows = conn.execute(select(table)).fetchall()
    return [{"text": row.text, "replies": row.replies} for row in rows]


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

    # table = sqlalchemy.Table('soc_classification_definitions', metadata, autoload_with=engine)
    # cols['soc_classification_definitions'] = [column.name for column in table.columns]

    table = sqlalchemy.Table('bls_wage_data', metadata, autoload_with=engine)
    cols['bls_wage_data'] = [column.name for column in table.columns]

    table = sqlalchemy.Table('matching_sbert', metadata, autoload_with=engine)
    cols['matching_sbert'] = [column.name for column in table.columns]

    table = sqlalchemy.Table('favorites', metadata, autoload_with=engine)
    cols['favorites'] = [column.name for column in table.columns]

    table = sqlalchemy.Table('comments', metadata, autoload_with=engine)
    cols['comments'] = [column.name for column in table.columns]

    return cols

#-----------------------------------------------------------------------

# get people generic (search placeholder)
def get_student_by_major(major, limit=default_limit):
    return get_rows("pton_demographics", "AcadPlanDescr", major, limit)

#-----------------------------------------------------------------------

# generic when given table, column, and equal
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

#-----------------------------------------------------------------------

# generic for all options (should be initial)
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

#-----------------------------------------------------------------------

# for filling when soc_code is selected
def get_occupational_data_full(soc_code):
    metadata = sqlalchemy.MetaData()
    metadata.reflect(engine)

    # Get table
    table_descrip = sqlalchemy.Table("onet_occupation_data", metadata, autoload_with=engine)
    table_skills = sqlalchemy.Table("onet_skills", metadata, autoload_with=engine)
    table_knowledge = sqlalchemy.Table("onet_knowledge", metadata, autoload_with=engine)
    table_wage = sqlalchemy.Table("bls_wage_data", metadata, autoload_with=engine)
    # Create a select query
    stmt_descrip = sqlalchemy.select(table_descrip.c.Description).where(table_descrip.columns["O*NET-SOC Code"] == soc_code)
    stmt_skills = (sqlalchemy.select(table_skills.c['Element Name'])
                   .where(table_skills.columns["O*NET-SOC Code"] == soc_code)
                   .where(table_skills.columns["Scale ID"] == "IM")
                   .order_by(desc(table_skills.c["Data Value"]))
                   .limit(5))
    stmt_knowledge = sqlalchemy.select(distinct(table_knowledge.c['Element Name'])).where(table_knowledge.columns["O*NET-SOC Code"] == soc_code)
    mod_soc_code = soc_code[:7]
    stmt_wage = sqlalchemy.select(table_wage).where(table_wage.c["OCC_CODE"] == mod_soc_code)
    # Execute the query and fetch the results
    with engine.connect() as conn:
        description = conn.execute(stmt_descrip).fetchall()
        skills = conn.execute(stmt_skills).fetchall()
        knowledge = conn.execute(stmt_knowledge).fetchall()
        wage = conn.execute(stmt_wage).fetchall()

    wage = {"mean": wage[0][18], "10": wage[0][25], "25": wage[0][26], "50": wage[0][27], "75": wage[0][28], "90": wage[0][29]}
    return {'description': description, 'skills': skills, 'knowledge': knowledge, 'wage': wage}

#-----------------------------------------------------------------------

def get_onet_soc_codes_by_acadplandesc(acad_plan_descr, algo="alphabetical", min_wage=None):
    metadata = sqlalchemy.MetaData()
    metadata.reflect(engine)
    
    # Get tables
    pton_demographics = sqlalchemy.Table('pton_demographics', metadata, autoload_with=engine)
    pton_student_outcomes = sqlalchemy.Table('pton_student_outcomes', metadata, autoload_with=engine)
    matching_sbert = sqlalchemy.Table('matching_sbert', metadata, autoload_with=engine)
    onet_occupation_data = sqlalchemy.Table('onet_occupation_data', metadata, autoload_with=engine)
    table_wage = sqlalchemy.Table('bls_wage_data', metadata, autoload_with=engine)
    
    try:
        # Define the count expression and label it
        position_count = func.count().label('position_count')
    except:
        pass
    
    # from wage
    wage_column = table_wage.c['A_MEDIAN']
    
    # Build the query with intermediary mapping
    stmt = (
        sqlalchemy.select(
            onet_occupation_data.c['O*NET-SOC Code'],
            onet_occupation_data.c['Title'],
            position_count
        )
        .select_from(
            pton_demographics
            .join(
                pton_student_outcomes,
                pton_demographics.c['StudyID'] == pton_student_outcomes.c['StudyID']
            )
            .join(
                matching_sbert,
                func.lower(pton_student_outcomes.c['Position']) == func.lower(matching_sbert.c['Target Job Title'])
            )
            .join(
                onet_occupation_data,
                func.lower(matching_sbert.c['Matched Job Title']) == func.lower(onet_occupation_data.c['Title'])
            )
            .join(
                table_wage,
                func.substr(onet_occupation_data.c['O*NET-SOC Code'], 1, 7) == table_wage.c['OCC_CODE'] # adjusted SOC code
            )
        )
    )
    
    # Apply filters based on parameters
    if acad_plan_descr != 'all':
        stmt = stmt.where(
            func.lower(pton_demographics.c['AcadPlanDescr']) == func.lower(acad_plan_descr)
        )
    
    if min_wage is not None:
        stmt = stmt.where(
            wage_column >= min_wage
        )
    
    # Group by the necessary columns
    stmt = stmt.group_by(
        onet_occupation_data.c['O*NET-SOC Code'],
        onet_occupation_data.c['Title']
    )
    
    # Apply sorting based on the 'algo' parameter
    if algo == 'alphabetical':
        stmt = stmt.order_by(
            onet_occupation_data.c['Title']
        )
    elif algo == 'most_common_job':
        stmt = stmt.order_by(
            position_count.desc()
        )
    else:
        raise ValueError(f"Unknown sorting algorithm: {algo}")
    
    # Execute the query and fetch the results
    with engine.connect() as conn:
        results = conn.execute(stmt).fetchall()
    
    # Extract O*NET-SOC Codes and Titles from the results
    onet_soc_codes = [(row[0], row[1]) for row in results]
    
    return onet_soc_codes


# gets job titles from major
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
            and_(
                pton_student_outcomes.c["Position"] != None,
                pton_student_outcomes.c["Position"] != ''
            )
        )
    )
    if acad_plan_descr != 'all':
        stmt = stmt.where(
            func.lower(pton_demographics.c["AcadPlanDescr"]) == func.lower(acad_plan_descr)
        )
    stmt = stmt.order_by(pton_student_outcomes.c["Position"])
    with engine.connect() as conn:
        results = conn.execute(stmt).fetchall()
    

    positions = [row[0] for row in results]
    
    return positions


def get_onet_soc_code_by_title(title):
    metadata = sqlalchemy.MetaData()
    metadata.reflect(engine)
    
    # Get the onet_occupation_data table
    onet_occupation_data = sqlalchemy.Table('onet_occupation_data', metadata, autoload_with=engine)
    
    # Build the query with case-insensitive matching
    stmt = (
        sqlalchemy.select(onet_occupation_data.c["O*NET-SOC Code"])
        .where(func.lower(onet_occupation_data.c["Title"]) == func.lower(title))
    )
    
    # Execute the query and fetch the result
    with engine.connect() as conn:
        result = conn.execute(stmt).fetchone()
    
    # Check if a result was found
    if result:
        onet_soc_code = result[0]
        return onet_soc_code
    else:
        return None  # or raise an exception, or return an empty list

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
