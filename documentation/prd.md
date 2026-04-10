# Product Requirements Document

## Product
ASOS Multimodal Fashion Search Engine — intelligent search over a fashion product catalog.

## Core Features
- **Text search** — natural language queries ("red floral summer dress")
- **Image search** — upload an image, retrieve visually similar products
- **Multimodal search** — combine text + image inputs
- **Intent parsing (NLU)** — extract attributes: gender, category, color, price range, occasion
- **Outfit recommendations** — suggest complementary items
- **Multilingual support** — detect query language, translate before encoding
- **Spell correction** — fix typos before processing
- **Hybrid ranking** — CLIP semantic score + BM25 lexical score fused

## API Endpoints
- `POST /search` — main search
- `GET /products/{id}` — product detail
- `GET /health` — service health

## Non-Functional Requirements
- Response time < 2s for text queries
- Graceful metadata filter relaxation when results are sparse
- Stateless backend — no user sessions
