# Product Requirements Document

## Product
Interlace — ASOS Multimodal Fashion Search Engine. Intelligent search over a real ASOS fashion catalog using FashionCLIP + FAISS + BM25.

## Core Features
- **Text search** — natural language queries ("red floral summer dress")
- **Image search** — upload a photo, retrieve visually similar products via FashionCLIP vision encoder
- **Multimodal search** — blend text + image embeddings via `text_weight` parameter
- **Intent parsing (NLU)** — extract gender, category, color, price range, style tags, material, size
- **Outfit recommendations** — suggest complementary items grouped by category
- **Similar products** — CLIP-based visual similarity for a given SKU
- **Multilingual support** — detect and translate non-English queries before encoding
- **Spell correction** — fix typos before NLU + CLIP processing
- **Hybrid ranking** — CLIP semantic + BM25 lexical fused via RRF, then reranked

## API Contract (all under `/api/v1`)
```
POST /search                   → SearchResponse
POST /search/image             → SearchResponse
GET  /search/similar/{sku}     → SimilarResponse { source, results, total }
GET  /products/{sku}           → ProductDetail
GET  /products/{sku}/outfit    → OutfitResponse { source, outfit: {category: [items]} }
GET  /health                   → { status, engine_ready, product_count }
```

## Frontend Routes
```
/                 Landing — brand story, featured carousel, search teaser
/search           Search — text/image/multimodal input, results grid, outfit strip
/products/[sku]   Product detail — gallery, info, accordions, "Complete the Look", "You May Also Like"
```

## Non-Functional Requirements
- Backend response < 2s for text queries after warm-up
- Graceful metadata filter relaxation when results sparse
- Stateless backend — no sessions, no auth
- Frontend: dark/light theme, mobile-responsive grid, no flash of unstyled content
- Mock mode when `NEXT_PUBLIC_API_URL` not set (for frontend-only development)
