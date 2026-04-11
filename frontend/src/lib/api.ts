import { SearchResponse, ProductDetail, OutfitResponse, SortOption } from './types'
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
  return res.json()
}

export async function getOutfit(sku: string): Promise<OutfitResponse> {
  if (useMock()) {
    return {
      items: MOCK_OUTFIT_ITEMS.map(p => ({
        sku: p.sku, name: p.name, brand: p.brand,
        price: p.price, category: p.category, image_url: p.image_url,
      })),
    }
  }
  const res = await fetch(`${BASE}/api/v1/products/${sku}/outfit`)
  if (!res.ok) throw new Error(`Outfit failed: ${sku}`)
  return res.json()
}

export async function getSimilar(sku: string, topN = 5): Promise<SearchResponse> {
  if (useMock()) {
    return {
      results: MOCK_RELATED,
      query_info: { ...EMPTY_QUERY_INFO },
      total: MOCK_RELATED.length,
    }
  }
  const res = await fetch(`${BASE}/api/v1/search/similar/${sku}?top_n=${topN}`)
  if (!res.ok) throw new Error(`Similar failed: ${sku}`)
  return res.json()
}
