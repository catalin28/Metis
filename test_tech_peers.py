#!/usr/bin/env python3

import asyncio
import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from metis.assistants.peer_discovery_service import PeerDiscoveryService

async def test_tech_company_peers():
    """Test peer discovery with a mid-cap technology company."""
    
    print("🚀 Testing Peer Discovery - Technology Sector")
    print("=" * 60)
    
    service = PeerDiscoveryService()
    symbol = "SNOW"  # Snowflake - Cloud data platform
    
    print(f"🔍 Testing Peer Discovery for {symbol} (Snowflake)")
    print("=" * 60)
    
    try:
        # Get company profile first
        profile_url = f"{service.base_url}/api/v3/profile/{symbol}"
        import requests
        response = requests.get(profile_url, params={'apikey': service.fmp_api_key})
        profile_data = response.json()
        
        if profile_data:
            company = profile_data[0]
            print(f"📊 Target Company:")
            print(f"   Name: {company.get('companyName', 'N/A')}")
            print(f"   Sector: {company.get('sector', 'N/A')}")
            print(f"   Industry: {company.get('industry', 'N/A')}")
            print(f"   Market Cap: ${company.get('mktCap', 0):,}")
            print(f"   Country: {company.get('country', 'N/A')}")
        
        print(f"\n🔍 Discovering peers...")
        
        # Discover peers
        peers = await service.identify_peers(symbol, max_peers=8)
        
        if peers:
            print(f"✅ Found {len(peers)} peers:")
            print("\n📈 Detailed Peer Analysis:")
            print("-" * 150)
            print(f"{'Rank':<4} {'Symbol':<8} {'Company':<30} {'Sector':<15} {'Industry':<25} {'Type':<10} {'Score':<6} {'Weighted':<8} {'Source'}")
            print("-" * 150)
            
            for i, peer in enumerate(peers, 1):
                # Get sector and industry for each peer
                try:
                    peer_profile_url = f"{service.base_url}/api/v3/profile/{peer['symbol']}"
                    peer_response = requests.get(peer_profile_url, params={'apikey': service.fmp_api_key})
                    peer_profile = peer_response.json()
                    industry = peer_profile[0].get('industry', 'N/A')[:23] + ".." if len(peer_profile[0].get('industry', 'N/A')) > 25 else peer_profile[0].get('industry', 'N/A')
                    sector = peer_profile[0].get('sector', 'N/A')[:13] + ".." if len(peer_profile[0].get('sector', 'N/A')) > 15 else peer_profile[0].get('sector', 'N/A')
                except:
                    industry = "N/A"
                    sector = "N/A"
                
                name = peer['name'][:28] + ".." if len(peer['name']) > 30 else peer['name']
                peer_type = peer.get('peerType', 'unknown')
                score = peer['similarityScore']
                weighted = peer.get('weightedScore', score)
                source = peer['source']
                
                print(f"{i:<4} {peer['symbol']:<8} {name:<30} {sector:<15} {industry:<25} {peer_type:<10} {score:<6} {weighted:<8} {source}")
            
            # Group analysis
            industry_count = sum(1 for p in peers if p.get('peerType') == 'industry')
            sector_count = sum(1 for p in peers if p.get('peerType') == 'sector')
            financial_count = sum(1 for p in peers if p.get('peerType') == 'financial')
            
            print(f"\n📊 Peer Type Distribution:")
            print(f"   🏪 Industry Peers (Same Business): {industry_count}")
            print(f"   🏢 Sector Peers (Related Business): {sector_count}")
            print(f"   💰 Financial Peers (Different Business): {financial_count}")
            
            print(f"\n💡 Financial Analysis Guidance:")
            if industry_count > 0:
                print(f"   ✅ Compare ALL financial metrics with Industry peers")
            if sector_count > 0:
                print(f"   ⚠️  Compare basic ratios CAREFULLY with Sector peers")
            if financial_count > 0:
                print(f"   📊 Use Financial peers ONLY for valuation multiples")
            
            # Show market cap range used
            target_mcap = company.get('mktCap', 0)
            mcap_min = target_mcap * 0.1
            mcap_max = target_mcap * 10
            print(f"\n🔍 Filter Details:")
            print(f"   Market Cap Range: ${mcap_min:,.0f} - ${mcap_max:,.0f}")
            print(f"   Target Industry: {company.get('industry', 'N/A')}")
            print(f"   Target Sector: {company.get('sector', 'N/A')}")
        
        else:
            print("❌ No peers found")
            # Let's debug why
            print(f"\n🔧 Debug - Let's check the filters:")
            target_mcap = company.get('mktCap', 0)
            print(f"   Market Cap: ${target_mcap:,}")
            print(f"   Market Cap Range: ${target_mcap * 0.1:,.0f} - ${target_mcap * 10:,.0f}")
            print(f"   Sector: {company.get('sector', 'N/A')}")
            print(f"   Industry: {company.get('industry', 'N/A')}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Technology sector peer discovery test completed!")

if __name__ == "__main__":
    asyncio.run(test_tech_company_peers())