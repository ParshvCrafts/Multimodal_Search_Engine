'use client'
import { useEffect, useRef, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'

export default function Hero() {
  const titleRef = useRef<HTMLHeadingElement>(null)
  const heroImgRef = useRef<HTMLImageElement>(null)
  const router = useRouter()
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageError, setImageError] = useState(false)

  useEffect(() => {
    import('gsap').then(({ gsap }) => {
      if (!titleRef.current) return
      const words = titleRef.current.querySelectorAll('.hero-word')
      gsap.fromTo(words,
        { y: 40, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.9, stagger: 0.12, ease: 'power3.out', delay: 0.2 }
      )
    })
    const img = heroImgRef.current
    if (img) {
      if (img.complete && img.naturalWidth > 0) setImageLoaded(true)
      else if (img.complete && img.naturalWidth === 0) setImageError(true)
    }
  }, [])

  const onHeroLoad = useCallback(() => setImageLoaded(true), [])
  const onHeroError = useCallback(() => setImageError(true), [])

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

      {/* Hero image — spans 80% on the right */}
      <div style={{
        position: 'absolute',
        top: 0, right: 0, bottom: 0,
        width: '75%',
        overflow: 'hidden',
        zIndex: 2,
      }}>
        {/* Image — always in the tree; opacity controls visibility */}
        <img
          ref={heroImgRef}
          src="/main.png?v=2"
          alt="Interlace Fashion"
          onLoad={onHeroLoad}
          onError={onHeroError}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: 'center center',
            display: 'block',
            opacity: imageLoaded ? 1 : 0,
            transition: 'opacity 0.6s ease',
          }}
        />

        {/* Error placeholder — always in the tree; opacity controls visibility */}
        <div style={{
          position: 'absolute',
          top: 0, right: 0, bottom: 0, left: 0,
          background: 'var(--bg-card)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          opacity: imageError ? 1 : 0,
          pointerEvents: imageError ? 'auto' : 'none',
          transition: 'opacity 0.3s ease',
        }}>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '16px',
            padding: '40px',
          }}>
            <div style={{
              width: '80px',
              height: '80px',
              border: '1px solid #222',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '28px',
              color: '#333',
            }}>
              ✦
            </div>
            <span style={{
              fontSize: '11px',
              letterSpacing: '0.25em',
              color: '#333',
              textTransform: 'uppercase',
              textAlign: 'center',
              lineHeight: 1.8,
            }}>
              Add your brand image<br/>
              <span style={{ color: '#555', letterSpacing: '0.15em', fontSize: '10px' }}>
                Place <code style={{ background: '#1a1a1a', padding: '2px 6px', borderRadius: '2px', color: 'var(--accent)' }}>main.png</code> in{' '}
                <code style={{ background: '#1a1a1a', padding: '2px 6px', borderRadius: '2px', color: 'var(--accent)' }}>frontend/public/</code>
              </span>
            </span>
          </div>
        </div>

        {/* Gradient fade — left edge dissolves into background */}
        <div style={{
          position: 'absolute',
          top: 0, bottom: 0, left: 0,
          width: '50%',
          background: 'linear-gradient(to right, var(--bg-primary) 0%, var(--bg-primary) 12%, rgba(8,8,8,0.65) 28%, rgba(8,8,8,0.4) 60%, transparent 100%)',
          pointerEvents: 'none',
          zIndex: 1,
        }} />
        {/* Top-edge vignette */}
        <div style={{
          position: 'absolute',
          top: 0, left: 0, right: 0,
          height: '70px',
          background: 'linear-gradient(to bottom, var(--bg-primary) 0%, transparent 100%)',
          pointerEvents: 'none',
          zIndex: 1,
        }} />
        {/* Bottom-edge vignette */}
        <div style={{
          position: 'absolute',
          bottom: 0, left: 0, right: 0,
          height: '120px',
          background: 'linear-gradient(to top, var(--bg-primary) 0%, transparent 100%)',
          pointerEvents: 'none',
          zIndex: 1,
        }} />
      </div>

      {/* Main content — text side */}
      <div style={{
        position: 'relative',
        zIndex: 3,
        padding: '0 56px 0 clamp(80px, 8vw, 140px)',
        maxWidth: '48%',
      }}>
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
