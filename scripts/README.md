# Government Scheme Data Scraping Scripts

This directory contains scripts to scrape government scheme data from official sources.

---

## Available Scripts

### 1. `scrape_schemes.py` - Basic Scraper

**Best for**: Static websites, API endpoints, simple HTML pages

**Features**:

- Scrapes myScheme.gov.in (attempts API first, falls back to HTML)
- Scrapes PM-KISAN portal
- Scrapes Ayushman Bharat portal
- Scrapes Wikipedia schemes list
- Merges with existing database
- No browser required

**Usage**:

```bash
# Install dependencies
pip install -r requirements.txt

# Run scraper
python scrape_schemes.py
```

**Output**: Updates `../data/schemes_database.json`

---

### 2. `scrape_schemes_advanced.py` - Selenium Scraper

**Best for**: JavaScript-heavy sites, dynamic content, SPAs

**Features**:

- Uses Selenium WebDriver (Chrome)
- Handles JavaScript rendering
- Scrolls to load more content
- Scrapes individual scheme detail pages
- Extracts benefits, eligibility, descriptions
- Can run headless or with visible browser

**Usage**:

```bash
# Install dependencies
pip install selenium

# Download ChromeDriver
# Visit: https://chromedriver.chromium.org/
# Or use: brew install chromedriver (Mac)
# Or use: apt-get install chromium-chromedriver (Linux)

# Run scraper
python scrape_schemes_advanced.py
```

**Output**: Creates `../data/schemes_selenium.json`

---

## Installation

### Basic Scraper Dependencies

```bash
pip install requests beautifulsoup4 lxml
```

### Advanced Scraper Dependencies

```bash
pip install selenium

# Install ChromeDriver
# Windows: Download from https://chromedriver.chromium.org/
# Mac: brew install chromedriver
# Linux: apt-get install chromium-chromedriver
```

### All Dependencies

```bash
pip install -r requirements.txt
```

---

## Data Sources

### Primary Sources

1. **myScheme.gov.in** - Official government schemes portal
   - 1000+ Central and State schemes
   - Managed by Digital India Corporation

2. **Individual Scheme Portals**
   - PM-KISAN: https://pmkisan.gov.in/
   - Ayushman Bharat: https://pmjay.gov.in/
   - PMAY: https://pmaymis.gov.in/

3. **Wikipedia**
   - Comprehensive list of Indian government schemes
   - Good for scheme names and basic info

---

## Scraping Strategy

### Method 1: API Endpoints (Fastest)

```python
# Try official APIs first
api_urls = [
    'https://www.myscheme.gov.in/api/schemes',
    'https://api.myscheme.gov.in/schemes',
]
```

### Method 2: HTML Scraping (Reliable)

```python
# Parse HTML with BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')
schemes = soup.find_all('div', class_='scheme-card')
```

### Method 3: Selenium (Most Comprehensive)

```python
# Use Selenium for JavaScript sites
driver = webdriver.Chrome()
driver.get('https://www.myscheme.gov.in/')
schemes = driver.find_elements(By.CSS_SELECTOR, '.scheme')
```

---

## Output Format

### JSON Structure

```json
{
  "schemes": [
    {
      "id": "pm-kisan",
      "name": "PM-KISAN",
      "nameHi": "प्रधानमंत्री किसान सम्मान निधि",
      "category": "Agriculture",
      "type": "Central",
      "ministry": "Ministry of Agriculture",
      "description": "Direct income support...",
      "descriptionHi": "प्रत्यक्ष आय सहायता...",
      "benefits": ["₹6,000 per year", "Direct transfer"],
      "benefitsHi": ["प्रति वर्ष ₹6,000", "सीधे हस्तांतरण"],
      "eligibility": {
        "minAge": 18,
        "maxAge": 100,
        "minIncome": 0,
        "maxIncome": 500000,
        "states": ["all"],
        "occupation": ["farmer"]
      },
      "documents": ["Aadhaar", "Bank Account"],
      "officialWebsite": "https://pmkisan.gov.in/",
      "lastUpdated": "2026-02-28"
    }
  ],
  "metadata": {
    "totalSchemes": 100,
    "lastUpdated": "2026-02-28 10:30:00",
    "source": "myScheme.gov.in, Official Portals",
    "categories": ["Agriculture", "Healthcare", "Housing"],
    "dataCollectionMethod": "Automated web scraping"
  }
}
```

---

## Scheduling Automated Updates

### Using Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Run daily at 2 AM
0 2 * * * cd /path/to/scripts && python scrape_schemes.py

# Run weekly on Sunday at 3 AM
0 3 * * 0 cd /path/to/scripts && python scrape_schemes_advanced.py
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily/weekly)
4. Action: Start a program
5. Program: `python`
6. Arguments: `C:\path\to\scripts\scrape_schemes.py`

### Using Python Schedule

```python
import schedule
import time

def job():
    os.system('python scrape_schemes.py')

schedule.every().day.at("02:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## Rate Limiting & Best Practices

### Respectful Scraping

```python
import time

# Add delays between requests
time.sleep(1)  # 1 second delay

# Use exponential backoff for retries
for attempt in range(3):
    try:
        response = requests.get(url)
        break
    except:
        time.sleep(2 ** attempt)
```

### User-Agent Rotation

```python
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...',
    'Mozilla/5.0 (X11; Linux x86_64)...'
]

headers = {'User-Agent': random.choice(USER_AGENTS)}
```

### Error Handling

```python
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
except requests.Timeout:
    print("Request timed out")
except requests.HTTPError as e:
    print(f"HTTP error: {e}")
except Exception as e:
    print(f"Error: {e}")
```

---

## Troubleshooting

### Issue: "ChromeDriver not found"

**Solution**:

```bash
# Mac
brew install chromedriver

# Linux
apt-get install chromium-chromedriver

# Windows
# Download from https://chromedriver.chromium.org/
# Add to PATH
```

### Issue: "Connection timeout"

**Solution**:

- Check internet connection
- Increase timeout: `requests.get(url, timeout=30)`
- Use VPN if site is geo-blocked

### Issue: "No schemes found"

**Solution**:

- Website structure may have changed
- Inspect website and update CSS selectors
- Try Selenium scraper for JavaScript sites
- Check if website requires authentication

### Issue: "Rate limited / Blocked"

**Solution**:

- Add delays: `time.sleep(2)`
- Rotate User-Agents
- Use proxies
- Respect robots.txt

---

## Advanced Features

### Proxy Support

```python
proxies = {
    'http': 'http://proxy.example.com:8080',
    'https': 'https://proxy.example.com:8080',
}

response = requests.get(url, proxies=proxies)
```

### Concurrent Scraping

```python
from concurrent.futures import ThreadPoolExecutor

def scrape_url(url):
    # Scraping logic
    pass

urls = ['url1', 'url2', 'url3']

with ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(scrape_url, urls)
```

### Data Validation

```python
def validate_scheme(scheme):
    required_fields = ['id', 'name', 'category']
    return all(field in scheme for field in required_fields)

valid_schemes = [s for s in schemes if validate_scheme(s)]
```

---

## Legal & Ethical Considerations

### robots.txt

Always check and respect robots.txt:

```bash
curl https://www.myscheme.gov.in/robots.txt
```

### Terms of Service

- Read website's Terms of Service
- Don't overload servers
- Use data responsibly
- Attribute sources properly

### Data Privacy

- Don't scrape personal information
- Follow GDPR/data protection laws
- Anonymize sensitive data

---

## Performance Optimization

### Caching

```python
import requests_cache

# Cache responses for 1 hour
requests_cache.install_cache('scheme_cache', expire_after=3600)
```

### Async Requests

```python
import aiohttp
import asyncio

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
```

---

## Monitoring & Logging

### Setup Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("Scraping started")
```

### Track Metrics

```python
metrics = {
    'total_requests': 0,
    'successful_scrapes': 0,
    'failed_scrapes': 0,
    'schemes_found': 0,
    'duration': 0
}
```

---

## Contributing

To add a new data source:

1. Create scraping function:

```python
def scrape_new_source():
    # Scraping logic
    return schemes
```

2. Add to main scraper:

```python
new_schemes = scrape_new_source()
all_schemes.extend(new_schemes)
```

3. Update documentation

---

## Support

For issues or questions:

- Check troubleshooting section
- Review website structure
- Test with headless=False to see browser
- Check logs for error messages

---

**Last Updated**: February 28, 2026
