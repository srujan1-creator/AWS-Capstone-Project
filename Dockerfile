# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for any potential library needs (like build-essential)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Set environment variables
ENV PORT=8000

# Run the application
# We use uvicorn to start the FastAPI app
# Host 0.0.0.0 is required for containerized environments
CMD uvicorn app:app --host 0.0.0.0 --port $PORT
