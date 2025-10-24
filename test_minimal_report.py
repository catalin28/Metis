"""
Minimal Report Generation Test

Tests just the Executive Summary section to verify the complete pipeline works
without generating all 6 sections (faster, cheaper testing).

Author: Metis Development Team
Created: 2025-10-22
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


async def test_executive_summary_only():
    """Test just Executive Summary generation (cheapest test)."""
    
    target_symbol = "CIB"
    
    logger.info("="*80)
    logger.info(f"TESTING EXECUTIVE SUMMARY: {target_symbol} (auto peer discovery)")
    logger.info("="*80)
    
    try:
        # Initialize services
        logger.info("\n[1/6] Initializing Services")
        generator = ReportGenerator()
        peer_service = PeerDiscoveryService()
        
        # Discover peers automatically
        logger.info("\n[2/6] Discovering Peers")
        peers = await peer_service.identify_peers(
            symbol=target_symbol,
            max_peers=3  # Just 3 peers for speed
        )
        peer_symbols = [p['symbol'] for p in peers]
        logger.info(f"✓ Discovered {len(peer_symbols)} peers: {', '.join(peer_symbols)}")
        
        # Collect data
        logger.info("\n[3/6] Collecting Data")
        company_data = generator.data_collector.collect_all_company_data(
            target_symbol=target_symbol,
            peer_symbols=peer_symbols,
            max_workers=3
        )
        logger.info(f"✓ Collected data for {len(company_data)} companies")
        
        # Calculate metrics
        logger.info("\n[4/6] Calculating Comparative Metrics")
        comparative_metrics = generator.data_collector.calculate_comparative_metrics(
            company_data=company_data,
            target_symbol=target_symbol
        )
        logger.info(f"✓ P/E Gap: {comparative_metrics['pe_gap']:+.1f}x ({comparative_metrics['pe_gap_pct']:+.1f}%)")
        
        # Web search
        logger.info("\n[5/6] Researching Company via Web Search")
        company_overview_result = generator.llm_agent.research_company_with_web_search(
            symbol=target_symbol,
            company_name=company_data[target_symbol]['name'],
            industry=company_data[target_symbol].get('industry', 'Technology'),
            sector=company_data[target_symbol].get('sector', 'Technology')
        )
        company_overview = company_overview_result['company_overview']
        logger.info(f"✓ Company overview: {len(company_overview)} chars")
        
        # Generate Executive Summary
        logger.info("\n[6/6] Generating Executive Summary (LLM call)")
        executive_summary = await generator.generate_executive_summary(
            target_symbol=target_symbol,
            company_data=company_data,
            comparative_metrics=comparative_metrics,
            company_overview=company_overview
        )
        
        # Display results
        logger.info("\n" + "="*80)
        logger.info("EXECUTIVE SUMMARY GENERATED!")
        logger.info("="*80)
        
        logger.info(f"\nCompany Overview ({len(executive_summary.company_overview)} chars):")
        logger.info(f"  {executive_summary.company_overview[:200]}...")
        
        logger.info(f"\nKey Finding:")
        logger.info(f"  {executive_summary.key_finding[:300]}...")
        
        logger.info(f"\nRoot Cause:")
        logger.info(f"  {executive_summary.root_cause[:300]}...")
        
        logger.info(f"\nTop Recommendations ({len(executive_summary.top_recommendations)} recommendations):")
        for i, rec in enumerate(executive_summary.top_recommendations, 1):
            logger.info(f"  {i}. {rec[:150]}...")
        
        # Save to JSON
        output_file = f"test_executive_summary_{target_symbol.lower()}.json"
        with open(output_file, 'w') as f:
            json.dump(
                executive_summary.model_dump(),
                f,
                indent=2,
                default=str
            )
        
        logger.info(f"\n✓ Saved to: {output_file}")
        logger.info("\n" + "="*80)
        logger.info("SUCCESS!")
        logger.info("="*80)
        
        return executive_summary
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(test_executive_summary_only())
