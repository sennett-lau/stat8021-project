# Flask Backend

A simple Flask backend with a `/healthcheck` endpoint.

## Setup

### Local Setup

1. Create a virtual environment (optional):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python app.py
   ```

The application will run on the port specified in the `.env` file (default: PORT=8021).

### Docker Setup

1. Build the Docker image:
   ```
   docker build -t flask-backend .
   ```

2. Run the Docker container:
   ```
   docker run -p 8021:8021 flask-backend
   ```

The application will be accessible at http://localhost:8021/healthcheck 