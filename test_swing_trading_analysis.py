#!/usr/bin/env python3
"""
Test Swing Trading Analysis Module

Tests the complete swing trading analysis pipeline:
1. Load competitive intelligence JSON
2. Extract trading signals
3. Generate LLM-powered narrative analysis
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from metis.swing_trading import SwingTraderAnalyzer


def main():
    """Test swing trading analysis with ASML report."""
    
    print("=" * 80)
    print("SWING TRADING ANALYSIS TEST")
    print("=" * 80)
    
    # Load ASML report
    report_path = "asml_with_qoq_labels.json"
    print(f"\n📊 Loading competitive intelligence report: {report_path}")
    
    if not Path(report_path).exists():
        print(f"❌ Error: Report file not found: {report_path}")
        print("\nAvailable JSON files:")
        for f in Path(".").glob("*.json"):
            print(f"  - {f}")
        return 1
    
    with open(report_path, 'r') as f:
        report_data = json.load(f)
    
    symbol = report_data.get('target_symbol', 'UNKNOWN')
    print(f"✓ Loaded report for {symbol}")
    
    # Initialize analyzer
    print("\n🔧 Initializing SwingTraderAnalyzer...")
    analyzer = SwingTraderAnalyzer()
    print("✓ Analyzer initialized")
    
    # Test 1: Extract structured signals
    print("\n" + "=" * 80)
    print("TEST 1: Extract Trading Signals")
    print("=" * 80)
    
    try:
        signals = analyzer.analyze_from_dict(report_data)
        
        print(f"\n✓ Signals extracted successfully!")
        print(f"\n📈 Trading Signal Summary:")
        print(f"  Symbol: {signals.target_symbol}")
        print(f"  Company: {signals.target_company_name}")
        print(f"  Overall Bias: {signals.overall_bias.value.upper()}")
        print(f"  Risk Level: {signals.risk_level.upper()}")
        print(f"  Conviction Score: {signals.conviction_score}/10")
        
        print(f"\n💰 Valuation Signal:")
        print(f"  Current P/E: {signals.valuation_signal.current_pe:.2f}x")
        print(f"  Peer Avg P/E: {signals.valuation_signal.peer_average_pe:.2f}x")
        print(f"  Premium: {signals.valuation_signal.premium_percent:+.2f}%")
        print(f"  Trade Direction: {signals.valuation_signal.trade_direction.value.upper()}")
        print(f"  Confidence: {signals.valuation_signal.confidence.upper()}")
        
        print(f"\n📊 Momentum Signal:")
        print(f"  Revenue Growth QoQ: {signals.momentum_signal.revenue_growth_qoq:.2f}%")
        print(f"  Peer Average: {signals.momentum_signal.peer_average_growth:.2f}%")
        print(f"  Rank: #{signals.momentum_signal.rank}")
        print(f"  Trend: {signals.momentum_signal.trend.upper()}")
        print(f"  Risk: {signals.momentum_signal.risk_level.upper()}")
        
        print(f"\n💎 Hidden Strengths: {len(signals.hidden_strengths)}")
        for i, strength in enumerate(signals.hidden_strengths[:3], 1):
            print(f"  {i}. {strength.metric_name.upper()}")
            print(f"     Valuation Impact: {strength.valuation_impact}")
        
        print(f"\n📝 Trading Scenarios: {len(signals.trading_scenarios)}")
        for scenario in signals.trading_scenarios:
            print(f"  - {scenario.scenario_type.value.upper()}: {scenario.timeframe}")
        
        print(f"\n📋 Summary:")
        print(f"  {signals.summary}")
        
        # Save signals to file
        output_path = f"{symbol.lower()}_trading_signals.json"
        with open(output_path, 'w') as f:
            json.dump(signals.model_dump(), f, indent=2)
        print(f"\n✓ Signals saved to: {output_path}")
        
    except Exception as e:
        print(f"\n❌ Error extracting signals: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Test 2: Generate LLM narrative (optional - costs money)
    print("\n" + "=" * 80)
    print("TEST 2: Generate LLM Trading Narrative")
    print("=" * 80)
    
    generate_narrative = input("\n⚠️  Generate LLM narrative? This will call OpenAI API (costs ~$0.02-0.05) [y/N]: ")
    
    if generate_narrative.lower() == 'y':
        try:
            print("\n🤖 Generating trading narrative with LLM...")
            print("   (This may take 10-30 seconds)")
            
            narrative = analyzer.generate_trading_narrative_sync(
                report_data,
                model="gpt-4",
                temperature=0.7
            )
            
            print("\n✓ Narrative generated successfully!")
            print(f"   Length: {len(narrative)} characters")
            
            # Save narrative to file
            output_path = f"{symbol.lower()}_trading_narrative.md"
            with open(output_path, 'w') as f:
                f.write(f"# Swing Trading Analysis: {signals.target_company_name} ({symbol})\n\n")
                f.write(narrative)
            
            print(f"✓ Narrative saved to: {output_path}")
            
            # Preview first 500 characters
            print("\n📄 Preview:")
            print("-" * 80)
            print(narrative[:500] + "...\n")
            print("-" * 80)
            
        except Exception as e:
            print(f"\n❌ Error generating narrative: {e}")
            import traceback
            traceback.print_exc()
            return 1
    else:
        print("\n⏭️  Skipping LLM narrative generation")
    
    # Test 3: Full analysis with all outputs
    print("\n" + "=" * 80)
    print("TEST 3: Full Analysis Pipeline")
    print("=" * 80)
    
    try:
        print("\n🔄 Running full analysis pipeline...")
        
        signals_full, prompt, narrative_full = analyzer.full_analysis(
            report_data,
            output_signals_path=f"{symbol.lower()}_full_signals.json",
            output_prompt_path=f"{symbol.lower()}_prompt.txt",
            generate_narrative=False  # Skip LLM for this test
        )
        
        print("\n✓ Full analysis complete!")
        print(f"  - Signals extracted: ✓")
        print(f"  - Prompt generated: ✓")
        print(f"  - Files saved: ✓")
        
    except Exception as e:
        print(f"\n❌ Error in full analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    
    print(f"\n📁 Output files created:")
    print(f"  1. {symbol.lower()}_trading_signals.json - Structured trading signals")
    print(f"  2. {symbol.lower()}_full_signals.json - Full analysis signals")
    print(f"  3. {symbol.lower()}_prompt.txt - LLM prompt template")
    if generate_narrative.lower() == 'y':
        print(f"  4. {symbol.lower()}_trading_narrative.md - LLM-generated analysis")
    
    print("\n💡 Next steps:")
    print("  - Review the structured signals JSON for programmatic trading integration")
    print("  - Read the narrative markdown for human-readable trading insights")
    print("  - Use the prompt.txt to test with other LLMs (Claude, etc.)")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
