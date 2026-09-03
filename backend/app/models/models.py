"""SQLAlchemy ORM models matching the plan's database schema."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    account_size = Column(Float, default=10000.0)
    risk_percent = Column(Float, default=1.0)
    sizing_pref = Column(String(20), default="lots")
    preferences = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    analyses = relationship("MarketAnalysis", back_populates="user")
    watchlist = relationship("WatchlistItem", back_populates="user")


class MarketAnalysis(Base):
    __tablename__ = "market_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    symbol = Column(String(20), index=True)
    market_type = Column(String(20))  # forex | commodity
    timeframe = Column(String(10))
    current_price = Column(Float, nullable=True)
    analysis_data = Column(JSON, default=dict)
    trade_setup = Column(JSON, default=dict)
    risk_reward = Column(JSON, default=dict)
    confidence = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="analyses")
    history = relationship("AnalysisHistory", back_populates="analysis", uselist=False)


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("market_analyses.id"))
    performance = Column(JSON, default=dict)
    outcome = Column(String(20), default="pending")  # win | loss | breakeven | pending

    analysis = relationship("MarketAnalysis", back_populates="history")


class WatchlistItem(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    symbol = Column(String(20), index=True)
    market_type = Column(String(20))
    alerts_enabled = Column(Boolean, default=True)
    price_targets = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="watchlist")
