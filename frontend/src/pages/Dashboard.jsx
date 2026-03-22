import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Watchlist from '../components/Watchlist.jsx'

const s = {
  page: { padding: '32px', maxWidth: '1200px' },
  header: { marginBottom: '32px' },
  greeting: { fontSize: '24px', fontWeight: 700, color: '#e2e8f0', marginBottom: '4px' },
  sub: { fontSize: '14px', color: '#718096' },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', marginBottom: '32px' },
  card: {
    background: '#0d1117', border: '1px solid #1e2738', borderRadius: '10px',
    padding: '20px',
  },
  cardLabel: { fontSize: '11px', color: '#718096', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px' },
  cardValue: { fontSize: '28px', fontWeight: 700, color: '#60a5fa' },
  cardSub: { fontSize: '12px', color: '#4a5568', marginTop: '4px' },
  row: { display: 'grid', gridTemplateColumns: '300px 1fr', gap: '24px' },
  recentSection: { background: '#0d1117', border: '1px solid #1e2738', borderRadius: '10px', padding: '20px' },
  sectionTitle: { fontSize: '12px', fontWeight: 600, color: '#718096', letterSpacing: '1px', textTransform: 'uppercase', marginBottom: '16px' },
  recentItem: {
    display: 'flex', alignItems: 'center', gap: '12px',
    padding: '10px 0', borderBottom: '1px solid #111827', cursor: 'pointer',
  },
  badge: {
    width: '36px', height: '36px', borderRadius: '8px',
    background: '#1e2738', display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: '12px', fontWeight: 700, color: '#60a5fa', flexShrink: 0,
  },
  itemTicker: { fontSize: '13px', fontWeight: 600, color: '#e2e8f0' },
  itemMeta: { fontSize: '11px', color: '#718096', marginTop: '2px' },
  score: { marginLeft: 'auto', fontSize: '13px', fontWeight: 700 },
  quickBtn: {
    background: '#1e40af', border: 'none', borderRadius: '6px', color: '#fff',
    padding: '10px 18px', fontSize: '13px', cursor: 'pointer', marginRight: '8px',
    fontWeight: 500,
  },
  demoBtn: {
    background: '#1a1f2e', border: '1px solid #2d3748', borderRadius: '6px', color: '#f6ad55',
    padding: '10px 18px', fontSize: '13px', cursor: 'pointer', fontWeight: 500,
  },
}

const DEMO_RECENTS = [
  { ticker: 'NVDA', company: 'Nvidia', score: '78% BULL', scoreColor: '#48bb78', personality: 'aggressive', time: '2h ago' },
  { ticker: 'TGT', company: 'Target', score: '41% BULL', scoreColor: '#fc8181', personality: 'conservative', time: '5h ago' },
  { ticker: 'AAPL', company: 'Apple', score: '63% BULL', scoreColor: '#48bb78', personality: 'macro', time: '1d ago' },
]

export default function Dashboard() {
  const navigate = useNavigate()
  const [apiStatus, setApiStatus] = useState('checking')

  useEffect(() => {
    fetch('/api/health')
      .then(r => r.ok ? setApiStatus('connected') : setApiStatus('error'))
      .catch(() => setApiStatus('disconnected'))
  }, [])

  return (
    <div style={s.page}>
      <div style={s.header}>
        <div style={s.greeting}>Research Intelligence Dashboard</div>
        <div style={s.sub}>
          AI-powered equity research · 6 specialized agents · Fund-specific personality
        </div>
      </div>

      <div style={s.grid}>
        <div style={s.card}>
          <div style={s.cardLabel}>API Status</div>
          <div style={{ ...s.cardValue, color: apiStatus === 'connected' ? '#48bb78' : '#fc8181', fontSize: '20px' }}>
            {apiStatus === 'connected' ? '● Connected' : apiStatus === 'checking' ? '○ Checking...' : '● Offline'}
          </div>
          <div style={s.cardSub}>HedgeOS API · port 5000</div>
        </div>
        <div style={s.card}>
          <div style={s.cardLabel}>Reports Generated</div>
          <div style={s.cardValue}>7</div>
          <div style={s.cardSub}>This session</div>
        </div>
        <div style={s.card}>
          <div style={s.cardLabel}>Active Fund Profile</div>
          <div style={{ ...s.cardValue, fontSize: '18px' }}>Default Fund</div>
          <div style={s.cardSub}>Aggressive growth · 6-12mo</div>
        </div>
      </div>

      <div style={{ marginBottom: '24px' }}>
        <button style={s.quickBtn} onClick={() => navigate('/research')}>
          ⚡ New Research
        </button>
        <button style={s.demoBtn} onClick={() => navigate('/research?demo=TGT')}>
          ▷ Demo Mode (TGT)
        </button>
      </div>

      <div style={s.row}>
        <Watchlist onSelect={(ticker, company) => navigate(`/research?ticker=${ticker}&company=${encodeURIComponent(company)}`)} />

        <div style={s.recentSection}>
          <div style={s.sectionTitle}>Recent Research</div>
          {DEMO_RECENTS.map(item => (
            <div
              key={item.ticker}
              style={s.recentItem}
              onClick={() => navigate('/vault')}
              onMouseEnter={e => e.currentTarget.style.background = '#111827'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <div style={s.badge}>{item.ticker.slice(0, 2)}</div>
              <div>
                <div style={s.itemTicker}>{item.ticker} — {item.company}</div>
                <div style={s.itemMeta}>{item.personality} · {item.time}</div>
              </div>
              <div style={{ ...s.score, color: item.scoreColor }}>{item.score}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
