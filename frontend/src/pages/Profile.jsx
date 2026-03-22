import { useState, useEffect } from 'react'

const s = {
  page: { padding: '32px', maxWidth: '900px' },
  title: { fontSize: '22px', fontWeight: 700, color: '#e2e8f0', marginBottom: '8px' },
  sub: { fontSize: '14px', color: '#718096', marginBottom: '28px' },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' },
  card: { background: '#0d1117', border: '1px solid #1e2738', borderRadius: '10px', padding: '20px' },
  cardTitle: { fontSize: '12px', fontWeight: 600, color: '#718096', letterSpacing: '1px', textTransform: 'uppercase', marginBottom: '16px' },
  field: { marginBottom: '14px' },
  label: { fontSize: '11px', color: '#718096', marginBottom: '6px', display: 'block' },
  input: {
    width: '100%', background: '#111827', border: '1px solid #2d3748', borderRadius: '6px',
    padding: '8px 10px', color: '#e2e8f0', fontSize: '13px', outline: 'none',
  },
  select: {
    width: '100%', background: '#111827', border: '1px solid #2d3748', borderRadius: '6px',
    padding: '8px 10px', color: '#e2e8f0', fontSize: '13px', outline: 'none',
  },
  range: { width: '100%', accentColor: '#3b82f6' },
  saveBtn: {
    background: '#1e40af', border: 'none', borderRadius: '8px', color: '#fff',
    padding: '10px 20px', fontSize: '13px', fontWeight: 600, cursor: 'pointer',
    marginTop: '20px',
  },
  saved: { color: '#48bb78', fontSize: '12px', marginLeft: '12px' },
  tagRow: { display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '8px' },
  tag: {
    background: '#1e2738', border: '1px solid #2d3748', borderRadius: '4px',
    padding: '3px 8px', fontSize: '11px', color: '#60a5fa', cursor: 'pointer',
  },
  tagActive: { background: '#1e3a8a', borderColor: '#3b82f6' },
  feedbackSection: { marginTop: '20px', gridColumn: '1 / -1' },
  feedbackCard: {
    background: '#0d1117', border: '1px solid #1e2738', borderRadius: '10px', padding: '20px',
  },
  star: { fontSize: '20px', cursor: 'pointer', marginRight: '4px' },
  textarea: {
    width: '100%', background: '#111827', border: '1px solid #2d3748', borderRadius: '6px',
    padding: '8px 10px', color: '#e2e8f0', fontSize: '13px', outline: 'none',
    resize: 'vertical', minHeight: '80px', marginTop: '8px',
  },
}

const SECTOR_OPTIONS = ['Technology', 'Healthcare', 'Consumer Discretionary', 'Consumer Staples',
  'Financials', 'Industrials', 'Energy', 'Materials', 'Real Estate', 'Utilities', 'Communication Services']

const PATTERN_OPTIONS = ['earnings_acceleration', 'margin_expansion', 'multiple_expansion_catalyst',
  'SaaS_NRR_expansion', 'biotech_catalyst', 'insider_buying', 'short_squeeze', 'turnaround']

export default function Profile() {
  const [profile, setProfile] = useState({
    fund_id: 'default',
    fund_name: 'My Fund',
    investment_style: { approach: 'long_short', time_horizon: '6-12 months', market_cap_preference: 'large_cap' },
    sector_focus: { primary: ['Technology'], secondary: [] },
    risk_profile: { max_position_size_pct: 10, max_drawdown_tolerance_pct: 15, stop_loss_trigger_pct: -20 },
    historical_edges: { pattern_preferences: ['earnings_acceleration'] },
    output_preferences: { brief_length: 'standard', tone: 'analytical' },
  })
  const [saved, setSaved] = useState(false)
  const [feedbackRating, setFeedbackRating] = useState(0)
  const [feedbackComment, setFeedbackComment] = useState('')
  const [feedbackTicker, setFeedbackTicker] = useState('')

  useEffect(() => {
    fetch('/api/profiles/default')
      .then(r => r.json())
      .then(data => { if (!data.error) setProfile(data) })
      .catch(() => {})
  }, [])

  function toggleSector(sector, type) {
    setProfile(prev => {
      const list = [...(prev.sector_focus[type] || [])]
      const idx = list.indexOf(sector)
      if (idx >= 0) list.splice(idx, 1)
      else list.push(sector)
      return { ...prev, sector_focus: { ...prev.sector_focus, [type]: list } }
    })
  }

  function togglePattern(pattern) {
    setProfile(prev => {
      const list = [...(prev.historical_edges.pattern_preferences || [])]
      const idx = list.indexOf(pattern)
      if (idx >= 0) list.splice(idx, 1)
      else list.push(pattern)
      return { ...prev, historical_edges: { ...prev.historical_edges, pattern_preferences: list } }
    })
  }

  async function saveProfile() {
    try {
      const r = await fetch('/api/profiles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
      })
      const data = await r.json()
      if (!data.error) { setSaved(true); setTimeout(() => setSaved(false), 3000) }
    } catch (e) {}
  }

  async function submitFeedback() {
    if (!feedbackTicker || !feedbackRating) return
    await fetch(`/api/profiles/default/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker: feedbackTicker, rating: feedbackRating, comment: feedbackComment }),
    })
    setFeedbackRating(0); setFeedbackComment(''); setFeedbackTicker('')
  }

  return (
    <div style={s.page}>
      <div style={s.title}>Fund Profile</div>
      <div style={s.sub}>Configure your fund's investment personality. This shapes every research brief.</div>

      <div style={s.grid}>
        {/* Identity */}
        <div style={s.card}>
          <div style={s.cardTitle}>Fund Identity</div>
          <div style={s.field}>
            <label style={s.label}>Fund Name</label>
            <input style={s.input} value={profile.fund_name}
              onChange={e => setProfile(p => ({ ...p, fund_name: e.target.value }))} />
          </div>
          <div style={s.field}>
            <label style={s.label}>Investment Style</label>
            <select style={s.select} value={profile.investment_style.approach}
              onChange={e => setProfile(p => ({ ...p, investment_style: { ...p.investment_style, approach: e.target.value } }))}>
              <option value="long_short">Long / Short</option>
              <option value="long_only">Long Only</option>
              <option value="macro">Global Macro</option>
              <option value="quant">Quantitative</option>
            </select>
          </div>
          <div style={s.field}>
            <label style={s.label}>Time Horizon</label>
            <select style={s.select} value={profile.investment_style.time_horizon}
              onChange={e => setProfile(p => ({ ...p, investment_style: { ...p.investment_style, time_horizon: e.target.value } }))}>
              <option>1-3 months</option>
              <option>3-6 months</option>
              <option>6-12 months</option>
              <option>12-24 months</option>
              <option>24-36 months</option>
            </select>
          </div>
        </div>

        {/* Risk */}
        <div style={s.card}>
          <div style={s.cardTitle}>Risk Parameters</div>
          <div style={s.field}>
            <label style={s.label}>Max Position Size: {profile.risk_profile.max_position_size_pct}%</label>
            <input type="range" style={s.range} min="1" max="25" value={profile.risk_profile.max_position_size_pct}
              onChange={e => setProfile(p => ({ ...p, risk_profile: { ...p.risk_profile, max_position_size_pct: +e.target.value } }))} />
          </div>
          <div style={s.field}>
            <label style={s.label}>Max Drawdown Tolerance: {profile.risk_profile.max_drawdown_tolerance_pct}%</label>
            <input type="range" style={s.range} min="5" max="40" value={profile.risk_profile.max_drawdown_tolerance_pct}
              onChange={e => setProfile(p => ({ ...p, risk_profile: { ...p.risk_profile, max_drawdown_tolerance_pct: +e.target.value } }))} />
          </div>
          <div style={s.field}>
            <label style={s.label}>Output Style</label>
            <select style={s.select} value={profile.output_preferences.brief_length}
              onChange={e => setProfile(p => ({ ...p, output_preferences: { ...p.output_preferences, brief_length: e.target.value } }))}>
              <option value="brief">Brief (concise)</option>
              <option value="standard">Standard</option>
              <option value="deep_dive">Deep Dive</option>
            </select>
          </div>
        </div>

        {/* Sectors */}
        <div style={s.card}>
          <div style={s.cardTitle}>Primary Sectors</div>
          <div style={s.tagRow}>
            {SECTOR_OPTIONS.map(sector => (
              <button key={sector} style={{
                ...s.tag,
                ...(profile.sector_focus.primary.includes(sector) ? s.tagActive : {})
              }} onClick={() => toggleSector(sector, 'primary')}>
                {sector}
              </button>
            ))}
          </div>
        </div>

        {/* Patterns */}
        <div style={s.card}>
          <div style={s.cardTitle}>Pattern Preferences</div>
          <div style={s.tagRow}>
            {PATTERN_OPTIONS.map(pattern => (
              <button key={pattern} style={{
                ...s.tag,
                ...(profile.historical_edges.pattern_preferences.includes(pattern) ? s.tagActive : {})
              }} onClick={() => togglePattern(pattern)}>
                {pattern.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Feedback */}
        <div style={{ ...s.feedbackSection }}>
          <div style={s.feedbackCard}>
            <div style={s.cardTitle}>Research Feedback (Reinforcement Learning)</div>
            <p style={{ fontSize: '13px', color: '#718096', marginBottom: '12px' }}>
              Rate research briefs to train the AI to think more like your fund over time.
            </p>
            <div style={s.field}>
              <label style={s.label}>Ticker</label>
              <input style={{ ...s.input, width: '120px' }} placeholder="NVDA"
                value={feedbackTicker} onChange={e => setFeedbackTicker(e.target.value.toUpperCase())} />
            </div>
            <div style={{ marginBottom: '12px' }}>
              <label style={s.label}>Rating</label>
              <div>
                {[1,2,3,4,5].map(n => (
                  <span key={n} style={{ ...s.star, color: n <= feedbackRating ? '#f6ad55' : '#4a5568' }}
                    onClick={() => setFeedbackRating(n)}>★</span>
                ))}
              </div>
            </div>
            <textarea style={s.textarea} placeholder="What was good or bad about this brief?"
              value={feedbackComment} onChange={e => setFeedbackComment(e.target.value)} />
            <button style={{ ...s.saveBtn, marginTop: '12px' }} onClick={submitFeedback}>
              Submit Feedback
            </button>
          </div>
        </div>
      </div>

      <button style={s.saveBtn} onClick={saveProfile}>Save Profile</button>
      {saved && <span style={s.saved}>✓ Saved</span>}
    </div>
  )
}
