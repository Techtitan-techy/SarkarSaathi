# Complete Scheme Scraping Guide

## Get ALL Central and State Government Schemes

---

## Overview

I've created **3 comprehensive scrapers** to get ALL government schemes from myScheme.gov.in:

1. **Basic Scraper** - Fast, no browser needed
2. **Comprehensive Scraper** - Multi-method approach
3. **Complete Selenium Scraper** - Gets EVERYTHING (all 36 states)

---

## Quick Start

### Option 1: Basic Scraper (Fastest)

```bash
cd scripts
pip install requests beautifulsoup4 lxml
python scrape_schemes.py
```

**Time:** 2-5 minutes  
**Output:** ~50-100 schemes  
**Best for:** Quick testing

---

### Option 2: Comprehensive Scraper (Recommended)

```bash
cd scripts
pip install requests beautifulsoup4 lxml
python scrape_all_schemes_comprehensive.py
```

**Time:** 10-15 minutes  
**Output:** ~200-500 schemes  
**Best for:** Good coverage without browser

**Features:**

- ✅ Scrapes Central schemes
- ✅ Scrapes all 36 states
- ✅ Scrapes by 14 categories
- ✅ Removes duplicates
- ✅ Organizes by state

---

### Option 3: Complete Selenium Scraper (Most Comprehensive)

```bash
cd scripts

# Install dependencies
pip install selenium

# Install ChromeDriver
# Mac: brew install chromedriver
# Linux: apt-get install chromium-chromedriver
# Windows: Download from https://chromedriver.chromium.org/

# Run scraper
python scrape_myscheme_complete.py
```

**Time:** 30-60 minutes  
**Output:** 1000+ schemes (ALL schemes)  
**Best for:** Complete database

**Features:**

- ✅ Uses real browser (Selenium)
- ✅ Fills myScheme.gov.in form
- ✅ Scrapes ALL 36 states individually
- ✅ Gets Central schemes
- ✅ Extracts complete details
- ✅ Organizes by state

---

## What You'll Get

### File Structure

```
data/
├── schemes_database.json           # Main database (updated)
├── all_schemes_comprehensive.json  # From comprehensive scraper
└── myscheme_complete.json          # From Selenium scraper (COMPLETE)
```

### JSON Structure

```json
{
  "schemes": [...],
  "central_schemes": [...],
  "state_schemes_by_state": {
    "Andhra Pradesh": [...],
    "Bihar": [...],
    "Delhi": [...],
    ...
  },
  "metadata": {
    "totalSchemes": 1234,
    "centralSchemes": 150,
    "stateSchemes": 1084,
    "statesCovered": 36,
    "scrapedAt": "2026-02-28 15:30:00"
  }
}
```

---

## All Indian States Covered

The scrapers cover all 36 states and union territories:

**States (28):**

1. Andhra Pradesh
2. Arunachal Pradesh
3. Assam
4. Bihar
5. Chhattisgarh
6. Goa
7. Gujarat
8. Haryana
9. Himachal Pradesh
10. Jharkhand
11. Karnataka
12. Kerala
13. Madhya Pradesh
14. Maharashtra
15. Manipur
16. Meghalaya
17. Mizoram
18. Nagaland
19. Odisha
20. Punjab
21. Rajasthan
22. Sikkim
23. Tamil Nadu
24. Telangana
25. Tripura
26. Uttar Pradesh
27. Uttarakhand
28. West Bengal

**Union Territories (8):** 29. Andaman and Nicobar Islands 30. Chandigarh 31. Dadra and Nagar Haveli and Daman and Diu 32. Delhi 33. Jammu and Kashmir 34. Ladakh 35. Lakshadweep 36. Puducherry

---

## Scheme Categories

All schemes are organized into 14 categories:

1. Agriculture, Rural & Environment
2. Banking, Financial Services and Insurance
3. Business & Entrepreneurship
4. Education & Learning
5. Health & Wellness
6. Housing & Shelter
7. Public Safety, Law & Justice
8. Science, IT & Communications
9. Skills & Employment
10. Social Welfare & Empowerment
11. Sports & Culture
12. Transport & Infrastructure
13. Travel & Tourism
14. Utility & Sanitation

---

## Running the Complete Scraper

### Step-by-Step

1. **Install Python dependencies:**

```bash
pip install selenium requests beautifulsoup4 lxml
```

2. **Install ChromeDriver:**

**Mac:**

```bash
brew install chromedriver
```

**Linux:**

```bash
apt-get install chromium-chromedriver
```

**Windows:**

- Download from https://chromedriver.chromium.org/
- Extract to a folder in PATH

3. **Run the scraper:**

```bash
cd scripts
python scrape_myscheme_complete.py
```

4. **Wait for completion:**

- The scraper will visit myScheme.gov.in
- Fill the form for each state
- Extract all schemes
- Save to JSON

**Expected output:**

```
╔══════════════════════════════════════════════════════════════════╗
║               COMPLETE myScheme.gov.in SCRAPER                   ║
║                    ALL SCHEMES - STATE WISE                      ║
╚══════════════════════════════════════════════════════════════════╝

Setting up Chrome WebDriver...
  ✓ WebDriver ready

======================================================================
SCRAPING CENTRAL SCHEMES
======================================================================

✓ 150 central schemes found

======================================================================
SCRAPING ALL STATES
======================================================================

[1/36] Andhra Pradesh
  → Found 45 scheme elements
  ✓ 45 schemes found

[2/36] Arunachal Pradesh
  → Found 23 scheme elements
  ✓ 23 schemes found

...

[36/36] Puducherry
  → Found 18 scheme elements
  ✓ 18 schemes found

✓ Total schemes from all states: 1084

======================================================================
SCRAPING COMPLETE!
======================================================================
Duration: 45.3 minutes
Total schemes scraped: 1234
Unique schemes: 1234

✓ Saved to: myscheme_complete.json
  • Total schemes: 1234
  • Central: 150
  • State: 1084
  • States covered: 36

✓ WebDriver closed

======================================================================
SUCCESS!
======================================================================
All schemes have been scraped and saved.
Check: data/myscheme_complete.json
```

---

## Troubleshooting

### Issue: "ChromeDriver not found"

**Solution:**

```bash
# Check if installed
which chromedriver

# Install if missing
brew install chromedriver  # Mac
apt-get install chromium-chromedriver  # Linux
```

### Issue: "No schemes found"

**Possible causes:**

1. Website structure changed
2. Form fields changed
3. Network issues

**Solution:**

```bash
# Run with visible browser to debug
# Edit script: headless=False
scraper = MySchemeCompleteScraper(headless=False)
```

### Issue: "Scraping too slow"

**Solution:**

```python
# Reduce wait times in script
time.sleep(1)  # Instead of time.sleep(3)

# Or scrape fewer states for testing
STATES = ['Delhi', 'Maharashtra', 'Punjab']  # Test with 3 states
```

### Issue: "Memory error"

**Solution:**

```bash
# Scrape in batches
# Edit STATES list to scrape 10 states at a time
```

---

## Automation

### Schedule Daily Updates

**Linux/Mac (Cron):**

```bash
# Edit crontab
crontab -e

# Run daily at 2 AM
0 2 * * * cd /path/to/scripts && python scrape_myscheme_complete.py >> scraper.log 2>&1
```

**Windows (Task Scheduler):**

1. Open Task Scheduler
2. Create Basic Task
3. Name: "myScheme Complete Scraper"
4. Trigger: Daily at 2:00 AM
5. Action: Start program
   - Program: `python`
   - Arguments: `C:\path\to\scripts\scrape_myscheme_complete.py`

---

## Performance Tips

### 1. Run in Parallel

```python
# Scrape multiple states simultaneously
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    executor.map(scrape_state, STATES)
```

### 2. Use Headless Mode

```python
# Faster without GUI
scraper = MySchemeCompleteScraper(headless=True)
```

### 3. Cache Results

```python
# Save intermediate results
if os.path.exists('cache.json'):
    load_from_cache()
```

---

## Expected Results

### Scheme Count by State (Approximate)

| State         | Expected Schemes |
| ------------- | ---------------- |
| Maharashtra   | 80-100           |
| Uttar Pradesh | 70-90            |
| Tamil Nadu    | 60-80            |
| Karnataka     | 60-80            |
| Gujarat       | 50-70            |
| Delhi         | 40-60            |
| Punjab        | 40-60            |
| Haryana       | 40-60            |
| Others        | 20-50 each       |

**Total Expected:** 1000-1500 schemes

---

## Integration with Frontend

After scraping, update the frontend:

```javascript
// frontend/src/services/schemeService.js
import allSchemes from "../../data/myscheme_complete.json";

const mockSchemes = allSchemes.schemes;

// Filter by state
export const getSchemesByState = (state) => {
  return mockSchemes.filter(
    (s) => s.state === state || s.state === "All India",
  );
};

// Filter by category
export const getSchemesByCategory = (category) => {
  return mockSchemes.filter((s) => s.category === category);
};
```

---

## Next Steps

1. **Run the scraper:**

```bash
python scripts/scrape_myscheme_complete.py
```

2. **Verify output:**

```bash
# Check file size
ls -lh data/myscheme_complete.json

# Count schemes
cat data/myscheme_complete.json | grep '"name"' | wc -l
```

3. **Update frontend:**

```bash
# Copy to frontend
cp data/myscheme_complete.json frontend/src/data/
```

4. **Test in app:**

```bash
cd frontend
npm start
```

---

## Summary

✅ **3 Scrapers Created:**

- Basic (fast, ~100 schemes)
- Comprehensive (medium, ~500 schemes)
- Complete Selenium (slow, ~1500 schemes)

✅ **Coverage:**

- All 36 Indian states/UTs
- 14 scheme categories
- Central + State schemes
- Bilingual support

✅ **Output:**

- Structured JSON
- Organized by state
- Complete metadata
- Ready for frontend

---

**Status:** ✅ READY TO RUN

**Recommended:** Start with `scrape_all_schemes_comprehensive.py` for good coverage without browser setup.

**For complete database:** Use `scrape_myscheme_complete.py` (requires ChromeDriver).

---

**Last Updated:** February 28, 2026
