# Architecture

## System Overview
```
Browser (Vercel)
  └── Next.js 15 App Router (frontend/)
        ├── /              → Landing: Hero, Carousel, Features, SearchTeaser
        ├── /search        → Search: SearchBar, FilterBar, ProductGrid, OutfitStrip
        └── /products/[sku] → Detail: Gallery, ProductInfo, Accordions, CompleteTheLook
              │
              │ fetch (NEXT_PUBLIC_API_URL)
              ▼
FastAPI Backend (backend/)
  └── lifespan: loads ASOSSearchEngine into app.state
  └── /api/v1/
        ├── /search          → search.py router → search_service.search()
        ├── /search/image    → search.py router → search_service.search_by_image()
        ├── /search/similar/{sku} → search_service.get_similar()
        ├── /products/{sku}  → products.py router → search_service.get_product_detail()
        ├── /products/{sku}/outfit → search_service.get_outfit()
        └── /health          → health.py
  └── ASOSSearchEngine (engine/search_engine.py)
        ├── encoder.py      FashionCLIP text+image embeddings
        ├── index.py        FAISS dual-index (image + text), ANN search
        ├── bm25.py         BM25 lexical retrieval
        ├── query_parser.py NLU: gender/category/color/price/style extraction
        ├── nlp.py          Language detection, spell correction
        └── reranker.py     Hybrid score fusion (CLIP 55% + BM25 15% + tags 25% + freshness 5%)
  └── Data: asos_clean.csv / asos_clean.parquet (in-memory Pandas)
  └── Persisted: asos_engine/ (FAISS .bin + .npy embeddings)
```

## Frontend Component Tree
```
layout.tsx (ThemeProvider + Navbar)
  ├── page.tsx (server)
  │     Hero → Marquee → Features → Carousel → SearchTeaser → Footer
  ├── search/page.tsx (client)
  │     SearchBar → FilterBar → ProductGrid → OutfitStrip → Footer
  └── products/[sku]/page.tsx (server, async)
        Gallery + ProductInfo + Accordions (left) | CompleteTheLook x2 (right)
```

## Frontend API Client (lib/api.ts)
Hybrid: `useMock() = !NEXT_PUBLIC_API_URL`. All functions fall back to mock data with simulated delays when no API URL is set.
```
searchProducts()   → POST /api/v1/search
searchByImage()    → POST /api/v1/search/image (multipart)
getProduct()       → GET  /api/v1/products/{sku}
getOutfit()        → GET  /api/v1/products/{sku}/outfit
getSimilar()       → GET  /api/v1/search/similar/{sku}
```

## Backend Data Layer
- `asos_clean.csv` (or `.parquet`) loaded into Pandas DataFrame at startup
- No database — all in-memory
- FAISS indexes and numpy embeddings persisted in `asos_engine/` and loaded on startup if present
- `primary_image_url` column = direct ASOS CDN URLs (images.asos-media.com)
