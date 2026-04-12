# Progress

## Completed — All Phases

### Phase 1–3: Foundation
- Backend modularization: monolith → `backend/app/engine/`, FastAPI API layer
- Frontend: App Router UI with hybrid mock/live client
- First live integration pass: fixed mock leaks, error swallowing, 404 handling

### Phase 4: Live Integration Stabilization
- Removed live-mode mock seeding on `/search`
- Changed invalid SKU behavior from `500` → `404`
- Surfaced search failures in `handleSearch` and `handleTopNChange`
- Mapped backend `materials` and `product_details` into product detail UI

### Phase 5: Landing Page Overhaul (Latest)
- **Carousel**: Replaced mock data with 12 hand-picked real ASOS products (curated for diversity across category, gender, color, price)
  - Source: `frontend/src/lib/featured-products.ts`
  - Infinite seamless loop using 3x card cloning (no snap-back glitch)
  - Card-by-card CSS transition stepping, auto-advance every 3.5s
  - Hover-to-pause, arrow navigation, clickable dot indicators
  - Cards link to real product detail pages (`/products/[sku]`)
- **Hero**: Added `main.png` brand image support
  - Loads `/main.png` from `frontend/public/` automatically
  - If missing: styled fallback placeholder with instructions
  - Hydration-safe: `useEffect` + `naturalWidth` check handles SSR race
- **Featured Products**: Created `featured-products.ts` with diverse ASOS catalog items:
  - Dresses, Jackets, Jeans, Knitwear, Tops, Skirts, Tailoring, Hoodies
  - Women / Men / Unisex mix, £13–£105 price range

## Verification Performed
- `GET /api/v1/health` → healthy, 29971 products
- `POST /api/v1/search` → real ASOS results with images
- `GET /api/v1/products/109450190` → full product detail
- `GET /api/v1/products/109450190/outfit` → outfit recommendations
- `GET /api/v1/search/similar/109450190` → similarity results
- `npx tsc --noEmit` → passes
- **Browser**: Landing page hero shows styled placeholder (or main.png if present)
- **Browser**: Carousel renders real ASOS product images, auto-scrolls, wraps infinitely
- **Browser**: Carousel arrow buttons step forward/backward, hover pauses
- **Browser**: Carousel cards navigate to live product detail pages
- **Browser**: Text search returns real results with visible images
- **Browser**: Product detail shows materials, sizes, Complete the Look, You May Also Like

### Phase 6: Search UX, Filter System, List View
- **FilterBar**: 5 filter dimensions (Gender, Category, Color, Size, Price) with backend-parseable query term mapping
  - Dropdowns rendered via React Portal (`createPortal`) onto `document.body` — escapes `overflowX: auto` scroll-container clipping
  - Position: `fixed` at `getBoundingClientRect().bottom/left`, `zIndex: 9999`
  - Scroll-close skips events originating inside the dropdown panel; outside-click via `mousedown` listener
  - Filter-only search supported: filter terms build a natural-language query the backend QueryParser extracts
  - Filter + text search: text query prepended so backend parser gives it priority
- **ProductCard list layout**: dedicated row layout when `view='list'`
  - 160px image strip left, info centre (brand/name/color·category·gender/style tags), price+score right
  - `minHeight: 176px`, `borderBottom` hairline separators, hover background highlight
- **Search page**: filter state drives immediate re-search; `textQuery` tracked for filter+text combo; `SearchSpinner` on loading
- **Layout fix**: `next/script` replaced with native `<script dangerouslySetInnerHTML>` in `<head>` — React 19 prohibits script elements in the component tree
- **Hero image**: served from `frontend/public/main.png`

## Still Pending
- Browser verification of image upload / multimodal search
- Deployment (backend + frontend) and production smoke tests
- Regression coverage for live-mode behavior
- Mobile responsiveness polish
