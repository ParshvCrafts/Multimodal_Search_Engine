'use client'
import Link from 'next/link'
import type { OutfitItem, SearchResultItem } from '@/lib/types'

type Item = OutfitItem | SearchResultItem

interface Props {
  items: Item[]
  title?: string
  subtitle?: string
}

export default function CompleteTheLook({ items, title = 'Complete the Look', subtitle = 'Curated pairings' }: Props) {
  if (!items.length) return null
  return (
    <div style={{ padding: '56px 56px 80px', borderTop: '1px solid var(--border-hard)', background: 'var(--bg-primary)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '36px' }}>
        <span style={{ fontFamily: "'Georgia', serif", fontSize: '26px', fontWeight: 300, color: 'var(--text-primary)' }}>
          {title}
        </span>
        <span style={{ fontSize: '12px', letterSpacing: '0.15em', textTransform: 'uppercase', color: '#555' }}>
          {subtitle}
        </span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '20px' }}>
        {items.slice(0, 5).map(item => (
          <Link key={item.sku} href={`/products/${item.sku}`} style={{ textDecoration: 'none' }}>
            <div style={{
              background: 'var(--bg-card)', cursor: 'pointer',
              border: '1px solid transparent', transition: 'border-color 0.2s, transform 0.3s',
            }}>
              <div style={{
                width: '100%', aspectRatio: '3/4',
                background: '#151515', display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <span style={{ fontSize: '10px', letterSpacing: '0.18em', color: '#222', textTransform: 'uppercase' }}>Image</span>
              </div>
              <div style={{ padding: '12px 2px 4px' }}>
                <div style={{ fontSize: '10px', letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--accent)', marginBottom: '4px' }}>
                  {item.brand}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-primary)', lineHeight: 1.4, marginBottom: '6px', fontWeight: 300 }}>
                  {item.name}
                </div>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  &#163;{item.price.toFixed(2)}
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
