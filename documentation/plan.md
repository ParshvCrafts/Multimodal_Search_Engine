# Project Plan

## Phase 1 — Engine Modularization [DONE]
- Refactor monolith (`finalized_search_engine_full_script.py`) into modules
- `engine/encoder.py` — FashionCLIP embeddings
- `engine/index.py` — FAISS index management
- `engine/bm25.py` — BM25 lexical retrieval
- `engine/query_parser.py` — NLU attribute extraction
- `engine/nlp.py` — language detection, spell correction
- `engine/reranker.py` — hybrid score fusion

## Phase 2 — FastAPI Backend [DONE]
- Routers, service layer, Pydantic v2 schemas
- Dependency injection, lifespan engine loading
- pytest test suite

## Phase 3 — Frontend [NEXT]
- React or Next.js UI
- Text + image search input
- Product grid results display
- Outfit recommendation panel

## Phase 4 — Deployment [PLANNED]
- Dockerize backend
- Cloud hosting (Render / Railway / AWS)
- CI/CD pipeline
