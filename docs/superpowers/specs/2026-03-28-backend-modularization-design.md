# ASOS Search Engine — Backend Modularization & API Design

## Overview
Split the 2,789-line monolithic `finalized_search_engine_full_script.py` into a production-grade modular FastAPI backend. In-memory CSV data store. No database.

## Tech Stack
- **Runtime:** Python 3.10+
- **Framework:** FastAPI + Uvicorn
- **Validation:** Pydantic v2
- **ML:** FashionCLIP (transformers), FAISS, PyTorch, NumPy, Pandas
- **Testing:** pytest + FastAPI TestClient
- **Logging:** Python stdlib logging (structured)

## Project Structure
```
Asos_Engine_Project/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, lifespan, CORS, exception handlers
│   │   ├── config.py            # SearchConfig dataclass + env-aware path resolution
│   │   ├── exceptions.py        # Custom exception classes
│   │   ├── dependencies.py      # FastAPI dependency injection (get_engine)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── search.py        # SearchRequest, SearchResponse, QueryInfo
│   │   │   └── product.py       # ProductDetail, OutfitResponse, SimilarResponse
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── search.py        # POST /search, POST /search/image, GET /search/similar/{sku}
│   │   │   ├── products.py      # GET /products/{sku}, GET /products/{sku}/outfit
│   │   │   └── health.py        # GET /health, GET /audit
│   │   ├── engine/
│   │   │   ├── __init__.py
│   │   │   ├── encoder.py       # FashionCLIPEncoder
│   │   │   ├── index.py         # DualFAISSIndex
│   │   │   ├── query_parser.py  # ParsedQuery dataclass + QueryParser
│   │   │   ├── bm25.py          # SimpleBM25
│   │   │   ├── nlp.py           # MultilingualHandler + SpellCorrector
│   │   │   ├── reranker.py      # _apply_filters, _relax_and_retry, _hybrid_rerank
│   │   │   ├── search_engine.py # ASOSSearchEngine orchestrator (delegates to above)
│   │   │   └── evaluator.py     # SearchEvaluator + EvalResult
│   │   └── services/
│   │       ├── __init__.py
│   │       └── search_service.py # Bridges routers ↔ engine, handles image decoding
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py          # Fixtures (mock engine, sample data)
│       ├── test_query_parser.py
│       ├── test_nlp.py
│       ├── test_bm25.py
│       ├── test_reranker.py
│       ├── test_api_search.py
│       ├── test_api_products.py
│       └── test_api_health.py
├── data/                         # asos_clean.csv (or symlink)
├── asos_engine/                  # Cached embeddings + FAISS indices
├── documentation/
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Module Responsibilities

### engine/nlp.py
- `MultilingualHandler`: language detection (FR/ES/DE/IT/PT/CJK/Cyrillic/Arabic/Devanagari), dictionary-based fashion term translation
- `SpellCorrector`: Norvig algorithm, catalog-trained vocabulary, fashion term boosting

### engine/encoder.py
- `FashionCLIPEncoder`: load FashionCLIP (fallback to generic CLIP), encode texts (batched), encode images (batched), prompt ensembling (5 templates), multimodal query fusion

### engine/index.py
- `DualFAISSIndex`: build/load/save dual FAISS indices (image + text), search with RRF fusion, auto-select IndexFlatIP vs IndexIVFFlat based on dataset size

### engine/query_parser.py
- `ParsedQuery` dataclass: all extracted intent fields
- `QueryParser`: regex-based NLU extracting category, color, gender, price, size, material, exclusions, style tags

### engine/bm25.py
- `SimpleBM25`: tokenize, fit document frequencies, score candidates

### engine/reranker.py
- `FilterEngine`: apply metadata filters (category, color, gender, price, size, material, exclusions, stock)
- `RelaxationEngine`: progressive filter relaxation (size/material → exclusions → color/gender/stock → price expansion → category)
- `HybridReranker`: weighted scoring (RRF + tag overlap + BM25 + stock + material + price proximity)

### engine/search_engine.py
- `ASOSSearchEngine`: orchestrator that wires together encoder, index, parser, BM25, NLP, reranker. Exposes search(), search_similar(), search_by_image(), complete_the_look(), get_product_detail()

### engine/evaluator.py
- `EvalResult` dataclass, `SearchEvaluator`: Recall@K, Precision@K, MRR, latency

### config.py
- `SearchConfig` dataclass: all model/FAISS/search/path configuration, env-aware path detection (colab/kaggle/local), derived path computation

### exceptions.py
- `EngineNotReadyError` → 503
- `SKUNotFoundError` → 404
- `InvalidQueryError` → 422

### dependencies.py
- `get_engine()`: FastAPI dependency that returns the engine singleton from `app.state`

### services/search_service.py
- Converts between Pydantic models and engine calls
- Handles image decoding (multipart upload → PIL Image)
- Converts DataFrame results → Pydantic response models

## API Endpoints

### POST /api/v1/search
Request: `{ query, top_n?, sort_by?, text_weight?, image_b64? }`
Response: `{ results: [...], query_info: {...}, total: int }`

### POST /api/v1/search/image
Request: multipart form with image file
Response: same as /search

### GET /api/v1/search/similar/{sku}?top_n=10
Response: `{ results: [...], source_product: {...} }`

### GET /api/v1/products/{sku}
Response: full product detail (all metadata + all image URLs)

### GET /api/v1/products/{sku}/outfit?n_per_category=3
Response: `{ source: {...}, outfit: { "Shoes": [...], "Bags": [...] } }`

### POST /api/v1/evaluate
Request: `{ test_queries: [...] }`
Response: evaluation report with aggregate metrics

### GET /api/v1/health
Response: `{ status: "ok", products: 29971, engine_ready: true }`

### GET /api/v1/audit
Response: full engine diagnostics

## Startup Lifecycle
1. FastAPI lifespan context manager
2. Load `SearchConfig` (reads env vars for overrides)
3. `ASOSSearchEngine(config)` → `load_data()` → `build_index()`
4. Store engine in `app.state.engine`
5. Server ready

## Error Handling
- Custom exceptions mapped to HTTP status codes via FastAPI exception handlers
- Global catch-all for unexpected errors → 500 with JSON body
- Request validation errors handled by Pydantic → 422

## Key Refactoring from Monolith
1. Extract filtering/relaxation/reranking from ASOSSearchEngine into reranker.py (~300 lines)
2. Extract NLP (multilingual + spell correction) into nlp.py (~250 lines)
3. Remove all Jupyter/IPython display functions (display_results, display_product_detail, display_outfit) — frontend responsibility
4. Remove demo/test execution code from bottom of script (~360 lines)
5. Add proper `__init__.py` exports for clean imports
6. Replace print() diagnostics with structured logging

## Testing
- Unit: QueryParser (25+ test cases), SpellCorrector, MultilingualHandler, BM25
- Integration: SearchEngine with small fixture data (no model loading in unit tests)
- API: TestClient against all endpoints with mocked engine
