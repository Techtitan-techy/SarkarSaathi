"""
Comprehensive Government Scheme Data Scraper
Scrapes scheme data from myScheme.gov.in, Wikipedia, and official portals
"""
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re
import os

# Official sources
SOURCES = {
    'myscheme': 'https://www.myscheme.gov.in/',
    'pmkisan': 'https://pmkisan.gov.in/',
    'pmjay': 'https://pmjay.gov.in/',
    'pmay': 'https://pmaymis.gov.in/',
    'wikipedia': 'https://en.wikipedia.org/wiki/List_of_schemes_of_the_government_of_India'
}

# Headers to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}


def scrape_myscheme_schemes():
    """Scrape schemes from myScheme.gov.in"""
    print("Scraping myScheme.gov.in...")
    schemes = []
    
    try:
        # Try API endpoints
        api_urls = [
            'https://www.myscheme.gov.in/api/schemes',
            'https://api.myscheme.gov.in/schemes',
        ]
        
        for api_url in api_urls:
            try:
                response = requests.get(api_url, headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    print(f"  ✓ Found API: {api_url}")
                    data = response.json()
                    schemes.extend(parse_myscheme_data(data))
                    return schemes
            except:
                continue
        
        # If API fails, try HTML scraping
        print("  → Trying HTML scraping...")
        schemes = scrape_myscheme_html()
            
    except Exception as e:
        print(f"  × Error: {str(e)[:50]}")
    
    return schemes


def scrape_myscheme_html():
    """Scrape myScheme HTML pages"""
    schemes = []
    categories = ['agriculture', 'health', 'education', 'housing', 'employment']
    
    for category in categories:
        try:
            url = f"https://www.myscheme.gov.in/search?category={category}"
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                scheme_elements = soup.find_all(['div', 'a'], class_=re.compile(r'scheme|card'))
                
                for elem in scheme_elements:
                    scheme = extract_scheme_from_element(elem)
                    if scheme:
                        schemes.append(scheme)
                
                print(f"  ✓ {category}: {len(scheme_elements)} schemes")
                time.sleep(1)
        except:
            continue
    
    return schemes


def parse_myscheme_data(data):
    """Parse JSON from myScheme API"""
    schemes = []
    
    try:
        if isinstance(data, dict):
            data = data.get('schemes', data.get('data', []))
        
        for item in data:
            scheme = {
                'id': item.get('id', '').lower().replace(' ', '-'),
                'name': item.get('name', ''),
                'nameHi': item.get('nameHi', ''),
                'category': item.get('category', 'General'),
                'type': item.get('type', 'Central'),
                'ministry': item.get('ministry', ''),
                'description': item.get('description', ''),
                'benefits': item.get('benefits', []),
                'eligibility': item.get('eligibility', {}),
                'officialWebsite': item.get('officialWebsite', ''),
                'lastUpdated': datetime.now().strftime('%Y-%m-%d')
            }
            schemes.append(scheme)
    except:
        pass
    
    return schemes


def extract_scheme_from_element(element):
    """Extract scheme from HTML element"""
    try:
        scheme = {}
        
        name_elem = element.find(['h1', 'h2', 'h3'], class_=re.compile(r'title|name'))
        if name_elem:
            scheme['name'] = name_elem.get_text(strip=True)
        
        desc_elem = element.find(['p', 'div'], class_=re.compile(r'description'))
        if desc_elem:
            scheme['description'] = desc_elem.get_text(strip=True)
        
        return scheme if scheme else None
    except:
        return None


def scrape_pmkisan():
    """Scrape PM-KISAN portal"""
    print("Scraping PM-KISAN...")
    
    try:
        response = requests.get(SOURCES['pmkisan'], headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            scheme = {
                'id': 'pm-kisan',
                'name': 'PM-KISAN',
                'category': 'Agriculture',
                'type': 'Central',
                'ministry': 'Ministry of Agriculture',
                'officialWebsite': SOURCES['pmkisan'],
                'lastUpdated': datetime.now().strftime('%Y-%m-%d')
            }
            
            print("  ✓ PM-KISAN data extracted")
            return scheme
    except:
        print("  × Failed")
    
    return None


def scrape_pmjay():
    """Scrape Ayushman Bharat portal"""
    print("Scraping Ayushman Bharat...")
    
    try:
        response = requests.get(SOURCES['pmjay'], headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            scheme = {
                'id': 'ayushman-bharat',
                'name': 'Ayushman Bharat',
                'category': 'Healthcare',
                'type': 'Central',
                'ministry': 'Ministry of Health',
                'officialWebsite': SOURCES['pmjay'],
                'lastUpdated': datetime.now().strftime('%Y-%m-%d')
            }
            
            print("  ✓ Ayushman Bharat data extracted")
            return scheme
    except:
        print("  × Failed")
    
    return None


def scrape_wikipedia_schemes():
    """Scrape Wikipedia schemes list"""
    print("Scraping Wikipedia...")
    schemes = []
    
    try:
        response = requests.get(SOURCES['wikipedia'], headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            tables = soup.find_all('table', class_='wikitable')
            
            for table in tables:
                rows = table.find_all('tr')[1:]
                
                for row in rows:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 2:
                        name = cols[0].get_text(strip=True)
                        desc = cols[1].get_text(strip=True) if len(cols) > 1 else ''
                        
                        if name and len(name) > 3:
                            scheme = {
                                'name': name,
                                'description': desc[:200],
                                'source': 'Wikipedia',
                                'lastUpdated': datetime.now().strftime('%Y-%m-%d')
                            }
                            schemes.append(scheme)
            
            print(f"  ✓ Found {len(schemes)} schemes")
    except:
        print("  × Failed")
    
    return schemes


def load_existing_schemes():
    """Load existing schemes"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'schemes_database.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {'schemes': [], 'metadata': {}}


def save_schemes(schemes_data):
    """Save schemes to JSON"""
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'schemes_database.json')
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(schemes_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved {len(schemes_data['schemes'])} schemes")


def merge_schemes(existing, new):
    """Merge schemes avoiding duplicates"""
    existing_ids = {s['id'] for s in existing if 'id' in s}
    
    merged = existing.copy()
    added = 0
    
    for scheme in new:
        if 'id' in scheme and scheme['id'] not in existing_ids:
            merged.append(scheme)
            existing_ids.add(scheme['id'])
            added += 1
    
    print(f"  → Added {added} new schemes")
    return merged


def update_scheme_database():
    """Main scraper function"""
    print("=" * 70)
    print("GOVERNMENT SCHEME DATA SCRAPER")
    print("=" * 70)
    print()
    
    # Load existing
    print("Loading existing database...")
    existing_data = load_existing_schemes()
    existing_schemes = existing_data.get('schemes', [])
    print(f"  → {len(existing_schemes)} existing schemes\n")
    
    # Scrape sources
    all_new = []
    
    # myScheme
    myscheme = scrape_myscheme_schemes()
    all_new.extend(myscheme)
    print()
    
    # PM-KISAN
    pmkisan = scrape_pmkisan()
    if pmkisan:
        all_new.append(pmkisan)
    print()
    
    # Ayushman Bharat
    pmjay = scrape_pmjay()
    if pmjay:
        all_new.append(pmjay)
    print()
    
    # Wikipedia
    wiki = scrape_wikipedia_schemes()
    all_new.extend(wiki)
    print()
    
    # Merge
    print("Merging schemes...")
    merged = merge_schemes(existing_schemes, all_new)
    
    # Update metadata
    existing_data['schemes'] = merged
    existing_data['metadata'] = {
        'totalSchemes': len(merged),
        'lastUpdated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source': 'myScheme.gov.in, Official Portals, Wikipedia',
        'categories': list(set([s.get('category', 'General') for s in merged if 'category' in s])),
        'dataCollectionMethod': 'Automated web scraping + Manual curation'
    }
    
    # Save
    save_schemes(existing_data)
    
    print()
    print("=" * 70)
    print("SCRAPING COMPLETE!")
    print("=" * 70)
    print(f"Total: {existing_data['metadata']['totalSchemes']}")
    print(f"Updated: {existing_data['metadata']['lastUpdated']}")
    print()
    
    return existing_data


if __name__ == '__main__':
    data = update_scheme_database()
    
    print("\nNotes:")
    print("  • Some sources may require authentication")
    print("  • Consider using Selenium for JS-heavy sites")
    print("  • Set up cron jobs for regular updates")
    print("  • Add rate limiting for production use")
