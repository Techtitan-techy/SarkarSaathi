"""
Final attempt to scrape myScheme using discovered API with proper authentication
Based on network traffic analysis, we know the API endpoint exists
"""
import requests
import json
from datetime import datetime
import os

# The real API endpoint we discovered
API_BASE = "https://api.myscheme.gov.in/search/v6"

def get_schemes_simple():
    """Try the simplest possible API call"""
    
    print("=" * 70)
    print("ATTEMPTING SIMPLE API CALL")
    print("=" * 70)
    print()
    
    # Try without any authentication first
    url = f"{API_BASE}/schemes"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.myscheme.gov.in/',
        'Origin': 'https://www.myscheme.gov.in'
    }
    
    try:
        print(f"GET {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Content length: {len(response.content)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n✓ SUCCESS!")
                print(f"Response keys: {list(data.keys())}")
                return data
            except:
                print(f"\nResponse text: {response.text[:500]}")
                return None
        else:
            print(f"\nResponse text: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"× Error: {str(e)}")
        return None


def try_facets_endpoint():
    """Try the facets endpoint we discovered"""
    
    print("\n" + "=" * 70)
    print("TRYING FACETS ENDPOINT")
    print("=" * 70)
    print()
    
    url = f"{API_BASE}/schemes/facets"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.myscheme.gov.in/',
        'Origin': 'https://www.myscheme.gov.in'
    }
    
    # Try with minimal params
    params = {'lang': 'en'}
    
    try:
        print(f"GET {url}")
        print(f"Params: {params}")
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.content)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n✓ SUCCESS!")
                print(f"Response: {json.dumps(data, indent=2)[:500]}")
                return data
            except:
                print(f"\nResponse text: {response.text}")
                return None
        else:
            print(f"\nResponse text: {response.text}")
            return None
            
    except Exception as e:
        print(f"× Error: {str(e)}")
        return None


def main():
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "FINAL myScheme API ATTEMPT" + " " * 27 + "║")
    print("║" + " " * 10 + "Testing Discovered API Endpoints" + " " * 26 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # Try simple call
    data1 = get_schemes_simple()
    
    # Try facets
    data2 = try_facets_endpoint()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    
    if data1 or data2:
        print("✓ At least one endpoint worked!")
        
        # Save whatever we got
        output = {
            'simple_endpoint': data1,
            'facets_endpoint': data2,
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open('api_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print("✓ Saved results to: api_test_results.json")
    else:
        print("× No endpoints worked")
        print("\nConclusion:")
        print("  The myScheme API requires authentication that we cannot")
        print("  obtain without official API keys or credentials.")
        print("\nRecommendation:")
        print("  1. Use the existing 8 curated schemes in schemes_database.json")
        print("  2. Manually add more schemes from official sources")
        print("  3. Apply for official API access from API Setu")
        print("  4. Continue with the project using existing data")


if __name__ == '__main__':
    main()
