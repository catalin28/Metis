"""
Input Model Transformer

Transforms collected FMP data into Pydantic Input models for LLM generation.
Bridges raw data collection to structured report generation.

CALCULATION ARCHITECTURE:
- All math done here in Python (outperformance ratios, percentages, valuation impacts)
- LLMs receive pre-calculated strings and only add narrative context
- Eliminates LLM math errors completely

Author: Metis Development Team
Created: 2025-10-22
Updated: 2025-10-23 (Added pre-calculated comparisons)
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models.report_schema_v2 import (
    ExecutiveSummaryInput,
    CompetitiveDashboardInput,
    HiddenStrengthsInput,
    StealTheirPlaybookInput,
    ValuationForensicsInput,
    ActionableRoadmapInput,
    AnalystConsensusInput,
    AnalystConsensusMetric,
)
from .dashboard_ranker import DashboardMetricsRanker
from ..utils.metric_calculations import (
    format_outperformance_vs_peers,
    calculate_valuation_impact,
    determine_metric_direction,
)


logger = logging.getLogger(__name__)


class InputModelTransformer:
    """
    Transforms collected data into Pydantic Input models for LLM generation.
    
    Each transform method takes raw/calculated data and produces a validated
    Input model ready to be combined with prompts for LLM generation.
    """
    
    @staticmethod
    def create_executive_summary_input(
        target_symbol: str,
        company_data: Dict[str, Dict[str, Any]],
        comparative_metrics: Dict[str, Any],
        company_overview: str
    ) -> ExecutiveSummaryInput:
        """
        Create ExecutiveSummaryInput from collected data.
        
        Args:
            target_symbol: Target company symbol
            company_data: All company data from collector
            comparative_metrics: Comparative analysis results
            company_overview: Web search-generated company overview
            
        Returns:
            Validated ExecutiveSummaryInput instance
        """
        logger.info(f"Creating ExecutiveSummaryInput for {target_symbol}")
        
        target_data = company_data[target_symbol]
        
        # Build peer symbols list
        peer_symbols = [
            symbol for symbol, data in company_data.items()
            if symbol != target_symbol and data.get('available', True)
        ]
        
        # Ensure we have 3-5 peers
        if len(peer_symbols) < 3:
            logger.warning(f"Only {len(peer_symbols)} peers available for {target_symbol}")
        peer_symbols = peer_symbols[:5]  # Cap at 5
        
        from datetime import datetime
        
        # Calculate target valuation metrics
        target_pe = comparative_metrics.get('target_pe', 0)
        current_pe = target_data.get('pe_ratio', 0)
        market_cap = target_data.get('market_cap', 0)
        
        # Calculate market cap change if target_pe is achieved
        # Formula: (target_pe / current_pe - 1) × current_market_cap
        # Positive = increase (stock undervalued), Negative = decrease (stock overvalued)
        if current_pe > 0 and target_pe > 0:
            target_market_cap_change = ((target_pe / current_pe) - 1) * market_cap
            target_gap_percentage = ((target_pe / current_pe) - 1) * 100
            is_trading_at_premium = target_pe < current_pe
            valuation_direction = "premium" if is_trading_at_premium else "discount"
        else:
            target_market_cap_change = 0
            target_gap_percentage = 0
            is_trading_at_premium = False
            valuation_direction = "unknown"
        
        return ExecutiveSummaryInput(
            # Company identification
            symbol=target_symbol,
            company_name=target_data.get('name', ''),
            industry=target_data.get('industry', ''),
            sector=target_data.get('sector', ''),
            report_date=datetime.now().strftime('%Y-%m-%d'),
            
            # Peer group context
            peer_count=len(peer_symbols),
            peer_symbols=peer_symbols,
            
            # Valuation metrics
            market_cap=market_cap,
            current_pe=current_pe,
            peer_average_pe=comparative_metrics.get('peer_average_pe', 0),
            valuation_gap=comparative_metrics.get('pe_gap', 0),
            gap_percentage=comparative_metrics.get('pe_gap_pct', 0),
            
            # Target valuation
            target_pe=target_pe,
            target_market_cap_change=target_market_cap_change,
            target_gap_percentage=target_gap_percentage,
            is_trading_at_premium=is_trading_at_premium,
            valuation_direction=valuation_direction,
            
            # Profitability metrics
            target_roe=target_data.get('roe', 0),
            peer_average_roe=comparative_metrics.get('peer_average_roe', 0),
            
            # Optional industry-specific
            target_combined_ratio=target_data.get('combined_ratio'),
            target_revenue_growth=target_data.get('revenue_growth'),
            
            # Competitive position
            target_rank=comparative_metrics.get('overall_rank', 1),  # Rankings start at 1
            areas_of_excellence=comparative_metrics.get('strengths', [])[:3],
            areas_of_improvement=comparative_metrics.get('weaknesses', [])[:3],
            perception_gaps=comparative_metrics.get('perception_gaps', [])
        )
    
    @staticmethod
    def create_competitive_dashboard_input(
        target_symbol: str,
        company_data: Dict[str, Dict[str, Any]],
        comparative_metrics: Dict[str, Any]
    ) -> CompetitiveDashboardInput:
        """
        Create CompetitiveDashboardInput from collected data.
        
        Uses DashboardMetricsRanker to extract and rank all metrics from company_data.
        No recalculation - all metrics already exist in company_data.
        
        Args:
            target_symbol: Target company symbol
            company_data: All company data from collector (metrics already calculated)
            comparative_metrics: Comparative analysis results (for reference)
            
        Returns:
            Validated CompetitiveDashboardInput instance
        """
        logger.info(f"Creating CompetitiveDashboardInput for {target_symbol}")
        
        target_data = company_data[target_symbol]
        
        # Build peer symbols list
        peer_symbols = [
            symbol for symbol, data in company_data.items()
            if symbol != target_symbol and data.get('available', True)
        ]
        
        # Use ranker to extract and rank all metrics
        ranker = DashboardMetricsRanker(company_data, target_symbol)
        all_ranked_metrics = ranker.extract_and_rank_all_metrics()
        
        # Build metrics list for CompetitiveDashboardInput
        metrics_list = []
        
        # Define metric mappings: (metric_key, display_name)
        metric_definitions = [
            ('market_cap_data', 'Market Cap'),
            ('pe_ratio_data', 'P/E Ratio'),
            ('roe_data', 'ROE'),
            ('revenue_growth_data', 'Revenue Growth'),
            ('debt_equity_data', 'Debt/Equity'),
            ('combined_ratio_data', 'Combined Ratio'),
            ('gross_margin_data', 'Gross Margin'),
            ('operating_margin_data', 'Operating Margin'),
            ('net_margin_data', 'Net Margin'),
        ]
        
        for metric_key, metric_name in metric_definitions:
            metric_data_list = all_ranked_metrics.get(metric_key, [])
            
            # Skip if no data for this metric
            if not metric_data_list:
                logger.debug(f"Skipping {metric_name} - no data available")
                continue
            
            # Find target company's value, rank, and tie status
            target_value = None
            target_rank = None
            is_tied = False
            for item in metric_data_list:
                if item['symbol'] == target_symbol:
                    target_value = item['value']
                    target_rank = item['rank']
                    is_tied = item.get('is_tied', False)
                    break
            
            if target_value is None:
                logger.warning(f"Target {target_symbol} not found in {metric_name} data")
                continue
            
            # Get peer values
            peer_values = ranker.get_peer_values_for_metric(metric_key, all_ranked_metrics)
            
            if not peer_values:
                logger.warning(f"No peer values for {metric_name}")
                continue
            
            # Generate rank qualifier (pass metric_name for P/E special handling)
            total_companies = len(metric_data_list)
            rank_qualifier = ranker.generate_rank_qualifier(target_rank, total_companies, is_tied, metric_name=metric_name)
            
            # Add to metrics list
            metrics_list.append({
                'metric_name': metric_name,
                'target_value': target_value,
                'peer_values': peer_values,
                'target_rank': target_rank,
                'rank_qualifier': rank_qualifier
            })
        
        if len(metrics_list) < 5:
            logger.warning(f"Only {len(metrics_list)} metrics available for dashboard (minimum 5 recommended)")
        
        # PRE-CALCULATE top 3 strengths (lowest ranks = best performance)
        # Exclude P/E ratio from strengths (low P/E = undervalued, not a strength)
        strength_candidates = [m for m in metrics_list if 'P/E' not in m['metric_name']]
        sorted_strengths = sorted(strength_candidates, key=lambda x: x['target_rank'])
        top_3_strengths = [
            {
                'metric_name': m['metric_name'],
                'target_value': m['target_value'],
                'target_rank': m['target_rank'],
                'rank_qualifier': m['rank_qualifier']
            }
            for m in sorted_strengths[:3]
        ]
        
        # PRE-CALCULATE top 3 weaknesses (highest ranks = worst performance)
        # Exclude metrics that are actually strengths (rank #1-2) from weakness candidates
        weakness_candidates = [m for m in metrics_list if m['target_rank'] > 2]
        sorted_weaknesses = sorted(weakness_candidates, key=lambda x: x['target_rank'], reverse=True)
        top_3_weaknesses = [
            {
                'metric_name': m['metric_name'],
                'target_value': m['target_value'],
                'target_rank': m['target_rank'],
                'rank_qualifier': m['rank_qualifier']
            }
            for m in sorted_weaknesses[:3]
        ]
        
        logger.info(f"Created dashboard input with {len(metrics_list)} metrics for {target_symbol}")
        logger.info(f"Top 3 strengths: {[m['metric_name'] for m in top_3_strengths]}")
        logger.info(f"Top 3 weaknesses: {[m['metric_name'] for m in top_3_weaknesses]}")
        
        return CompetitiveDashboardInput(
            target_symbol=target_symbol,
            peer_symbols=peer_symbols,
            metrics=metrics_list,
            top_3_strengths=top_3_strengths,
            top_3_weaknesses=top_3_weaknesses
        )
    
    @staticmethod
    def create_hidden_strengths_input(
        target_symbol: str,
        company_data: Dict[str, Dict[str, Any]],
        comparative_metrics: Dict[str, Any]
    ) -> HiddenStrengthsInput:
        """
        Create HiddenStrengthsInput from collected data.
        
        Args:
            target_symbol: Target company symbol
            company_data: All company data from collector
            comparative_metrics: Comparative analysis results
            
        Returns:
            Validated HiddenStrengthsInput instance
        """
        logger.info(f"Creating HiddenStrengthsInput for {target_symbol}")
        
        target_data = company_data[target_symbol]
        
        # Build peer details list for LLM to use in comparisons
        peer_details = []
        for symbol, data in company_data.items():
            if symbol != target_symbol and data.get('available', True):
                peer_details.append({
                    'symbol': symbol,
                    'name': data.get('name', symbol),
                    'pe_ratio': data.get('pe_ratio', 0)
                })
        
        # Find metrics where target ranks well but trades at discount
        underappreciated_metrics = []
        
        rankings = comparative_metrics.get('rankings', {})
        target_pe = target_data.get('pe_ratio', 0)
        peer_avg_pe = comparative_metrics.get('peer_average_pe', 0)
        
        trading_at_discount = target_pe < peer_avg_pe
        
        if trading_at_discount:
            # Look for top-ranked metrics (rank #1 or #2)
            for metric, (rank, desc) in rankings.items():
                if rank <= 2 and metric != 'pe_ratio':
                    metric_value = target_data.get(metric, 0)
                    
                    # Get peer values for comparison (as dict with company names)
                    peer_values_dict = {}
                    peer_values_list = []
                    for symbol, data in company_data.items():
                        if symbol != target_symbol and data.get('available', True):
                            value = data.get(metric, 0)
                            peer_values_dict[symbol] = value
                            peer_values_list.append(value)
                    
                    peer_avg = sum(peer_values_list) / len(peer_values_list) if peer_values_list else 0
                    
                    # PRE-CALCULATE comparison string (no LLM math!)
                    higher_is_better = determine_metric_direction(metric) == 'higher_is_better'
                    outperformance_calculated, peers_excluded_note = format_outperformance_vs_peers(
                        target_value=metric_value,
                        peer_values=peer_values_dict,
                        metric_name=metric,
                        higher_is_better=higher_is_better
                    )
                    
                    # PRE-CALCULATE valuation impact estimate
                    pct_improvement = ((metric_value / peer_avg) - 1) * 100 if peer_avg > 0 else 0
                    pe_impact, impact_string = calculate_valuation_impact(
                        metric_improvement=abs(pct_improvement),
                        base_pe=target_pe
                    )
                    
                    metric_dict = {
                        'metric_name': metric,
                        'target_value': metric_value,
                        'peer_average': peer_avg,
                        'target_rank': rank,
                        'peer_values': peer_values_dict,
                        'outperformance_magnitude_calculated': outperformance_calculated,
                        'estimated_pe_impact': impact_string
                    }
                    
                    # Add peers_excluded note if present (negative equity case)
                    if peers_excluded_note:
                        metric_dict['peers_excluded'] = peers_excluded_note
                    
                    underappreciated_metrics.append(metric_dict)
        
        # If no underappreciated metrics found, use all #1-2 ranked metrics even without discount
        if not underappreciated_metrics:
            for metric, (rank, desc) in rankings.items():
                if rank <= 2 and metric != 'pe_ratio':
                    metric_value = target_data.get(metric, 0)
                    
                    # Get peer values for comparison (as dict with company names)
                    peer_values_dict = {}
                    peer_values_list = []
                    for symbol, data in company_data.items():
                        if symbol != target_symbol and data.get('available', True):
                            value = data.get(metric, 0)
                            peer_values_dict[symbol] = value
                            peer_values_list.append(value)
                    
                    peer_avg = sum(peer_values_list) / len(peer_values_list) if peer_values_list else 0
                    
                    # PRE-CALCULATE comparison string (no LLM math!)
                    higher_is_better = determine_metric_direction(metric) == 'higher_is_better'
                    outperformance_calculated, peers_excluded_note = format_outperformance_vs_peers(
                        target_value=metric_value,
                        peer_values=peer_values_dict,
                        metric_name=metric,
                        higher_is_better=higher_is_better
                    )
                    
                    # PRE-CALCULATE valuation impact estimate
                    pct_improvement = ((metric_value / peer_avg) - 1) * 100 if peer_avg > 0 else 0
                    pe_impact, impact_string = calculate_valuation_impact(
                        metric_improvement=abs(pct_improvement),
                        base_pe=target_pe
                    )
                    
                    metric_dict = {
                        'metric_name': metric,
                        'target_value': metric_value,
                        'peer_average': peer_avg,
                        'target_rank': rank,
                        'peer_values': peer_values_dict,
                        'outperformance_magnitude_calculated': outperformance_calculated,
                        'estimated_pe_impact': impact_string
                    }
                    
                    if peers_excluded_note:
                        metric_dict['peers_excluded'] = peers_excluded_note
                    
                    underappreciated_metrics.append(metric_dict)
        
        # Ensure at least 1 metric
        if not underappreciated_metrics:
            # Fallback: use best metric regardless of rank
            best_metric = None
            best_rank = 999
            for metric, (rank, desc) in rankings.items():
                if metric != 'pe_ratio' and rank < best_rank:
                    best_rank = rank
                    best_metric = metric
            
            if best_metric:
                metric_value = target_data.get(best_metric, 0)
                
                # Get peer values for comparison (as dict with company names)
                peer_values_dict = {}
                peer_values_list = []
                for symbol, data in company_data.items():
                    if symbol != target_symbol and data.get('available', True):
                        value = data.get(best_metric, 0)
                        peer_values_dict[symbol] = value
                        peer_values_list.append(value)
                
                peer_avg = sum(peer_values_list) / len(peer_values_list) if peer_values_list else 0
                
                # PRE-CALCULATE comparison string (no LLM math!)
                higher_is_better = determine_metric_direction(best_metric) == 'higher_is_better'
                outperformance_calculated, peers_excluded_note = format_outperformance_vs_peers(
                    target_value=metric_value,
                    peer_values=peer_values_dict,
                    metric_name=best_metric,
                    higher_is_better=higher_is_better
                )
                
                # PRE-CALCULATE valuation impact estimate
                pct_improvement = ((metric_value / peer_avg) - 1) * 100 if peer_avg > 0 else 0
                pe_impact, impact_string = calculate_valuation_impact(
                    metric_improvement=abs(pct_improvement),
                    base_pe=target_pe
                )
                
                metric_dict = {
                    'metric_name': best_metric,
                    'target_value': metric_value,
                    'peer_average': peer_avg,
                    'target_rank': best_rank,
                    'peer_values': peer_values_dict,
                    'outperformance_magnitude_calculated': outperformance_calculated,
                    'estimated_pe_impact': impact_string
                }
                
                if peers_excluded_note:
                    metric_dict['peers_excluded'] = peers_excluded_note
                
                underappreciated_metrics.append(metric_dict)
        
        return HiddenStrengthsInput(
            target_symbol=target_symbol,
            underappreciated_metrics=underappreciated_metrics[:6],  # Max 6
            peer_details=peer_details,
            current_pe=target_pe,
            peer_average_pe=peer_avg_pe
        )
    
    @staticmethod
    def create_steal_their_playbook_input(
        target_symbol: str,
        company_data: Dict[str, Dict[str, Any]],
        comparative_metrics: Dict[str, Any]
    ) -> StealTheirPlaybookInput:
        """
        Create StealTheirPlaybookInput from collected data.
        
        Args:
            target_symbol: Target company symbol
            company_data: All company data from collector
            comparative_metrics: Comparative analysis results
            
        Returns:
            Validated StealTheirPlaybookInput instance
        """
        logger.info(f"Creating StealTheirPlaybookInput for {target_symbol}")
        
        # Identify top-performing peers (highest P/E ratios)
        peer_performances = []
        for symbol, data in company_data.items():
            if symbol != target_symbol and data.get('available', True):
                pe = data.get('pe_ratio', 0)
                if pe > 0:
                    peer_performances.append({
                        'symbol': symbol,
                        'name': data.get('name', ''),
                        'pe_ratio': pe,
                        'transcripts': data.get('transcripts', [])
                    })
        
        # Sort by P/E (highest first)
        peer_performances.sort(key=lambda x: x['pe_ratio'], reverse=True)
        
        # Get top 3 peers with transcripts
        top_peers_with_transcripts = []
        for peer in peer_performances:
            if peer['transcripts'] and len(peer['transcripts']) > 0:
                top_peers_with_transcripts.append({
                    'symbol': peer['symbol'],
                    'name': peer['name'],
                    'pe_ratio': peer['pe_ratio'],
                    'transcript_count': len(peer['transcripts']),
                    'latest_transcript': peer['transcripts'][0] if peer['transcripts'] else {}
                })
                
                if len(top_peers_with_transcripts) >= 3:
                    break
        
        return StealTheirPlaybookInput(
            target_symbol=target_symbol,
            top_performing_peers=top_peers_with_transcripts,
            
            # Include actual transcript data for analysis
            peer_transcripts={
                peer['symbol']: peer['latest_transcript'].get('content', '')
                for peer in top_peers_with_transcripts
                if peer.get('latest_transcript')
            },
            
            target_pe=company_data[target_symbol].get('pe_ratio', 0),
            sector=company_data[target_symbol].get('sector', '')
        )
    
    @staticmethod
    def create_valuation_forensics_input(
        target_symbol: str,
        company_data: Dict[str, Dict[str, Any]],
        comparative_metrics: Dict[str, Any]
    ) -> ValuationForensicsInput:
        """
        Create ValuationForensicsInput from collected data.
        
        Args:
            target_symbol: Target company symbol
            company_data: All company data from collector
            comparative_metrics: Comparative analysis results
            
        Returns:
            Validated ValuationForensicsInput instance
        """
        logger.info(f"Creating ValuationForensicsInput for {target_symbol}")
        
        target_data = company_data[target_symbol]
        
        # Build fundamental data for regression analysis
        fundamental_factors = {
            'roe': target_data.get('roe', 0),
            'revenue_growth': target_data.get('revenue_growth', 0),
            'debt_to_equity': target_data.get('debt_to_equity', 0),
            'net_margin': target_data.get('net_margin', 0),
            'operating_margin': target_data.get('operating_margin', 0),
            'roa': target_data.get('roa', 0),
            'market_cap': target_data.get('market_cap', 0),
            'beta': target_data.get('beta', 0),
        }
        
        # Insurance-specific
        if target_data.get('combined_ratio') is not None:
            fundamental_factors['combined_ratio'] = target_data['combined_ratio']
        
        # Peer comparison data
        peer_data_for_regression = []
        for symbol, data in company_data.items():
            if symbol != target_symbol and data.get('available', True):
                peer_data_for_regression.append({
                    'symbol': symbol,
                    'pe_ratio': data.get('pe_ratio', 0),
                    'roe': data.get('roe', 0),
                    'revenue_growth': data.get('revenue_growth', 0),
                    'debt_to_equity': data.get('debt_to_equity', 0),
                    'net_margin': data.get('net_margin', 0),
                })
        
        return ValuationForensicsInput(
            target_symbol=target_symbol,
            target_pe=target_data.get('pe_ratio', 0),
            peer_average_pe=comparative_metrics.get('peer_average_pe', 0),
            pe_gap=comparative_metrics.get('pe_gap', 0),
            
            # Fundamental factors
            target_fundamental_metrics=fundamental_factors,
            
            # Peer data for regression
            peer_comparison_data=peer_data_for_regression,
            
            # Identified strengths/weaknesses
            strengths=comparative_metrics.get('strengths', [])[:5],
            weaknesses=comparative_metrics.get('weaknesses', [])[:5],
            
            # Perception gaps
            perception_gaps=comparative_metrics.get('perception_gaps', [])
        )
    
    @staticmethod
    def create_actionable_roadmap_input(
        target_symbol: str,
        company_data: Dict[str, Dict[str, Any]],
        comparative_metrics: Dict[str, Any],
        executive_summary_output: Optional[Any] = None,
        competitive_dashboard_output: Optional[Any] = None,
        hidden_strengths_output: Optional[Any] = None,
        steal_their_playbook_output: Optional[Any] = None,
        valuation_forensics_output: Optional[Any] = None
    ) -> ActionableRoadmapInput:
        """
        Create ActionableRoadmapInput from all previous analysis outputs.
        
        This is the synthesis section that combines insights from all prior sections.
        
        Args:
            target_symbol: Target company symbol
            company_data: All company data from collector
            comparative_metrics: Comparative analysis results
            executive_summary_output: Output from Section 1 (optional)
            competitive_dashboard_output: Output from Section 2 (optional)
            hidden_strengths_output: Output from Section 3 (optional)
            steal_their_playbook_output: Output from Section 4 (optional)
            valuation_forensics_output: Output from Section 5 (optional)
            
        Returns:
            Validated ActionableRoadmapInput instance
        """
        logger.info(f"Creating ActionableRoadmapInput for {target_symbol}")
        
        target_data = company_data[target_symbol]
        
        # Aggregate insights from all sections
        all_insights = []
        
        # From executive summary
        if executive_summary_output:
            all_insights.extend(getattr(executive_summary_output, 'key_findings', []))
        
        # From hidden strengths
        if hidden_strengths_output:
            hidden_strengths_list = getattr(hidden_strengths_output, 'hidden_strengths', [])
            all_insights.extend([
                f"Hidden strength: {strength.strength_name}"
                for strength in hidden_strengths_list
            ])
        
        # From valuation forensics
        if valuation_forensics_output:
            gaps = getattr(valuation_forensics_output, 'valuation_gaps', [])
            all_insights.extend([
                f"Valuation gap: {gap.factor_name} ({gap.impact_on_pe:+.1f}x P/E)"
                for gap in gaps
            ])
        
        # Identify key problems to solve
        identified_problems = []
        
        # Problem 1: Valuation gap
        if comparative_metrics.get('pe_gap', 0) < 0:
            identified_problems.append({
                'problem_type': 'valuation_discount',
                'description': f"Trading at {abs(comparative_metrics.get('pe_gap_pct', 0)):.1f}% discount to peers",
                'impact_estimate': abs(comparative_metrics.get('pe_gap', 0)),
                'data_support': comparative_metrics.get('perception_gaps', [])
            })
        
        # Problem 2: Operational weaknesses
        weaknesses = comparative_metrics.get('weaknesses', [])
        if weaknesses:
            identified_problems.append({
                'problem_type': 'operational_weakness',
                'description': "Operational metrics lagging peers",
                'impact_estimate': 0,  # LLM will calculate
                'data_support': weaknesses[:3]
            })
        
        # Problem 3: Messaging/narrative gaps (if peers outperform)
        if comparative_metrics.get('peer_average_pe', 0) > target_data.get('pe_ratio', 0):
            identified_problems.append({
                'problem_type': 'narrative_gap',
                'description': "Messaging not resonating as effectively as higher-valued peers",
                'impact_estimate': 0,
                'data_support': []
            })
        
        return ActionableRoadmapInput(
            target_symbol=target_symbol,
            
            # All prior insights
            prior_insights=all_insights,
            
            # Identified problems
            identified_problems=identified_problems[:5],  # Top 5
            
            # Current state
            current_pe=target_data.get('pe_ratio', 0),
            peer_average_pe=comparative_metrics.get('peer_average_pe', 0),
            pe_gap_percentage=comparative_metrics.get('pe_gap_pct', 0),
            
            # Strengths to leverage
            strengths_to_leverage=comparative_metrics.get('strengths', [])[:5],
            
            # Weaknesses to address
            weaknesses_to_address=comparative_metrics.get('weaknesses', [])[:5],
            
            # Sector context
            sector=target_data.get('sector', ''),
            industry=target_data.get('industry', '')
        )
    
    @staticmethod
    def create_analyst_consensus_input(
        target_analysis: AnalystConsensusMetric,
        peer_analysis: List[AnalystConsensusMetric],
        dashboard_metrics: Optional[List[Dict[str, Any]]] = None,
        hidden_strengths: Optional[List[Dict[str, Any]]] = None
    ) -> AnalystConsensusInput:
        """
        Create AnalystConsensusInput from analyst grades data.
        
        Args:
            target_analysis: Target company analyst consensus metrics
            peer_analysis: Peer companies analyst consensus metrics
            dashboard_metrics: Optional metrics from Section 2 (to identify fundamental strengths)
            hidden_strengths: Optional hidden strengths from Section 3
            
        Returns:
            Validated AnalystConsensusInput instance
        """
        logger.info(f"Creating AnalystConsensusInput for {target_analysis.symbol}")
        
        # Extract fundamental strengths from dashboard and hidden strengths
        fundamental_strengths = []
        
        # From dashboard: metrics where target ranks #1 or #2
        if dashboard_metrics:
            for metric in dashboard_metrics:
                rank = metric.get('target_rank', 999)
                if rank <= 2:
                    metric_name = metric.get('metric_name', 'Unknown')
                    fundamental_strengths.append(f"#{rank} in {metric_name}")
        
        # From hidden strengths: add outperformance descriptions
        if hidden_strengths:
            for strength in hidden_strengths[:3]:  # Top 3
                metric_name = strength.get('metric_name', 'Unknown')
                magnitude = strength.get('outperformance_magnitude', 'significantly better')
                fundamental_strengths.append(f"Outperforms in {metric_name}: {magnitude}")
        
        # Ensure we have at least something
        if not fundamental_strengths:
            fundamental_strengths = ["No major fundamental advantages identified"]
        
        return AnalystConsensusInput(
            target_analysis=target_analysis,
            peer_analysis=peer_analysis,
            fundamental_strengths=fundamental_strengths
        )

