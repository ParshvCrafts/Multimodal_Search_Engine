'use client'
import { useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'

export default function Hero() {
  const titleRef = useRef<HTMLHeadingElement>(null)
  const router = useRouter()

  useEffect(() => {
    import('gsap').then(({ gsap }) => {
      if (!titleRef.current) return
      const words = titleRef.current.querySelectorAll('.hero-word')
      gsap.fromTo(words,
        { y: 40, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.9, stagger: 0.12, ease: 'power3.out', delay: 0.2 }
      )
    })
  }, [])

  return (
    <div style={{
      height: 'calc(92vh - 68px)',
      minHeight: '560px',
      position: 'relative',
      display: 'flex',
      alignItems: 'center',
      overflow: 'hidden',
      background: 'var(--bg-primary)',
    }}>
      {/* 5-column grid overlay */}
      <div style={{
        position: 'absolute', inset: 0,
        display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)',
        pointerEvents: 'none',
      }}>
        {[0,1,2,3,4].map(i => (
          <div key={i} style={{ borderRight: '1px solid var(--border-hard)' }} />
        ))}
      </div>

      {/* Right image panel */}
      <div style={{
        position: 'absolute', right: 0, top: 0, bottom: 0, width: '44%',
        background: 'var(--bg-card)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{ fontSize: '11px', letterSpacing: '0.25em', color: 'var(--border-soft)', textTransform: 'uppercase' }}>
          Hero Image
        </span>
        {/* Gradient fade on left edge */}
        <div style={{
          position: 'absolute', left: 0, top: 0, bottom: 0, width: '220px',
          background: 'linear-gradient(to right, var(--bg-primary) 0%, transparent 100%)',
          pointerEvents: 'none',
        }} />
      </div>

      {/* Main content */}
      <div style={{ position: 'relative', zIndex: 2, padding: '0 56px 0 96px', maxWidth: '60%' }}>
        {/* Eyebrow */}
        <div style={{
          fontSize: '12px', letterSpacing: '0.3em', textTransform: 'uppercase',
          color: 'var(--accent)', marginBottom: '28px',
          display: 'flex', alignItems: 'center', gap: '14px',
        }}>
          <span style={{ width: '36px', height: '1px', background: 'var(--accent)', display: 'block', flexShrink: 0 }} />
          AI-Powered Fashion Search
        </div>

        {/* H1 with GSAP targets */}
        <h1 ref={titleRef} style={{
          fontFamily: "'Georgia', serif",
          fontSize: 'clamp(52px, 7.5vw, 92px)',
          lineHeight: 0.92,
          letterSpacing: '-0.01em',
          color: 'var(--text-primary)',
          fontWeight: 300,
          marginBottom: '36px',
        }}>
          {[
            { text: 'Discover', italic: false },
            { text: 'exactly', italic: true },
            { text: 'what you', italic: false },
            { text: 'want.', italic: false },
          ].map((word, i) => (
            <span key={i} className="hero-word" style={{
              display: 'block',
              fontStyle: word.italic ? 'italic' : 'normal',
              color: word.italic ? 'var(--accent-soft)' : 'var(--text-primary)',
              opacity: 0,
            }}>
              {word.text}
            </span>
          ))}
        </h1>

        {/* Sub copy */}
        <p style={{
          fontSize: '16px', lineHeight: 1.75, color: 'var(--text-secondary)',
          maxWidth: '400px', marginBottom: '52px', letterSpacing: '0.02em',
        }}>
          Multimodal search that understands fashion. Describe it, photograph it, or just feel it. Interlace finds the perfect match.
        </p>

        {/* CTA */}
        <button
          onClick={() => router.push('/search')}
          style={{
            fontSize: '13px', letterSpacing: '0.2em', textTransform: 'uppercase',
            color: 'var(--bg-primary)', background: 'var(--text-primary)',
            padding: '15px 36px', border: 'none', cursor: 'pointer',
            transition: 'opacity 0.2s',
          }}
        >
          Explore Search
        </button>
      </div>
    </div>
  )
}
