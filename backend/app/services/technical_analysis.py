"""Technical analysis engine.

Computes indicators (trend, momentum, volatility, volume), detects market
structure (swing highs/lows, BOS/CHoCH), identifies key levels, and classifies
the market regime. Returns a normalized dictionary consumed by the AI agent.
"""
import math
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np


def _safe(val):
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, 6)
    except (TypeError, ValueError):
        return None


class AnalysisEngine:
    """Core technical analysis computation."""

    @staticmethod
    def compute_indicators(df: pd.DataFrame) -> Dict[str, Any]:
        """Compute all technical indicators from OHLCV DataFrame."""
        df = df.copy()
        for c in ["open", "high", "low", "close", "volume"]:
            if c not in df.columns:
                df[c] = np.nan

        # --- Trend ---
        df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
        df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
        df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()

        # ADX
        adx = AnalysisEngine._adx(df)

        # Supertrend (simplified)
        st = AnalysisEngine._supertrend(df)

        # --- Momentum ---
        rsi = AnalysisEngine._rsi(df["close"], 14)
        macd_line, macd_signal, macd_hist = AnalysisEngine._macd(df["close"])
        stoch_k, stoch_d = AnalysisEngine._stochastic(df)
        cci = AnalysisEngine._cci(df)

        # --- Volatility ---
        atr = AnalysisEngine._atr(df, 14)
        bb_upper, bb_mid, bb_lower = AnalysisEngine._bollinger(df, 20)

        # --- Volume ---
        obv = AnalysisEngine._obv(df)
        vwap = AnalysisEngine._vwap(df)
        vol_profile = AnalysisEngine._volume_profile(df)

        last = df.iloc[-1]
        return {
            "trend": {
                "ema20": _safe(last["ema20"]),
                "ema50": _safe(last["ema50"]),
                "ema200": _safe(last["ema200"]),
                "ema_align": "bullish" if _safe(last["ema20"]) > _safe(last["ema50"]) else "bearish",
                "adx": _safe(adx),
                "supertrend": "bullish" if st else "bearish",
            },
            "momentum": {
                "rsi14": _safe(rsi),
                "macd": _safe(macd_line),
                "macd_signal": _safe(macd_signal),
                "macd_hist": _safe(macd_hist),
                "stoch_k": _safe(stoch_k),
                "stoch_d": _safe(stoch_d),
                "cci": _safe(cci),
            },
            "volatility": {
                "atr14": _safe(atr),
                "bb_upper": _safe(bb_upper),
                "bb_middle": _safe(bb_mid),
                "bb_lower": _safe(bb_lower),
                "bb_position": _safe(bb_mid),
            },
            "volume": {
                "obv": _safe(obv),
                "vwap": _safe(vwap),
                "poc": _safe(vol_profile.get("poc")),
                "value_area_high": _safe(vol_profile.get("value_area_high")),
                "value_area_low": _safe(vol_profile.get("value_area_low")),
            },
            "current_price": _safe(last["close"]),
        }

    # --- Individual indicators ---

    @staticmethod
    def _rsi(series: pd.Series, period: int = 14) -> Optional[float]:
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    @staticmethod
    def _macd(series: pd.Series):
        ema12 = series.ewm(span=12, adjust=False).mean()
        ema26 = series.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal = macd_line.ewm(span=9, adjust=False).mean()
        hist = macd_line - signal
        return macd_line.iloc[-1], signal.iloc[-1], hist.iloc[-1]

    @staticmethod
    def _atr(df: pd.DataFrame, period: int = 14) -> Optional[float]:
        high, low, close = df["high"], df["low"], df["close"]
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ], axis=1).max(axis=1)
        return tr.ewm(alpha=1 / period, min_periods=period).mean().iloc[-1]

    @staticmethod
    def _bollinger(df: pd.DataFrame, period: int = 20):
        mid = df["close"].rolling(period).mean()
        std = df["close"].rolling(period).std()
        upper = mid + 2 * std
        lower = mid - 2 * std
        return upper.iloc[-1], mid.iloc[-1], lower.iloc[-1]

    @staticmethod
    def _stochastic(df: pd.DataFrame, k=14, d=3):
        low_min = df["low"].rolling(k).min()
        high_max = df["high"].rolling(k).max()
        rng = (high_max - low_min).replace(0, np.nan)
        k_line = 100 * ((df["close"] - low_min) / rng)
        d_line = k_line.rolling(d).mean()
        return k_line.iloc[-1], d_line.iloc[-1]

    @staticmethod
    def _cci(df: pd.DataFrame, period=20):
        tp = (df["high"] + df["low"] + df["close"]) / 3
        sma = tp.rolling(period).mean()
        mad = tp.rolling(period).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
        return ((tp - sma) / (0.015 * mad)).iloc[-1]

    @staticmethod
    def _adx(df: pd.DataFrame, period=14) -> Optional[float]:
        high, low, close = df["high"], df["low"], df["close"]
        up = high.diff()
        down = -low.diff()
        plus_dm = np.where((up > down) & (up > 0), up, 0.0)
        minus_dm = np.where((down > up) & (down > 0), down, 0.0)
        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1 / period, min_periods=period).mean()
        plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1 / period, min_periods=period).mean() / atr
        minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1 / period, min_periods=period).mean() / atr
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.ewm(alpha=1 / period, min_periods=period).mean()
        return adx.iloc[-1]

    @staticmethod
    def _obv(df: pd.DataFrame) -> Optional[float]:
        obv = (np.sign(df["close"].diff()) * df["volume"]).fillna(0).cumsum()
        return obv.iloc[-1]

    @staticmethod
    def _vwap(df: pd.DataFrame) -> Optional[float]:
        tp = (df["high"] + df["low"] + df["close"]) / 3
        if df["volume"].sum() == 0:
            return None
        return float((tp * df["volume"]).sum() / df["volume"].sum())

    @staticmethod
    def _volume_profile(df: pd.DataFrame, bins: int = 40) -> Dict[str, Any]:
        """Approximate volume profile via histogram; returns POC and value area."""
        if df.empty or "volume" not in df.columns or df["volume"].sum() == 0:
            return {}
        counts, edges = np.histogram(df["close"], bins=bins, weights=df["volume"])
        bin_centers = (edges[:-1] + edges[1:]) / 2
        poc_idx = int(np.argmax(counts))
        poc = float(bin_centers[poc_idx])
        total = counts.sum()
        counts_sorted = np.sort(counts)[::-1]
        value_area_vol = 0
        value_area_count = 0
        for c in counts_sorted:
            value_area_vol += c
            value_area_count += 1
            if value_area_vol / total >= 0.70:
                break
        idxs = np.argsort(counts)[::-1][:value_area_count]
        vals = bin_centers[idxs]
        return {
            "poc": poc,
            "value_area_high": float(vals.max()) if len(vals) else None,
            "value_area_low": float(vals.min()) if len(vals) else None,
        }

    @staticmethod
    def _supertrend(df: pd.DataFrame, period=10, multiplier=3.0) -> bool:
        """Return True if bullish supertrend, False if bearish."""
        hl2 = (df["high"] + df["low"]) / 2
        atr = df["high"].rolling(period).max() - df["low"].rolling(period).min()
        basic_upper = hl2 + multiplier * atr
        basic_lower = hl2 - multiplier * atr
        final_upper = basic_upper.copy()
        final_lower = basic_lower.copy()
        for i in range(1, len(df)):
            final_upper.iloc[i] = min(basic_upper.iloc[i], final_upper.iloc[i - 1]) if df["close"].iloc[i - 1] <= final_upper.iloc[i - 1] else basic_upper.iloc[i]
            final_lower.iloc[i] = max(basic_lower.iloc[i], final_lower.iloc[i - 1]) if df["close"].iloc[i - 1] >= final_lower.iloc[i - 1] else basic_lower.iloc[i]
        trend = df["close"] > ((final_upper + final_lower) / 2)
        return bool(trend.iloc[-1])
