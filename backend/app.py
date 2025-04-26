from flask import Flask, jsonify
from dotenv import load_dotenv
import os
import psycopg2
from pgvector.psycopg2 import register_vector

# Load environment variables from .env file
load_dotenv()

# Database configuration
DB_HOST = os.getenv('POSTGRES_HOST', 'postgres')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'vectordb')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')

app = Flask(__name__)

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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 