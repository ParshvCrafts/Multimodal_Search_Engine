'use client'
import { useState } from 'react'
import Link from 'next/link'
import type { SearchResultItem } from '@/lib/types'

interface Props {
  product: SearchResultItem
  showScore?: boolean
  view?: 'grid' | 'list'
}

export default function ProductCard({ product, showScore, view = 'grid' }: Props) {
  const [saved, setSaved] = useState(false)
  const [hovered, setHovered] = useState(false)

  const heartBtn = (
    <button
      onClick={e => {
        e.preventDefault()
        e.stopPropagation()
        setSaved(s => !s)
      }}
      style={{
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
        transition: 'opacity 0.25s',
        color: saved ? '#e84040' : '#888',
        flexShrink: 0,
      }}
    >
      {saved ? '♥' : '♡'}
    </button>
  )

  // ── List layout ─────────────────────────────────────────────────────────────
  if (view === 'list') {
    return (
      <Link href={`/products/${product.sku}`} style={{ textDecoration: 'none', display: 'block' }}>
        <div
          onMouseEnter={() => setHovered(true)}
          onMouseLeave={() => setHovered(false)}
          style={{
            display: 'flex',
            flexDirection: 'row',
            alignItems: 'stretch',
            background: hovered ? 'var(--bg-card)' : 'transparent',
            borderBottom: '1px solid #1e1e1e',
            cursor: 'pointer',
            transition: 'background 0.2s',
            minHeight: '176px',
          }}
        >
          {/* Image */}
          <div style={{
            width: '160px',
            flexShrink: 0,
            background: '#151515',
            overflow: 'hidden',
            position: 'relative',
          }}>
            {product.image_url ? (
              <img
                src={product.image_url}
                alt={product.name}
                style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
              />
            ) : (
              <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontSize: '9px', letterSpacing: '0.15em', color: '#222', textTransform: 'uppercase' }}>No Image</span>
              </div>
            )}
          </div>

          {/* Info */}
          <div style={{
            flex: 1,
            padding: '20px 24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
            minWidth: 0,
          }}>
            {/* Brand */}
            <div style={{ fontSize: '10px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'var(--accent)' }}>
              {product.brand}
            </div>

            {/* Name */}
            <div style={{
              fontSize: '15px',
              color: 'var(--text-primary)',
              fontWeight: 300,
              lineHeight: 1.45,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}>
              {product.name}
            </div>

            {/* Attributes row */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '4px', flexWrap: 'wrap' }}>
              {product.color && (
                <span style={{ fontSize: '11px', letterSpacing: '0.08em', color: '#b0a898' }}>
                  {product.color}
                </span>
              )}
              {product.color && product.category && (
                <span style={{ fontSize: '10px', color: '#555' }}>·</span>
              )}
              {product.category && (
                <span style={{ fontSize: '11px', letterSpacing: '0.08em', color: '#b0a898', textTransform: 'capitalize' }}>
                  {product.category}
                </span>
              )}
              {product.gender && (
                <>
                  <span style={{ fontSize: '10px', color: '#555' }}>·</span>
                  <span style={{ fontSize: '11px', letterSpacing: '0.08em', color: '#b0a898', textTransform: 'capitalize' }}>
                    {product.gender}
                  </span>
                </>
              )}
            </div>

            {/* Style tags */}
            {product.style_tags?.length > 0 && (
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '6px' }}>
                {product.style_tags.slice(0, 3).map(tag => (
                  <span key={tag} style={{
                    fontSize: '10px',
                    letterSpacing: '0.1em',
                    textTransform: 'uppercase',
                    color: '#999',
                    border: '1px solid #2e2e2e',
                    padding: '3px 8px',
                  }}>
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Right column: price + score + heart */}
          <div style={{
            flexShrink: 0,
            padding: '20px 24px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
            justifyContent: 'space-between',
            minWidth: '130px',
          }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
              <span style={{ fontSize: '17px', fontWeight: 300, color: 'var(--text-primary)', letterSpacing: '0.01em' }}>
                £{product.price.toFixed(2)}
              </span>
              {showScore && (
                <span style={{
                  fontSize: '9px',
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  color: 'var(--accent)',
                  border: '1px solid rgba(201,169,110,0.25)',
                  padding: '2px 7px',
                }}>
                  {Math.round(product.score * 100)}% match
                </span>
              )}
              {!product.in_stock && (
                <span style={{ fontSize: '9px', letterSpacing: '0.1em', textTransform: 'uppercase', color: '#555' }}>
                  Out of stock
                </span>
              )}
            </div>
            {heartBtn}
          </div>
        </div>
      </Link>
    )
  }

  // ── Grid layout ─────────────────────────────────────────────────────────────
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
          <div style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            zIndex: 2,
            opacity: saved || hovered ? 1 : 0,
            transition: 'opacity 0.25s',
          }}>
            {heartBtn}
          </div>
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
