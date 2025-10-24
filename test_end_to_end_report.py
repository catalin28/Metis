"""
Test End-to-End Report Generation Pipeline

This script tests the complete competitive intelligence report generation pipeline:
1. Data collection from FMP API
2. Data transformation to Input models
3. LLM generation for all 6 sections
4. Assembly into complete CompetitiveIntelligenceReport

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


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_report_generation():
    """Test complete report generation for a sample company."""
    
    # Test configuration
    target_symbol = "WRB"
    peer_symbols = ["PGR", "TRV", "CB", "ALL"]  # 4 peers
    
    logger.info("="*80)
    logger.info(f"TESTING REPORT GENERATION: {target_symbol}")
    logger.info(f"Peers: {', '.join(peer_symbols)}")
    logger.info("="*80)
    
    try:
        # Initialize report generator
        logger.info("\n[1/5] Initializing Report Generator")
        generator = ReportGenerator()
        
        # Generate complete report
        logger.info("\n[2/5] Generating Complete Report (this will take several minutes)")
        report = await generator.generate_complete_report(
            target_symbol=target_symbol,
            peer_symbols=peer_symbols,
            max_workers=6
        )
        
        # Validate report structure
        logger.info("\n[3/5] Validating Report Structure")
        logger.info(f"✓ Report metadata: {report.metadata.target_symbol} v{report.metadata.version}")
        logger.info(f"✓ Peer group: {len(report.peer_group.peers)} peers")
        logger.info(f"✓ Data sources: {len(report.data_sources)} sources")
        logger.info(f"✓ Section 1 (Executive Summary): {len(report.executive_summary.key_findings)} findings")
        logger.info(f"✓ Section 2 (Competitive Dashboard): {len(report.competitive_dashboard.metrics)} metrics")
        logger.info(f"✓ Section 3 (Hidden Strengths): {len(report.hidden_strengths.hidden_strengths)} strengths")
        logger.info(f"✓ Section 4 (Steal Their Playbook): {len(report.steal_their_playbook.messaging_patterns)} patterns")
        logger.info(f"✓ Section 5 (Valuation Forensics): {len(report.valuation_forensics.valuation_gaps)} gap factors")
        logger.info(f"✓ Section 6 (Actionable Roadmap): {len(report.actionable_roadmap.problems)} problems identified")
        
        # Display key findings
        logger.info("\n[4/5] Key Report Insights")
        logger.info(f"\nCompany Overview:")
        logger.info(f"  {report.executive_summary.company_overview[:200]}...")
        
        logger.info(f"\nKey Findings:")
        for i, finding in enumerate(report.executive_summary.key_findings[:3], 1):
            logger.info(f"  {i}. {finding[:100]}...")
        
        logger.info(f"\nTop Recommendations:")
        for i, rec in enumerate(report.executive_summary.top_recommendations[:3], 1):
            logger.info(f"  {i}. {rec[:100]}...")
        
        # Save report to JSON
        logger.info("\n[5/5] Saving Report")
        output_file = f"test_report_{target_symbol.lower()}_full.json"
        
        with open(output_file, 'w') as f:
            json.dump(
                report.model_dump(),
                f,
                indent=2,
                default=str  # Handle datetime serialization
            )
        
        logger.info(f"✓ Report saved to: {output_file}")
        logger.info(f"✓ Report size: {Path(output_file).stat().st_size / 1024:.1f} KB")
        
        logger.info("\n" + "="*80)
        logger.info("REPORT GENERATION SUCCESSFUL!")
        logger.info("="*80)
        
        return report
        
    except Exception as e:
        logger.error(f"\n❌ Report generation failed: {str(e)}", exc_info=True)
        raise


async def test_single_section():
    """Test generation of a single section for faster iteration."""
    
    target_symbol = "AAPL"
    peer_symbols = ["MSFT", "GOOGL", "META"]
    
    logger.info("="*80)
    logger.info(f"TESTING SINGLE SECTION: Executive Summary for {target_symbol}")
    logger.info("="*80)
    
    try:
        generator = ReportGenerator()
        
        # Just test data collection and transformation
        logger.info("\n[1/2] Collecting Data")
        company_data = generator.data_collector.collect_all_company_data(
            target_symbol=target_symbol,
            peer_symbols=peer_symbols,
            max_workers=4
        )
        
        logger.info(f"✓ Collected data for {len(company_data)} companies")
        
        logger.info("\n[2/2] Calculating Comparative Metrics")
        comparative_metrics = generator.data_collector.calculate_comparative_metrics(
            company_data=company_data,
            target_symbol=target_symbol
        )
        
        logger.info(f"✓ Target P/E: {company_data[target_symbol]['pe_ratio']:.1f}x")
        logger.info(f"✓ Peer Avg P/E: {comparative_metrics['peer_average_pe']:.1f}x")
        logger.info(f"✓ P/E Gap: {comparative_metrics['pe_gap']:+.1f}x ({comparative_metrics['pe_gap_pct']:+.1f}%)")
        logger.info(f"✓ Overall Rank: #{comparative_metrics['overall_rank']}")
        logger.info(f"✓ Strengths: {len(comparative_metrics['strengths'])}")
        logger.info(f"✓ Weaknesses: {len(comparative_metrics['weaknesses'])}")
        logger.info(f"✓ Perception Gaps: {len(comparative_metrics['perception_gaps'])}")
        
        logger.info("\n" + "="*80)
        logger.info("DATA COLLECTION & TRANSFORMATION SUCCESSFUL!")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    import sys
    
    # Choose test mode
    if len(sys.argv) > 1 and sys.argv[1] == "single":
        asyncio.run(test_single_section())
    else:
        asyncio.run(test_report_generation())
