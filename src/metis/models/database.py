"""Database models for Metis."""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, 
    DECIMAL, Date, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class CompetitiveIntelligenceReport(Base):
    """Stores competitive intelligence reports."""
    
    __tablename__ = "competitive_intelligence_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_symbol = Column(String(10), nullable=False)
    report_date = Column(Date, nullable=False)
    peer_symbols = Column(JSONB, nullable=False)  # ["PGR", "CB", "TRV", "HIG"]
    report_data = Column(JSONB, nullable=False)   # Full report structure
    processing_time_seconds = Column(Integer)
    blog_url = Column(Text)
    client_id = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index("idx_target_symbol", "target_symbol"),
        Index("idx_report_date", "report_date"),
        Index("idx_client_id", "client_id"),
        Index("idx_target_date", "target_symbol", "report_date"),
    )


class CompanyMetricsHistory(Base):
    """Stores individual company metrics for time-series analysis."""
    
    __tablename__ = "company_metrics_history"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False)
    metric_date = Column(Date, nullable=False)
    pe_ratio = Column(DECIMAL(5, 2))
    market_cap_billions = Column(DECIMAL(8, 2))
    roe = Column(DECIMAL(5, 2))
    roa = Column(DECIMAL(5, 2))
    revenue_growth = Column(DECIMAL(5, 2))
    debt_to_equity = Column(DECIMAL(5, 2))
    gross_margin = Column(DECIMAL(5, 2))
    operating_margin = Column(DECIMAL(5, 2))
    free_cash_flow_margin = Column(DECIMAL(5, 2))
    
    # Sector-specific metrics (nullable)
    combined_ratio = Column(DECIMAL(5, 2))  # Insurance
    reserve_development = Column(DECIMAL(5, 2))  # Insurance
    net_interest_margin = Column(DECIMAL(5, 2))  # Banking
    efficiency_ratio = Column(DECIMAL(5, 2))  # Banking
    
    # Sentiment and narrative scores
    management_sentiment_score = Column(Integer)  # 0-100
    analyst_confusion_score = Column(Integer)  # 0-100
    narrative_effectiveness_score = Column(Integer)  # 0-100
    
    # Earnings call metrics
    earnings_call_word_count = Column(Integer)
    tech_mention_frequency = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_symbol_date", "symbol", "metric_date"),
        Index("idx_metric_date", "metric_date"),
    )


class LinguisticPattern(Base):
    """Stores linguistic patterns extracted from earnings calls."""
    
    __tablename__ = "linguistic_patterns"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False)
    call_date = Column(Date, nullable=False)
    phrase = Column(Text, nullable=False)
    frequency = Column(Integer, nullable=False)  # Mentions per 1000 words
    context = Column(Text)  # Surrounding sentences
    sentiment_score = Column(DECIMAL(3, 2))  # -1.0 to 1.0
    category = Column(String(50))  # tech_terms, growth_terms, risk_terms
    
    # Event study correlation
    correlated_pe_change = Column(DECIMAL(5, 2))  # P/E change after earnings
    abnormal_return_1d = Column(DECIMAL(5, 4))
    abnormal_return_3d = Column(DECIMAL(5, 4))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_symbol_call_date", "symbol", "call_date"),
        Index("idx_phrase", "phrase"),
        Index("idx_category", "category"),
    )


class PeerGroupDefinition(Base):
    """Stores peer group definitions and overrides."""
    
    __tablename__ = "peer_group_definitions"
    
    id = Column(Integer, primary_key=True)
    target_symbol = Column(String(10), nullable=False)
    peer_symbol = Column(String(10), nullable=False)
    similarity_score = Column(DECIMAL(3, 2))
    selection_method = Column(String(20))  # auto, manual, client_override
    reason = Column(Text)  # Why this peer was selected
    active = Column(Boolean, default=True)
    client_id = Column(String(50))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index("idx_target_peer", "target_symbol", "peer_symbol"),
        Index("idx_target_active", "target_symbol", "active"),
    )


class EventStudyResult(Base):
    """Stores event study analysis results."""
    
    __tablename__ = "event_study_results"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False)
    event_date = Column(Date, nullable=False)
    event_type = Column(String(50), default="earnings_call")
    
    # Returns
    car_1d = Column(DECIMAL(6, 4))  # Cumulative abnormal return 1-day
    car_3d = Column(DECIMAL(6, 4))  # Cumulative abnormal return 3-day
    car_5d = Column(DECIMAL(6, 4))  # Cumulative abnormal return 5-day
    
    # Model used
    model_type = Column(String(20))  # market_model, fama_french, carhart
    benchmark_return = Column(DECIMAL(6, 4))
    
    # Controls
    earnings_surprise = Column(DECIMAL(5, 2))  # Actual vs consensus EPS
    revenue_surprise = Column(DECIMAL(5, 2))  # Actual vs consensus revenue
    guidance_change = Column(String(20))  # raised, lowered, maintained
    
    # Market conditions
    vix_level = Column(DECIMAL(5, 2))
    sector_return = Column(DECIMAL(6, 4))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_symbol_event_date", "symbol", "event_date"),
        Index("idx_event_date", "event_date"),
    )


class ClientTokenUsage(Base):
    """Tracks OpenAI token usage per client."""
    
    __tablename__ = "client_token_usage"
    
    id = Column(Integer, primary_key=True)
    client_id = Column(String(50), nullable=False)
    month = Column(Date, nullable=False)  # First day of month
    
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost_cents = Column(Integer, default=0)
    
    reports_generated = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index("idx_client_month", "client_id", "month"),
    )


class LLMCache(Base):
    """Caches LLM responses to reduce costs."""
    
    __tablename__ = "llm_cache"
    
    id = Column(Integer, primary_key=True)
    prompt_hash = Column(String(64), nullable=False, unique=True)  # SHA256
    context_hash = Column(String(64))  # Hash of input context
    model = Column(String(50), nullable=False)
    
    response = Column(JSONB, nullable=False)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    cost_cents = Column(Integer)
    
    # TTL management
    expires_at = Column(DateTime(timezone=True), nullable=False)
    hit_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_prompt_hash", "prompt_hash"),
        Index("idx_expires_at", "expires_at"),
    )