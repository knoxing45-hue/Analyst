"""News service.

Fetches relevant recent headlines/events for the instrument to include in
the AI prompt context. Uses a lightweight approach with yfinance news where
available; otherwise returns a placeholder signal list.
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class NewsService:
    @staticmethod
    def get_news(symbol: str, market_type: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch recent news for an instrument."""
        try:
            import yfinance as yf
            from app.services.market_data import normalize_symbol
            ticker = normalize_symbol(symbol, market_type)
            news = yf.Ticker(ticker).news
            if news:
                items = []
                for n in news[:limit]:
                    items.append({
                        "title": n.get("title", ""),
                        "publisher": n.get("publisher", ""),
                        "link": n.get("link", ""),
                        "timestamp": n.get("providerPublishTime"),
                    })
                return items
        except Exception as e:
            logger.warning(f"News fetch failed for {symbol}: {e}")
        return []

    @staticmethod
    def news_to_text(news: List[Dict[str, Any]]) -> str:
        if not news:
            return "None provided."
        lines = []
        for n in news:
            lines.append(f"- {n.get('title')} ({n.get('publisher')})")
        return "\n".join(lines)
