'use client'
import { useEffect, useRef, useState } from 'react'
import { MOCK_PRODUCTS } from '@/lib/mock-data'

const REAL_CARDS = MOCK_PRODUCTS.slice(0, 6)
// 2 leading clones (last 2 real cards) enable seamless backward wrap
const LEAD_CLONES = REAL_CARDS.slice(-2)
// 4 trailing clones (first 4 real cards) enable seamless forward wrap
const TRAIL_CLONES = REAL_CARDS.slice(0, 4)
const ALL_CARDS = [...LEAD_CLONES, ...REAL_CARDS, ...TRAIL_CLONES]
// Indices: [0=R4, 1=R5, 2=R0, 3=R1, 4=R2, 5=R3, 6=R4, 7=R5, 8=R0, 9=R1, 10=R2, 11=R3]
const OFFSET = LEAD_CLONES.length   // 2 — first real card lives at this index
const TOTAL_REAL = REAL_CARDS.length  // 6
const VISIBLE = 4
const GAP = 20
const MIN_IDX = OFFSET                           // 2
const MAX_IDX = OFFSET + TOTAL_REAL - VISIBLE    // 4

export default function Carousel() {
  const trackRef = useRef<HTMLDivElement>(null)
  const [current, setCurrent] = useState(MIN_IDX)
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
      track.getBoundingClientRect() // force reflow to flush the transition removal
      track.style.transition = 'transform 0.75s cubic-bezier(0.25, 0.46, 0.45, 0.94)'
    }
  }

  const withTransitionEnd = (cb: () => void) => {
    const track = trackRef.current!
    const handler = () => {
      track.removeEventListener('transitionend', handler)
      cb()
    }
    track.addEventListener('transitionend', handler)
  }

  const advance = () => {
    if (busyRef.current) return
    busyRef.current = true
    const next = current + 1
    if (next > MAX_IDX) {
      // Hit trailing clones — animate then snap back to MIN_IDX
      goTo(next, true)
      withTransitionEnd(() => {
        goTo(MIN_IDX, false)
        busyRef.current = false
      })
    } else {
      goTo(next, true)
      withTransitionEnd(() => { busyRef.current = false })
    }
  }

  const retreat = () => {
    if (busyRef.current) return
    busyRef.current = true
    const prev = current - 1
    if (prev < MIN_IDX) {
      // Hit leading clones — animate then snap forward to MAX_IDX
      goTo(prev, true)
      withTransitionEnd(() => {
        goTo(MAX_IDX, false)
        busyRef.current = false
      })
    } else {
      goTo(prev, true)
      withTransitionEnd(() => { busyRef.current = false })
    }
  }

  const resetTimer = () => {
    if (timerRef.current) clearInterval(timerRef.current)
    timerRef.current = setInterval(advance, 3500)
  }

  // Set initial scroll position to skip past leading clones (no animation)
  useEffect(() => {
    goTo(MIN_IDX, false)
  }, [])

  useEffect(() => {
    resetTimer()
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [current])

  // Dot 0 = MIN_IDX (2), dot 1 = MIN_IDX+1 (3), dot 2 = MAX_IDX (4)
  const activeDot = Math.max(0, Math.min(2, current - MIN_IDX))

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
                {card.image_url ? (
                  <img
                    src={card.image_url}
                    alt={card.name}
                    style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                  />
                ) : (
                  <span style={{ fontSize: '11px', letterSpacing: '0.2em', color: '#2a2a2a', textTransform: 'uppercase' }}>
                    Product Image
                  </span>
                )}
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
            onClick={() => { if (!busyRef.current) { goTo(MIN_IDX + i); resetTimer() } }}
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
