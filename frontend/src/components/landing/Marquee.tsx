const ITEMS = [
  'Visual Search',
  'Text + Image Hybrid',
  'FashionCLIP',
  'FAISS Index',
  'Multilingual',
  'Outfit Recommendations',
  'BM25 Hybrid Ranking',
  'NLU Intent Parsing',
]

export default function Marquee() {
  const doubled = [...ITEMS, ...ITEMS]
  return (
    <div style={{
      background: 'var(--bg-secondary)',
      borderTop: '1px solid #181818',
      borderBottom: '1px solid #181818',
      padding: '17px 0',
      overflow: 'hidden',
      whiteSpace: 'nowrap',
    }}>
      <div className="animate-marquee" style={{ display: 'inline-flex' }}>
        {doubled.map((item, i) => (
          <span key={i} style={{
            fontSize: '12px',
            letterSpacing: '0.25em',
            textTransform: 'uppercase',
            color: 'var(--text-primary)',
            padding: '0 44px',
            borderRight: '1px solid var(--border-soft)',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}>
            <span style={{
              width: '4px', height: '4px', borderRadius: '50%',
              background: 'var(--accent)', flexShrink: 0,
            }} />
            {item}
          </span>
        ))}
      </div>
    </div>
  )
}
