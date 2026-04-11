'use client'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useTheme } from '@/hooks/useTheme'

export default function Navbar() {
  const { theme, toggle } = useTheme()
  const router = useRouter()

  return (
    <nav style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 200,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 56px', height: '68px',
      background: 'var(--nav-bg)',
      backdropFilter: 'blur(12px)',
      WebkitBackdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--border-hard)',
      transition: 'background 0.3s',
    }}>
      <Link href="/" style={{
        fontFamily: "'Georgia', serif",
        fontSize: '17px',
        letterSpacing: '0.45em',
        textTransform: 'uppercase',
        fontWeight: 300,
        color: 'var(--text-primary)',
        textDecoration: 'none',
      }}>
        Interlace
      </Link>

      <div style={{ display: 'flex', alignItems: 'center', gap: '28px' }}>
        {['Collections', 'About', 'Technology'].map(label => (
          <Link key={label} href="/" style={{
            fontSize: '13px',
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            color: 'var(--text-secondary)',
            textDecoration: 'none',
            transition: 'color 0.2s',
          }}>
            {label}
          </Link>
        ))}

        <button
          onClick={() => router.push('/search')}
          style={{
            fontSize: '13px',
            letterSpacing: '0.15em',
            textTransform: 'uppercase',
            color: theme === 'dark' ? '#080808' : '#f5f0e8',
            background: theme === 'dark' ? '#e8e2d9' : '#1a1a1a',
            padding: '10px 24px',
            border: 'none',
            cursor: 'pointer',
            whiteSpace: 'nowrap',
            transition: 'background 0.3s, color 0.3s',
          }}
        >
          Search
        </button>

        <button
          onClick={toggle}
          title="Toggle light / dark mode"
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            background: theme === 'dark' ? '#1a1a1a' : '#e0d9ce',
            border: `1px solid ${theme === 'dark' ? '#2e2e2e' : '#c8bfb2'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            fontSize: '16px',
            lineHeight: '1',
            transition: 'background 0.3s, border-color 0.3s, transform 0.35s',
            flexShrink: 0,
          }}
        >
          {theme === 'dark' ? '🌙' : '☀️'}
        </button>
      </div>
    </nav>
  )
}
