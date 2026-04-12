'use client'
import { useRef, useState } from 'react'
import type { SearchMode } from '@/lib/types'

interface Props {
  onSearch: (query: string, imageFile?: File) => void
  loading: boolean
  initialQuery?: string
}

export default function SearchBar({ onSearch, loading, initialQuery = '' }: Props) {
  const [query, setQuery] = useState(initialQuery)
  const [imageFile, setImageFile] = useState<File | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const mode: SearchMode = query && imageFile ? 'multimodal' : imageFile ? 'image' : 'text'

  const modeDotColor = {
    text: '#c9a96e',
    image: '#7a9ec9',
    multimodal: '#9a7ac9',
  }[mode]

  const modeLabel = { text: 'Text', image: 'Image', multimodal: 'Multimodal' }[mode]

  const handleSubmit = () => {
    if (!query && !imageFile) return
    onSearch(query, imageFile ?? undefined)
  }

  return (
    <div style={{ padding: '48px 56px 32px', background: 'var(--bg-primary)', borderBottom: '1px solid #181818' }}>
      <div style={{ fontSize: '11px', letterSpacing: '0.3em', textTransform: 'uppercase', color: 'var(--accent)', marginBottom: '18px' }}>
        Search
      </div>
      <h1 style={{
        fontFamily: "'Georgia', serif",
        fontSize: '32px',
        fontWeight: 300,
        color: 'var(--text-primary)',
        marginBottom: '28px',
        letterSpacing: '-0.01em',
      }}>
        Find it with <em style={{ fontStyle: 'italic', color: 'var(--accent-soft)' }}>words, images,</em> or both.
      </h1>

      <div style={{
        display: 'flex',
        width: '100%',
        border: '1px solid #2a2a2a',
        background: 'var(--bg-card)',
      }}>
        {/* Text input */}
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSubmit()}
          placeholder="Describe what you are looking for..."
          style={{
            flex: 1,
            padding: '18px 24px',
            fontFamily: "'Palatino Linotype', Palatino, 'Book Antiqua', Georgia, serif",
            fontStyle: 'italic',
            fontSize: '17px',
            color: 'var(--text-primary)',
            background: 'transparent',
            border: 'none',
            outline: 'none',
            letterSpacing: '0.01em',
          }}
        />

        {/* Mode indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          padding: '0 16px',
          gap: '7px',
          fontSize: '11px',
          letterSpacing: '0.14em',
          textTransform: 'uppercase',
          color: '#555',
          borderLeft: '1px solid #1e1e1e',
          flexShrink: 0,
        }}>
          <span style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            background: modeDotColor,
            flexShrink: 0,
            transition: 'background 0.3s',
          }} />
          {modeLabel}
        </div>

        <div style={{ width: '1px', background: '#1e1e1e', flexShrink: 0 }} />

        {/* Image upload button */}
        <button
          onClick={() => fileRef.current?.click()}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '18px 22px',
            fontSize: '12px',
            letterSpacing: '0.15em',
            textTransform: 'uppercase',
            color: imageFile ? 'var(--accent)' : '#666',
            cursor: 'pointer',
            border: 'none',
            background: 'transparent',
            whiteSpace: 'nowrap',
            transition: 'color 0.2s',
          }}
        >
          {imageFile ? `${imageFile.name.slice(0, 14)}...` : 'Upload Image'}
        </button>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          style={{ display: 'none' }}
          onChange={e => setImageFile(e.target.files?.[0] ?? null)}
        />

        {/* Clear image button */}
        {imageFile && (
          <button
            onClick={() => setImageFile(null)}
            style={{
              padding: '0 12px',
              background: 'transparent',
              border: 'none',
              color: '#555',
              cursor: 'pointer',
              fontSize: '14px',
              transition: 'color 0.2s',
            }}
          >
            x
          </button>
        )}

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={loading}
          style={{
            padding: '18px 32px',
            background: loading ? '#555' : 'var(--text-primary)',
            fontSize: '12px',
            letterSpacing: '0.2em',
            textTransform: 'uppercase',
            color: 'var(--bg-primary)',
            border: 'none',
            cursor: loading ? 'not-allowed' : 'pointer',
            whiteSpace: 'nowrap',
            transition: 'background 0.2s',
          }}
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

    </div>
  )
}
