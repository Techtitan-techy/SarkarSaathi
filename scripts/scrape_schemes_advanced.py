"""
Advanced Government Scheme Scraper with Selenium
For JavaScript-heavy sites like myScheme.gov.in
"""
import json
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os


class SchemeScraperAdvanced:
    def __init__(self, headless=True):
        """Initialize Selenium WebDriver"""
        self.headless = headless
        self.driver = None
        self.schemes = []
        
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        print("Setting up Chrome WebDriver...")
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("  ✓ WebDriver ready")
        except Exception as e:
            print(f"  × Error: {str(e)}")
            print("  → Install ChromeDriver: https://chromedriver.chromium.org/")
            raise
    
    def scrape_myscheme_with_selenium(self):
        """Scrape myScheme.gov.in using Selenium"""
        print("\nScraping myScheme.gov.in with Selenium...")
        
        try:
            # Navigate to myScheme
            self.driver.get('https://www.myscheme.gov.in/find-scheme')
            print("  → Loaded myScheme.gov.in")
            
            # Wait for page to load
            time.sleep(3)
            
            # Try to find scheme elements
            try:
                # Wait for scheme cards to load
                wait = WebDriverWait(self.driver, 10)
                scheme_elements = wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[class*="scheme"], [class*="card"]'))
                )
                
                print(f"  ✓ Found {len(scheme_elements)} scheme elements")
                
                for element in scheme_elements:
                    try:
                        scheme_data = self.extract_scheme_from_selenium_element(element)
                        if scheme_data:
                            self.schemes.append(scheme_data)
                    except:
                        continue
                
            except TimeoutException:
                print("  × Timeout waiting for schemes")
                
                # Try alternative: Search by categories
                self.scrape_by_categories()
            
        except Exception as e:
            print(f"  × Error: {str(e)}")
    
    def scrape_by_categories(self):
        """Scrape schemes by navigating through categories"""
        print("  → Trying category-based scraping...")
        
        categories = [
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
        
        for category in categories:
            try:
                print(f"    → {category}")
                
                # Try to click category or navigate
                # This depends on the actual website structure
                # You may need to inspect the website and adjust selectors
                
                time.sleep(1)
                
            except:
                continue
    
    def extract_scheme_from_selenium_element(self, element):
        """Extract scheme data from Selenium WebElement"""
        try:
            scheme = {}
            
            # Try to extract scheme name
            try:
                name = element.find_element(By.CSS_SELECTOR, 'h1, h2, h3, h4, [class*="title"], [class*="name"]')
                scheme['name'] = name.text.strip()
            except:
                pass
            
            # Try to extract description
            try:
                desc = element.find_element(By.CSS_SELECTOR, 'p, [class*="description"], [class*="summary"]')
                scheme['description'] = desc.text.strip()
            except:
                pass
            
            # Try to extract link
            try:
                link = element.find_element(By.TAG_NAME, 'a')
                scheme['url'] = link.get_attribute('href')
            except:
                pass
            
            return scheme if scheme else None
            
        except:
            return None
    
    def scrape_scheme_detail_page(self, url):
        """Scrape individual scheme detail page"""
        print(f"  → Scraping: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(2)
            
            scheme = {
                'url': url,
                'lastUpdated': datetime.now().strftime('%Y-%m-%d')
            }
            
            # Extract scheme details
            try:
                # Scheme name
                name_elem = self.driver.find_element(By.CSS_SELECTOR, 'h1, [class*="scheme-name"]')
                scheme['name'] = name_elem.text.strip()
            except:
                pass
            
            try:
                # Description
                desc_elem = self.driver.find_element(By.CSS_SELECTOR, '[class*="description"], [class*="about"]')
                scheme['description'] = desc_elem.text.strip()
            except:
                pass
            
            try:
                # Benefits
                benefits_section = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Benefits') or contains(text(), 'लाभ')]")
                benefits_parent = benefits_section.find_element(By.XPATH, '..')
                benefits_items = benefits_parent.find_elements(By.TAG_NAME, 'li')
                scheme['benefits'] = [item.text.strip() for item in benefits_items]
            except:
                pass
            
            try:
                # Eligibility
                eligibility_section = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Eligibility') or contains(text(), 'पात्रता')]")
                eligibility_parent = eligibility_section.find_element(By.XPATH, '..')
                scheme['eligibility_text'] = eligibility_parent.text.strip()
            except:
                pass
            
            return scheme
            
        except Exception as e:
            print(f"    × Error: {str(e)[:50]}")
            return None
    
    def scrape_all_scheme_urls(self):
        """Get all scheme URLs from myScheme"""
        print("\nCollecting all scheme URLs...")
        
        urls = []
        
        try:
            self.driver.get('https://www.myscheme.gov.in/search')
            time.sleep(3)
            
            # Scroll to load more schemes
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            for i in range(5):  # Scroll 5 times
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # Find all scheme links
            links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="scheme"]')
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and 'scheme' in href.lower():
                        urls.append(href)
                except:
                    continue
            
            urls = list(set(urls))  # Remove duplicates
            print(f"  ✓ Found {len(urls)} unique scheme URLs")
            
        except Exception as e:
            print(f"  × Error: {str(e)}")
        
        return urls
    
    def scrape_all_schemes(self):
        """Main method to scrape all schemes"""
        print("=" * 70)
        print("ADVANCED SCHEME SCRAPER (Selenium)")
        print("=" * 70)
        
        try:
            self.setup_driver()
            
            # Method 1: Scrape main page
            self.scrape_myscheme_with_selenium()
            
            # Method 2: Get all URLs and scrape each
            if len(self.schemes) < 10:
                print("\n→ Trying detailed scraping...")
                urls = self.scrape_all_scheme_urls()
                
                for i, url in enumerate(urls[:20], 1):  # Limit to 20 for demo
                    print(f"\n[{i}/{min(20, len(urls))}]")
                    scheme = self.scrape_scheme_detail_page(url)
                    if scheme:
                        self.schemes.append(scheme)
                    time.sleep(1)  # Be respectful
            
            print(f"\n✓ Total schemes scraped: {len(self.schemes)}")
            
        except Exception as e:
            print(f"\n× Fatal error: {str(e)}")
        
        finally:
            if self.driver:
                self.driver.quit()
                print("\n✓ WebDriver closed")
        
        return self.schemes
    
    def save_schemes(self, filename='schemes_selenium.json'):
        """Save scraped schemes to JSON"""
        file_path = os.path.join(os.path.dirname(__file__), '..', 'data', filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        data = {
            'schemes': self.schemes,
            'metadata': {
                'totalSchemes': len(self.schemes),
                'scrapedAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'method': 'Selenium WebDriver',
                'source': 'myScheme.gov.in'
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved to {filename}")


def main():
    """Main execution"""
    scraper = SchemeScraperAdvanced(headless=True)
    
    try:
        schemes = scraper.scrape_all_schemes()
        
        if schemes:
            scraper.save_schemes()
            
            print("\n" + "=" * 70)
            print("SCRAPING SUMMARY")
            print("=" * 70)
            print(f"Total schemes: {len(schemes)}")
            print(f"Sample scheme: {schemes[0].get('name', 'N/A') if schemes else 'None'}")
        else:
            print("\n× No schemes scraped")
            print("\nTroubleshooting:")
            print("  1. Check if ChromeDriver is installed")
            print("  2. Verify myScheme.gov.in is accessible")
            print("  3. Try running with headless=False to see browser")
            print("  4. Check website structure hasn't changed")
    
    except Exception as e:
        print(f"\n× Error: {str(e)}")
        print("\nMake sure to install:")
        print("  pip install selenium")
        print("  Download ChromeDriver: https://chromedriver.chromium.org/")


if __name__ == '__main__':
    main()
