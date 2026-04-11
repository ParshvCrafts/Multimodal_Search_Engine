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

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
