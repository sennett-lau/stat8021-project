from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
import psycopg2
from pgvector.psycopg2 import register_vector
import numpy as np
import threading

# Load environment variables from .env file
load_dotenv()

# Database configuration
DB_HOST = os.getenv('POSTGRES_HOST', 'postgres')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'vectordb')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')

app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app, resources={r"/*": {"origins": "*"}})

def get_db_connection():
    """Connect to the PostgreSQL database server"""
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

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    try:
        # Test database connection
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return jsonify({"status": "ok", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "ok", "database": "error", "message": str(e)})

@app.route('/api/news', methods=['GET'])
def get_news():
    # Get query parameters
    source = request.args.get('source')
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Construct the query based on parameters
        query = "SELECT id, source, title, link, pub_date, content FROM news_articles"
        params = []
        
        if source:
            query += " WHERE source = %s"
            params.append(source)
            
        query += " ORDER BY pub_date DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        # Get total count for pagination
        count_query = "SELECT COUNT(*) FROM news_articles"
        if source:
            count_query += " WHERE source = %s"
            cur.execute(count_query, [source])
        else:
            cur.execute(count_query)
        total_count = cur.fetchone()[0]
        
        # Format results
        articles = []
        for row in rows:
            articles.append({
                "id": row[0],
                "source": row[1],
                "title": row[2],
                "link": row[3],
                "pub_date": row[4].isoformat() if row[4] else None,
                "content": row[5]
            })
        
        cur.close()
        conn.close()
        
        return jsonify({
            "total": total_count,
            "offset": offset,
            "limit": limit,
            "articles": articles
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/news/search', methods=['POST'])
def search_news():
    # Get search parameters from request body
    search_data = request.get_json()
    
    if not search_data:
        return jsonify({"error": "Search data is required"}), 400
        
    query = search_data.get('q', '')
    source = search_data.get('source')
    limit = int(search_data.get('limit', 10))
    
    if not query:
        return jsonify({"error": "Search query is required"}), 400
    
    try:
        from data_loader import create_simple_embedding
        
        # Create embedding from search query
        embedding = create_simple_embedding(query)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Construct the query based on parameters
        sql_query = """
            SELECT id, source, title, link, pub_date, content, 
                   embedding <=> %s::vector as distance
            FROM news_articles
        """
        params = [str(embedding)]  # Convert to string format for pgvector
        
        if source:
            sql_query += " WHERE source = %s"
            params.append(source)
            
        sql_query += " ORDER BY distance LIMIT %s"
        params.append(limit)
        
        cur.execute(sql_query, params)
        rows = cur.fetchall()
        
        # Format results
        articles = []
        for row in rows:
            articles.append({
                "id": row[0],
                "source": row[1],
                "title": row[2],
                "link": row[3],
                "pub_date": row[4].isoformat() if row[4] else None,
                "content": row[5],
                "similarity": 1 - row[6]  # Convert distance to similarity
            })
        
        cur.close()
        conn.close()
        
        return jsonify({
            "query": query,
            "articles": articles
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/summaries', methods=['POST'])
def create_summary():
    """Create a summary from a list of news article IDs"""
    # Get article IDs from request body
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Request data is required"}), 400
        
    article_ids = data.get('article_ids', [])
    
    if not article_ids:
        return jsonify({"error": "Article IDs are required"}), 400
    
    try:
        from summarize import summarize_news_articles
        
        # Generate summary for the provided articles
        result = summarize_news_articles(article_ids)
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 400
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/summaries', methods=['GET'])
def get_summaries():
    """Get all summaries or search for summaries by similarity"""
    # Get query parameters
    query = request.args.get('q')
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if query:
            # Search by similarity
            from data_loader import create_simple_embedding
            
            # Create embedding from search query
            embedding = create_simple_embedding(query)
            
            # Search by vector similarity
            sql_query = """
                SELECT id, title, tldr, summary, news_articles_ids, created_at,
                       embedding <=> %s::vector as distance
                FROM summaries
                ORDER BY distance
                LIMIT %s OFFSET %s
            """
            cur.execute(sql_query, (str(embedding), limit, offset))
        else:
            # Get all summaries
            sql_query = """
                SELECT id, title, tldr, summary, news_articles_ids, created_at
                FROM summaries
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            cur.execute(sql_query, (limit, offset))
        
        rows = cur.fetchall()
        
        # Get total count for pagination
        cur.execute("SELECT COUNT(*) FROM summaries")
        total_count = cur.fetchone()[0]
        
        # Format results
        summaries = []
        for row in rows:
            summary_data = {
                "id": row[0],
                "title": row[1],
                "tldr": row[2],
                "summary": row[3],
                "news_articles_ids": row[4],
                "created_at": row[5].isoformat() if row[5] else None
            }
            
            # Add similarity if search query was provided
            if query and len(row) > 6:
                summary_data["similarity"] = 1 - row[6]  # Convert distance to similarity
                
            summaries.append(summary_data)
        
        cur.close()
        conn.close()
        
        return jsonify({
            "total": total_count,
            "offset": offset,
            "limit": limit,
            "summaries": summaries
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/summaries/<int:summary_id>', methods=['GET'])
def get_summary(summary_id):
    """Get a specific summary by ID"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get the summary
        cur.execute("""
            SELECT id, title, tldr, summary, news_articles_ids, created_at
            FROM summaries
            WHERE id = %s
        """, (summary_id,))
        
        row = cur.fetchone()
        
        if not row:
            cur.close()
            conn.close()
            return jsonify({"error": "Summary not found"}), 404
        
        # Format result
        summary_data = {
            "id": row[0],
            "title": row[1],
            "tldr": row[2],
            "summary": row[3],
            "news_articles_ids": row[4],
            "created_at": row[5].isoformat() if row[5] else None
        }
        
        cur.close()
        conn.close()
        
        return jsonify(summary_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def load_data_async():
    """Load data asynchronously on startup"""
    try:
        from data_loader import load_csv_data
        load_csv_data()
    except Exception as e:
        print(f"Error loading data: {str(e)}")

if __name__ == '__main__':
    # Start data loading in a background thread
    threading.Thread(target=load_data_async).start()
    
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 