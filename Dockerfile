# GreenScale Worker Dockerfile
# Owner: P (Platform Engineer)
# Use python:3.9-slim as the base.
# Copy requirements.txt and worker.py.
# Install requirements.
# Set the CMD to run worker.py.

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker.py into the container
COPY worker.py .

# The final command
CMD ["python", "worker.py"]
