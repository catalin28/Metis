#!/usr/bin/env python3

import asyncio
import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from metis.assistants.peer_discovery_service import PeerDiscoveryService

async def debug_ktb_classification():
    """Debug why KTB is classified as sector peer instead of financial."""
    
    print("🔍 Debugging KTB Classification")
    print("=" * 50)
    
    service = PeerDiscoveryService()
    
    try:
        # Get Macy's profile
        print("📊 Getting company profiles...")
        
        m_url = f"{service.base_url}/api/v3/profile/M"
        ktb_url = f"{service.base_url}/api/v3/profile/KTB"
        
        import requests
        
        # Get Macy's data
        m_response = requests.get(m_url, params={'apikey': service.fmp_api_key})
        m_data = m_response.json()[0]
        
        # Get KTB data  
        ktb_response = requests.get(ktb_url, params={'apikey': service.fmp_api_key})
        ktb_data = ktb_response.json()[0]
        
        print(f"\n🏪 Macy's (M):")
        print(f"   Sector: '{m_data.get('sector', 'N/A')}'")
        print(f"   Industry: '{m_data.get('industry', 'N/A')}'")
        
        print(f"\n👔 Kontoor Brands (KTB):")
        print(f"   Sector: '{ktb_data.get('sector', 'N/A')}'")
        print(f"   Industry: '{ktb_data.get('industry', 'N/A')}'")
        
        # Test the classification logic
        print(f"\n🧬 Testing Classification Logic:")
        peer_type = service._classify_peer_type(m_data, ktb_data)
        print(f"   Classified as: '{peer_type}'")
        
        # Show the logic step by step
        target_sector = m_data.get('sector', '').lower().strip()
        candidate_sector = ktb_data.get('sector', '').lower().strip()
        target_industry = m_data.get('industry', '').lower().strip()
        candidate_industry = ktb_data.get('industry', '').lower().strip()
        
        print(f"\n🔬 Step-by-step Logic:")
        print(f"   Target sector (lowercase): '{target_sector}'")
        print(f"   Candidate sector (lowercase): '{candidate_sector}'")
        print(f"   Sectors match? {target_sector == candidate_sector}")
        
        print(f"   Target industry (lowercase): '{target_industry}'")
        print(f"   Candidate industry (lowercase): '{candidate_industry}'")
        print(f"   Industries match? {target_industry == candidate_industry}")
        
        # Check the classification conditions
        if target_industry and candidate_industry and target_industry == candidate_industry:
            expected = 'industry'
        elif target_sector and candidate_sector and target_sector == candidate_sector:
            expected = 'sector'
        else:
            expected = 'financial'
        
        print(f"\n🎯 Expected classification: '{expected}'")
        print(f"   Actual classification: '{peer_type}'")
        print(f"   Match? {'✅' if expected == peer_type else '❌'}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_ktb_classification())