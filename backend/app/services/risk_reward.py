"""Risk/Reward and trade setup calculator.

Computes position sizing, risk amounts, R:R ratios, and generates a trade plan
from proposed entry / stop / target levels.
"""
from typing import Dict, Any, List, Optional


# --- Forex pip / lot conventions ---
# Standard lots: 100,000 units. Pip sizes vary by pair.
class Markets:
    QUOTE_CURRENCY = {
        # The currency the profit is denominated in for standard pairs
    }

PIP_SIZE_MAP = {
    # JPY pairs use 0.01 pips for exchange-rate precision
    "JPY": 0.01,
    "XAUUSD": 0.10,
    "XAGUSD": 0.001,
    "GC=F": 0.10,
    "SI=F": 0.001,
    "CL=F": 0.01,
    "BZ=F": 0.01,
    "NG=F": 0.001,
    "HG=F": 0.0005,
}


def get_pip_size(symbol: str) -> float:
    s = symbol.upper()
    if "JPY" in s:
        return 0.01
    if s in ("XAUUSD", "GC=F"):
        return 0.10
    if s in ("XAGUSD", "SI=F"):
        return 0.001
    if s in ("CL=F", "BZ=F"):
        return 0.01
    if s in ("NG=F",):
        return 0.001
    if s in ("HG=F",):
        return 0.0005
    return 0.0001  # standard non-JPY forex


class RiskRewardCalculator:
    @staticmethod
    def calculate(
        entry: float,
        stop_loss: float,
        take_profit: float,
        account_size: float = 10000.0,
        risk_percent: float = 1.0,
        units_per_lot: float = 100000.0,
        pip_size: Optional[float] = None,
        symbol: str = "EURUSD",
    ) -> Dict[str, Any]:
        """Compute risk/reward metrics for a single entry/SL/TP."""
        if pip_size is None:
            pip_size = get_pip_size(symbol)

        risk_amount = account_size * (risk_percent / 100.0)
        direction = "long" if take_profit > entry else "short"

        # Distance in price and in pips
        sl_distance_price = abs(entry - stop_loss)
        tp_distance_price = abs(take_profit - entry)

        if sl_distance_price == 0:
            raise ValueError("Stop loss must differ from entry.")

        risk_pips = sl_distance_price / pip_size
        reward_pips = tp_distance_price / pip_size

        # Position size: units such that risk_amount = units * sl_distance_price
        # For forex, units refer to base currency quantity.
        units = risk_amount / sl_distance_price
        lots = units / units_per_lot

        reward_amount = units * tp_distance_price
        rr_ratio = reward_amount / risk_amount if risk_amount else 0.0

        return {
            "direction": direction,
            "risk_amount": round(risk_amount, 2),
            "reward_amount": round(reward_amount, 2),
            "rr_ratio": round(rr_ratio, 2),
            "risk_pips": round(risk_pips, 2),
            "reward_pips": round(reward_pips, 2),
            "position_size_units": round(units, 2),
            "position_lots": round(lots, 4),
            "units_per_lot": units_per_lot,
            "pip_size": pip_size,
        }

    @staticmethod
    def build_trade_plan(
        symbol: str,
        market_type: str,
        entry: float,
        stop_loss: float,
        take_profits: List[float],
        partial_close_pcts: Optional[List[float]] = None,
        account_size: float = 10000.0,
        risk_percent: float = 1.0,
    ) -> Dict[str, Any]:
        """Build a full trade plan with multiple targets, partial closes, and R:R per target."""
        risk_amount = account_size * (risk_percent / 100.0)
        pip_size = get_pip_size(symbol)

        if not take_profits:
            return {}

        sl_distance = abs(entry - stop_loss)
        if sl_distance == 0:
            raise ValueError("Stop loss must differ from entry.")

        units = risk_amount / sl_distance
        lots = units / 100000.0

        if partial_close_pcts is None:
            # Default ladder: 40/30/30 across however many targets
            n = len(take_profits)
            if n == 1:
                partial_close_pcts = [100]
            elif n == 2:
                partial_close_pcts = [50, 50]
            else:
                partial_close_pcts = [40, 30] + [30 / max(1, n - 2)] * (n - 2)

        targets = []
        for i, tp in enumerate(take_profits):
            reward = abs(tp - entry) * units
            pct = partial_close_pcts[i]
            targets.append({
                "target": round(tp, 6),
                "partial_close_pct": pct,
                "rr_ratio": round(reward / risk_amount, 2),
                "reward_amount": round(reward * (pct / 100), 2),
            })

        return {
            "symbol": symbol,
            "market_type": market_type,
            "direction": "long" if take_profits[-1] > entry else "short",
            "entry": round(entry, 6),
            "stop_loss": round(stop_loss, 6),
            "stop_loss_reason": "beyond structural level",
            "risk_amount": round(risk_amount, 2),
            "position_units": round(units, 2),
            "position_lots": round(lots, 4),
            "targets": targets,
            "pip_size": pip_size,
        }
