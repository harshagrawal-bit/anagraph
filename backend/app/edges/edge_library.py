"""
Phase 6 — Edge Discovery Engine
EDGE LIBRARY: Stores and manages the fund's discovered edge hypotheses.
Maps each edge to the 6 known pattern categories from the doc.

The six edge patterns:
  1. PHYSICAL WORLD PRECEDES FINANCIAL REPORTING
  2. DIGITAL BEHAVIOR PRECEDES REAL BEHAVIOR
  3. SUPPLY CHAIN SIGNALS UPSTREAM
  4. MANAGEMENT BEHAVIOR DIVERGES FROM WORDS
  5. CROSS-DOMAIN KNOWLEDGE TRANSFER
  6. INFORMATION LAG EXPLOITATION
"""

import json
import os
from datetime import datetime, timezone
from typing import Any

EDGES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "edges")

# ─────────────────────────────────────────────────────────
# EDGE PATTERN TAXONOMY
# ─────────────────────────────────────────────────────────

EDGE_PATTERNS = {
    "physical_world": {
        "id": "physical_world",
        "name": "Physical World Precedes Financial Reporting",
        "description": (
            "Real-world physical signals (parking lots, factory activity, shipping, "
            "satellite imagery) appear 4-8 weeks before they show up in quarterly reports."
        ),
        "data_sources": [
            "Satellite imagery (Maxar, Planet Labs)",
            "Parking lot occupancy (Orbital Insight)",
            "Port congestion data (Marine Traffic)",
            "Factory emissions/smoke patterns",
            "Foot traffic data (Placer.ai, SafeGraph)",
            "Trucking volume (FreightWaves, SONAR)",
        ],
        "lead_time_weeks": "4-8",
        "best_for": ["retail", "manufacturing", "energy", "real estate", "logistics"],
        "example": "Satellite showed empty Apple supplier parking lots 6 weeks before iPhone production cut announcement.",
    },
    "digital_behavior": {
        "id": "digital_behavior",
        "name": "Digital Behavior Precedes Real Behavior",
        "description": (
            "Consumer digital signals (search trends, app downloads, web traffic, "
            "job postings) predict revenue 1-2 quarters before it materializes."
        ),
        "data_sources": [
            "Google Trends (free)",
            "App Annie / data.ai (app downloads)",
            "SimilarWeb (web traffic)",
            "LinkedIn job postings",
            "Indeed hiring trends",
            "Glassdoor reviews (culture/morale signal)",
            "App Store ratings trend",
        ],
        "lead_time_weeks": "4-12",
        "best_for": ["consumer_internet", "SaaS", "e-commerce", "fintech", "gaming"],
        "example": "Google Trends for 'Shopify' rose 40% 8 weeks before GMV beat in Q4 2023.",
    },
    "supply_chain_upstream": {
        "id": "supply_chain_upstream",
        "name": "Supply Chain Signals Upstream",
        "description": (
            "Supplier earnings, raw material prices, and shipping rates predict "
            "downstream company performance with a 1-2 quarter lag."
        ),
        "data_sources": [
            "Supplier company earnings calls",
            "Baltic Dry Index (global shipping)",
            "FRED commodity price data",
            "ISM Manufacturing PMI",
            "Component pricing (DRAM, NAND, displays)",
            "Freight rates (Freightos, Drewry)",
            "Channel inventory data (distributors)",
        ],
        "lead_time_weeks": "6-16",
        "best_for": ["semiconductors", "consumer_electronics", "automotive", "aerospace", "retail"],
        "example": "TSMC capex guidance cut → ASML order book decline → semiconductor equipment names 1Q ahead.",
    },
    "management_behavior": {
        "id": "management_behavior",
        "name": "Management Behavior Diverges from Words",
        "description": (
            "Insider buying/selling, executive departures, option exercise timing, "
            "and conference attendance reveal conviction level public statements conceal."
        ),
        "data_sources": [
            "SEC Form 4 (insider trades — free, same-day)",
            "SEC Form 144 (planned sales)",
            "Executive departure announcements (8-K)",
            "Proxy statement (compensation structure)",
            "Conference attendance patterns",
            "Glassdoor CEO rating trend",
        ],
        "lead_time_weeks": "2-12",
        "best_for": ["all_sectors"],
        "example": "CEO bought $5M in personal shares 3 weeks before earnings beat. Signal value: high.",
    },
    "cross_domain": {
        "id": "cross_domain",
        "name": "Cross-Domain Knowledge Transfer",
        "description": (
            "Frameworks from epidemiology, military intelligence, sports analytics, "
            "or logistics applied to financial problems that mainstream analysts miss."
        ),
        "data_sources": [
            "Academic research (SSRN, arXiv)",
            "Military strategy frameworks",
            "Sports analytics models (Moneyball-style)",
            "Epidemiological spread models applied to market adoption",
            "Game theory applied to competitive dynamics",
        ],
        "lead_time_weeks": "varies",
        "best_for": ["all_sectors"],
        "example": "SIR epidemiological model applied to social media user growth predicted saturation 2Q early.",
    },
    "information_lag": {
        "id": "information_lag",
        "name": "Information Lag Exploitation",
        "description": (
            "Data that legally exists and is publicly accessible today but won't "
            "appear in SEC filings for 60-90 days. First-mover advantage in public data."
        ),
        "data_sources": [
            "State unemployment insurance filings (layoff signals)",
            "FOIA requests (regulatory correspondence)",
            "Local permit databases (construction, expansion)",
            "FAA aircraft registrations (executive travel patterns)",
            "FCC spectrum auction bids",
            "Import/export manifest data (Panjiva, ImportGenius)",
            "Patent filings (USPTO — new technology directions)",
        ],
        "lead_time_weeks": "4-12",
        "best_for": ["all_sectors"],
        "example": "Texas workforce commission layoff notices filed 60 days before tech company's 'strategic restructuring' 8-K.",
    },
}


def _ensure_dir():
    os.makedirs(EDGES_DIR, exist_ok=True)


def _edges_path(fund_id: str) -> str:
    return os.path.join(EDGES_DIR, f"{fund_id}_edges.json")


# ─────────────────────────────────────────────────────────
# EDGE LIBRARY CRUD
# ─────────────────────────────────────────────────────────

def get_pattern_library() -> dict:
    """Return the canonical 6-pattern edge taxonomy."""
    return EDGE_PATTERNS


def load_fund_edges(fund_id: str) -> list[dict]:
    """Load fund-specific edge hypotheses."""
    path = _edges_path(fund_id)
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def save_edge_hypothesis(fund_id: str, hypothesis: dict) -> dict:
    """Save a new edge hypothesis to the fund's edge library."""
    _ensure_dir()
    edges = load_fund_edges(fund_id)

    hypothesis["id"] = f"edge_{len(edges) + 1:04d}"
    hypothesis["created_at"] = datetime.now(timezone.utc).isoformat()
    hypothesis["status"] = hypothesis.get("status", "hypothesis")  # hypothesis | validated | rejected
    hypothesis["observations"] = []

    edges.append(hypothesis)

    path = _edges_path(fund_id)
    with open(path, "w") as f:
        json.dump(edges, f, indent=2)

    return hypothesis


def update_edge_status(fund_id: str, edge_id: str, status: str, note: str = "") -> dict | None:
    """Update edge hypothesis status: hypothesis → validated | rejected."""
    edges = load_fund_edges(fund_id)
    for edge in edges:
        if edge["id"] == edge_id:
            edge["status"] = status
            edge["updated_at"] = datetime.now(timezone.utc).isoformat()
            if note:
                edge.setdefault("notes", []).append({
                    "date": datetime.now(timezone.utc).isoformat(),
                    "note": note,
                })
            path = _edges_path(fund_id)
            with open(path, "w") as f:
                json.dump(edges, f, indent=2)
            return edge
    return None


def get_validated_edges(fund_id: str) -> list[dict]:
    """Return only validated (proven) edges for this fund."""
    return [e for e in load_fund_edges(fund_id) if e.get("status") == "validated"]


def get_edges_by_pattern(fund_id: str, pattern_id: str) -> list[dict]:
    """Return edges for a specific pattern category."""
    return [
        e for e in load_fund_edges(fund_id)
        if e.get("pattern_id") == pattern_id
    ]


def get_edges_by_ticker(fund_id: str, ticker: str) -> list[dict]:
    """Return all edges ever identified for a specific ticker."""
    return [
        e for e in load_fund_edges(fund_id)
        if ticker.upper() in e.get("tickers", [])
    ]


def get_edge_summary(fund_id: str) -> dict[str, Any]:
    """Summary statistics for the fund's edge library."""
    all_edges = load_fund_edges(fund_id)
    return {
        "fund_id": fund_id,
        "total_hypotheses": len(all_edges),
        "validated": sum(1 for e in all_edges if e.get("status") == "validated"),
        "rejected": sum(1 for e in all_edges if e.get("status") == "rejected"),
        "pending": sum(1 for e in all_edges if e.get("status") == "hypothesis"),
        "by_pattern": {
            pid: sum(1 for e in all_edges if e.get("pattern_id") == pid)
            for pid in EDGE_PATTERNS
        },
    }
