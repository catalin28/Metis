"""
Signal Extractor - Converts competitive intelligence JSON into trading signals.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from .models import (
    SwingTradingSignals,
    ValuationSignal,
    MomentumSignal,
    HiddenStrengthSignal,
    AnalystSentimentSignal,
    PeerRotationSignal,
    CatalystEvent,
    TradingScenarioSetup,
    TradeDirection,
    TradingScenario
)


class SignalExtractor:
    """Extracts actionable trading signals from competitive intelligence reports."""
    
    def __init__(self, report_data: Dict[str, Any]):
        """
        Initialize with competitive intelligence report JSON.
        
        Args:
            report_data: Parsed JSON report from competitive_intelligence_orchestrator
        """
        self.data = report_data
        self.target_symbol = report_data.get('target_symbol', '')
        self.valuation_context = report_data.get('valuation_context', {})
        self.dashboard = report_data.get('section_2_competitive_dashboard', {})
        self.analyst_data = report_data.get('section_2_5_analyst_consensus', {})
        self.hidden_strengths_data = report_data.get('section_3_hidden_strengths', {})
    
    def extract_all_signals(self) -> SwingTradingSignals:
        """Extract complete set of trading signals."""
        
        target_company = self.data.get('peer_group', {}).get('target_company', {})
        
        return SwingTradingSignals(
            target_symbol=self.target_symbol,
            target_company_name=target_company.get('company_name', 'Unknown'),
            analysis_date=datetime.now().strftime('%Y-%m-%d'),
            valuation_signal=self._extract_valuation_signal(),
            momentum_signal=self._extract_momentum_signal(),
            hidden_strengths=self._extract_hidden_strengths(),
            analyst_sentiment=self._extract_analyst_sentiment(),
            peer_rotation=self._extract_peer_rotation_signal(),
            trading_scenarios=self._generate_trading_scenarios(),
            overall_bias=self._determine_overall_bias(),
            risk_level=self._assess_risk_level(),
            conviction_score=self._calculate_conviction_score(),
            key_levels=self._identify_key_levels(),
            summary=self._generate_summary()
        )
    
    def _extract_valuation_signal(self) -> ValuationSignal:
        """Extract valuation-based trading signal."""
        current_pe = self.valuation_context.get('current_pe', 0)
        peer_pe = self.valuation_context.get('peer_average_pe', 0)
        premium = self.valuation_context.get('premium_vs_peer_percent', 0)
        downside = self.valuation_context.get('downside_to_peer_multiple_percent', 0)
        gap_dollars = self.valuation_context.get('valuation_gap_dollars', 0)
        
        # Determine trade direction
        if premium > 10:
            direction = TradeDirection.SHORT
            confidence = "high" if premium > 20 else "medium"
        elif premium < -10:
            direction = TradeDirection.LONG
            confidence = "high" if premium < -20 else "medium"
        else:
            direction = TradeDirection.NEUTRAL
            confidence = "low"
        
        return ValuationSignal(
            current_pe=current_pe,
            peer_average_pe=peer_pe,
            premium_percent=premium,
            downside_potential_percent=downside,
            valuation_gap_dollars=gap_dollars,
            fair_value_target=peer_pe,
            trade_direction=direction,
            confidence=confidence
        )
    
    def _extract_momentum_signal(self) -> MomentumSignal:
        """Extract momentum-based trading signal."""
        # Find revenue growth metric
        metrics = self.dashboard.get('metrics', [])
        revenue_growth_metric = next(
            (m for m in metrics if m.get('metric_name') == 'Revenue Growth'),
            {}
        )
        
        target_growth = revenue_growth_metric.get('target_value', 0)
        peer_values = revenue_growth_metric.get('peer_values', {})
        peer_avg = sum(peer_values.values()) / len(peer_values) if peer_values else 0
        rank = revenue_growth_metric.get('target_rank', 0)
        
        # Determine trend
        if target_growth > peer_avg and target_growth > 0:
            trend = "accelerating"
            risk = "low"
            interpretation = "Positive momentum - growth exceeds peers"
        elif target_growth < 0 and peer_avg > 0:
            trend = "decelerating"
            risk = "high"
            interpretation = "Negative momentum - vulnerable to downgrades"
        else:
            trend = "stable"
            risk = "medium"
            interpretation = "Neutral momentum - in line with peers"
        
        return MomentumSignal(
            revenue_growth_qoq=target_growth,
            peer_average_growth=peer_avg,
            rank=rank,
            trend=trend,
            risk_level=risk,
            interpretation=interpretation
        )
    
    def _extract_hidden_strengths(self) -> List[HiddenStrengthSignal]:
        """Extract hidden strength signals."""
        strengths = self.hidden_strengths_data.get('strengths', [])
        
        signals = []
        for strength in strengths:
            signals.append(HiddenStrengthSignal(
                metric_name=strength.get('metric_name', ''),
                target_value=strength.get('target_value', 0),
                peer_average=strength.get('peer_average', 0),
                outperformance_magnitude=strength.get('outperformance_magnitude', ''),
                why_ignored=strength.get('why_wall_street_ignores', ''),
                valuation_impact=strength.get('valuation_impact', ''),
                trade_opportunity=self._interpret_strength_for_trading(strength)
            ))
        
        return signals
    
    def _interpret_strength_for_trading(self, strength: Dict[str, Any]) -> str:
        """Interpret how to trade a hidden strength."""
        metric = strength.get('metric_name', '').lower()
        
        if 'roe' in metric or 'roa' in metric:
            return "Wait for pullback to peer multiple, then enter long on quality premium"
        elif 'growth' in metric:
            return "Buy on earnings dip if growth sustains; use as stop-loss trigger if growth turns negative"
        elif 'margin' in metric:
            return "Long on multiple compression events; margin strength should support recovery"
        else:
            return "Monitor for catalyst to unlock value recognition"
    
    def _extract_analyst_sentiment(self) -> AnalystSentimentSignal:
        """Extract analyst sentiment signal."""
        target_analysis = self.analyst_data.get('target_analysis', {})
        
        upgrades = target_analysis.get('upgrades_90d', 0)
        downgrades = target_analysis.get('downgrades_90d', 0)
        maintains = target_analysis.get('maintains_90d', 0)
        
        # Calculate divergence from fundamentals
        overall_rank = self.dashboard.get('overall_target_rank', 0)
        sentiment = target_analysis.get('net_sentiment', 'Neutral')
        
        if overall_rank <= 2 and sentiment == 'Neutral':
            divergence = "Strong fundamentals but neutral sentiment - underappreciated"
        elif overall_rank >= 3 and sentiment in ['Bullish', 'Positive']:
            divergence = "Weak fundamentals but positive sentiment - overvalued"
        else:
            divergence = "Sentiment aligned with fundamentals"
        
        return AnalystSentimentSignal(
            net_sentiment=sentiment,
            coverage_breadth=target_analysis.get('coverage_breadth', 0),
            upgrades_90d=upgrades,
            downgrades_90d=downgrades,
            maintains_90d=maintains,
            sentiment_divergence=divergence,
            contrarian_opportunity=self.analyst_data.get('contrarian_opportunity_score', 'Medium')
        )
    
    def _extract_peer_rotation_signal(self) -> PeerRotationSignal:
        """Extract peer sector rotation signal."""
        current_pe = self.valuation_context.get('current_pe', 0)
        
        # Get peer P/E ratios
        metrics = self.dashboard.get('metrics', [])
        pe_metric = next((m for m in metrics if m.get('metric_name') == 'P/E Ratio'), {})
        peer_pes = pe_metric.get('peer_values', {})
        
        # Calculate relative value rank
        all_pes = {self.target_symbol: current_pe, **peer_pes}
        sorted_pes = sorted(all_pes.items(), key=lambda x: x[1])
        rank = next((i + 1 for i, (sym, _) in enumerate(sorted_pes) if sym == self.target_symbol), 0)
        
        # Generate rotation opportunity text
        if rank == 1:
            rotation_text = f"{self.target_symbol} is cheapest in peer group - potential mean reversion play"
        elif rank == len(all_pes):
            rotation_text = f"{self.target_symbol} is most expensive - vulnerable to sector rotation"
        else:
            rotation_text = f"{self.target_symbol} is mid-pack valuation - monitor for catalyst"
        
        # Suggest pairs trade
        cheapest_peer = sorted_pes[0][0]
        most_expensive_peer = sorted_pes[-1][0]
        if self.target_symbol == most_expensive_peer and len(sorted_pes) > 1:
            pairs_trade = f"Long {cheapest_peer} / Short {self.target_symbol} on valuation compression"
        elif self.target_symbol == cheapest_peer:
            pairs_trade = f"Long {self.target_symbol} / Short {most_expensive_peer} on mean reversion"
        else:
            pairs_trade = None
        
        return PeerRotationSignal(
            target_symbol=self.target_symbol,
            target_pe=current_pe,
            peer_comparisons=peer_pes,
            relative_value_rank=rank,
            rotation_opportunity=rotation_text,
            pairs_trade_suggestion=pairs_trade
        )
    
    def _generate_trading_scenarios(self) -> List[TradingScenarioSetup]:
        """Generate trading scenario setups."""
        scenarios = []
        
        # Bearish scenario
        premium = self.valuation_context.get('premium_vs_peer_percent', 0)
        downside = self.valuation_context.get('downside_to_peer_multiple_percent', 0)
        if premium > 5:
            scenarios.append(TradingScenarioSetup(
                scenario_type=TradingScenario.BEARISH,
                timeframe="3-6 months",
                trigger="Next earnings shows continued negative revenue growth or guidance cut",
                entry_strategy="Short after earnings relief rally or buy puts",
                target_price_range=f"{downside:.1f}% downside to peer P/E",
                stop_loss=f"Above {premium + 5:.1f}% premium or +3% from entry",
                risk_reward_ratio="2:1 to 3:1",
                catalysts=[]
            ))
        
        # Bullish scenario
        if premium < 0 or (premium < 10 and self.dashboard.get('overall_target_rank', 5) <= 2):
            scenarios.append(TradingScenarioSetup(
                scenario_type=TradingScenario.BULLISH,
                timeframe="6-12 months",
                trigger="Revenue growth turns positive or strong earnings beat",
                entry_strategy="Buy on pullback to peer average P/E",
                target_price_range=f"Return to +10-15% premium or higher",
                stop_loss=f"Below peer average minus 5% or if fundamentals deteriorate",
                risk_reward_ratio="2:1 to 4:1",
                catalysts=[]
            ))
        
        # Neutral/wait scenario
        if abs(premium) <= 5:
            scenarios.append(TradingScenarioSetup(
                scenario_type=TradingScenario.NEUTRAL,
                timeframe="Current",
                trigger="Fairly valued - wait for catalyst",
                entry_strategy="Stay on sidelines until clear momentum develops",
                target_price_range=None,
                stop_loss="Set alerts at ±5% for breakout/breakdown",
                risk_reward_ratio=None,
                catalysts=[]
            ))
        
        return scenarios
    
    def _determine_overall_bias(self) -> TradeDirection:
        """Determine overall directional bias."""
        valuation_signal = self._extract_valuation_signal()
        momentum_signal = self._extract_momentum_signal()
        
        # Weight valuation more heavily
        if valuation_signal.trade_direction == TradeDirection.SHORT and momentum_signal.risk_level == "high":
            return TradeDirection.SHORT
        elif valuation_signal.trade_direction == TradeDirection.LONG and momentum_signal.trend == "accelerating":
            return TradeDirection.LONG
        else:
            return TradeDirection.NEUTRAL
    
    def _assess_risk_level(self) -> str:
        """Assess overall risk level."""
        momentum = self._extract_momentum_signal()
        premium = abs(self.valuation_context.get('premium_vs_peer_percent', 0))
        
        if momentum.risk_level == "high" and premium > 15:
            return "high"
        elif momentum.risk_level == "low" and premium < 5:
            return "low"
        else:
            return "medium"
    
    def _calculate_conviction_score(self) -> int:
        """Calculate conviction score 1-10."""
        valuation_signal = self._extract_valuation_signal()
        momentum_signal = self._extract_momentum_signal()
        
        score = 5  # Base neutral
        
        # Adjust for valuation confidence
        if valuation_signal.confidence == "high":
            score += 2
        elif valuation_signal.confidence == "low":
            score -= 1
        
        # Adjust for momentum
        if momentum_signal.risk_level == "low":
            score += 2
        elif momentum_signal.risk_level == "high":
            score -= 2
        
        # Adjust for analyst sentiment divergence
        sentiment = self._extract_analyst_sentiment()
        if "underappreciated" in sentiment.sentiment_divergence.lower():
            score += 1
        elif "overvalued" in sentiment.sentiment_divergence.lower():
            score -= 1
        
        return max(1, min(10, score))
    
    def _identify_key_levels(self) -> Dict[str, float]:
        """Identify key price levels."""
        current_pe = self.valuation_context.get('current_pe', 0)
        peer_pe = self.valuation_context.get('peer_average_pe', 0)
        
        return {
            'current_multiple': current_pe,
            'fair_value_multiple': peer_pe,
            'support_multiple': peer_pe * 0.95,
            'resistance_multiple': peer_pe * 1.10
        }
    
    def _generate_summary(self) -> str:
        """Generate executive summary for traders."""
        symbol = self.target_symbol
        premium = self.valuation_context.get('premium_vs_peer_percent', 0)
        downside = self.valuation_context.get('downside_to_peer_multiple_percent', 0)
        rank = self.dashboard.get('overall_target_rank', 0)
        
        if premium > 10:
            return (f"{symbol} trades at {premium:.1f}% premium to peers with rank #{rank} fundamentals. "
                   f"Downside risk: {downside:.1f}% if multiple compresses. Vulnerable to earnings disappointment.")
        elif premium < -10:
            return (f"{symbol} trades at {abs(premium):.1f}% discount to peers with rank #{rank} fundamentals. "
                   f"Upside potential if market recognizes value. Wait for catalyst.")
        else:
            return (f"{symbol} fairly valued vs peers (rank #{rank}). "
                   f"Wait for clear momentum or valuation dislocation before taking position.")
