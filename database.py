#!/usr/bin/env python
import sqlalchemy
import sqlalchemy.orm
from sqlalchemy import select, distinct, and_, desc, func, cast, Integer, case, update
from sqlalchemy.exc import SQLAlchemyError
import dotenv

#-----------------------------------------------------------------------

dotenv.load_dotenv()
DATABASE_URL = 'postgresql://tigeroutcomesdb_x9pf_user:Ewfihh7sXhDfzBS1JX51rem45ebypkqa@dpg-ctb2vm52ng1s73dphqqg-a.ohio-postgres.render.com/tigeroutcomesdb_x9pf'
engine = sqlalchemy.create_engine(DATABASE_URL)

default_limit = 10

# favorites database functions
#-----------------------------------------------------------------------

# read from favorites table
def read_favorites(name, soc_code=None, status=None, limit=default_limit):
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('favorites', metadata, autoload_with=engine)
    onet_occupation_data = sqlalchemy.Table('onet_occupation_data', metadata, autoload_with=engine)
    table_wage = sqlalchemy.Table('bls_wage_data', metadata, autoload_with=engine)

    query = (
        select(
            table,
            onet_occupation_data.c['Title']
        )
        .select_from(
            table.join(
                onet_occupation_data,
                table.c.soc_code == onet_occupation_data.c['O*NET-SOC Code']
            )
        )
    )

    # Apply filters if specified
    if name:
        query = query.where(table.c.name == name)
    if soc_code:
        query = query.where(table.c.soc_code == soc_code)
    if status is not None:
        query = query.where(table.c.status == status)
    
    # query = query.limit(limit)
    ret = []
    with engine.connect() as conn:
        try:
            rows = conn.execute(query).fetchall()
            # Order by descending mean wage
            for row in rows:
                soc_code = row.soc_code
                stmt_wage = sqlalchemy.select(table_wage).where(
                    table_wage.c["OCC_CODE"] == soc_code[:7]
                )
                wage_data = conn.execute(stmt_wage).fetchall()

                if wage_data:
                    mean_wage = wage_data[0][18]
                    try:
                        mean_wage = int(mean_wage)
                    except (ValueError, TypeError):
                        mean_wage = 0
                else:
                    mean_wage = 0

                ret.append({
                    "name": row.name,
                    "soc_code": row.soc_code,
                    "title": row.Title,
                    "mean_wage": mean_wage
                })
            ret.sort(key=lambda x: x["mean_wage"], reverse=True)
        except SQLAlchemyError as e:
            ret = f"Error reading favorites: {e}"
    return ret

# write to favorites table
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
                ret = clear_favorites(name, status, soc_code)
                return ret
            else:
                new_stmt = table.insert().values(name=name, soc_code=soc_code, status=status)
                conn.execute(new_stmt)
                ret = f"Added favorite for {name}."
            conn.commit()
        except SQLAlchemyError as e:
            ret = f"Error writing favorite: {e}"
            conn.rollback()
    return ret

# delete favorite for user
def clear_favorites(name, soc_code=None, status=None):
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
            ret = f"Removed favorite for {name}."
            conn.commit()
        except SQLAlchemyError as e:
            ret = f"Error deleting favorites: {e}"
            conn.rollback()
    return ret

# comments database functions
#-----------------------------------------------------------------------

# write a comment
def write_comment(name, soc_code, comment, valid=True):
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('comments', metadata, autoload_with=engine)
    ret = ''

    with engine.connect() as conn:
        try:
            conn.execute(
                table.insert().values(
                user=name,
                soc_code=soc_code,
                text=comment,
                valid=valid,
                # 'replies': []
            )
            )
            conn.commit()
            ret = soc_code
        except SQLAlchemyError as e:
            ret = f"Error deleting favorites: {e}"
            conn.rollback()
    return ret

# update a comment's state (flag or approve)
def update_comment(name, id, valid):
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('comments', metadata, autoload_with=engine)
    ret = ''
    with engine.connect() as conn:
        try:
            conn.execute(
                update(table).where(table.c.id==id).values(valid=valid)
            )
            conn.commit()
            ret = name
        except SQLAlchemyError as e:
            ret = f"Error deleting favorites: {e}"
            conn.rollback()
    return ret

# fetch all comments for a job given its soc code
def fetch_comments(soc_code):
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('comments', metadata, autoload_with=engine)

    with engine.connect() as conn:
        rows = conn.execute(select(table).where(table.c.soc_code == soc_code)).fetchall()
    ret = [{"id": row.id, "user": row.user, 
            "text": row.text, 
            # "replies": [{"reply": reply} for reply in row.replies]
            } for row in rows]
    return ret

# central major/job conversions and information sources
#-----------------------------------------------------------------------

# get relevant job information given soc code
def get_occupational_data_full(soc_code):
    metadata = sqlalchemy.MetaData()
    metadata.reflect(engine)

    # Get table
    table_descrip = sqlalchemy.Table("onet_occupation_data", metadata, autoload_with=engine)
    table_skills = sqlalchemy.Table("onet_skills", metadata, autoload_with=engine)
    table_knowledge = sqlalchemy.Table("onet_knowledge", metadata, autoload_with=engine)
    table_wage = sqlalchemy.Table("bls_wage_data", metadata, autoload_with=engine)
    table_work_styles = sqlalchemy.Table("onet_work_styles", metadata, autoload_with=engine)
    
    # Create a select query
    stmt_descrip = sqlalchemy.select(table_descrip.c.Description).where(table_descrip.columns["O*NET-SOC Code"] == soc_code)
    stmt_skills = (sqlalchemy.select(table_skills.c['Element Name'])
                   .where(table_skills.columns["O*NET-SOC Code"] == soc_code)
                   .where(table_skills.columns["Scale ID"] == "IM")
                   .order_by(desc(table_skills.c["Data Value"]))
                   .limit(5))
    stmt_work_styles = (sqlalchemy.select(table_work_styles.c['Element Name'])
                   .where(table_work_styles.columns["O*NET-SOC Code"] == soc_code)
                   .where(table_work_styles.columns["Scale ID"] == "IM")
                   .order_by(desc(table_work_styles.c["Data Value"]))
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
        work_styles = conn.execute(stmt_work_styles).fetchall()

    wage = {"mean": wage[0][18], "10": wage[0][25], "25": wage[0][26], "50": wage[0][27], "75": wage[0][28], "90": wage[0][29]}
    return {'description': description, 'skills': skills, 'knowledge': knowledge, 'wage': wage, "work_styles": work_styles}

# get matched jobs given a major, algorithm, and min_wage
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
        # from wage
        wage_column = (
            case(
                (table_wage.c['A_MEAN'] == "*", 0),
                else_=cast(table_wage.c['A_MEAN'], Integer),
            )
        )
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
    elif algo == 'common':
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

# get job title from soc code for card display
def get_name_from_soc(soc_code):
    metadata = sqlalchemy.MetaData()
    metadata.reflect(engine)
    onet_occupation_data = sqlalchemy.Table('onet_occupation_data', metadata, autoload_with=engine)
    
    # Build the query with intermediary mapping
    stmt = (
        sqlalchemy.select(onet_occupation_data.c['Title'])
        .where (onet_occupation_data.c['O*NET-SOC Code'] == soc_code)
    )

    with engine.connect() as conn:
        results = conn.execute(stmt).fetchall()
    return results

# deprecated functions
# # gets job titles from major
# def get_positions_by_acadplandesc(acad_plan_descr):
#     metadata = sqlalchemy.MetaData()
#     metadata.reflect(engine)
    
#     # Get tables
#     pton_demographics = sqlalchemy.Table('pton_demographics', metadata, autoload_with=engine)
#     pton_student_outcomes = sqlalchemy.Table('pton_student_outcomes', metadata, autoload_with=engine)
    
#     # Build  query
#     stmt = (
#         sqlalchemy.select(distinct(pton_student_outcomes.c["Position"]))
#         .select_from(
#             pton_demographics.join(
#                 pton_student_outcomes,
#                 pton_demographics.c["StudyID"] == pton_student_outcomes.c["StudyID"]
#             )
#         )
#         .where(
#             and_(
#                 pton_student_outcomes.c["Position"] != None,
#                 pton_student_outcomes.c["Position"] != ''
#             )
#         )
#     )
#     if acad_plan_descr != 'all':
#         stmt = stmt.where(
#             func.lower(pton_demographics.c["AcadPlanDescr"]) == func.lower(acad_plan_descr)
#         )
#     stmt = stmt.order_by(pton_student_outcomes.c["Position"])
#     with engine.connect() as conn:
#         results = conn.execute(stmt).fetchall()
    

#     positions = [row[0] for row in results]
    
#     return positions

# # gets onet soc code given job title
# def get_onet_soc_code_by_title(title):
#     metadata = sqlalchemy.MetaData()
#     metadata.reflect(engine)
    
#     # Get the onet_occupation_data table
#     onet_occupation_data = sqlalchemy.Table('onet_occupation_data', metadata, autoload_with=engine)
    
#     # Build the query with case-insensitive matching
#     stmt = (
#         sqlalchemy.select(onet_occupation_data.c["O*NET-SOC Code"])
#         .where(func.lower(onet_occupation_data.c["Title"]) == func.lower(title))
#     )
    
#     # Execute the query and fetch the result
#     with engine.connect() as conn:
#         result = conn.execute(stmt).fetchone()
    
#     # Check if a result was found
#     if result:
#         onet_soc_code = result[0]
#         return onet_soc_code
#     else:
#         return None  # or raise an exception, or return an empty list

# generic functions
#-----------------------------------------------------------------------

# get people generic (search placeholder)
def get_student_by_major(major, limit=default_limit):
    return get_rows("pton_demographics", "AcadPlanDescr", major, limit)

# full table generic when given table, column, and query
def get_rows(table_name, col_name, query, limit=default_limit):
    # input: table_name (sqlalchemy.Table): query table , col_name (str): target str, 
    #   query (str): rows we want to match
    #   limit (int): maximum number of rows that we want to return
    # output: finds all rows in table where row.col_name = query

    metadata = sqlalchemy.MetaData()
    metadata.reflect(engine)
    table = sqlalchemy.Table(table_name, metadata, autoload_with=engine)

    # Create a select query
    stmt = select(table).where(table.c[col_name] == query).limit(limit)

    # Execute the query and fetch the results
    with engine.connect() as conn:
        rows = conn.execute(stmt).fetchall()

    return rows

# check functions
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

def main():
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
