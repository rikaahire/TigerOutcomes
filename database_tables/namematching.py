#!/usr/bin/env python
import pandas as pd
import numpy as np
import dotenv
import sqlalchemy
import sqlalchemy.orm
from sqlalchemy import select, distinct
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from gensim.models import KeyedVectors
from sentence_transformers import SentenceTransformer

#-----------------------------------------------------------------------

dotenv.load_dotenv()
DATABASE_URL = 'postgresql://tigeroutcomesdb_x9pf_user:Ewfihh7sXhDfzBS1JX51rem45ebypkqa@dpg-ctb2vm52ng1s73dphqqg-a.ohio-postgres.render.com/tigeroutcomesdb_x9pf'
engine = sqlalchemy.create_engine(DATABASE_URL)

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

#-----------------------------------------------------------------------

def name_matching():
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

if __name__ == '__main__':
    name_matching()
