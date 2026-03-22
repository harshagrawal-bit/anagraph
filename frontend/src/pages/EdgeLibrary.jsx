import { useState, useEffect } from 'react'

const PATTERN_COLORS = {
  physical_world:       '#60a5fa',
  digital_behavior:     '#a78bfa',
  supply_chain_upstream:'#34d399',
  management_behavior:  '#f6ad55',
  cross_domain:         '#fb923c',
  information_lag:      '#f472b6',
}

const PATTERN_LABELS = {
  physical_world:       'Physical World',
  digital_behavior:     'Digital Behavior',
  supply_chain_upstream:'Supply Chain',
  management_behavior:  'Mgmt Behavior',
  cross_domain:         'Cross-Domain',
  information_lag:      'Info Lag',
}

const STATUS_STYLE = {
  hypothesis: { color: '#f6ad55', bg: '#2d2416' },
  validated:  { color: '#48bb78', bg: '#162420' },
  rejected:   { color: '#fc8181', bg: '#2d1616' },
}

const s = {
  page: { padding: '32px', maxWidth: '1200px' },
  header: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '28px' },
  title: { fontSize: '22px', fontWeight: 700, color: '#e2e8f0' },
  sub: { fontSize: '13px', color: '#718096', marginTop: '4px' },
  genRow: { display: 'flex', gap: '10px', alignItems: 'center' },
  input: {
    background: '#111827', border: '1px solid #2d3748', borderRadius: '6px',
    padding: '9px 12px', color: '#e2e8f0', fontSize: '13px', outline: 'none', width: '120px',
  },
  genBtn: {
    background: '#1e40af', border: 'none', borderRadius: '6px', color: '#fff',
    padding: '9px 18px', fontSize: '13px', fontWeight: 600, cursor: 'pointer',
  },
  statsRow: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '24px' },
  stat: {
    background: '#0d1117', border: '1px solid #1e2738', borderRadius: '8px',
    padding: '14px 16px',
  },
  statLabel: { fontSize: '11px', color: '#718096', textTransform: 'uppercase', letterSpacing: '1px' },
  statValue: { fontSize: '24px', fontWeight: 700, color: '#60a5fa', marginTop: '4px' },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' },
  card: {
    background: '#0d1117', border: '1px solid #1e2738', borderRadius: '10px',
    padding: '18px', display: 'flex', flexDirection: 'column', gap: '10px',
  },
  cardHeader: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' },
  cardTitle: { fontSize: '14px', fontWeight: 600, color: '#e2e8f0', flex: 1 },
  patternBadge: {
    fontSize: '10px', padding: '2px 8px', borderRadius: '4px',
    fontWeight: 600, letterSpacing: '0.5px', flexShrink: 0,
  },
  cardMeta: { fontSize: '12px', color: '#718096', lineHeight: 1.6 },
  cardDesc: { fontSize: '12px', color: '#94a3b8', lineHeight: 1.6 },
  footer: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '4px' },
  statusBadge: { fontSize: '10px', padding: '2px 8px', borderRadius: '4px', fontWeight: 600, textTransform: 'uppercase' },
  conviction: { fontSize: '11px' },
  actions: { display: 'flex', gap: '6px', marginTop: '8px' },
  actionBtn: {
    flex: 1, background: '#111827', border: '1px solid #2d3748', borderRadius: '4px',
    color: '#e2e8f0', padding: '5px', fontSize: '11px', cursor: 'pointer',
  },
  emptyState: {
    gridColumn: '1 / -1', textAlign: 'center', padding: '60px 20px',
    color: '#4a5568',
  },
  loading: { color: '#718096', padding: '40px 0', textAlign: 'center' },
}

const DEMO_EDGES = [
  {
    id: 'edge_0001', ticker: 'NVDA', company: 'Nvidia',
    pattern_id: 'supply_chain_upstream', status: 'hypothesis',
    title: 'TSMC CoWoS capacity utilization predicts NVDA data center revenue',
    description: 'TSMC quarterly earnings calls include CoWoS advanced packaging utilization rates. Since NVDA H100/H200 GPUs depend entirely on CoWoS, TSMC utilization >90% 6-8 weeks before NVDA earnings indicates supply constraint — the demand-side read is bullish.',
    data_source: 'TSMC quarterly earnings calls (public), estimated 6-8 week lead time',
    lead_time: '6-8 weeks', current_signal: 'Bullish', conviction_level: 'High',
    monitoring_cadence: 'Quarterly (TSMC earnings)',
  },
  {
    id: 'edge_0002', ticker: 'NVDA', company: 'Nvidia',
    pattern_id: 'digital_behavior', status: 'validated',
    title: 'LinkedIn CUDA engineer job postings predict enterprise AI adoption',
    description: 'Enterprise companies hiring CUDA engineers precedes GPU procurement by 1-2 quarters. Track LinkedIn postings for "CUDA" + "data center" roles at Fortune 500 companies. Rising postings = demand pipeline is building.',
    data_source: 'LinkedIn Jobs (free search), track weekly. Filter: CUDA + data center',
    lead_time: '8-12 weeks', current_signal: 'Bullish', conviction_level: 'High',
    monitoring_cadence: 'Weekly',
  },
  {
    id: 'edge_0003', ticker: 'TGT', company: 'Target',
    pattern_id: 'physical_world', status: 'hypothesis',
    title: 'Target store parking lot occupancy vs weekend traffic',
    description: 'Satellite foot traffic data for Target\'s top 200 stores vs prior year same-weekend. Sustained -15% or worse over a 4-week period is a leading indicator for comparable sales miss. Signal quality highest in October-December (holiday season).',
    data_source: 'Placer.ai (paid), SafeGraph (research access). Lead time: 4-6 weeks',
    lead_time: '4-6 weeks', current_signal: 'Neutral', conviction_level: 'Medium',
    monitoring_cadence: 'Weekly',
  },
  {
    id: 'edge_0004', ticker: 'AAPL', company: 'Apple',
    pattern_id: 'information_lag', status: 'hypothesis',
    title: 'Foxconn Zhengzhou overtime notices precede iPhone production volumes',
    description: 'Foxconn posts overtime and temporary worker recruitment notices in local Chinese job boards (Zhaopin, 51job) before major production ramps. Spike in Zhengzhou postings 8-10 weeks before Apple earnings = positive iPhone build signal.',
    data_source: 'Zhaopin.com, 51job.com (free, search "Foxconn Zhengzhou"). Lead: 8-10 weeks',
    lead_time: '8-10 weeks', current_signal: 'Neutral', conviction_level: 'Medium',
    monitoring_cadence: 'Bi-weekly',
  },
  {
    id: 'edge_0005', ticker: 'MSFT', company: 'Microsoft',
    pattern_id: 'management_behavior', status: 'validated',
    title: 'Insider Form 4 purchases ahead of major product announcements',
    description: 'Track SEC Form 4 filings for MSFT VP-level and above open-market purchases (not option exercises). Cluster of $1M+ purchases in 60-day window before earnings has historically preceded positive guidance revisions in Azure segment.',
    data_source: 'SEC EDGAR Form 4 (free, same-day filing). Filter: Open Market Purchase, VP+',
    lead_time: '2-8 weeks', current_signal: 'Neutral', conviction_level: 'High',
    monitoring_cadence: 'Daily (SEC EDGAR RSS feed)',
  },
]

export default function EdgeLibrary() {
  const [edges, setEdges] = useState(DEMO_EDGES)
  const [loading, setLoading] = useState(false)
  const [genTicker, setGenTicker] = useState('')
  const [genCompany, setGenCompany] = useState('')
  const [generating, setGenerating] = useState(false)
  const [filter, setFilter] = useState('all')

  async function generateHypotheses() {
    if (!genTicker) return
    setGenerating(true)
    try {
      const r = await fetch('/api/edges/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker: genTicker.toUpperCase(), company: genCompany || genTicker, fund_id: 'default' }),
      })
      const data = await r.json()
      if (data.hypotheses) setEdges(prev => [...data.hypotheses, ...prev])
    } catch (e) {}
    setGenerating(false)
  }

  async function updateStatus(edgeId, newStatus) {
    setEdges(prev => prev.map(e => e.id === edgeId ? { ...e, status: newStatus } : e))
    try {
      await fetch(`/api/edges/default/${edgeId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      })
    } catch (e) {}
  }

  const filtered = filter === 'all' ? edges : edges.filter(e => e.status === filter)
  const counts = {
    all: edges.length,
    hypothesis: edges.filter(e => e.status === 'hypothesis').length,
    validated: edges.filter(e => e.status === 'validated').length,
    rejected: edges.filter(e => e.status === 'rejected').length,
  }

  return (
    <div style={s.page}>
      <div style={s.header}>
        <div>
          <div style={s.title}>Edge Discovery Library</div>
          <div style={s.sub}>Alternative data hypotheses · 6 pattern categories · Fund-specific</div>
        </div>
        <div style={s.genRow}>
          <input style={s.input} placeholder="Ticker" value={genTicker}
            onChange={e => setGenTicker(e.target.value.toUpperCase())} />
          <input style={{ ...s.input, width: '140px' }} placeholder="Company (opt)"
            value={genCompany} onChange={e => setGenCompany(e.target.value)} />
          <button style={{ ...s.genBtn, opacity: generating ? 0.6 : 1 }}
            onClick={generateHypotheses} disabled={generating || !genTicker}>
            {generating ? '⟳ Generating...' : '◆ Generate 5 Hypotheses'}
          </button>
        </div>
      </div>

      {/* Stats */}
      <div style={s.statsRow}>
        {[
          { key: 'all', label: 'Total', color: '#60a5fa' },
          { key: 'hypothesis', label: 'Pending Review', color: '#f6ad55' },
          { key: 'validated', label: 'Validated', color: '#48bb78' },
          { key: 'rejected', label: 'Rejected', color: '#fc8181' },
        ].map(({ key, label, color }) => (
          <div key={key} style={{ ...s.stat, cursor: 'pointer', borderColor: filter === key ? color + '44' : '#1e2738' }}
            onClick={() => setFilter(key)}>
            <div style={s.statLabel}>{label}</div>
            <div style={{ ...s.statValue, color }}>{counts[key]}</div>
          </div>
        ))}
      </div>

      {/* Pattern legend */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '20px' }}>
        {Object.entries(PATTERN_LABELS).map(([id, label]) => (
          <div key={id} style={{
            fontSize: '11px', padding: '3px 10px', borderRadius: '4px',
            color: PATTERN_COLORS[id], background: PATTERN_COLORS[id] + '15',
            border: `1px solid ${PATTERN_COLORS[id]}33`,
          }}>
            {label}
          </div>
        ))}
      </div>

      {/* Edge cards */}
      <div style={s.grid}>
        {filtered.length === 0 ? (
          <div style={s.emptyState}>
            <div style={{ fontSize: '40px', marginBottom: '12px' }}>◆</div>
            <div>No hypotheses yet. Enter a ticker above to generate 5 edge hypotheses.</div>
          </div>
        ) : filtered.map(edge => {
          const patternColor = PATTERN_COLORS[edge.pattern_id] || '#718096'
          const st = STATUS_STYLE[edge.status] || STATUS_STYLE.hypothesis
          return (
            <div key={edge.id} style={{ ...s.card, borderColor: patternColor + '33' }}>
              <div style={s.cardHeader}>
                <div style={s.cardTitle}>{edge.title || 'Untitled Hypothesis'}</div>
                <div style={{ ...s.patternBadge, color: patternColor, background: patternColor + '15' }}>
                  {PATTERN_LABELS[edge.pattern_id] || edge.pattern_id}
                </div>
              </div>
              <div style={s.cardMeta}>
                <span style={{ color: '#60a5fa', fontWeight: 600 }}>{edge.ticker}</span>
                {' · '}Lead: {edge.lead_time}
                {' · '}Signal: <span style={{ color: edge.current_signal === 'Bullish' ? '#48bb78' : edge.current_signal === 'Bearish' ? '#fc8181' : '#718096' }}>{edge.current_signal}</span>
                {' · '}{edge.monitoring_cadence}
              </div>
              <div style={s.cardDesc}>{edge.description}</div>
              {edge.data_source && (
                <div style={{ fontSize: '11px', color: '#4a5568' }}>
                  <span style={{ color: '#718096' }}>Source:</span> {edge.data_source}
                </div>
              )}
              <div style={s.footer}>
                <div style={{ ...s.statusBadge, color: st.color, background: st.bg }}>
                  {edge.status}
                </div>
                <div style={{ ...s.conviction, color: edge.conviction_level === 'High' ? '#48bb78' : edge.conviction_level === 'Medium' ? '#f6ad55' : '#718096' }}>
                  {edge.conviction_level} conviction
                </div>
              </div>
              {edge.status === 'hypothesis' && (
                <div style={s.actions}>
                  <button style={{ ...s.actionBtn, color: '#48bb78', borderColor: '#48bb78' + '44' }}
                    onClick={() => updateStatus(edge.id, 'validated')}>✓ Validate</button>
                  <button style={{ ...s.actionBtn, color: '#fc8181', borderColor: '#fc8181' + '44' }}
                    onClick={() => updateStatus(edge.id, 'rejected')}>✕ Reject</button>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
