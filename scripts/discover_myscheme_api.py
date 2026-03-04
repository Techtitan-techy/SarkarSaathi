"""
Discover myScheme.gov.in API Endpoints
Uses Selenium to capture network requests and find the real API
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

def discover_api_endpoints():
    """Discover API endpoints by monitoring network traffic"""
    
    print("=" * 70)
    print("DISCOVERING myScheme.gov.in API ENDPOINTS")
    print("=" * 70)
    print()
    
    # Setup Chrome with network logging
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("1. Loading myScheme.gov.in...")
        driver.get('https://www.myscheme.gov.in/')
        time.sleep(5)
        
        print("2. Capturing network requests...")
        
        # Get performance logs
        logs = driver.get_log('performance')
        
        api_endpoints = []
        
        for log in logs:
            try:
                message = json.loads(log['message'])
                method = message.get('message', {}).get('method', '')
                
                if method == 'Network.responseReceived':
                    response = message['message']['params']['response']
                    url = response.get('url', '')
                    
                    # Look for API calls
                    if any(keyword in url.lower() for keyword in ['api', 'scheme', 'search', 'data', 'json']):
                        if url not in api_endpoints:
                            api_endpoints.append(url)
                            print(f"  ✓ Found: {url}")
                            
            except:
                continue
        
        print(f"\n3. Navigating to find-scheme page...")
        driver.get('https://www.myscheme.gov.in/find-scheme')
        time.sleep(5)
        
        # Get more logs
        logs = driver.get_log('performance')
        
        for log in logs:
            try:
                message = json.loads(log['message'])
                method = message.get('message', {}).get('method', '')
                
                if method == 'Network.responseReceived':
                    response = message['message']['params']['response']
                    url = response.get('url', '')
                    
                    if any(keyword in url.lower() for keyword in ['api', 'scheme', 'search', 'data', 'json']):
                        if url not in api_endpoints:
                            api_endpoints.append(url)
                            print(f"  ✓ Found: {url}")
                            
            except:
                continue
        
        print("\n" + "=" * 70)
        print("DISCOVERED API ENDPOINTS")
        print("=" * 70)
        
        if api_endpoints:
            for i, endpoint in enumerate(api_endpoints, 1):
                print(f"{i}. {endpoint}")
        else:
            print("× No API endpoints found")
            print("\nTrying alternative method...")
            
            # Try to find API calls in page source
            page_source = driver.page_source
            
            # Look for common API patterns
            import re
            api_patterns = [
                r'https?://[^"\']+/api/[^"\']+',
                r'https?://api\.[^"\']+',
                r'/api/v\d+/[^"\']+',
            ]
            
            found_apis = set()
            for pattern in api_patterns:
                matches = re.findall(pattern, page_source)
                found_apis.update(matches)
            
            if found_apis:
                print("\nFound in page source:")
                for api in found_apis:
                    print(f"  • {api}")
        
        # Save to file
        with open('discovered_apis.json', 'w') as f:
            json.dump({
                'endpoints': api_endpoints,
                'discovered_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=2)
        
        print(f"\n✓ Saved to: discovered_apis.json")
        
    finally:
        driver.quit()
        print("\n✓ Browser closed")

if __name__ == '__main__':
    discover_api_endpoints()
