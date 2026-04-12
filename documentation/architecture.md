# Architecture

## System Overview
```text
Browser
  -> Next.js App Router (frontend/)
     /                  landing: Hero + Marquee + Features + Carousel + SearchTeaser
     /search            client page, live or mock via NEXT_PUBLIC_API_URL
     /products/[sku]    server page, fetches product/outfit/similar
        |
        v
FastAPI (backend/app/)
  main.py              app setup, lifespan engine load, CORS
  routers/search.py    /search, /search/image, /search/similar/{sku}
  routers/products.py  /products/{sku}, /products/{sku}/outfit
  services/search_service.py
                       DataFrame/dict -> Pydantic response adapters
  engine/search_engine.py
                       FashionCLIP + dual FAISS + BM25 + reranking
```

## Runtime
- Backend: `http://localhost:8000` (uvicorn)
- Frontend: `http://localhost:3000` (next dev)
- API prefix: `/api/v1`
- Live/mock switch: `NEXT_PUBLIC_API_URL` env var (compile-time)

## Backend Data Layer
- Catalog: `asos_clean.csv` (~30K products)
- No database; Pandas in-memory
- Persistent: `asos_engine/` FAISS indexes + embeddings
- Images: `primary_image_url` from `images.asos-media.com` CDN

## Frontend File Ownership

### Integration Layer
- `frontend/src/lib/api.ts` — hybrid mock/live client + response adapters
- `frontend/src/lib/types.ts` — TypeScript interfaces for API shapes
- `frontend/src/lib/featured-products.ts` — curated real ASOS products for landing carousel
- `frontend/src/lib/mock-data.ts` — demo-only data (not used in live flows)

### Pages
- `frontend/src/app/page.tsx` — landing (Hero, Features, Carousel, SearchTeaser)
- `frontend/src/app/search/page.tsx` — search (empty in live mode until query)
- `frontend/src/app/products/[sku]/page.tsx` — product detail + 404

### Landing Components
- `frontend/src/components/landing/Hero.tsx` — loads `/main.png` from public/, fallback placeholder
- `frontend/src/components/landing/Carousel.tsx` — infinite loop carousel with real ASOS products
- `frontend/src/components/landing/Features.tsx` — 4 feature cards
- `frontend/src/components/landing/Marquee.tsx` — scrolling tech labels
- `frontend/src/components/landing/SearchTeaser.tsx` — search CTA with inline form

### Product/Search Components
- `frontend/src/components/search/SearchBar` — text+image input, mode indicator (text/image/multimodal)
- `frontend/src/components/search/FilterBar` — 5 filter dimensions; dropdowns via React Portal onto `document.body` (escapes scroll-container clipping); filter terms build natural-language queries for the backend QueryParser
- `frontend/src/components/search/ProductCard` — dual layout: `view='grid'` (3/4 aspect image card) / `view='list'` (horizontal row: image left, details centre, price right)
- `frontend/src/components/search/ProductGrid` — pagination tabs, passes `view` to ProductCard, 0-gap for list mode
- `frontend/src/components/product/` — Gallery, ProductInfo, Accordions, CompleteTheLook

## Design System
- CSS vars defined in `frontend/src/app/globals.css`
- Dark mode default (`.light` class for light mode)
- Serif-led typography (Georgia), accent color `#c9a96e`
- Raw `<img>` tags for ASOS CDN images (not `next/image`)

## Integration State
- All live search/product flows use real backend data
- Landing page carousel uses curated real ASOS products (not mock)
- Hero image: user places `main.png` in `frontend/public/`
- No mock content leaks into live search or product detail flows
