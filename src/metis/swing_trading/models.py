"""
Pydantic models for swing trading signals and analysis.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class TradeDirection(str, Enum):
    """Trade direction enum."""
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


class TradingScenario(str, Enum):
    """Trading scenario types."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class ValuationSignal(BaseModel):
    """Valuation-based trading signal."""
    current_pe: float = Field(..., description="Current P/E ratio")
    peer_average_pe: float = Field(..., description="Peer average P/E ratio")
    premium_percent: float = Field(..., description="Premium/discount vs peers (%)")
    downside_potential_percent: float = Field(..., description="Downside to peer multiple (%)")
    valuation_gap_dollars: float = Field(..., description="Market cap gap in dollars")
    fair_value_target: float = Field(..., description="Fair value P/E target")
    trade_direction: TradeDirection = Field(..., description="Recommended trade direction")
    confidence: str = Field(..., description="Signal confidence (high/medium/low)")


class MomentumSignal(BaseModel):
    """Momentum-based trading signal."""
    revenue_growth_qoq: float = Field(..., description="Revenue growth QoQ (%)")
    peer_average_growth: float = Field(..., description="Peer average growth (%)")
    rank: int = Field(..., description="Rank among peers")
    trend: str = Field(..., description="Momentum trend (accelerating/decelerating/stable)")
    risk_level: str = Field(..., description="Risk level (high/medium/low)")
    interpretation: str = Field(..., description="Trading interpretation")


class HiddenStrengthSignal(BaseModel):
    """Hidden strength metric signal."""
    metric_name: str = Field(..., description="Metric name (ROE, ROA, etc.)")
    target_value: float = Field(..., description="Target company value")
    peer_average: float = Field(..., description="Peer average value")
    outperformance_magnitude: str = Field(..., description="Magnitude of outperformance")
    why_ignored: str = Field(..., description="Why Wall Street ignores this")
    valuation_impact: str = Field(..., description="Estimated P/E impact")
    trade_opportunity: str = Field(..., description="How to trade this strength")


class AnalystSentimentSignal(BaseModel):
    """Analyst sentiment signal."""
    net_sentiment: str = Field(..., description="Net sentiment (Bullish/Neutral/Bearish)")
    coverage_breadth: int = Field(..., description="Number of analysts covering")
    upgrades_90d: int = Field(..., description="Upgrades in last 90 days")
    downgrades_90d: int = Field(..., description="Downgrades in last 90 days")
    maintains_90d: int = Field(..., description="Maintains in last 90 days")
    sentiment_divergence: str = Field(..., description="Divergence from fundamentals")
    contrarian_opportunity: str = Field(..., description="Contrarian opportunity score")


class PeerRotationSignal(BaseModel):
    """Peer sector rotation signal."""
    target_symbol: str = Field(..., description="Target company symbol")
    target_pe: float = Field(..., description="Target P/E ratio")
    peer_comparisons: Dict[str, float] = Field(..., description="Peer symbol -> P/E mapping")
    relative_value_rank: int = Field(..., description="Relative value rank (1=cheapest)")
    rotation_opportunity: str = Field(..., description="Sector rotation opportunity description")
    pairs_trade_suggestion: Optional[str] = Field(None, description="Suggested pairs trade")


class CatalystEvent(BaseModel):
    """Event-driven catalyst."""
    event_type: str = Field(..., description="Catalyst type (earnings, guidance, etc.)")
    timeframe: str = Field(..., description="Expected timeframe (3-6 months, etc.)")
    trigger_description: str = Field(..., description="What triggers the catalyst")
    expected_impact: str = Field(..., description="Expected price impact")
    probability: str = Field(..., description="Probability (high/medium/low)")


class TradingScenarioSetup(BaseModel):
    """Complete trading scenario with entry/exit/targets."""
    scenario_type: TradingScenario = Field(..., description="Scenario type")
    timeframe: str = Field(..., description="Trade timeframe")
    trigger: str = Field(..., description="Entry trigger")
    entry_strategy: str = Field(..., description="Entry strategy")
    target_price_range: Optional[str] = Field(None, description="Target price/multiple range")
    stop_loss: str = Field(..., description="Stop-loss criteria")
    risk_reward_ratio: Optional[str] = Field(None, description="Estimated risk/reward")
    catalysts: List[CatalystEvent] = Field(default_factory=list, description="Related catalysts")


class SwingTradingSignals(BaseModel):
    """Complete set of swing trading signals extracted from competitive intelligence report."""
    target_symbol: str = Field(..., description="Target company symbol")
    target_company_name: str = Field(..., description="Target company name")
    analysis_date: str = Field(..., description="Analysis date")
    
    valuation_signal: ValuationSignal = Field(..., description="Valuation-based signal")
    momentum_signal: MomentumSignal = Field(..., description="Momentum signal")
    hidden_strengths: List[HiddenStrengthSignal] = Field(default_factory=list, description="Hidden strength signals")
    analyst_sentiment: AnalystSentimentSignal = Field(..., description="Analyst sentiment signal")
    peer_rotation: PeerRotationSignal = Field(..., description="Peer rotation signal")
    
    trading_scenarios: List[TradingScenarioSetup] = Field(default_factory=list, description="Trading scenario setups")
    
    overall_bias: TradeDirection = Field(..., description="Overall directional bias")
    risk_level: str = Field(..., description="Overall risk level (high/medium/low)")
    conviction_score: int = Field(..., ge=1, le=10, description="Conviction score (1-10)")
    
    key_levels: Dict[str, float] = Field(
        default_factory=dict,
        description="Key price levels (support, resistance, fair_value)"
    )
    
    summary: str = Field(..., description="Executive summary for traders")
