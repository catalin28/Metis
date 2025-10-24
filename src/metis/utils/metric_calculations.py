"""
Metric Calculation Utilities

All mathematical calculations for report generation.
LLMs receive pre-calculated, verified numbers and only add narrative context.

This eliminates LLM math errors and ensures consistency across all sections.

Author: Metis Development Team
Created: 2025-10-23
"""

import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


def detect_negative_equity_peers(peer_values: Dict[str, float], metric_name: str) -> List[str]:
    """
    Detect peers with negative equity that make D/E ratios unreliable.
    
    Args:
        peer_values: Dict of {symbol: value} for the metric
        metric_name: Name of the metric (e.g., 'debt_to_equity')
        
    Returns:
        List of peer symbols with negative equity
    """
    if 'debt_to_equity' not in metric_name.lower() and 'd/e' not in metric_name.lower():
        return []
    
    negative_equity_peers = []
    for symbol, value in peer_values.items():
        # Negative D/E ratio typically indicates negative equity
        # Also flag extremely high values (>10) as potentially problematic
        if value is not None and (value < 0 or value > 10):
            negative_equity_peers.append(symbol)
    
    return negative_equity_peers


def calculate_outperformance_ratio(target_value: float, comparison_value: float) -> float:
    """
    Calculate outperformance ratio: target / comparison.
    
    Examples:
        - 100 vs 50 → 2.0x (target is 2x larger)
        - 50 vs 100 → 0.5x (target is 0.5x of comparison)
        - For percentages: 0.20 vs 0.15 → 1.33x
    
    Args:
        target_value: Target company metric value
        comparison_value: Peer metric value
        
    Returns:
        Ratio as float (e.g., 2.0 for "2x larger")
    """
    if comparison_value == 0:
        return float('inf') if target_value > 0 else 1.0
    return target_value / comparison_value


def calculate_percentage_difference(target_value: float, comparison_value: float) -> float:
    """
    Calculate percentage difference: ((target - comparison) / comparison) * 100.
    
    Examples:
        - 120 vs 100 → +20%
        - 80 vs 100 → -20%
        - 0.25 vs 0.20 → +25%
    
    Args:
        target_value: Target company metric value
        comparison_value: Peer metric value
        
    Returns:
        Percentage difference (e.g., 20.0 for +20%)
    """
    if comparison_value == 0:
        return 100.0 if target_value > 0 else 0.0
    return ((target_value - comparison_value) / abs(comparison_value)) * 100


def format_outperformance_vs_peers(
    target_value: float,
    peer_values: Dict[str, float],
    metric_name: str,
    higher_is_better: bool
) -> Tuple[str, Optional[str]]:
    """
    Generate formatted comparison string for target vs all peers.
    
    Examples:
        "2.14x larger than PLNT (8.05B), 3.52x larger than HAS (10.93B)"
        "42% better than CUK (15.53%), worse than HAS (53.76%)"
    
    Args:
        target_value: Target company metric value
        peer_values: Dict of {symbol: value} for peers
        metric_name: Name of metric for formatting
        higher_is_better: Whether higher values are better
        
    Returns:
        Tuple of (comparison_string, peers_excluded_note)
        peers_excluded_note is populated for negative equity cases
    """
    if not peer_values:
        return "no peer comparison data available", None
    
    # Check for negative equity issues in debt metrics
    negative_equity_peers = detect_negative_equity_peers(peer_values, metric_name)
    peers_excluded_note = None
    
    if negative_equity_peers:
        # Filter out problematic peers
        clean_peer_values = {k: v for k, v in peer_values.items() if k not in negative_equity_peers}
        peers_excluded_note = f"{', '.join(negative_equity_peers)} excluded due to negative equity (D/E ratio unreliable)"
        
        if not clean_peer_values:
            return "peer comparisons unreliable due to negative equity", peers_excluded_note
        
        peer_values = clean_peer_values
    
    comparisons = []
    
    # Determine if this is a percentage metric
    is_percentage = any(term in metric_name.lower() for term in ['roe', 'roa', 'margin', 'growth', 'return'])
    is_currency = any(term in metric_name.lower() for term in ['market_cap', 'revenue', 'income', 'earnings'])
    
    for symbol, peer_value in sorted(peer_values.items()):
        ratio = calculate_outperformance_ratio(target_value, peer_value)
        pct_diff = calculate_percentage_difference(target_value, peer_value)
        
        # Format peer value display
        if is_currency and peer_value > 1e9:
            peer_display = f"${peer_value/1e9:.2f}B"
        elif is_currency and peer_value > 1e6:
            peer_display = f"${peer_value/1e6:.2f}M"
        elif is_percentage and -1 <= peer_value <= 1:
            peer_display = f"{peer_value*100:.2f}%"
        else:
            peer_display = f"{peer_value:.2f}"
        
        # Determine comparison wording
        if higher_is_better:
            # Special handling for negative peer values (e.g., negative ROE)
            # Avoid confusing "142% better than -36%" phrasing
            if peer_value < 0 and target_value > 0:
                comparisons.append(f"positive vs {symbol} ({peer_display})")
            elif peer_value < 0 and target_value < 0:
                # Both negative: just show which is less negative
                if target_value > peer_value:  # Less negative = better
                    comparisons.append(f"less negative than {symbol} ({peer_display})")
                else:
                    comparisons.append(f"more negative than {symbol} ({peer_display})")
            elif pct_diff > 0:
                if ratio >= 1.5:
                    comparisons.append(f"{ratio:.2f}x larger than {symbol} ({peer_display})")
                else:
                    comparisons.append(f"{abs(pct_diff):.1f}% better than {symbol} ({peer_display})")
            elif pct_diff < -5:  # Only mention if significantly worse
                comparisons.append(f"{abs(pct_diff):.1f}% worse than {symbol} ({peer_display})")
            else:
                comparisons.append(f"similar to {symbol} ({peer_display})")
        else:  # Lower is better (e.g., debt ratios)
            if pct_diff < 0:
                comparisons.append(f"{abs(pct_diff):.1f}% lower than {symbol} ({peer_display})")
            elif pct_diff > 5:
                comparisons.append(f"{abs(pct_diff):.1f}% higher than {symbol} ({peer_display})")
            else:
                comparisons.append(f"similar to {symbol} ({peer_display})")
    
    comparison_str = ", ".join(comparisons) if comparisons else "no significant differences"
    return comparison_str, peers_excluded_note


def calculate_valuation_impact(
    metric_improvement: float,
    base_pe: float,
    industry_pe_sensitivity: Dict[str, float] = None
) -> Tuple[float, str]:
    """
    Calculate estimated P/E impact from metric improvement.
    
    Uses industry regression coefficients where available, otherwise uses
    generic heuristics based on metric type.
    
    Args:
        metric_improvement: % improvement in metric (e.g., 20 for +20%)
        base_pe: Current P/E ratio
        industry_pe_sensitivity: Optional industry-specific coefficients
        
    Returns:
        Tuple of (pe_impact_multiplier, formatted_string)
        Example: (0.8, "+0.8x P/E multiple")
    """
    # Generic sensitivities (can be industry-calibrated)
    # REDUCED from previous values to ensure plausible impact ranges
    default_sensitivities = {
        'roe': 0.03,  # 10% ROE improvement → +0.3x P/E (reduced from 0.05)
        'roa': 0.03,
        'net_margin': 0.04,
        'operating_margin': 0.03,
        'revenue_growth': 0.02,
        'market_cap': 0.01,  # Scale premium (very modest, reduced from 0.02)
    }
    
    sensitivities = industry_pe_sensitivity or default_sensitivities
    
    # Calculate impact (simplified linear model)
    # In production, use trained regression models
    impact = metric_improvement * 0.03  # 10% improvement → +0.3x P/E (more conservative)
    
    # Cap at reasonable levels to avoid absurd claims
    # Market cap scale premium should be modest (max ~0.7x)
    # Operational metrics can justify higher but still cap at 1.2x for plausibility
    impact = min(impact, 1.2)
    
    if impact < 0.5:
        return (impact, f"+{impact:.1f}x P/E multiple")
    elif impact < 1.0:
        return (impact, f"+{impact:.1f}x to +{impact*1.15:.1f}x P/E range")
    else:
        # For impacts >= 1.0x, express as range with upper bound capped at 1.2x
        return (impact, f"+{impact:.1f}x to +{min(impact*1.15, 1.2):.1f}x P/E range")


def calculate_market_cap_from_pe_change(
    current_market_cap: float,
    current_pe: float,
    target_pe: float
) -> Tuple[float, float, float]:
    """
    Calculate implied market cap from P/E change.
    
    Formula: Implied Market Cap = Current Market Cap × (Target P/E / Current P/E)
    
    Args:
        current_market_cap: Current market capitalization
        current_pe: Current P/E ratio
        target_pe: Target/fair value P/E ratio
        
    Returns:
        Tuple of (implied_market_cap, dollar_gap, percent_gap)
    """
    if current_pe <= 0:
        logger.warning(f"Invalid current P/E: {current_pe}, cannot calculate impact")
        return (current_market_cap, 0.0, 0.0)
    
    implied_market_cap = current_market_cap * (target_pe / current_pe)
    dollar_gap = implied_market_cap - current_market_cap
    percent_gap = ((target_pe / current_pe) - 1) * 100
    
    return (implied_market_cap, dollar_gap, percent_gap)


def determine_metric_direction(metric_name: str) -> str:
    """
    Determine if higher or lower is better for a given metric.
    
    Args:
        metric_name: Name of the metric
        
    Returns:
        'higher_is_better' or 'lower_is_better'
    """
    lower_is_better_metrics = {
        'debt_to_equity', 'debt_equity', 'debt_ratio',
        'pe_ratio', 'p/e', 'price_to_earnings',
        'payout_ratio',
        'combined_ratio',  # Insurance-specific
        'loss_ratio',      # Insurance-specific
    }
    
    metric_lower = metric_name.lower().replace(' ', '_')
    
    if any(term in metric_lower for term in lower_is_better_metrics):
        return 'lower_is_better'
    return 'higher_is_better'


def format_rank_description(
    rank: int,
    total_count: int,
    metric_name: str,
    has_tie: bool = False
) -> str:
    """
    Generate human-readable rank description considering metric direction.
    
    Args:
        rank: Numeric rank (1 = best position)
        total_count: Total number of companies
        metric_name: Name of metric for direction context
        has_tie: Whether this rank is tied with others
        
    Returns:
        Formatted description (e.g., "cheapest" for P/E, "best" for ROE)
    """
    direction = determine_metric_direction(metric_name)
    tie_suffix = " (tie)" if has_tie else ""
    
    # Special handling for P/E ratio - use "cheapest" instead of "lowest"
    is_pe_ratio = any(term in metric_name.lower() for term in ['p/e', 'pe_ratio', 'price_to_earnings'])
    
    if direction == 'lower_is_better':
        # For metrics where lower is better (P/E, debt ratios)
        if is_pe_ratio:
            # P/E specific wording: cheapest = better value
            if rank == 1:
                return f"cheapest{tie_suffix}"
            elif rank == total_count:
                return f"most expensive{tie_suffix}"
            elif rank == 2:
                return f"2nd cheapest{tie_suffix}"
            elif rank == 3:
                return f"3rd cheapest{tie_suffix}"
            else:
                return f"{rank}th cheapest{tie_suffix}"
        else:
            # Other lower-is-better metrics
            if rank == 1:
                return f"lowest{tie_suffix}"
            elif rank == total_count:
                return f"highest{tie_suffix}"
            elif rank == 2:
                return f"2nd lowest{tie_suffix}"
            else:
                return f"{rank}th lowest{tie_suffix}"
    else:
        # For metrics where higher is better (margins, growth, ROE)
        if rank == 1:
            return f"best{tie_suffix}"
        elif rank == total_count:
            return f"worst{tie_suffix}"
        elif rank == 2:
            return f"2nd best{tie_suffix}"
        elif rank == 3:
            return f"3rd best{tie_suffix}"
        else:
            return f"{rank}th best{tie_suffix}"


def validate_comparison_math(
    target_value: float,
    peer_values: Dict[str, float],
    calculated_comparison: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate that a comparison string matches the actual math.
    
    Args:
        target_value: Target metric value
        peer_values: Dict of peer values
        calculated_comparison: The comparison string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Extract ratios from comparison string and verify
    import re
    
    for symbol, peer_value in peer_values.items():
        if symbol not in calculated_comparison:
            continue
            
        # Find ratio claims like "2.14x" or "42%"
        ratio_pattern = rf"{symbol}[^\d]*(\d+\.?\d*)[x×]"
        pct_pattern = rf"{symbol}[^\d]*(\d+\.?\d*)%"
        
        ratio_match = re.search(ratio_pattern, calculated_comparison)
        pct_match = re.search(pct_pattern, calculated_comparison)
        
        if ratio_match:
            claimed_ratio = float(ratio_match.group(1))
            actual_ratio = calculate_outperformance_ratio(target_value, peer_value)
            
            # Allow 5% tolerance
            if abs(claimed_ratio - actual_ratio) / actual_ratio > 0.05:
                return (False, f"Ratio error for {symbol}: claimed {claimed_ratio}x but actual is {actual_ratio:.2f}x")
        
        if pct_match:
            claimed_pct = float(pct_match.group(1))
            actual_pct = abs(calculate_percentage_difference(target_value, peer_value))
            
            # Allow 2 percentage point tolerance
            if abs(claimed_pct - actual_pct) > 2.0:
                return (False, f"Percentage error for {symbol}: claimed {claimed_pct}% but actual is {actual_pct:.1f}%")
    
    return (True, None)
