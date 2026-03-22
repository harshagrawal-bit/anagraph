"""
Phase 6 — Edge Discovery Engine
HYPOTHESIS ENGINE: Uses Claude Opus to study a fund's historical edges,
extract the underlying logic, and generate NEW edge hypotheses for any ticker.

This is the most impressive feature and the deepest long-term moat.
After 12 months of use, the hypothesis engine knows which edge patterns
work for THIS specific fund's style and portfolio.
"""

import json
import os
import textwrap
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

from app.edges.edge_library import (
    EDGE_PATTERNS,
    get_validated_edges,
    load_fund_edges,
    save_edge_hypothesis,
)
from app.personality.profile_manager import load_profile

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# ─────────────────────────────────────────────────────────
# HYPOTHESIS GENERATION PROMPT
# ─────────────────────────────────────────────────────────

HYPOTHESIS_PROMPT = textwrap.dedent("""
You are a senior alternative data analyst at a premier long/short hedge fund.
Your job is to generate SPECIFIC, ACTIONABLE edge hypotheses for a company.

An "edge hypothesis" is a specific non-consensus data signal that:
1. Is observable BEFORE the market sees it in financial statements
2. Has a clear causal mechanism (not just correlation)
3. Can be accessed through public or licensable data
4. Has a defined lead time (when the signal appears vs when it shows up in results)

FUND CONTEXT:
{fund_context}

COMPANY BEING ANALYZED: {company} ({ticker})
SECTOR: {sector}
INDUSTRY: {industry}

VALIDATED EDGES FOR THIS FUND (what has worked before):
{validated_edges}

CURRENT DATA SIGNALS AVAILABLE:
{current_signals}

THE 6 EDGE PATTERN CATEGORIES:
{pattern_descriptions}

─────────────────────────────────────────────────────
Generate exactly 5 edge hypotheses for {company} ({ticker}).
Each hypothesis must follow this exact format:

HYPOTHESIS [N]:
Pattern Category: [one of the 6 pattern names]
Hypothesis Title: [concise title, 5-10 words]
Signal Description: [2-3 sentences — what exactly to look for and where]
Data Source: [specific, accessible data source with URL or access method if free]
Lead Time: [X weeks/months before it appears in financials]
Current Signal: [Bullish / Bearish / Neutral / Insufficient Data]
Evidence: [any current data supporting this hypothesis from the data provided]
Causal Mechanism: [1-2 sentences explaining WHY this predicts financial performance]
Monitoring Cadence: [Daily / Weekly / Monthly / On specific trigger]
Validation Criteria: [What would prove/disprove this hypothesis within 1-2 quarters?]
Conviction Level: [Low / Medium / High]
─────────────────────────────────────────────────────

Generate hypotheses that are SPECIFIC to {company}'s business model.
Generic hypotheses (like "monitor Google Trends") get rejected.
The best hypotheses are ones no sell-side analyst is writing about.
""")


def generate_hypotheses(
    ticker: str,
    company: str,
    fund_id: str,
    data_package: dict | None = None,
    n_hypotheses: int = 5,
) -> list[dict]:
    """
    Generate N edge hypotheses for a ticker using Claude Opus.
    Leverages the fund's validated edge history to improve relevance.

    Args:
        ticker: Stock ticker (e.g., "NVDA")
        company: Full company name (e.g., "Nvidia")
        fund_id: Fund profile to use for personalization
        data_package: Optional data from fetch_all() for current signal context
        n_hypotheses: Number of hypotheses to generate (default 5)

    Returns:
        List of hypothesis dicts, each saved to the edge library.
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Build context
    profile = load_profile(fund_id)
    validated_edges = get_validated_edges(fund_id)

    fund_context = _build_fund_context(profile)
    validated_edges_text = _format_validated_edges(validated_edges)
    current_signals_text = _format_current_signals(data_package or {})
    pattern_descriptions = _format_patterns()

    # Get sector/industry from data package if available
    sector = "Technology"
    industry = "Unknown"
    if data_package and "market_data" in data_package:
        md = data_package["market_data"]
        sector = md.get("sector", sector)
        industry = md.get("industry", industry)

    prompt = HYPOTHESIS_PROMPT.format(
        fund_context=fund_context,
        company=company,
        ticker=ticker,
        sector=sector,
        industry=industry,
        validated_edges=validated_edges_text,
        current_signals=current_signals_text,
        pattern_descriptions=pattern_descriptions,
    )

    print(f"[HypothesisEngine] Generating {n_hypotheses} edge hypotheses for {ticker}...")

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_output = response.content[0].text
    hypotheses = _parse_hypotheses(raw_output, ticker, company, fund_id)

    print(f"[HypothesisEngine] Generated {len(hypotheses)} hypotheses for {ticker}")
    return hypotheses


def _build_fund_context(profile: dict) -> str:
    style = profile.get("investment_style", {})
    sectors = profile.get("sector_focus", {})
    edges = profile.get("historical_edges", {})

    lines = [
        f"Fund: {profile.get('fund_name', 'Unknown')}",
        f"Style: {style.get('approach', 'long_short')} | "
        f"Horizon: {style.get('time_horizon', '6-12 months')}",
        f"Primary sectors: {', '.join(sectors.get('primary', []))}",
        f"Pattern preferences: {', '.join(edges.get('pattern_preferences', []))}",
        f"Anti-patterns (avoid): {', '.join(edges.get('anti_patterns', []))}",
    ]
    return "\n".join(lines)


def _format_validated_edges(edges: list[dict]) -> str:
    if not edges:
        return "No validated edges yet — this fund is building its edge library."

    lines = []
    for edge in edges[:10]:  # top 10 validated edges
        lines.append(
            f"- [{edge.get('pattern_id', 'unknown')}] {edge.get('title', 'N/A')}: "
            f"{edge.get('description', '')[:100]}"
        )
    return "\n".join(lines)


def _format_current_signals(data_package: dict) -> str:
    """Extract key signals from data package for hypothesis context."""
    lines = []

    md = data_package.get("market_data", {})
    if "price" in md:
        p = md["price"]
        lines.append(f"Price: ${p.get('current')} | 1m: {p.get('return_1m_pct')}% | "
                     f"3m: {p.get('return_3m_pct')}%")
        lines.append(f"Short interest: {md.get('fundamentals', {}).get('short_pct_of_float', 'N/A')}")

    gt = data_package.get("google_trends", {})
    if "trend_direction_90d" in gt:
        lines.append(f"Google Trends 90d: {gt['trend_direction_90d'].upper()}")

    rd = data_package.get("reddit", {})
    if "sentiment_summary" in rd:
        ss = rd["sentiment_summary"]
        lines.append(f"Reddit sentiment: {ss.get('overall', 'N/A').upper()} "
                     f"({ss.get('bull_pct')}% bull)")

    sec = data_package.get("sec_edgar", {})
    filings = sec.get("filings", {})
    if filings.get("8K_recent"):
        lines.append(f"Recent 8-Ks: {len(filings['8K_recent'])} in last period")

    web = data_package.get("web_intelligence", {})
    intel = web.get("intelligence", {})
    if intel.get("recent_news"):
        news_count = len(intel["recent_news"])
        lines.append(f"Recent news items found: {news_count}")

    return "\n".join(lines) if lines else "No current data available"


def _format_patterns() -> str:
    lines = []
    for pid, pattern in EDGE_PATTERNS.items():
        lines.append(
            f"{pattern['name']}:\n"
            f"  {pattern['description'][:120]}\n"
            f"  Lead time: {pattern.get('lead_time_weeks', 'varies')} weeks | "
            f"Best for: {', '.join(pattern.get('best_for', []))}"
        )
    return "\n\n".join(lines)


def _parse_hypotheses(raw_text: str, ticker: str, company: str, fund_id: str) -> list[dict]:
    """
    Parse Claude's hypothesis output into structured dicts and save to edge library.
    """
    hypotheses = []
    sections = raw_text.split("HYPOTHESIS ")

    for section in sections[1:]:  # skip first empty split
        lines = section.strip().split("\n")
        h = {
            "ticker": ticker.upper(),
            "company": company,
            "fund_id": fund_id,
            "tickers": [ticker.upper()],
            "raw_text": section.strip()[:2000],
        }

        for line in lines:
            if ":" in line:
                key, _, value = line.partition(":")
                key_clean = key.strip().lower().replace(" ", "_")
                value_clean = value.strip()

                key_map = {
                    "pattern_category": "pattern_id",
                    "hypothesis_title": "title",
                    "signal_description": "description",
                    "data_source": "data_source",
                    "lead_time": "lead_time",
                    "current_signal": "current_signal",
                    "evidence": "evidence",
                    "causal_mechanism": "causal_mechanism",
                    "monitoring_cadence": "monitoring_cadence",
                    "validation_criteria": "validation_criteria",
                    "conviction_level": "conviction_level",
                }

                mapped_key = key_map.get(key_clean, key_clean)
                if mapped_key in key_map.values():
                    h[mapped_key] = value_clean

        # Map pattern name to ID
        pattern_name = h.get("pattern_id", "").lower()
        for pid, pdata in EDGE_PATTERNS.items():
            if pid.replace("_", " ") in pattern_name or pattern_name in pdata["name"].lower():
                h["pattern_id"] = pid
                break

        if h.get("title"):
            saved = save_edge_hypothesis(fund_id, h)
            hypotheses.append(saved)

    return hypotheses


# ─────────────────────────────────────────────────────────
# BATCH HYPOTHESIS REVIEW
# ─────────────────────────────────────────────────────────

def review_pending_hypotheses(fund_id: str) -> list[dict]:
    """
    Return all pending hypotheses that need validation.
    Used by the frontend Edge Discovery screen.
    """
    all_edges = load_fund_edges(fund_id)
    return [e for e in all_edges if e.get("status") == "hypothesis"]


def get_hypothesis_digest(fund_id: str) -> str:
    """
    Generate a weekly digest summary of edge hypotheses for a fund.
    Formatted for analyst consumption.
    """
    edges = load_fund_edges(fund_id)
    pending = [e for e in edges if e.get("status") == "hypothesis"]
    validated = [e for e in edges if e.get("status") == "validated"]
    rejected = [e for e in edges if e.get("status") == "rejected"]

    lines = [
        f"EDGE HYPOTHESIS DIGEST — {datetime.now().strftime('%Y-%m-%d')}",
        f"{'=' * 50}",
        f"Library: {len(edges)} total | {len(pending)} pending | "
        f"{len(validated)} validated | {len(rejected)} rejected",
        "",
    ]

    if pending:
        lines.append(f"PENDING REVIEW ({len(pending)}):")
        for e in pending[-5:]:
            lines.append(
                f"  [{e.get('id')}] {e.get('title', 'Untitled')} "
                f"({e.get('ticker')}) — {e.get('conviction_level', 'N/A')} conviction"
            )
        lines.append("")

    if validated:
        lines.append(f"TOP VALIDATED EDGES ({min(3, len(validated))}):")
        for e in validated[:3]:
            lines.append(
                f"  [{e.get('id')}] {e.get('title', 'Untitled')} "
                f"— {e.get('pattern_id', 'N/A')}"
            )

    return "\n".join(lines)
