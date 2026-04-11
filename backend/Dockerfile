FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PIL, torch, faiss
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libgomp1 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source (data files are mounted at runtime)
COPY . /app/backend/

ENV PYTHONPATH=/app
ENV ASOS_DATA_PATH=/data/asos_clean.csv
ENV ASOS_PERSISTENT_DIR=/data/asos_engine

# PORT is injected by Render (~10000) and HuggingFace Spaces (7860); falls back to 8000 locally
EXPOSE ${PORT:-8000}

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
