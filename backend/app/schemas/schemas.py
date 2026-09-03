"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    email: str
    account_size: float = 10000.0
    risk_percent: float = 1.0
    sizing_pref: str = "lots"


class UserOut(BaseModel):
    id: int
    email: str
    account_size: float
    risk_percent: float
    sizing_pref: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisRequest(BaseModel):
    symbol: str = Field(..., description="Instrument, e.g., EURUSD, XAUUSD, CL=F")
    market_type: str = Field("forex", description="forex | commodity")
    timeframe: str = Field("H4", description="M5, M15, H1, H4, D1, W1, MN")
    account_size: float = Field(10000.0)
    risk_percent: float = Field(1.0)
    sizing_pref: str = Field("lots")
    include_news: bool = Field(True)
    question: Optional[str] = Field(None, description="Optional custom question")


class RiskRewardRequest(BaseModel):
    entry: float
    stop_loss: float
    take_profit: float
    account_size: float = 10000.0
    risk_percent: float = 1.0
    lot_size: float = 100000.0
    pip_size: float = 0.0001


class RiskRewardOut(BaseModel):
    risk_amount: float
    reward_amount: float
    rr_ratio: float
    risk_pips: float
    reward_pips: float
    position_size_units: float
    position_lots: float
    units_per_lot: float = 100000.0


class TradeSetupOut(BaseModel):
    recommendation: str
    entry: float
    stop_loss: float
    take_profits: List[float]
    rr_ratios: List[float]
    position_size: float
    confidence: int
    reasoning: str


class AnalysisOut(BaseModel):
    id: int
    symbol: str
    market_type: str
    timeframe: str
    current_price: float
    analysis_data: Dict[str, Any]
    trade_setup: Dict[str, Any]
    risk_reward: Dict[str, Any]
    confidence: int
    created_at: datetime

    class Config:
        from_attributes = True


class WatchlistAdd(BaseModel):
    symbol: str
    market_type: str = "forex"
    alerts_enabled: bool = True


class WatchlistOut(BaseModel):
    id: int
    symbol: str
    market_type: str
    alerts_enabled: bool
    price_targets: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
