"""Analysis orchestrator.

Coordinates market data -> indicator computation -> structure detection ->
AI (DeepSeek or mock) -> persistence to the database.
"""
import logging
from typing import Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

from app.services.market_data import MarketDataService, normalize_symbol
from app.services.technical_analysis import AnalysisEngine
from app.services.structure import StructureDetector
from app.services.risk_reward import RiskRewardCalculator, get_pip_size
from app.services.agent_service import AgentService
from app.services.mock_analysis import generate_mock_analysis
from app.services.news_service import NewsService


class AnalysisOrchestrator:
    @staticmethod
    def run(
        symbol: str,
        market_type: str,
        timeframe: str = "H4",
        account_size: float = 10000.0,
        risk_percent: float = 1.0,
        sizing_pref: str = "lots",
        include_news: bool = True,
        question: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute the full analysis pipeline."""
        # 1. Fetch data
        df = MarketDataService.get_historical(symbol, market_type, timeframe)
        if df is None or df.empty:
            return {"error": f"No market data found for {symbol} on {timeframe} timeframe."}

        quote = MarketDataService.get_quote(symbol, market_type)
        current_price = float(df["close"].iloc[-1])

        # 2. Compute indicators
        indicators = AnalysisEngine.compute_indicators(df)

        # 3. Detect structure
        structure = StructureDetector.run(df, indicators)

        # 4. Prepare candles for AI
        candles = MarketDataService.get_candles_json(
            symbol, market_type, timeframe, limit=60
        )

        # 5. Correlations context
        correlations = AnalysisOrchestrator._correlation_context(market_type)

        # 6. News
        news_list = NewsService.get_news(symbol, market_type) if include_news else []
        news_text = NewsService.news_to_text(news_list)

        # 7. Build params and call AI
        params = {
            "symbol": normalize_symbol(symbol, market_type),
            "market_type": market_type,
            "timeframe": timeframe,
            "current_price": current_price,
            "candles": candles or [],
            "indicators": indicators,
            "structure": structure,
            "correlations": correlations,
            "news": news_text,
            "account_size": account_size,
            "risk_percent": risk_percent,
            "sizing_pref": sizing_pref,
            "question": question,
        }

        # 8. Run via DeepSeek; fall back to mock if key missing
        result = AgentService.run_analysis(params)
        if result.get("error"):
            logger.info("DeepSeek unavailable, using mock analysis.")
            result = generate_mock_analysis(
                symbol=symbol,
                market_type=market_type,
                timeframe=timeframe,
                current_price=current_price,
                indicators=indicators,
                structure=structure,
                account_size=account_size,
                risk_percent=risk_percent,
                question=question or "",
            )
        else:
            result["mock"] = False

        # 9. Augment with computed trade data (for structured UI)
        trade_setup = AnalysisOrchestrator._extract_setup_from_text(
            result.get("analysis", {}).get("trade_setup", {})
        )
        if not trade_setup:
            trade_setup = result.get("trade_setup", {})

        return {
            "symbol": symbol,
            "ticker": normalize_symbol(symbol, market_type),
            "market_type": market_type,
            "timeframe": timeframe,
            "current_price": current_price,
            "quote": quote,
            "indicators": indicators,
            "structure": structure,
            "ai_output": result.get("content"),
            "analysis": result.get("analysis", {}),
            "trade_setup": trade_setup,
            "confidence": result.get("confidence")
            or (result.get("analysis", {}) or {}).get("confidence", 50),
            "mock": result.get("mock", True),
            "news": news_list,
        }

    @staticmethod
    def _correlation_context(market_type: str) -> str:
        if market_type == "commodity":
            return (
                "Primary drivers: US Dollar Index (DXY), 10-year Treasury yields, "
                "and dollar-denominated pricing. Monitor USD strength as an inverse "
                "correlation for most commodities."
            )
        return (
            "Context: monitor the US Dollar Index (DXY), central bank policy stance, "
            "and note that USD/JPY acts as a risk-proxy. Session timing matters "
            "(Asia/London/New York overlap)."
        )

    @staticmethod
    def _extract_setup_from_text(setup: Any) -> Dict[str, Any]:
        """Best-effort extraction of a structured setup if the AI returned text."""
        if isinstance(setup, dict) and setup:
            return setup
        return {}
