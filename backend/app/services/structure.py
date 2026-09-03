"""Market structure and key-level detection.

Detects swing highs/lows, Break of Structure (BOS), Change of Character (CHoCH),
order blocks, fair value gaps, liquidity pools, psychological levels, and
classifies the market regime.
"""
from typing import Dict, Any, List
import pandas as pd


class StructureDetector:
    """Identifies market structure and key levels from OHLC data."""

    @staticmethod
    def find_swings(df: pd.DataFrame, left: int = 5, right: int = 5) -> Dict[str, Any]:
        """Find swing highs and swing lows using left/right lookback."""
        highs = df["high"].values
        lows = df["low"].values
        dates = df["date"].astype(str).values if "date" in df.columns else [str(i) for i in range(len(df))]
        swing_highs = []
        swing_lows = []
        for i in range(left, len(df) - right):
            window_high = highs[i - left : i + right + 1]
            if highs[i] == window_high.max():
                swing_highs.append({"price": float(highs[i]), "index": i, "date": dates[i]})
            window_low = lows[i - left : i + right + 1]
            if lows[i] == window_low.min():
                swing_lows.append({"price": float(lows[i]), "index": i, "date": dates[i]})
        return {"swing_highs": swing_highs, "swing_lows": swing_lows}

    @staticmethod
    def detect_bos_choch(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect Break of Structure and Change of Character events."""
        swings = StructureDetector.find_swings(df)
        highs = swings["swing_highs"]
        lows = swings["swing_lows"]
        events = []

        # Look at last few swing highs/lows for structure breaks
        recent_high = max(highs[-3:], key=lambda x: x["price"]) if highs else None
        recent_low = min(lows[-3:], key=lambda x: x["price"]) if lows else None
        prev_high = max(highs[-4:-1], key=lambda x: x["price"]) if len(highs) >= 2 else None
        prev_low = min(lows[-4:-1], key=lambda x: x["price"]) if len(lows) >= 2 else None

        if recent_high and prev_high and recent_high["price"] > prev_high["price"]:
            events.append({"type": "BOS_UP", "level": recent_high["price"], "detail": "Break of prior swing high"})
        if recent_low and prev_low and recent_low["price"] < prev_low["price"]:
            events.append({"type": "BOS_DOWN", "level": recent_low["price"], "detail": "Break of prior swing low"})

        # CHoCH detection: recent low > prior high (shift to bullish) or vice versa
        if recent_low and prev_high and recent_low["price"] > prev_high["price"]:
            events.append({"type": "CHoCH_BULL", "level": recent_low["price"], "detail": "Structure shifted bullish"})
        if recent_high and prev_low and recent_high["price"] < prev_low["price"]:
            events.append({"type": "CHoCH_BEAR", "level": recent_high["price"], "detail": "Structure shifted bearish"})

        return events

    @staticmethod
    def find_order_blocks(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Find order blocks: last opposite candle before an impulsive move."""
        blocks = []
        closes = df["close"].values
        opens = df["open"].values
        highs = df["high"].values
        lows = df["low"].values
        for i in range(2, len(df) - 1):
            # Impulse = large candle relative to the previous
            imp = abs(closes[i] - opens[i])
            prev = abs(closes[i - 1] - opens[i - 1]) if i >= 1 else 0
            if imp > prev * 1.5 and imp > 0:
                # The candle before the impulse is a candidate order block
                ob_high = max(highs[i - 1], opens[i - 1], closes[i - 1])
                ob_low = min(lows[i - 1], opens[i - 1], closes[i - 1])
                direction = "bullish" if closes[i] > opens[i] else "bearish"
                blocks.append({
                    "type": f"order_block_{direction}",
                    "top": float(ob_high),
                    "bottom": float(ob_low),
                })
        # Keep unique recent blocks
        seen = []
        for b in blocks[-8:]:
            key = (round(b["top"], 5), round(b["bottom"], 5))
            if key not in seen:
                seen.append(key)
        return blocks[-6:]

    @staticmethod
    def find_fvg(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Find Fair Value Gaps: gaps between candle[i-1] high and candle[i+1] low."""
        fvgs = []
        highs = df["high"].values
        lows = df["low"].values
        for i in range(1, len(df) - 1):
            # Bullish FVG: candle[i+1].low > candle[i-1].high
            if lows[i + 1] > highs[i - 1]:
                fvgs.append({
                    "type": "bullish_fvg",
                    "gap_top": float(lows[i + 1]),
                    "gap_bottom": float(highs[i - 1]),
                })
            # Bearish FVG: candle[i+1].high < candle[i-1].low
            elif highs[i + 1] < lows[i - 1]:
                fvgs.append({
                    "type": "bearish_fvg",
                    "gap_top": float(lows[i - 1]),
                    "gap_bottom": float(highs[i + 1]),
                })
        return fvgs[-4:]

    @staticmethod
    def find_liquidity_pools(swing_highs, swing_lows) -> List[Dict[str, Any]]:
        """Liquidity pools: clusters of equal highs/lows (stop hunts)."""
        pools = []
        if swing_highs:
            px = [s["price"] for s in swing_highs]
            target = max(px)
            count = px.count(target)
            if count >= 2:
                pools.append({"type": "buy_side_liquidity", "level": float(target), "touches": count})
        if swing_lows:
            px = [s["price"] for s in swing_lows]
            target = min(px)
            count = px.count(target)
            if count >= 2:
                pools.append({"type": "sell_side_liquidity", "level": float(target), "touches": count})
        return pools

    @staticmethod
    def psychological_levels(price: float) -> List[Dict[str, Any]]:
        """Round number psychological levels around current price."""
        magnitude = 10 ** (int(str(int(price))[0].__len__()) - 1) if price != 0 else 10
        base = round(price / magnitude) * magnitude
        levels = []
        for i in (-1, 0, 1):
            levels.append({"type": "psychological", "level": float(base + i * magnitude)})
        return levels

    @staticmethod
    def detect_regime(df: pd.DataFrame, indicators: Dict[str, Any]) -> str:
        """Classify the market regime: trending/ranging/volatile/transition."""
        closes = df["close"].values
        if len(closes) < 20:
            return "insufficient_data"

        # Count consecutive higher lows / lower highs for trend
        high_changes = df["high"].diff().dropna().values
        low_changes = df["low"].diff().dropna().values
        up_lows = int((low_changes > 0).sum())
        down_highs = int((high_changes < 0).sum())
        total = len(high_changes)

        adx = indicators.get("trend", {}).get("adx")
        atr = indicators.get("volatility", {}).get("atr14")
        bb_upper = indicators.get("volatility", {}).get("bb_upper")
        bb_lower = indicators.get("volatility", {}).get("bb_lower")
        bb_mid = indicators.get("volatility", {}).get("bb_middle")
        price = closes[-1]

        # Volatility test
        volatile = False
        if atr and bb_mid and bb_upper and bb_lower:
            bb_width = (bb_upper - bb_lower)
            if bb_width > 0 and atr > bb_width * 0.20:
                # Price near extremes
                if price > bb_upper or price < bb_lower:
                    volatile = True

        if volatile:
            return "volatile/choppy"

        if adx:
            if adx > 25:
                if up_lows / total > 0.6 and down_highs / total < 0.4:
                    return "trending_up"
                elif down_highs / total > 0.6 and up_lows / total < 0.4:
                    return "trending_down"
                return "transition"
            elif adx < 20:
                return "ranging"
            else:
                return "transition"
        return "insufficient_data"

    @staticmethod
    def run(df: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Run the full structure pipeline and return compiled result."""
        swings = StructureDetector.find_swings(df)
        events = StructureDetector.detect_bos_choch(df)
        order_blocks = StructureDetector.find_order_blocks(df)
        fvgs = StructureDetector.find_fvg(df)
        liquidity = StructureDetector.find_liquidity_pools(
            swings["swing_highs"], swings["swing_lows"]
        )
        price = float(df["close"].iloc[-1])
        psych = StructureDetector.psychological_levels(price)
        regime = StructureDetector.detect_regime(df, indicators)

        # Compile key levels
        levels = []
        for s in swings["swing_highs"][-3:]:
            levels.append({"type": "swing_high", "price": s["price"]})
        for s in swings["swing_lows"][-3:]:
            levels.append({"type": "swing_low", "price": s["price"]})
        for pb in psych:
            levels.append({"type": "psychological", "price": pb["level"]})
        # Round levels
        rounded = []
        seen = set()
        for lv in levels:
            key = round(lv["price"], 4)
            if key not in seen:
                seen.add(key)
                rounded.append({**lv, "price": round(lv["price"], 6)})

        return {
            "regime": regime,
            "swings": {
                "highs": swings["swing_highs"][-4:],
                "lows": swings["swing_lows"][-4:],
            },
            "bos_choch": events,
            "order_blocks": order_blocks,
            "fair_value_gaps": fvgs,
            "liquidity_pools": liquidity,
            "key_levels": rounded,
        }
