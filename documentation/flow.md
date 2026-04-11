# Request Flow

## API Endpoints (all prefixed `/api/v1`)

| Method | Path | Request | Response |
|--------|------|---------|---------|
| POST | `/search` | `{query, top_n, sort_by, text_weight?, image_b64?}` | `SearchResponse` |
| POST | `/search/image` | multipart `file` + query param `top_n` | `SearchResponse` |
| GET | `/search/similar/{sku}` | query param `top_n` | `SimilarResponse` |
| GET | `/products/{sku}` | — | `ProductDetail` |
| GET | `/products/{sku}/outfit` | query param `n_per_category` | `OutfitResponse` |
| GET | `/health` | — | `{status, engine_ready, product_count}` |

## Response Schemas

### SearchResponse
```json
{
  "results": [{ "sku", "name", "brand", "price", "color", "color_family", "category", "gender", "image_url", "url", "score", "style_tags", "in_stock" }],
  "query_info": { "original_query", "processed_query", "detected_language", "was_translated", "parsed_category", "parsed_color", "parsed_price_range", "sort_by", "suggested_searches", ... },
  "total": 20
}
```

### ProductDetail
```json
{ "sku", "name", "brand", "price", "color", "color_family", "category", "gender", "image_url", "image_urls", "url", "style_tags", "materials", "sizes_available", "product_details", "in_stock" }
```

### OutfitResponse (backend shape — frontend needs adapter)
```json
{
  "source": { ...ProductDetail },
  "outfit": { "Tops": [...OutfitItem], "Shoes": [...OutfitItem] }
}
```
`OutfitItem`: `{ sku, name, brand, price, color_family, category, image_url, outfit_score }`

### SimilarResponse (backend shape — frontend needs adapter)
```json
{
  "source": { ...ProductDetail },
  "results": [{ "sku", "name", "brand", "price", "color", "category", "image_url", "similarity_score" }],
  "total": 10
}
```

## Text Search Pipeline
```
POST /search {query, top_n}
  1. NLP: language detect → translate if needed
  2. Spell correction
  3. NLU parsing → extract gender, category, color, price range, style tags
  4. CLIP encoding (5 prompt templates → averaged embedding)
  5. Dual FAISS retrieval (~300 candidates, image-index 55% + text-index 45% via RRF)
  6. BM25 lexical retrieval
  7. Metadata filter (relax if < threshold results)
  8. Hybrid reranking → CLIP 55% + tags 25% + BM25 15% + freshness 5%
  9. Sort + slice → top_n results
```

## Image Search Pipeline
Steps 1–3 skipped. Image encoded directly via FashionCLIP vision encoder → FAISS retrieval → reranking.

## Multimodal Search
`image_b64` provided alongside `text`. `text_weight` (0–1) blends the two embeddings before FAISS retrieval.
