import { useState } from 'react'

const DEFAULT_WATCHLIST = [
  { ticker: 'NVDA', company: 'Nvidia', change: '+2.4%', positive: true },
  { ticker: 'TGT',  company: 'Target', change: '-1.1%', positive: false },
  { ticker: 'AAPL', company: 'Apple', change: '+0.8%', positive: true },
  { ticker: 'MSFT', company: 'Microsoft', change: '+1.3%', positive: true },
  { ticker: 'TSLA', company: 'Tesla', change: '-3.2%', positive: false },
]

const s = {
  container: {
    background: '#0d1117', border: '1px solid #1e2738',
    borderRadius: '10px', overflow: 'hidden',
  },
  header: {
    padding: '14px 16px', borderBottom: '1px solid #1e2738',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
  },
  title: { fontSize: '12px', fontWeight: 600, color: '#718096', letterSpacing: '1px', textTransform: 'uppercase' },
  addBtn: {
    fontSize: '11px', color: '#60a5fa', background: 'none', border: 'none',
    cursor: 'pointer', padding: '4px 8px', borderRadius: '4px',
  },
  item: {
    display: 'flex', alignItems: 'center', padding: '10px 16px',
    borderBottom: '1px solid #111827', cursor: 'pointer',
    transition: 'background 0.15s',
  },
  ticker: { fontSize: '13px', fontWeight: 700, color: '#e2e8f0', width: '50px' },
  name: { fontSize: '11px', color: '#718096', flex: 1 },
  change: { fontSize: '12px', fontWeight: 600 },
  inputRow: {
    display: 'flex', gap: '8px', padding: '10px 16px',
    borderBottom: '1px solid #111827',
  },
  input: {
    flex: 1, background: '#111827', border: '1px solid #2d3748',
    borderRadius: '4px', padding: '6px 8px', color: '#e2e8f0',
    fontSize: '12px', outline: 'none',
  },
  submitBtn: {
    background: '#1e40af', border: 'none', borderRadius: '4px',
    color: '#fff', padding: '6px 12px', fontSize: '12px',
    cursor: 'pointer',
  },
}

export default function Watchlist({ onSelect }) {
  const [items, setItems] = useState(DEFAULT_WATCHLIST)
  const [adding, setAdding] = useState(false)
  const [newTicker, setNewTicker] = useState('')

  function addItem() {
    if (!newTicker.trim()) return
    setItems(prev => [...prev, {
      ticker: newTicker.trim().toUpperCase(),
      company: newTicker.trim().toUpperCase(),
      change: '—',
      positive: null,
    }])
    setNewTicker('')
    setAdding(false)
  }

  return (
    <div style={s.container}>
      <div style={s.header}>
        <span style={s.title}>Watchlist</span>
        <button style={s.addBtn} onClick={() => setAdding(!adding)}>+ Add</button>
      </div>
      {adding && (
        <div style={s.inputRow}>
          <input
            style={s.input}
            placeholder="Ticker..."
            value={newTicker}
            onChange={e => setNewTicker(e.target.value.toUpperCase())}
            onKeyDown={e => e.key === 'Enter' && addItem()}
            autoFocus
          />
          <button style={s.submitBtn} onClick={addItem}>Add</button>
        </div>
      )}
      {items.map(item => (
        <div
          key={item.ticker}
          style={s.item}
          onClick={() => onSelect?.(item.ticker, item.company)}
          onMouseEnter={e => e.currentTarget.style.background = '#111827'}
          onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
        >
          <div style={s.ticker}>{item.ticker}</div>
          <div style={s.name}>{item.company}</div>
          <div style={{
            ...s.change,
            color: item.positive === true ? '#48bb78' : item.positive === false ? '#fc8181' : '#718096',
          }}>
            {item.change}
          </div>
        </div>
      ))}
    </div>
  )
}
