#!/bin/bash

# ================================================================
# BreachWatch Local Development Startup Script
# ================================================================
# Skrip ini mengotomatiskan penyiapan lingkungan pengembangan lokal
# untuk aplikasi BreachWatch, termasuk:
# - Memeriksa dependensi (Docker, Docker Compose, Node.js, npm)
# - Mengkonfigurasi file .env backend (termasuk SECRET_KEY)
# - Memulai container Backend, Database (PostgreSQL), dan Cache (Redis) menggunakan Docker Compose
# - Menginstal dependensi Frontend (npm install)
# - Memulai server pengembangan Frontend (Next.js)
#
# Cara Penggunaan:
# 1. Pastikan Anda memiliki Docker, Docker Compose, Node.js, dan npm terinstal.
# 2. Jalankan skrip ini dari direktori root proyek BreachWatch:
#    cd /path/to/breachwatch
#    sh run-local.sh
#
# Untuk menghentikan semua layanan, tekan Ctrl+C di terminal ini.
# ================================================================

# Exit on any error
set -e

# --- Configuration ---
FRONTEND_PORT="9002"
BACKEND_PORT="8000"
PROJECT_ROOT=$(pwd) # Asumsikan skrip dijalankan dari root
BACKEND_DIR="${PROJECT_ROOT}/breachwatch_backend"
FRONTEND_DIR="${PROJECT_ROOT}" # Asumsikan frontend ada di root
# --- End Configuration ---

# --- Helper Functions ---
echo_status() {
  echo "-----------------------------------------------------"
  echo ">>> $1"
  echo "-----------------------------------------------------"
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# --- Dependency Checks ---
check_dependencies() {
  echo_status "Checking Dependencies..."

  # Check Docker
  if ! command_exists docker; then
    echo "Error: Docker is not installed. Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
  fi
  echo "Docker found."

  # Check Docker Compose (V1 or V2)
  if command_exists docker-compose; then
    DOCKER_COMPOSE_CMD="docker-compose"
    echo "Using 'docker-compose' (V1)."
  elif docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
    echo "Using 'docker compose' (V2 plugin)."
  else
    echo "Error: docker-compose (or 'docker compose' plugin) is not installed. Please install it: https://docs.docker.com/compose/install/"
    exit 1
  fi
  echo "Docker Compose found."

  # Check Node.js and npm
  if ! command_exists node || ! command_exists npm ; then
    echo "Error: Node.js and/or npm are not installed. Please install them for the frontend (https://nodejs.org/)."
    exit 1
  fi
  echo "Node.js and npm found."

  echo "All dependencies checked."
}

# --- Backend Setup ---
setup_backend_env() {
  echo_status "Setting up Backend Environment (${BACKEND_DIR})..."

  if [ ! -d "${BACKEND_DIR}" ]; then
    echo "Error: Backend directory '${BACKEND_DIR}' not found."
    echo "Please ensure you are running this script from the project root directory that contains 'breachwatch_backend'."
    exit 1
  fi

  local env_file="${BACKEND_DIR}/.env"
  local example_env_file="${BACKEND_DIR}/.env.example"

  if [ ! -f "${env_file}" ]; then
    echo "Backend .env file not found."
    if [ -f "${example_env_file}" ]; then
      echo "Copying from ${example_env_file}..."
      cp "${example_env_file}" "${env_file}"
      echo "Backend .env file created from example."
    else
      echo "Warning: ${example_env_file} not found. Cannot create .env automatically."
      echo "The backend might fail without a properly configured .env file."
      # Consider exiting here if .env is absolutely critical and no example exists
      # exit 1
    fi
  else
    echo "Backend .env file already exists."
  fi

  # Check and generate SECRET_KEY if missing or empty in .env
  if [ -f "${env_file}" ]; then
    if ! grep -q "^SECRET_KEY=" "${env_file}" || grep -q "^SECRET_KEY=\s*$" "${env_file}"; then
       echo "SECRET_KEY is missing or empty in ${env_file}."
       # Remove existing empty/commented line if necessary
       sed -i.bak '/^#*SECRET_KEY=/d' "${env_file}" && rm "${env_file}.bak"
       # Generate a new key
       local new_key=$(openssl rand -hex 32)
       echo "Generating a new SECRET_KEY..."
       echo "" >> "${env_file}" # Add newline for separation
       echo "SECRET_KEY=${new_key}" >> "${env_file}"
       echo "New SECRET_KEY added to ${env_file}."
       echo "Note: For persistent local development, consider setting a fixed SECRET_KEY yourself."
    else
        echo "SECRET_KEY found in ${env_file}."
    fi
  fi

  # Ensure data directory for downloads exists (volume will map this)
  mkdir -p "${BACKEND_DIR}/data/downloaded_files"
  echo "Ensured data/downloaded_files directory exists in backend."
}

# --- Start Services ---
start_docker_services() {
  echo_status "Starting Backend, Database, and Cache with Docker Compose..."
  echo "Building images if necessary (this may take time on first run)..."
  # Use -d to run in detached mode. Remove -d to see logs directly.
  ${DOCKER_COMPOSE_CMD} up --build -d

  echo "Waiting for services to become healthy (this might take a minute)..."
  # Add a simple wait loop for backend health (optional but good practice)
  # This requires the backend to have a health check or a reliable startup message
  # For now, we'll just add a short sleep. Replace with more robust checks if needed.
  sleep 15

  # Verify containers are running
  echo "Checking running containers..."
  ${DOCKER_COMPOSE_CMD} ps

  echo "-----------------------------------------------------"
  echo "Docker services (Backend, DB, Cache) started."
  echo "Backend API should be available at http://localhost:${BACKEND_PORT}"
  echo "View backend logs: ${DOCKER_COMPOSE_CMD} logs -f backend"
  echo "View database logs: ${DOCKER_COMPOSE_CMD} logs -f db"
  echo "View cache (Redis) logs: ${DOCKER_COMPOSE_CMD} logs -f redis"
   echo "-----------------------------------------------------"
}

start_frontend() {
  echo_status "Setting up and Starting Frontend (${FRONTEND_DIR})..."

  if [ ! -f "${FRONTEND_DIR}/package.json" ]; then
      echo "Error: package.json not found in '${FRONTEND_DIR}'. Cannot start frontend."
      exit 1
  fi

  echo "Installing frontend dependencies (npm install)..."
  # Navigate to frontend dir if it's different from root, otherwise stay
  # cd "${FRONTEND_DIR}" || exit
  npm install
  # cd "${PROJECT_ROOT}" # Go back to root if needed

  echo "Starting Frontend development server on port ${FRONTEND_PORT} (Logging to frontend_dev.log)..."
  # Start in background, log output to a file
  (npm run dev -- -p ${FRONTEND_PORT} > frontend_dev.log 2>&1 &)
  FRONTEND_PID=$! # Capture the PID of the background process

  # Give it a moment to potentially start or fail
  sleep 8

  if ps -p $FRONTEND_PID > /dev/null; then
     echo "Frontend development server likely started (PID: $FRONTEND_PID)."
     echo "Frontend should be available at: http://localhost:${FRONTEND_PORT}"
     echo "View frontend logs in: ${PROJECT_ROOT}/frontend_dev.log"
  else
     echo "Error: Frontend process doesn't seem to be running."
     echo "Check logs in ${PROJECT_ROOT}/frontend_dev.log"
     echo "Try running 'npm run dev -- -p ${FRONTEND_PORT}' manually in the '${FRONTEND_DIR}' directory to debug."
     # Optionally exit if frontend start fails critically
     # exit 1
  fi
}

# --- Cleanup Function ---
cleanup() {
  echo ""
  echo_status "Received shutdown signal. Cleaning up..."

  # Find and kill the frontend process if it was started by this script
  if [ ! -z "$FRONTEND_PID" ] && ps -p $FRONTEND_PID > /dev/null; then
    echo "Stopping frontend development server (PID: $FRONTEND_PID)..."
    # Send SIGTERM first, then SIGKILL if it doesn't stop
    kill $FRONTEND_PID || true # Allow failure if already stopped
    sleep 2
    kill -9 $FRONTEND_PID 2>/dev/null || true # Force kill if still running
  else
    echo "Frontend process not found or already stopped."
  fi

  echo "Stopping backend, database, and cache (docker-compose down)..."
  # Ensure we are in project root for docker-compose
  cd "${PROJECT_ROOT}" || echo "Warning: Could not change to project root for docker-compose down."
  ${DOCKER_COMPOSE_CMD} down --remove-orphans # Use --remove-orphans to clean up
  echo "Docker services stopped."

  echo "Cleanup complete. Exiting."
  exit 0
}

# --- Main Execution ---

# Trap Ctrl+C (SIGINT) and script termination (SIGTERM) to call cleanup
trap cleanup SIGINT SIGTERM

echo "=== BreachWatch Local Development Startup ==="
echo "Running script from: ${PROJECT_ROOT}"

check_dependencies
setup_backend_env
start_docker_services
start_frontend

echo ""
echo_status "Application Setup Complete!"
echo "Frontend running at:          http://localhost:${FRONTEND_PORT}"
echo "Backend API running at:       http://localhost:${BACKEND_PORT}"
echo "Backend API Docs (Swagger): http://localhost:${BACKEND_PORT}/docs"
echo ""
echo "View Frontend Logs: tail -f ${PROJECT_ROOT}/frontend_dev.log"
echo "View Backend Logs:  ${DOCKER_COMPOSE_CMD} logs -f backend"
echo ""
echo ">>> Press Ctrl+C in this terminal to stop all services. <<<"
echo ""

# Keep the script alive so Ctrl+C can be caught for cleanup
# This loop prevents the script from exiting immediately after starting background processes.
while true; do
  # Check if docker-compose services are still running (optional check)
  if ! ${DOCKER_COMPOSE_CMD} ps | grep -q 'Up'; then
      echo "Warning: Docker Compose services seem to have stopped unexpectedly."
      # cleanup # Optionally trigger cleanup automatically
      # break # Exit the loop
  fi
   # Check if the frontend process is still running
  if [ ! -z "$FRONTEND_PID" ] && ! ps -p $FRONTEND_PID > /dev/null; then
    echo "Warning: Frontend process (PID: $FRONTEND_PID) appears to have stopped."
    FRONTEND_PID="" # Clear PID
    # cleanup # Optionally trigger cleanup automatically
    # break # Exit the loop
  fi
  sleep 10 # Check every 10 seconds
done
