import { useState } from 'react'
import ResearchBrief from '../components/ResearchBrief.jsx'

// Demo vault data — populated from real runs as they happen
const DEMO_REPORTS = [
  {
    ticker: 'NVDA', company: 'Nvidia Corporation',
    personality: 'Aggressive Growth', personality_key: 'aggressive',
    generated_at: '2026-03-22T15:44:47Z',
    model: 'claude-opus-4-6',
    usage: { estimated_cost_usd: 0.31 },
    brief: `## SIGNAL SUMMARY
Nvidia shows exceptional multi-source signal convergence. Market data confirms the stock is 8% below its 52-week high with short interest at only 2.1% of float, indicating minimal bearish positioning [MARKET]. Google Trends for "Nvidia AI" and "H100" show a rising 90-day trend, up 34% vs the prior 3-month period, suggesting enterprise demand is accelerating [TRENDS]. Reddit sentiment is broadly bullish at 71% across 63 posts — approaching contrarian threshold but not yet extreme [REDDIT]. The most recent 8-K disclosed a $25B additional share buyback authorization [SEC]. Web intelligence shows 4 analyst upgrades in the past 30 days with target price increases averaging 18% [WEB]. Overall: dominant bull signal with one area of caution (crowded retail positioning).

## BULL CASE
1. **Data center revenue acceleration structurally underestimated** — Q3 FY2025 data center revenue of $30.8B grew 112% YoY, and management guided Q4 at $37.5B (another 22% sequential step-up). The Blackwell architecture ramp is supply-constrained, not demand-constrained — TSMC CoWoS capacity is the binding constraint, which is being expanded [SEC, MARKET].

2. **Gross margin expansion runway remains intact** — Gross margins reached 74.6% in Q3, up from 56.1% two years ago. The shift from hardware-only to hardware+software (NIM, CUDA ecosystem, DGX Cloud) supports continued expansion toward 75-78%. Every 100bps of margin expansion = ~$400M in incremental operating income at current revenue run rate [SEC, Item 8].

3. **Sovereign AI demand is a new, underpenetrated TAM** — 50+ countries are actively building national AI infrastructure. This demand is non-cyclical (national security/competitiveness framing) and is not reflected in most sell-side models. Management cited sovereign AI as a "new category" on the last earnings call with $4B+ already contracted [WEB].

## BEAR CASE
1. **Blackwell supply-demand normalization risk in H2 2026** — TSMC CoWoS capacity expansion will likely create supply relief by H2 2026. Historically, when AI hardware supply exceeds demand after a shortage cycle, gross margins compress 500-800bps rapidly. The market may begin pricing this 6-9 months early [MARKET, WEB].

2. **Customer concentration creating single-point risk** — Microsoft, Google, Amazon, and Meta represent an estimated 40-50% of data center revenue. Any major cloud provider pausing or shifting to in-house silicon (Google TPU, Amazon Trainium) would create a step-down [SEC, Item 1A].

3. **Regulatory export control escalation** — The Biden-era chip export rules are being tightened under the Trump administration's AI diffusion framework. China + restricted countries represent ~15% of revenue being progressively locked out. Further restrictions on H20 sales to "Tier 2" countries could accelerate [WEB, SEC Item 1A].

## KEY RISKS
• **Export control expansion to Tier 2 countries** → -$4-6B annualized revenue impact → -10% to -15% stock reaction → Reduce position 50%
• **Hyperscaler CapEx guidance cut** at any major cloud earnings → Sector de-rating of 15-25% → Exit within 48 hours
• **Gross margin compression below 70% guidance** at next earnings → Multiple compression 5-8 turns on NTM P/E → Reassess thesis
• **AMD MI400 competitive breakthrough** (benchmarks showing parity) → Narrative shift risk → Hedge with AMD calls

## CONFIDENCE SCORE
78% BULL

The weight of evidence is strongly bullish. Revenue acceleration is real and supply-constrained. Gross margin expansion is structural. The primary risks (export controls, hyperscaler spending) are known and partially priced in. Conviction would increase to 85%+ on any pullback to $110-115 where EV/NTM earnings compresses to 30x. Thesis plays out over 6-12 months; the next earnings call is the near-term catalyst.

## SIGNALS TO MONITOR WEEKLY
1. **TSMC CoWoS capacity utilization** — Quarterly (TSMC earnings, ~mid-month after quarter end). Bull trigger: utilization >90% = NVDA supply still constrained = demand healthy. Bear trigger: management commentary on capacity "normalizing" = end of shortage premium.

2. **LinkedIn "CUDA" + "data center" enterprise job postings** — Weekly. Track postings at Fortune 500 companies via LinkedIn search. Bull: rising >10% MoM = new enterprise AI projects starting. Bear: flat or declining = CapEx pause risk. Current direction: Rising (estimated +23% vs 60 days ago).

3. **Short interest bi-weekly FINRA report** — Every 2 weeks. Current: 2.1% of float. Bull: declining below 1.5% = no conviction on short side. Bear: rising above 5% = institutional bears building positions, potential indicator of deteriorating fundamentals ahead.`,
  },
]

const s = {
  page: { padding: '32px', maxWidth: '1400px' },
  header: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '28px' },
  title: { fontSize: '22px', fontWeight: 700, color: '#e2e8f0' },
  sub: { fontSize: '13px', color: '#718096', marginTop: '4px' },
  layout: { display: 'grid', gridTemplateColumns: '280px 1fr', gap: '24px', alignItems: 'start' },
  sidebar: { background: '#0d1117', border: '1px solid #1e2738', borderRadius: '10px', overflow: 'hidden' },
  sidebarHeader: {
    padding: '14px 16px', borderBottom: '1px solid #1e2738',
    fontSize: '11px', color: '#718096', textTransform: 'uppercase', letterSpacing: '1px',
  },
  item: {
    padding: '12px 16px', borderBottom: '1px solid #111827', cursor: 'pointer',
    transition: 'background 0.15s',
  },
  itemActive: { background: '#111827', borderLeft: '2px solid #3b82f6' },
  itemTicker: { fontSize: '14px', fontWeight: 700, color: '#60a5fa' },
  itemCompany: { fontSize: '11px', color: '#718096', marginTop: '2px' },
  itemMeta: { display: 'flex', gap: '8px', marginTop: '4px', fontSize: '11px', color: '#4a5568' },
  scoreChip: { fontSize: '10px', padding: '1px 6px', borderRadius: '3px', fontWeight: 600 },
  mainPanel: { background: '#0d1117', border: '1px solid #1e2738', borderRadius: '10px', overflow: 'hidden' },
  empty: {
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    justifyContent: 'center', height: '400px', color: '#4a5568',
  },
  filterRow: {
    padding: '12px 16px', borderBottom: '1px solid #111827',
    display: 'flex', gap: '8px',
  },
  filterBtn: {
    background: 'none', border: '1px solid #2d3748', borderRadius: '4px',
    color: '#718096', padding: '4px 10px', fontSize: '11px', cursor: 'pointer',
  },
  filterBtnActive: { borderColor: '#3b82f6', color: '#60a5fa', background: '#1e2738' },
}

export default function Vault() {
  const [reports] = useState(DEMO_REPORTS)
  const [selected, setSelected] = useState(DEMO_REPORTS[0] || null)
  const [filter, setFilter] = useState('all')

  const filtered = filter === 'all' ? reports : reports.filter(r => r.personality_key === filter)

  return (
    <div style={s.page}>
      <div style={s.header}>
        <div>
          <div style={s.title}>Research Vault</div>
          <div style={s.sub}>Stored research briefs · {reports.length} total</div>
        </div>
      </div>

      <div style={s.layout}>
        {/* Sidebar list */}
        <div style={s.sidebar}>
          <div style={s.sidebarHeader}>Saved Briefs</div>
          <div style={s.filterRow}>
            {['all', 'aggressive', 'conservative', 'macro'].map(f => (
              <button key={f} style={{ ...s.filterBtn, ...(filter === f ? s.filterBtnActive : {}) }}
                onClick={() => setFilter(f)}>
                {f}
              </button>
            ))}
          </div>
          {filtered.length === 0 ? (
            <div style={{ padding: '24px', color: '#4a5568', fontSize: '13px', textAlign: 'center' }}>
              No briefs yet. Run research to populate the vault.
            </div>
          ) : filtered.map(report => (
            <div
              key={report.ticker + report.generated_at}
              style={{ ...s.item, ...(selected === report ? s.itemActive : {}) }}
              onClick={() => setSelected(report)}
              onMouseEnter={e => { if (selected !== report) e.currentTarget.style.background = '#0f141f' }}
              onMouseLeave={e => { if (selected !== report) e.currentTarget.style.background = '' }}
            >
              <div style={s.itemTicker}>{report.ticker}</div>
              <div style={s.itemCompany}>{report.company}</div>
              <div style={s.itemMeta}>
                <span>{new Date(report.generated_at).toLocaleDateString()}</span>
                <span style={{
                  ...s.scoreChip,
                  color: '#48bb78', background: '#16242044',
                }}>
                  {report.personality}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Main content */}
        <div style={s.mainPanel}>
          {selected ? (
            <ResearchBrief result={selected} />
          ) : (
            <div style={s.empty}>
              <div style={{ fontSize: '40px', marginBottom: '12px' }}>⊞</div>
              <div>Select a brief from the vault</div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
