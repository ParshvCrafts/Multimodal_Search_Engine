# Tech Stack

## Backend
| Technology | Version | Rationale |
|---|---|---|
| Python | 3.10+ | Type hints, dataclasses, ecosystem |
| FastAPI | latest | Async, auto OpenAPI docs, Pydantic integration |
| Pydantic v2 | v2 | Fast validation, strict schemas |
| FashionCLIP | `patrickjohncyh/fashion-clip` | Fashion-domain CLIP for image+text embeddings |
| PyTorch | latest | FashionCLIP inference |
| FAISS | latest | High-speed ANN search; dual index (image + text) |
| rank-bm25 | latest | Lexical keyword matching |
| spaCy / langdetect | latest | NLP pipeline, language detection |
| TextBlob / pyspellchecker | latest | Spell correction |
| Pandas | latest | In-memory CSV/parquet data store |
| Uvicorn | latest | ASGI server |
| pydantic-settings | latest | Settings from env vars |

## Frontend
| Technology | Version | Rationale |
|---|---|---|
| Next.js | 15 (App Router) | SSR/SSG, file-based routing, `next/image` optimization |
| TypeScript | strict | Type safety across API boundary |
| Tailwind CSS | v4 | Utility-first styles |
| GSAP | latest | Hero text stagger animation |
| Framer Motion | latest | Page transitions (wired, not yet used) |
| Vercel | — | Zero-config Next.js deployment |

## Design System (Noir Editorial)
- Dark default: `--bg-primary: #080808`, `--text-primary: #e8e2d9`, `--accent: #c9a96e`
- Light mode: `.light` class on `<html>`, `--bg-primary: #f5f0e8`, `--accent: #7a5c3a`
- Fonts: Georgia serif (headings), Palatino (body inputs)
- Toggle: 36px circle moon/sun in Navbar; localStorage persisted; blocking inline script prevents flash

## Why Hybrid Retrieval
CLIP handles semantic/visual similarity; BM25 handles exact keyword recall. RRF fusion of dual FAISS indexes (image + text embeddings), then final reranking blends CLIP + BM25 + tag overlap + freshness.
