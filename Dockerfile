# Use a multi-stage build to reduce image size

# Builder stage for dependencies
FROM python:3.10-slim AS builder

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install only the core dependencies (without worker group)
RUN poetry install --no-root --without worker

# Final stage
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy the application code
COPY smse_backend/ ./smse_backend/
COPY swagger.json ./swagger.json

# Create directories for uploads and checkpoints
RUN mkdir -p ./tmp/uploads
RUN mkdir -p ./.checkpoints

# Set environment variables
ENV FLASK_APP=smse_backend/app.py
ENV FLASK_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose the port the app runs on
EXPOSE 5000

# Run the application with gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "smse_backend.app:app"]