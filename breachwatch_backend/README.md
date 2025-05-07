# BreachWatch Backend

This directory contains the Python backend for the BreachWatch application.
It uses FastAPI for the API, SQLAlchemy for ORM (with PostgreSQL), and is structured for modularity and future expansion (e.g., Celery for background tasks).

## Setup

1.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure environment variables:**
    Create a `.env` file in the `breachwatch_backend` root directory (based on `.env.example` if provided) with your database credentials and other settings.
    A common variable will be `DATABASE_URL`, e.g.:
    `DATABASE_URL=postgresql://user:password@host:port/dbname`

4.  **Initialize the database (if using Alembic for migrations, not set up by default here):**
    You might need to run database migrations. (Alembic setup is a further step).
    For now, ensure your PostgreSQL database is running and accessible. Tables will be created by SQLAlchemy on app startup if they don't exist (for simple models).

5.  **Run the development server:**
    ```bash
    uvicorn breachwatch.main:app --reload
    ```
    The API will typically be available at `http://127.0.0.1:8000`.

## Project Structure

-   `breachwatch/`: Main application package.
    -   `api/`: FastAPI routers, request/response schemas (Pydantic).
    -   `core/`: Core business logic (crawling, file identification, keyword matching, downloading).
    -   `strategies/`: Different crawling strategies (search engine, direct probe, recursive).
    -   `storage/`: Database interaction (SQLAlchemy models, session management), file storage handling.
    -   `tasks/`: Background tasks (e.g., for Celery).
    -   `utils/`: Utility functions (config loading, logging, network helpers).
    -   `main.py`: FastAPI application entry point.
-   `config/`: Configuration files (e.g., `default_config.yml`).
-   `data/`: Directory for local data storage (e.g., downloaded files, local DB if not using managed PostgreSQL).
-   `tests/`: Unit and integration tests.
-   `requirements.txt`: Python dependencies.
-   `.env`: Environment variables (ignored by Git).
