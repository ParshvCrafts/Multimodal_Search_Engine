# CLAUDE.md — Agent Context

## Project
Multimodal fashion search engine backend for ASOS data. FastAPI + FashionCLIP + FAISS.

## Structure
```
backend/app/
  main.py          # FastAPI app, lifespan startup
  config.py        # Settings (paths, thresholds, model name)
  dependencies.py  # Engine singleton injection
  exceptions.py    # Custom HTTP exceptions
  engine/          # Core ML: encoder, index, bm25, query_parser, nlp, reranker, evaluator
  routers/         # FastAPI routes: search, products, health
  services/        # search_service.py — bridges routers and engine
  models/          # Pydantic schemas: search.py, product.py
backend/tests/     # pytest test suite
```

## Run
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Key Conventions
- Engine loaded once at startup via FastAPI `lifespan`, injected via `dependencies.py`
- All config in `app/config.py` — no hardcoded paths elsewhere
- Pydantic v2 models for all request/response schemas
- Data source: `asos_clean.csv` in project root (in-memory via Pandas)
