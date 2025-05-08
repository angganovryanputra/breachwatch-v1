
#!/bin/bash

# Script to run the BreachWatch application locally (Frontend, Backend, DB, Cache)

# Exit on any error
set -e

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# --- Configuration ---
FRONTEND_PORT="9002"
BACKEND_PORT="8000"
# --- End Configuration ---

echo "=== BreachWatch Local Development Startup Script ==="

# Check for Docker and Docker Compose
echo_status() {
  echo "-----------------------------------------------------"
  echo "$1"
  echo "-----------------------------------------------------"
}

check_docker() {
  echo_status "Checking Docker and Docker Compose..."
  if ! command_exists docker; then
    echo "Error: Docker is not installed. Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
  fi

  if command_exists docker-compose; then
    DOCKER_COMPOSE_CMD="docker-compose"
  elif docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
    echo "Using 'docker compose' (Docker Compose V2 plugin)."
  else
    echo "Error: docker-compose (or 'docker compose' plugin) is not installed. Please install it: https://docs.docker.com/compose/install/"
    exit 1
  fi
  echo "Docker and Docker Compose found."
}

# Check for Node.js and npm (for frontend)
check_node() {
  echo_status "Checking Node.js and npm..."
  if ! command_exists node || ! command_exists npm ; then
    echo "Error: Node.js and/or npm are not installed. Please install them to run the frontend (https://nodejs.org/)."
    exit 1
  fi
  echo "Node.js and npm found."
}

setup_backend_env() {
  echo_status "Setting up Backend Environment..."
  if [ ! -d "breachwatch_backend" ]; then
    echo "Error: breachwatch_backend directory not found in the current location ($(pwd))."
    echo "Please run this script from the project root directory."
    exit 1
  fi

  cd breachwatch_backend || exit
  if [ ! -f .env ]; then
    echo "No .env file found in breachwatch_backend. Copying from .env.example..."
    if [ -f .env.example ]; then
      cp .env.example .env
      echo ".env file created in breachwatch_backend. Defaults are suitable for Docker Compose."
      echo "Review breachwatch_backend/.env if you have specific configuration needs (e.g., SECRET_KEY, REDIS_PASSWORD)."
    else
      echo "Warning: breachwatch_backend/.env.example not found. Please create a .env file manually."
      echo "The backend might not start correctly without it (especially DB connection and SECRET_KEY)."
    fi
  else
    echo "breachwatch_backend/.env file already exists."
  fi

  # Ensure data directory for downloads exists (volume will map this)
  mkdir -p ./data/downloaded_files
  echo "Ensured ./data/downloaded_files directory exists in breachwatch_backend."
  cd .. # Back to project root
}

start_backend_db_cache() {
  echo_status "Starting Backend, Database, and Cache with Docker Compose..."
  echo "This may take a while on the first run as images are downloaded and built."
  # Use -d to run in detached mode. Remove -d to see logs in this terminal.
  ${DOCKER_COMPOSE_CMD} up --build -d

  echo "Backend, Database, and Cache services started (or starting) in detached mode."
  echo "Backend API should be available at http://localhost:${BACKEND_PORT}"
  echo "View backend logs: ${DOCKER_COMPOSE_CMD} logs -f backend"
  echo "View database logs: ${DOCKER_COMPOSE_CMD} logs -f db"
  echo "View cache (Redis) logs: ${DOCKER_COMPOSE_CMD} logs -f redis"
}

start_frontend() {
  echo_status "Setting up and Starting Frontend..."
  # Assuming package.json is in the root. If it's in a 'frontend' subdir, cd into it.
  if [ ! -f "package.json" ]; then
      echo "Error: package.json not found in project root. Cannot start frontend."
      exit 1
  fi

  echo "Installing frontend dependencies (npm install)..."
  npm install

  echo "Starting Frontend development server on port ${FRONTEND_PORT}..."
  # Start in background. To see logs, run 'npm run dev' manually in another terminal.
  (npm run dev > frontend_dev.log 2>&1 &)
  FRONTEND_PID=$! # Capture the PID of the background process

  # Give it a moment to start
  sleep 5

  if ps -p $FRONTEND_PID > /dev/null; then
     echo "Frontend development server started (PID: $FRONTEND_PID). Logs: frontend_dev.log"
  else
     echo "Error starting frontend. Check frontend_dev.log and run 'npm run dev' manually to debug."
  fi
}

cleanup() {
  echo ""
  echo_status "Shutting down services..."
  # Find and kill the frontend process if it was started by this script
  if [ ! -z "$FRONTEND_PID" ] && ps -p $FRONTEND_PID > /dev/null; then
    echo "Stopping frontend development server (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID
    wait $FRONTEND_PID 2>/dev/null # Wait for it to terminate, suppress errors if already gone
  fi

  echo "Stopping backend, database, and cache (docker-compose down)..."
  cd "$(dirname "$0")" # Ensure we are in project root for docker-compose
  ${DOCKER_COMPOSE_CMD} down --remove-orphans # Use --remove-orphans to clean up potential old containers
  echo "Backend, Database, and Cache services stopped."

  echo "Cleanup complete."
  exit 0
}

# Trap Ctrl+C (SIGINT) and call cleanup function
trap cleanup SIGINT

# Main script execution
check_docker
check_node
setup_backend_env
start_backend_db_cache
start_frontend

echo ""
echo_status "Application Setup Complete!"
echo "Frontend running at: http://localhost:${FRONTEND_PORT}"
echo "Backend API running at: http://localhost:${BACKEND_PORT}"
echo "Backend API Docs (Swagger): http://localhost:${BACKEND_PORT}/docs"
echo ""
echo "Press Ctrl+C in this terminal to attempt to stop all services and cleanup."
echo ""

# Keep the script alive so Ctrl+C can be caught for cleanup
# This loop can be improved, but serves the purpose for now
while true; do
  # Check if the frontend process is still running
  if [ ! -z "$FRONTEND_PID" ] && ! ps -p $FRONTEND_PID > /dev/null; then
    echo "Frontend process (PID: $FRONTEND_PID) appears to have stopped."
    FRONTEND_PID="" # Clear PID so cleanup doesn't try to kill it again
    # Optionally, trigger cleanup automatically or just let the user Ctrl+C
    # cleanup
  fi
  sleep 5 # Check every 5 seconds
done
