"""
Scrape schemes using PUBLIC API Setu endpoints
These are official government APIs that don't require authentication!
"""
import requests
import json
from datetime import datetime
import os
import urllib3

# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# PUBLIC API endpoints from API Setu
API_SETU_BASE = "https://apisetu.gov.in/dic/myscheme"

ENDPOINTS = {
    'ministry_count_v3': '/srv/v3/public/schemes/ministries/count',
    'ministry_count_v4': '/srv/v4/public/schemes/ministries/count',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
}


def test_endpoint(name, path):
    """Test a single endpoint"""
    url = f"{API_SETU_BASE}{path}"
    
    print(f"\n{'=' * 70}")
    print(f"TESTING: {name}")
    print(f"{'=' * 70}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        
        print(f"Status: {response.status_code}")
        print(f"Content-Length: {len(response.content)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✓ SUCCESS!")
                print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'List'}")
                print(f"Sample data: {json.dumps(data, indent=2)[:500]}")
                return {'success': True, 'data': data, 'url': url}
            except Exception as e:
                print(f"× JSON parse error: {str(e)}")
                print(f"Response text: {response.text[:500]}")
                return {'success': False, 'error': 'JSON parse error'}
        else:
            print(f"× Failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return {'success': False, 'status': response.status_code}
            
    except Exception as e:
        print(f"× Error: {str(e)}")
        return {'success': False, 'error': str(e)}


def discover_more_endpoints():
    """Try to discover more public endpoints"""
    
    print(f"\n{'=' * 70}")
    print("DISCOVERING MORE ENDPOINTS")
    print(f"{'=' * 70}")
    
    # Common API patterns to try
    patterns = [
        '/srv/v3/public/schemes',
        '/srv/v4/public/schemes',
        '/srv/v3/public/schemes/list',
        '/srv/v4/public/schemes/list',
        '/srv/v3/public/schemes/all',
        '/srv/v4/public/schemes/all',
        '/srv/v3/public/schemes/search',
        '/srv/v4/public/schemes/search',
        '/srv/v3/public/schemes/categories',
        '/srv/v4/public/schemes/categories',
        '/srv/v3/public/schemes/states',
        '/srv/v4/public/schemes/states',
    ]
    
    working = []
    
    for pattern in patterns:
        url = f"{API_SETU_BASE}{pattern}"
        print(f"\nTrying: {url}")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
            
            if response.status_code == 200:
                print(f"  ✓ SUCCESS! Size: {len(response.content)} bytes")
                try:
                    data = response.json()
                    working.append({'url': url, 'data': data})
                except:
                    print(f"  × Not JSON")
            elif response.status_code == 404:
                print(f"  × 404 Not Found")
            elif response.status_code == 401:
                print(f"  × 401 Unauthorized")
            else:
                print(f"  × {response.status_code}")
                
        except Exception as e:
            print(f"  × Error: {str(e)[:50]}")
    
    return working


def main():
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "API SETU PUBLIC ENDPOINTS" + " " * 28 + "║")
    print("║" + " " * 10 + "Testing Official Government APIs" + " " * 26 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    results = {}
    
    # Test known endpoints
    for name, path in ENDPOINTS.items():
        result = test_endpoint(name, path)
        results[name] = result
    
    # Discover more endpoints
    discovered = discover_more_endpoints()
    
    # Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    print()
    
    working_endpoints = [name for name, result in results.items() if result.get('success')]
    
    if working_endpoints or discovered:
        print(f"✓ Found {len(working_endpoints)} working known endpoints")
        print(f"✓ Discovered {len(discovered)} additional endpoints")
        print()
        
        for name in working_endpoints:
            print(f"  • {name}: {results[name]['url']}")
        
        for disc in discovered:
            print(f"  • Discovered: {disc['url']}")
        
        # Save all data
        output = {
            'known_endpoints': results,
            'discovered_endpoints': discovered,
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        output_file = os.path.join('..', 'data', 'apisetu_data.json')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved to: {output_file}")
        
        # Extract ministry data if available
        for name, result in results.items():
            if result.get('success') and 'ministry' in name.lower():
                data = result['data']
                print(f"\n{name} data:")
                print(json.dumps(data, indent=2)[:1000])
        
    else:
        print("× No working endpoints found")
        print("\nThese endpoints might require:")
        print("  1. API keys from API Setu registration")
        print("  2. Specific request parameters")
        print("  3. POST requests instead of GET")


if __name__ == '__main__':
    main()
