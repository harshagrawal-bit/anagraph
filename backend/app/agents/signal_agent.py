"""
Phase 4 — Multi-Agent System
SIGNAL AGENT: Synthesizes data from all sources into actionable market signals.
Identifies where sources converge or diverge, computes conviction level.
"""

from crewai import Agent, Task


def create_signal_agent(llm) -> Agent:
    return Agent(
        role="Quantitative Signal Analyst",
        goal=(
            "Synthesize raw data from all sources into clear, quantified market signals. "
            "Identify where data sources converge (high conviction) vs diverge (uncertainty). "
            "Produce a Signal Summary and Confidence Score for the investment thesis."
        ),
        backstory=(
            "You spent 12 years at a quant hedge fund building signal models. You know how "
            "to separate noise from signal. You are deeply skeptical of narrative — you want "
            "numbers that confirm the story, not a story built around numbers. You assign "
            "conviction scores based on the weight of evidence, not gut feel. You are the "
            "fund's BS detector — if the data doesn't support the thesis, you say so."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def create_signal_task(agent: Agent, data_output: str, ticker: str, company: str) -> Task:
    return Task(
        description=f"""
        Using the data package for {company} ({ticker}), synthesize the following signals:

        DATA PACKAGE:
        {data_output}

        Analyze and produce:

        1. SIGNAL CONVERGENCE MAP
           For each signal dimension below, state: Bullish / Bearish / Neutral + confidence %
           - Price momentum (1m, 3m, 1y returns vs market)
           - Valuation (cheap/fair/expensive relative to sector/history)
           - Earnings trend (accelerating/decelerating/stable)
           - Short interest (crowded short/neutral/crowded long)
           - Institutional ownership trend
           - Google Trends direction vs earnings proximity
           - Reddit sentiment (note if contrarian signal applies)
           - Recent news flow (positive/negative/neutral)

        2. SIGNAL SUMMARY (4-8 sentences)
           What does the aggregate weight of evidence say? Where do sources agree?
           Where do they contradict? What is the dominant signal?

        3. CONFIDENCE SCORE
           State: XX% BULL / XX% BEAR / NEUTRAL
           Explain: what would move this score 10 points in either direction?

        Be data-driven. Cite specific numbers. No narrative filler.
        """,
        agent=agent,
        expected_output=(
            "Signal Convergence Map with conviction ratings for each dimension. "
            "Signal Summary paragraph. Confidence Score with clear explanation. "
            "Total output 200-400 words."
        ),
        context=[],  # will be set by crew orchestrator with data task output
    )
