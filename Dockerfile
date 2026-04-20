FROM python:3.11-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . /app/

# Port used by Fly
EXPOSE 8000

# Start fastapi
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
