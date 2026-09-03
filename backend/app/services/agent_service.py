"""DeepSeek AI agent service.

Loads the master prompt (from prompts/master_agent_prompt.md), builds the
runtime-variable-injected analysis prompt, calls the DeepSeek API, and parses
the structured response.
"""
import json
import logging
import os
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.core.config import get_settings

settings = get_settings()

PROMPT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "prompts")
MASTER_PROMPT_PATH = os.path.abspath(os.path.join(PROMPT_DIR, "master_agent_prompt.md"))

# Simple fallback in case the file isn't found
DEFAULT_MASTER_PROMPT = """
You are an elite financial market analyst specializing in FOREX and COMMODITY markets.
Follow the full analysis framework: regime detection -> market structure -> key levels ->
indicator confluence -> scenarios -> risk/reward -> invalidation -> confidence.
Always append the standard risk disclaimer. Be precise with numbers; never fabricate data.
"""


class AgentService:
    HARD_LIMIT = 4000  # Limit candles passed to the model to avoid token blowout

    @staticmethod
    def load_master_prompt() -> str:
        """Load the master system prompt from disk."""
        try:
            with open(MASTER_PROMPT_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"Master prompt not found at {MASTER_PROMPT_PATH}, using default.")
            return DEFAULT_MASTER_PROMPT

    @staticmethod
    def _client():
        from openai import OpenAI
        return OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )

    @staticmethod
    def build_user_message(params: Dict[str, Any]) -> str:
        """Construct the user-turn analysis prompt with runtime data injected."""
        user_request = params.get("question") or (
            f"Provide a full analysis and identify the highest-probability trade setup "
            f"on {params['symbol']} ({params['market_type']}) on the {params['timeframe']} timeframe."
        )
        candles = params.get("candles", [])
        if candles and len(candles) > AgentService.HARD_LIMIT:
            candles = candles[-AgentService.HARD_LIMIT:]

        return f"""[ANALYSIS REQUEST]
{user_request}

[INSTRUMENT]
Symbol: {params.get('symbol')}
Market Type: {params.get('market_type')}
Timeframe: {params.get('timeframe')}
Current Price: {params.get('current_price', 'N/A')}

[OHLC DATA]
```json
{json.dumps(candles, indent=2)}
```

[INDICATORS]
```json
{json.dumps(params.get('indicators', {}), indent=2, default=str)}
```

[MARKET STRUCTURE / LEVELS]
```json
{json.dumps(params.get('structure', {}), indent=2, default=str)}
```

[CORRELATIONS / CONTEXT]
{params.get('correlations', 'None provided.')}

[RECENT NEWS]
{params.get('news', 'None provided.')}

[ACCOUNT PARAMETERS]
Account Size: ${params.get('account_size', 10000)}
Risk Tolerance: {params.get('risk_percent', 1.0)}%
Position Sizing Preference: {params.get('sizing_pref', 'lots')}

Analyze using the complete framework and return the standard structured output format.
"""

    @staticmethod
    def run_analysis(params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a full analysis through DeepSeek and return the structured result."""
        api_key = settings.deepseek_api_key
        if not api_key or api_key == "your-deepseek-api-key-here":
            logger.error("DeepSeek API key not configured.")
            return {
                "error": "DeepSeek API key not configured. Set DEEPSEEK_API_KEY in .env",
                "mock": True,
            }

        client = AgentService._client()
        system = AgentService.load_master_prompt()
        user = AgentService.build_user_message(params)

        logger.info("Calling DeepSeek API...")
        try:
            response = client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.3,
                max_tokens=4000,
            )
            content = response.choices[0].message.content
            return {
                "content": content,
                "mock": False,
                "usage": response.usage.model_dump() if response.usage else None,
            }
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            return {"error": str(e), "mock": False}
