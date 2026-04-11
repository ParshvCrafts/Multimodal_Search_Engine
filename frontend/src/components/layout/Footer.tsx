export default function Footer() {
  return (
    <footer style={{
      padding: '44px 56px',
      background: 'var(--bg-secondary)',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      borderTop: '1px solid var(--border-hard)',
    }}>
      <span style={{
        fontFamily: "'Georgia', serif",
        fontSize: '14px',
        letterSpacing: '0.4em',
        textTransform: 'uppercase',
        color: 'var(--text-primary)',
        fontWeight: 300,
      }}>
        Interlace
      </span>
      <span style={{
        fontSize: '13px',
        letterSpacing: '0.1em',
        color: 'var(--text-primary)',
      }}>
        FashionCLIP · FAISS · BM25 · Built at UC Berkeley
      </span>
    </footer>
  )
}
