'use client'
import { useState, useEffect, useRef, useCallback } from 'react'
import { createPortal } from 'react-dom'
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
  onFilterChange: (key: string, value: string | null) => void
}

const FILTER_OPTIONS: Record<string, string[]> = {
  Gender:   ['Women', 'Men'],
  Category: [
    'Dresses', 'Tops', 'Jeans', 'Trousers', 'Knitwear',
    'Coats & Jackets', 'Hoodies & Sweatshirts', 'Skirts', 'Shorts',
    'Shoes', 'Bags', 'Accessories', 'Suits & Tailoring',
    'Swimwear', 'Jumpsuits & Playsuits',
  ],
  Color: [
    'Black', 'White', 'Navy', 'Blue', 'Red', 'Pink', 'Green',
    'Grey', 'Brown', 'Beige', 'Yellow', 'Orange', 'Purple',
    'Burgundy', 'Khaki', 'Multi',
  ],
  Size:  ['XS', 'S', 'M', 'L', 'XL', 'XXL', '6', '8', '10', '12', '14', '16', '18'],
  Price: ['Under £25', '£25–£50', '£50–£100', 'Over £100'],
}

const PRICE_QUERY_MAP: Record<string, string> = {
  'Under £25': 'under 25',
  '£25–£50':  '25 to 50',
  '£50–£100': '50 to 100',
  'Over £100': 'over 100',
}

export function filterValueToQueryTerm(key: string, value: string): string {
  if (key === 'Price') return PRICE_QUERY_MAP[value] ?? value
  return value
}

const TOP_N_OPTIONS = [5, 10, 20, 25, 50, 75, 100]
const SORT_OPTIONS: { label: string; value: SortOption }[] = [
  { label: 'Relevance',   value: 'relevance'  },
  { label: 'Price: Low',  value: 'price_asc'  },
  { label: 'Price: High', value: 'price_desc' },
]
const FILTER_LABELS = Object.keys(FILTER_OPTIONS)

// Per-row height and max visible rows before scroll
const ITEM_H  = 40
const MAX_VIS = 5

// Tracks which dropdown is open and where to position it (viewport coords)
interface DropdownState {
  label: string
  top:   number
  left:  number
}

export default function FilterBar({
  topN, onTopNChange, sort, onSortChange, view, onViewChange,
  activeFilters, onRemoveFilter: _onRemoveFilter, onFilterChange,
}: Props) {
  const [dropdown, setDropdown] = useState<DropdownState | null>(null)
  const [mounted,  setMounted]  = useState(false)
  const barRef      = useRef<HTMLDivElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // createPortal needs document.body – only available after hydration
  useEffect(() => { setMounted(true) }, [])

  // Close on outside click or any scroll event
  useEffect(() => {
    if (!dropdown) return
    const close = () => setDropdown(null)
    const handleMouseDown = (e: MouseEvent) => {
      const t = e.target as Node
      if (barRef.current?.contains(t) || dropdownRef.current?.contains(t)) return
      close()
    }
    const handleScroll = (e: Event) => {
      if (dropdownRef.current?.contains(e.target as Node)) return
      close()
    }
    document.addEventListener('mousedown', handleMouseDown)
    window.addEventListener('scroll', handleScroll, { capture: true })
    return () => {
      document.removeEventListener('mousedown', handleMouseDown)
      window.removeEventListener('scroll', handleScroll, { capture: true })
    }
  }, [dropdown])

  const toggleFilter = useCallback((label: string, e: React.MouseEvent<HTMLButtonElement>) => {
    if (dropdown?.label === label) { setDropdown(null); return }
    const rect = e.currentTarget.getBoundingClientRect()
    setDropdown({ label, top: rect.bottom, left: rect.left })
  }, [dropdown])

  const handleOptionClick = (filterKey: string, option: string) => {
    const queryTerm = filterValueToQueryTerm(filterKey, option)
    const isActive  = activeFilters[filterKey] === queryTerm
    onFilterChange(filterKey, isActive ? null : queryTerm)
    setDropdown(null)
  }

  const activeDisplayValue = (key: string): string | null => {
    const qt = activeFilters[key]
    if (!qt) return null
    if (key === 'Price') return Object.entries(PRICE_QUERY_MAP).find(([, v]) => v === qt)?.[0] ?? qt
    return qt
  }

  // ── Portal dropdown ────────────────────────────────────────────────────────
  const DropdownPortal = () => {
    if (!mounted || !dropdown) return null
    const opts = FILTER_OPTIONS[dropdown.label]
    const visCount = Math.min(opts.length, MAX_VIS)
    const panelH   = visCount * ITEM_H
    const scrollable = opts.length > MAX_VIS

    return createPortal(
      <div
        ref={dropdownRef}
        style={{
          position: 'fixed',
          top:  dropdown.top,
          left: dropdown.left,
          zIndex: 9999,
        }}
      >
        {/* Scroll container */}
        <div
          className="filter-scroll"
          style={{
            background:  'var(--bg-card)',
            border:      '1px solid var(--border-soft)',
            minWidth:    '172px',
            height:      `${panelH}px`,
            overflowY:   scrollable ? 'auto' : 'hidden',
            boxShadow:   '0 12px 40px rgba(0,0,0,0.55)',
          }}
        >
          {opts.map(option => {
            const queryTerm  = filterValueToQueryTerm(dropdown.label, option)
            const isSelected = activeFilters[dropdown.label] === queryTerm
            return (
              <button
                key={option}
                onMouseDown={e => e.stopPropagation()} // don't trigger outside-click handler
                onClick={() => handleOptionClick(dropdown.label, option)}
                style={{
                  display:         'flex',
                  alignItems:      'center',
                  justifyContent:  'space-between',
                  width:           '100%',
                  height:          `${ITEM_H}px`,
                  padding:         '0 16px',
                  fontSize:        '12px',
                  letterSpacing:   '0.1em',
                  color:           isSelected ? 'var(--accent)' : 'var(--text-primary)',
                  background:      isSelected ? 'rgba(201,169,110,0.07)' : 'transparent',
                  border:          'none',
                  borderBottom:    '1px solid var(--border-hard)',
                  cursor:          'pointer',
                  textAlign:       'left',
                  whiteSpace:      'nowrap',
                  flexShrink:      0,
                  transition:      'background 0.15s, color 0.15s',
                }}
              >
                {option}
                {isSelected && (
                  <span style={{ fontSize: '9px', color: 'var(--accent)', marginLeft: '14px', flexShrink: 0 }}>✓</span>
                )}
              </button>
            )
          })}
        </div>

        {/* Bottom fade — signals more content below */}
        {scrollable && (
          <div style={{
            position:       'absolute',
            bottom:         0,
            left:           0,
            width:          '172px',
            height:         '18px',
            background:     'linear-gradient(to bottom, transparent, var(--bg-card))',
            pointerEvents:  'none',
          }} />
        )}
      </div>,
      document.body
    )
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <>
      <div
        ref={barRef}
        style={{
          background:   'var(--bg-secondary)',
          borderBottom: '1px solid #181818',
          padding:      '0 56px',
          display:      'flex',
          alignItems:   'center',
          overflowX:    'auto',
          minHeight:    '54px',
          flexWrap:     'nowrap',
        }}
      >
        {/* Filter buttons */}
        {FILTER_LABELS.map(label => {
          const isOpen    = dropdown?.label === label
          const activeVal = activeDisplayValue(label)
          return (
            <button
              key={label}
              onClick={e => toggleFilter(label, e)}
              style={{
                display:       'flex',
                alignItems:    'center',
                gap:           '7px',
                padding:       '0 20px',
                height:        '54px',
                fontSize:      '12px',
                letterSpacing: '0.15em',
                textTransform: 'uppercase',
                color:         isOpen || activeVal ? 'var(--text-primary)' : 'var(--text-secondary)',
                cursor:        'pointer',
                background:    'transparent',
                border:        'none',
                borderRight:   '1px solid #181818',
                whiteSpace:    'nowrap',
                flexShrink:    0,
                boxShadow:     isOpen || activeVal ? 'inset 0 -2px 0 var(--accent)' : 'none',
                transition:    'color 0.2s',
              }}
            >
              {activeVal
                ? <span style={{ color: 'var(--accent)' }}>{activeVal}</span>
                : label}
              <span style={{
                fontSize:   '8px',
                opacity:    0.45,
                transform:  isOpen ? 'rotate(180deg)' : 'none',
                transition: 'transform 0.2s',
                display:    'inline-block',
              }}>▼</span>
            </button>
          )
        })}

        {/* Active filter chips — commented out: clutters the filter bar and extends its horizontal length.
             The selected state is already shown via the accent underline on the filter button itself.
             Re-enable later if a dedicated chip tray area is added below the filter bar.
        {Object.entries(activeFilters).map(([key, val]) => {
          const display = activeDisplayValue(key) ?? val
          return (
            <div key={key} style={{
              display:       'flex',
              alignItems:    'center',
              gap:           '6px',
              padding:       '5px 12px',
              background:    'rgba(201,169,110,0.08)',
              border:        '1px solid rgba(201,169,110,0.2)',
              fontSize:      '11px',
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
              color:         'var(--accent)',
              whiteSpace:    'nowrap',
              marginLeft:    '8px',
              flexShrink:    0,
            }}>
              {display}
              <span
                onClick={() => onRemoveFilter(key)}
                style={{ fontSize: '10px', cursor: 'pointer', marginLeft: '2px', opacity: 0.7 }}
              >✕</span>
            </div>
          )
        })}
        */}

        {/* Right controls */}
        <div style={{ display: 'flex', alignItems: 'center', marginLeft: 'auto', flexShrink: 0 }}>
          {/* Retrieve */}
          <div style={{
            display:     'flex',
            alignItems:  'center',
            gap:         '10px',
            padding:     '0 20px',
            borderRight: '1px solid #181818',
            height:      '54px',
          }}>
            <span style={{ fontSize: '11px', letterSpacing: '0.15em', textTransform: 'uppercase', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
              Retrieve
            </span>
            <select
              value={topN}
              onChange={e => onTopNChange(Number(e.target.value))}
              style={{
                background:        'var(--bg-card)',
                border:            '1px solid var(--border-soft)',
                color:             'var(--text-primary)',
                fontSize:          '12px',
                padding:           '5px 10px',
                cursor:            'pointer',
                outline:           'none',
                appearance:        'none',
                WebkitAppearance:  'none',
              }}
            >
              {TOP_N_OPTIONS.map(n => <option key={n} value={n}>{n} results</option>)}
            </select>
          </div>

          {/* Sort */}
          {SORT_OPTIONS.map(({ label, value }) => (
            <button
              key={value}
              onClick={() => onSortChange(value)}
              style={{
                padding:       '0 16px',
                height:        '54px',
                fontSize:      '12px',
                letterSpacing: '0.15em',
                textTransform: 'uppercase',
                color:         sort === value ? 'var(--text-primary)' : 'var(--text-secondary)',
                cursor:        'pointer',
                background:    'transparent',
                border:        'none',
                borderRight:   '1px solid #181818',
                whiteSpace:    'nowrap',
                transition:    'color 0.2s',
                boxShadow:     sort === value ? 'inset 0 -2px 0 var(--accent)' : 'none',
              }}
            >
              {label}
            </button>
          ))}

          {/* View toggle */}
          {([{ v: 'grid', icon: '⊞' }, { v: 'list', icon: '≡' }] as const).map(({ v, icon }) => (
            <button
              key={v}
              onClick={() => onViewChange(v)}
              style={{
                width:      '44px',
                height:     '54px',
                display:    'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor:     'pointer',
                border:     'none',
                background: 'transparent',
                color:      view === v ? 'var(--text-primary)' : 'var(--text-secondary)',
                fontSize:   '14px',
                borderLeft: '1px solid #181818',
                transition: 'color 0.2s',
              }}
            >
              {icon}
            </button>
          ))}
        </div>
      </div>

      {/* Dropdown rendered in a portal — completely outside the filter bar's overflow context */}
      <DropdownPortal />
    </>
  )
}
