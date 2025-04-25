#!/bin/bash

# Navigate to the backend directory
cd "$(dirname "$0")/backend"

# Build the Docker image
echo "Building Flask backend Docker image..."
docker build -t flask-backend .

# Run the Docker container
echo "Starting Flask backend container..."
docker run -d -p 8021:8021 --name flask-backend-container flask-backend

echo "Flask backend running at http://localhost:8021" 