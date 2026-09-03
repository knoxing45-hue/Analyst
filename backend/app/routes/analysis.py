"""API routes for market data, analysis, trade setup, and watchlist."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import (
    AnalysisRequest,
    AnalysisOut,
    RiskRewardRequest,
    RiskRewardOut,
    WatchlistAdd,
    WatchlistOut,
)
from app.services.market_data import MarketDataService
from app.services.risk_reward import RiskRewardCalculator
from app.services.analyzer import AnalysisOrchestrator
from app.models.models import MarketAnalysis, WatchlistItem

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/market/{symbol}/quote")
def get_quote(symbol: str, market_type: str = "forex"):
    quote = MarketDataService.get_quote(symbol, market_type)
    if quote is None:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote


@router.get("/market/{symbol}/historical")
def get_historical(
    symbol: str,
    market_type: str = "forex",
    timeframe: str = "H4",
    limit: int = 100,
):
    candles = MarketDataService.get_candles_json(symbol, market_type, timeframe, limit)
    if candles is None:
        raise HTTPException(status_code=404, detail="No data found")
    return {"symbol": symbol, "timeframe": timeframe, "candles": candles}


@router.post("/analysis/analyze")
def analyze(req: AnalysisRequest):
    """Run a full AI market analysis."""
    try:
        result = AnalysisOrchestrator.run(
            symbol=req.symbol,
            market_type=req.market_type,
            timeframe=req.timeframe,
            account_size=req.account_size,
            risk_percent=req.risk_percent,
            sizing_pref=req.sizing_pref,
            include_news=req.include_news,
            question=req.question,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trade/calculate-risk-reward", response_model=RiskRewardOut)
def calculate_risk_reward(req: RiskRewardRequest):
    """Compute risk/reward for a manual setup."""
    try:
        result = RiskRewardCalculator.calculate(
            entry=req.entry,
            stop_loss=req.stop_loss,
            take_profit=req.take_profit,
            account_size=req.account_size,
            risk_percent=req.risk_percent,
            units_per_lot=req.lot_size,
            pip_size=req.pip_size,
        )
        return RiskRewardOut(
            risk_amount=result["risk_amount"],
            reward_amount=result["reward_amount"],
            rr_ratio=result["rr_ratio"],
            risk_pips=result["risk_pips"],
            reward_pips=result["reward_pips"],
            position_size_units=result["position_size_units"],
            position_lots=result["position_lots"],
            units_per_lot=result["units_per_lot"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/trade/suggest-setup")
def suggest_setup(req: AnalysisRequest):
    """Return a structured trade plan from an AI analysis."""
    result = AnalysisOrchestrator.run(
        symbol=req.symbol,
        market_type=req.market_type,
        timeframe=req.timeframe,
        account_size=req.account_size,
        risk_percent=req.risk_percent,
        sizing_pref=req.sizing_pref,
        include_news=req.include_news,
        question="Provide the highest-probability trade setup with exact levels.",
    )
    return {"trade_setup": result.get("trade_setup"), "confidence": result.get("confidence")}


@router.get("/analysis/history")
def analysis_history(db: Session = Depends(get_db)):
    items = db.query(MarketAnalysis).order_by(MarketAnalysis.created_at.desc()).limit(50).all()
    return [
        {
            "id": a.id,
            "symbol": a.symbol,
            "market_type": a.market_type,
            "timeframe": a.timeframe,
            "confidence": a.confidence,
            "created_at": a.created_at,
        }
        for a in items
    ]


@router.post("/watchlist")
def add_to_watchlist(req: WatchlistAdd, db: Session = Depends(get_db)):
    existing = db.query(WatchlistItem).filter(
        WatchlistItem.symbol == req.symbol.upper()
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Symbol already in watchlist")
    item = WatchlistItem(
        symbol=req.symbol.upper(),
        market_type=req.market_type,
        alerts_enabled=req.alerts_enabled,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/watchlist")
def get_watchlist(db: Session = Depends(get_db)):
    items = db.query(WatchlistItem).all()
    return items


@router.delete("/watchlist/{symbol}")
def remove_from_watchlist(symbol: str, db: Session = Depends(get_db)):
    item = db.query(WatchlistItem).filter(
        WatchlistItem.symbol == symbol.upper()
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return {"status": "removed"}
