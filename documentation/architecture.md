# Architecture

## Overview
```
FastAPI App (main.py)
  └── Lifespan: loads engine singleton into app.state
  └── Routers
        ├── /search   → search.py
        ├── /products → products.py
        └── /health   → health.py
  └── Dependencies (dependencies.py)
        └── Injects engine from app.state

Routers → Services (search_service.py) → Engine modules
```

## Engine Modules (`backend/app/engine/`)
| Module | Responsibility |
|---|---|
| `encoder.py` | FashionCLIP text/image embeddings |
| `index.py` | FAISS index: build, save, load, query |
| `bm25.py` | BM25 lexical retrieval |
| `query_parser.py` | NLU: extract gender, category, color, price |
| `nlp.py` | Language detection, spell correction |
| `reranker.py` | Hybrid CLIP + BM25 score fusion |
| `evaluator.py` | Retrieval quality evaluation |

## Data Layer
- `asos_clean.csv` loaded into Pandas DataFrame at startup
- No database — all in-memory for fast prototyping
