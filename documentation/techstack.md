# Tech Stack

| Technology | Version | Rationale |
|---|---|---|
| Python | 3.10+ | Type hints, match statements, ecosystem |
| FastAPI | latest | Async, auto OpenAPI docs, Pydantic integration |
| Pydantic v2 | v2 | Fast validation, strict schemas, serialization |
| FashionCLIP | transformers | Fashion-domain CLIP for image+text embeddings |
| PyTorch | latest | FashionCLIP inference backend |
| FAISS | latest | High-speed approximate nearest-neighbor search |
| BM25 (rank-bm25) | latest | Lexical keyword matching for hybrid retrieval |
| spaCy / langdetect | latest | NLP pipeline: NER, language detection |
| TextBlob / pyspellchecker | latest | Spell correction pre-processing |
| Pandas | latest | In-memory CSV data store for product catalog |
| Uvicorn | latest | ASGI server for FastAPI |

## Why Hybrid?
CLIP handles semantic/visual similarity; BM25 handles exact keyword recall. Combined via weighted reranking for best precision + recall.
