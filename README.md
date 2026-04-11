# Interlace — Multimodal Fashion Search Engine

A semantic fashion search engine built on FashionCLIP, FAISS, and BM25, with a Next.js frontend. Supports text search, image upload search, and multimodal queries against an ASOS product catalog.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11 | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| npm | 9+ | bundled with Node.js |

---

## Project Structure

```
Asos_Engine_Project/
  backend/          FastAPI backend (ML engine + REST API)
    app/
      engine/       FashionCLIP encoder, FAISS index, BM25, reranker
      routers/      API route handlers
      services/     Search orchestration
      models/       Pydantic schemas
    requirements.txt
    Dockerfile
  frontend/         Next.js 15 App Router frontend
    src/
      app/          Pages (/, /search, /products/[sku])
      components/   UI components
      lib/          API client, types, mock data
  asos_clean.csv    Product catalog (not in repo — required for backend)
  asos_engine/      FAISS indexes + embeddings (auto-generated on first run)
```

---

## Running Locally

There are two modes:

- **Mock mode** — frontend only, uses hardcoded sample products. No backend needed. Good for UI demos.
- **Full stack** — frontend + backend, returns real ASOS search results with images.

---

### Option A: Frontend only (mock mode)

Use this if you just want to demo the UI without running the ML backend.

**Terminal 1:**
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

The app detects that no backend URL is configured and falls back to mock data automatically.

---

### Option B: Full stack (backend + frontend)

Use this for a real demo with live search results.

#### Step 1: Set up the backend

> **Important:** All backend commands must be run from the **project root** (`Asos_Engine_Project/`), not from inside `backend/`. The module imports use the `backend.` prefix and require the project root on the Python path.

**Terminal 1 — install and start the backend:**
```bash
# From Asos_Engine_Project/
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8000
```

> **Windows note:** Use `python -m uvicorn` (not bare `uvicorn`). PowerShell does not automatically add Python's `Scripts/` folder to PATH, so the bare command is not found.

On first run, the engine will build FAISS indexes from `asos_clean.csv`. This takes a few minutes and produces files in `asos_engine/`. Subsequent runs skip this and load directly.

Expected output when ready:
```
Engine ready with 46,000+ products
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Verify it is running:
```bash
curl http://localhost:8000/api/v1/health
# Expected: {"status":"ok","engine_ready":true,"product_count":...}
```

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

#### Step 2: Set up the frontend

**Terminal 2 — configure and start the frontend:**
```bash
cd frontend

# Create local env file pointing to the running backend
# Use printf, not echo -- PowerShell's echo writes UTF-16 which Next.js cannot read
printf 'NEXT_PUBLIC_API_URL=http://localhost:8000\n' > .env.local

npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Data File

`asos_clean.csv` is not stored in this repository (too large for Git). It must be present in the project root for the backend to start. The config auto-detects it:

```
Asos_Engine_Project/
  asos_clean.csv   <-- place it here
```

If you have the `.parquet` version instead (`asos_clean.parquet`), that also works and is preferred (faster to load).

---

## Environment Variables

### Backend

Set via shell environment or a `.env` file in `backend/`:

| Variable | Default | Description |
|----------|---------|-------------|
| `ASOS_DATA_PATH` | auto-detected | Path to `asos_clean.csv` / `.parquet` |
| `ASOS_PERSISTENT_DIR` | `./asos_engine` | Where FAISS indexes are saved |
| `ASOS_LOG_LEVEL` | `INFO` | Logging verbosity |
| `HF_TOKEN` | (none) | HuggingFace token — needed to download FashionCLIP on first run if rate-limited |

### Frontend

Set in `frontend/.env.local` (this file is gitignored):

| Variable | Example | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL. If unset, app uses mock data. |

---

## API Endpoints

All routes are prefixed with `/api/v1`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Engine status and product count |
| POST | `/search` | Text, image (base64), or multimodal search |
| POST | `/search/image` | Image file upload search |
| GET | `/search/similar/{sku}` | Visually similar products |
| GET | `/products/{sku}` | Product detail by SKU |
| GET | `/products/{sku}/outfit` | Outfit recommendations for a product |

---

## Tech Stack

**Backend:** Python 3.11 · FastAPI · FashionCLIP · FAISS · BM25 · PyTorch · Pydantic v2 · Pandas · Uvicorn

**Frontend:** Next.js 15 (App Router) · TypeScript · Tailwind CSS v4 · Framer Motion · GSAP
