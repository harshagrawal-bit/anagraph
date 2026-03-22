"""
Phase 5 — Reinforcement Learning Layer
Learns from analyst feedback to improve research quality over time.
This is the defensible moat: after 12 months, the AI thinks like THIS specific fund.

Three learning mechanisms:
  1. Feedback-weighted prompt adjustment (immediate — shifts tone/emphasis)
  2. Pattern extraction from high-rated memos (medium-term — learns fund preferences)
  3. Edge hypothesis validation (long-term — validates which alt-data signals work)
"""

import json
import os
import statistics
from datetime import datetime, timezone
from typing import Any

from app.personality.profile_manager import load_profile, save_profile


# ─────────────────────────────────────────────────────────
# FEEDBACK ANALYSIS
# ─────────────────────────────────────────────────────────

def analyze_feedback(fund_id: str) -> dict[str, Any]:
    """
    Analyze the fund's feedback log to extract learning signals.
    Returns summary statistics and actionable adjustments.
    """
    profile = load_profile(fund_id)
    feedback_log = profile.get("feedback_log", [])

    if not feedback_log:
        return {
            "fund_id": fund_id,
            "status": "no_feedback",
            "message": "No feedback recorded yet. Rate research briefs to enable learning.",
            "adjustments": [],
        }

    ratings = [fb["rating"] for fb in feedback_log]
    avg_rating = statistics.mean(ratings)
    recent_ratings = [fb["rating"] for fb in feedback_log[-10:]]
    recent_avg = statistics.mean(recent_ratings) if recent_ratings else avg_rating

    # Identify low-rated patterns (what to avoid)
    low_rated = [fb for fb in feedback_log if fb["rating"] <= 2]
    high_rated = [fb for fb in feedback_log if fb["rating"] >= 4]

    low_themes = _extract_themes([fb.get("comment", "") for fb in low_rated])
    high_themes = _extract_themes([fb.get("comment", "") for fb in high_rated])

    # Ticker-level performance
    ticker_ratings: dict[str, list] = {}
    for fb in feedback_log:
        t = fb.get("ticker", "UNKNOWN")
        ticker_ratings.setdefault(t, []).append(fb["rating"])

    ticker_summary = {
        t: {"avg": round(statistics.mean(r), 2), "count": len(r)}
        for t, r in ticker_ratings.items()
    }

    # Generate adjustments
    adjustments = _generate_adjustments(avg_rating, recent_avg, low_themes, high_themes)

    return {
        "fund_id": fund_id,
        "status": "analyzed",
        "total_feedback_count": len(feedback_log),
        "avg_rating": round(avg_rating, 2),
        "recent_avg_rating": round(recent_avg, 2),
        "trend": "improving" if recent_avg > avg_rating else "declining" if recent_avg < avg_rating - 0.3 else "stable",
        "high_rated_themes": high_themes,
        "low_rated_themes": low_themes,
        "ticker_performance": ticker_summary,
        "adjustments": adjustments,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


def _extract_themes(comments: list[str]) -> list[str]:
    """Simple keyword extraction from feedback comments."""
    theme_keywords = {
        "too_long": ["too long", "too verbose", "shorter", "concise"],
        "too_short": ["too short", "more detail", "deeper", "expand"],
        "wrong_tone": ["too bullish", "too bearish", "biased", "one-sided"],
        "good_risks": ["risk", "downside", "bear", "flag"],
        "good_data": ["data", "numbers", "specific", "quantified"],
        "missing_macro": ["macro", "rates", "fed", "dollar", "global"],
        "needs_catalyst": ["catalyst", "trigger", "when", "timeline"],
        "good_signals": ["signals", "monitor", "tracking", "weekly"],
    }

    found_themes = []
    combined = " ".join(comments).lower()

    for theme, keywords in theme_keywords.items():
        if any(kw in combined for kw in keywords):
            found_themes.append(theme)

    return found_themes


def _generate_adjustments(
    avg_rating: float,
    recent_avg: float,
    low_themes: list[str],
    high_themes: list[str],
) -> list[dict]:
    """Generate specific prompt/behavior adjustments based on feedback patterns."""
    adjustments = []

    if "too_long" in low_themes:
        adjustments.append({
            "type": "output_length",
            "action": "reduce",
            "reason": "Analysts rated lengthy briefs lower",
            "prompt_delta": "Be MORE concise. Target 400 words max per section.",
        })

    if "too_short" in low_themes:
        adjustments.append({
            "type": "output_length",
            "action": "increase",
            "reason": "Analysts want more depth",
            "prompt_delta": "Provide more analytical depth. Expand each section with supporting data.",
        })

    if "wrong_tone" in low_themes:
        adjustments.append({
            "type": "balance",
            "action": "rebalance",
            "reason": "Analysts flagged tone bias",
            "prompt_delta": "Ensure bull and bear cases are equally rigorous. No bias in either direction.",
        })

    if "missing_macro" in low_themes:
        adjustments.append({
            "type": "macro_context",
            "action": "amplify",
            "reason": "Analysts want more macro context",
            "prompt_delta": "Always connect company analysis to current macro environment (rates, FX, sector cycle).",
        })

    if "needs_catalyst" in low_themes:
        adjustments.append({
            "type": "catalyst_timing",
            "action": "add",
            "reason": "Analysts want specific catalysts with timing",
            "prompt_delta": "Always specify WHEN the thesis plays out. Name specific catalysts with dates.",
        })

    if avg_rating < 3.0:
        adjustments.append({
            "type": "overall_quality",
            "action": "improve",
            "reason": f"Average rating {avg_rating:.1f}/5 is below threshold",
            "prompt_delta": "Focus more on data-driven insights vs narrative. Every claim needs a number.",
        })

    return adjustments


# ─────────────────────────────────────────────────────────
# REINFORCEMENT — APPLY LEARNINGS TO PROFILE
# ─────────────────────────────────────────────────────────

def apply_reinforcement(fund_id: str) -> dict:
    """
    Apply feedback-based learnings to the fund's profile.
    Updates output_preferences and adds learned adjustments.
    Called automatically after every 5 feedback entries.
    """
    analysis = analyze_feedback(fund_id)
    if analysis["status"] == "no_feedback":
        return analysis

    profile = load_profile(fund_id)

    # Apply output length adjustment
    for adj in analysis["adjustments"]:
        if adj["type"] == "output_length":
            if adj["action"] == "reduce":
                profile["output_preferences"]["brief_length"] = "brief"
            elif adj["action"] == "increase":
                profile["output_preferences"]["brief_length"] = "deep_dive"

        elif adj["type"] == "balance":
            profile["output_preferences"]["tone"] = "analytical"

        elif adj["type"] == "macro_context":
            emphasis = profile["output_preferences"].get("emphasis", [])
            if "macro_context" not in emphasis:
                emphasis.append("macro_context")
            profile["output_preferences"]["emphasis"] = emphasis

    # Store reinforcement history
    reinforcement_history = profile.get("reinforcement_history", [])
    reinforcement_history.append({
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "based_on_n_feedback": analysis["total_feedback_count"],
        "avg_rating": analysis["avg_rating"],
        "adjustments_applied": [a["type"] for a in analysis["adjustments"]],
    })
    profile["reinforcement_history"] = reinforcement_history[-20:]  # keep last 20

    updated = save_profile(profile)
    print(f"[Reinforcement] Applied {len(analysis['adjustments'])} adjustments to {fund_id}")
    return {
        "fund_id": fund_id,
        "status": "reinforcement_applied",
        "adjustments_applied": analysis["adjustments"],
        "new_profile_version": updated["version"],
    }


# ─────────────────────────────────────────────────────────
# EDGE VALIDATION
# ─────────────────────────────────────────────────────────

def validate_edge_hypothesis(
    fund_id: str,
    edge_name: str,
    ticker: str,
    predicted_direction: str,
    actual_outcome: str,
    return_pct: float,
) -> dict:
    """
    Record the outcome of an edge hypothesis to validate its predictive power.
    Over time, this builds a fund-specific edge library with real win rates.

    Args:
        predicted_direction: "bull" or "bear"
        actual_outcome: "bull" or "bear" (what actually happened)
        return_pct: actual stock return after thesis period (e.g., 15.3 for +15.3%)
    """
    profile = load_profile(fund_id)
    edges = profile.get("historical_edges", {})
    proven_edges = edges.get("proven_edges", [])

    # Find or create edge record
    edge_record = next((e for e in proven_edges if e["edge_name"] == edge_name), None)

    if not edge_record:
        edge_record = {
            "edge_name": edge_name,
            "description": f"Auto-discovered edge: {edge_name}",
            "observations": [],
            "win_count": 0,
            "total_count": 0,
            "win_rate": 0.0,
            "avg_return": 0.0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        proven_edges.append(edge_record)

    # Record observation
    is_win = predicted_direction.lower() == actual_outcome.lower()
    observation = {
        "ticker": ticker.upper(),
        "date": datetime.now(timezone.utc).isoformat(),
        "predicted": predicted_direction,
        "actual": actual_outcome,
        "return_pct": return_pct,
        "win": is_win,
    }
    edge_record["observations"] = edge_record.get("observations", [])[-49:]  # keep last 50
    edge_record["observations"].append(observation)

    # Recompute stats
    all_obs = edge_record["observations"]
    edge_record["win_count"] = sum(1 for o in all_obs if o["win"])
    edge_record["total_count"] = len(all_obs)
    edge_record["win_rate"] = round(edge_record["win_count"] / edge_record["total_count"] * 100, 1)
    edge_record["avg_return"] = round(statistics.mean(o["return_pct"] for o in all_obs), 2)
    edge_record["last_updated"] = datetime.now(timezone.utc).isoformat()

    # Auto-promote edge if win rate > 60% with 10+ samples
    if edge_record["win_rate"] >= 60 and edge_record["total_count"] >= 10:
        if edge_name not in edges.get("pattern_preferences", []):
            edges.setdefault("pattern_preferences", []).append(edge_name)
            print(f"[Reinforcement] Edge '{edge_name}' promoted to pattern preferences "
                  f"(win rate: {edge_record['win_rate']}%)")

    edges["proven_edges"] = proven_edges
    profile["historical_edges"] = edges
    save_profile(profile)

    return {
        "edge_name": edge_name,
        "observation_recorded": observation,
        "edge_stats": {
            "win_rate": edge_record["win_rate"],
            "avg_return": edge_record["avg_return"],
            "sample_size": edge_record["total_count"],
        },
    }


# ─────────────────────────────────────────────────────────
# PROMPT AUGMENTATION (called before each research request)
# ─────────────────────────────────────────────────────────

def get_reinforcement_prompt_delta(fund_id: str) -> str:
    """
    Generate additional prompt instructions based on accumulated learnings.
    Injected into every research request to gradually improve output quality.
    """
    analysis = analyze_feedback(fund_id)
    if analysis["status"] == "no_feedback" or not analysis.get("adjustments"):
        return ""

    delta_lines = ["\nLEARNED PREFERENCES FOR THIS FUND (from analyst feedback):"]
    for adj in analysis["adjustments"]:
        delta_lines.append(f"- {adj['prompt_delta']}")

    return "\n".join(delta_lines)
