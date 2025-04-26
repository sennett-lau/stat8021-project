# STAT8021 Project: News Analysis and Summarization System

This project is a full-stack application for analyzing and summarizing Hong Kong news articles using vector embeddings and AI-powered summaries.

## Setup

### Prerequisites
- Docker and Docker Compose installed on your system

### Starting the Services
Please copy `backend/.env.example` as `backend/.env`, place your OpenAI API key to `OPENAI_API_KEY`, then start the entire application stack:

```bash
./start.sh
```

This will:
1. Build and start the Vite frontend on port 8020
2. Build and start the Flask backend on port 8021
3. Start a PostgreSQL database with pgvector extension on port 8022
4. Load pre-crawled news data to the database
5. Load pre-summaries data to the database

## Architecture Overview

### Backend
- Flask API with PostgreSQL/pgvector for vector similarity search
- OpenAI integration for generating intelligent news summaries
- Automated news crawling and extraction from multiple sources
- Vector embedding generation for semantic search

### Frontend
- Vite + React + TypeScript web application
- Tailwind CSS for styling
- Search interface for finding relevant news
- Summary generation and viewing capabilities

## Features

### News Data Collection
- Multi-source news crawler supporting:
  - SCMP (South China Morning Post)
  - HKFP (Hong Kong Free Press)
  - RTHK (Radio Television Hong Kong)
- Automatically extracts and preprocesses news content

### Vector Search
- Semantic search for finding relevant news articles
- Uses embeddings to find similar content
- Multi-faceted search with filtering options

### AI-Powered Summaries
- Generate concise summaries from multiple news articles
- Automatic extraction of key points and TL;DR sections
- Reference tracking to source articles

## API Endpoints

### News Articles
- `GET /api/news` - Retrieve news articles with pagination and filtering
- `POST /api/news/search` - Semantic search for news articles

### Summaries
- `POST /api/summaries` - Generate a new summary from selected articles
- `GET /api/summaries` - Retrieve existing summaries
- `GET /api/summaries/<id>` - Get a specific summary
- `POST /api/summaries/search` - Search for relevant summaries

## Data Management

### Update News Data
We retrieve the data from RSS api from:
- SCMP
- HKFP
- RTHK

Run the following command should get the latest news and the data will be stored in csv.

```bash
python data_extraction.py
```

### Database Connection

To connect to the PostgreSQL database directly:

```bash
psql -h localhost -p 8022 -U postgres -d vectordb
```

Default credentials: `postgres/postgres`

## Development

### Environment Variables
The backend uses `.env` file for configuration. See `.env.example` for available options.

### Database Schema
- `news_articles` - Stores news articles with vector embeddings
- `summaries` - Stores AI-generated summaries with references to articles