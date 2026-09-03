"""Mock analysis generator.

Produces a realistic structured analysis without calling the DeepSeek API.
Useful for development/demo when no API key is configured, and for running
automated tests of the pipeline.
"""
import json
from typing import Dict, Any, List
import numpy as np

from app.services.risk_reward import RiskRewardCalculator, get_pip_size
from app.services.structure import StructureDetector


def generate_mock_analysis(
    symbol: str,
    market_type: str,
    timeframe: str,
    current_price: float,
    indicators: Dict[str, Any],
    structure: Dict[str, Any],
    account_size: float = 10000.0,
    risk_percent: float = 1.0,
    question: str = "",
) -> Dict[str, Any]:
    """Generate a deterministic mock analysis from computed data."""
    price = current_price

    # Pick a direction from momentum bias
    rsi = (indicators.get("momentum", {}) or {}).get("rsi14") or 50
    bias = "bullish" if rsi >= 50 else "bearish"

    # Build a plausible trade setup
    atr = (indicators.get("volatility", {}) or {}).get("atr14") or price * 0.0005
    if bias == "bullish":
        entry = price
        stop_loss = price - 1.5 * atr
        take_profits = [price + atr, price + 2 * atr, price + 2.75 * atr]
    else:
        entry = price
        stop_loss = price + 1.5 * atr
        take_profits = [price - atr, price - 2 * atr, price - 2.75 * atr]

    plan = RiskRewardCalculator.build_trade_plan(
        symbol=symbol, market_type=market_type,
        entry=entry, stop_loss=stop_loss, take_profits=take_profits,
        account_size=account_size, risk_percent=risk_percent,
    )

    regime = structure.get("regime", "unknown")
    rr = plan["targets"][-1]["rr_ratio"] if plan.get("targets") else 0
    confidence = int(min(90, max(35, 50 + rr * 10 - (0 if regime != "volatile/choppy" else 15))))

    summary = (
        f"{symbol} is currently in a {regime.replace('_', ' ')} regime on {timeframe}. "
        f"Price at {price:.5f} with {bias} momentum bias."
    )

    analysis = {
        "executive_summary": summary,
        "market_regime": regime,
        "market_structure": structure,
        "indicators": indicators,
        "scenarios": {
            "bullish": f"Break above resistance toward {price + 2 * atr:.5f}",
            "bearish": f"Break below support toward {price - 2 * atr:.5f}",
            "base": f"Range between {price - atr:.5f} and {price + atr:.5f}",
        },
        "invalidation": f"Price closing beyond the {stop_loss:.5f} level invalidates the {bias} thesis.",
        "confidence": confidence,
        "disclaimer": (
            "Trading foreign exchange and commodities carries a high level of risk. "
            "This analysis is for educational purposes only and is not financial advice."
        ),
    }

    return {
        "analysis": analysis,
        "trade_setup": plan,
        "confidence": confidence,
        "mock": True,
        "generated_at": None,
    }
