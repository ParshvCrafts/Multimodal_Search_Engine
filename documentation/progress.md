# Progress

## Completed
- [x] **Phase 1 — Engine modularization**: Refactored 2,789-line monolith into `backend/app/engine/` modules
- [x] **Phase 2 — FastAPI backend**: Routers, service layer, Pydantic v2, dependency injection, lifespan startup, CORS
- [x] **Backend tests**: pytest suite — API endpoints, query parser, NLP, BM25 (`backend/tests/`)
- [x] **Phase 3 — Frontend**: Next.js 15 App Router, "Noir Editorial" design system, all 3 routes (landing/search/product detail), hybrid mock+live API client, theme toggle, GSAP animations, clone carousel, pagination
- [x] **Frontend deployed**: Live at `https://frontend-ten-phi-njv8fyo6df.vercel.app` (mock mode, no backend connected)
- [x] **Post-review bug fixes**: Carousel busyRef + seamless backward wrap, ProductGrid page reset, ThemeContext flash fix

## In Progress / Blocked
- [ ] **Frontend ↔ Backend integration**: Schema mismatches in `api.ts` + image rendering (see below)
- [ ] **Backend deployment**: Not deployed — no live URL yet

## Known Schema Mismatches (must fix before live integration)
| Issue | Location | Fix |
|---|---|---|
| `getOutfit()` flat vs grouped | `frontend/src/lib/api.ts` | Flatten backend `outfit: {category: items[]}` |
| `getSimilar()` field mismatch | `frontend/src/lib/api.ts` | Map `similarity_score` → `score` |
| `getProduct()` field mismatch | `frontend/src/lib/api.ts` | Map `sizes_available` → `available_sizes` |
| Image placeholders | `ProductCard, Gallery, Carousel, OutfitStrip, CompleteTheLook` | Use `<img src={image_url}>` |

## Next Up
- Phase 4: Fix schema mismatches + render real images (see `docs/superpowers/plans/2026-04-11-frontend-backend-integration.md`)
- Phase 5: Deploy backend to Railway/Render, wire `NEXT_PUBLIC_API_URL` on Vercel

## Stats
- Backend: 12 Python modules, 6 test files
- Frontend: 18 components, 3 routes, 1 context, hybrid API client
- Data: `asos_clean.csv` in project root (gitignored)
- Indexes: `asos_engine/` (gitignored, regenerated on startup)
