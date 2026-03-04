"""
Comprehensive Scheme Scraper - ALL Central and State Schemes
Scrapes complete scheme database from myScheme.gov.in organized by state
"""
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import os

# Indian States and UTs
INDIAN_STATES = [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
    'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
    'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
    'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
    'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
    'Andaman and Nicobar Islands', 'Chandigarh', 'Dadra and Nagar Haveli and Daman and Diu',
    'Delhi', 'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry'
]

# Scheme Categories
CATEGORIES = [
    'Agriculture, Rural & Environment',
    'Banking, Financial Services and Insurance',
    'Business & Entrepreneurship',
    'Education & Learning',
    'Health & Wellness',
    'Housing & Shelter',
    'Public Safety, Law & Justice',
    'Science, IT & Communications',
    'Skills & Employment',
    'Social Welfare & Empowerment',
    'Sports & Culture',
    'Transport & Infrastructure',
    'Travel & Tourism',
    'Utility & Sanitation'
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
}


class ComprehensiveSchemeScraper:
    def __init__(self):
        self.schemes = []
        self.central_schemes = []
        self.state_schemes = {}
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
    def scrape_myscheme_api(self):
        """Try to access myScheme API endpoints"""
        print("=" * 70)
        print("ATTEMPTING API ACCESS")
        print("=" * 70)
        print()
        
        # Possible API endpoints
        api_endpoints = [
            'https://www.myscheme.gov.in/api/scheme',
            'https://www.myscheme.gov.in/api/schemes',
            'https://api.myscheme.gov.in/v1/schemes',
            'https://www.myscheme.gov.in/api/v1/schemes',
            'https://www.myscheme.gov.in/api/search',
        ]
        
        for endpoint in api_endpoints:
            try:
                print(f"Trying: {endpoint}")
                response = self.session.get(endpoint, timeout=10)
                
                if response.status_code == 200:
                    print(f"  ✓ SUCCESS! Found API endpoint")
                    data = response.json()
                    print(f"  → Response keys: {list(data.keys()) if isinstance(data, dict) else 'List'}")
                    return data
                else:
                    print(f"  × Status: {response.status_code}")
                    
            except Exception as e:
                print(f"  × Error: {str(e)[:50]}")
        
        print("\n× No API endpoints found. Will use alternative methods.\n")
        return None
    
    def scrape_central_schemes(self):
        """Scrape all Central Government schemes"""
        print("=" * 70)
        print("SCRAPING CENTRAL GOVERNMENT SCHEMES")
        print("=" * 70)
        print()
        
        # Try to get central schemes list
        urls_to_try = [
            'https://www.myscheme.gov.in/search?level=central',
            'https://www.myscheme.gov.in/schemes?type=central',
            'https://www.india.gov.in/topics/agriculture/schemes',
        ]
        
        for url in urls_to_try:
            try:
                print(f"Trying: {url}")
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for scheme elements
                    scheme_elements = soup.find_all(['div', 'article', 'section'], 
                                                   class_=lambda x: x and ('scheme' in x.lower() or 'card' in x.lower()))
                    
                    if scheme_elements:
                        print(f"  ✓ Found {len(scheme_elements)} scheme elements")
                        
                        for elem in scheme_elements:
                            scheme = self.extract_scheme_info(elem, 'Central')
                            if scheme:
                                self.central_schemes.append(scheme)
                        
                        break
                    else:
                        print(f"  × No scheme elements found")
                        
            except Exception as e:
                print(f"  × Error: {str(e)[:50]}")
        
        print(f"\n✓ Total Central Schemes: {len(self.central_schemes)}\n")
    
    def scrape_state_schemes(self, state):
        """Scrape schemes for a specific state"""
        print(f"Scraping: {state}")
        
        state_code = state.lower().replace(' ', '-')
        
        urls_to_try = [
            f'https://www.myscheme.gov.in/search?state={state_code}',
            f'https://www.myscheme.gov.in/schemes?state={state}',
        ]
        
        schemes_found = []
        
        for url in urls_to_try:
            try:
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    scheme_elements = soup.find_all(['div', 'article'], 
                                                   class_=lambda x: x and 'scheme' in x.lower())
                    
                    if scheme_elements:
                        for elem in scheme_elements:
                            scheme = self.extract_scheme_info(elem, state)
                            if scheme:
                                schemes_found.append(scheme)
                        
                        print(f"  ✓ {len(schemes_found)} schemes")
                        break
                        
            except Exception as e:
                continue
        
        if not schemes_found:
            print(f"  × No schemes found")
        
        self.state_schemes[state] = schemes_found
        time.sleep(0.5)  # Be respectful
    
    def scrape_all_states(self):
        """Scrape schemes for all Indian states"""
        print("=" * 70)
        print("SCRAPING STATE-WISE SCHEMES")
        print("=" * 70)
        print()
        
        for i, state in enumerate(INDIAN_STATES, 1):
            print(f"[{i}/{len(INDIAN_STATES)}] ", end='')
            self.scrape_state_schemes(state)
        
        total_state_schemes = sum(len(schemes) for schemes in self.state_schemes.values())
        print(f"\n✓ Total State Schemes: {total_state_schemes}\n")
    
    def extract_scheme_info(self, element, location):
        """Extract scheme information from HTML element"""
        try:
            scheme = {
                'type': 'Central' if location == 'Central' else 'State',
                'state': location if location != 'Central' else 'All India',
                'lastUpdated': datetime.now().strftime('%Y-%m-%d')
            }
            
            # Extract name
            name_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5'])
            if name_elem:
                scheme['name'] = name_elem.get_text(strip=True)
            
            # Extract description
            desc_elem = element.find(['p', 'div'], class_=lambda x: x and 'desc' in x.lower())
            if desc_elem:
                scheme['description'] = desc_elem.get_text(strip=True)[:300]
            
            # Extract link
            link_elem = element.find('a', href=True)
            if link_elem:
                scheme['url'] = link_elem['href']
                if not scheme['url'].startswith('http'):
                    scheme['url'] = 'https://www.myscheme.gov.in' + scheme['url']
            
            # Extract category
            category_elem = element.find(class_=lambda x: x and 'category' in x.lower())
            if category_elem:
                scheme['category'] = category_elem.get_text(strip=True)
            
            return scheme if 'name' in scheme else None
            
        except:
            return None
    
    def scrape_by_category(self, category):
        """Scrape schemes by category"""
        print(f"Category: {category}")
        
        category_code = category.lower().replace(' ', '-').replace('&', 'and')
        url = f'https://www.myscheme.gov.in/search?category={category_code}'
        
        try:
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                scheme_elements = soup.find_all(['div', 'article'], 
                                               class_=lambda x: x and 'scheme' in x.lower())
                
                schemes_found = []
                for elem in scheme_elements:
                    scheme = self.extract_scheme_info(elem, 'Central')
                    if scheme:
                        scheme['category'] = category
                        schemes_found.append(scheme)
                
                print(f"  ✓ {len(schemes_found)} schemes")
                return schemes_found
                
        except Exception as e:
            print(f"  × Error: {str(e)[:50]}")
        
        return []
    
    def scrape_by_categories(self):
        """Scrape all schemes organized by category"""
        print("=" * 70)
        print("SCRAPING BY CATEGORIES")
        print("=" * 70)
        print()
        
        category_schemes = []
        
        for i, category in enumerate(CATEGORIES, 1):
            print(f"[{i}/{len(CATEGORIES)}] ", end='')
            schemes = self.scrape_by_category(category)
            category_schemes.extend(schemes)
            time.sleep(0.5)
        
        print(f"\n✓ Total schemes from categories: {len(category_schemes)}\n")
        return category_schemes
    
    def scrape_all(self):
        """Main method to scrape everything"""
        print("\n")
        print("╔" + "═" * 68 + "╗")
        print("║" + " " * 15 + "COMPREHENSIVE SCHEME SCRAPER" + " " * 25 + "║")
        print("║" + " " * 18 + "ALL CENTRAL & STATE SCHEMES" + " " * 23 + "║")
        print("╚" + "═" * 68 + "╝")
        print()
        
        start_time = time.time()
        
        # Method 1: Try API
        api_data = self.scrape_myscheme_api()
        if api_data:
            # Process API data
            pass
        
        # Method 2: Scrape Central Schemes
        self.scrape_central_schemes()
        
        # Method 3: Scrape State-wise
        self.scrape_all_states()
        
        # Method 4: Scrape by Categories
        category_schemes = self.scrape_by_categories()
        
        # Combine all schemes
        all_schemes = []
        all_schemes.extend(self.central_schemes)
        
        for state, schemes in self.state_schemes.items():
            all_schemes.extend(schemes)
        
        all_schemes.extend(category_schemes)
        
        # Remove duplicates
        unique_schemes = self.remove_duplicates(all_schemes)
        
        duration = time.time() - start_time
        
        # Summary
        print("=" * 70)
        print("SCRAPING COMPLETE!")
        print("=" * 70)
        print(f"Duration: {duration:.1f} seconds")
        print(f"Central Schemes: {len(self.central_schemes)}")
        print(f"State Schemes: {sum(len(s) for s in self.state_schemes.values())}")
        print(f"Category Schemes: {len(category_schemes)}")
        print(f"Total Unique Schemes: {len(unique_schemes)}")
        print()
        
        return unique_schemes
    
    def remove_duplicates(self, schemes):
        """Remove duplicate schemes"""
        seen = set()
        unique = []
        
        for scheme in schemes:
            # Create identifier
            identifier = scheme.get('name', '') + scheme.get('state', '')
            
            if identifier and identifier not in seen:
                seen.add(identifier)
                unique.append(scheme)
        
        return unique
    
    def save_schemes(self, schemes):
        """Save schemes to JSON file"""
        file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'all_schemes_comprehensive.json')
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Organize by type
        central = [s for s in schemes if s.get('type') == 'Central']
        state = [s for s in schemes if s.get('type') == 'State']
        
        # Organize state schemes by state
        by_state = {}
        for scheme in state:
            state_name = scheme.get('state', 'Unknown')
            if state_name not in by_state:
                by_state[state_name] = []
            by_state[state_name].append(scheme)
        
        data = {
            'schemes': schemes,
            'central_schemes': central,
            'state_schemes': by_state,
            'metadata': {
                'totalSchemes': len(schemes),
                'centralSchemes': len(central),
                'stateSchemes': len(state),
                'states': list(by_state.keys()),
                'scrapedAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'myScheme.gov.in - Comprehensive Scrape',
                'method': 'Multi-method scraping (API + HTML + Category + State-wise)'
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved to: all_schemes_comprehensive.json")
        print()
        
        # Also update main database
        self.update_main_database(schemes)
    
    def update_main_database(self, new_schemes):
        """Update main schemes database"""
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'schemes_database.json')
        
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except:
            existing_data = {'schemes': [], 'metadata': {}}
        
        # Merge schemes
        existing_schemes = existing_data.get('schemes', [])
        existing_ids = {s.get('name', '') + s.get('state', '') for s in existing_schemes}
        
        added = 0
        for scheme in new_schemes:
            identifier = scheme.get('name', '') + scheme.get('state', '')
            if identifier and identifier not in existing_ids:
                existing_schemes.append(scheme)
                added += 1
        
        existing_data['schemes'] = existing_schemes
        existing_data['metadata'] = {
            'totalSchemes': len(existing_schemes),
            'lastUpdated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'myScheme.gov.in - Comprehensive',
            'newSchemesAdded': added
        }
        
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Updated main database (+{added} new schemes)")


def main():
    scraper = ComprehensiveSchemeScraper()
    
    try:
        schemes = scraper.scrape_all()
        
        if schemes:
            scraper.save_schemes(schemes)
            
            print("=" * 70)
            print("SUCCESS!")
            print("=" * 70)
            print(f"Scraped {len(schemes)} schemes")
            print("Files created:")
            print("  • data/all_schemes_comprehensive.json")
            print("  • data/schemes_database.json (updated)")
            print()
        else:
            print("\n× No schemes scraped")
            print("\nNote: myScheme.gov.in may require:")
            print("  1. User interaction (form filling)")
            print("  2. JavaScript execution (use Selenium)")
            print("  3. Authentication")
            print("\nTry running: python scrape_schemes_advanced.py")
    
    except KeyboardInterrupt:
        print("\n\n× Scraping interrupted by user")
    except Exception as e:
        print(f"\n× Error: {str(e)}")


if __name__ == '__main__':
    main()
