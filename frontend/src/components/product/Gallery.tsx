'use client'
import { useState } from 'react'

interface Props {
  imageUrls: string[]
  score?: number
  productName: string
}

export default function Gallery({ imageUrls, score, productName }: Props) {
  const [activeThumb, setActiveThumb] = useState(0)
  const thumbs = imageUrls.length >= 4 ? imageUrls.slice(0, 4) : ['', '', '', '']

  return (
    <div style={{ padding: '40px 40px 40px 56px', background: 'var(--bg-primary)' }}>
      {/* Main image: 86% width, 3/4 aspect ratio */}
      <div style={{
        width: '86%',
        aspectRatio: '3/4',
        background: 'var(--bg-card)',
        position: 'relative',
        border: '1px solid var(--border-hard)',
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <span style={{ fontSize: '11px', letterSpacing: '0.25em', color: '#222', textTransform: 'uppercase' }}>
          {productName}
        </span>

        {/* Match score badge - top left */}
        {score !== undefined && (
          <div style={{
            position: 'absolute', top: '16px', left: '16px',
            fontSize: '10px', letterSpacing: '0.12em', textTransform: 'uppercase',
            background: 'rgba(8,8,8,0.88)', color: 'var(--accent)',
            padding: '5px 10px', border: '1px solid rgba(201,169,110,0.3)', zIndex: 2,
            pointerEvents: 'none',
          }}>
            {Math.round(score * 100)}% match
          </div>
        )}
      </div>

      {/* 4 thumbnails */}
      <div style={{ display: 'flex', gap: '10px', marginTop: '14px' }}>
        {thumbs.map((_, i) => (
          <div
            key={i}
            onClick={() => setActiveThumb(i)}
            style={{
              width: '92px',
              aspectRatio: '3/4',
              background: 'var(--bg-card)',
              border: `1px solid ${activeThumb === i ? 'var(--accent)' : '#1e1e1e'}`,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'border-color 0.2s',
              flexShrink: 0,
              overflow: 'hidden',
            }}
          >
            <span style={{ fontSize: '9px', letterSpacing: '0.15em', color: '#222', textTransform: 'uppercase' }}>
              {i + 1}
            </span>
          </div>
        ))}
      </div>

      <div style={{ marginTop: '12px', fontSize: '11px', color: '#2e2e2e', letterSpacing: '0.1em', display: 'flex', alignItems: 'center', gap: '7px' }}>
        <span style={{ fontSize: '13px' }}>+</span> Hover to zoom
      </div>
    </div>
  )
}
