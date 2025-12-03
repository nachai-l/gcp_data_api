# Dockerfile
#
# Container image for the E-portfolio Data API.
# Runtime: Python 3.12 + FastAPI + Uvicorn.
# Designed for Cloud Run (listens on $PORT, default 8080).

FROM python:3.12-slim

# Avoid Python writing .pyc, keep output unbuffered (better logs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Optional: Cloud Run convention
ENV PORT=8080

WORKDIR /app

# Install system deps (curl, ca-certificates, etc. if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# If you use a service account JSON inside the image, uncomment and adjust:
# ENV GOOGLE_APPLICATION_CREDENTIALS=/app/parameters/keys/cvloader_key.json

# Expose the port for local testing (Cloud Run ignores EXPOSE but it's nice to have)
EXPOSE 8080

# Start FastAPI via Uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
