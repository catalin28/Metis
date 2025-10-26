"""
High-level API functions for external projects.

These functions provide a clean, simple interface for generating
competitive intelligence and swing trading analysis.
"""

import asyncio
from typing import Dict, Any, Optional, List

# Import from internal metis modules (avoid circular imports with root-level scripts)
from metis.swing_trading import SwingTraderAnalyzer
from metis.assistants.peer_discovery_service import PeerDiscoveryService
from metis.data_collecting.fmp_client import FMPClient
from metis.data_collecting.competitive_data_collector import CompetitiveDataCollector
from metis.orchestrators.report_generator import ReportGenerator
from metis.models.report_schema_v2 import ReportMethodology


async def generate_competitive_intelligence(
    symbol: str,
    peer_symbols: Optional[List[str]] = None,
    sections: Optional[List[int]] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate competitive intelligence report for a company.
    
    Args:
        symbol: Target company ticker symbol (e.g., 'AAPL', 'MSFT')
        peer_symbols: Optional list of peer symbols. If None, auto-discovers peers.
        sections: List of section numbers to generate (default: [1, 2, 2.5, 3])
                 1 = Executive Summary
                 2 = Competitive Dashboard
                 2.5 = Analyst Consensus
                 3 = Hidden Strengths
        api_key: Optional OpenAI API key (uses env var if not provided)
    
    Returns:
        Dictionary containing the complete competitive intelligence report
    
    Example:
        >>> import asyncio
        >>> from metis import generate_competitive_intelligence
        >>> 
        >>> report = asyncio.run(generate_competitive_intelligence('AAPL'))
        >>> print(report['target_symbol'])
        'AAPL'
        >>> print(report['valuation_context']['premium_vs_peer_percent'])
        15.23
    """
    if sections is None:
        sections = [1, 2, 2.5, 3]
    
    # Initialize services
    report_generator = ReportGenerator()
    peer_service = PeerDiscoveryService()
    
    # Discover or validate peers
    if peer_symbols is None:
        peers = await peer_service.identify_peers(symbol=symbol, max_peers=3)
        peer_symbols = [p['symbol'] for p in peers]
        if not peer_symbols:
            raise ValueError(f"Could not find peers for {symbol}")
    
    # Collect data for all companies
    company_data = report_generator.data_collector.collect_all_company_data(
        target_symbol=symbol,
        peer_symbols=peer_symbols,
        max_workers=3
    )
    
    if symbol not in company_data or not company_data[symbol].get('available'):
        raise ValueError(f"Could not collect data for {symbol}")
    
    # Calculate comparative metrics
    comparative_metrics = report_generator.data_collector.calculate_comparative_metrics(
        company_data=company_data,
        target_symbol=symbol
    )
    
    # Get target company data
    target_data = company_data[symbol]
    
    # Prepare valuation context
    peer_benchmark_pe = round(comparative_metrics.get('peer_average_pe', 0), 2)
    current_pe = round(target_data.get('pe_ratio', 0), 2)
    current_market_cap = round(target_data.get('market_cap', 0))
    
    valuation_context = {
        'current_pe': current_pe,
        'peer_average_pe': peer_benchmark_pe,
        'peer_benchmark_pe': peer_benchmark_pe,
        'current_market_cap': current_market_cap,
        'implied_market_cap': 0,
        'implied_market_cap_method': 'current_market_cap × (peer_benchmark_pe / current_pe)',
        'premium_vs_peer_percent': 0,
        'downside_to_peer_multiple_percent': 0,
        'valuation_gap_dollars': 0
    }
    
    # Calculate implied values
    if current_pe > 0 and peer_benchmark_pe > 0:
        ratio = peer_benchmark_pe / current_pe
        valuation_context['implied_market_cap'] = round(current_market_cap * ratio)
        valuation_context['premium_vs_peer_percent'] = round(((current_pe - peer_benchmark_pe) / peer_benchmark_pe) * 100, 2)
        valuation_context['downside_to_peer_multiple_percent'] = round((ratio - 1) * 100, 2)
        valuation_context['valuation_gap_dollars'] = round(valuation_context['implied_market_cap'] - current_market_cap)
    
    # Build peer group with selection rationale
    peer_group = report_generator._create_peer_group(
        target_symbol=symbol,
        company_data=company_data
    )
    
    # Create methodology section
    methodology = ReportMethodology()
    
    # Build result
    result = {
        'target_symbol': symbol,
        'peer_symbols': peer_symbols,
        'valuation_context': valuation_context,
        'methodology': methodology.model_dump(),
        'peer_group': peer_group.model_dump()
    }
    
    # Generate requested sections
    dashboard_metrics = None
    dashboard = None
    
    # Generate dashboard FIRST to get accurate overall_target_rank
    if 2 in sections:
        dashboard = await report_generator.generate_competitive_dashboard(
            target_symbol=symbol,
            company_data=company_data,
            comparative_metrics=comparative_metrics
        )
        result['section_2_competitive_dashboard'] = dashboard.model_dump()
        dashboard_metrics = [metric.model_dump() for metric in dashboard.metrics]
        comparative_metrics['overall_rank'] = dashboard.overall_target_rank
    
    if 1 in sections:
        exec_summary = await report_generator.generate_executive_summary(
            target_symbol=symbol,
            company_data=company_data,
            comparative_metrics=comparative_metrics,
            company_overview="A leading company in its sector."
        )
        result['section_1_executive_summary'] = exec_summary.model_dump()
    
    if 2.5 in sections:
        analyst_consensus = await report_generator.generate_analyst_consensus(
            target_symbol=symbol,
            peer_symbols=peer_symbols,
            company_data=company_data,
            dashboard_metrics=dashboard_metrics,
            hidden_strengths=None
        )
        result['section_2_5_analyst_consensus'] = analyst_consensus.model_dump()
    
    if 3 in sections:
        hidden_strengths = await report_generator.generate_hidden_strengths(
            target_symbol=symbol,
            company_data=company_data,
            comparative_metrics=comparative_metrics
        )
        result['section_3_hidden_strengths'] = hidden_strengths.model_dump()
    
    return result


async def generate_swing_trading_analysis(
    symbol: str,
    peer_symbols: Optional[List[str]] = None,
    generate_narrative: bool = True,
    model: str = "gpt-4",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate complete swing trading analysis for a company.
    
    Args:
        symbol: Target company ticker symbol
        peer_symbols: Optional list of peer symbols
        generate_narrative: Whether to generate LLM narrative (default: True)
        model: LLM model to use for narrative generation (default: gpt-4)
        api_key: Optional OpenAI API key
    
    Returns:
        Dictionary with:
            - 'competitive_intelligence': Full CI report
            - 'signals': Structured trading signals (dict)
            - 'narrative': LLM-generated trading analysis (if generate_narrative=True)
    
    Example:
        >>> import asyncio
        >>> from metis import generate_swing_trading_analysis
        >>> 
        >>> analysis = asyncio.run(generate_swing_trading_analysis('TSLA'))
        >>> print(analysis['signals']['overall_bias'])
        'long'
        >>> print(analysis['signals']['conviction_score'])
        8
        >>> print(analysis['narrative'][:200])
        'Tesla (TSLA) Swing Trading Analysis...'
    """
    # Step 1: Generate competitive intelligence
    ci_report = await generate_competitive_intelligence(
        symbol=symbol,
        peer_symbols=peer_symbols,
        sections=[1, 2, 2.5, 3]
    )
    
    # Step 2: Extract trading signals
    analyzer = SwingTraderAnalyzer(api_key=api_key)
    signals = analyzer.analyze_from_dict(ci_report)
    
    # Step 3: Generate narrative if requested
    narrative = None
    if generate_narrative:
        narrative = await analyzer.generate_trading_narrative(
            report_data=ci_report,
            model=model
        )
    
    return {
        'competitive_intelligence': ci_report,
        'signals': signals.model_dump(),
        'narrative': narrative
    }


async def discover_peers(
    symbol: str,
    max_peers: int = 5,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Discover peer companies for a given symbol.
    
    Args:
        symbol: Target company ticker symbol
        max_peers: Maximum number of peers to return (default: 5)
        api_key: Optional FMP API key
    
    Returns:
        Dictionary with:
            - 'target': Target company info
            - 'peers': List of peer companies with similarity scores
    
    Example:
        >>> import asyncio
        >>> from metis import discover_peers
        >>> 
        >>> result = asyncio.run(discover_peers('NVDA', max_peers=3))
        >>> for peer in result['peers']:
        ...     print(f"{peer['symbol']}: {peer['similarity_score']:.2f}")
        AMD: 0.95
        INTC: 0.89
        QCOM: 0.87
    """
    fmp_client = FMPClient()
    peer_service = PeerDiscoveryService(fmp_client)
    
    peers = await peer_service.discover_peers(symbol, max_peers=max_peers)
    
    return {
        'target': {
            'symbol': symbol,
            'name': peers[0]['company_name'] if peers else None
        },
        'peers': peers
    }


# Synchronous wrappers for convenience
def generate_competitive_intelligence_sync(
    symbol: str,
    peer_symbols: Optional[List[str]] = None,
    sections: Optional[List[int]] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Synchronous wrapper for generate_competitive_intelligence()."""
    return asyncio.run(generate_competitive_intelligence(
        symbol=symbol,
        peer_symbols=peer_symbols,
        sections=sections,
        api_key=api_key
    ))


def generate_swing_trading_analysis_sync(
    symbol: str,
    peer_symbols: Optional[List[str]] = None,
    generate_narrative: bool = True,
    model: str = "gpt-4",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Synchronous wrapper for generate_swing_trading_analysis()."""
    return asyncio.run(generate_swing_trading_analysis(
        symbol=symbol,
        peer_symbols=peer_symbols,
        generate_narrative=generate_narrative,
        model=model,
        api_key=api_key
    ))


def discover_peers_sync(
    symbol: str,
    max_peers: int = 5,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Synchronous wrapper for discover_peers()."""
    return asyncio.run(discover_peers(
        symbol=symbol,
        max_peers=max_peers,
        api_key=api_key
    ))
