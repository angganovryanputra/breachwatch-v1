# BreachWatch

This is a Next.js frontend application designed to interact with a Python backend (intended to be built separately) for identifying publicly accessible files potentially related to data breaches for research purposes.

## Features

*   **Dashboard:** View discovered files suspected to be part of a data breach.
*   **Downloaded Files:** See records of files processed by the backend.
*   **Settings:** Configure parameters for new crawl jobs (keywords, extensions, URLs, dorks, depth, scheduling, etc.).
*   **Crawl Jobs:** Monitor the status and results of backend crawl jobs.
*   **Ethical Guidelines:** Important reminders for responsible usage.
*   **User Management:** (Admin only) Manage user roles and statuses.
*   **User Profile:** View profile information and change password.
*   **User Preferences:** Customize application settings like items per page.

## Local Setup (Frontend + Backend Simulation)

This repository contains the Next.js frontend and a conceptual Python backend structure. To run the full application locally with the backend:

1.  **Prerequisites:**
    *   Node.js and npm (or yarn)
    *   Docker and Docker Compose
    *   Python 3.8+ and pip

2.  **Clone the Repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

3.  **Setup Backend (Python/FastAPI):**
    *   Navigate to the `breachwatch_backend` directory (if it exists from previous steps).
    *   Follow the instructions in `breachwatch_backend/README.md` to set up the Python environment, install dependencies (`pip install -r requirements.txt`), and configure the `.env` file (especially `DATABASE_URL`).

4.  **Run Services with Script:**
    *   From the **project root directory**, run the provided shell script:
        ```bash
        sh run-local.sh
        ```
    *   This script attempts to:
        *   Check dependencies (Docker, Node).
        *   Set up the backend `.env` file if missing.
        *   Start the backend (Python API) and PostgreSQL database using `docker-compose up --build -d`.
        *   Install frontend dependencies (`npm install`).
        *   Start the frontend Next.js development server (`npm run dev`) on port 9002.

5.  **Access the Application:**
    *   Frontend: `http://localhost:9002`
    *   Backend API: `http://localhost:8000`
    *   Backend API Docs (Swagger): `http://localhost:8000/docs`

6.  **Stopping:** Press `Ctrl+C` in the terminal where `run-local.sh` is running. This should trigger `docker-compose down` to stop the backend and database. The frontend process might need manual stopping.

## Troubleshooting

*   **NetworkError when fetching resource:** This usually means the frontend cannot connect to the backend API.
    *   **Is the backend running?** Check the terminal where you started the backend (or `docker-compose logs -f backend`) for errors.
    *   **Is the URL correct?** Verify `NEXT_PUBLIC_BACKEND_API_URL` in your frontend environment (e.g., in a `.env.local` file or system variables) matches the backend address (e.g., `http://localhost:8000`).
    *   **CORS?** Ensure the backend's CORS configuration in `breachwatch/main.py` allows requests from your frontend origin (`http://localhost:9002`).
    *   **Network Issues?** Check firewalls or VPNs that might be blocking the connection. Can you access `http://localhost:8000/docs` directly in your browser?
*   **Database Connection Errors:** Check the `DATABASE_URL` in `breachwatch_backend/.env` and ensure the PostgreSQL container (`db`) is running and healthy (`docker ps`).
*   **Frontend Build Errors:** Ensure `npm install` completed successfully. Check the terminal where `npm run dev` is running for specific errors.

## Development

*   **Frontend:** Modify files within the `src` directory. The development server (`npm run dev`) uses Turbopack for fast refreshes.
*   **Backend:** Modify files within the `breachwatch_backend` directory. If using Docker Compose with volumes, changes should reflect automatically due to Uvicorn's `--reload` flag.

## Ethical Considerations

Always use this tool responsibly and ethically. Refer to the **Ethical Guidelines** page within the application. Misuse can lead to serious consequences.
