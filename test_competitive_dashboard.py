"""
Test Competitive Dashboard Generation

Tests Executive Summary + Competitive Dashboard sections together
to verify the complete pipeline works with data reuse.

Author: Metis Development Team
Created: 2025-10-23
"""

import asyncio
import logging
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from metis.orchestrators.report_generator import ReportGenerator
from metis.assistants.peer_discovery_service import PeerDiscoveryService


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_competitive_dashboard():
    """Test Executive Summary + Competitive Dashboard generation."""
    
    target_symbol = "CIB"
    
    logger.info("="*80)
    logger.info(f"TESTING COMPETITIVE DASHBOARD: {target_symbol}")
    logger.info("="*80)
    
    try:
        # Initialize services
        logger.info("\n[1/7] Initializing Services")
        generator = ReportGenerator()
        peer_service = PeerDiscoveryService()
        
        # Discover peers automatically
        logger.info("\n[2/7] Discovering Peers")
        peers = await peer_service.identify_peers(
            symbol=target_symbol,
            max_peers=3
        )
        peer_symbols = [p['symbol'] for p in peers]
        logger.info(f"✓ Discovered {len(peer_symbols)} peers: {', '.join(peer_symbols)}")
        
        # Collect data (ONCE for both sections)
        logger.info("\n[3/7] Collecting Data (for both sections)")
        company_data = generator.data_collector.collect_all_company_data(
            target_symbol=target_symbol,
            peer_symbols=peer_symbols,
            max_workers=3
        )
        logger.info(f"✓ Collected data for {len(company_data)} companies")
        
        # Calculate metrics (ONCE for both sections)
        logger.info("\n[4/7] Calculating Comparative Metrics (for both sections)")
        comparative_metrics = generator.data_collector.calculate_comparative_metrics(
            company_data=company_data,
            target_symbol=target_symbol
        )
        logger.info(f"✓ P/E Gap: {comparative_metrics['pe_gap']:+.1f}x ({comparative_metrics['pe_gap_pct']:+.1f}%)")
        
        # Web search (for Executive Summary)
        logger.info("\n[5/7] Researching Company via Web Search")
        company_overview_result = generator.llm_agent.research_company_with_web_search(
            symbol=target_symbol,
            company_name=company_data[target_symbol]['name'],
            industry=company_data[target_symbol].get('industry', 'Technology'),
            sector=company_data[target_symbol].get('sector', 'Technology')
        )
        company_overview = company_overview_result['company_overview']
        logger.info(f"✓ Company overview: {len(company_overview)} chars")
        
        # Generate Section 1: Executive Summary
        logger.info("\n[6/7] Generating Section 1: Executive Summary")
        executive_summary = await generator.generate_executive_summary(
            target_symbol=target_symbol,
            company_data=company_data,
            comparative_metrics=comparative_metrics,
            company_overview=company_overview
        )
        logger.info(f"✓ Executive Summary generated: {len(executive_summary.company_overview)} char overview")
        
        # Generate Section 2: Competitive Dashboard (REUSES same data!)
        logger.info("\n[7/7] Generating Section 2: Competitive Dashboard")
        logger.info("      (Reusing data from steps 3-4, NO new API calls)")
        competitive_dashboard = await generator.generate_competitive_dashboard(
            target_symbol=target_symbol,
            company_data=company_data,  # REUSE!
            comparative_metrics=comparative_metrics  # REUSE!
        )
        logger.info(f"✓ Competitive Dashboard generated: {len(competitive_dashboard.metrics)} metrics")
        
        # Display Dashboard Results
        logger.info("\n" + "="*80)
        logger.info("COMPETITIVE DASHBOARD GENERATED!")
        logger.info("="*80)
        
        logger.info(f"\nOverall Target Rank: #{competitive_dashboard.overall_target_rank}")
        logger.info(f"Perception Gap Count: {competitive_dashboard.perception_gap_count}")
        
        logger.info(f"\nKey Strengths:")
        logger.info(f"  {competitive_dashboard.key_strengths_summary}")
        
        logger.info(f"\nKey Weaknesses:")
        logger.info(f"  {competitive_dashboard.key_weaknesses_summary}")
        
        logger.info(f"\n📊 Dashboard Metrics ({len(competitive_dashboard.metrics)} total):")
        for i, metric in enumerate(competitive_dashboard.metrics, 1):
            peer_avg = sum(metric.peer_values.values()) / len(metric.peer_values) if metric.peer_values else 0
            logger.info(f"\n  {i}. {metric.metric_name}")
            logger.info(f"     Target: {metric.target_value:.2f} (Rank #{metric.target_rank})")
            logger.info(f"     Peer Avg: {peer_avg:.2f}")
            logger.info(f"     Perception: {metric.market_perception.value}")
            logger.info(f"     Explanation: {metric.perception_explanation[:150]}...")
        
        # Save both sections to JSON
        output_data = {
            "target_symbol": target_symbol,
            "peer_symbols": peer_symbols,
            "executive_summary": executive_summary.model_dump(),
            "competitive_dashboard": competitive_dashboard.model_dump()
        }
        
        output_file = f"test_dashboard_{target_symbol.lower()}.json"
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        logger.info(f"\n✓ Saved both sections to: {output_file}")
        logger.info("\n" + "="*80)
        logger.info("SUCCESS! Both Executive Summary and Competitive Dashboard working!")
        logger.info("="*80)
        
        return {
            'executive_summary': executive_summary,
            'competitive_dashboard': competitive_dashboard
        }
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(test_competitive_dashboard())
