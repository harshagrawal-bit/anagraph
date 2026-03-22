import { useState, useEffect } from 'react'

const AGENTS = [
  { id: 'data',     label: 'Data Agent',     icon: '◈', description: 'SEC EDGAR · yfinance · Reddit · Trends' },
  { id: 'signal',   label: 'Signal Analyst',  icon: '⚡', description: 'Momentum · Valuation · Sentiment' },
  { id: 'industry', label: 'Industry Expert', icon: '◆', description: 'Competitive · Moat · TAM' },
  { id: 'risk',     label: 'Risk Manager',    icon: '⚠', description: 'Downside · Thesis breaks' },
  { id: 'edge',     label: 'Edge Specialist', icon: '◉', description: 'Alt-data · Leading indicators' },
  { id: 'checker',  label: 'Fact Checker',    icon: '✓', description: 'Validate · Integrate · Finalize' },
]

const STATUS_STYLES = {
  idle:    { color: '#4a5568', bg: '#1a1f2e' },
  running: { color: '#f6ad55', bg: '#2d2416' },
  done:    { color: '#48bb78', bg: '#162420' },
  error:   { color: '#fc8181', bg: '#2d1616' },
}

const s = {
  container: { display: 'flex', flexDirection: 'column', gap: '8px' },
  agent: {
    display: 'flex', alignItems: 'center', gap: '12px',
    padding: '12px 14px', borderRadius: '8px',
    border: '1px solid #1e2738', background: '#0d1117',
    transition: 'all 0.3s',
  },
  icon: { fontSize: '16px', width: '20px', textAlign: 'center', flexShrink: 0 },
  info: { flex: 1 },
  label: { fontSize: '13px', fontWeight: 600, marginBottom: '2px' },
  desc: { fontSize: '11px', color: '#718096' },
  badge: {
    fontSize: '10px', padding: '2px 8px', borderRadius: '4px',
    fontWeight: 600, letterSpacing: '0.5px', textTransform: 'uppercase',
    flexShrink: 0,
  },
  spinner: {
    display: 'inline-block', width: '10px', height: '10px',
    border: '1.5px solid #f6ad55', borderTopColor: 'transparent',
    borderRadius: '50%', marginRight: '6px',
    animation: 'spin 0.8s linear infinite',
  },
}

export default function AgentStatus({ statuses = {}, isRunning = false }) {
  const [pulseAgent, setPulseAgent] = useState(null)

  useEffect(() => {
    if (!isRunning) { setPulseAgent(null); return }
    const running = Object.entries(statuses).find(([, s]) => s === 'running')
    setPulseAgent(running?.[0] || null)
  }, [statuses, isRunning])

  return (
    <>
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
      <div style={s.container}>
        {AGENTS.map(agent => {
          const status = statuses[agent.id] || 'idle'
          const st = STATUS_STYLES[status]
          return (
            <div
              key={agent.id}
              style={{
                ...s.agent,
                background: st.bg,
                borderColor: status !== 'idle' ? st.color + '44' : '#1e2738',
              }}
            >
              <div style={{ ...s.icon, color: st.color }}>{agent.icon}</div>
              <div style={s.info}>
                <div style={{ ...s.label, color: st.color }}>{agent.label}</div>
                <div style={s.desc}>{agent.description}</div>
              </div>
              <div style={{ ...s.badge, color: st.color, background: st.bg }}>
                {status === 'running' && <span style={s.spinner} />}
                {status}
              </div>
            </div>
          )
        })}
      </div>
    </>
  )
}
