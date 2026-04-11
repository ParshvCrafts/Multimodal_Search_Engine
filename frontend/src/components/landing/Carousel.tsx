'use client'
import { useEffect, useRef, useState } from 'react'
import { MOCK_PRODUCTS } from '@/lib/mock-data'

const REAL_CARDS = MOCK_PRODUCTS.slice(0, 6)
const CLONE_CARDS = MOCK_PRODUCTS.slice(0, 4)
const ALL_CARDS = [...REAL_CARDS, ...CLONE_CARDS]
const TOTAL_REAL = REAL_CARDS.length  // 6
const VISIBLE = 4
const GAP = 20

export default function Carousel() {
  const trackRef = useRef<HTMLDivElement>(null)
  const [current, setCurrent] = useState(0)
  const busyRef = useRef(false)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const cardWidth = () => {
    const card = trackRef.current?.querySelector('.carousel-card') as HTMLElement | null
    return card ? card.offsetWidth + GAP : 0
  }

  const goTo = (idx: number, animate = true) => {
    const track = trackRef.current
    if (!track) return
    if (!animate) {
      track.style.transition = 'none'
    }
    track.style.transform = `translateX(-${idx * cardWidth()}px)`
    setCurrent(idx)
    if (!animate) {
      track.getBoundingClientRect()
      track.style.transition = 'transform 0.75s cubic-bezier(0.25, 0.46, 0.45, 0.94)'
    }
  }

  const advance = () => {
    if (busyRef.current) return
    const next = current + 1
    if (next > TOTAL_REAL - VISIBLE) {
      busyRef.current = true
      goTo(next, true)
      const track = trackRef.current!
      const handler = () => {
        track.removeEventListener('transitionend', handler)
        goTo(0, false)
        busyRef.current = false
      }
      track.addEventListener('transitionend', handler)
    } else {
      goTo(next)
    }
  }

  const retreat = () => {
    if (busyRef.current) return
    if (current === 0) {
      busyRef.current = true
      const max = TOTAL_REAL - VISIBLE
      goTo(max + 1, false)
      requestAnimationFrame(() => requestAnimationFrame(() => {
        goTo(max, true)
        const track = trackRef.current!
        const handler = () => {
          track.removeEventListener('transitionend', handler)
          busyRef.current = false
        }
        track.addEventListener('transitionend', handler)
      }))
    } else {
      goTo(current - 1)
    }
  }

  const resetTimer = () => {
    if (timerRef.current) clearInterval(timerRef.current)
    timerRef.current = setInterval(advance, 3500)
  }

  useEffect(() => {
    resetTimer()
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [current])

  const activeDot = Math.min(Math.floor(current / 2), 2)

  return (
    <div style={{ padding: '80px 0', background: 'var(--bg-primary)', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
        padding: '0 56px 28px', marginBottom: '44px',
        borderBottom: '1px solid #151515',
      }}>
        <span style={{
          fontFamily: "'Georgia', serif", fontSize: '36px',
          color: 'var(--text-primary)', fontWeight: 300, letterSpacing: '-0.01em',
        }}>
          Featured Pieces
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ fontSize: '13px', letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
            View all
          </span>
          {[
            { label: '\u2190', action: () => { retreat(); resetTimer() } },
            { label: '\u2192', action: () => { advance(); resetTimer() } },
          ].map(({ label, action }) => (
            <button key={label} onClick={action} style={{
              width: '44px', height: '44px',
              border: '1px solid #2a2a2a', background: 'transparent',
              color: '#888', fontSize: '16px', cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'all 0.25s',
            }}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Viewport */}
      <div style={{ overflow: 'hidden', padding: '0 56px' }}>
        <div
          ref={trackRef}
          style={{
            display: 'flex',
            gap: `${GAP}px`,
            transition: 'transform 0.75s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
            willChange: 'transform',
          }}
        >
          {ALL_CARDS.map((card, i) => (
            <div key={`${card.sku}-${i}`} className="carousel-card" style={{
              flex: `0 0 calc((100% - ${GAP * (VISIBLE - 1)}px) / ${VISIBLE})`,
              background: 'var(--bg-card)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              transition: 'transform 0.4s cubic-bezier(0.25,0.46,0.45,0.94)',
            }}>
              {/* Image */}
              <div style={{
                width: '100%', aspectRatio: '3/4',
                background: '#161616',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}>
                <span style={{ fontSize: '11px', letterSpacing: '0.2em', color: '#2a2a2a', textTransform: 'uppercase' }}>
                  Product Image
                </span>
              </div>
              {/* Body */}
              <div style={{ padding: '18px 2px 2px', display: 'flex', flexDirection: 'column', flex: 1 }}>
                <div style={{ fontSize: '11px', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--accent)', marginBottom: '7px' }}>
                  {card.brand}
                </div>
                <div style={{ fontSize: '13px', color: 'var(--text-primary)', lineHeight: 1.5, fontWeight: 300, flex: 1, marginBottom: '12px' }}>
                  {card.name}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
                  <span style={{ fontSize: '13px', color: '#888' }}>&pound;{card.price.toFixed(2)}</span>
                  <span style={{ fontSize: '11px', letterSpacing: '0.14em', textTransform: 'uppercase', color: '#444' }}>{card.category}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Dots */}
      <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginTop: '44px' }}>
        {[0, 1, 2].map(i => (
          <button
            key={i}
            onClick={() => { goTo(i * 2); resetTimer() }}
            style={{
              height: '2px',
              width: activeDot === i ? '56px' : '28px',
              background: activeDot === i ? 'var(--accent)' : '#222',
              border: 'none', padding: 0, cursor: 'pointer',
              transition: 'background 0.3s, width 0.35s',
            }}
          />
        ))}
      </div>
    </div>
  )
}
