# Project Plan

## Phase 1 — Engine Modularization [DONE]
Refactored 2,789-line monolith into `backend/app/engine/`: encoder, index, bm25, query_parser, nlp, reranker, search_engine

## Phase 2 — FastAPI Backend [DONE]
Routers (`/api/v1/search`, `/products`, `/health`), service layer, Pydantic v2 schemas, dependency injection, lifespan engine loading, pytest suite

## Phase 3 — Frontend [DONE — deployed, mock mode]
Next.js 15 App Router, "Noir Editorial" dark/light design system, 3 routes:
- `/` landing: Hero (GSAP stagger), Marquee, Features, Carousel (clone-based), SearchTeaser
- `/search`: SearchBar (text/image/multimodal), FilterBar, ProductGrid (pagination), OutfitStrip
- `/products/[sku]`: Gallery, ProductInfo (sizes/colors/accordion), CompleteTheLook x2
Hybrid API client (mock fallback), theme toggle, Vercel deployment

## Phase 4 — Frontend ↔ Backend Integration [NEXT]
See full plan: `docs/superpowers/plans/2026-04-11-frontend-backend-integration.md`
- Fix schema mismatches in `api.ts` (outfit, similar, product detail field mapping)
- Render real product images from `image_url` in all card components
- Deploy backend, set `NEXT_PUBLIC_API_URL` on Vercel

## Phase 5 — Production Deployment [PLANNED]
- Dockerize backend (`backend/Dockerfile`)
- Deploy to Railway or Render (free tier supports FastAPI)
- Set env vars: `ASOS_DATA_PATH`, `ASOS_PERSISTENT_DIR`, `HF_TOKEN`
- Configure Vercel `NEXT_PUBLIC_API_URL` to point to deployed backend
- End-to-end smoke tests: text search, image upload, product detail, outfit
