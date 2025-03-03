# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY pyproject.toml poetry.lock ./

# Install Poetry
RUN pip install poetry

# Install dependencies
RUN poetry install --no-root

# Copy the rest of the application code into the container
COPY smse_backend/ ./smse_backend/
COPY swagger.json ./swagger.json

# Set environment variables
ENV FLASK_APP=smse_backend/app.py
ENV FLASK_ENV=production

# Expose the port the app runs on
EXPOSE 5000

# Run the application with gunicorn
CMD ["poetry", "run", "gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "smse_backend.app:app"]