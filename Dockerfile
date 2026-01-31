# GreenScale Worker Dockerfile
# Owner: P (Platform Engineer)
# Create a multi-stage Dockerfile for a Python application.
# Base Image: python:3.9-slim
# 1. Install dependencies from requirements.txt.
# 2. Copy worker.py into the container.
# 3. The final command should be: CMD ["python", "worker.py"]

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker.py into the container
COPY src/worker.py .

# The final command
CMD ["python", "worker.py"]
