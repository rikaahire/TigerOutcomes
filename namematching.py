#!/usr/bin/env python
import keyring
import pandas as pd
import os
import sys
import argparse
import sqlalchemy
import sqlalchemy.orm
from sqlalchemy import select, distinct, func, and_
from sqlalchemy.exc import SQLAlchemyError
import dotenv


from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
import numpy as np
from gensim.models import KeyedVectors
from sklearn.metrics.pairwise import cosine_similarity
from gensim.scripts.glove2word2vec import glove2word2vec
from sentence_transformers import SentenceTransformer

#-----------------------------------------------------------------------

dotenv.load_dotenv()
DATABASE_URL = 'postgresql://tigeroutcomesdb_x9pf_user:Ewfihh7sXhDfzBS1JX51rem45ebypkqa@dpg-ctb2vm52ng1s73dphqqg-a.ohio-postgres.render.com/tigeroutcomesdb_x9pf'
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
            ret = f"Delete favorite for user {name} with SOC {soc_code}."
            conn.commit()
        except SQLAlchemyError as e:
            ret = f"Error deleting favorites: {e}"
            conn.rollback()
    return ret

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

    return [row[0] for row in rows]

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
    stmt_skills = sqlalchemy.select(distinct(table_skills.c['Element Name'])).where(table_skills.columns["O*NET-SOC Code"] == soc_code)
    stmt_knowledge = sqlalchemy.select(distinct(table_knowledge.c['Element Name'])).where(table_knowledge.columns["O*NET-SOC Code"] == soc_code)
    mod_soc_code = soc_code[:7]
    stmt_wage = sqlalchemy.select(table_wage).where(table_wage.c["OCC_CODE"] == mod_soc_code)
    # Execute the query and fetch the results
    with engine.connect() as conn:
        description = conn.execute(stmt_descrip).fetchall()
        skills = conn.execute(stmt_skills).fetchall()
        knowledge = conn.execute(stmt_knowledge).fetchall()
        wage = conn.execute(stmt_wage).fetchall()

    print(wage)
    wage = [[wage[0][18]], [wage[0][25]], [wage[0][26]], [wage[0][27]], [wage[0][28]], [wage[0][29]]]
    return {'description': description, 'skills': skills, 'knowledge': knowledge, 'wage': wage}

#-----------------------------------------------------------------------

# replacement for results from search (soc_codes from major)
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

# ##################################

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def mapping_cosine(targets, job_titles):

    # filter out not none types
    targets = [target for target in targets if target is not None]
    job_titles = [job_title for job_title in job_titles if job_title is not None]

    # Combine all targets and job titles for vectorization
    all_texts = targets + job_titles
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(all_texts)
    
    # Separate the target and job title vectors
    target_vectors = vectors[:len(targets)]  # First `len(targets)` rows
    job_title_vectors = vectors[len(targets):]  # Remaining rows

    # Calculate pairwise cosine similarity between all targets and job titles
    similarity_matrix = cosine_similarity(target_vectors, job_title_vectors)

    # Find the most similar job title for each target
    most_similar_indices = similarity_matrix.argmax(axis=1)
    most_similar_scores = similarity_matrix.max(axis=1)

    # Create a DataFrame
    df = pd.DataFrame({
        "princeton_positions": targets,
        "o_net_titles": [job_titles[i] for i in most_similar_indices],
        "similarity_score": most_similar_scores
    })

    return df

def mapping_bow(targets, job_titles):
    # Filter out None values
    targets = [target for target in targets if target is not None]
    job_titles = [job_title for job_title in job_titles if job_title is not None]

    # Combine all targets and job titles for vectorization
    all_texts = targets + job_titles
    vectorizer = CountVectorizer()
    vectors = vectorizer.fit_transform(all_texts)
    
    # Separate the target and job title vectors
    target_vectors = vectors[:len(targets)]  # First `len(targets)` rows
    job_title_vectors = vectors[len(targets):]  # Remaining rows

    # Calculate pairwise cosine similarity between all targets and job titles
    similarity_matrix = cosine_similarity(target_vectors, job_title_vectors)

    # Find the most similar job title for each target
    most_similar_indices = similarity_matrix.argmax(axis=1)
    most_similar_scores = similarity_matrix.max(axis=1)

    # Create a DataFrame
    df = pd.DataFrame({
        "princeton_positions": targets,
        "o_net_titles": [job_titles[i] for i in most_similar_indices],
        "similarity_score": most_similar_scores
    })

    df.to_csv("bow.txt")

    return df

def average_word_embeddings(text, model, vector_size=100):
    # Generate average word embeddings for the input text
    if text is None or not isinstance(text, str):
        return np.zeros(vector_size)
    
    words = text.lower().split()
    embeddings = [model[word] for word in words if word in model]
    if embeddings:
        return np.mean(embeddings, axis=0)
    else:
        return np.zeros(vector_size)

def mapping_embeddings(targets, job_titles, model, vector_size=100):
    # Filter out None values
    targets = [target for target in targets if target is not None]
    job_titles = [job_title for job_title in job_titles if job_title is not None]

    # Calculate the embeddings for all targets
    target_vectors = np.array([average_word_embeddings(target, model, vector_size) for target in targets])
    
    # Calculate the embeddings for all job titles
    job_title_vectors = np.array([average_word_embeddings(job_title, model, vector_size) for job_title in job_titles])

    # Compute pairwise cosine similarity
    similarity_matrix = cosine_similarity(target_vectors, job_title_vectors)

    # Find the most similar job title for each target
    most_similar_indices = similarity_matrix.argmax(axis=1)
    most_similar_scores = similarity_matrix.max(axis=1)

    # Create a DataFrame
    df = pd.DataFrame({
        "princeton_positions": targets,
        "o_net_titles": [job_titles[i] for i in most_similar_indices],
        "similarity_score": most_similar_scores
    })

    return df

def mapping_embeddings_weighted(targets, job_titles, model, vector_size=100):
    """
    Calculate cosine similarity between a list of target job titles and a list of job titles
    using TF-IDF-weighted word embeddings.

    Args:
        targets (list): List of target job titles.
        job_titles (list): List of job titles to compare against.
        model: Pre-trained word embeddings (e.g., Word2Vec or GloVe).
        vector_size (int): Size of the word embeddings.

    Returns:
        pd.DataFrame: DataFrame containing the targets, most similar job titles, and their similarity scores.
    """
    # Filter out None values
    targets = [target for target in targets if target is not None]
    job_titles = [job_title for job_title in job_titles if job_title is not None]

    # Combine all texts for TF-IDF fitting
    all_texts = targets + job_titles

    # Fit TF-IDF on all job titles and targets
    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform(all_texts)
    feature_names = tfidf.get_feature_names_out()
    idf_dict = dict(zip(feature_names, tfidf.idf_))

    def weighted_average(text):
        # Generate TF-IDF-weighted average embedding for a text
        words = text.lower().split()
        embeddings = [model[word] * idf_dict.get(word, 0) for word in words if word in model and word in idf_dict]
        if embeddings:
            return np.mean(embeddings, axis=0)
        else:
            return np.zeros(vector_size)

    # Calculate the embeddings for all targets
    target_vectors = np.array([weighted_average(target) for target in targets])

    # Calculate the embeddings for all job titles
    job_title_vectors = np.array([weighted_average(job_title) for job_title in job_titles])

    # Compute pairwise cosine similarity
    similarity_matrix = cosine_similarity(target_vectors, job_title_vectors)

    # Find the most similar job title for each target
    most_similar_indices = similarity_matrix.argmax(axis=1)
    most_similar_scores = similarity_matrix.max(axis=1)

    # Get the corresponding job titles
    most_similar_job_titles = [job_titles[i] for i in most_similar_indices]

    # Create a DataFrame
    df = pd.DataFrame({
        "Target Job Title": targets,
        "Most Similar Job Title": most_similar_job_titles,
        "Similarity Score": most_similar_scores
    })

    df.to_csv("embeddings-weighted.txt")

    return df

def mapping_embeddings_sbert(targets, job_titles):

    # Filter out None values
    targets = [target for target in targets if target is not None]
    job_titles = [job_title for job_title in job_titles if job_title is not None]

    # Load pre-trained SBERT model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Encode the job titles
    target_vectors = model.encode(targets, convert_to_tensor=True)
    job_title_vectors = model.encode(job_titles, convert_to_tensor=True)
    
    # Compute pairwise cosine similarity
    similarity_matrix = cosine_similarity(target_vectors.cpu(), job_title_vectors.cpu())
    
    # Find the most similar job titles for each target
    top_n = 1  # Number of top matches to retrieve
    top_indices = np.argsort(-similarity_matrix, axis=1)[:, :top_n]
    
    # Compile the results
    results = []
    for idx, target in enumerate(targets):
        similar_jobs = [(job_titles[i], similarity_matrix[idx][i]) for i in top_indices[idx]]
        for job_title, score in similar_jobs:
            results.append({
                "Target Job Title": target,
                "Matched Job Title": job_title,
                "Similarity Score": score
            })
    
    # Create a DataFrame
    df = pd.DataFrame(results)

    df.to_csv("sentence_bert.txt")
    return df

def name_matching():
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

    princeton_positions = get_all_instances("pton_student_outcomes", "Position")
    o_net_titles = get_all_instances("onet_occupation_data", "Title")

    out_cos = mapping_cosine(princeton_positions, o_net_titles)
    out_bow = mapping_bow(princeton_positions, o_net_titles)

    glove_input_file = 'resources/glove.6B.100d.word2vec.txt'
    word_vectors = KeyedVectors.load_word2vec_format(glove_input_file, binary=False)
    out_embeddings = mapping_embeddings(princeton_positions, o_net_titles, word_vectors, 100)
    out_embeddings_weighted = mapping_embeddings_weighted(princeton_positions, o_net_titles, word_vectors, 100)

    out_sbert = mapping_embeddings_sbert(princeton_positions, o_net_titles)

    try:

        # Load DataFrame into PostgreSQL table, replacing if it exists
        out_cos.to_sql("matching_cosine", engine, if_exists='replace', index=False)
        out_bow.to_sql("matching_bow", engine, if_exists='replace', index=False)
        out_embeddings.to_sql("matching_embeddings", engine, if_exists='replace', index=False)
        out_embeddings_weighted.to_sql("matching_embeddings_weighted", engine, if_exists='replace', index=False)
        out_sbert.to_sql("matching_sbert", engine, if_exists='replace', index=False)
        
        print(f"Data loaded successfully.")
    except Exception as e:
        print(f"Error loading data into tables: {e}")


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
    name_matching()
