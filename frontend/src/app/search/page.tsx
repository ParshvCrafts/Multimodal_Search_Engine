'use client'
import { useState, useCallback, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import SearchBar from '@/components/search/SearchBar'
import FilterBar from '@/components/search/FilterBar'
import ProductGrid from '@/components/search/ProductGrid'
import OutfitStrip from '@/components/search/OutfitStrip'
import Footer from '@/components/layout/Footer'
import { isMockMode, searchProducts, searchByImage } from '@/lib/api'
import { MOCK_PRODUCTS, MOCK_OUTFIT_ITEMS } from '@/lib/mock-data'
import type { SearchResultItem, SortOption } from '@/lib/types'

// ── Spinner ──────────────────────────────────────────────────────────────────
function SearchSpinner() {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '100px 56px',
      background: 'var(--bg-primary)',
    }}>
      <div style={{
        width: '36px',
        height: '36px',
        borderRadius: '50%',
        border: '1.5px solid var(--border-soft)',
        borderTopColor: 'var(--accent)',
        animation: 'spin 0.85s linear infinite',
      }} />
      <div style={{
        marginTop: '22px',
        fontSize: '10px',
        letterSpacing: '0.28em',
        textTransform: 'uppercase',
        color: 'var(--text-dim)',
      }}>
        Searching
      </div>
    </div>
  )
}

// ── Build the effective query from user text + active filters ─────────────────
// Text query always comes first so the backend parser gives it priority.
function buildEffectiveQuery(text: string, filters: Record<string, string>): string {
  const filterTerms = Object.values(filters).filter(Boolean)
  if (text.trim()) {
    return filterTerms.length ? `${text.trim()} ${filterTerms.join(' ')}` : text.trim()
  }
  return filterTerms.join(' ')
}

// ── Core search page (needs Suspense for useSearchParams) ─────────────────────
function SearchPageContent() {
  const mockMode = isMockMode()
  const searchParams = useSearchParams()
  const initialQuery = searchParams.get('q') ?? ''

  const [results, setResults] = useState<SearchResultItem[]>(mockMode ? MOCK_PRODUCTS : [])
  const [total, setTotal] = useState(mockMode ? MOCK_PRODUCTS.length : 0)
  const [loading, setLoading] = useState(false)
  const [topN, setTopN] = useState(20)
  const [sort, setSort] = useState<SortOption>('relevance')
  // textQuery tracks the last text typed in the search bar (for filter-triggered re-searches)
  const [textQuery, setTextQuery] = useState(initialQuery)
  const [hasSearched, setHasSearched] = useState(mockMode)
  const [error, setError] = useState<string | null>(null)
  const [view, setView] = useState<'grid' | 'list'>('grid')
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({})

  // ── Search ────────────────────────────────────────────────────────────────
  const handleSearch = useCallback(async (query: string, imageFile?: File) => {
    setLoading(true)
    setError(null)
    setHasSearched(true)
    if (query) setTextQuery(query)
    try {
      let res
      if (imageFile && !query) {
        res = await searchByImage(imageFile, topN)
      } else if (query) {
        res = await searchProducts({ query, topN, sortBy: sort })
      } else {
        setLoading(false)
        return
      }
      setResults(res.results)
      setTotal(res.total)
    } catch (err) {
      setResults([])
      setTotal(0)
      setError(err instanceof Error ? err.message : 'Search failed')
    } finally {
      setLoading(false)
    }
  }, [topN, sort])

  // Auto-trigger search when navigating from teaser with ?q=
  useEffect(() => {
    if (initialQuery) handleSearch(initialQuery)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ── TopN change ───────────────────────────────────────────────────────────
  const handleTopNChange = (n: number) => {
    setTopN(n)
    if (hasSearched && !mockMode) {
      const effective = buildEffectiveQuery(textQuery, activeFilters)
      if (effective) {
        setLoading(true)
        searchProducts({ query: effective, topN: n, sortBy: sort })
          .then(res => { setResults(res.results); setTotal(res.total); setError(null) })
          .catch(err => { setError(err instanceof Error ? err.message : 'Search failed') })
          .finally(() => setLoading(false))
      }
    }
  }

  // ── Filter change — updates state and immediately re-searches ─────────────
  const handleFilterChange = useCallback((key: string, value: string | null) => {
    setActiveFilters(prev => {
      const next = { ...prev }
      if (value === null) delete next[key]
      else next[key] = value
      const effective = buildEffectiveQuery(textQuery, next)
      if (effective) {
        // Fire search with the updated filters outside setState
        setLoading(true)
        setHasSearched(true)
        searchProducts({ query: effective, topN, sortBy: sort })
          .then(res => { setResults(res.results); setTotal(res.total); setError(null) })
          .catch(err => { setResults([]); setTotal(0); setError(err instanceof Error ? err.message : 'Search failed') })
          .finally(() => setLoading(false))
      }
      return next
    })
  }, [textQuery, topN, sort])

  return (
    <main>
      <SearchBar onSearch={handleSearch} loading={loading} initialQuery={initialQuery} />
      <FilterBar
        topN={topN}
        onTopNChange={handleTopNChange}
        sort={sort}
        onSortChange={setSort}
        view={view}
        onViewChange={setView}
        activeFilters={activeFilters}
        onRemoveFilter={key => handleFilterChange(key, null)}
        onFilterChange={handleFilterChange}
      />

      {error && !loading && (
        <div style={{
          padding: '20px 56px 0',
          background: 'var(--bg-primary)',
          color: '#c77f7f',
          fontSize: '13px',
          letterSpacing: '0.04em',
        }}>
          {error}
        </div>
      )}

      {loading ? (
        <SearchSpinner />
      ) : hasSearched ? (
        <ProductGrid products={results} total={total} view={view} />
      ) : (
        <div style={{
          padding: '48px 56px 80px',
          background: 'var(--bg-primary)',
          color: 'var(--text-secondary)',
          borderTop: '1px solid #141414',
        }}>
          <div style={{ fontFamily: "'Georgia', serif", fontSize: '24px', fontWeight: 300, color: 'var(--text-primary)', marginBottom: '12px' }}>
            Search the live ASOS catalog
          </div>
          <div style={{ fontSize: '14px', lineHeight: 1.7 }}>
            Enter a query or upload an image to fetch results from the FastAPI backend.
          </div>
        </div>
      )}

      {mockMode && <OutfitStrip items={MOCK_OUTFIT_ITEMS} />}
      <Footer />
    </main>
  )
}

// ── Page export (Suspense required for useSearchParams in App Router) ─────────
export default function SearchPage() {
  return (
    <Suspense>
      <SearchPageContent />
    </Suspense>
  )
}
