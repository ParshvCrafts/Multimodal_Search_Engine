# CLAUDE.md — Agent Context

## Project
Interlace is a multimodal ASOS fashion search engine:
- **Backend**: FastAPI + FashionCLIP + FAISS + BM25 over ~30K products
- **Frontend**: Next.js App Router + TypeScript strict
- **Data**: real ASOS catalog in `asos_clean.csv`

## Read These First
1. `frontend/src/lib/api.ts` — live/mock switch, response adapters
2. `frontend/src/lib/featured-products.ts` — curated landing carousel data
3. `frontend/src/app/search/page.tsx` — search page (empty in live mode)
4. `frontend/src/app/products/[sku]/page.tsx` — product detail + 404
5. `frontend/src/components/landing/Hero.tsx` — hero with main.png support
6. `frontend/src/components/landing/Carousel.tsx` — infinite-loop carousel
7. `backend/app/main.py` — app setup, CORS, lifespan
8. `backend/app/engine/search_engine.py` — core search logic

## Repo Layout
```text
backend/app/
  main.py              app setup + CORS + lifespan
  config.py            env-backed settings
  routers/             search.py, products.py, health.py
  services/            search_service.py (response adapters)
  models/              Pydantic schemas
  engine/              encoder, index, bm25, query_parser, nlp, reranker, search_engine

frontend/src/
  app/
    page.tsx                   landing (Hero + Features + Carousel + SearchTeaser)
    search/page.tsx            search page
    products/[sku]/page.tsx    product detail
    globals.css                CSS variables + keyframes
  components/
    landing/                   Hero, Carousel, Features, Marquee, SearchTeaser
    search/                    SearchBar, ProductGrid, ProductCard, OutfitStrip
    product/                   Gallery, ProductInfo, Accordions, CompleteTheLook
  lib/
    api.ts                     hybrid mock/live client + adapters
    types.ts                   TypeScript interfaces
    featured-products.ts       curated real ASOS products for carousel
    mock-data.ts               demo data (not used in live flows)

frontend/public/
  main.png                     hero brand image (user-provided, optional)

documentation/
  architecture.md, flow.md, plan.md, progress.md, techstack.md, prd.md
```

## Local Run
```bash
# Backend
python -m uvicorn backend.app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm run dev
```

Frontend env (`frontend/.env.local`):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```
**Restart frontend dev server after changing `.env.local`.**

## Current Integration State
- **All live flows use real backend data.** No mock content leaks.
- Landing carousel: 12 curated real ASOS products in `featured-products.ts`
- Hero: loads `/main.png` from public/; shows placeholder if missing
- Search: empty until user query (live mode)
- Product detail: fetches from backend, 404 for unknown SKUs
- Carousel: infinite seamless loop (3x clone strategy), hover-pause, arrow nav

## Key Design Decisions
- ASOS CDN images rendered via raw `<img>` (not `next/image`)
- `NEXT_PUBLIC_API_URL` is compile-time; mock mode when unset
- Carousel uses card-by-card CSS transitions, not continuous scroll
- Hero image: `frontend/public/main.png` (static file, served directly)
- Theme script: native `<script dangerouslySetInnerHTML>` in `<head>` (not `next/script` — React 19 prohibits script nodes in component tree)
- FilterBar dropdowns: React Portal onto `document.body` + `position:fixed` — `overflowX:auto` on the bar would clip `position:absolute` children regardless of z-index
- Filter search: filter values map to natural-language query terms appended after user text query; backend QueryParser extracts them

## Important Data Columns
`sku, name, brand, price, color_clean, color_family, category, gender, primary_image_url, url, style_tags, any_in_stock, sizes_available, product_details, materials`

## What's Working
- Text search, filter search (Gender/Category/Color/Size/Price), filter+text combo
- Grid and list view layouts in search results
- Product detail, outfit recommendations, similar items
- Landing page with real product carousel and hero image
- Light/dark mode toggle
- TypeScript passes: `npx tsc --noEmit`

## What's Pending
- Image upload / multimodal search (backend endpoint exists, UI untested)
- Mobile responsiveness polish
- Deployment
