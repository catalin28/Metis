"""
Test FMP peers endpoints directly to see what they return.
"""

import requests
import json
import os


def test_fmp_peers_endpoints():
    """Test FMP peers endpoints for M symbol."""
    
    api_key = os.environ.get('FMP_API_KEY', 'QIGYIgEO5xPtzUFyESt9vnydVBn4gbIy')
    base_url = "https://financialmodelingprep.com"
    symbol = 'M'
    
    print("🔍 Testing FMP Peers Endpoints for M (Macy's)")
    print("=" * 60)
    
    # Test 1: v4 stock peers endpoint
    print("1. Testing v4 stock_peers endpoint:")
    url = f"{base_url}/api/v4/stock_peers"
    params = {'symbol': symbol, 'apikey': api_key}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response Type: {type(data)}")
            print(f"   Response Content:")
            print(json.dumps(data, indent=2))
        else:
            print(f"   Error Response: {response.text}")
    except Exception as e:
        print(f"   Exception: {str(e)}")
    
    # Test 2: v3 stock-peers endpoint (with dash)
    print(f"\n2. Testing v3 stock-peers endpoint:")
    url = f"{base_url}/api/v3/stock-peers"
    params = {'symbol': symbol, 'apikey': api_key}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response Type: {type(data)}")
            print(f"   Response Content:")
            print(json.dumps(data, indent=2))
        else:
            print(f"   Error Response: {response.text}")
    except Exception as e:
        print(f"   Exception: {str(e)}")
    
    # Test 3: Alternative peers endpoint (if exists)
    print(f"\n3. Testing alternative peers endpoint:")
    url = f"{base_url}/api/v3/peers"
    params = {'symbol': symbol, 'apikey': api_key}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response Type: {type(data)}")
            print(f"   Response Content:")
            print(json.dumps(data, indent=2))
        else:
            print(f"   Error Response: {response.text}")
    except Exception as e:
        print(f"   Exception: {str(e)}")
    
    # Test 4: Try with a more common stock symbol to see if peers work
    print(f"\n4. Testing with AAPL to compare:")
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    for test_symbol in test_symbols:
        print(f"\n   Testing {test_symbol}:")
        url = f"{base_url}/api/v4/stock_peers"
        params = {'symbol': test_symbol, 'apikey': api_key}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                print(f"     ✅ Success: {type(data)} with {len(data) if isinstance(data, list) else 'unknown'} items")
                if isinstance(data, list) and len(data) > 0:
                    print(f"     First few peers: {data[:3]}")
                elif isinstance(data, dict):
                    print(f"     Data keys: {list(data.keys())}")
                else:
                    print(f"     Data: {data}")
            else:
                print(f"     ❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"     ❌ Exception: {str(e)}")


if __name__ == "__main__":
    test_fmp_peers_endpoints()