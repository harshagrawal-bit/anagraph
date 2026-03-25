"""
AI report generation service.
Provider priority: OpenRouter → Anthropic direct → Groq (free fallback)

Takes a 10-K document and produces a structured, fully-cited research memo.
"""

import re
from datetime import datetime, timezone

from app.core.config import settings
from app.models.research import FilingMetadata, ReportResponse

# --- OpenRouter (primary, OpenAI-compatible) ---
try:
    from openai import OpenAI as _OpenAI
    _openrouter_client = (
        _OpenAI(
            api_key=settings.OPEN_ROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            default_headers={"HTTP-Referer": "https://hedgeos.ai", "X-Title": "HedgeOS"},
        )
        if settings.OPEN_ROUTER_API_KEY
        else None
    )
except ImportError:
    _openrouter_client = None

# --- Anthropic direct ---
try:
    import anthropic as _anthropic
    _anthropic_client = (
        _anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        if settings.ANTHROPIC_API_KEY
        else None
    )
except ImportError:
    _anthropic_client = None

# --- Groq fallback ---
try:
    from openai import OpenAI as _OpenAI
    _groq_client = (
        _OpenAI(api_key=settings.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
        if settings.GROQ_API_KEY
        else None
    )
except ImportError:
    _groq_client = None

SYSTEM_PROMPT = """\
You are a senior equity research analyst at a premier long/short hedge fund.
Your job: produce rigorous, fully-cited research memos from SEC 10-K filings.

Hard rules — no exceptions:
1. Every factual claim, number, or statistic must have an inline citation:
   [10-K, Item X] or [10-K, FY<year>, <section>]
2. Never fabricate, infer, or estimate data not present in the source document.
   If data is absent, say "not disclosed in this filing."
3. Be concise and precise. No filler. Write like a memo, not an essay.
4. Flag risks prominently — do not bury them.
5. This output is analytical research, NOT investment advice. The analyst
   makes their own investment decision.
"""

REPORT_PROMPT = """\
Analyze the 10-K filing below and produce a structured equity research memo.

Company: {company}
Ticker: {ticker}
Filing Date: {filing_date}
Source: SEC EDGAR 10-K Filing

---
FILING CONTENT:
{content}
---

Write the research memo with these exact sections:

## 1. Business Overview
What the company does, key segments, geographic footprint, and market position.
Cite the relevant Item 1 passages.

## 2. Financial Snapshot
Revenue, gross margin, operating income, net income, EPS, FCF, and YoY growth.
Pull exact figures and cite the financial statements or MD&A section.

## 3. Balance Sheet & Capital Allocation
Debt levels, cash position, capex, buybacks/dividends, leverage ratios.
Cite Item 8 or MD&A.

## 4. Competitive Position & Moat
Key competitive advantages, moat sources, major competitors named in the filing.
Cite Item 1 or Item 1A.

## 5. Key Risk Factors
The 5 most material risks. Be specific — no generic boilerplate.
Cite Item 1A directly.

## 6. Management & Strategy
Stated strategic priorities, capital allocation philosophy, any recent guidance.
Cite MD&A or Item 7.

## 7. Investment Thesis
**Bull case (3 bullets):** Why this could outperform.
**Bear case (3 bullets):** Why this could disappoint.
Ground both cases in data from the filing.

## 8. Key Metrics to Monitor
What data points, releases, or events an analyst should track each quarter.

---
End the memo with this exact footer (fill in the blanks):
> Research memo generated from SEC 10-K filed {filing_date}.
> Source document: SEC EDGAR — {company} ({ticker}).
> This is analytical research, not investment advice. All figures sourced from
> the company's public SEC filing. Verify all data before acting.
"""

_SECTION_PATTERNS = [
    ("Business",     r"item\s+1[\.\s]",  40_000),
    ("Risk Factors", r"item\s+1a[\.\s]", 35_000),
    ("MDA",          r"item\s+7[\.\s]",  40_000),
    ("Financials",   r"item\s+8[\.\s]",  40_000),
]

# Groq free tier: ~12k TPM limit; Claude can handle much larger windows
_MAX_CHARS_GROQ = 20_000
_MAX_CHARS_CLAUDE = 80_000


def _extract_sections(text: str, max_chars: int) -> str:
    """Extract the most analytically valuable sections from a large 10-K."""
    if len(text) <= max_chars:
        return text

    text_lower = text.lower()
    TOC_SKIP = 20_000  # skip table of contents area

    found = []
    for label, pattern, _ in _SECTION_PATTERNS:
        m = re.search(pattern, text_lower[TOC_SKIP:])
        if m:
            found.append((label, m.start() + TOC_SKIP))

    if not found:
        mid = len(text) // 4
        return text[mid: mid + max_chars]

    per_section = max_chars // len(found)
    extracted = []
    for label, start in found:
        chunk = text[start: start + per_section]
        extracted.append(f"[Section: {label}]\n{chunk}")

    return "\n\n".join(extracted)


def _generate_with_claude(prompt: str) -> tuple:
    """Generate report using Anthropic Claude Opus. Returns (text, in_tok, out_tok, cost)."""
    message = _anthropic_client.messages.create(
        model=settings.anthropic_model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text
    in_tok = message.usage.input_tokens
    out_tok = message.usage.output_tokens
    cost = (in_tok * _CLAUDE_INPUT_COST_PER_M + out_tok * _CLAUDE_OUTPUT_COST_PER_M) / 1_000_000
    return text, in_tok, out_tok, round(cost, 4)


def _generate_with_groq(prompt: str) -> tuple:
    """Generate report using Groq LLaMA fallback. Returns (text, in_tok, out_tok, cost)."""
    message = _groq_client.chat.completions.create(
        model=settings.MODEL,
        max_tokens=settings.MAX_TOKENS,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    text = message.choices[0].message.content
    in_tok = message.usage.prompt_tokens
    out_tok = message.usage.completion_tokens
    return text, in_tok, out_tok, 0.0


def _generate_with_openrouter(prompt: str) -> tuple:
    """Generate report using OpenRouter (primary provider)."""
    response = _openrouter_client.chat.completions.create(
        model=settings.OPEN_ROUTER_MODEL,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    text = response.choices[0].message.content
    in_tok = response.usage.prompt_tokens
    out_tok = response.usage.completion_tokens
    return text, in_tok, out_tok, 0.0


def generate_report(text: str, filing: FilingMetadata) -> ReportResponse:
    """
    Generate a structured research report from 10-K plain text.
    Provider priority: OpenRouter → Anthropic → Groq
    """
    use_openrouter = _openrouter_client is not None and settings.use_openrouter
    use_claude = _anthropic_client is not None and settings.use_anthropic
    max_chars = _MAX_CHARS_CLAUDE if (use_openrouter or use_claude) else _MAX_CHARS_GROQ

    content = _extract_sections(text, max_chars)
    prompt = REPORT_PROMPT.format(
        company=filing.company,
        ticker=filing.ticker,
        filing_date=filing.date,
        content=content,
    )

    if use_openrouter:
        report_text, input_tok, output_tok, cost = _generate_with_openrouter(prompt)
        model_used = settings.OPEN_ROUTER_MODEL
    elif use_claude:
        report_text, input_tok, output_tok, cost = _generate_with_claude(prompt)
        model_used = "claude-opus-4-6"
    elif _groq_client is not None:
        report_text, input_tok, output_tok, cost = _generate_with_groq(prompt)
        model_used = settings.MODEL
    else:
        raise RuntimeError(
            "No AI provider configured. Set OPEN_ROUTER_API_KEY, ANTHROPIC_API_KEY, "
            "or GROQ_API_KEY in backend/.env"
        )

    return ReportResponse(
        ticker=filing.ticker,
        company=filing.company,
        filing_date=filing.date,
        report=report_text,
        input_tokens=input_tok,
        output_tokens=output_tok,
        estimated_cost_usd=cost,
        model=model_used,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
