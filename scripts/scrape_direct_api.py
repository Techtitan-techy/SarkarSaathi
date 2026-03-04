"""
Direct API Scraper for myScheme.gov.in
Tries multiple API endpoint patterns to get scheme data
"""
import requests
import json
from datetime import datetime
import time
import os

# Possible API endpoints based on common patterns
API_ENDPOINTS = [
    # myScheme API patterns
    'https://www.myscheme.gov.in/api/scheme',
    'https://www.myscheme.gov.in/api/schemes',
    'https://www.myscheme.gov.in/api/v1/schemes',
    'https://www.myscheme.gov.in/api/v2/schemes',
    'https://api.myscheme.gov.in/schemes',
    'https://api.myscheme.gov.in/v1/schemes',
    
    # Search endpoints
    'https://www.myscheme.gov.in/api/search',
    'https://www.myscheme.gov.in/api/scheme/search',
    'https://www.myscheme.gov.in/api/v1/search',
    
    # Data endpoints
    'https://www.myscheme.gov.in/api/data/schemes',
    'https://www.myscheme.gov.in/data/schemes.json',
    'https://www.myscheme.gov.in/schemes.json',
    
    # Backend endpoints
    'https://backend.myscheme.gov.in/api/schemes',
    'https://backend.myscheme.gov.in/schemes',
    
    # CDN endpoints
    'https://cdn.myscheme.gov.in/data/schemes.json',
    'https://cdn.myscheme.gov.in/schemes.json',
]

# API Setu endpoints
API_SETU_ENDPOINTS = [
    'https://www.apisetu.gov.in/api/myscheme/schemes',
    'https://api.apisetu.gov.in/myscheme/schemes',
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.myscheme.gov.in/',
    'Origin': 'https://www.myscheme.gov.in',
}


def try_api_endpoint(url, method='GET', data=None):
    """Try to access an API endpoint"""
    try:
        if method == 'GET':
            response = requests.get(url, headers=HEADERS, timeout=10)
        else:
            response = requests.post(url, headers=HEADERS, json=data, timeout=10)
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                return {
                    'success': True,
                    'url': url,
                    'data': json_data,
                    'size': len(response.content)
                }
            except:
                # Not JSON, might be HTML
                return {
                    'success': False,
                    'url': url,
                    'error': 'Not JSON response'
                }
        else:
            return {
                'success': False,
                'url': url,
                'status': response.status_code
            }
    except requests.Timeout:
        return {'success': False, 'url': url, 'error': 'Timeout'}
    except requests.ConnectionError:
        return {'success': False, 'url': url, 'error': 'Connection error'}
    except Exception as e:
        return {'success': False, 'url': url, 'error': str(e)[:50]}


def discover_working_apis():
    """Try all possible API endpoints"""
    print("=" * 70)
    print("DISCOVERING WORKING API ENDPOINTS")
    print("=" * 70)
    print()
    
    working_apis = []
    
    print("Testing myScheme endpoints...")
    for i, endpoint in enumerate(API_ENDPOINTS, 1):
        print(f"[{i}/{len(API_ENDPOINTS)}] {endpoint}")
        
        result = try_api_endpoint(endpoint)
        
        if result['success']:
            print(f"  ✓ SUCCESS! Size: {result['size']} bytes")
            working_apis.append(result)
        else:
            error = result.get('error', result.get('status', 'Unknown'))
            print(f"  × {error}")
        
        time.sleep(0.5)
    
    print(f"\nTesting API Setu endpoints...")
    for i, endpoint in enumerate(API_SETU_ENDPOINTS, 1):
        print(f"[{i}/{len(API_SETU_ENDPOINTS)}] {endpoint}")
        
        result = try_api_endpoint(endpoint)
        
        if result['success']:
            print(f"  ✓ SUCCESS! Size: {result['size']} bytes")
            working_apis.append(result)
        else:
            error = result.get('error', result.get('status', 'Unknown'))
            print(f"  × {error}")
        
        time.sleep(0.5)
    
    return working_apis


def try_post_requests():
    """Try POST requests with search parameters"""
    print("\n" + "=" * 70)
    print("TRYING POST REQUESTS")
    print("=" * 70)
    print()
    
    post_endpoints = [
        'https://www.myscheme.gov.in/api/search',
        'https://www.myscheme.gov.in/api/scheme/search',
        'https://www.myscheme.gov.in/api/v1/search',
    ]
    
    # Sample search payload
    search_data = {
        'age': 25,
        'gender': 'Male',
        'state': 'Delhi',
        'category': 'Agriculture'
    }
    
    working_posts = []
    
    for endpoint in post_endpoints:
        print(f"POST {endpoint}")
        
        result = try_api_endpoint(endpoint, method='POST', data=search_data)
        
        if result['success']:
            print(f"  ✓ SUCCESS! Size: {result['size']} bytes")
            working_posts.append(result)
        else:
            error = result.get('error', result.get('status', 'Unknown'))
            print(f"  × {error}")
        
        time.sleep(0.5)
    
    return working_posts


def try_graphql_endpoint():
    """Try GraphQL endpoint"""
    print("\n" + "=" * 70)
    print("TRYING GRAPHQL ENDPOINT")
    print("=" * 70)
    print()
    
    graphql_url = 'https://www.myscheme.gov.in/graphql'
    
    query = {
        'query': '''
        {
            schemes {
                id
                name
                description
                category
                state
            }
        }
        '''
    }
    
    print(f"POST {graphql_url}")
    result = try_api_endpoint(graphql_url, method='POST', data=query)
    
    if result['success']:
        print(f"  ✓ SUCCESS! Size: {result['size']} bytes")
        return [result]
    else:
        error = result.get('error', result.get('status', 'Unknown'))
        print(f"  × {error}")
        return []


def scrape_india_gov_schemes():
    """Scrape from india.gov.in"""
    print("\n" + "=" * 70)
    print("TRYING INDIA.GOV.IN")
    print("=" * 70)
    print()
    
    endpoints = [
        'https://www.india.gov.in/api/schemes',
        'https://api.india.gov.in/schemes',
        'https://www.india.gov.in/data/schemes.json',
    ]
    
    working = []
    
    for endpoint in endpoints:
        print(f"GET {endpoint}")
        result = try_api_endpoint(endpoint)
        
        if result['success']:
            print(f"  ✓ SUCCESS! Size: {result['size']} bytes")
            working.append(result)
        else:
            error = result.get('error', result.get('status', 'Unknown'))
            print(f"  × {error}")
    
    return working


def main():
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "DIRECT API SCRAPER" + " " * 30 + "║")
    print("║" + " " * 15 + "Finding Working API Endpoints" + " " * 24 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    all_working = []
    
    # Try GET requests
    working_gets = discover_working_apis()
    all_working.extend(working_gets)
    
    # Try POST requests
    working_posts = try_post_requests()
    all_working.extend(working_posts)
    
    # Try GraphQL
    working_graphql = try_graphql_endpoint()
    all_working.extend(working_graphql)
    
    # Try india.gov.in
    working_india = scrape_india_gov_schemes()
    all_working.extend(working_india)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if all_working:
        print(f"\n✓ Found {len(all_working)} working API endpoint(s)!\n")
        
        for i, api in enumerate(all_working, 1):
            print(f"{i}. {api['url']}")
            print(f"   Size: {api['size']:,} bytes")
            
            # Show sample data
            data = api['data']
            if isinstance(data, dict):
                print(f"   Keys: {list(data.keys())[:5]}")
            elif isinstance(data, list):
                print(f"   Items: {len(data)}")
                if data:
                    print(f"   Sample: {list(data[0].keys())[:5] if isinstance(data[0], dict) else data[0]}")
            print()
        
        # Save working APIs
        output = {
            'working_apis': [
                {
                    'url': api['url'],
                    'size': api['size'],
                    'discovered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                for api in all_working
            ],
            'sample_data': all_working[0]['data'] if all_working else None
        }
        
        with open('working_apis.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print("✓ Saved to: working_apis.json")
        
        # Extract and save schemes
        all_schemes = []
        for api in all_working:
            data = api['data']
            if isinstance(data, list):
                all_schemes.extend(data)
            elif isinstance(data, dict):
                if 'schemes' in data:
                    all_schemes.extend(data['schemes'])
                elif 'data' in data:
                    if isinstance(data['data'], list):
                        all_schemes.extend(data['data'])
        
        if all_schemes:
            print(f"\n✓ Extracted {len(all_schemes)} schemes")
            
            # Save schemes
            schemes_file = os.path.join('..', 'data', 'schemes_from_api.json')
            os.makedirs(os.path.dirname(schemes_file), exist_ok=True)
            
            with open(schemes_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'schemes': all_schemes,
                    'metadata': {
                        'total': len(all_schemes),
                        'source': 'Direct API',
                        'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                }, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Saved schemes to: {schemes_file}")
    
    else:
        print("\n× No working API endpoints found")
        print("\nPossible reasons:")
        print("  1. APIs require authentication")
        print("  2. APIs use different URL patterns")
        print("  3. Data is loaded dynamically via JavaScript")
        print("\nRecommendations:")
        print("  1. Run: python discover_myscheme_api.py")
        print("  2. Use Selenium scraper: python scrape_myscheme_complete.py")
        print("  3. Check browser DevTools Network tab manually")


if __name__ == '__main__':
    main()
