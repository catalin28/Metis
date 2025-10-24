"""
Debug the screener endpoint data directly.
"""

import asyncio
import os
import sys
import requests
sys.path.insert(0, 'src')

from src.metis.assistants.peer_discovery_service import PeerDiscoveryService


async def debug_screener_data():
    """Debug what data is actually returned by screener."""
    
    api_key = os.environ.get('FMP_API_KEY')
    base_url = "https://financialmodelingprep.com"
    
    print("🔍 Debugging Screener Data for M (Macy's)")
    print("=" * 60)
    
    # Get target profile first
    service = PeerDiscoveryService()
    target_profile = await service._get_company_profile('M')
    
    print(f"Target Market Cap: ${target_profile.get('mktCap', 0):,.0f}")
    
    # Test screener endpoint directly
    target_market_cap = target_profile.get('mktCap', 0)
    market_cap_min = int(target_market_cap * 0.1)
    market_cap_max = int(target_market_cap * 10)
    
    print(f"Screener parameters:")
    print(f"  Sector: {target_profile.get('sector')}")
    print(f"  Market cap range: ${market_cap_min:,.0f} - ${market_cap_max:,.0f}")
    
    url = f"{base_url}/stable/company-screener"
    params = {
        'apikey': api_key,
        'sector': target_profile.get('sector'),
        'marketCapMoreThan': market_cap_min,
        'marketCapLowerThan': market_cap_max,
        'isActivelyTrading': 'true',
        'country': 'US',
        'limit': 5
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        candidates = response.json()
        print(f"\nScreener returned {len(candidates)} candidates:")
        
        for i, candidate in enumerate(candidates, 1):
            print(f"\n{i}. {candidate.get('companyName')} ({candidate.get('symbol')})")
            print(f"   Raw marketCap: {candidate.get('marketCap')}")
            print(f"   Raw mktCap: {candidate.get('mktCap', 'NOT_FOUND')}")
            
            # Test normalization
            normalized = service._normalize_company_data(candidate, 'screener')
            print(f"   After normalization - mktCap: {normalized.get('mktCap')}")
            
            # Test similarity calculation
            if candidate.get('symbol') != 'M':
                similarity = await service._calculate_similarity_score(target_profile, normalized)
                print(f"   Similarity score: {similarity.final_score:.3f}")
                print(f"   Market cap score: {similarity.market_cap_score:.3f}")
    else:
        print(f"❌ Screener request failed: {response.status_code}")
        print(f"Response: {response.text}")


if __name__ == "__main__":
    asyncio.run(debug_screener_data())