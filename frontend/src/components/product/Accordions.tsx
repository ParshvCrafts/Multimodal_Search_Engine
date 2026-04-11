'use client'
import { useState } from 'react'
import type { ProductDetail } from '@/lib/types'

interface Props { product: ProductDetail }

export default function Accordions({ product }: Props) {
  const [openId, setOpenId] = useState<string | null>(null)

  const sections = [
    {
      id: 'details',
      title: 'Product Details',
      content: product.description ?? 'Premium quality construction with attention to detail.',
      type: 'text' as const,
    },
    {
      id: 'care',
      title: 'Materials and Care',
      content: product.care_instructions ?? ['Machine wash cold', 'Do not tumble dry', 'Cool iron if needed', 'Do not bleach'],
      type: 'list' as const,
    },
    {
      id: 'sizing',
      title: 'Sizing and Fit',
      content: product.sizing_info ?? 'True to size. We recommend ordering your usual size.',
      type: 'text' as const,
    },
    {
      id: 'delivery',
      title: 'Delivery and Returns',
      content: product.delivery_info ?? 'Free standard delivery on orders over £35. Free returns within 28 days.',
      type: 'text' as const,
    },
  ]

  return (
    <div>
      {sections.map(({ id, title, content, type }) => (
        <div key={id} style={{ borderTop: '1px solid var(--border-hard)' }}>
          <button
            onClick={() => setOpenId(openId === id ? null : id)}
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '16px 0', cursor: 'pointer', width: '100%',
              background: 'none', border: 'none',
            }}
          >
            <span style={{ fontSize: '12px', letterSpacing: '0.2em', textTransform: 'uppercase', color: '#888' }}>
              {title}
            </span>
            <span style={{
              fontSize: '11px', color: '#444',
              transform: openId === id ? 'rotate(45deg)' : 'none',
              transition: 'transform 0.25s', display: 'inline-block',
            }}>
              +
            </span>
          </button>
          <div style={{
            overflow: 'hidden',
            maxHeight: openId === id ? '300px' : 0,
            transition: 'max-height 0.35s ease',
          }}>
            <div style={{ paddingBottom: '18px', fontSize: '13px', color: '#888', lineHeight: 1.7, letterSpacing: '0.02em' }}>
              {type === 'list' && Array.isArray(content) ? (
                <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {(content as string[]).map((item, i) => (
                    <li key={i} style={{ display: 'flex', gap: '10px' }}>
                      <span style={{ color: '#333', flexShrink: 0 }}>-</span>
                      {item}
                    </li>
                  ))}
                </ul>
              ) : (
                <p>{content as string}</p>
              )}
            </div>
          </div>
        </div>
      ))}
      <div style={{ borderBottom: '1px solid var(--border-hard)' }} />
    </div>
  )
}
