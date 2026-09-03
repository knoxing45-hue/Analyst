# ============================================================
# DEEPSEEK ANALYSIS PROMPT — FULL MARKET ANALYSIS
# Injected when a user requests analysis of a specific symbol.
# Replace {placeholders} with actual data from the backend.
# ============================================================

PREAMBLE:
You are performing a comprehensive institutional-grade analysis of the following instrument. Apply your full analysis framework (regime → structure → levels → indicators → scenarios → risk/reward → invalidation → confidence). Return the result in your standard structured output format.

---

## MARKET DATA

**Symbol:** {symbol}
**Market Type:** {market_type}            (forex | commodity)
**Timeframe:** {timeframe}                (e.g., M5, M15, H1, H4, D1)
**Analysis Requested At:** {analysis_time}
**Current Price:** {current_price}

### OHLC DATA (Last {n} candles)
```json
{ohlc_data_json}
```

### INDICATOR VALUES
```json
{indicators_json}
# Expected keys when available:
# - ADX, RSI14, MACD (macd, signal, hist)
# - EMA20, EMA50, EMA200
# - ATR14, BollingerBands (upper, middle, lower)
# - Stochastic, CCI
# - OBV, VWAP, VolumeProfile (POC, value_area_high, value_area_low)
```

### VOLUME DATA
```json
{volume_json}
```

### RECENT RELEVANT NEWS / EVENTS
```
{news_summary}
```

### ACCOUNT PARAMETERS
**Account Size:** ${account_size}
**Default Risk Tolerance:** {risk_percent}%
**Position Sizing Preference:** {sizing_pref}   (lots | %account | units)

### CORRELATED MARKET CONTEXT (if applicable)
```
{correlations}
# e.g., for XAU/USD: current DXY (dollar index), 10Y treasury yields
# for EUR/USD: EUR/JPY cross, DXY, EUR/GBP
```

---

## ANALYSIS INSTRUCTIONS

Follow this EXACT sequence. Do not skip steps. Show your reasoning at each step.

### STEP 1 — REGIME DETECTION
Classify the market regime using the ATR and price structure (trending/ranging/volatile/transition). State evidence:
- ATR relative to recent average
- Whether price is inside or outside Bollinger Bands
- Consecutive higher/lower closes

### STEP 2 — STRUCTURE
- Identify swing highs/swing lows (last 2-3 visible each way)
- Note any recent BOS or CHoCH and its significance
- Mark order blocks, fair value gaps, liquidity pools

### STEP 3 — KEY LEVELS
Produce a table of the most relevant levels (max 8). Include:
- Major S/R, minor S/R, psychological, previous day/week high/low, premium/discount zones

### STEP 4 — INDICATOR CONFLUENCE
For each indicator group (trend, momentum, volatility, volume), report:
- The raw reading
- The interpretation (bullish/bearish/neutral)
- Any divergences (price vs momentum, price vs volume)
- Whether the group is in alignment or disagreement

### STEP 5 — SCENARIOS
Three scenarios with trigger conditions and price targets:
- Bullish: what must happen to confirm, upside targets
- Bearish: what must happen to confirm, downside targets
- Base: the consolidation range if neither confirmation occurs

### STEP 6 — TRADE SETUP
Only if a valid setup exists (structure + confluence + R:R >= 1:1.5):
- Entry price and order type (limit/market)
- Stop loss — must be BEYOND structure, justify with the specific level
- TP1, TP2, TP3 with suggested partial-close percentages (e.g., 40%/30%/30%)
- Exact R:R for each target
- Position size in user's preferred units based on account and risk %
If NO valid setup exists, explicitly state "NO TRADE — [reason]" and do not force a recommendation.

### STEP 7 — INVALIDATION
Give the exact price that invalidates the thesis and the reason.

### STEP 8 — CONFIDENCE + RISK WARNINGS
- Confidence score 1-100% with justification
- Warn about upcoming high-impact news within ±4 hours
- Note correlation risks (e.g., dollar moves, gold inverse correlation)
- Always append the standard risk disclaimer

---

## OUTPUT

Return your analysis in the structured markdown format defined in your system prompt (## EXECUTIVE SUMMARY through ## RISK WARNINGS). Be precise with numbers. Do NOT invent data that was not provided — if an indicator is missing, note it and adjust confidence accordingly.

---

## RISK DISCLAIMER (Always include at the end)
"Trading foreign exchange and commodities carries a high level of risk and may not be suitable for all investors. Past performance is not indicative of future results. This analysis is for educational purposes only and is not financial advice. Only trade with capital you can afford to lose."
