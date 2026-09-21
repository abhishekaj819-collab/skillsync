# ==============================================================================
# SkillSetu FastAPI Multi-Agent LMI Engine Dockerfile
# Base: python:3.11-slim
# Port: 8080 (Cloud Run Standard)
# ==============================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    PYTHONPATH=/app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first for optimal Docker layer caching
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy complete application repository
COPY . /app

# Cloud Run container contract expects port 8080
EXPOSE 8080

# Run from backend directory to resolve relative imports cleanly
WORKDIR /app/backend

# Launch FastAPI server via uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
