"""
Test FMP API endpoints directly to understand data availability.
"""

import asyncio
import os
import sys
import requests
sys.path.insert(0, 'src')


async def test_fmp_endpoints():
    """Test different FMP endpoints to understand data availability."""
    
    api_key = os.environ.get('FMP_API_KEY')
    base_url = "https://financialmodelingprep.com"
    symbol = 'M'
    
    print("🔍 Testing FMP API Endpoints for M (Macy's)")
    print("=" * 60)
    
    # Test 1: Company Profile
    print("1. Company Profile Endpoint:")
    url = f"{base_url}/api/v3/profile/{symbol}"
    response = requests.get(url, params={'apikey': api_key})
    if response.status_code == 200:
        data = response.json()
        if data:
            profile = data[0]
            print(f"   ✅ Success: {profile.get('companyName')}")
            print(f"   Market Cap: ${profile.get('mktCap', 0):,.0f}")
            print(f"   Revenue: ${profile.get('revenue', 0):,.0f}")
            print(f"   Price: ${profile.get('price', 0):.2f}")
            print(f"   Sector: {profile.get('sector')}")
            print(f"   Industry: {profile.get('industry')}")
        else:
            print("   ❌ No data returned")
    else:
        print(f"   ❌ Failed: {response.status_code}")
    
    # Test 2: Key Metrics (TTM)
    print(f"\n2. Key Metrics TTM Endpoint:")
    url = f"{base_url}/api/v3/key-metrics-ttm/{symbol}"
    response = requests.get(url, params={'apikey': api_key})
    if response.status_code == 200:
        data = response.json()
        if data:
            metrics = data[0] if isinstance(data, list) else data
            print(f"   ✅ Success")
            print(f"   Market Cap TTM: ${metrics.get('marketCapTTM', 0):,.0f}")
            print(f"   Revenue TTM: ${metrics.get('revenueTTM', 0):,.0f}")
            print(f"   PE Ratio TTM: {metrics.get('peRatioTTM', 'N/A')}")
        else:
            print("   ❌ No data returned")
    else:
        print(f"   ❌ Failed: {response.status_code}")
    
    # Test 3: Quote (Real-time data)
    print(f"\n3. Quote Endpoint:")
    url = f"{base_url}/api/v3/quote/{symbol}"
    response = requests.get(url, params={'apikey': api_key})
    if response.status_code == 200:
        data = response.json()
        if data:
            quote = data[0]
            print(f"   ✅ Success")
            print(f"   Market Cap: ${quote.get('marketCap', 0):,.0f}")
            print(f"   Price: ${quote.get('price', 0):.2f}")
            print(f"   PE: {quote.get('pe', 'N/A')}")
        else:
            print("   ❌ No data returned")
    else:
        print(f"   ❌ Failed: {response.status_code}")
    
    # Test 4: Income Statement (Annual)
    print(f"\n4. Income Statement (Annual) Endpoint:")
    url = f"{base_url}/api/v3/income-statement/{symbol}"
    response = requests.get(url, params={'apikey': api_key, 'limit': 1})
    if response.status_code == 200:
        data = response.json()
        if data:
            income = data[0]
            print(f"   ✅ Success")
            print(f"   Revenue: ${income.get('revenue', 0):,.0f}")
            print(f"   Date: {income.get('date', 'N/A')}")
        else:
            print("   ❌ No data returned")
    else:
        print(f"   ❌ Failed: {response.status_code}")
    
    # Test 5: Company Screener for similar companies
    print(f"\n5. Company Screener Endpoint (Consumer Cyclical):")
    url = f"{base_url}/stable/company-screener"
    params = {
        'apikey': api_key,
        'sector': 'Consumer Cyclical',
        'marketCapMoreThan': 1000000000,  # 1B+
        'marketCapLowerThan': 10000000000,  # 10B
        'isActivelyTrading': 'true',
        'country': 'US',
        'limit': 5
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data:
            print(f"   ✅ Success: Found {len(data)} companies")
            for i, company in enumerate(data[:3], 1):
                print(f"   {i}. {company.get('companyName')} ({company.get('symbol')})")
                print(f"      Market Cap: ${company.get('marketCap', 0):,.0f}")
                print(f"      Industry: {company.get('industry', 'N/A')}")
        else:
            print("   ❌ No data returned")
    else:
        print(f"   ❌ Failed: {response.status_code}")


if __name__ == "__main__":
    asyncio.run(test_fmp_endpoints())