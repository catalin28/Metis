#!/usr/bin/env python3
"""
Generate Complete Swing Trading Report for MO (Altria Group)

This script:
1. Generates competitive intelligence report for MO
2. Extracts trading signals
3. Generates LLM-powered swing trading narrative
4. Saves all outputs
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import async generate_report directly, not the sync wrapper
from generate_competitive_report import generate_report
from metis.swing_trading import SwingTraderAnalyzer


async def main_async():
    symbol = 'MO'
    
    print("=" * 80)
    print(f"GENERATING COMPLETE SWING TRADING REPORT FOR {symbol}")
    print("=" * 80)
    
    # Step 1: Generate competitive intelligence report
    print(f"\n📊 Step 1: Generating competitive intelligence report for {symbol}...")
    print("   (This may take 30-60 seconds - fetching financial data, discovering peers, running analysis)")
    try:
        mo_report = await generate_report(
            symbol=symbol,
            peer_symbols=None,  # Auto-discover peers
            sections=[1, 2, 2.5, 3]  # All relevant sections
        )
        
        # Save CI report
        import json
        with open(f'{symbol.lower()}_competitive_intelligence.json', 'w') as f:
            json.dump(mo_report, f, indent=2)
        
        print(f"✓ Competitive intelligence report generated")
        print(f"  - Target: {mo_report['target_symbol']}")
        print(f"  - Peers: {', '.join(mo_report['peer_symbols'])}")
        print(f"  - Current P/E: {mo_report['valuation_context']['current_pe']:.2f}x")
        print(f"  - Peer Avg P/E: {mo_report['valuation_context']['peer_average_pe']:.2f}x")
        print(f"  - Premium: {mo_report['valuation_context']['premium_vs_peer_percent']:+.2f}%")
        
    except Exception as e:
        print(f"\n❌ Error generating competitive intelligence report: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Step 2: Generate swing trading analysis
    print(f"\n📈 Step 2: Generating swing trading analysis...")
    print("   (Extracting signals + calling LLM for narrative - may take 20-40 seconds)")
    
    try:
        analyzer = SwingTraderAnalyzer()
        
        # Extract signals first (sync)
        signals = analyzer.analyze_from_dict(mo_report)
        prompt = analyzer.generate_llm_prompt(mo_report)
        
        # Save signals and prompt
        import json
        with open(f'{symbol.lower()}_trading_signals.json', 'w') as f:
            json.dump(signals.model_dump(), f, indent=2)
        
        with open(f'{symbol.lower()}_trading_prompt.txt', 'w') as f:
            f.write(prompt)
        
        # Generate narrative asynchronously
        narrative = await analyzer.generate_trading_narrative(
            report_data=mo_report,
            model='gpt-4',
            temperature=0.7
        )
        
        # Save narrative
        with open(f'{symbol.lower()}_swing_trading_report.md', 'w') as f:
            f.write(narrative)
        
        print(f"\n✓ Swing trading analysis complete!")
        
    except Exception as e:
        print(f"\n❌ Error generating swing trading analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Step 3: Display summary
    print("\n" + "=" * 80)
    print("📋 ANALYSIS SUMMARY")
    print("=" * 80)
    
    print(f"\n🎯 Trading Signals:")
    print(f"  Symbol: {signals.target_symbol}")
    print(f"  Company: {signals.target_company_name}")
    print(f"  Overall Bias: {signals.overall_bias.value.upper()}")
    print(f"  Risk Level: {signals.risk_level.upper()}")
    print(f"  Conviction Score: {signals.conviction_score}/10")
    
    print(f"\n💰 Valuation:")
    print(f"  Current P/E: {signals.valuation_signal.current_pe:.2f}x")
    print(f"  Peer Avg P/E: {signals.valuation_signal.peer_average_pe:.2f}x")
    print(f"  Premium: {signals.valuation_signal.premium_percent:+.2f}%")
    print(f"  Trade Direction: {signals.valuation_signal.trade_direction.value.upper()}")
    print(f"  Confidence: {signals.valuation_signal.confidence.upper()}")
    
    print(f"\n📊 Momentum:")
    print(f"  Revenue Growth QoQ: {signals.momentum_signal.revenue_growth_qoq:.2f}%")
    print(f"  Peer Average: {signals.momentum_signal.peer_average_growth:.2f}%")
    print(f"  Trend: {signals.momentum_signal.trend.upper()}")
    print(f"  Risk: {signals.momentum_signal.risk_level.upper()}")
    
    print(f"\n💎 Hidden Strengths: {len(signals.hidden_strengths)}")
    for i, strength in enumerate(signals.hidden_strengths[:3], 1):
        print(f"  {i}. {strength.metric_name.upper()}: {strength.valuation_impact}")
    
    print(f"\n📝 Trading Scenarios: {len(signals.trading_scenarios)}")
    for scenario in signals.trading_scenarios:
        print(f"  - {scenario.scenario_type.value.upper()}: {scenario.timeframe}")
        print(f"    Trigger: {scenario.trigger}")
        print(f"    Target: {scenario.target_price_range or 'See narrative'}")
    
    print(f"\n📄 Executive Summary:")
    print(f"  {signals.summary}")
    
    # Step 4: Show narrative preview
    print("\n" + "=" * 80)
    print("📖 NARRATIVE PREVIEW (First 1000 characters)")
    print("=" * 80)
    print(narrative[:1000] + "...\n")
    
    # Step 5: List output files
    print("=" * 80)
    print("📁 OUTPUT FILES")
    print("=" * 80)
    print(f"\n✓ Generated files:")
    print(f"  1. {symbol.lower()}_competitive_intelligence.json - Full CI report data")
    print(f"  2. {symbol.lower()}_trading_signals.json - Structured trading signals")
    print(f"  3. {symbol.lower()}_trading_prompt.txt - LLM prompt (for debugging)")
    print(f"  4. {symbol.lower()}_swing_trading_report.md - **COMPLETE NARRATIVE ANALYSIS**")
    
    print(f"\n💡 Next steps:")
    print(f"  - Read {symbol.lower()}_swing_trading_report.md for full analysis")
    print(f"  - Use {symbol.lower()}_trading_signals.json for programmatic trading")
    print(f"  - Review competitive_intelligence.json for underlying data")
    
    print("\n" + "=" * 80)
    print("✅ COMPLETE!")
    print("=" * 80)
    
    return 0


def main():
    """Synchronous wrapper for async main."""
    return asyncio.run(main_async())


if __name__ == '__main__':
    sys.exit(main())
