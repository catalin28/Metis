"""
Dashboard Metrics Ranker

Extracts financial metrics from company_data and applies competitive rankings.
NO recalculation - all metrics are already computed by CompetitiveDataCollector.

Author: Metis Development Team
Created: 2025-10-23
"""

import logging
from typing import Dict, List, Any, Optional


logger = logging.getLogger(__name__)


class DashboardMetricsRanker:
    """
    Extract and rank dashboard metrics (NO recalculation - data already exists).
    
    All metrics are already calculated in company_data by CompetitiveDataCollector._collect_single_company().
    This class simply extracts those values and applies competitive rankings.
    """
    
    def __init__(self, company_data: Dict[str, Dict], target_symbol: str):
        """
        Initialize ranker with company data.
        
        Args:
            company_data: Dictionary mapping symbols to comprehensive company data
            target_symbol: Target company symbol
        """
        self.company_data = company_data
        self.target_symbol = target_symbol
        
        # Filter to valid companies only
        self.valid_companies = {
            symbol: data for symbol, data in company_data.items()
            if data.get('available', True)
        }
        
        logger.info(f"DashboardMetricsRanker initialized for {target_symbol} with {len(self.valid_companies)} companies")
    
    def extract_and_rank_all_metrics(self) -> Dict[str, List[Dict]]:
        """
        Extract metrics from company_data and apply rankings.
        
        Returns:
            Dictionary with ranked metric data:
            {
                'market_cap_data': [{symbol, value, rank, company_name}, ...],
                'pe_ratio_data': [{symbol, value, rank, company_name}, ...],
                ...
            }
        """
        logger.info("Extracting and ranking all metrics")
        
        return {
            'market_cap_data': self._extract_and_rank(field='market_cap', higher_is_better=True),
            'pe_ratio_data': self._extract_and_rank(field='pe_ratio', higher_is_better=False),
            'roe_data': self._extract_and_rank(field='roe', higher_is_better=True),
            'roa_data': self._extract_and_rank(field='roa', higher_is_better=True),
            'revenue_growth_data': self._extract_and_rank(field='revenue_growth', higher_is_better=True),
            'debt_equity_data': self._extract_and_rank(field='debt_to_equity', higher_is_better=False),
            'combined_ratio_data': self._extract_and_rank(field='combined_ratio', higher_is_better=False),
            'gross_margin_data': self._extract_and_rank(field='gross_margin', higher_is_better=True),
            'operating_margin_data': self._extract_and_rank(field='operating_margin', higher_is_better=True),
            'net_margin_data': self._extract_and_rank(field='net_margin', higher_is_better=True),
        }
    
    def _extract_and_rank(self, field: str, higher_is_better: bool) -> List[Dict]:
        """
        Extract field from company_data and apply dense ranking with tie handling.
        
        Dense ranking means ties get the same rank, next rank continues (1,1,3 not 1,2,3).
        
        Args:
            field: Field name in company_data (e.g., 'pe_ratio', 'roe')
            higher_is_better: If True, rank 1 = highest value. If False, rank 1 = lowest value.
            
        Returns:
            List of dicts with symbol, value, rank, company_name
        """
        # Extract metric for all companies
        metric_data = []
        for symbol, data in self.valid_companies.items():
            value = data.get(field)
            
            # Skip if metric doesn't exist or is None
            if value is None:
                continue
            
            # For P/E, skip if 0 or negative (invalid P/E)
            if field == 'pe_ratio' and value <= 0:
                continue
            
            metric_data.append({
                'symbol': symbol,
                'value': value,
                'company_name': data.get('name', symbol)
            })
        
        # Sort and rank
        if not metric_data:
            logger.warning(f"No valid data for metric '{field}'")
            return []
        
        # Sort: higher_is_better=True means descending (best=highest), False means ascending (best=lowest)
        sorted_data = sorted(
            metric_data,
            key=lambda x: x['value'],
            reverse=higher_is_better
        )
        
        # Assign dense ranks (handle ties)
        current_rank = 1
        previous_value = None
        
        for i, item in enumerate(sorted_data):
            # If value changed from previous, increment rank
            if previous_value is not None and abs(item['value'] - previous_value) > 1e-6:
                current_rank = i + 1  # Jump to position (handles ties properly)
            
            item['rank'] = current_rank
            item['is_tied'] = False  # Will mark ties in second pass
            previous_value = item['value']
        
        # Second pass: mark which items are tied
        for i, item in enumerate(sorted_data):
            # Check if same rank as previous or next item
            is_tied = False
            if i > 0 and sorted_data[i-1]['rank'] == item['rank']:
                is_tied = True
            if i < len(sorted_data) - 1 and sorted_data[i+1]['rank'] == item['rank']:
                is_tied = True
            item['is_tied'] = is_tied
        
        logger.debug(f"Ranked {field}: {len(sorted_data)} companies")
        return sorted_data
    
    def calculate_overall_rank(self, company_symbol: str, all_ranked_metrics: Dict[str, List[Dict]]) -> int:
        """
        Calculate weighted overall rank from individual metric ranks.
        
        Args:
            company_symbol: Company to calculate rank for
            all_ranked_metrics: Output from extract_and_rank_all_metrics()
            
        Returns:
            Overall rank (1 = best)
        """
        # Weights for each metric (sum to 1.0)
        weights = {
            'pe_ratio_data': 0.15,
            'roe_data': 0.20,
            'revenue_growth_data': 0.15,
            'combined_ratio_data': 0.10,  # Insurance-specific, 0 for others
            'market_cap_data': 0.10,
            'debt_equity_data': 0.10,
            'gross_margin_data': 0.05,
            'operating_margin_data': 0.05,
            'net_margin_data': 0.10,
        }
        
        # Calculate weighted average of ranks
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric_key, weight in weights.items():
            metric_list = all_ranked_metrics.get(metric_key, [])
            
            # Find this company's rank in this metric
            company_rank = None
            for item in metric_list:
                if item['symbol'] == company_symbol:
                    company_rank = item['rank']
                    break
            
            if company_rank is not None:
                weighted_sum += company_rank * weight
                total_weight += weight
        
        # Average and round
        if total_weight == 0:
            logger.warning(f"No valid metrics for {company_symbol}, defaulting to rank 999")
            return 999
        
        overall_rank = round(weighted_sum / total_weight)
        return max(1, overall_rank)  # Ensure at least rank 1
    
    def get_target_rank_for_metric(self, metric_key: str, all_ranked_metrics: Dict[str, List[Dict]]) -> Optional[int]:
        """
        Get target company's rank for a specific metric.
        
        Args:
            metric_key: Metric key (e.g., 'pe_ratio_data')
            all_ranked_metrics: Output from extract_and_rank_all_metrics()
            
        Returns:
            Target's rank, or None if not found
        """
        metric_list = all_ranked_metrics.get(metric_key, [])
        for item in metric_list:
            if item['symbol'] == self.target_symbol:
                return item['rank']
        return None
    
    def get_peer_values_for_metric(self, metric_key: str, all_ranked_metrics: Dict[str, List[Dict]]) -> Dict[str, float]:
        """
        Get peer values (excluding target) for a specific metric.
        
        Args:
            metric_key: Metric key (e.g., 'pe_ratio_data')
            all_ranked_metrics: Output from extract_and_rank_all_metrics()
            
        Returns:
            Dictionary mapping peer symbols to their values
        """
        metric_list = all_ranked_metrics.get(metric_key, [])
        peer_values = {}
        
        for item in metric_list:
            if item['symbol'] != self.target_symbol:
                peer_values[item['symbol']] = item['value']
        
        return peer_values
    
    @staticmethod
    def generate_rank_qualifier(rank: int, total_companies: int, is_tied: bool = False, metric_name: str = None) -> str:
        """
        Generate rank qualifier string based on rank and context.
        
        Args:
            rank: Numeric rank (1 = best)
            total_companies: Total number of companies in comparison
            is_tied: Whether this rank is tied with another company
            metric_name: Name of the metric (for P/E special handling)
            
        Returns:
            Qualifier string like "best", "2nd cheapest" (P/E), "worst", "tied for 2nd"
        """
        # Special case: P/E Ratio uses "cheapest" not "best" (lower = better value)
        is_pe_ratio = metric_name and 'P/E' in metric_name
        best_word = "cheapest" if is_pe_ratio else "best"
        worst_word = "most expensive" if is_pe_ratio else "worst"
        
        if rank == 1:
            if is_tied:
                return f"tied for {best_word}"
            return best_word
        
        if rank == total_companies:
            if is_tied:
                return f"tied for {worst_word}"
            return worst_word
        
        # Middle ranks
        ordinal_suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
        suffix = ordinal_suffixes.get(rank % 10 if rank not in [11, 12, 13] else 0, 'th')
        
        if is_tied:
            return f"tied for {rank}{suffix} {best_word}"
        return f"{rank}{suffix} {best_word}"
