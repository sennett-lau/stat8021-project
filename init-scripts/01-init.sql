-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create a sample table with vector support
CREATE TABLE IF NOT EXISTS embeddings (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(384) -- 384-dimension vector, adjust as needed
);

-- Create an index for vector similarity search
CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100); 