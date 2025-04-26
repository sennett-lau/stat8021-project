import os
from data_loader import load_csv_data, load_summaries_json
import psycopg2
from pgvector.psycopg2 import register_vector

def get_db_connection():
    """Connect to the PostgreSQL database server"""
    DB_HOST = os.getenv('POSTGRES_HOST', 'postgres')
    DB_PORT = os.getenv('POSTGRES_PORT', '5432')
    DB_NAME = os.getenv('POSTGRES_DB', 'vectordb')
    DB_USER = os.getenv('POSTGRES_USER', 'postgres')
    DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
    
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    # Enable autocommit to avoid transaction issues
    conn.autocommit = True
    # Register the vector type with psycopg2
    register_vector(conn)
    return conn

def check_table_exists():
    """Check if the news_articles table exists"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'news_articles'
        )
    """)
    exists = cur.fetchone()[0]
    cur.close()
    conn.close()
    return exists

def list_csv_files():
    """List CSV files in the hk_news directory"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    hk_news_dir = os.path.join(base_dir, 'hk_news')
    
    print(f"Current directory: {os.getcwd()}")
    print(f"Script directory: {base_dir}")
    print(f"Looking for CSV files in: {hk_news_dir}")
    
    if os.path.exists(hk_news_dir):
        files = os.listdir(hk_news_dir)
        csv_files = [f for f in files if f.endswith('.csv')]
        print(f"CSV files found: {csv_files}")
        return csv_files
    else:
        print(f"Directory does not exist: {hk_news_dir}")
        return []

if __name__ == "__main__":
    print("Starting data load script...")
    
    # Check if table exists
    if check_table_exists():
        print("Table 'news_articles' exists in the database.")
    else:
        print("ERROR: Table 'news_articles' does not exist in the database!")
        print("Make sure the initialization scripts have run correctly.")
    
    # List available CSV files
    csv_files = list_csv_files()
    if not csv_files:
        print("No CSV files found. Check the directory path.")
    
    # Try to load data
    print("Attempting to load news article data...")
    try:
        load_csv_data()
        print("News article data loading completed.")
    except Exception as e:
        print(f"Error loading news article data: {str(e)}")
    
    # Try to load summaries
    print("Attempting to load summaries data...")
    try:
        load_summaries_json()
        print("Summaries data loading completed.")
    except Exception as e:
        print(f"Error loading summaries data: {str(e)}")
    
    # Check if data was loaded
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM news_articles")
    articles_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM summaries")
    summaries_count = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    print(f"Number of news articles in the database: {articles_count}")
    print(f"Number of summaries in the database: {summaries_count}")
    print("Data loading process completed.") 