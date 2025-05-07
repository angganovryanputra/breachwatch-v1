
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for psycopg2 if needed (psycopg2-binary usually handles this)
# RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's source code from the host to the container.
# This includes the 'breachwatch' package and other files/directories at the root of breachwatch_backend.
COPY . .

# The command to run the application will be specified in docker-compose.yml
# Expose the port the app runs on (optional, as docker-compose handles port mapping)
# EXPOSE 8000
