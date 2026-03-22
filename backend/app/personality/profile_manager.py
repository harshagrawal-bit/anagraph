"""
Phase 5 — Fund Personality & Profile Manager
Manages fund-specific investment profiles that shape how the AI analyst
reasons and outputs research. Each fund's profile is stored, versioned,
and injected into every research request.

The Five Personality Layers (from the doc):
  1. Investment style & time horizon
  2. Sector expertise & focus areas
  3. Risk tolerance & position sizing philosophy
  4. Historical edges & pattern preferences
  5. Output format preferences & reporting style
"""

import json
import os
from datetime import datetime, timezone
from typing import Any

# Default storage path — in production this would be a database
PROFILES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "profiles")


def _ensure_dir():
    os.makedirs(PROFILES_DIR, exist_ok=True)


def _profile_path(fund_id: str) -> str:
    return os.path.join(PROFILES_DIR, f"{fund_id}.json")


# ─────────────────────────────────────────────────────────
# DEFAULT PROFILE TEMPLATE
# ─────────────────────────────────────────────────────────

DEFAULT_PROFILE = {
    "fund_id": "default",
    "fund_name": "Default Fund",
    "created_at": None,
    "updated_at": None,
    "version": 1,

    # Layer 1: Investment Style
    "investment_style": {
        "approach": "long_short",  # long_only | long_short | macro | quant
        "time_horizon": "6-12 months",
        "market_cap_preference": "large_cap",  # mega | large | mid | small | all
        "geographic_focus": ["US"],
        "sector_exclusions": [],  # sectors you never touch
    },

    # Layer 2: Sector Expertise
    "sector_focus": {
        "primary": ["Technology", "Consumer Discretionary"],
        "secondary": ["Healthcare", "Financials"],
        "expertise_notes": (
            "Deepest expertise in software and semiconductors. "
            "Track record in consumer internet. Avoid energy and utilities."
        ),
    },

    # Layer 3: Risk Tolerance
    "risk_profile": {
        "max_position_size_pct": 10,  # max % of portfolio in single name
        "max_drawdown_tolerance_pct": 15,
        "leverage": 1.5,  # gross leverage target
        "stop_loss_trigger_pct": -20,  # automatic review trigger
        "short_book_active": True,
        "options_allowed": True,
    },

    # Layer 4: Historical Edges & Patterns
    "historical_edges": {
        "proven_edges": [],
        # Format: {"edge_name": str, "description": str, "win_rate": float,
        #           "avg_return": float, "sample_size": int, "last_updated": str}
        "pattern_preferences": [
            "earnings_acceleration",
            "margin_expansion",
            "multiple_expansion_catalyst",
        ],
        "anti_patterns": [
            "value_trap",
            "low_quality_leverage",
            "commodity_exposure",
        ],
    },

    # Layer 5: Output Preferences
    "output_preferences": {
        "brief_length": "standard",  # brief | standard | deep_dive
        "emphasis": ["bull_case", "key_risks", "signals"],
        "include_price_targets": True,
        "include_position_sizing": False,
        "custom_sections": [],
        "tone": "analytical",  # analytical | conservative | aggressive
    },

    # Fund-specific research memos (uploaded by user for learning)
    "private_memos": [],
    # Format: {"title": str, "date": str, "ticker": str, "outcome": str, "text_preview": str}

    # Feedback history (reinforcement learning input)
    "feedback_log": [],
    # Format: {"ticker": str, "date": str, "rating": int (1-5),
    #           "comment": str, "brief_id": str}
}


# ─────────────────────────────────────────────────────────
# PROFILE CRUD
# ─────────────────────────────────────────────────────────

def create_profile(fund_id: str, fund_name: str, overrides: dict | None = None) -> dict:
    """Create a new fund profile with optional overrides."""
    _ensure_dir()

    profile = dict(DEFAULT_PROFILE)
    profile["fund_id"] = fund_id
    profile["fund_name"] = fund_name
    profile["created_at"] = datetime.now(timezone.utc).isoformat()
    profile["updated_at"] = profile["created_at"]

    if overrides:
        _deep_merge(profile, overrides)

    path = _profile_path(fund_id)
    with open(path, "w") as f:
        json.dump(profile, f, indent=2)

    print(f"[ProfileManager] Created profile: {fund_id} ({fund_name})")
    return profile


def load_profile(fund_id: str) -> dict:
    """Load a fund profile. Returns default profile if not found."""
    path = _profile_path(fund_id)
    if not os.path.exists(path):
        return dict(DEFAULT_PROFILE)

    with open(path) as f:
        return json.load(f)


def save_profile(profile: dict) -> dict:
    """Save (update) a fund profile."""
    _ensure_dir()
    profile["updated_at"] = datetime.now(timezone.utc).isoformat()
    profile["version"] = profile.get("version", 1) + 1

    path = _profile_path(profile["fund_id"])
    with open(path, "w") as f:
        json.dump(profile, f, indent=2)

    return profile


def list_profiles() -> list[dict]:
    """List all fund profiles (metadata only)."""
    _ensure_dir()
    profiles = []
    for filename in os.listdir(PROFILES_DIR):
        if filename.endswith(".json"):
            path = os.path.join(PROFILES_DIR, filename)
            with open(path) as f:
                p = json.load(f)
                profiles.append({
                    "fund_id": p.get("fund_id"),
                    "fund_name": p.get("fund_name"),
                    "updated_at": p.get("updated_at"),
                    "version": p.get("version"),
                })
    return profiles


def delete_profile(fund_id: str) -> bool:
    """Delete a fund profile."""
    path = _profile_path(fund_id)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


# ─────────────────────────────────────────────────────────
# PROFILE → SYSTEM PROMPT INJECTOR
# ─────────────────────────────────────────────────────────

def build_personality_prompt(profile: dict) -> str:
    """
    Convert a fund profile into a system prompt personality injection.
    This is what makes each fund's AI uniquely theirs.
    """
    style = profile.get("investment_style", {})
    sectors = profile.get("sector_focus", {})
    risk = profile.get("risk_profile", {})
    edges = profile.get("historical_edges", {})
    output_prefs = profile.get("output_preferences", {})

    proven_edges = edges.get("proven_edges", [])
    edge_text = ""
    if proven_edges:
        edge_descriptions = [
            f"  - {e['edge_name']}: {e['description']} "
            f"(win rate {e.get('win_rate', 'N/A')}%, avg return {e.get('avg_return', 'N/A')}%)"
            for e in proven_edges[:5]
        ]
        edge_text = "YOUR PROVEN HISTORICAL EDGES:\n" + "\n".join(edge_descriptions) + "\n"

    patterns_text = ""
    if edges.get("pattern_preferences"):
        patterns_text = (
            f"PATTERNS YOU SEEK: {', '.join(edges['pattern_preferences'])}\n"
            f"PATTERNS YOU AVOID: {', '.join(edges.get('anti_patterns', []))}\n"
        )

    prompt = f"""
YOU ARE AN AI ANALYST FOR: {profile.get('fund_name', 'Unknown Fund')}

FUND INVESTMENT STYLE:
- Approach: {style.get('approach', 'long_short').replace('_', ' ').title()}
- Time Horizon: {style.get('time_horizon', '6-12 months')}
- Market Cap Focus: {style.get('market_cap_preference', 'large_cap').replace('_', ' ').title()}
- Geographic Focus: {', '.join(style.get('geographic_focus', ['US']))}
- Sectors You Exclude: {', '.join(style.get('sector_exclusions', ['none']))}

SECTOR EXPERTISE:
- Primary Coverage: {', '.join(sectors.get('primary', []))}
- Secondary Coverage: {', '.join(sectors.get('secondary', []))}
- Notes: {sectors.get('expertise_notes', '')}

RISK PARAMETERS:
- Max Position Size: {risk.get('max_position_size_pct', 10)}% of portfolio
- Max Drawdown Tolerance: {risk.get('max_drawdown_tolerance_pct', 15)}%
- Leverage Target: {risk.get('leverage', 1.5)}x gross
- Stop-Loss Trigger: {risk.get('stop_loss_trigger_pct', -20)}%
- Active Short Book: {'Yes' if risk.get('short_book_active') else 'No'}

{edge_text}{patterns_text}
OUTPUT PREFERENCES:
- Brief Length: {output_prefs.get('brief_length', 'standard').title()}
- Tone: {output_prefs.get('tone', 'analytical').title()}
- Emphasize: {', '.join(output_prefs.get('emphasis', ['bull_case', 'key_risks']))}

Apply this fund's personality to every research output. The fund's style should be
reflected in how you weight signals, size conviction, and frame risk.
""".strip()

    return prompt


# ─────────────────────────────────────────────────────────
# MEMO MANAGEMENT
# ─────────────────────────────────────────────────────────

def add_private_memo(fund_id: str, memo: dict) -> dict:
    """
    Add a private research memo to the fund profile.
    Memos are used by the reinforcement layer to learn fund-specific patterns.
    """
    profile = load_profile(fund_id)
    memos = profile.get("private_memos", [])
    memo["added_at"] = datetime.now(timezone.utc).isoformat()
    memo["id"] = f"memo_{len(memos) + 1:04d}"
    memos.append(memo)
    profile["private_memos"] = memos
    return save_profile(profile)


def add_feedback(fund_id: str, ticker: str, rating: int, comment: str, brief_id: str = "") -> dict:
    """
    Record analyst feedback on a research brief.
    Rating: 1-5 (1=poor, 5=excellent)
    This is the primary reinforcement signal.
    """
    profile = load_profile(fund_id)
    log = profile.get("feedback_log", [])
    log.append({
        "id": f"fb_{len(log) + 1:04d}",
        "ticker": ticker.upper(),
        "date": datetime.now(timezone.utc).isoformat(),
        "rating": max(1, min(5, rating)),
        "comment": comment,
        "brief_id": brief_id,
    })
    profile["feedback_log"] = log
    return save_profile(profile)


# ─────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────

def _deep_merge(base: dict, overrides: dict) -> None:
    """Recursively merge overrides into base dict in-place."""
    for key, value in overrides.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


# ─────────────────────────────────────────────────────────
# CLI DEMO
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Demo: create and display a profile
    profile = create_profile(
        fund_id="demo_fund",
        fund_name="Apex Capital Management",
        overrides={
            "investment_style": {
                "approach": "long_short",
                "time_horizon": "3-9 months",
                "market_cap_preference": "mid_cap",
            },
            "sector_focus": {
                "primary": ["Technology", "Healthcare"],
                "secondary": ["Industrials"],
                "expertise_notes": "Deep expertise in SaaS metrics and biotech catalysts.",
            },
            "risk_profile": {
                "max_position_size_pct": 8,
                "max_drawdown_tolerance_pct": 12,
                "stop_loss_trigger_pct": -15,
            },
            "historical_edges": {
                "pattern_preferences": [
                    "earnings_acceleration",
                    "biotech_catalyst",
                    "SaaS_NRR_expansion",
                ],
            },
        },
    )

    print("\n── PERSONALITY PROMPT ──")
    print(build_personality_prompt(profile))
