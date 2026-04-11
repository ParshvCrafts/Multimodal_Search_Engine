import { SearchResponse, SearchResultItem, ProductDetail, OutfitResponse, OutfitItem, SortOption } from './types'
import { MOCK_PRODUCTS, MOCK_PRODUCT_DETAIL, MOCK_OUTFIT_ITEMS, MOCK_RELATED } from './mock-data'

const BASE = process.env.NEXT_PUBLIC_API_URL

function useMock() { return !BASE }

const EMPTY_QUERY_INFO = {
  original_query: '',
  processed_query: '',
  detected_language: 'en',
  was_translated: false,
  sort_by: 'relevance',
  suggested_searches: [],
  parsed_price_range: [null, null] as [null, null],
}

export async function searchProducts(params: {
  query?: string
  imageB64?: string
  topN: number
  sortBy: SortOption
}): Promise<SearchResponse> {
  if (useMock()) {
    await new Promise(r => setTimeout(r, 400))
    const count = Math.min(params.topN, MOCK_PRODUCTS.length)
    return {
      results: MOCK_PRODUCTS.slice(0, count),
      query_info: {
        ...EMPTY_QUERY_INFO,
        original_query: params.query ?? '',
        processed_query: params.query ?? '',
        sort_by: params.sortBy,
        suggested_searches: ['black midi dress', 'floral wrap dress', 'tailored trousers'],
      },
      total: count,
    }
  }

  const body: Record<string, unknown> = {
    query: params.query ?? '',
    top_n: params.topN,
    sort_by: params.sortBy,
  }
  if (params.imageB64) body.image_b64 = params.imageB64
  const res = await fetch(`${BASE}/api/v1/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`Search failed: ${res.status}`)
  return res.json()
}

export async function searchByImage(file: File, topN: number): Promise<SearchResponse> {
  if (useMock()) {
    await new Promise(r => setTimeout(r, 500))
    return {
      results: MOCK_PRODUCTS.slice(0, Math.min(topN, MOCK_PRODUCTS.length)),
      query_info: { ...EMPTY_QUERY_INFO },
      total: Math.min(topN, MOCK_PRODUCTS.length),
    }
  }
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/api/v1/search/image?top_n=${topN}`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(`Image search failed: ${res.status}`)
  return res.json()
}

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
