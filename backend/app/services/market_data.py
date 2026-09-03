"""Market data service layer.

Fetches OHLC / quote data for forex and commodity instruments.
Primary source: Yahoo Finance (yfinance — free, no key).
Fallback: Alpha Vantage (free API key).
"""
import logging
from typing import Optional, Dict, Any, List
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.core.config import get_settings

settings = get_settings()

TIMEFRAME_MAP = {
    "M5": "5m",
    "M15": "15m",
    "M30": "30m",
    "H1": "60m",
    "H4": "60m",   # yfinance native has no 4h; we resample in analysis engine
    "D1": "1d",
    "W1": "1wk",
    "MN": "1mo",
}

PERIOD_MAP = {
    "M5": "5d",
    "M15": "5d",
    "M30": "1mo",
    "H1": "1mo",
    "H4": "3mo",
    "D1": "1y",
    "W1": "5y",
    "MN": "max",
}


def normalize_symbol(symbol: str, market_type: str) -> str:
    """Convert human-readable symbols to Yahoo Finance tickers."""
    s = symbol.upper().strip()
    if market_type == "commodity":
        known = {
            "XAUUSD": "GC=F",
            "GOLD": "GC=F",
            "XAGUSD": "SI=F",
            "SILVER": "SI=F",
            "WTI": "CL=F",
            "BRENT": "BZ=F",
            "NATGAS": "NG=F",
            "NATURAL GAS": "NG=F",
            "COPPER": "HG=F",
            "PLATINUM": "PL=F",
        }
        return known.get(s, s)
    # Forex: for currency pairs that yfinance needs (e.g., EURUSD=X)
    if "=" not in s and len(s) == 6 and s.isalpha():
        return f"{s}=X"
    return s


class MarketDataService:
    """Fetches market data from configured providers."""

    @staticmethod
    def get_quote(symbol: str, market_type: str) -> Optional[Dict[str, Any]]:
        """Get current quote for an instrument."""
        ticker = normalize_symbol(symbol, market_type)
        try:
            import yfinance as yf  # lazy import to keep startup fast
            t = yf.Ticker(ticker)
            info = t.fast_info
            return {
                "symbol": symbol,
                "ticker": ticker,
                "price": float(info.last_price),
                "open": float(info.open),
                "high": float(info.day_high),
                "low": float(info.day_low),
                "volume": int(info.last_volume),
                "currency": getattr(info, "currency", None),
            }
        except Exception as e:
            logger.error(f"yfinance quote failed for {ticker}: {e}")
            if settings.alpha_vantage_enabled:
                return MarketDataService._alpha_lookup_quote(symbol)
            return None

    @staticmethod
    def get_historical(
        symbol: str,
        market_type: str,
        timeframe: str = "H4",
    ) -> Optional[pd.DataFrame]:
        """Fetch historical OHLCV data as a DataFrame."""
        ticker = normalize_symbol(symbol, market_type)
        interval = TIMEFRAME_MAP.get(timeframe, "60m")
        period = PERIOD_MAP.get(timeframe, "3mo")
        try:
            import yfinance as yf
            df = yf.download(
                ticker,
                interval=interval,
                period=period,
                progress=False,
                auto_adjust=True,
            )
            if df is None or df.empty:
                return None
            df = df.reset_index()
            # Flatten MultiIndex columns (yfinance >= 1.x returns tuples like
            # ('Close', 'EURUSD=X')). Keep just the price-level name, lowercased.
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [str(c[0]).lower() for c in df.columns]
            else:
                df.columns = [str(c).lower() for c in df.columns]
            # Normalize date column
            if "datetime" in df.columns:
                df.rename(columns={"datetime": "date"}, inplace=True)
            # Some yfinance builds name the index 'Price'; the date col may be 'date'
            if "date" not in df.columns and "index" in df.columns:
                df.rename(columns={"index": "date"}, inplace=True)
            # If H4 requested, resample from 60m to 4h
            if timeframe == "H4":
                df = MarketDataService._resample_h4(df)
            return df
        except Exception as e:
            logger.error(f"yfinance historical failed for {ticker}: {e}")
            return None

    @staticmethod
    def _resample_h4(df: pd.DataFrame) -> pd.DataFrame:
        """Resample hourly data to 4-hour candles."""
        if "date" not in df.columns:
            return df
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        resampled = df.resample("4h").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }).dropna()
        return resampled.reset_index()

    @staticmethod
    def get_candles_json(
        symbol: str,
        market_type: str,
        timeframe: str = "H4",
        limit: int = 100,
    ) -> Optional[List[Dict[str, Any]]]:
        """Return OHLC candles as a list of dicts for the AI prompt."""
        df = MarketDataService.get_historical(symbol, market_type, timeframe)
        if df is None or df.empty:
            if settings.alpha_vantage_enabled:
                return MarketDataService._alpha_candles(symbol)
            return None
        df = df.tail(limit)
        cols = [c for c in ["date", "open", "high", "low", "close", "volume"] if c in df.columns]
        records = []
        for _, row in df[cols].iterrows():
            rec = {}
            for c in cols:
                if c == "date":
                    rec["timestamp"] = str(row[c])
                else:
                    rec[c] = float(row[c]) if pd.notna(row[c]) else None
            records.append(rec)
        return records

    # --- Alpha Vantage fallback -> placeholder stubs ---
    @staticmethod
    def _alpha_lookup_quote(symbol: str) -> Optional[Dict[str, Any]]:
        logger.warning("Alpha Vantage quote lookup not yet implemented.")
        return None

    @staticmethod
    def _alpha_candles(symbol: str) -> Optional[List[Dict[str, Any]]]:
        logger.warning("Alpha Vantage candle lookup not yet implemented.")
        return None
