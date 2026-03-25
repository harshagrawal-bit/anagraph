"""
Phase 3 — Single Agent Brain
HedgeOS core AI: Claude Opus agent that ingests multi-source data,
applies fund personality, and produces a 6-section structured research brief.

The six sections (non-negotiable per doc):
  1. SIGNAL SUMMARY  — what the data shows, with source citations
  2. BULL CASE       — top 3 reasons to be long, each data-backed
  3. BEAR CASE       — top 3 risks to the thesis, each data-backed
  4. KEY RISKS       — specific events that would break the thesis
  5. CONFIDENCE SCORE — percentage with direction e.g. "71% BULL"
  6. SIGNALS TO MONITOR WEEKLY — 3 specific things to track going forward

Usage:
    python brain.py NVDA "Nvidia" aggressive
    python brain.py TGT "Target" conservative
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")
OPEN_ROUTER_MODEL = os.getenv("OPEN_ROUTER_MODEL", "anthropic/claude-opus-4-5")
OPEN_ROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ─────────────────────────────────────────────────────────
# FUND PERSONALITY PROFILES
# These shape how the AI analyst frames the research.
# Each fund has a different risk tolerance, time horizon,
# and focus — the same data produces different conclusions.
# ─────────────────────────────────────────────────────────

FUND_PERSONALITIES = {
    "aggressive": {
        "name": "Aggressive Growth",
        "style": "long/short growth equity",
        "time_horizon": "3-12 months",
        "focus": "earnings acceleration, momentum, narrative catalysts",
        "bias": "willing to pay for growth, high-conviction concentrated bets",
        "risk_tolerance": "high — 20%+ drawdown acceptable for 3-5x upside",
        "short_criteria": "decelerating growth, narrative collapse, valuation compression",
        "key_metrics": "revenue growth, gross margin expansion, forward EV/revenue",
        "personality_prompt": (
            "You are an aggressive growth fund manager. You seek companies growing revenue "
            ">30% YoY with expanding margins. You buy narrative catalysts early and sell into "
            "strength. You are willing to hold through volatility for multi-bagger returns. "
            "You weigh momentum data and alternative signals heavily. You are NOT deterred by "
            "high valuations if growth justifies them. Flag any deceleration risk immediately."
        ),
    },
    "conservative": {
        "name": "Conservative Value",
        "style": "long-biased deep value",
        "time_horizon": "12-36 months",
        "focus": "FCF yield, balance sheet quality, margin of safety",
        "bias": "only buy when trading below intrinsic value, patient accumulation",
        "risk_tolerance": "low — capital preservation priority, max 10% position sizing",
        "short_criteria": "fraudulent accounting, unsustainable leverage, value traps",
        "key_metrics": "P/FCF, EV/EBITDA, net debt/EBITDA, dividend coverage",
        "personality_prompt": (
            "You are a conservative value fund manager. You only invest when there is a clear "
            "margin of safety — you want to buy $1 of value for $0.70. You focus on FCF "
            "generation, balance sheet strength, and dividend sustainability. High growth at "
            "any price is not your style. You are deeply skeptical of accounting quality and "
            "management promises. You hold for 2-3 years and let value accrete."
        ),
    },
    "macro": {
        "name": "Global Macro",
        "style": "top-down macro-driven equity",
        "time_horizon": "1-6 months",
        "focus": "macro regime, sector rotation, cross-asset signals",
        "bias": "position sizing driven by macro conviction, not bottoms-up research",
        "risk_tolerance": "medium — uses options for defined risk expression",
        "short_criteria": "sector in macro headwind, rate sensitivity, FX exposure",
        "key_metrics": "beta to macro factors, rate sensitivity, USD/commodity exposure",
        "personality_prompt": (
            "You are a global macro fund manager. You evaluate individual stocks through a "
            "macro lens — sector tailwinds/headwinds, rate environment, commodity cycles, "
            "and geopolitical risk. You care deeply about a company's sensitivity to macro "
            "factors. You use options to express views with defined risk. You rotate sectors "
            "based on macro regime changes, not company-specific catalysts."
        ),
    },
    "quant": {
        "name": "Quantitative Systematic",
        "style": "factor-based systematic long/short",
        "time_horizon": "1-3 months",
        "focus": "factor exposures, statistical signals, mean reversion",
        "bias": "data-driven, no narrative bias, systematic rebalancing",
        "risk_tolerance": "medium — portfolio-level risk management, not stock-level",
        "short_criteria": "negative momentum, deteriorating quality factors, crowding",
        "key_metrics": "momentum score, quality score, valuation rank, short interest change",
        "personality_prompt": (
            "You are a quantitative systematic fund manager. You look for statistically "
            "significant signals across momentum, value, quality, and sentiment factors. "
            "You have no narrative bias — data is data. You are acutely aware of crowding "
            "risk (too many quants in the same trade). You monitor factor exposures carefully "
            "and rebalance systematically. Short interest trends and institutional flows are "
            "key inputs to your decision."
        ),
    },
}

DEFAULT_PERSONALITY = "aggressive"


# ─────────────────────────────────────────────────────────
# SYSTEM PROMPT — THE ANALYST PERSONA
# ─────────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """You are a senior equity research analyst at a premier hedge fund.

YOUR FUND'S INVESTMENT PERSONALITY:
{personality_prompt}

FUND STYLE: {style}
TIME HORIZON: {time_horizon}
FOCUS: {focus}
RISK TOLERANCE: {risk_tolerance}
KEY METRICS: {key_metrics}

HARD RULES — NO EXCEPTIONS:
1. Every factual claim must cite its data source: [SEC], [MARKET], [TRENDS], [REDDIT], [WEB]
2. Never fabricate numbers. If data is missing, say "not available in current data."
3. The Confidence Score must reflect the WEIGHT OF EVIDENCE, not optimism bias.
4. Be brutally honest about the Bear Case — burying risks costs real money.
5. Signals to Monitor must be SPECIFIC — not generic. Name the exact metric, release date, or event.
6. This is analytical research, NOT investment advice. The PM makes the final call.
7. Write like a hedge fund analyst, not a journalist. Dense, precise, no filler.
"""

RESEARCH_PROMPT_TEMPLATE = """
Analyze the following multi-source data package for {company} ({ticker}) and produce
a structured research brief.

════════════════════════════════════════
MARKET DATA:
{market_summary}

SEC FILING DATA:
{sec_summary}

GOOGLE TRENDS:
{trends_summary}

REDDIT SENTIMENT:
{reddit_summary}

WEB INTELLIGENCE:
{web_summary}
════════════════════════════════════════

Produce EXACTLY the following 6 sections. Do not add extra sections.
Use the exact section headers shown.

## SIGNAL SUMMARY
Synthesize what all data sources collectively show. What is the dominant signal?
Where do sources agree vs contradict? Cite each source used.
Minimum 4 sentences. Maximum 8 sentences.

## BULL CASE
List exactly 3 reasons to be long. Each must:
- Start with a bold header (the thesis in 5-8 words)
- Include specific data backing from at least one source
- Quantify where possible (%, $, bps)
Format as numbered list.

## BEAR CASE
List exactly 3 risks to the bull thesis. Each must:
- Start with a bold header (the risk in 5-8 words)
- Include specific data or evidence
- State the downside magnitude if the risk materializes
Format as numbered list.

## KEY RISKS
Name 3-5 SPECIFIC events or data releases that would BREAK the thesis entirely.
These are binary risks — if they happen, you exit the position.
Format as bullet points with trigger condition and expected market reaction.

## CONFIDENCE SCORE
State: XX% [BULL/BEAR/NEUTRAL]
Then 2-3 sentences explaining:
- What drives the score up or down
- What data point would change your conviction most
- Time horizon for the thesis to play out

## SIGNALS TO MONITOR WEEKLY
List exactly 3 specific, actionable things to track:
- Name the exact metric, data source, or event
- State the frequency (weekly, monthly, on earnings, etc.)
- State what would be bullish vs bearish for each signal
"""


# ─────────────────────────────────────────────────────────
# DATA SUMMARIZERS
# Condense each source to prevent context overflow
# ─────────────────────────────────────────────────────────

def _summarize_market(md: dict) -> str:
    if "error" in md:
        return f"Market data unavailable: {md['error']}"

    price = md.get("price", {})
    fund = md.get("fundamentals", {})
    analyst = md.get("analyst", {})

    lines = [
        f"Price: ${price.get('current', 'N/A')} | "
        f"52w range: ${price.get('52w_low')}–${price.get('52w_high')} | "
        f"From 52w high: {price.get('pct_from_52w_high')}%",

        f"Returns: 1m={price.get('return_1m_pct')}% | "
        f"3m={price.get('return_3m_pct')}% | "
        f"1y={price.get('return_1y_pct')}%",

        f"Mkt Cap: ${fund.get('market_cap', 'N/A'):,}" if fund.get('market_cap')
        else "Mkt Cap: N/A",

        f"Valuation: P/E fwd={fund.get('pe_forward')} | "
        f"EV/EBITDA={fund.get('ev_ebitda')} | "
        f"P/S={fund.get('ps_ratio')} | "
        f"PEG={fund.get('peg_ratio')}",

        f"Margins: Gross={_pct(fund.get('gross_margin'))} | "
        f"Operating={_pct(fund.get('operating_margin'))} | "
        f"Net={_pct(fund.get('net_margin'))}",

        f"Growth: Revenue YoY={_pct(fund.get('revenue_growth_yoy'))} | "
        f"Earnings YoY={_pct(fund.get('earnings_growth_yoy'))}",

        f"Capital: Cash=${fund.get('total_cash', 'N/A')} | "
        f"Debt=${fund.get('total_debt', 'N/A')} | "
        f"FCF=${fund.get('free_cash_flow', 'N/A')}",

        f"Short Interest: {_pct(fund.get('short_pct_of_float'))} of float | "
        f"Short ratio: {fund.get('short_ratio')} days",

        f"Ownership: Inst={_pct(fund.get('institutional_pct'))} | "
        f"Insider={_pct(fund.get('insider_pct'))}",

        f"Analyst Consensus: {analyst.get('recommendation', 'N/A')} | "
        f"Target: ${analyst.get('target_mean')} (n={analyst.get('analyst_count')})",

        f"Next Earnings: {md.get('next_earnings_date', 'Not disclosed')}",
        f"Sector: {md.get('sector')} | Industry: {md.get('industry')}",
    ]
    return "\n".join(lines)


def _summarize_sec(sec: dict) -> str:
    if "error" in sec:
        return f"SEC data unavailable: {sec['error']}"

    filings = sec.get("filings", {})
    lines = [f"Company: {sec.get('company')} | CIK: {sec.get('cik')}"]

    if filings.get("10K"):
        lines.append(f"Latest 10-K filed: {filings['10K'].get('date')}")
    if filings.get("10Q"):
        lines.append(f"Latest 10-Q filed: {filings['10Q'].get('date')}")

    recent_8k = filings.get("8K_recent", [])
    if recent_8k:
        lines.append(f"Recent 8-K events ({len(recent_8k)} total):")
        for filing in recent_8k[:3]:
            lines.append(f"  - {filing.get('date')}: {filing.get('primary_doc', 'material event')}")

    return "\n".join(lines)


def _summarize_trends(gt: dict) -> str:
    if "error" in gt:
        return f"Google Trends unavailable: {gt['error']}"

    direction = gt.get("trend_direction_90d", "unknown")
    interest_90d = gt.get("interest_90d", [])

    recent_val = interest_90d[-1]["value"] if interest_90d else None
    old_val = interest_90d[0]["value"] if interest_90d else None

    return (
        f"90-day trend direction: {direction.upper()}\n"
        f"Interest range: {old_val} → {recent_val} (scale 0-100)\n"
        f"Signal: {gt.get('signal_interpretation', '')}"
    )


def _summarize_reddit(rd: dict) -> str:
    if "error" in rd:
        return f"Reddit data unavailable: {rd['error']}"

    ss = rd.get("sentiment_summary", {})
    top_posts = rd.get("top_posts", [])[:3]

    lines = [
        f"Overall sentiment: {ss.get('overall', 'N/A').upper()} "
        f"(Bull {ss.get('bull_pct')}% / Bear {ss.get('bear_pct')}%)",
        f"Posts scanned: {rd.get('post_count', 0)} across 4 subreddits",
    ]

    if top_posts:
        lines.append("Top posts by engagement:")
        for post in top_posts:
            lines.append(
                f"  [{post.get('subreddit')}] \"{post.get('title')[:80]}\" "
                f"| score={post.get('score')} | sentiment={post.get('sentiment')}"
            )

    lines.append(rd.get("signal_interpretation", ""))
    return "\n".join(lines)


def _summarize_web(web: dict) -> str:
    if "error" in web:
        return f"Web intelligence unavailable: {web['error']}"

    intel = web.get("intelligence", {})

    if "raw" in intel:
        return f"Web Intelligence:\n{intel['raw'][:1500]}"

    lines = []

    news = intel.get("recent_news", [])
    if news:
        lines.append("Recent News:")
        for item in news[:4]:
            lines.append(f"  [{item.get('date', 'N/A')}] {item.get('headline', '')} "
                         f"— Impact: {item.get('impact', 'N/A')}")

    analyst = intel.get("analyst_activity", [])
    if analyst:
        lines.append("Analyst Activity:")
        for item in analyst[:3]:
            lines.append(f"  [{item.get('date', 'N/A')}] {item.get('firm', 'N/A')}: "
                         f"{item.get('action', 'N/A')} | Target: "
                         f"{item.get('old_target', 'N/A')} → {item.get('new_target', 'N/A')}")

    macro = intel.get("macro_context", {})
    if macro:
        tailwinds = macro.get("tailwinds", [])
        headwinds = macro.get("headwinds", [])
        if tailwinds:
            lines.append(f"Macro Tailwinds: {'; '.join(tailwinds[:3])}")
        if headwinds:
            lines.append(f"Macro Headwinds: {'; '.join(headwinds[:3])}")

    comp = intel.get("competitive_dynamics", {})
    if comp and comp.get("summary"):
        lines.append(f"Competitive: {comp['summary']}")

    return "\n".join(lines) if lines else "Web intelligence: no structured data extracted"


def _pct(val) -> str:
    if val is None:
        return "N/A"
    return f"{val * 100:.1f}%"


# ─────────────────────────────────────────────────────────
# CORE BRAIN FUNCTION
# ─────────────────────────────────────────────────────────

def generate_brief(
    data_package: dict[str, Any],
    personality: str = DEFAULT_PERSONALITY,
) -> dict[str, Any]:
    """
    Core brain: takes a fetch_all() data package and produces a structured
    6-section research brief.

    AI provider priority:
      1. Anthropic Claude Opus (if ANTHROPIC_API_KEY set)
      2. Groq LLaMA fallback (if GROQ_API_KEY set) — free tier, slightly lower quality
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    groq_model = os.getenv("MODEL", "llama-3.3-70b-versatile")

    if not OPEN_ROUTER_API_KEY and not ANTHROPIC_API_KEY and not groq_api_key:
        raise RuntimeError(
            "No AI provider configured. Set OPEN_ROUTER_API_KEY (primary), "
            "ANTHROPIC_API_KEY, or GROQ_API_KEY in backend/.env"
        )

    profile = FUND_PERSONALITIES.get(personality, FUND_PERSONALITIES[DEFAULT_PERSONALITY])

    ticker = data_package.get("ticker", "UNKNOWN")
    company = data_package.get("company", "Unknown Company")

    # Build data summaries
    market_summary = _summarize_market(data_package.get("market_data", {"error": "not fetched"}))
    sec_summary = _summarize_sec(data_package.get("sec_edgar", {"error": "not fetched"}))
    trends_summary = _summarize_trends(data_package.get("google_trends", {"error": "not fetched"}))
    reddit_summary = _summarize_reddit(data_package.get("reddit", {"error": "not fetched"}))
    web_summary = _summarize_web(data_package.get("web_intelligence", {"error": "not fetched"}))

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(**profile)
    research_prompt = RESEARCH_PROMPT_TEMPLATE.format(
        company=company,
        ticker=ticker,
        market_summary=market_summary,
        sec_summary=sec_summary,
        trends_summary=trends_summary,
        reddit_summary=reddit_summary,
        web_summary=web_summary,
    )

    from openai import OpenAI

    # ── Priority 1: OpenRouter (primary) ─────────────────
    if OPEN_ROUTER_API_KEY:
        client = OpenAI(
            api_key=OPEN_ROUTER_API_KEY,
            base_url=OPEN_ROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": "https://hedgeos.ai",
                "X-Title": "HedgeOS Research",
            },
        )
        model_used = OPEN_ROUTER_MODEL
        print(f"[Brain] OpenRouter ({model_used}) → {ticker} ({profile['name']})")

        response = client.chat.completions.create(
            model=model_used,
            max_tokens=1500,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": research_prompt},
            ],
        )
        brief_text = response.choices[0].message.content
        input_tok = response.usage.prompt_tokens
        output_tok = response.usage.completion_tokens
        cost = 0.0  # varies by model on OpenRouter
        print(f"[Brain] Done — {input_tok}in/{output_tok}out")

    # ── Priority 2: Anthropic direct ─────────────────────
    elif ANTHROPIC_API_KEY:
        import anthropic
        ac = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        model_used = "claude-opus-4-6"
        print(f"[Brain] Anthropic ({model_used}) → {ticker} ({profile['name']})")

        message = ac.messages.create(
            model=model_used,
            max_tokens=3000,
            system=system_prompt,
            messages=[{"role": "user", "content": research_prompt}],
        )
        brief_text = message.content[0].text
        input_tok = message.usage.input_tokens
        output_tok = message.usage.output_tokens
        cost = (input_tok * 15.0 + output_tok * 75.0) / 1_000_000
        print(f"[Brain] Done — {input_tok}in/{output_tok}out ${cost:.4f}")

    # ── Priority 3: Groq free fallback ───────────────────
    else:
        client = OpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        model_used = groq_model
        print(f"[Brain] Groq ({model_used}) → {ticker} ({profile['name']})")

        response = client.chat.completions.create(
            model=model_used,
            max_tokens=int(os.getenv("MAX_TOKENS", 4096)),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": research_prompt},
            ],
        )
        brief_text = response.choices[0].message.content
        input_tok = response.usage.prompt_tokens
        output_tok = response.usage.completion_tokens
        cost = 0.0
        print(f"[Brain] Done — {input_tok}in/{output_tok}out (Groq free)")

    return {
        "ticker": ticker,
        "company": company,
        "personality": profile["name"],
        "personality_key": personality,
        "brief": brief_text,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "claude-opus-4-6",
        "usage": {
            "input_tokens": input_tok,
            "output_tokens": output_tok,
            "estimated_cost_usd": round(cost, 4),
        },
    }


# ─────────────────────────────────────────────────────────
# CLI RUNNER
# ─────────────────────────────────────────────────────────

async def _run(ticker: str, company: str, personality: str):
    from data_fetcher import fetch_all  # noqa: PLC0415

    data = await fetch_all(ticker, company)

    result = generate_brief(data, personality)

    out_file = f"brief_{ticker}_{personality}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_file, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"RESEARCH BRIEF: {company} ({ticker})")
    print(f"Fund Personality: {result['personality']}")
    print(f"Generated: {result['generated_at']}")
    print(f"Cost: ${result['usage']['estimated_cost_usd']}")
    print(f"{'=' * 60}\n")
    print(result["brief"])
    print(f"\nFull report saved → {out_file}")


if __name__ == "__main__":
    ticker_arg = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
    company_arg = sys.argv[2] if len(sys.argv) > 2 else "Nvidia"
    personality_arg = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_PERSONALITY

    if personality_arg not in FUND_PERSONALITIES:
        print(f"Invalid personality '{personality_arg}'. "
              f"Choose from: {list(FUND_PERSONALITIES.keys())}")
        sys.exit(1)

    asyncio.run(_run(ticker_arg, company_arg, personality_arg))
