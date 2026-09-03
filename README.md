<<<<<<< HEAD
# ============================================================
# MARKET ANALYSIS AGENT 
# AI-powered forex & commodity market analysis
# ============================================================

## Overview
A web application that analyzes forex and commodity markets using a deep
technical-analysis pipeline (structure, volatility, volume, indicators, risk/
reward, trade setups) combined with a DeepSeek LLM agent for institutional-grade
reasoning and high-probability trade setups.

## Project Structure
```
market-analysis-agent/
├── backend/                 # Python FastAPI service
│   ├── app/
│   │   ├── core/            # config, database
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── routes/          # API routes
│   │   └── services/        # market data, indicators, structure,
│   │                        #   risk/reward, agent (DeepSeek), mock
│   ├── tests/               # unit tests
│   └── requirements.txt
├── frontend/                # React (Vite) client
│   └── src/
│       ├── components/      # Sidebar, ChartView
│       ├── pages/           # AnalysisPage
│       └── services/        # API client
└── prompts/
    └── master_agent_prompt.md   # Full DeepSeek system prompt
```

## Quick Start

### 1. Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# EDIT .env → set DEEPSEEK_API_KEY (required for full AI mode)
uvicorn app.main:app --reload --port 8000
```
- API docs: http://localhost:8000/docs
- Runs in **mock mode** if no DeepSeek key is set (still computes real indicators/structure and a trade plan from real Yahoo Finance data).

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```
- Open http://localhost:5173
- Vite proxies `/api` → localhost:8000.

### 3. Requirements
- **Python 3.10+** and Node 18+
- **DeepSeek API key** (https://platform.deepseek.com) — makes the AI analysis real instead of mock.
- Optionally an **Alpha Vantage** key for a fallback data source.

## API Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Health check |
| GET | `/api/market/{symbol}/quote` | Current quote |
| GET | `/api/market/{symbol}/historical` | OHLC candles |
| POST | `/api/analysis/analyze` | Full AI analysis |
| POST | `/api/trade/calculate-risk-reward` | Manual R:R calc |
| POST | `/api/trade/suggest-setup` | AI trade plan |
| GET | `/api/analysis/history` | Past analyses |
| CRUD | `/api/watchlist` | Watchlist management |

## How the Analysis Pipeline Works
1. **MarketDataService** fetches OHLCV from Yahoo Finance.
2. **AnalysisEngine** computes indicators (ADX, RSI, MACD, ATR, Bollinger, Stoch, CCI, OBV, VWAP, Volume Profile).
3. **StructureDetector** finds swing highs/lows, BOS/CHoCH, order blocks, fair value gaps, liquidity pools, psychological levels, and classifies the regime.
4. **RiskRewardCalculator** sizes positions and computes R:R ladders.
5. **AgentService** sends all of this + the master prompt to DeepSeek for reasoned analysis.
6. If no DeepSeek key, **mock_analysis** produces a deterministic demo result.

## Configuration (.env)
See `backend/.env.example` for all options. The key ones:
- `DEEPSEEK_API_KEY` — required for full AI reasoning
- `DEEPSEEK_MODEL` — e.g., `deepseek-chat`
- `DATABASE_URL` — default SQLite; use PostgreSQL for production
- `ALPHA_VANTAGE_API_KEY` — optional fallback data source

## Customizing the AI
Edit `prompts/master_agent_prompt.md` — it is loaded at runtime by the backend as
the DeepSeek system prompt. Modify the analysis framework, output format, risk
rules, or markets covered there.

## Tests
```bash
cd backend && source venv/bin/activate
python -m unittest discover -s tests
```

## Disclaimer
Trading forex and commodities carries a high level of risk. This software is for
educational purposes only and does not provide financial advice. Only trade with
capital you can afford to lose.
=======
# Analyst
markets and agents
>>>>>>> aeb95167eaa8b397801bb3e760a7f5792b642c70
