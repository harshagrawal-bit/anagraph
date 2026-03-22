"""
Phase 4 — Multi-Agent System
FACT CHECKER AGENT: Final quality control agent. Validates all claims,
catches contradictions between agents, and produces the final integrated brief.
Last agent to run — nothing ships without this review.
"""

from crewai import Agent, Task


def create_fact_checker_agent(llm) -> Agent:
    return Agent(
        role="Research Quality Control & Integration Analyst",
        goal=(
            "Validate all factual claims from other agents against the raw data. "
            "Identify contradictions, unsupported assertions, or fabricated numbers. "
            "Integrate all agent outputs into one coherent, polished research brief "
            "with the exact 6-section structure required."
        ),
        backstory=(
            "You were a research director at Bridgewater, running quality control on "
            "all research memos before they reached the investment committee. You have "
            "zero tolerance for unsupported claims or internal contradictions. You've "
            "caught analysts making up numbers under deadline pressure. You verify every "
            "statistic against its stated source. You also have an editorial eye — you "
            "remove redundancy and tighten prose without losing precision. "
            "The brief you produce is the final product clients see."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def create_fact_check_task(
    agent: Agent,
    ticker: str,
    company: str,
    data_output: str,
    signal_output: str,
    industry_output: str,
    risk_output: str,
    edge_output: str,
) -> Task:
    return Task(
        description=f"""
        Validate and integrate all research agent outputs into the final brief for
        {company} ({ticker}).

        RAW DATA (source of truth):
        {data_output[:2000]}

        SIGNAL AGENT OUTPUT:
        {signal_output}

        INDUSTRY AGENT OUTPUT:
        {industry_output}

        RISK AGENT OUTPUT:
        {risk_output}

        EDGE AGENT OUTPUT:
        {edge_output}

        YOUR TASKS:

        1. FACT VALIDATION
           - Check all specific numbers cited by agents against the raw data
           - Flag any claim that cannot be verified as [UNVERIFIED]
           - Remove any fabricated or hallucinated statistics
           - Note contradictions between agents

        2. INTEGRATION
           Produce the FINAL RESEARCH BRIEF with EXACTLY these 6 sections:

           ## SIGNAL SUMMARY
           [Synthesize signal agent + your validation — 4-8 sentences, all cited]

           ## BULL CASE
           [3 bullets from industry agent, validated and quantified]

           ## BEAR CASE
           [3 bullets from industry agent + risk agent, validated and quantified]

           ## KEY RISKS
           [Top 4 risks from risk agent, validated, with specific triggers]

           ## CONFIDENCE SCORE
           [From signal agent, with direction e.g. "68% BULL" — explain briefly]

           ## SIGNALS TO MONITOR WEEKLY
           [3 specific signals from edge agent — name metric, frequency, bull/bear triggers]

        3. QUALITY CHECKLIST
           Before finalizing, confirm:
           □ All numbers have source citations [SEC], [MARKET], [TRENDS], [REDDIT], [WEB]
           □ No fabricated statistics
           □ Bull and Bear cases are balanced (not cheerleading or doom-saying)
           □ Signals to Monitor are SPECIFIC, not generic
           □ Brief reads like a professional hedge fund memo

        Output the final brief cleanly. Quality > length.
        """,
        agent=agent,
        expected_output=(
            "Final validated research brief with exactly 6 sections: "
            "SIGNAL SUMMARY, BULL CASE, BEAR CASE, KEY RISKS, CONFIDENCE SCORE, "
            "SIGNALS TO MONITOR WEEKLY. All claims cited. Clean professional format."
        ),
    )
