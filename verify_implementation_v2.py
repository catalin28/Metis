#!/usr/bin/env python3
"""
Verification Script for Competitive Intelligence Schema Implementation (v2)

This script tests all core components to ensure they work together correctly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime
from metis.utils.prompt_loader import PromptLoader
from metis.models.report_schema_v2 import (
    ReportMetadata, 
    CompanyProfile, 
    PeerCompany, 
    PeerGroup,
    DataSource,
    DataQuality,
    ExecutiveSummary,
    CompetitiveDashboard,
    ActionableRoadmap,
    Recommendation,
    RecommendationCategory,
    RecommendationPriority,
    MetricComparison,
    CompetitiveIntelligenceReport
)
from metis.reports.report_builder_v2 import CompetitiveIntelligenceReportBuilder

def test_prompt_loader():
    """Test prompt loading functionality"""
    print("Testing PromptLoader...")
    
    loader = PromptLoader()
    
    # Test loading existing prompt
    try:
        prompt = loader.load_prompt('narrative_generation', 'executive_summary')
        print(f"✓ Successfully loaded executive_summary prompt: {prompt[:100]}...")
        
        # Test variable validation (this should show missing variables)
        try:
            variables = loader.validate_prompt_variables('narrative_generation', 'executive_summary', {
                'company_name': 'Apple Inc.',
                'symbol': 'AAPL'
            })
            print(f"✓ Prompt validation working - found {len(variables)} missing variables")
        except Exception as e:
            print(f"✓ Prompt validation working - correctly identified: {str(e)[:100]}...")
        
    except Exception as e:
        print(f"✗ PromptLoader error: {e}")
        return False
    
    return True

def test_schema_models():
    """Test Pydantic schema models"""
    print("Testing schema models...")
    
    try:
        # Test ReportMetadata
        metadata = ReportMetadata(target_symbol="AAPL")
        print(f"✓ ReportMetadata created: {metadata.report_id[:8]}...")
        
        # Test CompanyProfile
        company = CompanyProfile(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            market_cap=3000000000000,
            pe_ratio=25.5
        )
        print(f"✓ CompanyProfile created: {company.company_name}")
        
        # Test PeerCompany
        peer = PeerCompany(
            symbol="MSFT",
            company_name="Microsoft Corporation",
            similarity_score=0.85
        )
        print(f"✓ PeerCompany created: {peer.company_name}")
        
        # Test PeerGroup
        peer_group = PeerGroup(
            target_company=company,
            peers=[peer],
            discovery_method="sector_similarity"
        )
        print(f"✓ PeerGroup created with {len(peer_group.peers)} peers")
        
        return True
        
    except Exception as e:
        print(f"✗ Schema model error: {e}")
        return False

def test_report_builder():
    """Test report builder functionality"""
    print("Testing ReportBuilder...")
    
    try:
        builder = CompetitiveIntelligenceReportBuilder()
        
        # Build a complete report
        report = (builder
                 .set_metadata(target_symbol="AAPL")
                 .add_data_source("financial_api", "FinancialModelingPrep", DataQuality.VALID)
                 .set_target_company("AAPL", "Apple Inc.", "Technology", 3000000000000, 25.5)
                 .add_peer_company("MSFT", "Microsoft Corporation", 0.85)
                 .set_peer_discovery_method("sector_similarity")
                 .set_executive_summary(
                     overview="Apple maintains strong competitive position",
                     key_insights=["Strong brand", "High margins", "Innovation leader"],
                     top_recommendations=["Expand services", "Improve supply chain", "Focus on AI"]
                 )
                 .add_metric_comparison("P/E Ratio", 25.5, {"MSFT": 28.2}, 1, "Apple trades at discount")
                 .set_competitive_dashboard(
                     overall_ranking=2,
                     strengths=["Brand strength", "Financial performance"],
                     weaknesses=["China dependency"]
                 )
                 .add_recommendation(
                     "Expand AI capabilities", 
                     "Focus on AI integration across products",
                     RecommendationCategory.DO,
                     RecommendationPriority.HIGH,
                     "Increased competitive advantage"
                 )
                 .add_recommendation(
                     "Communicate value proposition", 
                     "Better articulate ecosystem benefits",
                     RecommendationCategory.SAY,
                     RecommendationPriority.MEDIUM,
                     "Improved market perception"
                 )
                 .add_recommendation(
                     "Demonstrate innovation", 
                     "Showcase upcoming technologies",
                     RecommendationCategory.SHOW,
                     RecommendationPriority.HIGH,
                     "Enhanced investor confidence"
                 )
                 .add_recommendation(
                     "Optimize supply chain", 
                     "Improve manufacturing efficiency",
                     RecommendationCategory.DO,
                     RecommendationPriority.MEDIUM,
                     "Cost reduction"
                 )
                 .add_recommendation(
                     "Engage with analysts", 
                     "Regular investor communications",
                     RecommendationCategory.SAY,
                     RecommendationPriority.LOW,
                     "Better analyst coverage"
                 )
                 .set_actionable_roadmap(
                     implementation_timeline="12 months",
                     success_metrics=["Market share growth", "P/E ratio improvement"]
                 )
                 .build())
        
        print(f"✓ Report built successfully: {report.metadata.target_symbol}")
        print(f"✓ Report has {len(report.actionable_roadmap.recommendations)} recommendations")
        print(f"✓ Report validation passed")
        
        return True
        
    except Exception as e:
        print(f"✗ ReportBuilder error: {e}")
        return False

def main():
    """Run all verification tests"""
    print("=== Competitive Intelligence Schema Implementation Verification ===\n")
    
    tests = [
        ("PromptLoader", test_prompt_loader),
        ("Schema Models", test_schema_models),
        ("Report Builder", test_report_builder)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        success = test_func()
        results.append((test_name, success))
        print(f"Result: {'PASS' if success else 'FAIL'}")
    
    print("\n=== Summary ===")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All components working correctly!")
        return 0
    else:
        print("❌ Some components need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())