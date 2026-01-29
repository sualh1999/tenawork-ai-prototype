import sqlite3
import faiss
import numpy as np
import os
import json
from fastembed import TextEmbedding
from loguru import logger
import time

# --- Configuration ---
DB_FILE = "candidates.db"
FAISS_INDEX_FILE = "candidates.faiss"
MODEL_NAME = "BAAI/bge-small-en-v1.5"

# --- Initialize Model ---
embedding_model = TextEmbedding(model_name=MODEL_NAME)
logger.info(f"Text embedding model '{MODEL_NAME}' initialized.")

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(wipe=True):
    """Initializes the databases. If wipe is True, deletes existing files."""
    start_time = time.time()
    if wipe:
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            logger.warning(f"Removed existing database file: {DB_FILE}")
        if os.path.exists(FAISS_INDEX_FILE):
            os.remove(FAISS_INDEX_FILE)
            logger.warning(f"Removed existing FAISS index file: {FAISS_INDEX_FILE}")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            location TEXT,
            willing_to_travel BOOLEAN,
            phone TEXT,
            email TEXT UNIQUE,
            bio TEXT,
            languages_spoken TEXT,
            education TEXT,
            experience TEXT
        )
    """)
    conn.commit()
    conn.close()
    if wipe:
        logger.info(f"Database initialized and wiped in {time.time() - start_time:.2f} seconds.")
    else:
        logger.info(f"Database connection verified in {time.time() - start_time:.2f} seconds.")


def _deserialize_row(row):
    """Deserializes JSON fields for a single database row."""
    if not row:
        return None
    row_dict = dict(row)
    row_dict['languages_spoken'] = json.loads(row_dict['languages_spoken'] or '[]')
    row_dict['education'] = json.loads(row_dict['education'] or '[]')
    row_dict['experience'] = json.loads(row_dict['experience'] or '[]')
    return row_dict

def get_candidate_count():
    """Returns the total number of candidates in the database."""
    if not os.path.exists(DB_FILE):
        return 0
    conn = get_db_connection()
    cursor = conn.cursor()
    count = cursor.execute("SELECT COUNT(id) FROM candidates").fetchone()[0]
    conn.close()
    return count

def add_candidate_to_db(candidate_data):
    """
    Adds a structured candidate profile to SQLite and their vector to FAISS.
    """
    add_start_time = time.time()

    # 1. Generate a rich text document for embedding
    exp_titles = [exp.get('title', '') for exp in candidate_data.get('experience', [])]
    edu_degrees = [edu.get('degree', '') for edu in candidate_data.get('education', [])]
    
    text_to_embed = (
        f"Bio: {candidate_data.get('bio', '')}. "
        f"Experience titles: {', '.join(exp_titles)}. "
        f"Education: {', '.join(edu_degrees)}. "
        f"Languages: {', '.join(candidate_data.get('languages_spoken', []))}"
    )
    
    embed_start_time = time.time()
    embedding = list(embedding_model.embed([text_to_embed]))[0]
    logger.info(f"Generated embedding for '{candidate_data['full_name']}' in {time.time() - embed_start_time:.4f}s.")

    # 2. Add to SQLite, serializing complex fields
    sql_start_time = time.time()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO candidates (
            full_name, location, willing_to_travel, phone, email, bio, 
            languages_spoken, education, experience
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            candidate_data.get('full_name'), candidate_data.get('location'),
            candidate_data.get('willing_to_travel'), candidate_data.get('phone'),
            candidate_data.get('email'), candidate_data.get('bio'),
            json.dumps(candidate_data.get('languages_spoken', [])),
            json.dumps(candidate_data.get('education', [])),
            json.dumps(candidate_data.get('experience', []))
        )
    )
    candidate_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logger.info(f"Added '{candidate_data['full_name']}' to SQLite with ID {candidate_id} in {time.time() - sql_start_time:.4f}s.")

    # 3. Add to FAISS
    faiss_start_time = time.time()
    dimension = embedding.shape[0]

    if os.path.exists(FAISS_INDEX_FILE):
        index = faiss.read_index(FAISS_INDEX_FILE)
    else:
        index = faiss.IndexFlatL2(dimension)
        index = faiss.IndexIDMap(index)

    index.add_with_ids(np.array([embedding], dtype=np.float32), np.array([candidate_id], dtype=np.int64))
    faiss.write_index(index, FAISS_INDEX_FILE)
    logger.info(f"Added vector for ID {candidate_id} to FAISS in {time.time() - faiss_start_time:.4f}s.")

    logger.success(f"Successfully processed candidate '{candidate_data['full_name']}' in {time.time() - add_start_time:.2f}s.")
    return candidate_id

def search_candidates_from_db(query_text, k=5):
    """
    Finds the top k candidates matching a query text.
    """
    search_start_time = time.time()
    logger.info(f"Starting search for query: '{query_text[:50]}...'")

    if not os.path.exists(FAISS_INDEX_FILE):
        logger.error("FAISS index file not found. Please load sample data first.")
        return []

    # 1. Generate Query Vector
    embed_start_time = time.time()
    query_vector = list(embedding_model.embed([query_text]))[0]
    logger.info(f"Generated query vector in {time.time() - embed_start_time:.4f}s.")

    # 2. Search FAISS
    faiss_start_time = time.time()
    index = faiss.read_index(FAISS_INDEX_FILE)
    _, ids = index.search(np.array([query_vector], dtype=np.float32), k)
    found_ids = [int(i) for i in ids[0] if i != -1] # Filter out -1, which indicates no result
    logger.info(f"FAISS search completed in {time.time() - faiss_start_time:.4f}s. Found {len(found_ids)} matches.")

    if not found_ids:
        return []

    # 3. Retrieve from SQLite and deserialize
    sql_start_time = time.time()
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholders = ','.join(['?'] * len(found_ids))
    query = f"SELECT * FROM candidates WHERE id IN ({placeholders})"
    
    results = cursor.execute(query, found_ids).fetchall()
    
    results_dict = {row['id']: _deserialize_row(row) for row in results}
    ordered_results = [results_dict[id] for id in found_ids if id in results_dict]
    
    conn.close()
    logger.info(f"Retrieved and deserialized {len(ordered_results)} candidates from SQLite in {time.time() - sql_start_time:.4f}s.")

    logger.success(f"Total search operation completed in {time.time() - search_start_time:.2f}s.")
    return ordered_results

def get_candidate_by_id(candidate_id):
    """Fetches a single candidate by ID and deserializes their data."""
    conn = get_db_connection()
    cursor = conn.cursor()
    result = cursor.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
    conn.close()
    return _deserialize_row(result)

def get_filtered_candidate_count(location: str | None, title: str | None, travel: bool | None):
    """Gets the total count of candidates based on filters."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT COUNT(id) FROM candidates"
    where_clauses = []
    params = []

    if location:
        where_clauses.append("location LIKE ?")
        params.append(f"%{location}%")
    if title:
        where_clauses.append("LOWER(experience) LIKE ?")
        params.append(f'%\"title\": \"%{(title or "").lower()}%\"%')
    if travel is not None:
        where_clauses.append("willing_to_travel = ?")
        params.append(travel)

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
        
    count = cursor.execute(query, params).fetchone()[0]
    conn.close()
    return count

def get_all_candidates_paginated_and_filtered(
    location: str | None, title: str | None, travel: bool | None,
    page: int, page_size: int
):
    """Gets all candidates with pagination and filtering."""
    offset = (page - 1) * page_size
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM candidates"
    where_clauses = []
    params = []

    if location:
        where_clauses.append("location LIKE ?")
        params.append(f"%{location}%")
    if title:
        where_clauses.append("LOWER(experience) LIKE ?")
        params.append(f'%\"title\": \"%{(title or "").lower()}%\"%')
    if travel is not None:
        where_clauses.append("willing_to_travel = ?")
        params.append(travel)

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([page_size, offset])

    results = cursor.execute(query, params).fetchall()
    conn.close()
    
    return [_deserialize_row(row) for row in results]


# Ensure DB is created on startup if it doesn't exist.
init_db(wipe=False)
