'use client'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

export default function SearchTeaser() {
  const router = useRouter()
  const [query, setQuery] = useState('')

  const handleSearch = () => {
    const q = query.trim()
    router.push(q ? `/search?q=${encodeURIComponent(q)}` : '/search')
  }

  return (
    <div style={{
      padding: '110px 56px',
      background: 'var(--bg-teaser)',
      textAlign: 'center',
      borderTop: '1px solid #181818',
    }}>
      <div style={{ fontSize: '12px', letterSpacing: '0.3em', textTransform: 'uppercase', color: 'var(--accent)', marginBottom: '24px' }}>
        The Search Engine
      </div>
      <h2 style={{
        fontFamily: "'Georgia', serif",
        fontSize: 'clamp(38px, 5vw, 58px)',
        color: 'var(--text-primary)',
        fontWeight: 300,
        letterSpacing: '-0.02em',
        marginBottom: '20px',
        lineHeight: 1.1,
      }}>
        Find it with<br />
        <em style={{ fontStyle: 'italic', color: 'var(--accent-soft)' }}>words, images,</em><br />
        or both.
      </h2>
      <p style={{
        fontSize: '16px',
        color: '#888',
        marginBottom: '52px',
        letterSpacing: '0.02em',
        lineHeight: 1.65,
      }}>
        Powered by FashionCLIP, FAISS, and BM25. Multimodal fashion retrieval at scale.
      </p>
      <div style={{
        maxWidth: '640px',
        margin: '0 auto',
        display: 'flex',
        border: '1px solid #272727',
        background: '#0f0f0f',
      }}>
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
          placeholder='Try "red floral summer dress"...'
          style={{
            flex: 1,
            padding: '19px 26px',
            fontFamily: "'Palatino Linotype', Palatino, 'Book Antiqua', Georgia, serif",
            fontStyle: 'italic',
            fontSize: '15px',
            color: 'var(--text-primary)',
            background: 'transparent',
            border: 'none',
            outline: 'none',
            letterSpacing: '0.03em',
          }}
        />
        <div style={{ width: '1px', background: '#222', flexShrink: 0 }} />
        <span style={{ padding: '19px 22px', fontSize: '14px', color: '#777', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
          Upload
        </span>
        <button
          onClick={handleSearch}
          style={{
            padding: '19px 30px',
            background: 'var(--text-primary)',
            fontSize: '12px',
            letterSpacing: '0.2em',
            textTransform: 'uppercase',
            color: 'var(--bg-primary)',
            border: 'none',
            cursor: 'pointer',
            whiteSpace: 'nowrap',
          }}
        >
          Search
        </button>
      </div>
    </div>
  )
}
