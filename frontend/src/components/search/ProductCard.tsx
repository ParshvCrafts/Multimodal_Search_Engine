'use client'
import { useState } from 'react'
import Link from 'next/link'
import type { SearchResultItem } from '@/lib/types'

interface Props {
  product: SearchResultItem
  showScore?: boolean
}

export default function ProductCard({ product, showScore }: Props) {
  const [saved, setSaved] = useState(false)
  const [hovered, setHovered] = useState(false)

  return (
    <Link href={`/products/${product.sku}`} style={{ textDecoration: 'none', display: 'block' }}>
      <div
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        style={{
          position: 'relative',
          background: 'var(--bg-card)',
          cursor: 'pointer',
          display: 'flex',
          flexDirection: 'column',
          border: `1px solid ${hovered ? '#2a2a2a' : 'transparent'}`,
          transform: hovered ? 'translateY(-4px)' : 'translateY(0)',
          transition: 'border-color 0.25s, transform 0.35s cubic-bezier(0.25,0.46,0.45,0.94)',
        }}
      >
        {/* Image */}
        <div style={{
          width: '100%',
          aspectRatio: '3/4',
          background: '#151515',
          position: 'relative',
          overflow: 'hidden',
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
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

          {/* Score badge */}
          {showScore && (
            <div style={{
              position: 'absolute',
              top: '8px',
              left: '8px',
              fontSize: '9px',
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              background: 'rgba(8,8,8,0.85)',
              color: 'var(--accent)',
              padding: '3px 7px',
              border: '1px solid rgba(201,169,110,0.25)',
              pointerEvents: 'none',
            }}>
              {Math.round(product.score * 100)}% match
            </div>
          )}

          {/* Heart button */}
          <button
            onClick={e => {
              e.preventDefault()
              e.stopPropagation()
              setSaved(s => !s)
            }}
            style={{
              position: 'absolute',
              top: '8px',
              right: '8px',
              zIndex: 2,
              width: '30px',
              height: '30px',
              borderRadius: '50%',
              background: 'rgba(8,8,8,0.7)',
              border: '1px solid rgba(255,255,255,0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              fontSize: '14px',
              lineHeight: '1',
              opacity: saved || hovered ? 1 : 0,
              transition: 'opacity 0.25s, transform 0.2s',
              color: saved ? '#e84040' : '#888',
            }}
          >
            {saved ? '♥' : '♡'}
          </button>
        </div>

        {/* Card body */}
        <div style={{ padding: '12px 0 0', display: 'flex', flexDirection: 'column', flex: 1 }}>
          <div style={{ fontSize: '10px', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--accent)', marginBottom: '5px' }}>
            {product.brand}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-primary)', lineHeight: 1.45, fontWeight: 300, flex: 1, marginBottom: '8px' }}>
            {product.name}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingBottom: '2px' }}>
            <span style={{ fontSize: '12px', color: '#888' }}>£{product.price.toFixed(2)}</span>
            <span style={{ fontSize: '10px', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#3a3a3a' }}>
              {product.category}
            </span>
          </div>
        </div>
      </div>
    </Link>
  )
}
