# ASOS Multimodal Fashion Search Engine

An intelligent fashion search backend that combines visual and textual understanding to search ASOS product catalogs using FashionCLIP, FAISS, and BM25.

## Features
- Text, image, and multimodal search
- NLU-based attribute extraction (color, gender, category, price)
- Multilingual query support with auto-detection
- Spell correction pre-processing
- Hybrid CLIP + BM25 reranking
- Outfit recommendations
- Graceful metadata filter relaxation

## Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API available at `http://localhost:8000` — docs at `http://localhost:8000/docs`

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/search` | Text / image / multimodal search |
| GET | `/products/{id}` | Product detail by ID |
| GET | `/health` | Service health check |

## Tech Stack
Python 3.10+ · FastAPI · FashionCLIP · FAISS · PyTorch · BM25 · Pydantic v2 · Pandas · Uvicorn

## Project Layout
```
backend/app/
  engine/    # ML core
  routers/   # API routes
  services/  # Business logic
  models/    # Pydantic schemas
documentation/  # Architecture, flow, PRD, plan
```
