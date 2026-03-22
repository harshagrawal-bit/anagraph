"""
Phase 4 — Multi-Agent System
RISK AGENT: Identifies, quantifies, and prioritizes investment risks.
Produces Key Risks section and specific thesis-breaking events to monitor.
The most important agent — capital preservation starts here.
"""

from crewai import Agent, Task


def create_risk_agent(llm) -> Agent:
    return Agent(
        role="Risk Management Analyst",
        goal=(
            "Identify, quantify, and prioritize all material risks to the investment thesis. "
            "Find the specific events that would break the thesis entirely. "
            "Think like a risk manager: assume the bull case is wrong and explain why."
        ),
        backstory=(
            "You ran risk management at a $20B multi-strat fund. You've seen every blowup — "
            "Archegos, Enron, short squeezes, earnings disasters. Your job is to stress-test "
            "every thesis before capital is deployed. You are paid to be the devil's advocate. "
            "You ask: 'What would cause me to lose 40% on this position?' and then you work "
            "backward from that scenario. You make the PMs uncomfortable — that's your job."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def create_risk_task(agent: Agent, data_output: str, ticker: str, company: str) -> Task:
    return Task(
        description=f"""
        Perform a comprehensive risk analysis for {company} ({ticker}).

        DATA AVAILABLE:
        {data_output}

        Analyze and produce:

        1. KEY RISKS (4-6 items)
           For each risk:
           - Risk name (clear, specific, not generic)
           - Current evidence this risk is real (cite data)
           - Probability assessment: Low / Medium / High
           - Impact if realized: state expected % drawdown
           - Mitigation: what would reduce this risk?

           Categories to consider:
           - Fundamental (earnings, margins, leverage)
           - Competitive (market share loss, pricing pressure, disruption)
           - Regulatory/Legal (pending investigations, compliance costs)
           - Macro (rate sensitivity, FX exposure, commodity exposure)
           - Technical (crowded positioning, short squeeze potential, options overhang)
           - Management (execution risk, key person risk, incentive misalignment)
           - Accounting (revenue recognition, off-balance-sheet liabilities)

        2. THESIS-BREAKING EVENTS (3-5 bullets)
           Specific, observable events that would cause immediate position exit:
           Format: [Trigger] → [Expected market reaction] → [Action]
           Example: "Q3 revenue misses by >5% → stock -15% to -25% → exit position"

        3. RISK SCORE
           Overall risk rating: Low / Medium / High / Very High
           One sentence justification.

        Be specific. Quantify everything possible. Do not write generic risks like
        "macroeconomic uncertainty" — that tells us nothing.
        """,
        agent=agent,
        expected_output=(
            "4-6 Key Risks with evidence, probability, and impact quantified. "
            "3-5 Thesis-Breaking Events with specific triggers and expected reactions. "
            "Overall Risk Score. Total 400-600 words."
        ),
    )
