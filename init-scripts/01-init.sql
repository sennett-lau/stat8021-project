-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create a table for news articles with vector support
CREATE TABLE IF NOT EXISTS news_articles (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    link TEXT UNIQUE NOT NULL,
    pub_date TIMESTAMP NOT NULL,
    content TEXT NOT NULL,
    embedding vector(384), -- 384-dimension vector, adjust as needed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create an index for vector similarity search
CREATE INDEX ON news_articles USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100); 