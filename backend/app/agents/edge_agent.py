"""
Phase 4 — Multi-Agent System
EDGE AGENT: Identifies non-consensus signals and alternative data edges.
Surfaces what the market may be missing. Produces the "Signals to Monitor Weekly"
and flags any early-warning alternative data patterns.
"""

from crewai import Agent, Task


# The six edge patterns from the doc (Phase 6 Edge Discovery Engine)
EDGE_PATTERNS = """
1. PHYSICAL WORLD PRECEDES FINANCIAL REPORTING
   Parking lots, factory smoke, ship movements, satellite imagery
   → Real-world activity shows up 4-8 weeks before quarterly reports

2. DIGITAL BEHAVIOR PRECEDES REAL BEHAVIOR
   Google Trends, app downloads, job postings, web traffic
   → Consumer intent visible before revenue materializes

3. SUPPLY CHAIN SIGNALS UPSTREAM
   Supplier earnings, raw material prices, shipping rates, component orders
   → Upstream data predicts downstream revenue with 1-2 quarter lag

4. MANAGEMENT BEHAVIOR DIVERGES FROM WORDS
   Insider buying/selling, executive departures, option exercise timing
   → Actions reveal conviction that public commentary conceals

5. CROSS-DOMAIN KNOWLEDGE TRANSFER
   Epidemiology models applied to demand curves, sports analytics for team dynamics
   → Non-consensus frameworks applied to financial problems

6. INFORMATION LAG EXPLOITATION
   Data that exists 4-8 weeks before appearing in SEC filings
   → FOIA requests, state databases, permit filings, job postings
"""


def create_edge_agent(llm) -> Agent:
    return Agent(
        role="Alternative Data & Edge Discovery Specialist",
        goal=(
            "Identify non-consensus signals, alternative data edges, and early-warning "
            "indicators that the market is likely missing. Surface what mainstream analysts "
            "are not looking at. Produce specific, actionable signals to monitor weekly."
        ),
        backstory=(
            "You spent 8 years at a data-driven hedge fund pioneering alt-data strategies. "
            "You tracked satellite parking lot data before it was mainstream. You used "
            "job posting trends to predict Amazon AWS revenue 2 quarters early. "
            "You think in leading indicators, not lagging ones. You know that by the time "
            "something appears in a 10-K, the market already knows it. "
            "Your edge is finding signals that precede the data everyone else watches."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def create_edge_task(agent: Agent, data_output: str, ticker: str, company: str) -> Task:
    return Task(
        description=f"""
        Identify alternative data edges and non-consensus signals for {company} ({ticker}).

        DATA AVAILABLE:
        {data_output}

        KNOWN EDGE PATTERN CATEGORIES:
        {EDGE_PATTERNS}

        Produce:

        1. EDGE OPPORTUNITIES (2-3 items)
           For each edge:
           - Which edge pattern does it map to?
           - What specific data would confirm or deny it?
           - Where can this data be sourced? (free or accessible)
           - What is the lead time before it shows up in financials?
           - Current signal direction: positive / negative / neutral

        2. SIGNALS TO MONITOR WEEKLY (exactly 3)
           These are the 3 most actionable, specific things to track.
           Format for each:
           - Metric name and data source
           - Frequency: daily / weekly / monthly / on earnings
           - Bullish trigger: [specific threshold or event]
           - Bearish trigger: [specific threshold or event]
           - Why this metric matters for THIS company specifically

           Examples of good signals (be this specific):
           - "Google Trends for '{company}' — track weekly. Rising >20% vs 4-week avg
             heading into earnings = bull signal. Flat or falling = demand softness."
           - "Job postings on LinkedIn for {company} engineering roles — track monthly.
             >10% growth = expansion signal. Cuts in AI/ML roles = pivot risk."

        3. INFORMATION LAG OPPORTUNITY
           Is there any data that exists right now but won't appear in filings for 60+ days?
           Name it specifically and explain how to access it.

        Think creatively. The best edges are counterintuitive.
        """,
        agent=agent,
        expected_output=(
            "2-3 Edge Opportunities mapped to pattern categories. "
            "3 specific weekly signals with bullish/bearish triggers. "
            "Information lag opportunity if identified. Total 300-500 words."
        ),
    )
