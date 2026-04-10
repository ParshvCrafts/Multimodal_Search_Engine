# Request Flow

## Text Search Query
```
POST /search  {query: "red floral dress", top_k: 20}
  │
  ├── 1. Language detection (langdetect)
  │       └── Non-English → translate to English
  │
  ├── 2. Spell correction (TextBlob / pyspellchecker)
  │
  ├── 3. NLU parsing (query_parser.py)
  │       └── Extract: gender, category, color, price range, occasion
  │
  ├── 4. CLIP encoding (encoder.py)
  │       └── 5 prompt templates → averaged embedding
  │
  ├── 5. Dual FAISS retrieval (index.py)
  │       └── ~300 candidates from ANN search
  │
  ├── 6. BM25 retrieval (bm25.py)
  │       └── Lexical keyword candidates
  │
  ├── 7. Metadata filtering (search_service.py)
  │       └── Apply NLU filters; relax if < threshold results
  │
  └── 8. Hybrid reranking (reranker.py)
          └── Weighted CLIP score + BM25 score → top-N response
```

## Image Search
Steps 1–3 skipped. Image encoded directly via FashionCLIP vision encoder.
