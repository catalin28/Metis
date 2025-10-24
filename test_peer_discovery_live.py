"""
Live test of peer discovery service with M (Macy's) symbol.

This script tests the peer discovery service with real API calls
to see how it performs with actual data.
"""

import asyncio
import os
import sys
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.metis.assistants.peer_discovery_service import PeerDiscoveryService


async def test_peer_discovery_for_m():
    """Test peer discovery for M (Macy's) symbol."""
    
    # Check if we have FMP API key
    api_key = os.environ.get('FMP_API_KEY')
    if not api_key:
        print("❌ FMP_API_KEY environment variable not set")
        print("Set it with: export FMP_API_KEY=your_api_key")
        return
    
    print("🔍 Testing Peer Discovery for M (Macy's)")
    print("=" * 50)
    
    try:
        # Initialize service
        service = PeerDiscoveryService()
        print(f"✅ Service initialized with API key: {api_key[:10]}...")
        
        # Test 1: Get company profile for M
        print("\n📊 Step 1: Getting company profile for M...")
        target_profile = await service._get_company_profile('M')
        
        if target_profile:
            print(f"✅ Found company: {target_profile.get('companyName', 'Unknown')}")
            print(f"   Sector: {target_profile.get('sector', 'Unknown')}")
            print(f"   Industry: {target_profile.get('industry', 'Unknown')}")
            print(f"   Market Cap: ${target_profile.get('mktCap', 0):,.0f}")
            print(f"   Country: {target_profile.get('country', 'Unknown')}")
        else:
            print("❌ Could not retrieve company profile for M")
            return
        
        # Test 2: Discover peers
        print(f"\n🔍 Step 2: Discovering peers for M...")
        peers = await service.identify_peers('M', max_peers=5)
        
        if peers:
            print(f"✅ Found {len(peers)} peers:")
            print("\n📈 Peer Analysis:")
            print("-" * 80)
            print(f"{'Symbol':<8} {'Company':<30} {'Score':<6} {'Source':<12} {'Explanation'}")
            print("-" * 80)
            
            for peer in peers:
                company_name = peer.get('name', 'Unknown')[:28]
                score = peer.get('similarityScore', 0)
                source = peer.get('source', 'unknown')
                explanation = peer.get('explanation', 'No explanation')[:30]
                
                print(f"{peer.get('symbol', 'Unknown'):<8} {company_name:<30} {score:<6.3f} {source:<12} {explanation}")
            
            # Test 3: Show similarity component breakdown for first peer
            if peers and 'components' in peers[0]:
                print(f"\n🔬 Detailed Analysis for {peers[0]['symbol']}:")
                components = peers[0]['components']
                print(f"  • Sector Score: {components.get('sectorScore', 0):.3f}")
                print(f"  • Market Cap Score: {components.get('marketCapScore', 0):.3f}")
                print(f"  • Revenue Score: {components.get('revenueScore', 0):.3f}")
                print(f"  • Geographic Score: {components.get('geographicScore', 0):.3f}")
        else:
            print("❌ No peers found")
        
        # Test 4: Test different discovery methods individually
        print(f"\n🔧 Step 3: Testing individual discovery methods...")
        
        # Test screener method
        print("  Testing screener method...")
        screener_candidates = await service._discover_via_screener(
            target_profile, 
            target_profile.get('sector', ''), 
            10
        )
        print(f"    Screener found: {len(screener_candidates)} candidates")
        
        # Test FMP peers method
        print("  Testing FMP peers method...")
        fmp_candidates = await service._discover_via_fmp_peers('M', target_profile)
        print(f"    FMP peers found: {len(fmp_candidates)} candidates")
        
        print("\n✅ Peer discovery test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during peer discovery test: {str(e)}")
        import traceback
        traceback.print_exc()


def test_similarity_scoring():
    """Test similarity scoring components."""
    print("\n🧪 Testing Similarity Scoring Components")
    print("=" * 50)
    
    try:
        service = PeerDiscoveryService()
        
        # Test market cap scoring
        print("\n📊 Market Cap Similarity Tests:")
        test_cases = [
            (1000000000, 1000000000, "Equal market caps"),
            (1000000000, 2000000000, "2x difference"),
            (1000000000, 500000000, "0.5x difference"),
            (1000000000, 10000000000, "10x difference"),
        ]
        
        for target_mcap, candidate_mcap, description in test_cases:
            score = service._calculate_market_cap_score(target_mcap, candidate_mcap)
            print(f"  {description}: {score:.3f}")
        
        # Test sector scoring
        print("\n🏢 Sector Similarity Tests:")
        sector_tests = [
            ('Technology', 'Software', 'Technology', 'Software', "Exact match"),
            ('Technology', 'Software', 'Technology', 'Hardware', "Same sector, diff industry"),
            ('Technology', 'Software', 'Retail', 'Software', "Same industry, diff sector"),
            ('Technology', 'Software', 'Healthcare', 'Pharmaceuticals', "No match"),
        ]
        
        for t_sector, t_industry, c_sector, c_industry, description in sector_tests:
            score = service._calculate_sector_score(t_sector, t_industry, c_sector, c_industry)
            print(f"  {description}: {score:.3f}")
        
        # Test geographic scoring
        print("\n🌍 Geographic Similarity Tests:")
        geo_tests = [
            ('US', 'US', "Same country"),
            ('US', 'USA', "US variations"),
            ('US', 'Canada', "Same region"),
            ('US', 'Germany', "Different regions"),
            ('Unknown', 'US', "Unknown country"),
        ]
        
        for target_country, candidate_country, description in geo_tests:
            score = service._calculate_geographic_score(target_country, candidate_country)
            print(f"  {description}: {score:.3f}")
            
        print("\n✅ Similarity scoring tests completed!")
        
    except Exception as e:
        print(f"❌ Error during similarity scoring test: {str(e)}")


async def main():
    """Run all tests."""
    print("🚀 Live Peer Discovery Testing")
    print("=" * 50)
    
    # Test similarity scoring (synchronous)
    test_similarity_scoring()
    
    # Test live peer discovery (asynchronous)
    await test_peer_discovery_for_m()


if __name__ == "__main__":
    asyncio.run(main())