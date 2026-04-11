'use client'
import { useState } from 'react'
import type { SortOption } from '@/lib/types'

interface Props {
  topN: number
  onTopNChange: (n: number) => void
  sort: SortOption
  onSortChange: (s: SortOption) => void
  view: 'grid' | 'list'
  onViewChange: (v: 'grid' | 'list') => void
  activeFilters: Record<string, string>
  onRemoveFilter: (key: string) => void
}

const FILTER_LABELS = ['Gender', 'Category', 'Color', 'Price', 'Size']
const TOP_N_OPTIONS = [5, 10, 20, 25, 50, 75, 100]
const SORT_OPTIONS: { label: string; value: SortOption }[] = [
  { label: 'Relevance', value: 'relevance' },
  { label: 'Price: Low', value: 'price_asc' },
  { label: 'Price: High', value: 'price_desc' },
]

export default function FilterBar({
  topN, onTopNChange, sort, onSortChange, view, onViewChange, activeFilters, onRemoveFilter,
}: Props) {
  const [openFilter, setOpenFilter] = useState<string | null>(null)

  return (
    <div style={{
      background: 'var(--bg-secondary)',
      borderBottom: '1px solid #181818',
      padding: '0 56px',
      display: 'flex',
      alignItems: 'center',
      overflowX: 'auto',
      minHeight: '54px',
      flexWrap: 'nowrap',
    }}>
      {/* Filter buttons */}
      {FILTER_LABELS.map(label => (
        <button
          key={label}
          onClick={() => setOpenFilter(openFilter === label ? null : label)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '7px',
            padding: '0 20px',
            height: '54px',
            fontSize: '12px',
            letterSpacing: '0.15em',
            textTransform: 'uppercase',
            color: openFilter === label ? 'var(--text-primary)' : '#777',
            cursor: 'pointer',
            background: 'transparent',
            border: 'none',
            borderRight: '1px solid #181818',
            whiteSpace: 'nowrap',
            boxShadow: openFilter === label ? 'inset 0 -2px 0 var(--text-primary)' : 'none',
            transition: 'color 0.2s',
            flexShrink: 0,
          }}
        >
          {label}
          <span style={{ fontSize: '9px', opacity: 0.4 }}>v</span>
        </button>
      ))}

      {/* Active filter chips */}
      {Object.entries(activeFilters).map(([key, val]) => (
        <div key={key} style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '5px 12px',
          background: '#1a1a1a',
          border: '1px solid #2a2a2a',
          fontSize: '11px',
          letterSpacing: '0.12em',
          textTransform: 'uppercase',
          color: 'var(--text-primary)',
          whiteSpace: 'nowrap',
          marginLeft: '8px',
          flexShrink: 0,
        }}>
          {val}
          <span
            onClick={() => onRemoveFilter(key)}
            style={{ fontSize: '10px', color: '#666', cursor: 'pointer', marginLeft: '2px' }}
          >
            x
          </span>
        </div>
      ))}

      {/* Right controls */}
      <div style={{ display: 'flex', alignItems: 'center', marginLeft: 'auto', flexShrink: 0 }}>
        {/* Retrieve selector */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '0 20px',
          borderRight: '1px solid #181818',
          height: '54px',
        }}>
          <span style={{ fontSize: '11px', letterSpacing: '0.15em', textTransform: 'uppercase', color: '#555', whiteSpace: 'nowrap' }}>
            Retrieve
          </span>
          <select
            value={topN}
            onChange={e => onTopNChange(Number(e.target.value))}
            style={{
              background: '#141414',
              border: '1px solid #2a2a2a',
              color: 'var(--text-primary)',
              fontSize: '12px',
              padding: '5px 10px',
              cursor: 'pointer',
              outline: 'none',
              appearance: 'none',
              WebkitAppearance: 'none',
            }}
          >
            {TOP_N_OPTIONS.map(n => (
              <option key={n} value={n}>{n} results</option>
            ))}
          </select>
        </div>

        {/* Sort buttons */}
        {SORT_OPTIONS.map(({ label, value }) => (
          <button
            key={value}
            onClick={() => onSortChange(value)}
            style={{
              padding: '0 16px',
              height: '54px',
              fontSize: '12px',
              letterSpacing: '0.15em',
              textTransform: 'uppercase',
              color: sort === value ? 'var(--text-primary)' : '#555',
              cursor: 'pointer',
              background: 'transparent',
              border: 'none',
              borderRight: '1px solid #181818',
              transition: 'color 0.2s',
              whiteSpace: 'nowrap',
            }}
          >
            {label}
          </button>
        ))}

        {/* View toggle */}
        {[
          { v: 'grid' as const, icon: '⊞' },
          { v: 'list' as const, icon: '≡' },
        ].map(({ v, icon }) => (
          <button
            key={v}
            onClick={() => onViewChange(v)}
            style={{
              width: '44px',
              height: '54px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              border: 'none',
              background: 'transparent',
              color: view === v ? 'var(--text-primary)' : '#444',
              fontSize: '14px',
              borderLeft: '1px solid #181818',
              transition: 'color 0.2s',
            }}
          >
            {icon}
          </button>
        ))}
      </div>
    </div>
  )
}
