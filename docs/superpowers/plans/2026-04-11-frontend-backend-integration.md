# Frontend ↔ Backend Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the live Next.js frontend to the FastAPI backend — fix all API schema mismatches, render real product images, deploy the backend, and wire the Vercel env var so the full end-to-end flow works.

**Architecture:** Frontend's `api.ts` uses a hybrid mock/live pattern gated on `NEXT_PUBLIC_API_URL`. Three schema mismatches need adapters in `api.ts`, five component files need `<img>` rendering, and one `next.config.ts` domain allowlist is already in place.

**Tech Stack:** Next.js 15, TypeScript, FastAPI, Railway/Render (backend hosting), Vercel (frontend hosting)

---

## File Map

| File | Change |
|------|--------|
| `frontend/src/lib/api.ts` | Fix `getOutfit()`, `getSimilar()`, `getProduct()` live paths |
| `frontend/src/lib/types.ts` | Align `OutfitResponse`, add `SimilarResponse` type |
| `frontend/src/components/search/ProductCard.tsx` | Render `image_url` |
| `frontend/src/components/search/OutfitStrip.tsx` | Render `image_url` |
| `frontend/src/components/landing/Carousel.tsx` | Render `image_url` on real product cards |
| `frontend/src/components/product/Gallery.tsx` | Render `image_url` + `image_urls` |
| `frontend/src/components/product/CompleteTheLook.tsx` | Render `image_url` |
| `backend/Dockerfile` | New — containerize backend |
| `frontend/vercel.json` | Already exists, no change needed |

---

### Task 1: Fix `api.ts` — align all live response adapters

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/lib/types.ts`

**Context:**
- `getOutfit(sku)` hits `GET /api/v1/products/{sku}/outfit` which returns `{ source: ProductDetail, outfit: { [category: string]: OutfitItem[] } }`. Frontend expects `{ items: OutfitItem[] }`.
- `getSimilar(sku)` hits `GET /api/v1/search/similar/{sku}` which returns `{ source: ProductDetail, results: SimilarProductItem[], total }` where `SimilarProductItem` has `similarity_score` (not `score`). Frontend expects `SearchResponse`.
- `getProduct(sku)` hits `GET /api/v1/products/{sku}` which returns `sizes_available: string[]`. Frontend `ProductDetail` type expects `available_sizes`, `unavailable_sizes`, `available_colors`.

- [ ] **Step 1: Update `types.ts` — fix `OutfitResponse` and add `SimilarResponse`**

```typescript
// Replace the existing OutfitItem and OutfitResponse interfaces with:
export interface OutfitItem {
  sku: string
  name: string
  brand: string
  price: number
  color_family: string
  category: string
  image_url: string
  outfit_score?: number
}

export interface OutfitResponse {
  items: OutfitItem[]  // frontend-normalized flat list
}
```

- [ ] **Step 2: Update `getOutfit()` live path in `api.ts`**

Replace the live branch of `getOutfit()`:
```typescript
export async function getOutfit(sku: string): Promise<OutfitResponse> {
  if (useMock()) {
    await new Promise(r => setTimeout(r, 300))
    return {
      items: MOCK_OUTFIT_ITEMS.map(p => ({
        sku: p.sku, name: p.name, brand: p.brand,
        price: p.price, category: p.category, image_url: p.image_url,
        color_family: '',
      })),
    }
  }
  const res = await fetch(`${BASE}/api/v1/products/${sku}/outfit`)
  if (!res.ok) throw new Error(`Outfit failed: ${sku}`)
  const raw = await res.json()
  // Backend returns { source, outfit: { [category]: OutfitItem[] } }
  // Flatten to a single list
  const items: OutfitItem[] = Object.values(
    raw.outfit as Record<string, OutfitItem[]>
  ).flat()
  return { items }
}
```

- [ ] **Step 3: Update `getSimilar()` live path in `api.ts`**

Replace the live branch of `getSimilar()`:
```typescript
export async function getSimilar(sku: string, topN = 5): Promise<SearchResponse> {
  if (useMock()) {
    await new Promise(r => setTimeout(r, 350))
    return {
      results: MOCK_RELATED,
      query_info: { ...EMPTY_QUERY_INFO },
      total: MOCK_RELATED.length,
    }
  }
  const res = await fetch(`${BASE}/api/v1/search/similar/${sku}?top_n=${topN}`)
  if (!res.ok) throw new Error(`Similar failed: ${sku}`)
  const raw = await res.json()
  // Backend returns SimilarResponse { source, results: SimilarProductItem[], total }
  // SimilarProductItem has similarity_score, not score
  const results: SearchResultItem[] = raw.results.map((item: {
    sku: string; name: string; brand: string; price: number;
    color: string; category: string; image_url: string; similarity_score: number;
  }) => ({
    sku: item.sku,
    name: item.name,
    brand: item.brand,
    price: item.price,
    color: item.color,
    color_family: '',
    category: item.category,
    gender: '',
    image_url: item.image_url,
    score: item.similarity_score,
    style_tags: [],
    in_stock: true,
  }))
  return { results, query_info: { ...EMPTY_QUERY_INFO }, total: raw.total }
}
```

- [ ] **Step 4: Update `getProduct()` live path in `api.ts`**

Replace the live branch of `getProduct()`:
```typescript
export async function getProduct(sku: string): Promise<ProductDetail> {
  if (useMock()) {
    await new Promise(r => setTimeout(r, 200))
    return { ...MOCK_PRODUCT_DETAIL, sku }
  }
  const res = await fetch(`${BASE}/api/v1/products/${sku}`)
  if (!res.ok) throw new Error(`Product not found: ${sku}`)
  const raw = await res.json()
  // Backend returns sizes_available, no available_colors array
  return {
    ...raw,
    available_sizes: raw.sizes_available ?? [],
    unavailable_sizes: [],
    available_colors: raw.color
      ? [{ name: raw.color, hex: '' }]
      : [],
  }
}
```

- [ ] **Step 5: Run TypeScript check**
```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors

- [ ] **Step 6: Commit**
```bash
git add frontend/src/lib/api.ts frontend/src/lib/types.ts
git commit -m "fix: align api.ts adapters with backend response shapes"
```

---

### Task 2: Render real images in ProductCard and OutfitStrip

**Files:**
- Modify: `frontend/src/components/search/ProductCard.tsx`
- Modify: `frontend/src/components/search/OutfitStrip.tsx`

**Context:** Both components currently show a `<div>` placeholder with the text "Image". They receive `product.image_url` / `item.image_url` which are ASOS CDN URLs. `next.config.ts` already allows `images.asos-media.com`. Use a plain `<img>` tag (not `next/image`) to avoid needing `width`/`height` props — use `object-fit: cover` and the existing `aspectRatio: '3/4'` container.

- [ ] **Step 1: Replace image placeholder in `ProductCard.tsx`**

Read `frontend/src/components/search/ProductCard.tsx` first, then replace the image `<div>` block:
```tsx
{/* Replace the inner div that shows "Image" text with: */}
{product.image_url ? (
  <img
    src={product.image_url}
    alt={product.name}
    style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
  />
) : (
  <span style={{ fontSize: '10px', letterSpacing: '0.18em', color: '#222', textTransform: 'uppercase' }}>
    No Image
  </span>
)}
```

- [ ] **Step 2: Replace image placeholder in `OutfitStrip.tsx`**

Replace the inner span that shows "Image" text:
```tsx
{item.image_url ? (
  <img
    src={item.image_url}
    alt={item.name}
    style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
  />
) : (
  <span style={{ fontSize: '10px', letterSpacing: '0.18em', color: '#222', textTransform: 'uppercase' }}>No Image</span>
)}
```

- [ ] **Step 3: Commit**
```bash
git add frontend/src/components/search/ProductCard.tsx frontend/src/components/search/OutfitStrip.tsx
git commit -m "feat: render real product images in ProductCard and OutfitStrip"
```

---

### Task 3: Render real images in Gallery and CompleteTheLook

**Files:**
- Modify: `frontend/src/components/product/Gallery.tsx`
- Modify: `frontend/src/components/product/CompleteTheLook.tsx`

**Context:**
- `Gallery.tsx` shows the product's `image_url` (primary) and `image_urls[]` (thumbnails). Main image is 86% width aspectRatio 3/4. Thumbnails are 92px wide.
- `CompleteTheLook.tsx` accepts `OutfitItem | SearchResultItem` and shows items in a 5-column grid. Each item has `image_url`.

- [ ] **Step 1: Read `Gallery.tsx`**
Read `frontend/src/components/product/Gallery.tsx` to see exact placeholder structure.

- [ ] **Step 2: Replace main image placeholder in Gallery**

The main image container currently shows a placeholder. Replace it with:
```tsx
{/* Inside the main image container div */}
{product.image_url ? (
  <img
    src={product.image_url}
    alt={product.name}
    style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
  />
) : (
  <span style={{ fontSize: '11px', letterSpacing: '0.18em', color: '#2a2a2a', textTransform: 'uppercase' }}>No Image</span>
)}
```

- [ ] **Step 3: Replace thumbnail placeholders in Gallery**

Thumbnails map over `(product.image_urls?.length ? product.image_urls : [product.image_url])`. Replace each thumbnail `<div>` placeholder with:
```tsx
{url ? (
  <img src={url} alt={`${product.name} view ${i + 1}`}
    style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
) : null}
```

- [ ] **Step 4: Replace image placeholder in CompleteTheLook**

Read `frontend/src/components/product/CompleteTheLook.tsx`, then replace the image placeholder with:
```tsx
{item.image_url ? (
  <img src={item.image_url} alt={item.name}
    style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
) : (
  <span style={{ fontSize: '10px', letterSpacing: '0.18em', color: '#222', textTransform: 'uppercase' }}>No Image</span>
)}
```

- [ ] **Step 5: Run TypeScript check**
```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors

- [ ] **Step 6: Commit**
```bash
git add frontend/src/components/product/Gallery.tsx frontend/src/components/product/CompleteTheLook.tsx
git commit -m "feat: render real product images in Gallery and CompleteTheLook"
```

---

### Task 4: Render images in landing Carousel

**Files:**
- Modify: `frontend/src/components/landing/Carousel.tsx`

**Context:** Carousel uses `REAL_CARDS` (first 6 of MOCK_PRODUCTS) for card data in mock mode. When live, the carousel is static (it always uses MOCK_PRODUCTS — it's a featured display, not search results). The mock products in `mock-data.ts` have `image_url` fields. Replace the placeholder with an `<img>` tag.

- [ ] **Step 1: Replace image placeholder in Carousel**

Find the `<div>` that shows "Product Image" placeholder text and replace with:
```tsx
{card.image_url ? (
  <img
    src={card.image_url}
    alt={card.name}
    style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
  />
) : (
  <span style={{ fontSize: '11px', letterSpacing: '0.2em', color: '#2a2a2a', textTransform: 'uppercase' }}>
    Product Image
  </span>
)}
```

- [ ] **Step 2: Commit**
```bash
git add frontend/src/components/landing/Carousel.tsx
git commit -m "feat: render product images in landing carousel"
```

---

### Task 5: Dockerize backend

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/.dockerignore`

**Context:** Backend runs with `uvicorn app.main:app`. It loads `asos_clean.csv` from the project root at startup (path auto-detected by `config.py`). For Docker, the CSV must be available at a known path — mount it as a volume or bake it in (the file is large). Use a volume mount approach so the image stays lean.

- [ ] **Step 1: Create `backend/Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PIL, torch, faiss
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libgomp1 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source (data files are mounted at runtime)
COPY . /app/backend/

ENV PYTHONPATH=/app
ENV ASOS_DATA_PATH=/data/asos_clean.csv
ENV ASOS_PERSISTENT_DIR=/data/asos_engine

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create `backend/.dockerignore`**

```
__pycache__
*.pyc
.pytest_cache
tests/
*.npy
*.bin
```

- [ ] **Step 3: Test build locally**
```bash
cd backend
docker build -t interlace-backend .
```
Expected: build succeeds (may take a few minutes for torch + faiss)

- [ ] **Step 4: Commit**
```bash
git add backend/Dockerfile backend/.dockerignore
git commit -m "feat: add Dockerfile for backend deployment"
```

---

### Task 6: Deploy backend to Railway + wire Vercel

**Context:** Railway is the recommended deployment target. It supports Docker deployments, free tier with 500hr/month, automatic HTTPS, and environment variable injection. Alternatively use Render (free tier but spins down after 15min inactivity — bad for ML models).

- [ ] **Step 1: Deploy to Railway**
1. Go to `railway.app` → New Project → Deploy from GitHub repo
2. Select the repo, set root directory to `backend/`
3. Railway auto-detects Dockerfile
4. Set environment variables in Railway dashboard:
   - `ASOS_DATA_PATH=/data/asos_clean.csv` (if mounting volume) OR upload CSV and set path
   - `ASOS_PERSISTENT_DIR=/data/asos_engine`
   - `HF_TOKEN=<your_huggingface_token>` (needed for FashionCLIP download on first run)
   - `ASOS_LOG_LEVEL=INFO`
5. Add a persistent volume at `/data` for the CSV and FAISS indexes
6. Upload `asos_clean.csv` to the Railway volume via their dashboard or CLI

- [ ] **Step 2: Get backend URL**
After deploy, Railway gives a URL like `https://interlace-backend.up.railway.app`
Verify: `curl https://interlace-backend.up.railway.app/api/v1/health`
Expected: `{"status":"ok","engine_ready":true,"product_count":...}`

- [ ] **Step 3: Set `NEXT_PUBLIC_API_URL` on Vercel**
1. Go to `vercel.com` → Project → Settings → Environment Variables
2. Add: `NEXT_PUBLIC_API_URL` = `https://interlace-backend.up.railway.app`
3. Redeploy frontend: `vercel --prod` OR push to `main` (auto-deploys)

- [ ] **Step 4: Smoke test end-to-end**

Test each flow on the live Vercel URL:
- Text search: type "black midi dress" → should return real ASOS products with images
- Image upload: upload any fashion photo → should return visually similar products
- Product detail: click any card → `/products/{sku}` → gallery + outfit recommendations load
- Theme toggle: dark↔light persists across page refresh

- [ ] **Step 5: Commit smoke test notes**
```bash
git commit --allow-empty -m "chore: backend deployed and wired to Vercel"
```
