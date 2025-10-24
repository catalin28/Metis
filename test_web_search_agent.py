"""
Test script for the web search company research agent
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from metis.assistants.generic_llm_agent import GenericLLMAgent


def test_web_search_company_research():
    """Test the web search company research functionality"""
    
    print("=" * 80)
    print("Testing Web Search Company Research Agent")
    print("=" * 80)
    
    # Initialize the agent
    agent = GenericLLMAgent()
    
    # Test with W.R. Berkley (WRB) - insurance company
    test_cases = [
        {
            "symbol": "WRB",
            "company_name": "W.R. Berkley Corporation",
            "industry": "Property & Casualty Insurance",
            "sector": "Financials",
            "description": "Insurance company (established, should have good data)"
        },
        {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "industry": "Consumer Electronics",
            "sector": "Technology",
            "description": "Tech giant (very well known)"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"Test Case {i}: {test_case['symbol']} - {test_case['description']}")
        print(f"{'=' * 80}")
        
        try:
            result = agent.research_company_with_web_search(
                symbol=test_case["symbol"],
                company_name=test_case["company_name"],
                industry=test_case["industry"],
                sector=test_case["sector"]
            )
            
            print("\n✅ Research completed successfully!")
            print(f"\n📄 Company Overview ({len(result['company_overview'])} characters):")
            print("-" * 80)
            print(result["company_overview"])
            print("-" * 80)
            
            print(f"\n🔗 Sources consulted: {result['search_metadata']['sources_count']}")
            if result['sources']:
                for idx, source in enumerate(result['sources'][:5], 1):  # Show first 5
                    print(f"   {idx}. {source}")
                if len(result['sources']) > 5:
                    print(f"   ... and {len(result['sources']) - 5} more")
            
            print(f"\n📌 Citations in text: {result['search_metadata']['citations_count']}")
            if result['citations']:
                for idx, citation in enumerate(result['citations'][:3], 1):  # Show first 3
                    print(f"   {idx}. {citation['title']}")
                    print(f"      URL: {citation['url']}")
                    print(f"      Text: \"{citation['text_excerpt'][:100]}...\"")
                if len(result['citations']) > 3:
                    print(f"   ... and {len(result['citations']) - 3} more citations")
            
            # Validate output length
            overview_length = len(result['company_overview'])
            if 200 <= overview_length <= 2000:
                print(f"\n✅ Overview length is valid: {overview_length} chars (200-2000 range)")
            else:
                print(f"\n⚠️  Warning: Overview length {overview_length} is outside expected range (200-2000)")
            
        except Exception as e:
            print(f"\n❌ Research failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
        if i < len(test_cases):
            print("\n" + "=" * 80)
            input("Press Enter to continue to next test case...")
    
    print("\n" + "=" * 80)
    print("🎉 All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    test_web_search_company_research()
