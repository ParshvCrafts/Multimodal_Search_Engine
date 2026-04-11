'use client'
import { useState, useCallback } from 'react'
import SearchBar from '@/components/search/SearchBar'
import FilterBar from '@/components/search/FilterBar'
import ProductGrid from '@/components/search/ProductGrid'
import OutfitStrip from '@/components/search/OutfitStrip'
import Footer from '@/components/layout/Footer'
import { searchProducts, searchByImage } from '@/lib/api'
import { MOCK_PRODUCTS, MOCK_OUTFIT_ITEMS } from '@/lib/mock-data'
import type { SearchResultItem, SortOption } from '@/lib/types'

export default function SearchPage() {
  const [results, setResults] = useState<SearchResultItem[]>(MOCK_PRODUCTS)
  const [total, setTotal] = useState(MOCK_PRODUCTS.length)
  const [loading, setLoading] = useState(false)
  const [topN, setTopN] = useState(20)
  const [sort, setSort] = useState<SortOption>('relevance')
  const [view, setView] = useState<'grid' | 'list'>('grid')
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({})

  const handleSearch = useCallback(async (query: string, imageFile?: File) => {
    setLoading(true)
    try {
      let res
      if (imageFile && !query) {
        res = await searchByImage(imageFile, topN)
      } else {
        // Note: when both query and imageFile are present, text search is used.
        // Full multimodal support (with FileReader for B64) can be added later.
        res = await searchProducts({ query, topN, sortBy: sort })
      }
      setResults(res.results)
      setTotal(res.total)
    } catch {
      // Keep previous results on error
    } finally {
      setLoading(false)
    }
  }, [topN, sort])

  const handleTopNChange = (n: number) => {
    setTopN(n)
    // Re-run search with new topN if results have been customized from the default
    if (results !== MOCK_PRODUCTS) {
      setLoading(true)
      searchProducts({ query: '', topN: n, sortBy: sort })
        .then(res => { setResults(res.results); setTotal(res.total) })
        .catch(() => {})
        .finally(() => setLoading(false))
    }
  }

  const removeFilter = (key: string) => {
    setActiveFilters(prev => {
      const next = { ...prev }
      delete next[key]
      return next
    })
  }

  return (
    <main>
      <SearchBar onSearch={handleSearch} loading={loading} />
      <FilterBar
        topN={topN}
        onTopNChange={handleTopNChange}
        sort={sort}
        onSortChange={setSort}
        view={view}
        onViewChange={setView}
        activeFilters={activeFilters}
        onRemoveFilter={removeFilter}
      />
      <ProductGrid products={results} total={total} view={view} />
      <OutfitStrip items={MOCK_OUTFIT_ITEMS} />
      <Footer />
    </main>
  )
}
