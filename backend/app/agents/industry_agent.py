"""
Phase 4 — Multi-Agent System
INDUSTRY AGENT: Deep sector and competitive analysis.
Evaluates company position within industry structure, moat durability, and
competitive dynamics. Produces bull and bear cases.
"""

from crewai import Agent, Task


def create_industry_agent(llm) -> Agent:
    return Agent(
        role="Sector Research Analyst",
        goal=(
            "Produce a rigorous industry and competitive analysis for the target company. "
            "Evaluate moat durability, competitive positioning, and sector tailwinds/headwinds. "
            "Build the Bull Case and Bear Case from fundamental industry dynamics."
        ),
        backstory=(
            "You covered technology and consumer sectors at Goldman Sachs for 10 years before "
            "joining the fund. You understand Porter's Five Forces in your sleep. You think in "
            "terms of TAM expansion, pricing power, switching costs, and network effects. "
            "You've seen too many companies with great stories but deteriorating fundamentals — "
            "you always ask: 'why does this competitive advantage last 5 years?' "
            "You also study the short side — which moats are crumbling?"
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def create_industry_task(agent: Agent, data_output: str, ticker: str, company: str) -> Task:
    return Task(
        description=f"""
        Produce a sector and competitive analysis for {company} ({ticker}).

        DATA AVAILABLE:
        {data_output}

        Using the data plus your deep sector knowledge, analyze:

        1. COMPETITIVE POSITION (200 words max)
           - Market share position (leader/challenger/niche)
           - Moat sources: pricing power, switching costs, network effects, cost advantage, IP
           - Moat durability: is it strengthening or eroding? Why?
           - Named competitors and their relative positions

        2. SECTOR DYNAMICS (150 words max)
           - Current sector tailwinds (what structural forces benefit this company?)
           - Current sector headwinds (what structural forces threaten it?)
           - Where are we in the sector cycle?

        3. BULL CASE (3 bullets)
           Each bullet: bold header + specific data + upside quantification
           Focus on: growth vectors, margin expansion potential, re-rating catalysts

        4. BEAR CASE (3 bullets)
           Each bullet: bold header + specific evidence + downside quantification
           Focus on: competitive threats, margin compression, TAM ceiling, moat erosion

        Ground everything in the data provided. Cite specific metrics.
        """,
        agent=agent,
        expected_output=(
            "Competitive Position analysis, Sector Dynamics summary, "
            "3 Bull Case bullets with data, 3 Bear Case bullets with data. "
            "Total 400-600 words. All claims cited with data source."
        ),
    )
