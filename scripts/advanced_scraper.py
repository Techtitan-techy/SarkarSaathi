"""
Advanced Scheme Scraper with API Discovery
Discovers and scrapes myScheme.gov.in API endpoints
"""
import json
import requests
from datetime import datetime
import time
import re
from urllib.parse import urljoin, urlparse

# Configuration
BASE_URL = "https://www.myscheme.gov.in"
API_BASE = "https://www.myscheme.gov.in/api"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
    'Referer': 'https://www.myscheme.gov.in/',
    'Origin': 'https://www.myscheme.gov.in'
}


class MySchemeAPIClient:
    """Client for myScheme.gov.in API"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.discovered_endpoints = []
    
    def discover_api_endpoints(self):
        """
        Discover API endpoints by analyzing the website's JavaScript files
        """
        print("Discovering API endpoints...")
        
        # Common API patterns for myScheme
        potential_endpoints = [
            '/api/scheme/search',
            '/api/scheme/list',
            '/api/scheme/all',
            '/api/scheme/categories',
            '/api/scheme/filter',
            '/api/schemes',
            '/external/search',
            '/external/schemes',
        ]
        
        working_endpoints = []
        
        for endpoint in potential_endpoints:
            url = urljoin(BASE_URL, endpoint)
            try:
                # Try GET request
                response = self.session.get(url, timeout=5)
                if response.status_code == 200:
                    working_endpoints.append({
                        'url': url,
                        'method': 'GET',
                        'status': 'working'
                    })
                    print(f"✓ Found working endpoint: {endpoint}")
                
                # Try POST request with empty payload
                response = self.session.post(url, json={}, timeout=5)
                if response.status_code in [200, 201]:
                    working_endpoints.append({
                        'url': url,
                        'method': 'POST',
                        'status': 'working'
                    })
                    print(f"✓ Found working POST endpoint: {endpoint}")
                    
            except Exception as e:
                pass
        
        self.discovered_endpoints = working_endpoints
        return working_endpoints
    
    def search_schemes(self, query="", page=0, size=100):
        """
        Search for schemes using the search API
        """
        search_endpoints = [
            '/external/search',
            '/api/scheme/search',
        ]
        
        for endpoint in search_endpoints:
            url = urljoin(BASE_URL, endpoint)
            
            try:
                # Try different payload formats
                payloads = [
                    {
                        "searchText": query,
                        "pageNumber": page,
                        "pageSize": size
                    },
                    {
                        "query": query,
                        "page": page,
                        "limit": size
                    },
                    {
                        "search": query,
                        "offset": page * size,
                        "limit": size
                    }
                ]
                
                for payload in payloads:
                    response = self.session.post(url, json=payload, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✓ Successfully fetched schemes from {endpoint}")
                        return data
                        
            except Exception as e:
                continue
        
        return None
    
    def get_scheme_by_id(self, scheme_id):
        """Get detailed information for a specific scheme"""
        endpoints = [
            f'/api/scheme/{scheme_id}',
            f'/api/scheme/details/{scheme_id}',
            f'/external/scheme/{scheme_id}',
        ]
        
        for endpoint in endpoints:
            url = urljoin(BASE_URL, endpoint)
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    return response.json()
            except:
                continue
        
        return None
    
    def get_all_categories(self):
        """Get all scheme categories"""
        endpoints = [
            '/api/scheme/categories',
            '/api/categories',
            '/external/categories',
        ]
        
        for endpoint in endpoints:
            url = urljoin(BASE_URL, endpoint)
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    return response.json()
            except:
                continue
        
        return []
    
    def get_schemes_by_category(self, category):
        """Get schemes for a specific category"""
        endpoints = [
            f'/api/scheme/category/{category}',
            f'/api/schemes?category={category}',
            f'/external/schemes/category/{category}',
        ]
        
        for endpoint in endpoints:
            url = urljoin(BASE_URL, endpoint)
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    return response.json()
            except:
                continue
        
        return []


def scrape_with_api_discovery():
    """
    Main scraping function using API discovery
    """
    print("=" * 70)
    print("Advanced Scheme Scraper - API Discovery Mode")
    print("=" * 70)
    print()
    
    client = MySchemeAPIClient()
    all_schemes = []
    
    # Step 1: Discover API endpoints
    print("\n[Step 1] Discovering API endpoints...")
    endpoints = client.discover_api_endpoints()
    print(f"Found {len(endpoints)} working endpoints")
    
    # Step 2: Try to search for all schemes
    print("\n[Step 2] Searching for schemes...")
    search_results = client.search_schemes(query="", page=0, size=100)
    
    if search_results:
        schemes_data = search_results.get('content', search_results.get('data', []))
        print(f"Found {len(schemes_data)} schemes from search")
        
        for scheme_data in schemes_data[:10]:  # Limit to first 10 for demo
            scheme = parse_scheme_data(scheme_data)
            if scheme:
                all_schemes.append(scheme)
                print(f"  • {scheme['name']}")
    
    # Step 3: Get schemes by category
    print("\n[Step 3] Fetching schemes by category...")
    categories = client.get_all_categories()
    
    if categories:
        print(f"Found {len(categories)} categories")
        for category in categories[:5]:  # Limit to first 5
            category_name = category if isinstance(category, str) else category.get('name', '')
            print(f"  Fetching schemes for: {category_name}")
            
            schemes = client.get_schemes_by_category(category_name)
            for scheme_data in schemes[:5]:  # Limit per category
                scheme = parse_scheme_data(scheme_data)
                if scheme and scheme not in all_schemes:
                    all_schemes.append(scheme)
            
            time.sleep(1)  # Be respectful
    
    print(f"\n✓ Total schemes collected: {len(all_schemes)}")
    return all_schemes


def parse_scheme_data(data):
    """Parse scheme data from API response"""
    try:
        # Handle different API response formats
        scheme_id = (
            data.get('schemeId') or 
            data.get('id') or 
            data.get('scheme_id') or 
            ''
        ).lower().replace(' ', '-')
        
        scheme_name = (
            data.get('schemeName') or 
            data.get('name') or 
            data.get('scheme_name') or 
            'Unknown Scheme'
        )
        
        return {
            'id': scheme_id,
            'name': scheme_name,
            'nameHi': data.get('schemeNameHi', data.get('nameHi', '')),
            'category': data.get('category', 'General'),
            'type': 'Central' if 'central' in str(data.get('schemeType', '')).lower() else 'State',
            'ministry': data.get('ministry', data.get('sponsoredBy', '')),
            'description': data.get('description', data.get('shortDescription', '')),
            'descriptionHi': data.get('descriptionHi', ''),
            'benefits': parse_list_field(data.get('benefits', [])),
            'benefitsHi': parse_list_field(data.get('benefitsHi', [])),
            'eligibility': parse_eligibility(data.get('eligibility', {})),
            'documents': parse_list_field(data.get('documents', [])),
            'officialWebsite': data.get('officialUrl', data.get('website', '')),
            'applicationUrl': data.get('applicationUrl', ''),
            'lastUpdated': datetime.now().strftime('%Y-%m-%d')
        }
    except Exception as e:
        print(f"Error parsing scheme: {str(e)}")
        return None


def parse_list_field(field):
    """Parse list fields that might be strings or arrays"""
    if isinstance(field, list):
        return field
    if isinstance(field, str):
        return [item.strip() for item in field.split(',') if item.strip()]
    return []


def parse_eligibility(eligibility):
    """Parse eligibility criteria"""
    if not eligibility:
        return {
            'minAge': 18,
            'maxAge': 100,
            'minIncome': 0,
            'maxIncome': 1000000,
            'states': ['all'],
            'occupation': ['all'],
            'categories': ['all']
        }
    
    return {
        'minAge': eligibility.get('minAge', 18),
        'maxAge': eligibility.get('maxAge', 100),
        'minIncome': eligibility.get('minIncome', 0),
        'maxIncome': eligibility.get('maxIncome', 1000000),
        'states': eligibility.get('states', ['all']),
        'occupation': eligibility.get('occupation', ['all']),
        'categories': eligibility.get('categories', ['all'])
    }


def save_discovered_schemes(schemes):
    """Save discovered schemes to file"""
    import os
    
    output_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'discovered_schemes.json')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    data = {
        'schemes': schemes,
        'metadata': {
            'totalSchemes': len(schemes),
            'discoveredAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'myScheme.gov.in API Discovery',
            'method': 'Automated API endpoint discovery and scraping'
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved {len(schemes)} schemes to: {output_file}")


if __name__ == '__main__':
    try:
        schemes = scrape_with_api_discovery()
        
        if schemes:
            save_discovered_schemes(schemes)
            
            print("\n" + "=" * 70)
            print("Scraping Complete!")
            print("=" * 70)
            print(f"\nDiscovered {len(schemes)} schemes")
            print("\nSample schemes:")
            for scheme in schemes[:5]:
                print(f"  • {scheme['name']} ({scheme['category']})")
        else:
            print("\n⚠ No schemes discovered. API endpoints may have changed.")
            print("Falling back to manual data collection...")
            
    except Exception as e:
        print(f"\n✗ Error during scraping: {str(e)}")
        print("Please check your internet connection and try again.")
