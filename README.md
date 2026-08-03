# Toolhub Naiyo Backend

A Python backend using FastAPI and PostgreSQL.

## Local Setup (Without Docker)

1. **Prerequisites**
   - Python 3.10+
   - PostgreSQL installed and running locally.

2. **Create Database**
   Ensure your PostgreSQL server is running. It connects by default to a database named `postgres` with user `postgress` and password `password`. You can change this in `database.py` or `.env`.

3. **Install Dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Run the Server**
   ```bash
   uvicorn main:app --reload
   ```

5. **API Documentation**
   Open your browser and navigate to: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
