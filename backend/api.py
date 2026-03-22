"""
Phase 4 — Flask API
REST API wrapper for the multi-agent research system.
Exposes the crew_main pipeline over HTTP on port 5000.

Endpoints:
  GET  /api/health          — health check
  POST /api/research        — run multi-agent research for a ticker
  GET  /api/research/{ticker} — same as POST, uses defaults
  GET  /api/profiles        — list all fund profiles
  POST /api/profiles        — create/update a fund profile
  GET  /api/profiles/{fund_id} — get a specific profile
  POST /api/profiles/{fund_id}/feedback — submit feedback
  GET  /api/edges/{fund_id}  — get edge hypotheses for a fund
  POST /api/edges/generate   — generate new edge hypotheses
  GET  /api/demo/{ticker}    — return cached demo brief instantly (no API call)
"""

import json
import os
import sys
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Path for demo cache
DEMO_CACHE_DIR = os.path.join(os.path.dirname(__file__), "data", "demo_cache")


# ─────────────────────────────────────────────────────────
# HEALTH
# ─────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "version": "1.0.0", "timestamp": datetime.now(timezone.utc).isoformat()})


# ─────────────────────────────────────────────────────────
# RESEARCH
# ─────────────────────────────────────────────────────────

@app.post("/api/research")
def run_research():
    """
    Run multi-agent research for a ticker.
    Body: {"ticker": "NVDA", "company": "Nvidia", "personality": "aggressive", "fund_id": "default"}
    """
    data = request.get_json() or {}
    ticker = data.get("ticker", "NVDA").upper()
    company = data.get("company", ticker)
    personality = data.get("personality", "aggressive")
    fund_id = data.get("fund_id", "default")

    try:
        from crew_main import run_crew
        result = run_crew(ticker, company, personality)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/research/<ticker>")
def get_research(ticker: str):
    """GET convenience — runs research with default settings."""
    try:
        from crew_main import run_crew
        result = run_crew(ticker.upper(), ticker.upper(), "aggressive")
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────
# DEMO MODE (instant, no API calls)
# ─────────────────────────────────────────────────────────

@app.get("/api/demo/<ticker>")
def get_demo(ticker: str):
    """Return a cached demo brief instantly without any AI API calls."""
    os.makedirs(DEMO_CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(DEMO_CACHE_DIR, f"{ticker.upper()}.json")

    if os.path.exists(cache_file):
        with open(cache_file) as f:
            data = json.load(f)
        data["demo_mode"] = True
        return jsonify(data)

    # No cache — return a realistic placeholder
    return jsonify({
        "ticker": ticker.upper(),
        "demo_mode": True,
        "brief": _demo_brief(ticker.upper()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "demo_cache",
    })


@app.post("/api/demo/cache")
def cache_demo():
    """Save a research result as the demo cache for a ticker."""
    data = request.get_json() or {}
    ticker = data.get("ticker", "").upper()
    if not ticker:
        return jsonify({"error": "ticker required"}), 400

    os.makedirs(DEMO_CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(DEMO_CACHE_DIR, f"{ticker}.json")
    with open(cache_file, "w") as f:
        json.dump(data, f, indent=2)

    return jsonify({"status": "cached", "ticker": ticker})


# ─────────────────────────────────────────────────────────
# PROFILES
# ─────────────────────────────────────────────────────────

@app.get("/api/profiles")
def list_profiles():
    from app.personality.profile_manager import list_profiles as _list
    return jsonify(_list())


@app.post("/api/profiles")
def create_or_update_profile():
    data = request.get_json() or {}
    fund_id = data.get("fund_id")
    fund_name = data.get("fund_name", fund_id)
    if not fund_id:
        return jsonify({"error": "fund_id required"}), 400

    from app.personality.profile_manager import create_profile, load_profile, save_profile
    import os as _os
    profile_path = _os.path.join(
        _os.path.dirname(__file__), "data", "profiles", f"{fund_id}.json"
    )

    if _os.path.exists(profile_path):
        profile = load_profile(fund_id)
        from app.personality.profile_manager import _deep_merge
        _deep_merge(profile, data)
        updated = save_profile(profile)
        return jsonify(updated)
    else:
        created = create_profile(fund_id, fund_name, overrides=data)
        return jsonify(created), 201


@app.get("/api/profiles/<fund_id>")
def get_profile(fund_id: str):
    from app.personality.profile_manager import load_profile
    return jsonify(load_profile(fund_id))


@app.post("/api/profiles/<fund_id>/feedback")
def submit_feedback(fund_id: str):
    data = request.get_json() or {}
    from app.personality.profile_manager import add_feedback
    result = add_feedback(
        fund_id=fund_id,
        ticker=data.get("ticker", ""),
        rating=int(data.get("rating", 3)),
        comment=data.get("comment", ""),
        brief_id=data.get("brief_id", ""),
    )
    return jsonify({"status": "ok", "profile_version": result.get("version")})


# ─────────────────────────────────────────────────────────
# EDGE HYPOTHESES
# ─────────────────────────────────────────────────────────

@app.get("/api/edges/<fund_id>")
def get_edges(fund_id: str):
    from app.edges.edge_library import load_fund_edges, get_edge_summary
    return jsonify({
        "edges": load_fund_edges(fund_id),
        "summary": get_edge_summary(fund_id),
    })


@app.post("/api/edges/generate")
def generate_edges():
    data = request.get_json() or {}
    ticker = data.get("ticker", "NVDA").upper()
    company = data.get("company", ticker)
    fund_id = data.get("fund_id", "default")

    try:
        from app.edges.hypothesis_engine import generate_hypotheses
        hypotheses = generate_hypotheses(ticker, company, fund_id)
        return jsonify({"ticker": ticker, "hypotheses": hypotheses})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.patch("/api/edges/<fund_id>/<edge_id>")
def update_edge(fund_id: str, edge_id: str):
    data = request.get_json() or {}
    from app.edges.edge_library import update_edge_status
    updated = update_edge_status(fund_id, edge_id, data.get("status", "hypothesis"), data.get("note", ""))
    if updated:
        return jsonify(updated)
    return jsonify({"error": "edge not found"}), 404


@app.get("/api/edges/patterns")
def get_patterns():
    from app.edges.edge_library import get_pattern_library
    return jsonify(get_pattern_library())


# ─────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────

def _demo_brief(ticker: str) -> str:
    return f"""## SIGNAL SUMMARY
{ticker} shows a mixed signal environment. Market data indicates the stock is trading 12% below its 52-week high with moderate short interest at 4.2% of float [MARKET]. Recent Google Trends show a rising 90-day trend for the company name, suggesting growing consumer awareness [TRENDS]. Reddit sentiment is broadly bullish (62% bull across 47 posts scanned) though primarily concentrated in wallstreetbets, which carries contrarian risk at extremes [REDDIT]. The most recent 8-K (filed 3 weeks ago) disclosed no material adverse events [SEC]. Web intelligence indicates 2 analyst upgrades in the past month [WEB].

## BULL CASE
1. **Revenue acceleration into new product cycle** — Q3 results showed 18% YoY revenue growth, accelerating from 12% in Q2, driven by the new product category which represents $2.1B in incremental TAM [MARKET]. Forward P/E of 22x is below the 5-year average of 26x, suggesting the market hasn't priced in the acceleration [MARKET].

2. **Margin expansion runway intact** — Gross margin expanded 180bps YoY to 43.2%. Operating leverage is kicking in as R&D as % of revenue declined from 19% to 16% [SEC]. Consensus models only have 50bps of further expansion built in, which appears conservative given the shift to higher-margin software revenue [WEB].

3. **Institutional conviction building** — Institutional ownership increased from 71% to 76% over the last two quarters [MARKET]. This trend coincides with 3 major fund initiations (Goldman, Coatue, Dragoneer) suggesting smart money accumulation phase is ongoing [WEB].

## BEAR CASE
1. **Competitive displacement risk accelerating** — Primary competitor launched a directly competing product at 30% lower price point last month [WEB]. Historical price wars in this category have compressed gross margins by 400-600bps within 4-6 quarters [SEC, Item 1A]. {ticker}'s current gross margin provides limited buffer against this dynamic.

2. **Customer concentration risk underappreciated** — Top 3 customers represent 41% of revenue [SEC, Item 1]. Any loss of a major contract would create a revenue step-down of 8-15%. The largest customer is reportedly evaluating alternatives per channel checks [WEB, UNVERIFIED].

3. **Valuation not as cheap as it appears** — EV/EBITDA of 18x looks reasonable vs 22x peers, but adjusting for $800M in capitalized development costs that should arguably be expensed, the adjusted multiple is closer to 24x [SEC, Item 8]. FCF conversion is also tracking below net income at 72%, which limits the buyback firepower management has promised [MARKET].

## KEY RISKS
• **Earnings miss >5% vs consensus** → Expected stock reaction -15% to -20% → Exit position / reassess thesis
• **Customer announces vendor diversification** (8-K event) → -10% to -25% depending on customer size → Reduce position 50%
• **Gross margin guidance cut below 40%** at next earnings → Multiple compression event → Exit immediately
• **Competitor pricing war escalates** (press release or earnings commentary) → Sector de-rating of 2-4x turns on EV/EBITDA → Hedge with sector ETF puts

## CONFIDENCE SCORE
63% BULL

The weight of evidence favors the long thesis, but not overwhelmingly. The bull case rests on continued revenue acceleration and margin expansion — both of which require execution in a more competitive environment than 6 months ago. A single earnings miss would shift this to 40% bull or lower. The thesis plays out over 6-9 months; the key catalyst is the next earnings call demonstrating the competitive response isn't materially impacting growth rates.

## SIGNALS TO MONITOR WEEKLY
1. **Google Trends for "{ticker}" and product name** — Track weekly. Rising >15% vs 4-week average heading into earnings = bull signal. Flat or declining in Month 2 of quarter = demand softness early warning [TRENDS source: trends.google.com, free].

2. **LinkedIn job postings in Sales & Engineering** — Track monthly. >10% MoM growth in sales headcount = expansion confidence. Freeze or cuts in product roles = strategic pivot risk. Benchmark: current posting count on LinkedIn filtered to {ticker} company page [DIGITAL source: LinkedIn, free].

3. **Short interest % of float** — Track bi-weekly (when FINRA releases data). Current: 4.2%. If short interest rises above 7% = crowding concern / potential thesis reversal. If it declines below 2% = short squeeze exhaustion of upside catalyst [MARKET source: FINRA short sale data, free]."""


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    print(f"[HedgeOS API] Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
