"""
Phase 4 — Multi-Agent CrewAI System
HedgeOS multi-agent research crew: 6 specialized agents working in sequence.

Execution order:
  1. Data Agent     — fetches all 5 data sources in parallel
  2. Signal Agent   — synthesizes signals and confidence score   (depends on 1)
  3. Industry Agent — competitive analysis, bull/bear cases      (depends on 1)
  4. Risk Agent     — key risks and thesis-breaking events       (depends on 1)
  5. Edge Agent     — alt-data edges and weekly signals          (depends on 1)
  6. Fact Checker   — validates, integrates, produces final brief (depends on 2-5)

Data agent runs first. Agents 2-5 run in parallel on its output.
Fact checker synthesizes all outputs into the final 6-section brief.

Usage:
    python crew_main.py NVDA "Nvidia" aggressive
    python crew_main.py TGT "Target" conservative
"""

import json
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def build_llm():
    """Build the LLM for CrewAI — Claude Opus primary, Groq fallback."""
    from crewai import LLM

    if ANTHROPIC_API_KEY:
        return LLM(
            model="claude-opus-4-6",
            api_key=ANTHROPIC_API_KEY,
        )
    elif GROQ_API_KEY:
        print("[CrewAI] Anthropic key not set — using Groq LLaMA fallback")
        return LLM(
            model="groq/llama-3.3-70b-versatile",
            api_key=GROQ_API_KEY,
        )
    else:
        raise RuntimeError("No AI provider configured. Set ANTHROPIC_API_KEY or GROQ_API_KEY.")


def run_crew(ticker: str, company: str, personality: str = "aggressive") -> dict:
    """
    Run the full 6-agent research crew for a ticker.

    Returns the final research brief dict with all 6 sections.
    """
    import asyncio

    from crewai import Crew, Process

    from app.agents.data_agent import create_data_agent, create_data_task
    from app.agents.edge_agent import create_edge_agent, create_edge_task
    from app.agents.fact_checker import create_fact_checker_agent, create_fact_check_task
    from app.agents.industry_agent import create_industry_agent, create_industry_task
    from app.agents.risk_agent import create_risk_agent, create_risk_task
    from app.agents.signal_agent import create_signal_agent, create_signal_task
    from data_fetcher import fetch_all

    ticker = ticker.upper()
    print(f"\n{'=' * 60}")
    print(f"[HedgeOS Crew] Starting research for {company} ({ticker})")
    print(f"[HedgeOS Crew] Personality: {personality}")
    print(f"{'=' * 60}\n")

    # ── Step 1: Fetch all data (parallel, outside CrewAI) ──────────────
    print("[Step 1/3] Fetching data from all 5 sources...")
    data_package = asyncio.run(fetch_all(ticker, company))

    # Serialize for passing to agents as context string
    data_str = json.dumps(data_package, default=str, indent=2)
    # Truncate to avoid context overflow (keep first 8000 chars of data summary)
    data_summary = data_str[:8000]

    # ── Step 2: Build LLM ──────────────────────────────────────────────
    llm = build_llm()

    # ── Step 3: Create agents ──────────────────────────────────────────
    print("[Step 2/3] Initializing 5 analysis agents...")

    signal_agent = create_signal_agent(llm)
    industry_agent = create_industry_agent(llm)
    risk_agent = create_risk_agent(llm)
    edge_agent = create_edge_agent(llm)
    fact_checker = create_fact_checker_agent(llm)

    # ── Step 4: Create tasks (agents 2-5 use data as input context) ───
    signal_task = create_signal_task(signal_agent, data_summary, ticker, company)
    industry_task = create_industry_task(industry_agent, data_summary, ticker, company)
    risk_task = create_risk_task(risk_agent, data_summary, ticker, company)
    edge_task = create_edge_task(edge_agent, data_summary, ticker, company)

    # ── Step 5: Run parallel analysis crew (agents 2-5) ──────────────
    print("[Step 3/3] Running analysis agents in parallel...")

    analysis_crew = Crew(
        agents=[signal_agent, industry_agent, risk_agent, edge_agent],
        tasks=[signal_task, industry_task, risk_task, edge_task],
        process=Process.sequential,  # CrewAI parallel via sequential with shared context
        verbose=True,
    )

    analysis_results = analysis_crew.kickoff()

    # Extract individual task outputs
    task_outputs = analysis_results.tasks_output if hasattr(analysis_results, "tasks_output") else []

    signal_out = task_outputs[0].raw if len(task_outputs) > 0 else "Signal analysis not available"
    industry_out = task_outputs[1].raw if len(task_outputs) > 1 else "Industry analysis not available"
    risk_out = task_outputs[2].raw if len(task_outputs) > 2 else "Risk analysis not available"
    edge_out = task_outputs[3].raw if len(task_outputs) > 3 else "Edge analysis not available"

    # ── Step 6: Fact checker synthesizes the final brief ──────────────
    print("[Final] Fact checker integrating and validating all outputs...")

    fact_task = create_fact_check_task(
        agent=fact_checker,
        ticker=ticker,
        company=company,
        data_output=data_summary,
        signal_output=signal_out,
        industry_output=industry_out,
        risk_output=risk_out,
        edge_output=edge_out,
    )

    final_crew = Crew(
        agents=[fact_checker],
        tasks=[fact_task],
        process=Process.sequential,
        verbose=True,
    )

    final_result = final_crew.kickoff()
    final_brief = final_result.raw if hasattr(final_result, "raw") else str(final_result)

    # ── Build result dict ──────────────────────────────────────────────
    result = {
        "ticker": ticker,
        "company": company,
        "personality": personality,
        "brief": final_brief,
        "agent_outputs": {
            "signal": signal_out,
            "industry": industry_out,
            "risk": risk_out,
            "edge": edge_out,
        },
        "data_sources": {
            k: "ok" if "error" not in v else f"error: {v.get('error')}"
            for k, v in data_package.items()
            if isinstance(v, dict) and k not in ["ticker", "company", "fetched_at"]
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "claude-opus-4-6" if ANTHROPIC_API_KEY else "groq/llama-3.3-70b-versatile",
    }

    return result


# ─────────────────────────────────────────────────────────
# CLI RUNNER
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    ticker_arg = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
    company_arg = sys.argv[2] if len(sys.argv) > 2 else "Nvidia"
    personality_arg = sys.argv[3] if len(sys.argv) > 3 else "aggressive"

    result = run_crew(ticker_arg, company_arg, personality_arg)

    out_file = f"crew_brief_{ticker_arg}_{personality_arg}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_file, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"FINAL RESEARCH BRIEF: {company_arg} ({ticker_arg})")
    print(f"Personality: {personality_arg}")
    print(f"{'=' * 60}\n")
    print(result["brief"])
    print(f"\nFull report saved → {out_file}")
