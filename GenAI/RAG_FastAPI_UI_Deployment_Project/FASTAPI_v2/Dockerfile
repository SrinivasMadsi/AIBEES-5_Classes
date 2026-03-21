# Base image
FROM mirror.gcr.io/library/python:3.12-slim

# Set working dir
WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy dependencies first
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY medical_app ./medical_app
COPY .env .env

# Expose the default Cloud Run port
EXPOSE 8080

# Run FastAPI using Cloud Run's PORT env variable
CMD ["uvicorn", "medical_app.main:app", "--host", "0.0.0.0", "--port", "8080"]