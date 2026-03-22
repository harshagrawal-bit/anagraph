import ReactMarkdown from 'react-markdown'

const SECTION_COLORS = {
  'SIGNAL SUMMARY': '#60a5fa',
  'BULL CASE': '#48bb78',
  'BEAR CASE': '#fc8181',
  'KEY RISKS': '#f6ad55',
  'CONFIDENCE SCORE': '#a78bfa',
  'SIGNALS TO MONITOR': '#34d399',
}

function getSectionColor(heading) {
  for (const [key, color] of Object.entries(SECTION_COLORS)) {
    if (heading.toUpperCase().includes(key)) return color
  }
  return '#718096'
}

const s = {
  container: { color: '#e2e8f0' },
  header: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '20px 24px', borderBottom: '1px solid #1e2738', marginBottom: '24px',
  },
  ticker: { fontSize: '28px', fontWeight: 700, color: '#60a5fa' },
  company: { fontSize: '14px', color: '#718096', marginTop: '2px' },
  meta: { textAlign: 'right', fontSize: '12px', color: '#4a5568' },
  metaItem: { marginBottom: '4px' },
  cost: { color: '#48bb78', fontWeight: 600 },
  content: { padding: '0 24px 32px' },
}

const markdownStyles = {
  h2: {
    fontSize: '13px', fontWeight: 700, letterSpacing: '1.5px',
    textTransform: 'uppercase', padding: '16px 16px 12px',
    marginBottom: '12px', marginTop: '24px',
    borderRadius: '6px 6px 0 0',
    borderLeft: '3px solid',
  },
  p: { fontSize: '14px', lineHeight: 1.7, color: '#cbd5e0', marginBottom: '12px' },
  li: { fontSize: '14px', lineHeight: 1.7, color: '#cbd5e0', marginBottom: '8px' },
  strong: { color: '#e2e8f0', fontWeight: 600 },
  blockquote: {
    borderLeft: '2px solid #2d3748', paddingLeft: '16px',
    color: '#718096', fontSize: '12px', marginTop: '24px',
  },
}

function BriefMarkdown({ content }) {
  return (
    <ReactMarkdown
      components={{
        h2: ({ children }) => {
          const text = String(children)
          const color = getSectionColor(text)
          return (
            <h2 style={{
              ...markdownStyles.h2,
              color, borderLeftColor: color,
              background: color + '11',
            }}>
              {children}
            </h2>
          )
        },
        p: ({ children }) => <p style={markdownStyles.p}>{children}</p>,
        li: ({ children }) => <li style={markdownStyles.li}>{children}</li>,
        strong: ({ children }) => <strong style={markdownStyles.strong}>{children}</strong>,
        blockquote: ({ children }) => <blockquote style={markdownStyles.blockquote}>{children}</blockquote>,
        ul: ({ children }) => <ul style={{ paddingLeft: '20px', marginBottom: '16px' }}>{children}</ul>,
        ol: ({ children }) => <ol style={{ paddingLeft: '20px', marginBottom: '16px' }}>{children}</ol>,
      }}
    >
      {content}
    </ReactMarkdown>
  )
}

export default function ResearchBrief({ result }) {
  if (!result) return null

  const usage = result.usage || {}
  const model = result.model || 'N/A'
  const isDemo = result.demo_mode

  return (
    <div style={s.container}>
      <div style={s.header}>
        <div>
          <div style={s.ticker}>{result.ticker}</div>
          <div style={s.company}>{result.company}</div>
          {result.personality && (
            <div style={{ fontSize: '11px', color: '#a78bfa', marginTop: '4px' }}>
              {result.personality} personality
            </div>
          )}
        </div>
        <div style={s.meta}>
          {isDemo && (
            <div style={{ ...s.metaItem, color: '#f6ad55', fontWeight: 700 }}>DEMO MODE</div>
          )}
          <div style={s.metaItem}>{new Date(result.generated_at).toLocaleString()}</div>
          <div style={s.metaItem}>{model}</div>
          {usage.estimated_cost_usd !== undefined && (
            <div style={{ ...s.metaItem, ...s.cost }}>
              ${usage.estimated_cost_usd?.toFixed(4)} cost
            </div>
          )}
        </div>
      </div>
      <div style={s.content}>
        <BriefMarkdown content={result.brief || result.report || ''} />
      </div>
    </div>
  )
}
