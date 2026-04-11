# CLAUDE.md — Agent Context

## Project
Interlace — multimodal fashion search engine. Full-stack: FastAPI backend + Next.js 15 frontend deployed to Vercel. UC Berkeley Fashion x Data Science project using real ASOS catalog data.

## Repo Layout
```
Asos_Engine_Project/
  backend/app/
    main.py            # FastAPI app, lifespan startup, CORS, exception handlers
    config.py          # Settings (env vars) + SearchConfig (ML params, file paths)
    dependencies.py    # get_engine() → injects ASOSSearchEngine from app.state
    exceptions.py      # SKUNotFoundError, InvalidQueryError, EngineNotReadyError
    engine/            # ML core: encoder, index, bm25, query_parser, nlp, reranker, evaluator, search_engine
    routers/           # FastAPI routes: search.py, products.py, health.py
    services/          # search_service.py — bridges routers ↔ engine, row→model adapters
    models/            # Pydantic v2: search.py (SearchRequest/Response/ResultItem/QueryInfo), product.py (ProductDetail/OutfitItem/OutfitResponse/SimilarResponse)
  backend/tests/       # pytest suite (conftest, api, bm25, nlp, query_parser)
  frontend/src/
    app/               # Next.js App Router: page.tsx, search/page.tsx, products/[sku]/page.tsx, layout.tsx, globals.css
    components/        # layout/ (Navbar, Footer), landing/ (Hero, Marquee, Features, Carousel, SearchTeaser), search/ (SearchBar, FilterBar, ProductCard, ProductGrid, OutfitStrip), product/ (Gallery, ProductInfo, Accordions, Breadcrumb, CompleteTheLook)
    lib/               # types.ts, api.ts (hybrid mock/live), mock-data.ts
    context/           # ThemeContext.tsx (dark/light toggle, localStorage persist)
    hooks/             # useTheme.ts
  documentation/       # This folder — agent context, architecture, flow, techstack, progress
  docs/superpowers/    # Implementation plans (plans/) and specs (specs/)
  asos_clean.csv       # Product catalog (in-memory via Pandas, ~10k+ rows)
  asos_engine/         # Persisted FAISS indexes + embeddings (gitignored)
```

## Run Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# Starts on http://localhost:8000
# API docs: http://localhost:8000/docs
```

## Run Frontend
```bash
cd frontend
npm install
npm run dev          # http://localhost:3000
# With live backend:
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## API Base: `/api/v1`
All routes prefixed with `/api/v1`. See `flow.md` for full endpoint reference.

## Key Conventions
- Engine loaded once at startup via lifespan, injected via `get_engine()` dependency
- All ML config in `config.py` — no hardcoded paths elsewhere
- Pydantic v2 for all request/response schemas
- Frontend `api.ts`: `useMock() = !process.env.NEXT_PUBLIC_API_URL` — falls back to rich mock data
- Frontend theme: `.light` class toggled on `document.documentElement`; blocking inline script prevents flash
- No em dashes anywhere in frontend copy

## Schema Mismatches (frontend ↔ backend) — NOT YET FIXED
- `getOutfit()`: backend returns `{ source, outfit: { [category]: OutfitItem[] } }`, frontend `api.ts` expects `{ items: OutfitItem[] }`
- `getSimilar()`: backend returns `SimilarResponse { source, results: SimilarProductItem[], total }`, frontend expects `SearchResponse`; field `similarity_score` vs `score`
- `ProductDetail`: frontend has `available_sizes`, `unavailable_sizes`, `available_colors`; backend returns `sizes_available`, no colors array
- Image placeholders: all product cards show placeholder text instead of actual `image_url`

## Data Columns (asos_clean.csv key fields)
`sku, name, brand, price, color_clean, color_family, category, gender, primary_image_url, url, style_tags, any_in_stock, sizes_available, product_details, materials`
