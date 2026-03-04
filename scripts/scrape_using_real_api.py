"""
Scrape schemes using the REAL myScheme.gov.in API
Discovered endpoint: https://api.myscheme.gov.in/search/v6/schemes/facets
"""
import requests
import json
from datetime import datetime
import time
import os

# Real API endpoint discovered from network traffic
BASE_API = "https://api.myscheme.gov.in/search/v6"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.myscheme.gov.in/',
    'Origin': 'https://www.myscheme.gov.in',
}

# Indian States
STATES = [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
    'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
    'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
    'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
    'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
    'Andaman and Nicobar Islands', 'Chandigarh', 
    'Dadra and Nagar Haveli and Daman and Diu',
    'Delhi', 'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry'
]


def get_schemes_by_level(level='Central'):
    """Get schemes by level (Central or State)"""
    url = f"{BASE_API}/schemes/facets"
    params = {
        'lang': 'en',
        'q': json.dumps([{"identifier": "level", "value": level}])
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  × Status {response.status_code}")
            return None
    except Exception as e:
        print(f"  × Error: {str(e)[:50]}")
        return None


def get_schemes_by_state(state):
    """Get schemes for a specific state"""
    url = f"{BASE_API}/schemes/facets"
    params = {
        'lang': 'en',
        'q': json.dumps([
            {"identifier": "level", "value": "State"},
            {"identifier": "state", "value": state}
        ])
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None


def search_all_schemes():
    """Search for all schemes without filters"""
    url = f"{BASE_API}/schemes"
    params = {'lang': 'en'}
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None


def main():
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "REAL API SCRAPER FOR myScheme" + " " * 24 + "║")
    print("║" + " " * 10 + "Using Discovered API Endpoint" + " " * 29 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    all_schemes = []
    
    # Try to get all schemes first
    print("=" * 70)
    print("FETCHING ALL SCHEMES")
    print("=" * 70)
    print()
    
    all_data = search_all_schemes()
    if all_data:
        print(f"✓ Response received")
        print(f"  Keys: {list(all_data.keys())}")
        
        if 'schemes' in all_data:
            schemes = all_data['schemes']
            print(f"  ✓ Found {len(schemes)} schemes")
            all_schemes.extend(schemes)
        elif 'data' in all_data:
            schemes = all_data['data']
            print(f"  ✓ Found {len(schemes)} schemes")
            all_schemes.extend(schemes)
        else:
            print(f"  Response structure: {json.dumps(all_data, indent=2)[:500]}")
    
    # Get Central schemes
    print("\n" + "=" * 70)
    print("FETCHING CENTRAL SCHEMES")
    print("=" * 70)
    print()
    
    central_data = get_schemes_by_level('Central')
    if central_data:
        print(f"✓ Response received")
        print(f"  Keys: {list(central_data.keys())}")
        
        if 'schemes' in central_data:
            schemes = central_data['schemes']
            print(f"  ✓ Found {len(schemes)} central schemes")
            for scheme in schemes:
                scheme['level'] = 'Central'
                scheme['state'] = 'All India'
            all_schemes.extend(schemes)
        elif 'facets' in central_data:
            print(f"  Facets: {central_data['facets']}")
    
    # Get State schemes
    print("\n" + "=" * 70)
    print("FETCHING STATE SCHEMES")
    print("=" * 70)
    print()
    
    state_data = get_schemes_by_level('State')
    if state_data:
        print(f"✓ Response received")
        print(f"  Keys: {list(state_data.keys())}")
        
        if 'schemes' in state_data:
            schemes = state_data['schemes']
            print(f"  ✓ Found {len(schemes)} state schemes")
            for scheme in schemes:
                scheme['level'] = 'State'
            all_schemes.extend(schemes)
    
    # Try each state individually
    print("\n" + "=" * 70)
    print("FETCHING SCHEMES BY STATE")
    print("=" * 70)
    print()
    
    for i, state in enumerate(STATES, 1):
        print(f"[{i}/{len(STATES)}] {state}")
        
        state_schemes = get_schemes_by_state(state)
        if state_schemes:
            if 'schemes' in state_schemes:
                schemes = state_schemes['schemes']
                print(f"  ✓ {len(schemes)} schemes")
                for scheme in schemes:
                    scheme['level'] = 'State'
                    scheme['state'] = state
                all_schemes.extend(schemes)
            else:
                print(f"  × No schemes key")
        else:
            print(f"  × Failed")
        
        time.sleep(0.5)  # Be respectful
    
    # Remove duplicates
    print("\n" + "=" * 70)
    print("PROCESSING RESULTS")
    print("=" * 70)
    print()
    
    unique_schemes = []
    seen_ids = set()
    
    for scheme in all_schemes:
        scheme_id = scheme.get('id') or scheme.get('schemeId') or scheme.get('name')
        if scheme_id and scheme_id not in seen_ids:
            seen_ids.add(scheme_id)
            unique_schemes.append(scheme)
    
    print(f"Total schemes fetched: {len(all_schemes)}")
    print(f"Unique schemes: {len(unique_schemes)}")
    
    if unique_schemes:
        # Save to file
        output_file = os.path.join('..', 'data', 'schemes_from_real_api.json')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Organize by level
        central = [s for s in unique_schemes if s.get('level') == 'Central']
        state = [s for s in unique_schemes if s.get('level') == 'State']
        
        # Organize by state
        by_state = {}
        for scheme in state:
            state_name = scheme.get('state', 'Unknown')
            if state_name not in by_state:
                by_state[state_name] = []
            by_state[state_name].append(scheme)
        
        output_data = {
            'schemes': unique_schemes,
            'central_schemes': central,
            'state_schemes_by_state': by_state,
            'metadata': {
                'totalSchemes': len(unique_schemes),
                'centralSchemes': len(central),
                'stateSchemes': len(state),
                'statesCovered': len(by_state),
                'scrapedAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'myScheme.gov.in Real API',
                'apiEndpoint': BASE_API
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved to: {output_file}")
        print(f"  • Total schemes: {len(unique_schemes)}")
        print(f"  • Central: {len(central)}")
        print(f"  • State: {len(state)}")
        print(f"  • States covered: {len(by_state)}")
        
        # Show sample scheme
        if unique_schemes:
            print(f"\nSample scheme:")
            sample = unique_schemes[0]
            print(f"  Name: {sample.get('name', 'N/A')}")
            print(f"  ID: {sample.get('id', 'N/A')}")
            print(f"  Level: {sample.get('level', 'N/A')}")
            print(f"  Keys: {list(sample.keys())}")
        
        print("\n" + "=" * 70)
        print("SUCCESS!")
        print("=" * 70)
    else:
        print("\n× No schemes found")
        print("\nThe API might require:")
        print("  1. Authentication tokens")
        print("  2. Different query parameters")
        print("  3. POST requests instead of GET")
        print("\nTry running the Selenium scraper instead:")
        print("  python scrape_myscheme_complete.py")


if __name__ == '__main__':
    main()
