#!/usr/bin/env python3
"""
AlphaOS MVP Smoke Test
======================
Pulls the latest 10-K for a company from SEC EDGAR,
sends it through Claude, and prints a fully-cited research memo.

Usage:
    python scripts/test_mvp.py AAPL
    python scripts/test_mvp.py MSFT
    python scripts/test_mvp.py NVDA
"""

import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime

# Make sure the backend package is importable when running from any directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.edgar import fetch_10k
from app.services.report_generator import generate_report


async def run(ticker: str) -> None:
    sep = "=" * 64

    print(f"\n{sep}")
    print(f"  AlphaOS — Research Report Generator")
    print(f"  Ticker: {ticker}")
    print(f"{sep}\n")

    # ── Step 1: EDGAR ──────────────────────────────────────────────
    print("Step 1/2  Fetching 10-K from SEC EDGAR...")
    text, filing = await fetch_10k(ticker)
    print(f"  Company      : {filing.company}")
    print(f"  Filing date  : {filing.date}")
    print(f"  CIK          : {filing.cik}")
    print(f"  Document size: {len(text):,} characters\n")

    # ── Step 2: Report generation ───────────────────────────────────
    print("Step 2/2  Generating research memo with Claude...")
    result = generate_report(text, filing)
    print(f"  Model        : {result.model}")
    print(f"  Tokens in/out: {result.input_tokens:,} / {result.output_tokens:,}")
    print(f"  Est. cost    : ${result.estimated_cost_usd:.4f}\n")

    # ── Output ──────────────────────────────────────────────────────
    print(sep)
    print("  RESEARCH MEMO")
    print(sep)
    print()
    print(result.report)
    print()

    # Save JSON artefact
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(f"report_{ticker}_{ts}.json")
    out_path.write_text(json.dumps(result.model_dump(), indent=2))
    print(f"\n[Saved to {out_path}]")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    asyncio.run(run(sys.argv[1].upper()))
