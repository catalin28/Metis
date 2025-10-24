"""
Competitive Intelligence Data Collector

Orchestrates data collection from FMP API for target company and peers.
Prepares all data needed for report generation with proper validation and transformation.

Author: Metis Development Team
Created: 2025-10-22
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Any

from .fmp_client import FMPClient, FMPClientError


logger = logging.getLogger(__name__)


class CompetitiveDataCollector:
    """
    Collects and prepares financial data for competitive intelligence analysis.
    
    This class handles:
    - Parallel data collection for target + peers
    - Data validation and error handling
    - Metric calculation and ranking
    - Data transformation to report schema format
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize data collector.
        
        Args:
            api_key: Optional FMP API key (uses env variable if not provided)
        """
        self.fmp_client = FMPClient(api_key=api_key)
        logger.info("CompetitiveDataCollector initialized")
    
    def collect_all_company_data(
        self,
        target_symbol: str,
        peer_symbols: List[str],
        max_workers: int = 6
    ) -> Dict[str, Dict[str, Any]]:
        """
        Collect comprehensive data for target company and all peers in parallel.
        
        Args:
            target_symbol: Stock ticker for target company
            peer_symbols: List of peer company symbols
            max_workers: Maximum parallel workers (default: 6)
            
        Returns:
            Dictionary mapping symbols to their comprehensive data:
            {
                'WRB': {...comprehensive data...},
                'PGR': {...comprehensive data...},
                ...
            }
        """
        all_symbols = [target_symbol] + peer_symbols
        logger.info(f"Collecting data for {len(all_symbols)} companies: {target_symbol} + {len(peer_symbols)} peers")
        
        company_data = {}
        
        # Parallel data collection
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_symbol = {
                executor.submit(self._collect_single_company, symbol): symbol
                for symbol in all_symbols
            }
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    data = future.result(timeout=120)  # 2 minute timeout per company
                    company_data[symbol] = data
                    logger.info(f"Successfully collected data for {symbol}")
                    
                except Exception as e:
                    logger.error(f"Failed to collect data for {symbol}: {str(e)}")
                    # Fail-soft: store error info
                    company_data[symbol] = {
                        'symbol': symbol,
                        'error': str(e),
                        'available': False
                    }
        
        # Validate we have at least target + 2 peers
        available_count = sum(1 for data in company_data.values() if data.get('available', True))
        if available_count < 3:
            raise ValueError(
                f"Insufficient data: need target + at least 2 peers, got {available_count} companies"
            )
        
        logger.info(f"Data collection complete: {available_count}/{len(all_symbols)} successful")
        return company_data
    
    def _collect_single_company(self, symbol: str) -> Dict[str, Any]:
        """
        Collect all data for a single company.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Comprehensive company data with calculated metrics
        """
        logger.info(f"Collecting comprehensive data for {symbol}")
        
        try:
            # Get all raw data from FMP
            raw_data = self.fmp_client.get_comprehensive_company_data(symbol, periods=5)
            
            # Calculate derived metrics
            calculated_metrics = self._calculate_metrics(raw_data)
            
            # Transform to standardized format
            company_data = {
                'symbol': symbol,
                'available': True,
                'collected_at': raw_data['collected_at'],
                
                # Profile information
                'name': raw_data['profile'].get('companyName', ''),
                'sector': raw_data['profile'].get('sector', ''),
                'industry': raw_data['profile'].get('industry', ''),
                'market_cap': raw_data['profile'].get('mktCap', 0),
                'country': raw_data['profile'].get('country', ''),
                'exchange': raw_data['profile'].get('exchange', ''),
                'description': raw_data['profile'].get('description', ''),
                'website': raw_data['profile'].get('website', ''),
                'ceo': raw_data['profile'].get('ceo', ''),
                
                # Current market data
                'price': raw_data['quote'].get('price', 0),
                'pe_ratio': raw_data['quote'].get('pe', 0),
                'eps': raw_data['quote'].get('eps', 0),
                'beta': raw_data['profile'].get('beta', 0),
                'volume': raw_data['quote'].get('volume', 0),
                '52_week_high': raw_data['quote'].get('yearHigh', 0),
                '52_week_low': raw_data['quote'].get('yearLow', 0),
                
                # Financial metrics (TTM or most recent)
                'revenue': self._get_latest_value(raw_data['income_statement'], 'revenue'),
                'net_income': self._get_latest_value(raw_data['income_statement'], 'netIncome'),
                'gross_profit': self._get_latest_value(raw_data['income_statement'], 'grossProfit'),
                'operating_income': self._get_latest_value(raw_data['income_statement'], 'operatingIncome'),
                'ebitda': self._get_latest_value(raw_data['income_statement'], 'ebitda'),
                
                'total_assets': self._get_latest_value(raw_data['balance_sheet'], 'totalAssets'),
                'total_equity': self._get_latest_value(raw_data['balance_sheet'], 'totalEquity'),
                'total_debt': self._get_latest_value(raw_data['balance_sheet'], 'totalDebt'),
                'cash': self._get_latest_value(raw_data['balance_sheet'], 'cashAndCashEquivalents'),
                
                'operating_cash_flow': self._get_latest_value(raw_data['cash_flow'], 'operatingCashFlow'),
                'free_cash_flow': self._get_latest_value(raw_data['cash_flow'], 'freeCashFlow'),
                'capex': self._get_latest_value(raw_data['cash_flow'], 'capitalExpenditure'),
                
                # Calculated ratios
                'roe': calculated_metrics.get('roe', 0),
                'roa': calculated_metrics.get('roa', 0),
                'roic': calculated_metrics.get('roic', 0),
                'debt_to_equity': calculated_metrics.get('debt_to_equity', 0),
                'current_ratio': calculated_metrics.get('current_ratio', 0),
                'gross_margin': calculated_metrics.get('gross_margin', 0),
                'operating_margin': calculated_metrics.get('operating_margin', 0),
                'net_margin': calculated_metrics.get('net_margin', 0),
                'revenue_growth': calculated_metrics.get('revenue_growth', 0),
                
                # Insurance-specific metrics (if applicable)
                'combined_ratio': calculated_metrics.get('combined_ratio'),
                
                # Rating
                'rating': raw_data.get('rating', {}).get('rating') if raw_data.get('rating') else None,
                'rating_score': raw_data.get('rating', {}).get('ratingScore', 0) if raw_data.get('rating') else 0,
                
                # Transcripts
                'transcripts': raw_data.get('transcripts', []),
                'has_transcripts': len(raw_data.get('transcripts', [])) > 0,
                
                # Raw data for advanced analysis
                'raw_data': raw_data
            }
            
            return company_data
            
        except FMPClientError as e:
            logger.error(f"FMP API error for {symbol}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error collecting data for {symbol}: {str(e)}")
            raise
    
    def _calculate_metrics(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate derived financial metrics from raw data.
        
        Args:
            raw_data: Raw FMP API data
            
        Returns:
            Dictionary of calculated metrics
        """
        metrics = {}
        
        try:
            # Get most recent periods
            latest_income = raw_data['income_statement'][0] if raw_data['income_statement'] else {}
            latest_balance = raw_data['balance_sheet'][0] if raw_data['balance_sheet'] else {}
            latest_ratios = raw_data['ratios'][0] if raw_data['ratios'] else {}
            latest_key_metrics = raw_data['key_metrics'][0] if raw_data['key_metrics'] else {}
            
            # ROE (Return on Equity)
            metrics['roe'] = latest_key_metrics.get('roe') or latest_ratios.get('returnOnEquity', 0)
            
            # ROA (Return on Assets)
            metrics['roa'] = latest_key_metrics.get('roa') or latest_ratios.get('returnOnAssets', 0)
            
            # ROIC (Return on Invested Capital)
            metrics['roic'] = latest_key_metrics.get('roic', 0)
            
            # Leverage ratios
            metrics['debt_to_equity'] = latest_key_metrics.get('debtToEquity') or latest_ratios.get('debtEquityRatio', 0)
            metrics['current_ratio'] = latest_ratios.get('currentRatio', 0)
            
            # Profitability margins
            metrics['gross_margin'] = latest_ratios.get('grossProfitMargin', 0)
            metrics['operating_margin'] = latest_ratios.get('operatingProfitMargin', 0)
            metrics['net_margin'] = latest_ratios.get('netProfitMargin', 0)
            
            # Growth metrics - Quarter-over-Quarter (QoQ)
            # NOTE: QoQ growth compares most recent quarter vs previous quarter.
            # This can show negative values even when annual/YoY growth is positive,
            # especially for companies with seasonal or lumpy revenue patterns.
            # For competitive analysis, this metric should be labeled as "QoQ" to prevent
            # misinterpretation as annual weakness.
            if len(raw_data['income_statement']) >= 2:
                current_revenue = raw_data['income_statement'][0].get('revenue', 0)
                prior_revenue = raw_data['income_statement'][1].get('revenue', 0)
                
                if prior_revenue and prior_revenue != 0:
                    # Store as 'revenue_growth' for backward compatibility, but context indicates QoQ
                    metrics['revenue_growth'] = ((current_revenue - prior_revenue) / prior_revenue) * 100
                else:
                    metrics['revenue_growth'] = 0
            else:
                metrics['revenue_growth'] = 0
            
            # Insurance-specific: Combined Ratio (if applicable)
            # Combined Ratio = (Incurred Losses + Expenses) / Earned Premiums
            # For insurance companies, we calculate from income statement if possible
            if self._is_insurance_company(raw_data):
                metrics['combined_ratio'] = self._calculate_combined_ratio(latest_income)
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Error calculating metrics: {str(e)}")
            return metrics
    
    def _is_insurance_company(self, raw_data: Dict[str, Any]) -> bool:
        """Check if company is in insurance sector."""
        sector = raw_data.get('profile', {}).get('sector', '').lower()
        industry = raw_data.get('profile', {}).get('industry', '').lower()
        return 'insurance' in sector or 'insurance' in industry
    
    def _calculate_combined_ratio(self, income_statement: Dict[str, Any]) -> Optional[float]:
        """
        Calculate combined ratio for insurance companies.
        
        Combined Ratio = (Loss Ratio + Expense Ratio) * 100
        
        This is a simplified calculation. More sophisticated calculation would
        require specific insurance financial statement line items.
        """
        try:
            # Simplified: (Cost of Revenue + Operating Expenses) / Revenue
            revenue = income_statement.get('revenue', 0)
            cost_of_revenue = income_statement.get('costOfRevenue', 0)
            operating_expenses = income_statement.get('operatingExpenses', 0)
            
            if revenue and revenue != 0:
                combined_ratio = ((cost_of_revenue + operating_expenses) / revenue) * 100
                return combined_ratio
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not calculate combined ratio: {str(e)}")
            return None
    
    def _get_latest_value(
        self,
        data_list: List[Dict[str, Any]],
        field: str
    ) -> Optional[float]:
        """
        Get the most recent value for a field from a time series list.
        
        Args:
            data_list: List of financial data dictionaries (sorted newest first)
            field: Field name to extract
            
        Returns:
            Most recent value or None if not available
        """
        if not data_list or len(data_list) == 0:
            return None
        
        return data_list[0].get(field)
    
    def calculate_comparative_metrics(
        self,
        company_data: Dict[str, Dict[str, Any]],
        target_symbol: str
    ) -> Dict[str, Any]:
        """
        Calculate comparative metrics and rankings across all companies.
        
        Args:
            company_data: Dictionary mapping symbols to company data
            target_symbol: Symbol of the target company
            
        Returns:
            Dictionary with comparative analysis:
            - peer_average_pe: Average P/E ratio of peers
            - peer_average_roe: Average ROE of peers
            - pe_gap: P/E difference (target - peer avg)
            - overall_rank: Target's overall ranking
            - strengths: List of metrics where target excels
            - weaknesses: List of metrics where target lags
            - perception_gaps: List of perception gap descriptions
        """
        logger.info(f"Calculating comparative metrics for {target_symbol}")
        
        # Filter out failed data collections
        valid_data = {
            symbol: data for symbol, data in company_data.items()
            if data.get('available', True)
        }
        
        if target_symbol not in valid_data:
            raise ValueError(f"No data available for target company {target_symbol}")
        
        target_data = valid_data[target_symbol]
        peer_data = {s: d for s, d in valid_data.items() if s != target_symbol}
        
        if len(peer_data) < 2:
            raise ValueError("Need at least 2 peers with valid data for comparison")
        
        # Calculate peer averages
        peer_pe_values = [d['pe_ratio'] for d in peer_data.values() if d.get('pe_ratio', 0) > 0]
        peer_roe_values = [d['roe'] for d in peer_data.values() if d.get('roe', 0) != 0]
        
        peer_average_pe = sum(peer_pe_values) / len(peer_pe_values) if peer_pe_values else 0
        peer_average_roe = sum(peer_roe_values) / len(peer_roe_values) if peer_roe_values else 0
        
        # Calculate gaps
        target_pe = target_data.get('pe_ratio', 0)
        target_roe = target_data.get('roe', 0)
        
        pe_gap = target_pe - peer_average_pe
        pe_gap_pct = (pe_gap / peer_average_pe * 100) if peer_average_pe != 0 else 0
        
        # Rank metrics
        rankings = self._rank_companies_on_metrics(valid_data, target_symbol)
        
        # Identify strengths and weaknesses
        strengths = [
            f"{metric}: {target_data.get(metric, 0):.2f} (#{rank}, {desc})"
            for metric, (rank, desc) in rankings.items()
            if rank <= 2  # Top 2 rankings are strengths
        ]
        
        weaknesses = [
            f"{metric}: {target_data.get(metric, 0):.2f} (#{rank}, {desc})"
            for metric, (rank, desc) in rankings.items()
            if rank >= len(valid_data) - 1  # Bottom 2 rankings are weaknesses
        ]
        
        # Identify perception gaps (good metrics but low valuation)
        perception_gaps = []
        if target_pe < peer_average_pe:  # Trading at discount
            for metric, (rank, desc) in rankings.items():
                if rank <= 2 and metric != 'pe_ratio':
                    perception_gaps.append(
                        f"{metric}: ranks #{rank} but P/E at discount ({target_pe:.1f}x vs peers {peer_average_pe:.1f}x)"
                    )
        
        # Calculate target P/E for valuation rerate recommendations
        # Use conservative 35% of way from current to peer average
        # This typically yields ~20x target for companies trading at deep discounts
        # Round to nearest 0.05 for cleaner P/E targets (19.75x vs 19.77x)
        if target_pe < peer_average_pe and peer_average_pe > 0:
            target_pe_recommendation = target_pe + (peer_average_pe - target_pe) * 0.35
            # Round to nearest 0.05 for cleaner targets
            target_pe_recommendation = round(target_pe_recommendation * 20) / 20
        else:
            target_pe_recommendation = peer_average_pe  # Use peer average if not at discount
        
        return {
            'peer_average_pe': peer_average_pe,
            'peer_average_roe': peer_average_roe,
            'pe_gap': pe_gap,
            'pe_gap_pct': pe_gap_pct,
            'target_pe': round(target_pe_recommendation, 2),  # Target P/E for recommendations
            'overall_rank': 1,  # Placeholder - will be overwritten by dashboard's overall_target_rank
            'strengths': strengths[:5],  # Top 5 strengths
            'weaknesses': weaknesses[:5],  # Top 5 weaknesses
            'perception_gaps': perception_gaps,
            'rankings': rankings
        }
    
    def _rank_companies_on_metrics(
        self,
        company_data: Dict[str, Dict[str, Any]],
        target_symbol: str
    ) -> Dict[str, tuple]:
        """
        Rank all companies on key metrics.
        
        Args:
            company_data: Dictionary of company data
            target_symbol: Target company symbol
            
        Returns:
            Dictionary mapping metric names to (rank, description) tuples
        """
        # Metrics to rank (higher is better unless specified)
        metrics_to_rank = {
            'pe_ratio': ('lower_better', 'P/E Ratio'),
            'roe': ('higher_better', 'ROE'),
            'roa': ('higher_better', 'ROA'),
            'revenue_growth': ('higher_better', 'Revenue Growth'),
            'debt_to_equity': ('lower_better', 'Debt/Equity'),
            'market_cap': ('higher_better', 'Market Cap'),
            'net_margin': ('higher_better', 'Net Margin'),
        }
        
        # Add combined ratio for insurance companies
        if any('combined_ratio' in data and data['combined_ratio'] is not None 
               for data in company_data.values()):
            metrics_to_rank['combined_ratio'] = ('lower_better', 'Combined Ratio')
        
        rankings = {}
        
        for metric, (direction, description) in metrics_to_rank.items():
            # Get values for all companies
            values = {
                symbol: data.get(metric, 0)
                for symbol, data in company_data.items()
                if data.get(metric, 0) != 0  # Exclude zero values
            }
            
            if not values:
                continue
            
            # Sort companies
            if direction == 'lower_better':
                sorted_symbols = sorted(values.items(), key=lambda x: x[1])
            else:
                sorted_symbols = sorted(values.items(), key=lambda x: x[1], reverse=True)
            
            # Find target's rank
            for rank, (symbol, value) in enumerate(sorted_symbols, 1):
                if symbol == target_symbol:
                    rank_desc = "best" if rank == 1 else ("worst" if rank == len(sorted_symbols) else f"{rank}th")
                    rankings[metric] = (rank, rank_desc)
                    break
        
        return rankings
