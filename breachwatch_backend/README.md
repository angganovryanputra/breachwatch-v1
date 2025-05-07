
# BreachWatch Backend

This directory contains the Python backend for the BreachWatch application.
It uses FastAPI for the API, SQLAlchemy for ORM (with PostgreSQL), and is structured for modularity and future expansion.

## Setup & Running with Docker Compose (Recommended for Local Development)

This is the easiest way to get the backend and its PostgreSQL database running locally.

1.  **Prerequisites:**
    *   Docker: [Install Docker](https://docs.docker.com/get-docker/)
    *   Docker Compose: Usually comes with Docker Desktop. If not, [install Docker Compose](https://docs.docker.com/compose/install/).

2.  **Configure Environment Variables:**
    *   Navigate to the `breachwatch_backend` directory.
    *   Copy `.env.example` to `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Review and **edit `breachwatch_backend/.env`**. The defaults are set up for Docker Compose (e.g., `DB_HOST=db`). You typically don't need to change database credentials for local Docker setup unless you have specific needs.
    *   The `OUTPUT_LOCATIONS_DOWNLOADED_FILES` is set to `/app/data/downloaded_files` which, with Docker Compose, will map to `breachwatch_backend/data/downloaded_files` on your host machine.

3.  **Build and Run Services:**
    *   Navigate to the **root directory of the entire project** (the one containing `docker-compose.yml`).
    *   Run the following command:
        ```bash
        docker-compose up --build
        ```
        (or `docker compose up --build` if you are using Docker Compose V2 CLI plugin)
    *   This command will:
        *   Build the Docker image for the backend service (if it doesn't exist or `Dockerfile` changed).
        *   Start the PostgreSQL database container.
        *   Start the backend API container.
    *   The backend API will be available at `http://localhost:8000`.
    *   To run in detached mode (in the background), add the `-d` flag: `docker-compose up --build -d`.

4.  **Accessing Services:**
    *   Backend API: `http://localhost:8000` (e.g., `http://localhost:8000/api/v1/` for API root, `http://localhost:8000/docs` for Swagger UI).
    *   PostgreSQL: The database runs inside Docker. If you need to connect directly (e.g., with pgAdmin or DBeaver), you can uncomment the port mapping for `db` service in `docker-compose.yml` and connect to `localhost` on the specified port (default 5432) using credentials from your `.env` file.

5.  **Stopping Services:**
    *   If running in the foreground, press `Ctrl+C` in the terminal where `docker-compose up` is running.
    *   If running in detached mode, or from another terminal, navigate to the project root and run:
        ```bash
        docker-compose down
        ```
        To also remove volumes (deleting database data): `docker-compose down -v`

## Manual Setup (Without Docker - More Complex)

If you prefer not to use Docker:

1.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup PostgreSQL Database:**
    *   Ensure you have PostgreSQL installed and running.
    *   Create a database and a user for BreachWatch.
    *   Configure environment variables in `breachwatch_backend/.env` (copy from `.env.example`):
        *   Set `DB_USER`, `DB_PASSWORD`, `DB_HOST` (e.g., `localhost`), `DB_PORT`, `DB_NAME` to match your PostgreSQL setup.
        *   Update `OUTPUT_LOCATIONS_DOWNLOADED_FILES` to a suitable path on your local system (e.g., `data/downloaded_files` relative to `breachwatch_backend`).

4.  **Initialize the database tables:**
    The application will attempt to create tables on startup based on SQLAlchemy models.

5.  **Run the development server:**
    ```bash
    uvicorn breachwatch.main:app --reload --host 0.0.0.0 --port 8000
    ```
    The API will typically be available at `http://localhost:8000`.

## Project Structure

(Structure explanation remains the same)
-   `breachwatch/`: Main application package.
    -   `api/`: FastAPI routers, request/response schemas (Pydantic).
    -   `core/`: Core business logic (crawling, file identification, keyword matching, downloading).
    -   `strategies/`: Different crawling strategies (search engine, direct probe, recursive).
    -   `storage/`: Database interaction (SQLAlchemy models, session management), file storage handling.
    -   `tasks/`: Background tasks (e.g., for Celery).
    -   `utils/`: Utility functions (config loading, logging, network helpers).
    -   `main.py`: FastAPI application entry point.
-   `config/`: Configuration files (e.g., `default_config.yml`).
-   `data/`: Directory for local data storage (e.g., downloaded files if `OUTPUT_LOCATIONS_DOWNLOADED_FILES` points here).
-   `tests/`: Unit and integration tests.
-   `requirements.txt`: Python dependencies.
-   `.env`: Environment variables (ignored by Git by default).
-   `Dockerfile`: For building the backend Docker image.

## Running Tests
```bash
pytest
```
(Ensure your environment is set up, especially for integration tests requiring a database).
