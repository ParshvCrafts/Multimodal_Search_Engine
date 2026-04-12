'use client'
import { useEffect, useRef, useState, useCallback } from 'react'
import Link from 'next/link'
import { FEATURED_PRODUCTS, type FeaturedProduct } from '@/lib/featured-products'

const CARDS: FeaturedProduct[] = FEATURED_PRODUCTS.slice(0, 8)
const VISIBLE = 4
const GAP = 20
const TOTAL = CARDS.length // 8

/*
 * Seamless infinite loop strategy:
 *
 * Track layout: [clone set] [REAL set] [clone set]
 *                 0..7        8..15       16..23
 *
 * We always start viewing from the REAL set (index 8).
 * When advancing past MAX_IDX into the trailing clones, we animate the
 * transition, then snap back to the equivalent leading-clone position.
 * Because the clones are visually identical, the snap is invisible.
 */
const ALL_CARDS = [...CARDS, ...CARDS, ...CARDS]
const OFFSET = TOTAL          // 8 — first real card
const MIN_IDX = OFFSET        // 8
const MAX_IDX = OFFSET + TOTAL - VISIBLE  // 12

export default function Carousel() {
  const trackRef = useRef<HTMLDivElement>(null)
  const [current, setCurrent] = useState(MIN_IDX)
  const busyRef = useRef(false)
  const hoveredRef = useRef(false)
  const [hovered, setHovered] = useState(false)

  // ── Helpers ────────────────────────────────────────────────────────────
  const cardWidth = (): number => {
    const card = trackRef.current?.querySelector('.carousel-card') as HTMLElement | null
    return card ? card.offsetWidth + GAP : 0
  }

  const goTo = (idx: number, animate: boolean) => {
    const track = trackRef.current
    if (!track) return
    if (!animate) {
      track.style.transition = 'none'
    }
    track.style.transform = `translateX(-${idx * cardWidth()}px)`
    setCurrent(idx)
    if (!animate) {
      // Force reflow so the instant move is applied before restoring transition
      void track.offsetHeight
      track.style.transition = 'transform 0.7s cubic-bezier(0.25, 0.46, 0.45, 0.94)'
    }
  }

  const onTransitionEnd = (cb: () => void) => {
    const track = trackRef.current
    if (!track) return
    const handler = () => {
      track.removeEventListener('transitionend', handler)
      cb()
    }
    track.addEventListener('transitionend', handler)
  }

  // ── Navigation ─────────────────────────────────────────────────────────
  const advance = useCallback(() => {
    if (busyRef.current) return
    busyRef.current = true
    const next = current + 1

    goTo(next, true)

    if (next > MAX_IDX) {
      // Animated into trailing clone → snap to equivalent leading-clone pos
      onTransitionEnd(() => {
        goTo(next - TOTAL, false)
        busyRef.current = false
      })
    } else {
      onTransitionEnd(() => { busyRef.current = false })
    }
  }, [current])

  const retreat = useCallback(() => {
    if (busyRef.current) return
    busyRef.current = true
    const prev = current - 1

    goTo(prev, true)

    if (prev < MIN_IDX) {
      // Animated into leading clone → snap to equivalent trailing-clone pos
      onTransitionEnd(() => {
        goTo(prev + TOTAL, false)
        busyRef.current = false
      })
    } else {
      onTransitionEnd(() => { busyRef.current = false })
    }
  }, [current])

  // ── Lifecycle ──────────────────────────────────────────────────────────

  // Set initial position (skip leading clones, no animation)
  useEffect(() => {
    goTo(MIN_IDX, false)
  }, [])

  // Auto-advance every 3.5s — pauses when hovered
  useEffect(() => {
    if (hovered) return
    const id = setInterval(() => {
      if (!busyRef.current && !hoveredRef.current) {
        advance()
      }
    }, 3500)
    return () => clearInterval(id)
  }, [current, hovered, advance])

  // ── Hover pause ────────────────────────────────────────────────────────
  const handleMouseEnter = useCallback(() => {
    hoveredRef.current = true
    setHovered(true)
  }, [])

  const handleMouseLeave = useCallback(() => {
    hoveredRef.current = false
    setHovered(false)
  }, [])

  // ── Dot indicator ──────────────────────────────────────────────────────
  const DOT_COUNT = TOTAL - VISIBLE + 1 // 5 positions
  const normalizedPos = ((current - MIN_IDX) % TOTAL + TOTAL) % TOTAL
  const activeDot = Math.min(normalizedPos, DOT_COUNT - 1)

  const jumpToDot = (dotIdx: number) => {
    if (busyRef.current) return
    busyRef.current = true
    goTo(MIN_IDX + dotIdx, true)
    onTransitionEnd(() => { busyRef.current = false })
  }

  // ── Render ─────────────────────────────────────────────────────────────
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
          <Link href="/search" style={{
            fontSize: '13px', letterSpacing: '0.18em', textTransform: 'uppercase',
            color: 'var(--text-secondary)', textDecoration: 'none', transition: 'color 0.2s',
          }}>
            View all
          </Link>
          {[
            { label: '\u2190', action: retreat },
            { label: '\u2192', action: advance },
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

      {/* Carousel viewport */}
      <div
        style={{ overflow: 'hidden', padding: '0 56px' }}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        <div
          ref={trackRef}
          style={{
            display: 'flex',
            gap: `${GAP}px`,
            transition: 'transform 0.7s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
            willChange: 'transform',
          }}
        >
          {ALL_CARDS.map((card, i) => (
            <Link
              key={`${card.sku}-${i}`}
              href={`/products/${card.sku}`}
              style={{
                textDecoration: 'none',
                display: 'block',
                flex: `0 0 calc((100% - ${GAP * (VISIBLE - 1)}px) / ${VISIBLE})`,
              }}
            >
              <div className="carousel-card" style={{
                background: 'var(--bg-card)',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.4s cubic-bezier(0.25,0.46,0.45,0.94), border-color 0.25s',
                border: '1px solid transparent',
              }}>
                {/* Image */}
                <div style={{
                  width: '100%', aspectRatio: '3/4',
                  background: '#161616',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0,
                  overflow: 'hidden',
                }}>
                  {card.image_url ? (
                    <img
                      src={card.image_url}
                      alt={card.name}
                      loading="lazy"
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
                    <span style={{ fontSize: '11px', letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>{card.category}</span>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Dots */}
      <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginTop: '44px' }}>
        {Array.from({ length: DOT_COUNT }, (_, i) => (
          <button
            key={i}
            onClick={() => jumpToDot(i)}
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
