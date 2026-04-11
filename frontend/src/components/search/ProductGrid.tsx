'use client'
import { useState, useEffect } from 'react'
import ProductCard from './ProductCard'
import type { SearchResultItem } from '@/lib/types'

interface Props {
  products: SearchResultItem[]
  total: number
  view: 'grid' | 'list'
}

const PAGE_SIZE = 20

export default function ProductGrid({ products, total, view }: Props) {
  const [pageIndex, setPageIndex] = useState(0)

  useEffect(() => { setPageIndex(0) }, [products])

  const pageCount = Math.ceil(products.length / PAGE_SIZE)
  const safePage = Math.min(pageIndex, Math.max(0, pageCount - 1))
  const pageProducts = products.slice(safePage * PAGE_SIZE, (safePage + 1) * PAGE_SIZE)
  const showPagination = products.length > PAGE_SIZE

  const colCount = pageProducts.length <= 2 ? 2 : pageProducts.length <= 3 ? 3 : 5
  const gridCols = view === 'list' ? '1fr' : `repeat(${colCount}, 1fr)`

  return (
    <div style={{ padding: '28px 56px 80px', background: 'var(--bg-primary)' }}>
      {/* Results meta row */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '20px',
        paddingBottom: '18px',
        borderBottom: '1px solid #141414',
      }}>
        <span style={{ fontSize: '13px', color: '#666', letterSpacing: '0.05em' }}>
          <strong style={{ color: 'var(--text-primary)', fontWeight: 'normal' }}>{total}</strong> results
        </span>
        {showPagination && (
          <span style={{
            fontSize: '13px',
            color: 'var(--text-primary)',
            letterSpacing: '0.1em',
            fontFamily: "'Georgia', serif",
          }}>
            Page{' '}
            <span style={{ color: 'var(--accent)', fontStyle: 'italic' }}>{safePage + 1}</span>
            {' '}of{' '}
            <span style={{ color: 'var(--accent)', fontStyle: 'italic' }}>{pageCount}</span>
          </span>
        )}
      </div>

      {/* Pagination tabs */}
      {showPagination && (
        <div style={{ display: 'flex', gap: '4px', marginBottom: '24px', flexWrap: 'wrap' }}>
          {Array.from({ length: pageCount }).map((_, i) => {
            const start = i * PAGE_SIZE + 1
            const end = Math.min((i + 1) * PAGE_SIZE, products.length)
            return (
              <button
                key={i}
                onClick={() => setPageIndex(i)}
                style={{
                  padding: '8px 18px',
                  fontSize: '11px',
                  letterSpacing: '0.12em',
                  textTransform: 'uppercase',
                  cursor: 'pointer',
                  background: safePage === i ? 'var(--text-primary)' : '#0f0f0f',
                  color: safePage === i ? 'var(--bg-primary)' : '#555',
                  border: `1px solid ${safePage === i ? 'var(--text-primary)' : '#222'}`,
                  transition: 'all 0.2s',
                }}
              >
                {start}-{end}
              </button>
            )
          })}
        </div>
      )}

      {/* Product grid */}
      {products.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '80px 0', color: 'var(--text-secondary)' }}>
          <div style={{ fontFamily: "'Georgia', serif", fontSize: '24px', fontWeight: 300, marginBottom: '16px' }}>
            No results found
          </div>
          <div style={{ fontSize: '14px' }}>Try a different search term or upload an image.</div>
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: gridCols,
          gap: '16px',
          transition: 'grid-template-columns 0.3s',
        }}>
          {pageProducts.map(p => (
            <ProductCard key={p.sku} product={p} showScore />
          ))}
        </div>
      )}
    </div>
  )
}
