#!/usr/bin/env python3
"""
Generate Competitive Intelligence Report JSON

Usage:
    python generate_competitive_report.py AAPL
    python generate_competitive_report.py AAPL --peers MSFT,GOOGL,META
    python generate_competitive_report.py CCL --peers CUK,HAS,PLNT --output report.json
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from metis.assistants.peer_discovery_service import PeerDiscoveryService
from metis.data_collecting.competitive_data_collector import CompetitiveDataCollector
from metis.data_collecting.fmp_client import FMPClient
from metis.orchestrators.report_generator import ReportGenerator
from metis.models.report_schema_v2 import ReportMethodology

# Configure logging (suppress unless --verbose)
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


async def generate_report(
    symbol: str,
    peer_symbols: list = None,
    sections: list = None
) -> dict:
    """
    Generate competitive intelligence report for a symbol.
    
    Args:
        symbol: Target company symbol (e.g., 'AAPL')
        peer_symbols: Optional list of peer symbols. If None, will auto-discover.
        sections: List of section numbers to generate (default: [1, 2, 2.5, 3])
                 1 = Executive Summary
                 2 = Competitive Dashboard
                 2.5 = Analyst Consensus
                 3 = Hidden Strengths
    
    Returns:
        dict: Report data with all requested sections
    """
    if sections is None:
        sections = [1, 2, 2.5, 3]
    
    # Initialize services
    logger.info("Initializing services...")
    report_generator = ReportGenerator()
    peer_service = PeerDiscoveryService()
    
    # Discover or validate peers
    if peer_symbols is None:
        logger.info(f"Discovering peers for {symbol}...")
        peers = await peer_service.identify_peers(symbol=symbol, max_peers=3)
        peer_symbols = [p['symbol'] for p in peers]
        if not peer_symbols:
            raise ValueError(f"Could not find peers for {symbol}")
        logger.info(f"Discovered {len(peer_symbols)} peers: {', '.join(peer_symbols)}")
    else:
        logger.info(f"Using provided peers: {', '.join(peer_symbols)}")
    
    # Collect data for all companies
    logger.info(f"Collecting data for {symbol} and {len(peer_symbols)} peers...")
    company_data = report_generator.data_collector.collect_all_company_data(
        target_symbol=symbol,
        peer_symbols=peer_symbols,
        max_workers=3
    )
    
    if symbol not in company_data or not company_data[symbol].get('available'):
        raise ValueError(f"Could not collect data for {symbol}")
    
    # Calculate comparative metrics
    logger.info("Calculating comparative metrics...")
    comparative_metrics = report_generator.data_collector.calculate_comparative_metrics(
        company_data=company_data,
        target_symbol=symbol
    )
    
    # Get target company data
    target_data = company_data[symbol]
    
    # Prepare valuation context (always needed)
    peer_benchmark_pe = comparative_metrics.get('peer_average_pe', 0)
    current_pe = target_data.get('pe_ratio', 0)
    current_market_cap = target_data.get('market_cap', 0)
    
    valuation_context = {
        'current_pe': current_pe,
        'peer_average_pe': peer_benchmark_pe,
        'peer_benchmark_pe': peer_benchmark_pe,  # Renamed for clarity
        'current_market_cap': current_market_cap,
        'implied_market_cap': 0,
        'implied_market_cap_method': 'current_market_cap × (peer_benchmark_pe / current_pe)',
        'premium_vs_peer_percent': 0,  # Basis: peer average
        'downside_to_peer_multiple_percent': 0,  # Basis: current
        'valuation_gap_dollars': 0
    }
    
    # Calculate implied values
    if current_pe > 0 and peer_benchmark_pe > 0:
        ratio = peer_benchmark_pe / current_pe
        valuation_context['implied_market_cap'] = current_market_cap * ratio
        
        # Premium vs peer (basis = peer): (current - peer) / peer × 100
        valuation_context['premium_vs_peer_percent'] = ((current_pe - peer_benchmark_pe) / peer_benchmark_pe) * 100
        
        # Downside to compress to peer (basis = current): (implied - current) / current × 100
        valuation_context['downside_to_peer_multiple_percent'] = (ratio - 1) * 100
        
        valuation_context['valuation_gap_dollars'] = valuation_context['implied_market_cap'] - current_market_cap
    
    # Build peer group with selection rationale
    logger.info("Generating peer group structure...")
    peer_group = report_generator._create_peer_group(
        target_symbol=symbol,
        company_data=company_data
    )
    
    # Create methodology section (auto-populated with defaults)
    methodology = ReportMethodology()
    
    # Build result
    result = {
        'target_symbol': symbol,
        'peer_symbols': peer_symbols,
        'valuation_context': valuation_context,
        'methodology': methodology.model_dump(),
        'peer_group': peer_group.model_dump()
    }
    
    # Prepare company names for analyst consensus
    company_names = {}
    for sym in [symbol] + peer_symbols:
        if sym in company_data:
            company_names[sym] = company_data[sym].get('name', sym)
    
    # Generate requested sections
    dashboard_metrics = None
    
    if 1 in sections:
        logger.info("Generating Section 1: Executive Summary...")
        exec_summary = await report_generator.generate_executive_summary(
            target_symbol=symbol,
            company_data=company_data,
            comparative_metrics=comparative_metrics,
            company_overview="A leading company in its sector."  # Placeholder
        )
        result['section_1_executive_summary'] = exec_summary.model_dump()
    
    if 2 in sections:
        logger.info("Generating Section 2: Competitive Dashboard...")
        dashboard = await report_generator.generate_competitive_dashboard(
            target_symbol=symbol,
            company_data=company_data,
            comparative_metrics=comparative_metrics
        )
        result['section_2_competitive_dashboard'] = dashboard.model_dump()
        dashboard_metrics = [metric.model_dump() for metric in dashboard.metrics]
    
    if 2.5 in sections:
        logger.info("Generating Section 2.5: Analyst Consensus...")
        analyst_consensus = await report_generator.generate_analyst_consensus(
            target_symbol=symbol,
            peer_symbols=peer_symbols,
            company_data=company_data,
            dashboard_metrics=dashboard_metrics,
            hidden_strengths=None
        )
        result['section_2_5_analyst_consensus'] = analyst_consensus.model_dump()
    
    if 3 in sections:
        logger.info("Generating Section 3: Hidden Strengths...")
        hidden_strengths = await report_generator.generate_hidden_strengths(
            target_symbol=symbol,
            company_data=company_data,
            comparative_metrics=comparative_metrics
        )
        result['section_3_hidden_strengths'] = hidden_strengths.model_dump()
    
    logger.info("Report generation complete")
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Generate competitive intelligence report JSON',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-discover peers
  python generate_competitive_report.py AAPL
  
  # Specify peers
  python generate_competitive_report.py AAPL --peers MSFT,GOOGL,META
  
  # Generate specific sections only
  python generate_competitive_report.py CCL --peers CUK,HAS,PLNT --sections 1,2,3
  
  # Save to file
  python generate_competitive_report.py AAPL --output report.json
  
  # Verbose logging
  python generate_competitive_report.py AAPL --verbose
        """
    )
    
    parser.add_argument(
        'symbol',
        type=str,
        help='Target company symbol (e.g., AAPL, MSFT, CCL)'
    )
    
    parser.add_argument(
        '--peers',
        type=str,
        help='Comma-separated list of peer symbols (e.g., MSFT,GOOGL,META). If not provided, peers will be auto-discovered.'
    )
    
    parser.add_argument(
        '--sections',
        type=str,
        default='1,2,2.5,3',
        help='Comma-separated section numbers to generate (default: 1,2,2.5,3)'
    )
    
    parser.add_argument(
        '--output',
        '-o',
        type=str,
        help='Output file path (default: print to stdout)'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--compact',
        '-c',
        action='store_true',
        help='Output compact JSON without indentation (default: pretty-printed)'
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger('metis').setLevel(logging.INFO)
    
    # Parse peer symbols
    peer_symbols = None
    if args.peers:
        peer_symbols = [s.strip().upper() for s in args.peers.split(',')]
    
    # Parse sections
    sections = []
    for s in args.sections.split(','):
        s = s.strip()
        if s == '2.5':
            sections.append(2.5)
        else:
            sections.append(int(s))
    
    try:
        # Generate report (run async function)
        result = asyncio.run(generate_report(
            symbol=args.symbol.upper(),
            peer_symbols=peer_symbols,
            sections=sections
        ))
        
        # Output JSON (always pretty-print by default)
        json_kwargs = {'indent': 2}
        if hasattr(args, 'compact') and args.compact:
            json_kwargs = {}
        
        json_output = json.dumps(result, **json_kwargs)
        
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(json_output)
            if args.verbose:
                logger.info(f"Report saved to {output_path}")
        else:
            print(json_output)
        
        return 0
    
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
