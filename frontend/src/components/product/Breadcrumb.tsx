'use client'
import { useRouter } from 'next/navigation'

interface Props { name: string; category: string; gender: string }

export default function Breadcrumb({ name, category, gender }: Props) {
  const router = useRouter()
  return (
    <div style={{
      padding: '20px 56px',
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      borderBottom: '1px solid var(--border-hard)',
      background: 'var(--bg-primary)',
      flexWrap: 'wrap',
    }}>
      <button
        onClick={() => router.back()}
        style={{
          display: 'flex', alignItems: 'center', gap: '8px',
          fontSize: '12px', letterSpacing: '0.15em', textTransform: 'uppercase',
          color: '#555', cursor: 'pointer', background: 'none', border: 'none',
          transition: 'color 0.2s', padding: 0,
        }}
      >
        <span style={{ fontSize: '14px' }}>&#8592;</span> Back to results
      </button>
      {[gender, category, name].map((item, i) => (
        <span key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ color: '#2a2a2a', fontSize: '10px' }}>&#8250;</span>
          <span style={{
            fontSize: '12px', letterSpacing: '0.12em', textTransform: 'uppercase',
            color: i === 2 ? '#888' : '#555',
            cursor: i < 2 ? 'pointer' : 'default',
          }}>
            {item}
          </span>
        </span>
      ))}
    </div>
  )
}
