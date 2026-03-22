"""
Phase 2 — Data Pipeline
HedgeOS multi-source data fetcher.

Five parallel data sources:
  1. SEC EDGAR    — 10-K, 10-Q, 8-K filings
  2. yfinance     — market data, fundamentals, options flow
  3. Google Trends — consumer interest (leading indicator)
  4. Reddit       — retail sentiment (praw: wallstreetbets, investing, stocks)
  5. Claude AI    — web intelligence via Anthropic web_search tool

Entry point:
  asyncio.run(fetch_all("NVDA", "Nvidia"))

Each function is independently runnable and returns a typed dict.
"""

import asyncio
import json
import os
import re
import textwrap
from datetime import datetime, timezone
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "hedgeos_research_v1")
SEC_USER_AGENT = os.getenv("SEC_USER_AGENT", "HedgeOS research@hedgeos.ai")

# ─────────────────────────────────────────────────────────
# SOURCE 1 — SEC EDGAR
# ─────────────────────────────────────────────────────────

EDGAR_BASE = "https://data.sec.gov"
SEC_HEADERS = {"User-Agent": SEC_USER_AGENT}


async def _edgar_get(url: str) -> dict:
    async with httpx.AsyncClient(timeout=20.0) as c:
        r = await c.get(url, headers=SEC_HEADERS)
        r.raise_for_status()
        return r.json()


async def fetch_sec_data(ticker: str) -> dict[str, Any]:
    """
    Fetch recent SEC filings for a ticker:
    - Latest 10-K (annual report)
    - Latest 10-Q (quarterly report)
    - Last 5 8-K (material events)

    Returns structured dict with filing metadata and key dates.
    As a hedge fund analyst, 8-Ks are gold — they surface material events
    before the market fully prices them in.
    """
    company_map_url = "https://www.sec.gov/files/company_tickers.json"
    async with httpx.AsyncClient(timeout=15.0) as c:
        r = await c.get(company_map_url, headers=SEC_HEADERS)
        r.raise_for_status()
        tickers_data = r.json()

    cik = None
    company_name = None
    for entry in tickers_data.values():
        if entry["ticker"] == ticker.upper():
            cik = str(entry["cik_str"]).zfill(10)
            company_name = entry["title"]
            break

    if not cik:
        return {"error": f"Ticker '{ticker}' not found in SEC EDGAR", "source": "SEC_EDGAR"}

    subs_url = f"{EDGAR_BASE}/submissions/CIK{cik}.json"
    data = await _edgar_get(subs_url)
    filings = data["filings"]["recent"]

    forms = filings["form"]
    accessions = filings["accessionNumber"]
    dates = filings["filingDate"]
    descriptions = filings.get("primaryDocument", [""] * len(forms))

    result: dict[str, Any] = {
        "source": "SEC_EDGAR",
        "ticker": ticker.upper(),
        "company": company_name,
        "cik": cik,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "filings": {
            "10K": None,
            "10Q": None,
            "8K_recent": [],
        },
    }

    for i, form in enumerate(forms):
        form_clean = form.strip()
        if form_clean == "10-K" and result["filings"]["10K"] is None:
            result["filings"]["10K"] = {
                "accession": accessions[i],
                "date": dates[i],
                "url": (
                    f"https://www.sec.gov/Archives/edgar/data/{int(cik)}"
                    f"/{accessions[i].replace('-', '')}"
                ),
            }
        elif form_clean == "10-Q" and result["filings"]["10Q"] is None:
            result["filings"]["10Q"] = {
                "accession": accessions[i],
                "date": dates[i],
                "url": (
                    f"https://www.sec.gov/Archives/edgar/data/{int(cik)}"
                    f"/{accessions[i].replace('-', '')}"
                ),
            }
        elif form_clean == "8-K" and len(result["filings"]["8K_recent"]) < 5:
            result["filings"]["8K_recent"].append({
                "accession": accessions[i],
                "date": dates[i],
                "primary_doc": descriptions[i] if i < len(descriptions) else "",
            })

        if (
            result["filings"]["10K"]
            and result["filings"]["10Q"]
            and len(result["filings"]["8K_recent"]) >= 5
        ):
            break

    return result


# ─────────────────────────────────────────────────────────
# SOURCE 2 — YFINANCE (market data + fundamentals)
# ─────────────────────────────────────────────────────────

async def fetch_market_data(ticker: str) -> dict[str, Any]:
    """
    Fetch comprehensive market data via yfinance (runs in thread pool).

    Captured: price action, valuation multiples, margins, capital structure,
    analyst consensus, short interest, institutional/insider ownership.
    """
    def _sync_fetch():
        import yfinance as yf  # noqa: PLC0415
        t = yf.Ticker(ticker)
        info = t.info or {}

        hist = t.history(period="1y", auto_adjust=True)
        hist_3m = hist.tail(63)
        hist_1m = hist.tail(21)

        def pct_return(df):
            if df.empty or len(df) < 2:
                return None
            return round((df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100, 2)

        high_52w = float(hist["High"].max()) if not hist.empty else None
        low_52w = float(hist["Low"].min()) if not hist.empty else None
        current_price = float(hist["Close"].iloc[-1]) if not hist.empty else None
        avg_vol_20d = int(hist["Volume"].tail(20).mean()) if not hist.empty else None

        fundamentals = {
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
            "pe_trailing": info.get("trailingPE"),
            "pe_forward": info.get("forwardPE"),
            "ps_ratio": info.get("priceToSalesTrailing12Months"),
            "pb_ratio": info.get("priceToBook"),
            "ev_ebitda": info.get("enterpriseToEbitda"),
            "ev_revenue": info.get("enterpriseToRevenue"),
            "peg_ratio": info.get("pegRatio"),
            "revenue_ttm": info.get("totalRevenue"),
            "gross_margin": info.get("grossMargins"),
            "operating_margin": info.get("operatingMargins"),
            "net_margin": info.get("profitMargins"),
            "revenue_growth_yoy": info.get("revenueGrowth"),
            "earnings_growth_yoy": info.get("earningsGrowth"),
            "return_on_equity": info.get("returnOnEquity"),
            "return_on_assets": info.get("returnOnAssets"),
            "debt_to_equity": info.get("debtToEquity"),
            "total_cash": info.get("totalCash"),
            "total_debt": info.get("totalDebt"),
            "free_cash_flow": info.get("freeCashflow"),
            "beta": info.get("beta"),
            "dividend_yield": info.get("dividendYield"),
            "payout_ratio": info.get("payoutRatio"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "float_shares": info.get("floatShares"),
            "shares_short": info.get("sharesShort"),
            "short_ratio": info.get("shortRatio"),
            "short_pct_of_float": info.get("shortPercentOfFloat"),
            "institutional_pct": info.get("heldPercentInstitutions"),
            "insider_pct": info.get("heldPercentInsiders"),
        }

        analyst = {
            "target_mean": info.get("targetMeanPrice"),
            "target_high": info.get("targetHighPrice"),
            "target_low": info.get("targetLowPrice"),
            "analyst_count": info.get("numberOfAnalystOpinions"),
            "recommendation": info.get("recommendationKey"),
        }

        earnings_date = None
        try:
            cal = t.calendar
            if cal is not None and "Earnings Date" in cal:
                dates = cal["Earnings Date"]
                if hasattr(dates, "to_list"):
                    dates = dates.to_list()
                if dates:
                    earnings_date = str(dates[0])
        except Exception:
            pass

        return {
            "source": "YFINANCE",
            "ticker": ticker.upper(),
            "company": info.get("longName", ticker),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "price": {
                "current": current_price,
                "52w_high": high_52w,
                "52w_low": low_52w,
                "pct_from_52w_high": (
                    round((current_price / high_52w - 1) * 100, 2)
                    if current_price and high_52w
                    else None
                ),
                "return_1m_pct": pct_return(hist_1m),
                "return_3m_pct": pct_return(hist_3m),
                "return_1y_pct": pct_return(hist),
                "avg_volume_20d": avg_vol_20d,
                "currency": info.get("currency", "USD"),
            },
            "fundamentals": fundamentals,
            "analyst": analyst,
            "next_earnings_date": earnings_date,
            "exchange": info.get("exchange"),
            "description": info.get("longBusinessSummary", "")[:500],
        }

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_fetch)


# ─────────────────────────────────────────────────────────
# SOURCE 3 — GOOGLE TRENDS (consumer interest signal)
# ─────────────────────────────────────────────────────────

async def fetch_google_trends(company_name: str, ticker: str) -> dict[str, Any]:
    """
    Fetch Google Trends for company name and ticker symbol.

    Analyst insight: rising search interest 4-8 weeks before earnings
    is a leading indicator for consumer-facing companies. Flat/declining
    mid-cycle suggests demand softness.
    """
    def _sync_fetch():
        from pytrends.request import TrendReq  # noqa: PLC0415

        pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        kw_list = [company_name, ticker]

        pytrends.build_payload(kw_list, cat=0, timeframe="today 3-m", geo="US")
        df_90d = pytrends.interest_over_time()

        pytrends.build_payload(kw_list, cat=0, timeframe="today 12-m", geo="US")
        df_12m = pytrends.interest_over_time()

        def df_to_list(df, col):
            if df.empty or col not in df.columns:
                return []
            return [
                {"date": str(idx.date()), "value": int(val)}
                for idx, val in df[col].items()
            ]

        def trend_direction(df, col):
            if df.empty or col not in df.columns or len(df) < 4:
                return "insufficient_data"
            recent = df[col].iloc[-2:].mean()
            prior = df[col].iloc[-4:-2].mean()
            if recent > prior * 1.10:
                return "rising"
            elif recent < prior * 0.90:
                return "falling"
            return "flat"

        primary_kw = company_name
        return {
            "source": "GOOGLE_TRENDS",
            "ticker": ticker.upper(),
            "company": company_name,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "keywords_searched": kw_list,
            "trend_direction_90d": trend_direction(df_90d, primary_kw),
            "interest_90d": df_to_list(df_90d, primary_kw),
            "interest_12m": df_to_list(df_12m, primary_kw),
            "ticker_interest_90d": df_to_list(df_90d, ticker),
            "signal_interpretation": (
                "Rising search interest is a potential leading indicator for "
                "consumer-facing businesses. Compare vs prior earnings cycles."
            ),
        }

    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _sync_fetch)
    except Exception as e:
        return {
            "source": "GOOGLE_TRENDS",
            "ticker": ticker.upper(),
            "error": str(e),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }


# ─────────────────────────────────────────────────────────
# SOURCE 4 — REDDIT SENTIMENT (retail pulse)
# ─────────────────────────────────────────────────────────

REDDIT_SUBREDDITS = ["wallstreetbets", "investing", "stocks", "SecurityAnalysis"]

_SENTIMENT_KEYWORDS = {
    "bullish": ["bull", "long", "buy", "calls", "moon", "squeeze", "undervalued", "cheap"],
    "bearish": ["bear", "short", "puts", "dump", "overvalued", "bubble", "fraud", "sell"],
}


def _score_sentiment(text: str) -> str:
    text_lower = text.lower()
    bull_score = sum(1 for w in _SENTIMENT_KEYWORDS["bullish"] if w in text_lower)
    bear_score = sum(1 for w in _SENTIMENT_KEYWORDS["bearish"] if w in text_lower)
    if bull_score > bear_score:
        return "bullish"
    elif bear_score > bull_score:
        return "bearish"
    return "neutral"


async def fetch_reddit_sentiment(ticker: str, company_name: str) -> dict[str, Any]:
    """
    Scan recent Reddit posts mentioning the ticker across 4 subreddits.

    Analyst note: WSB sentiment is a contrarian indicator at extremes.
    SecurityAnalysis carries higher signal quality. Track post volume
    week-over-week as a crowding risk indicator.
    """
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        return {
            "source": "REDDIT",
            "ticker": ticker.upper(),
            "error": "Reddit credentials not configured (REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET)",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    def _sync_fetch():
        import praw  # noqa: PLC0415

        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )

        posts: list[dict] = []
        sentiment_counts = {"bullish": 0, "bearish": 0, "neutral": 0}

        for sub_name in REDDIT_SUBREDDITS:
            sub = reddit.subreddit(sub_name)
            for term in [f"${ticker}", ticker]:
                try:
                    for post in sub.search(term, sort="new", time_filter="week", limit=15):
                        combined_text = f"{post.title} {post.selftext}"
                        sentiment = _score_sentiment(combined_text)
                        sentiment_counts[sentiment] += 1
                        posts.append({
                            "subreddit": sub_name,
                            "title": post.title[:150],
                            "score": post.score,
                            "num_comments": post.num_comments,
                            "created_utc": datetime.fromtimestamp(
                                post.created_utc, tz=timezone.utc
                            ).isoformat(),
                            "sentiment": sentiment,
                            "url": f"https://reddit.com{post.permalink}",
                        })
                except Exception:
                    continue

        posts.sort(key=lambda x: x["score"] + x["num_comments"] * 2, reverse=True)

        total = sum(sentiment_counts.values())
        overall = "neutral"
        if total > 0:
            bull_pct = sentiment_counts["bullish"] / total
            bear_pct = sentiment_counts["bearish"] / total
            if bull_pct > 0.55:
                overall = "bullish"
            elif bear_pct > 0.55:
                overall = "bearish"

        return {
            "source": "REDDIT",
            "ticker": ticker.upper(),
            "company": company_name,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "post_count": len(posts),
            "sentiment_summary": {
                "overall": overall,
                "bullish_count": sentiment_counts["bullish"],
                "bearish_count": sentiment_counts["bearish"],
                "neutral_count": sentiment_counts["neutral"],
                "bull_pct": round(sentiment_counts["bullish"] / total * 100, 1) if total else 0,
                "bear_pct": round(sentiment_counts["bearish"] / total * 100, 1) if total else 0,
            },
            "top_posts": posts[:10],
            "signal_interpretation": (
                "Extreme Reddit bullishness (>70% bull) in WSB is historically contrarian. "
                "SecurityAnalysis posts carry higher signal quality."
            ),
        }

    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _sync_fetch)
    except Exception as e:
        return {
            "source": "REDDIT",
            "ticker": ticker.upper(),
            "error": str(e),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }


# ─────────────────────────────────────────────────────────
# SOURCE 5 — CLAUDE WEB INTELLIGENCE
# ─────────────────────────────────────────────────────────

_WEB_INTEL_PROMPT = textwrap.dedent("""
You are a senior research analyst at a $5B long/short equity hedge fund.
Search the web and gather current intelligence on {company} ({ticker}).

Collect and structure the following:

1. RECENT NEWS (last 30 days): Material events — earnings beats/misses, guidance changes,
   M&A, regulatory actions, management changes, product launches.

2. ANALYST ACTIVITY: Recent upgrades/downgrades, price target changes, initiations.
   Note direction and firm name.

3. MACRO TAILWINDS / HEADWINDS: Current macro factors most relevant to this company's sector.
   Be specific — tariffs, interest rates, commodity prices, FX moves.

4. SUPPLY CHAIN SIGNALS: Upstream/downstream signals — supplier results, shipping data,
   channel checks, distributor inventory levels.

5. MANAGEMENT CREDIBILITY: Recent management commentary, conference appearances,
   or insider activity (buys/sells) in the past 60 days.

6. COMPETITIVE LANDSCAPE: Competitive dynamics that have shifted — new entrants,
   pricing pressure, market share data.

Format as structured JSON with these exact keys:
{{
  "recent_news": [list of {{date, headline, impact}}],
  "analyst_activity": [list of {{date, firm, action, old_target, new_target}}],
  "macro_context": {{tailwinds: [], headwinds: []}},
  "supply_chain": {{signals: [], confidence: "high/medium/low"}},
  "management_signals": [list of {{date, type, detail}}],
  "competitive_dynamics": {{summary: str, risks: []}}
}}

Be factual. Only include verifiable recent information. Mark uncertain items [UNVERIFIED].
""")


async def fetch_web_intelligence(ticker: str, company_name: str) -> dict[str, Any]:
    """
    Use Claude Opus with web_search tool to gather current market intelligence.
    This catches recent news, analyst moves, and macro signals not yet in filings.
    """
    if not ANTHROPIC_API_KEY:
        return {
            "source": "CLAUDE_WEB",
            "ticker": ticker.upper(),
            "error": "ANTHROPIC_API_KEY not configured",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    import anthropic  # noqa: PLC0415

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = _WEB_INTEL_PROMPT.format(company=company_name, ticker=ticker)

    def _sync_call():
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}],
        )

        text_parts = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)

        raw_text = "\n".join(text_parts)

        parsed = None
        json_match = re.search(r"\{[\s\S]*\}", raw_text)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
            except json.JSONDecodeError:
                parsed = None

        return {
            "source": "CLAUDE_WEB",
            "ticker": ticker.upper(),
            "company": company_name,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "intelligence": parsed or {"raw": raw_text},
            "model": "claude-opus-4-6",
        }

    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _sync_call)
    except Exception as e:
        return {
            "source": "CLAUDE_WEB",
            "ticker": ticker.upper(),
            "error": str(e),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }


# ─────────────────────────────────────────────────────────
# MASTER FETCHER — all 5 sources in parallel
# ─────────────────────────────────────────────────────────

async def fetch_all(ticker: str, company_name: str) -> dict[str, Any]:
    """
    Run all five data sources concurrently via asyncio.gather.
    Returns a unified research data package.

    Usage:
        data = asyncio.run(fetch_all("NVDA", "Nvidia"))
    """
    ticker = ticker.upper()
    print(f"[HedgeOS] Fetching data for {ticker} ({company_name}) from 5 sources...")

    results = await asyncio.gather(
        fetch_sec_data(ticker),
        fetch_market_data(ticker),
        fetch_google_trends(company_name, ticker),
        fetch_reddit_sentiment(ticker, company_name),
        fetch_web_intelligence(ticker, company_name),
        return_exceptions=True,
    )

    sources = ["sec_edgar", "market_data", "google_trends", "reddit", "web_intelligence"]
    package: dict[str, Any] = {
        "ticker": ticker,
        "company": company_name,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

    for key, result in zip(sources, results):
        if isinstance(result, Exception):
            package[key] = {"source": key.upper(), "error": str(result)}
            print(f"  [!] {key}: FAILED — {result}")
        else:
            package[key] = result
            status = "ERROR" if "error" in result else "OK"
            print(f"  [+] {key}: {status}")

    print(f"[HedgeOS] Data fetch complete for {ticker}")
    return package


# ─────────────────────────────────────────────────────────
# CLI TEST
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    ticker_arg = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
    company_arg = sys.argv[2] if len(sys.argv) > 2 else "Nvidia"

    data = asyncio.run(fetch_all(ticker_arg, company_arg))

    out_file = f"data_{ticker_arg}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_file, "w") as f:
        json.dump(data, f, indent=2, default=str)

    print(f"\nData saved → {out_file}")

    print("\n── SUMMARY ──")
    md = data.get("market_data", {})
    if "price" in md:
        p = md["price"]
        f_data = md.get("fundamentals", {})
        print(f"Price:      ${p.get('current', 'N/A')}")
        print(f"52w range:  ${p.get('52w_low')} – ${p.get('52w_high')}")
        print(f"1m return:  {p.get('return_1m_pct')}%")
        print(f"3m return:  {p.get('return_3m_pct')}%")
        mkt_cap = f_data.get("market_cap")
        print(f"Mkt cap:    ${mkt_cap:,.0f}" if mkt_cap else "Mkt cap:    N/A")
        print(f"P/E fwd:    {f_data.get('pe_forward', 'N/A')}")
        print(f"Analyst:    {md.get('analyst', {}).get('recommendation', 'N/A')}")
        print(f"Target:     ${md.get('analyst', {}).get('target_mean', 'N/A')}")

    gt = data.get("google_trends", {})
    print(f"GT trend:   {gt.get('trend_direction_90d', 'N/A')}")

    rd = data.get("reddit", {})
    ss = rd.get("sentiment_summary", {})
    print(f"Reddit:     {ss.get('overall', 'N/A')} ({rd.get('post_count', 0)} posts)")
