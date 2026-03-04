"""
Complete myScheme.gov.in Scraper with Selenium
Gets ALL Central and State schemes by filling the form and extracting results
"""
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os


# Indian States
STATES = [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
    'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
    'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
    'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
    'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
    'Andaman and Nicobar Islands', 'Chandigarh', 'Dadra and Nagar Haveli and Daman and Diu',
    'Delhi', 'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry'
]


class MySchemeCompleteScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.all_schemes = []
        
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        print("Setting up Chrome WebDriver...")
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        print("  ✓ WebDriver ready\n")
    
    def fill_form_and_search(self, state=None, age=25, gender='Male'):
        """Fill the myScheme form and search for schemes"""
        try:
            # Navigate to find-scheme page
            self.driver.get('https://www.myscheme.gov.in/find-scheme')
            time.sleep(3)
            
            # Fill gender
            try:
                gender_radio = self.driver.find_element(By.XPATH, f"//input[@value='{gender}']")
                gender_radio.click()
            except:
                pass
            
            # Fill age
            try:
                age_input = self.driver.find_element(By.NAME, 'age')
                age_input.clear()
                age_input.send_keys(str(age))
            except:
                pass
            
            # Select state if provided
            if state:
                try:
                    state_dropdown = Select(self.driver.find_element(By.NAME, 'state'))
                    state_dropdown.select_by_visible_text(state)
                except:
                    pass
            
            # Click search/submit button
            try:
                submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Search') or contains(text(), 'Submit')]")
                submit_btn.click()
                time.sleep(3)
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"  × Form fill error: {str(e)[:50]}")
            return False
    
    def extract_schemes_from_results(self, state=None):
        """Extract all schemes from search results"""
        schemes = []
        
        try:
            # Wait for results to load
            wait = WebDriverWait(self.driver, 10)
            
            # Scroll to load all schemes
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            for _ in range(5):  # Scroll 5 times
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # Find all scheme cards/elements
            scheme_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                '[class*="scheme"], [class*="card"], [class*="result"]')
            
            print(f"  → Found {len(scheme_elements)} scheme elements")
            
            for elem in scheme_elements:
                try:
                    scheme = self.extract_scheme_details(elem, state)
                    if scheme:
                        schemes.append(scheme)
                except:
                    continue
            
        except TimeoutException:
            print("  × Timeout waiting for results")
        except Exception as e:
            print(f"  × Extraction error: {str(e)[:50]}")
        
        return schemes
    
    def extract_scheme_details(self, element, state=None):
        """Extract details from a scheme element"""
        try:
            scheme = {
                'type': 'State' if state else 'Central',
                'state': state if state else 'All India',
                'scrapedAt': datetime.now().strftime('%Y-%m-%d')
            }
            
            # Extract name
            try:
                name = element.find_element(By.CSS_SELECTOR, 'h1, h2, h3, h4, [class*="title"], [class*="name"]')
                scheme['name'] = name.text.strip()
            except:
                pass
            
            # Extract description
            try:
                desc = element.find_element(By.CSS_SELECTOR, 'p, [class*="description"], [class*="summary"]')
                scheme['description'] = desc.text.strip()[:300]
            except:
                pass
            
            # Extract category
            try:
                category = element.find_element(By.CSS_SELECTOR, '[class*="category"], [class*="tag"]')
                scheme['category'] = category.text.strip()
            except:
                pass
            
            # Extract link
            try:
                link = element.find_element(By.TAG_NAME, 'a')
                scheme['url'] = link.get_attribute('href')
            except:
                pass
            
            return scheme if 'name' in scheme else None
            
        except:
            return None
    
    def scrape_all_states(self):
        """Scrape schemes for all states"""
        print("=" * 70)
        print("SCRAPING ALL STATES")
        print("=" * 70)
        print()
        
        for i, state in enumerate(STATES, 1):
            print(f"[{i}/{len(STATES)}] {state}")
            
            # Fill form for this state
            if self.fill_form_and_search(state=state):
                # Extract schemes
                schemes = self.extract_schemes_from_results(state=state)
                self.all_schemes.extend(schemes)
                print(f"  ✓ {len(schemes)} schemes found")
            else:
                print(f"  × Failed to search")
            
            time.sleep(2)  # Be respectful
        
        print(f"\n✓ Total schemes from all states: {len(self.all_schemes)}\n")
    
    def scrape_central_schemes(self):
        """Scrape central government schemes"""
        print("=" * 70)
        print("SCRAPING CENTRAL SCHEMES")
        print("=" * 70)
        print()
        
        # Search without state filter to get central schemes
        if self.fill_form_and_search(state=None):
            schemes = self.extract_schemes_from_results(state=None)
            self.all_schemes.extend(schemes)
            print(f"✓ {len(schemes)} central schemes found\n")
    
    def scrape_complete(self):
        """Main scraping method"""
        print("\n")
        print("╔" + "═" * 68 + "╗")
        print("║" + " " * 15 + "COMPLETE myScheme.gov.in SCRAPER" + " " * 21 + "║")
        print("║" + " " * 20 + "ALL SCHEMES - STATE WISE" + " " * 24 + "║")
        print("╚" + "═" * 68 + "╝")
        print()
        
        try:
            self.setup_driver()
            
            start_time = time.time()
            
            # Scrape central schemes
            self.scrape_central_schemes()
            
            # Scrape all state schemes
            self.scrape_all_states()
            
            duration = time.time() - start_time
            
            # Remove duplicates
            unique_schemes = self.remove_duplicates(self.all_schemes)
            
            print("=" * 70)
            print("SCRAPING COMPLETE!")
            print("=" * 70)
            print(f"Duration: {duration/60:.1f} minutes")
            print(f"Total schemes scraped: {len(self.all_schemes)}")
            print(f"Unique schemes: {len(unique_schemes)}")
            print()
            
            return unique_schemes
            
        except Exception as e:
            print(f"\n× Fatal error: {str(e)}")
            return []
        
        finally:
            if self.driver:
                self.driver.quit()
                print("✓ WebDriver closed\n")
    
    def remove_duplicates(self, schemes):
        """Remove duplicate schemes"""
        seen = set()
        unique = []
        
        for scheme in schemes:
            identifier = scheme.get('name', '') + scheme.get('state', '')
            if identifier and identifier not in seen:
                seen.add(identifier)
                unique.append(scheme)
        
        return unique
    
    def save_schemes(self, schemes):
        """Save schemes to JSON"""
        file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'myscheme_complete.json')
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Organize by type
        central = [s for s in schemes if s.get('type') == 'Central']
        state = [s for s in schemes if s.get('type') == 'State']
        
        # Organize by state
        by_state = {}
        for scheme in state:
            state_name = scheme.get('state', 'Unknown')
            if state_name not in by_state:
                by_state[state_name] = []
            by_state[state_name].append(scheme)
        
        data = {
            'schemes': schemes,
            'central_schemes': central,
            'state_schemes_by_state': by_state,
            'metadata': {
                'totalSchemes': len(schemes),
                'centralSchemes': len(central),
                'stateSchemes': len(state),
                'statesCovered': len(by_state),
                'scrapedAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'myScheme.gov.in',
                'method': 'Selenium WebDriver - Complete State-wise Scrape'
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved to: myscheme_complete.json")
        print(f"  • Total schemes: {len(schemes)}")
        print(f"  • Central: {len(central)}")
        print(f"  • State: {len(state)}")
        print(f"  • States covered: {len(by_state)}")
        print()


def main():
    print("\nIMPORTANT: This scraper will take 30-60 minutes to complete.")
    print("It will scrape schemes for all 36 states/UTs.\n")
    
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("Scraping cancelled.")
        return
    
    scraper = MySchemeCompleteScraper(headless=True)
    
    try:
        schemes = scraper.scrape_complete()
        
        if schemes:
            scraper.save_schemes(schemes)
            
            print("=" * 70)
            print("SUCCESS!")
            print("=" * 70)
            print("All schemes have been scraped and saved.")
            print("Check: data/myscheme_complete.json")
        else:
            print("\n× No schemes scraped")
            print("\nTroubleshooting:")
            print("  1. Run with headless=False to see browser")
            print("  2. Check if myScheme.gov.in is accessible")
            print("  3. Website structure may have changed")
    
    except KeyboardInterrupt:
        print("\n\n× Scraping interrupted by user")
    except Exception as e:
        print(f"\n× Error: {str(e)}")


if __name__ == '__main__':
    main()
