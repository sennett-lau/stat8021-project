import os
import csv
import psycopg2
from pgvector.psycopg2 import register_vector
import numpy as np
from datetime import datetime
import pandas as pd
from app import get_db_connection
import time
import json

# Global model variable to avoid reloading for each embedding
_model = None

def get_embedding_model():
    """
    Lazily load the embedding model to avoid loading it unnecessarily
    """
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            print("Loading sentence transformer model...")
            # Use a smaller, faster model for demo purposes
            _model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')  # 384 dimensions
            print("Model loaded successfully")
        except ImportError:
            print("WARNING: sentence-transformers not available, falling back to simple embeddings")
            _model = None
    return _model

def create_simple_embedding(text, vector_size=384):
    """
    Creates an embedding for text using a pre-trained model.
    Falls back to simple random embedding if model is not available.
    """
    # Clean and truncate the text (models have input limits)
    if not text or not isinstance(text, str):
        text = "No content available"
    
    # Truncate long texts (most models have a token limit)
    max_chars = 10000
    if len(text) > max_chars:
        text = text[:max_chars]
    
    model = get_embedding_model()
    
    if model:
        try:
            # Get embedding from the model
            embedding = model.encode(text)
            # Format for pgvector: "[x1,x2,x3,...]"
            return "[" + ",".join(str(x) for x in embedding.tolist()) + "]"
        except Exception as e:
            print(f"Error generating embedding: {str(e)}, falling back to simple embedding")
            # Fall back to simple embedding if model fails
    
    # Simple fallback embedding
    print("Using fallback random embedding")
    np.random.seed(hash(text) % 2**32)
    embedding = np.random.rand(vector_size).astype(np.float32)
    embedding = embedding / np.linalg.norm(embedding)
    return "[" + ",".join(str(x) for x in embedding.tolist()) + "]"

def check_data_exists():
    """Check if there's already data in the news_articles table"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM news_articles")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count > 0

def load_csv_data():
    """Load all CSV files if no data exists in the database"""
    if check_data_exists():
        print("Data already exists in the database. Skipping import.")
        return
    
    print("No data found. Starting import process...")
    
    # Get the base directory for more reliable file paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Process each CSV file with absolute paths
    csv_files = {
        'HKFP': os.path.join(base_dir, 'hk_news', 'hkfp_news.csv'),
        'RTHK': os.path.join(base_dir, 'hk_news', 'rthk_news.csv'),
        'SCMP': os.path.join(base_dir, 'hk_news', 'scmp_news.csv')
    }
    
    # Verify files exist
    for source, file_path in csv_files.items():
        if not os.path.exists(file_path):
            print(f"WARNING: File not found: {file_path}")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    total_imported = 0
    
    for source, file_path in csv_files.items():
        imported = import_csv_file(source, file_path, cur)
        total_imported += imported
        
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Import complete. Total records imported: {total_imported}")

def import_csv_file(source_name, file_path, cursor):
    """Import data from a specific CSV file into the database"""
    print(f"Importing {source_name} data from {file_path}...")
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return 0
    
    # Read CSV with pandas to handle any potential encoding issues
    df = pd.read_csv(file_path)
    
    imported_count = 0
    for _, row in df.iterrows():
        try:
            # Get the appropriate content field based on the source
            if source_name == 'HKFP':
                content = row['full_content']
            elif source_name == 'RTHK':
                content = row['full_content']
            elif source_name == 'SCMP':
                content = row['full_paragraphs']
            else:
                content = "No content available"
            
            # Parse date using pub_date_formatted which should be consistently formatted
            try:
                # If pub_date_formatted exists and has time component
                if 'pub_date_formatted' in row and ':' in str(row['pub_date_formatted']):
                    pub_date = datetime.strptime(row['pub_date_formatted'], '%Y-%m-%d %H:%M:%S')
                # If pub_date_formatted exists but is just a date
                elif 'pub_date_formatted' in row:
                    date_str = str(row['pub_date_formatted']).strip()
                    if date_str:
                        try:
                            pub_date = datetime.strptime(date_str, '%Y-%m-%d')
                        except ValueError:
                            # For any other format, just extract year-month-day
                            print(f"Converting non-standard date: {date_str}")
                            pub_date = datetime.now()
                    else:
                        pub_date = datetime.now()
                else:
                    # Fallback to current date if formatted date isn't available
                    pub_date = datetime.now()
                    print(f"Missing pub_date_formatted for {source_name} article: {row['title'][:30]}...")
            except Exception as e:
                print(f"Date parsing error ({source_name}): {e}, using current date")
                pub_date = datetime.now()  # Use current date as fallback
            
            # Create embedding
            embedding = create_simple_embedding(content)
            
            # Insert into database
            cursor.execute("""
                INSERT INTO news_articles (source, title, link, pub_date, content, embedding, is_summarized)
                VALUES (%s, %s, %s, %s, %s, %s::vector, FALSE)
                ON CONFLICT (link) DO NOTHING
            """, (
                source_name, 
                row['title'], 
                row['link'], 
                pub_date, 
                content, 
                embedding
            ))
            
            imported_count += 1
            
            # Print progress every 100 records
            if imported_count % 100 == 0:
                print(f"Imported {imported_count} records from {source_name}...")
                
        except Exception as e:
            print(f"Error importing record from {source_name}: {str(e)}")
            continue
    
    print(f"Completed import of {imported_count} records from {source_name}")
    return imported_count

def check_summaries_exist():
    """Check if there's already data in the summaries table"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM summaries")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count > 0

def load_summaries_json():
    """Load summaries from JSON file if no data exists in the summaries table"""
    if check_summaries_exist():
        print("Summaries already exist in the database. Skipping import.")
        return
    
    print("No summaries found. Starting import process...")
    
    # Get the base directory for more reliable file paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, 'hk_news', 'summaries.json')
    
    if not os.path.exists(json_path):
        print(f"WARNING: Summaries file not found: {json_path}")
        return
    
    # Read JSON file
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            summaries = json.load(f)
    except Exception as e:
        print(f"Error reading summaries JSON file: {str(e)}")
        return
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    imported_count = 0
    
    for summary in summaries:
        try:
            title = summary.get('title', 'No title')
            tldr = summary.get('tldr', [])
            summary_text = summary.get('summary', 'No summary')
            news_articles_ids = summary.get('news_articles_ids', [])
            
            # Extract just the sentences from refs and convert to a text array
            # PostgreSQL expects TEXT[] for refs, not an array of dictionaries
            refs_list = []
            for ref in summary.get('refs', []):
                # Extract the sentence value from each ref dict
                if isinstance(ref, dict) and 'sentence' in ref:
                    refs_list.append(ref['sentence'])
                else:
                    refs_list.append(str(ref))
            
            # Create embedding from summary text
            embedding = create_simple_embedding(summary_text)
            
            # Insert into database
            cur.execute("""
                INSERT INTO summaries (title, tldr, summary, news_articles_ids, refs, embedding)
                VALUES (%s, %s, %s, %s, %s, %s::vector)
            """, (
                title,
                tldr,
                summary_text,
                news_articles_ids,
                refs_list,  # Now this is a simple array of strings
                embedding
            ))
            
            imported_count += 1
            
        except Exception as e:
            print(f"Error importing summary: {str(e)}")
            continue
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Import complete. Total summaries imported: {imported_count}")

if __name__ == "__main__":
    # Can be run directly to load data
    load_csv_data()
    load_summaries_json() 