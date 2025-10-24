"""
Detailed peer discovery debugging for M symbol.
"""

import asyncio
import os
import sys
sys.path.insert(0, 'src')

from src.metis.assistants.peer_discovery_service import PeerDiscoveryService


async def debug_peer_discovery():
    """Debug peer discovery for M symbol."""
    
    print("🔍 Debugging Peer Discovery for M (Macy's)")
    print("=" * 60)
    
    service = PeerDiscoveryService()
    
    # Get target profile
    target_profile = await service._get_company_profile('M')
    print(f"Target: {target_profile.get('companyName')} ({target_profile.get('symbol')})")
    print(f"Sector: {target_profile.get('sector')}")
    print(f"Industry: {target_profile.get('industry')}")
    print(f"Market Cap: ${target_profile.get('mktCap', 0):,.0f}")
    print(f"Revenue: ${target_profile.get('revenue', 0):,.0f}")
    print(f"Country: {target_profile.get('country')}")
    
    # Test screener discovery with detailed output
    print(f"\n🔍 Testing screener discovery...")
    screener_candidates = await service._discover_via_screener(
        target_profile, 
        target_profile.get('sector', ''), 
        10
    )
    
    print(f"Found {len(screener_candidates)} screener candidates:")
    
    scored_candidates = []
    for i, candidate in enumerate(screener_candidates[:5], 1):  # Test first 5
        if candidate.get('symbol') != 'M':  # Skip target
            try:
                similarity = await service._calculate_similarity_score(target_profile, candidate)
                scored_candidates.append({
                    'candidate': candidate,
                    'similarity': similarity
                })
                
                print(f"\n{i}. {candidate.get('companyName', 'Unknown')} ({candidate.get('symbol', 'Unknown')})")
                print(f"   Sector: {candidate.get('sector', 'Unknown')}")
                print(f"   Industry: {candidate.get('industry', 'Unknown')}")
                print(f"   Market Cap: ${candidate.get('mktCap', 0):,.0f}")
                print(f"   Country: {candidate.get('country', 'Unknown')}")
                print(f"   Similarity Score: {similarity.final_score:.3f}")
                print(f"   Components: Sector={similarity.sector_score:.3f}, MCap={similarity.market_cap_score:.3f}, "
                      f"Revenue={similarity.revenue_score:.3f}, Geo={similarity.geographic_score:.3f}")
                print(f"   Threshold check: {'✅ PASS' if similarity.final_score >= service.similarity_threshold else '❌ FAIL'} "
                      f"(threshold: {service.similarity_threshold})")
                
            except Exception as e:
                print(f"   ❌ Error calculating similarity: {e}")
    
    # Show threshold analysis
    print(f"\n📊 Threshold Analysis:")
    print(f"Current threshold: {service.similarity_threshold}")
    passing_candidates = [c for c in scored_candidates if c['similarity'].final_score >= service.similarity_threshold]
    print(f"Candidates passing threshold: {len(passing_candidates)}")
    
    if not passing_candidates:
        print("\n💡 Suggestions:")
        best_candidate = max(scored_candidates, key=lambda x: x['similarity'].final_score, default=None)
        if best_candidate:
            best_score = best_candidate['similarity'].final_score
            print(f"   • Best candidate score: {best_score:.3f}")
            print(f"   • Consider lowering threshold to: {best_score - 0.01:.2f}")
        
        # Test with lower threshold
        print(f"\n🧪 Testing with lower threshold (0.4)...")
        original_threshold = service.similarity_threshold
        service.similarity_threshold = 0.4
        
        peers = await service.identify_peers('M', max_peers=3)
        print(f"With threshold 0.4, found {len(peers)} peers:")
        for peer in peers:
            print(f"   • {peer.get('symbol')}: {peer.get('similarityScore'):.3f}")
        
        # Restore original threshold
        service.similarity_threshold = original_threshold


if __name__ == "__main__":
    asyncio.run(debug_peer_discovery())