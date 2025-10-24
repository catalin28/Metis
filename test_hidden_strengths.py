"""
Test Hidden Strengths Generation with Analyst Consensus

Tests Sections 1, 2, 2.5 (NEW), and 3 together to verify the complete pipeline works.

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
from metis.models.report_schema_v2 import ValuationContext, format_percentage, normalize_percentage_display


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_hidden_strengths():
    """Test Sections 1-3: Executive Summary + Competitive Dashboard + Analyst Consensus + Hidden Strengths."""
    
    target_symbol = "CCL"
    
    logger.info("="*80)
    logger.info(f"TESTING SECTIONS 1, 2, 2.5, 3: {target_symbol}")
    logger.info("="*80)
    
    try:
        # Initialize services
        logger.info("\n[1/9] Initializing Services")
        generator = ReportGenerator()
        peer_service = PeerDiscoveryService()
        
        # Discover peers
        logger.info("\n[2/9] Discovering Peers")
        peers = await peer_service.identify_peers(
            symbol=target_symbol,
            max_peers=3
        )
        peer_symbols = [p['symbol'] for p in peers]
        logger.info(f"✓ Discovered {len(peer_symbols)} peers: {', '.join(peer_symbols)}")
        
        # Collect data (ONCE for all sections)
        logger.info("\n[3/9] Collecting Data (for all sections)")
        company_data = generator.data_collector.collect_all_company_data(
            target_symbol=target_symbol,
            peer_symbols=peer_symbols,
            max_workers=3
        )
        logger.info(f"✓ Collected data for {len(company_data)} companies")
        
        # Calculate metrics (ONCE for all sections)
        logger.info("\n[4/9] Calculating Comparative Metrics (for all sections)")
        comparative_metrics = generator.data_collector.calculate_comparative_metrics(
            company_data=company_data,
            target_symbol=target_symbol
        )
        logger.info(f"✓ P/E Gap: {comparative_metrics['pe_gap']:+.1f}x ({comparative_metrics['pe_gap_pct']:+.1f}%)")
        
        # Use dummy text for faster testing (web search takes time)
        logger.info("\n[5/9] Using Dummy Company Overview (fast test mode)")
        company_overview = "A leading financial services company with strong regional presence and competitive positioning."
        logger.info(f"✓ Company overview: {len(company_overview)} chars")
        
        # Generate Section 1: Executive Summary
        logger.info("\n[6/9] Generating Section 1: Executive Summary")
        executive_summary = await generator.generate_executive_summary(
            target_symbol=target_symbol,
            company_data=company_data,
            comparative_metrics=comparative_metrics,
            company_overview=company_overview
        )
        logger.info(f"✓ Executive Summary: {len(executive_summary.company_overview)} chars")
        
        # Generate Section 2: Competitive Dashboard
        logger.info("\n[7/9] Generating Section 2: Competitive Dashboard")
        competitive_dashboard = await generator.generate_competitive_dashboard(
            target_symbol=target_symbol,
            company_data=company_data,
            comparative_metrics=comparative_metrics
        )
        logger.info(f"✓ Competitive Dashboard: {len(competitive_dashboard.metrics)} metrics")
        
        # Generate Section 2.5: Analyst Consensus (NEW!)
        logger.info("\n[8/9] Generating Section 2.5: Analyst Consensus")
        
        # Build company names dict for analyst collector
        company_names = {
            target_symbol: company_data[target_symbol].get('name', target_symbol)
        }
        for symbol in peer_symbols:
            if symbol in company_data:
                company_names[symbol] = company_data[symbol].get('name', symbol)
        
        # Extract dashboard metrics for context
        dashboard_metrics = [metric.model_dump() for metric in competitive_dashboard.metrics]
        
        analyst_consensus = await generator.generate_analyst_consensus(
            target_symbol=target_symbol,
            peer_symbols=peer_symbols,
            company_names=company_names,
            dashboard_metrics=dashboard_metrics,
            hidden_strengths=None  # Will pass after Section 3
        )
        logger.info(f"✓ Analyst Consensus: {analyst_consensus.contrarian_opportunity_score} contrarian score")
        logger.info(f"   Target coverage: {analyst_consensus.target_analysis.coverage_breadth} firms")
        logger.info(f"   Target sentiment: {analyst_consensus.target_analysis.net_sentiment}")
        logger.info(f"   Recent actions: {analyst_consensus.target_analysis.recent_actions_90d} (90d)")
        
        # Generate Section 3: Hidden Strengths
        logger.info("\n[9/9] Generating Section 3: Hidden Strengths")
        hidden_strengths = await generator.generate_hidden_strengths(
            target_symbol=target_symbol,
            company_data=company_data,
            comparative_metrics=comparative_metrics
        )
        logger.info(f"✓ Hidden Strengths: {len(hidden_strengths.strengths)} strengths identified")
        
        # Calculate Valuation Context Summary
        target_data = company_data[target_symbol]
        current_pe = target_data.get('pe_ratio', 0)  # Actual current P/E, not target
        peer_avg_pe = comparative_metrics.get('peer_average_pe', 0)
        current_market_cap = target_data.get('market_cap', 0)
        
        # Extract target P/E from hidden strengths aggregate impact
        # Format: "+25-30% to fair value (19.5x-20.0x P/E)"
        import re
        aggregate_text = hidden_strengths.aggregate_impact_estimate
        pe_match = re.search(r'\((\d+\.?\d*)x-(\d+\.?\d*)x P/E\)', aggregate_text)
        if pe_match:
            target_pe_low = float(pe_match.group(1))
            target_pe_high = float(pe_match.group(2))
            target_pe = (target_pe_low + target_pe_high) / 2
        else:
            # Fallback: use peer average as target
            target_pe = peer_avg_pe if peer_avg_pe > 0 else current_pe * 1.2
        
        # Calculate implied market cap and gaps
        if current_pe > 0:
            implied_market_cap = current_market_cap * (target_pe / current_pe)
            valuation_gap_dollars = implied_market_cap - current_market_cap
            valuation_gap_percent = ((target_pe / current_pe) - 1) * 100
        else:
            implied_market_cap = current_market_cap
            valuation_gap_dollars = 0
            valuation_gap_percent = 0
        
        valuation_context = ValuationContext(
            current_pe=current_pe,
            peer_average_pe=peer_avg_pe,
            target_pe=target_pe,
            current_market_cap=current_market_cap,
            implied_market_cap=implied_market_cap,
            valuation_gap_percent=valuation_gap_percent,
            valuation_gap_dollars=valuation_gap_dollars
        )
        
        # Display Results
        logger.info("\n" + "="*80)
        logger.info("ANALYST CONSENSUS INSIGHTS!")
        logger.info("="*80)
        
        logger.info(f"\n📊 {target_symbol} Analyst Coverage:")
        logger.info(f"   Coverage: {analyst_consensus.target_analysis.coverage_breadth} firms")
        logger.info(f"   Recent Actions (90d): {analyst_consensus.target_analysis.recent_actions_90d}")
        logger.info(f"     - Upgrades: {analyst_consensus.target_analysis.upgrades_90d}")
        logger.info(f"     - Downgrades: {analyst_consensus.target_analysis.downgrades_90d}")
        logger.info(f"     - Maintains: {analyst_consensus.target_analysis.maintains_90d}")
        logger.info(f"   Net Sentiment: {analyst_consensus.target_analysis.net_sentiment}")
        
        logger.info(f"\n📈 Peer Comparison:")
        for peer in analyst_consensus.peer_analysis:
            logger.info(f"   {peer.symbol}: {peer.coverage_breadth} firms, {peer.recent_actions_90d} actions, {peer.net_sentiment}")
        
        logger.info(f"\n🎯 Contrarian Opportunity: {analyst_consensus.contrarian_opportunity_score}")
        logger.info(f"\n💡 Perception Gap:")
        logger.info(f"   {analyst_consensus.perception_gap_narrative[:200]}...")
        
        logger.info("\n" + "="*80)
        logger.info("HIDDEN STRENGTHS IDENTIFIED!")
        logger.info("="*80)
        
        logger.info(f"\n💎 Found {len(hidden_strengths.strengths)} Hidden Strengths:\n")
        for i, strength in enumerate(hidden_strengths.strengths, 1):
            logger.info(f"{i}. {strength.metric_name}")
            logger.info(f"   Target: {strength.target_value:.2f} | Peer Avg: {strength.peer_average:.2f}")
            logger.info(f"   Advantage: {strength.outperformance_magnitude}")
            logger.info(f"   Why Ignored: {strength.why_wall_street_ignores[:150]}...")
            logger.info(f"   Valuation Impact: {strength.valuation_impact}\n")
        
        logger.info(f"\n💰 Aggregate Impact:")
        logger.info(f"   {hidden_strengths.aggregate_impact_estimate}\n")
        
        # Display Valuation Context
        logger.info("\n" + "="*80)
        logger.info("VALUATION CONTEXT SUMMARY")
        logger.info("="*80)
        logger.info(f"\n📊 Current Valuation:")
        logger.info(f"   P/E Ratio: {valuation_context.current_pe:.2f}x")
        logger.info(f"   Market Cap: ${valuation_context.current_market_cap / 1e9:.2f}B")
        logger.info(f"\n🎯 Target Valuation:")
        logger.info(f"   Target P/E: {valuation_context.target_pe:.2f}x")
        logger.info(f"   Implied Market Cap: ${valuation_context.implied_market_cap / 1e9:.2f}B")
        logger.info(f"\n📈 Valuation Gap:")
        logger.info(f"   Gap: {valuation_context.valuation_gap_percent:+.1f}% ({format_percentage(valuation_context.valuation_gap_percent / 100)})")
        logger.info(f"   Dollar Impact: ${valuation_context.valuation_gap_dollars / 1e9:+.2f}B")
        logger.info(f"   Peer Average P/E: {valuation_context.peer_average_pe:.2f}x\n")
        
        # Save all 4 sections to JSON with formatted percentages
        def format_metrics_for_output(data, parent_key=''):
            """Add formatted percentage fields to metrics recursively"""
            if isinstance(data, dict):
                result = {}
                for key, value in data.items():
                    result[key] = format_metrics_for_output(value, key)
                    
                    # Add formatted percentage for decimal values that look like percentages
                    if isinstance(value, float):
                        # Check if this is a percentage field (between -1 and 1, excluding ratios/ranks)
                        is_percentage_field = any(term in key.lower() for term in [
                            'roe', 'roa', 'margin', 'growth', 'return'
                        ])
                        is_not_ratio = not any(term in key.lower() for term in [
                            'debt_to_equity', 'pe_ratio', 'rank', 'ratio', 'cap'
                        ])
                        
                        if is_percentage_field and is_not_ratio and -1 <= value <= 1:
                            result[f"{key}_pct"] = normalize_percentage_display(value)
                            result[f"{key}_formatted"] = format_percentage(value)
                        
                        # Special handling for target_value in metrics with percentage names
                        if key == 'target_value' and parent_key == 'metrics':
                            metric_name = data.get('metric_name', '').lower()
                            if any(term in metric_name for term in ['roe', 'roa', 'margin', 'growth']) and -1 <= value <= 1:
                                result['target_value_pct'] = normalize_percentage_display(value)
                                result['target_value_formatted'] = format_percentage(value)
                
                return result
            elif isinstance(data, list):
                return [format_metrics_for_output(item, parent_key) for item in data]
            return data
        
        output_data = {
            "target_symbol": target_symbol,
            "peer_symbols": peer_symbols,
            "valuation_context": valuation_context.model_dump(),
            "section_1_executive_summary": format_metrics_for_output(executive_summary.model_dump()),
            "section_2_competitive_dashboard": format_metrics_for_output(competitive_dashboard.model_dump(), 'dashboard'),
            "section_2_5_analyst_consensus": analyst_consensus.model_dump(),
            "section_3_hidden_strengths": format_metrics_for_output(hidden_strengths.model_dump())
        }
        
        output_file = f"test_sections_1_2_2.5_3_{target_symbol.lower()}.json"
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        logger.info(f"✓ Saved all 4 sections to: {output_file}")
        logger.info("\n" + "="*80)
        logger.info("SUCCESS! Sections 1, 2, 2.5 (Analyst Consensus), and 3 all working!")
        logger.info("="*80)
        
        return {
            'executive_summary': executive_summary,
            'competitive_dashboard': competitive_dashboard,
            'analyst_consensus': analyst_consensus,
            'hidden_strengths': hidden_strengths
        }
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(test_hidden_strengths())
