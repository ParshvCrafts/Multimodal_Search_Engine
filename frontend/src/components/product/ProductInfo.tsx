'use client'
import { useState } from 'react'
import type { ProductDetail } from '@/lib/types'

interface Props { product: ProductDetail }

export default function ProductInfo({ product }: Props) {
  const [selectedSize, setSelectedSize] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  const [selectedColor, setSelectedColor] = useState(0)

  const allSizes = [
    ...(product.available_sizes ?? []),
    ...(product.unavailable_sizes ?? []),
  ]

  return (
    <div style={{ padding: '40px 56px 40px 40px', borderLeft: '1px solid var(--border-hard)', display: 'flex', flexDirection: 'column' }}>
      {/* Brand + category tag */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
        <span style={{ fontSize: '11px', letterSpacing: '0.3em', textTransform: 'uppercase', color: 'var(--accent)' }}>
          {product.brand}
        </span>
        <span style={{
          fontSize: '10px', letterSpacing: '0.18em', textTransform: 'uppercase',
          color: '#555', background: '#141414', border: '1px solid #222', padding: '4px 10px',
        }}>
          {product.category}
        </span>
      </div>

      {/* Product name */}
      <h1 style={{
        fontFamily: "'Palatino Linotype', Palatino, 'Book Antiqua', Georgia, serif",
        fontSize: '28px', fontWeight: 400, color: 'var(--text-primary)',
        lineHeight: 1.3, letterSpacing: '-0.01em', marginBottom: '20px',
      }}>
        {product.name}
      </h1>

      {/* Price (single price only) */}
      <div style={{ marginBottom: '24px', paddingBottom: '24px', borderBottom: '1px solid var(--border-hard)' }}>
        <span style={{ fontFamily: "'Georgia', serif", fontSize: '26px', color: 'var(--text-primary)', fontWeight: 300 }}>
          &#163;{product.price.toFixed(2)}
        </span>
      </div>

      {/* 2x2 attribute grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 24px', marginBottom: '28px', paddingBottom: '28px', borderBottom: '1px solid var(--border-hard)' }}>
        {[
          { label: 'Gender', value: product.gender },
          { label: 'Color', value: product.color },
          { label: 'Fit', value: product.fit ?? 'Regular' },
          { label: 'Material', value: product.material ?? 'Viscose' },
        ].map(({ label, value }) => (
          <div key={label} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '10px', letterSpacing: '0.22em', textTransform: 'uppercase', color: '#888' }}>{label}</span>
            <span style={{ fontSize: '13px', color: 'var(--text-primary)', letterSpacing: '0.03em' }}>{value}</span>
          </div>
        ))}
      </div>

      {/* Color swatches */}
      {product.available_colors && product.available_colors.length > 0 && (
        <div style={{ marginBottom: '28px', paddingBottom: '28px', borderBottom: '1px solid var(--border-hard)' }}>
          <div style={{ fontSize: '10px', letterSpacing: '0.22em', textTransform: 'uppercase', color: '#888', marginBottom: '12px' }}>
            Color
          </div>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            {product.available_colors.map((c, i) => (
              <div
                key={c.name}
                onClick={() => setSelectedColor(i)}
                title={c.name}
                style={{
                  width: '28px', height: '28px', borderRadius: '50%',
                  background: c.hex,
                  border: selectedColor === i ? '2px solid var(--text-primary)' : '2px solid #333',
                  cursor: 'pointer',
                  transform: selectedColor === i ? 'scale(1.12)' : 'scale(1)',
                  transition: 'border-color 0.2s, transform 0.2s',
                  position: 'relative',
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* Size selector */}
      {allSizes.length > 0 && (
        <div style={{ marginBottom: '28px', paddingBottom: '28px', borderBottom: '1px solid var(--border-hard)' }}>
          <div style={{ marginBottom: '12px' }}>
            <span style={{ fontSize: '10px', letterSpacing: '0.22em', textTransform: 'uppercase', color: '#888' }}>Size</span>
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {allSizes.map(size => {
              const unavailable = product.unavailable_sizes?.includes(size)
              const isSelected = selectedSize === size
              return (
                <button
                  key={size}
                  disabled={unavailable}
                  onClick={() => !unavailable && setSelectedSize(isSelected ? null : size)}
                  style={{
                    minWidth: '52px', height: '42px',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '12px', letterSpacing: '0.12em', textTransform: 'uppercase',
                    background: isSelected ? 'var(--text-primary)' : 'var(--bg-card)',
                    border: `1px solid ${isSelected ? 'var(--text-primary)' : '#222'}`,
                    color: unavailable ? '#2e2e2e' : isSelected ? 'var(--bg-primary)' : '#888',
                    cursor: unavailable ? 'not-allowed' : 'pointer',
                    textDecoration: unavailable ? 'line-through' : 'none',
                    transition: 'all 0.2s', padding: '0 12px',
                  }}
                >
                  {size}
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* CTA row */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '28px' }}>
        <button style={{
          flex: 1, height: '52px', background: 'var(--text-primary)', color: 'var(--bg-primary)',
          border: 'none', fontSize: '13px', letterSpacing: '0.2em', textTransform: 'uppercase',
          cursor: 'pointer', transition: 'opacity 0.2s',
        }}>
          Add to Bag
        </button>
        <button
          onClick={() => setSaved(s => !s)}
          style={{
            width: '52px', height: '52px', background: 'var(--bg-card)',
            border: `1px solid ${saved ? 'rgba(232,64,64,0.3)' : '#2a2a2a'}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '20px', cursor: 'pointer',
            color: saved ? '#e84040' : '#555', transition: 'all 0.2s', flexShrink: 0,
          }}
        >
          {saved ? '\u2665' : '\u2661'}
        </button>
      </div>

      {/* Style tags */}
      {product.style_tags.length > 0 && (
        <div style={{ marginBottom: '28px', paddingBottom: '28px', borderBottom: '1px solid var(--border-hard)' }}>
          <div style={{ fontSize: '10px', letterSpacing: '0.22em', textTransform: 'uppercase', color: '#888', marginBottom: '10px' }}>Style</div>
          <div style={{ display: 'flex', gap: '7px', flexWrap: 'wrap' }}>
            {product.style_tags.map(tag => (
              <span key={tag} style={{
                fontSize: '10px', letterSpacing: '0.14em', textTransform: 'uppercase',
                color: '#666', background: '#111', border: '1px solid #1e1e1e',
                padding: '5px 12px', cursor: 'pointer', transition: 'all 0.2s',
              }}>
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
