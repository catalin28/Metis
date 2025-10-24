"""
Check what fields are actually returned by FMP API endpoints.
"""

import asyncio
import os
import sys
import requests
import json
sys.path.insert(0, 'src')


def check_api_endpoints():
    """Check what fields are returned by different FMP endpoints."""
    
    api_key = os.environ.get('FMP_API_KEY')
    base_url = "https://financialmodelingprep.com"
    
    print("🔍 Checking FMP API Endpoint Fields")
    print("=" * 60)
    
    # Test 1: Profile endpoint for M
    print("1. Profile endpoint for M (/api/v3/profile/M):")
    url = f"{base_url}/api/v3/profile/M"
    response = requests.get(url, params={'apikey': api_key})
    if response.status_code == 200:
        data = response.json()
        if data:
            profile = data[0]
            print("   ✅ Success - All fields returned:")
            for key, value in profile.items():
                print(f"     {key}: {value}")
        else:
            print("   ❌ No data returned")
    else:
        print(f"   ❌ Failed: {response.status_code}")
    
    # Test 2: Screener endpoint 
    print(f"\n2. Screener endpoint (/stable/company-screener):")
    url = f"{base_url}/stable/company-screener"
    params = {
        'apikey': api_key,
        'sector': 'Consumer Cyclical',
        'marketCapMoreThan': 1000000000,
        'limit': 1
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data:
            candidate = data[0]
            print(f"   ✅ Success - Company: {candidate.get('companyName', 'Unknown')}")
            print("   All fields returned:")
            for key, value in candidate.items():
                print(f"     {key}: {value}")
        else:
            print("   ❌ No data returned")
    else:
        print(f"   ❌ Failed: {response.status_code}")
    
    # Test 3: Quote endpoint for comparison
    print(f"\n3. Quote endpoint for M (/api/v3/quote/M):")
    url = f"{base_url}/api/v3/quote/M"
    response = requests.get(url, params={'apikey': api_key})
    if response.status_code == 200:
        data = response.json()
        if data:
            quote = data[0]
            print("   ✅ Success - Market cap related fields:")
            for key, value in quote.items():
                if 'cap' in key.lower() or 'market' in key.lower() or key in ['symbol', 'name', 'price']:
                    print(f"     {key}: {value}")
        else:
            print("   ❌ No data returned")
    else:
        print(f"   ❌ Failed: {response.status_code}")


if __name__ == "__main__":
    check_api_endpoints()