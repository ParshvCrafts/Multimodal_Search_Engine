const FEATURES = [
  {
    num: '01',
    title: 'Visual Search',
    desc: 'Upload any image and find visually similar items using FashionCLIP embeddings trained on fashion data.',
  },
  {
    num: '02',
    title: 'Text Intelligence',
    desc: 'Natural language queries with NLU parsing. Extracts color, gender, occasion, and price range automatically.',
  },
  {
    num: '03',
    title: 'Hybrid Ranking',
    desc: 'CLIP semantic scores fused with BM25 lexical recall for the best precision and coverage across all queries.',
  },
  {
    num: '04',
    title: 'Outfit Discovery',
    desc: 'Complementary item suggestions to find pieces that complete your look, powered by semantic similarity.',
  },
]

export default function Features() {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(4, 1fr)',
      background: 'var(--bg-secondary)',
      borderBottom: '1px solid #181818',
    }}>
      {FEATURES.map((f, i) => (
        <div key={i} style={{
          padding: '48px 40px',
          borderRight: i < 3 ? '1px solid #181818' : 'none',
        }}>
          <div style={{
            fontSize: '11px', letterSpacing: '0.22em',
            color: 'var(--accent)', marginBottom: '18px',
          }}>
            {f.num}
          </div>
          <div style={{
            fontFamily: "'Georgia', serif", fontSize: '21px',
            color: 'var(--text-primary)', fontWeight: 300,
            marginBottom: '14px', lineHeight: 1.3,
          }}>
            {f.title}
          </div>
          <div style={{
            fontSize: '14px', color: 'var(--text-secondary)',
            lineHeight: 1.8, letterSpacing: '0.02em',
          }}>
            {f.desc}
          </div>
        </div>
      ))}
    </div>
  )
}
