export interface SearchResultItem {
  sku: string
  name: string
  brand: string
  price: number
  color: string
  color_family: string
  category: string
  gender: string
  image_url: string
  url?: string
  score: number
  style_tags: string[]
  in_stock: boolean
}

export interface QueryInfo {
  original_query: string
  processed_query: string
  detected_language: string
  was_translated: boolean
  parsed_category?: string
  parsed_color?: string
  parsed_price_range: [number | null, number | null]
  parsed_gender?: string
  sort_by: string
  suggested_searches: string[]
}

export interface SearchResponse {
  results: SearchResultItem[]
  query_info: QueryInfo
  total: number
}

export interface ProductDetail {
  sku: string
  name: string
  brand: string
  price: number
  color: string
  color_family: string
  category: string
  gender: string
  image_url: string
  image_urls: string[]
  url?: string
  score?: number
  style_tags: string[]
  in_stock: boolean
  fit?: string
  material?: string
  available_sizes: string[]
  unavailable_sizes: string[]
  available_colors: { name: string; hex: string }[]
  description?: string
  care_instructions?: string[]
  sizing_info?: string
  delivery_info?: string
}

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
  items: OutfitItem[]
}

export type SearchMode = 'text' | 'image' | 'multimodal'

export type SortOption = 'relevance' | 'price_asc' | 'price_desc'

export interface SearchFilters {
  gender?: string
  category?: string
  color?: string
  price_min?: number
  price_max?: number
  size?: string
}
