import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import AgentStatus from '../components/AgentStatus.jsx'
import ResearchBrief from '../components/ResearchBrief.jsx'

const PERSONALITIES = [
  { key: 'aggressive', label: 'Aggressive Growth', desc: 'Momentum · Earnings accel · High conviction' },
  { key: 'conservative', label: 'Conservative Value', desc: 'FCF yield · Margin of safety · 2-3yr horizon' },
  { key: 'macro', label: 'Global Macro', desc: 'Top-down · Sector rotation · Options expression' },
  { key: 'quant', label: 'Quantitative', desc: 'Factor-based · Statistical signals · Mean reversion' },
]

const AGENT_SEQUENCE = ['data', 'signal', 'industry', 'risk', 'edge', 'checker']

const s = {
  page: { padding: '32px', maxWidth: '1400px' },
  title: { fontSize: '22px', fontWeight: 700, color: '#e2e8f0', marginBottom: '24px' },
  layout: { display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px', alignItems: 'start' },
  panel: { background: '#0d1117', border: '1px solid #1e2738', borderRadius: '10px', padding: '20px' },
  label: { fontSize: '11px', color: '#718096', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px', display: 'block' },
  input: {
    width: '100%', background: '#111827', border: '1px solid #2d3748', borderRadius: '6px',
    padding: '10px 12px', color: '#e2e8f0', fontSize: '14px', outline: 'none',
    marginBottom: '14px',
  },
  personalityGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '16px' },
  personalityBtn: {
    background: '#111827', border: '1px solid #2d3748', borderRadius: '6px',
    padding: '10px', cursor: 'pointer', textAlign: 'left', transition: 'all 0.15s',
  },
  personalityBtnActive: { border: '1px solid #3b82f6', background: '#1e2738' },
  personalityLabel: { fontSize: '12px', fontWeight: 600, color: '#e2e8f0', marginBottom: '2px' },
  personalityDesc: { fontSize: '10px', color: '#718096', lineHeight: 1.4 },
  runBtn: {
    width: '100%', background: '#1e40af', border: 'none', borderRadius: '8px',
    color: '#fff', padding: '12px', fontSize: '14px', fontWeight: 600,
    cursor: 'pointer', marginBottom: '10px', transition: 'opacity 0.15s',
  },
  demoBtn: {
    width: '100%', background: '#1a1f2e', border: '1px solid #2d3748', borderRadius: '8px',
    color: '#f6ad55', padding: '10px', fontSize: '13px', cursor: 'pointer',
  },
  divider: { borderTop: '1px solid #1e2738', margin: '16px 0' },
  agentSection: { marginTop: '0' },
  sectionTitle: { fontSize: '11px', color: '#718096', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '12px' },
  resultPanel: { background: '#0d1117', border: '1px solid #1e2738', borderRadius: '10px', overflow: 'hidden', minHeight: '400px' },
  emptyState: {
    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
    height: '400px', color: '#4a5568',
  },
  emptyIcon: { fontSize: '48px', marginBottom: '16px' },
  emptyText: { fontSize: '14px' },
  error: {
    padding: '16px', background: '#2d1616', border: '1px solid #fc818144',
    borderRadius: '8px', color: '#fc8181', fontSize: '13px', margin: '16px',
  },
}

function simulate_agent_progress(onUpdate, onDone) {
  let idx = 0
  const statuses = {}

  function step() {
    if (idx >= AGENT_SEQUENCE.length) {
      onDone()
      return
    }
    const agent = AGENT_SEQUENCE[idx]
    if (idx > 0) statuses[AGENT_SEQUENCE[idx - 1]] = 'done'
    statuses[agent] = 'running'
    onUpdate({ ...statuses })
    idx++
    const delay = agent === 'data' ? 3000 : agent === 'checker' ? 4000 : 2500
    setTimeout(step, delay)
  }
  step()
}

export default function Research() {
  const [params] = useSearchParams()
  const [ticker, setTicker] = useState(params.get('ticker') || '')
  const [company, setCompany] = useState(params.get('company') || '')
  const [personality, setPersonality] = useState('aggressive')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [agentStatuses, setAgentStatuses] = useState({})
  const progressRef = useRef(null)

  useEffect(() => {
    const demo = params.get('demo')
    if (demo) handleDemo(demo)
  }, [])

  async function handleDemo(demoTicker = 'TGT') {
    setLoading(true)
    setError(null)
    setResult(null)
    setAgentStatuses({})
    try {
      const r = await fetch(`/api/demo/${demoTicker}`)
      const data = await r.json()
      // Simulate agent animation for demo
      simulate_agent_progress(setAgentStatuses, () => {
        const allDone = Object.fromEntries(AGENT_SEQUENCE.map(a => [a, 'done']))
        setAgentStatuses(allDone)
        setResult(data)
        setLoading(false)
      })
    } catch (e) {
      setError(e.message)
      setLoading(false)
    }
  }

  async function handleRun() {
    if (!ticker.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    setAgentStatuses({})

    // Start visual agent animation
    simulate_agent_progress(setAgentStatuses, () => {})

    try {
      const r = await fetch('/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: ticker.trim().toUpperCase(),
          company: company.trim() || ticker.trim().toUpperCase(),
          personality,
          fund_id: 'default',
        }),
      })
      const data = await r.json()
      if (data.error) throw new Error(data.error)
      const allDone = Object.fromEntries(AGENT_SEQUENCE.map(a => [a, 'done']))
      setAgentStatuses(allDone)
      setResult(data)
    } catch (e) {
      setError(e.message)
      const allErr = Object.fromEntries(AGENT_SEQUENCE.map(a => [a, 'error']))
      setAgentStatuses(allErr)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={s.page}>
      <div style={s.title}>Research Console</div>
      <div style={s.layout}>
        {/* Left panel */}
        <div>
          <div style={s.panel}>
            <label style={s.label}>Ticker</label>
            <input
              style={s.input}
              placeholder="e.g. NVDA"
              value={ticker}
              onChange={e => setTicker(e.target.value.toUpperCase())}
              onKeyDown={e => e.key === 'Enter' && handleRun()}
            />
            <label style={s.label}>Company Name</label>
            <input
              style={s.input}
              placeholder="e.g. Nvidia (optional)"
              value={company}
              onChange={e => setCompany(e.target.value)}
            />
            <label style={s.label}>Fund Personality</label>
            <div style={s.personalityGrid}>
              {PERSONALITIES.map(p => (
                <button
                  key={p.key}
                  style={{ ...s.personalityBtn, ...(personality === p.key ? s.personalityBtnActive : {}) }}
                  onClick={() => setPersonality(p.key)}
                >
                  <div style={s.personalityLabel}>{p.label}</div>
                  <div style={s.personalityDesc}>{p.desc}</div>
                </button>
              ))}
            </div>
            <button
              style={{ ...s.runBtn, opacity: loading || !ticker ? 0.6 : 1 }}
              onClick={handleRun}
              disabled={loading || !ticker}
            >
              {loading ? '⟳ Running Agents...' : '⚡ Run Research'}
            </button>
            <button style={s.demoBtn} onClick={() => handleDemo('TGT')} disabled={loading}>
              ▷ Demo Mode (TGT — instant)
            </button>
          </div>

          <div style={{ ...s.panel, marginTop: '16px' }}>
            <div style={s.sectionTitle}>Agent Status</div>
            <AgentStatus statuses={agentStatuses} isRunning={loading} />
          </div>
        </div>

        {/* Right panel */}
        <div style={s.resultPanel}>
          {error && <div style={s.error}>Error: {error}</div>}
          {result ? (
            <ResearchBrief result={result} />
          ) : !loading ? (
            <div style={s.emptyState}>
              <div style={s.emptyIcon}>◈</div>
              <div style={s.emptyText}>Enter a ticker and run research</div>
            </div>
          ) : (
            <div style={s.emptyState}>
              <div style={{ ...s.emptyIcon, fontSize: '32px' }}>⟳</div>
              <div style={s.emptyText}>Agents running... this takes 60-90 seconds</div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
