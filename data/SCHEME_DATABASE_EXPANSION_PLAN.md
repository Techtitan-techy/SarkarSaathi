# Scheme Database Expansion Plan - 1000+ Schemes

## Executive Summary

Plan to expand SarkariSaathi database from 10 schemes to 1000+ schemes using official government sources and structured data collection.

## Data Sources Identified

### Primary Sources (Official Government)

1. **myScheme.gov.in** (Official Government Portal)
   - URL: https://www.myscheme.gov.in
   - Coverage: Central and State schemes
   - Features: Eligibility checker, scheme search
   - API: Available (requires registration)
   - Contact: support-myscheme@digitalindia.gov.in
   - Phone: (011) 24303714

2. **data.gov.in** (Open Government Data Platform)
   - URL: https://data.gov.in
   - Coverage: 4,510+ government schemes
   - Format: CSV, JSON, XML, API
   - API Key: Required (32-character hexadecimal)
   - Python Package: `datagovindia` (PyPI)
   - GitHub: https://github.com/addypy/datagovindia

3. **ProjectSarthi.com**
   - URL: https://projectsarthi.com
   - Coverage: 4,584+ Central & State schemes
   - Features: Smart eligibility filters
   - Categories: By state, ministry, category

4. **Digital India Corporation (DIC)**
   - URL: https://dic.gov.in/my-scheme/
   - Official government initiative
   - Comprehensive scheme marketplace

### Secondary Sources (Aggregators)

5. **Wikipedia - List of Government Schemes**
   - URL: https://en.wikipedia.org/wiki/List_of_schemes_of_the_government_of_India
   - Coverage: 157 CS and CSS schemes (₹500 crore+ each)
   - Well-structured, verified data

6. **State Government Portals**
   - Maharashtra: https://www.maharashtra.gov.in
   - Karnataka: https://www.karnataka.gov.in
   - Tamil Nadu: https://www.tn.gov.in
   - Gujarat: https://www.gujarat.gov.in
   - Uttar Pradesh: https://www.up.gov.in
   - (All 29 states + 8 UTs)

## Scheme Categories to Cover

### Central Schemes (Target: 400+)

1. Agriculture & Farmers Welfare (50+)
2. Healthcare & Medical (60+)
3. Housing & Urban Development (40+)
4. Education & Skill Development (80+)
5. Employment & Entrepreneurship (50+)
6. Women & Child Development (40+)
7. Social Security & Pensions (30+)
8. Financial Inclusion & Banking (25+)
9. Rural Development (35+)
10. Energy & Environment (30+)

### State Schemes (Target: 600+)

- 29 States × ~20 schemes each = 580 schemes
- 8 Union Territories × ~3 schemes each = 24 schemes

## Data Structure Required

### Minimum Fields (Per Scheme)

```json
{
  "schemeId": "unique-id",
  "name": {
    "en": "English Name",
    "hi": "हिंदी नाम",
    "regional": "Regional Language Name"
  },
  "description": {
    "en": "English Description",
    "hi": "हिंदी विवरण",
    "regional": "Regional Description"
  },
  "category": "Category Name",
  "type": "Central" | "State",
  "state": "State Name" | "All India",
  "ministry": "Ministry/Department Name",
  "launchingAuthority": "Authority Name",
  "launchedDate": "YYYY-MM-DD",
  "eligibilityCriteria": {
    "ageRange": { "min": 0, "max": 999 },
    "incomeRange": { "min": 0, "max": 999999999 },
    "allowedStates": ["state1", "state2"],
    "allowedCategories": ["General", "OBC", "SC", "ST"],
    "requiredOccupations": ["occupation1"],
    "excludedOccupations": ["occupation2"],
    "gender": "All" | "Male" | "Female" | "Transgender",
    "additionalCriteria": "Text description"
  },
  "benefits": {
    "en": ["Benefit 1", "Benefit 2"],
    "hi": ["लाभ 1", "लाभ 2"]
  },
  "financialBenefit": {
    "amount": 6000,
    "frequency": "Annual" | "Monthly" | "One-time",
    "currency": "INR"
  },
  "applicationProcess": {
    "en": "Process description",
    "hi": "प्रक्रिया विवरण",
    "steps": ["Step 1", "Step 2", "Step 3"],
    "onlineUrl": "https://...",
    "offlineProcess": "Visit CSC/Office"
  },
  "requiredDocuments": [
    "Aadhaar Card",
    "Bank Account Details",
    "Income Certificate"
  ],
  "deadlines": ["Date 1", "Date 2"],
  "contactInfo": {
    "officialWebsite": "https://...",
    "helpline": "1800-xxx-xxx",
    "email": "support@...",
    "address": "Office address"
  },
  "tags": ["tag1", "tag2"],
  "lastUpdated": "2026-03-01"
}
```

## Implementation Strategy

### Phase 1: Data Collection (Week 1-2)

#### Step 1.1: Register for API Access

- [ ] Register at data.gov.in for API key
- [ ] Register at myScheme.gov.in for API access
- [ ] Document API endpoints and rate limits

#### Step 1.2: Automated Data Collection

Create Python scripts to:

```python
# Script 1: data.gov.in API scraper
# Script 2: myScheme.gov.in scraper
# Script 3: State portal scrapers
# Script 4: Wikipedia structured data extractor
```

#### Step 1.3: Manual Data Collection

- Research top 100 most popular schemes
- Verify data from official sources
- Add missing fields (documents, process, etc.)

### Phase 2: Data Cleaning & Standardization (Week 2-3)

#### Step 2.1: Data Validation

- Remove duplicates
- Standardize field names
- Validate eligibility criteria
- Check for missing required fields

#### Step 2.2: Translation

- Translate to Hindi using Google Translate API
- Manual verification of key schemes
- Add regional language support (Tamil, Telugu, Bengali)

#### Step 2.3: Enrichment

- Add application process details
- Add required documents
- Add helpline numbers
- Add official website links

### Phase 3: Database Integration (Week 3-4)

#### Step 3.1: Database Schema

- Design PostgreSQL/MongoDB schema
- Create indexes for fast search
- Set up full-text search
- Configure vector embeddings for semantic search

#### Step 3.2: Data Import

- Import cleaned data
- Generate embeddings using AWS Titan
- Index in OpenSearch
- Seed DynamoDB tables

#### Step 3.3: API Development

- Create REST API endpoints
- Implement filtering (state, category, eligibility)
- Add pagination
- Add caching layer

### Phase 4: Testing & Validation (Week 4)

#### Step 4.1: Data Quality Checks

- Verify 100 random schemes manually
- Check eligibility logic
- Test search functionality
- Validate multilingual content

#### Step 4.2: User Testing

- Test with real user profiles
- Verify scheme matching accuracy
- Check application process clarity
- Gather feedback

## Data Collection Scripts

### Script 1: data.gov.in API Client

```python
# data_gov_scraper.py
import requests
import json
import time

class DataGovIndia:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.data.gov.in/resource"

    def search_schemes(self, query, limit=100):
        """Search for government schemes"""
        params = {
            'api-key': self.api_key,
            'format': 'json',
            'filters[title]': query,
            'limit': limit
        }
        response = requests.get(self.base_url, params=params)
        return response.json()

    def get_all_schemes(self):
        """Get all government schemes"""
        schemes = []
        offset = 0
        limit = 100

        while True:
            params = {
                'api-key': self.api_key,
                'format': 'json',
                'offset': offset,
                'limit': limit
            }
            response = requests.get(self.base_url, params=params)
            data = response.json()

            if not data.get('records'):
                break

            schemes.extend(data['records'])
            offset += limit
            time.sleep(1)  # Rate limiting

        return schemes

# Usage
api_key = "YOUR_API_KEY_HERE"
client = DataGovIndia(api_key)
schemes = client.get_all_schemes()
```

### Script 2: Web Scraper for myScheme.gov.in

```python
# myscheme_scraper.py
import requests
from bs4 import BeautifulSoup
import json

class MySchemeScr aper:
    def __init__(self):
        self.base_url = "https://www.myscheme.gov.in"
        self.session = requests.Session()

    def get_scheme_categories(self):
        """Get all scheme categories"""
        url = f"{self.base_url}/search/ministry/all-ministries"
        response = self.session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        # Parse categories
        return categories

    def get_schemes_by_category(self, category):
        """Get schemes for a specific category"""
        # Implementation
        pass

    def get_scheme_details(self, scheme_id):
        """Get detailed information for a scheme"""
        # Implementation
        pass
```

### Script 3: State Portal Scraper

```python
# state_schemes_scraper.py
import requests
from bs4 import BeautifulSoup

class StateSchemesScraper:
    def __init__(self, state_name):
        self.state_name = state_name
        self.state_urls = {
            'Maharashtra': 'https://www.maharashtra.gov.in/schemes',
            'Karnataka': 'https://www.karnataka.gov.in/schemes',
            # Add all states
        }

    def scrape_state_schemes(self):
        """Scrape schemes from state portal"""
        url = self.state_urls.get(self.state_name)
        if not url:
            return []

        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        # Parse schemes
        return schemes
```

## Data Sources Summary

| Source          | Schemes     | Format   | API     | Cost |
| --------------- | ----------- | -------- | ------- | ---- |
| data.gov.in     | 4,510+      | JSON/CSV | Yes     | Free |
| myScheme.gov.in | 1,000+      | HTML/API | Yes     | Free |
| ProjectSarthi   | 4,584+      | HTML     | No      | Free |
| Wikipedia       | 157+        | HTML     | No      | Free |
| State Portals   | 600+        | HTML     | Varies  | Free |
| **Total**       | **10,000+** | Mixed    | Partial | Free |

## Timeline

### Week 1: Setup & Initial Collection

- Day 1-2: Register for APIs, set up environment
- Day 3-4: Develop scraping scripts
- Day 5-7: Collect data from primary sources

### Week 2: Data Processing

- Day 8-10: Clean and standardize data
- Day 11-12: Translate to Hindi
- Day 13-14: Enrich with additional details

### Week 3: Database Integration

- Day 15-17: Set up database schema
- Day 18-19: Import data and create indexes
- Day 20-21: Develop API endpoints

### Week 4: Testing & Launch

- Day 22-24: Quality assurance testing
- Day 25-26: User acceptance testing
- Day 27-28: Deploy and monitor

## Quality Assurance

### Data Validation Checklist

- [ ] All required fields present
- [ ] Eligibility criteria logical
- [ ] Contact information verified
- [ ] Official website accessible
- [ ] Application process clear
- [ ] Documents list complete
- [ ] Hindi translation accurate
- [ ] No duplicate schemes
- [ ] Dates in correct format
- [ ] Financial amounts verified

### Testing Checklist

- [ ] Search by category works
- [ ] Filter by state works
- [ ] Eligibility matching accurate
- [ ] Multilingual display correct
- [ ] Application links functional
- [ ] Helpline numbers valid
- [ ] Performance acceptable (<2s response)
- [ ] Mobile responsive

## Success Metrics

### Quantitative

- 1,000+ schemes in database
- 29 states covered
- 10+ categories
- 95%+ data completeness
- <2s search response time
- 99.9% API uptime

### Qualitative

- Accurate eligibility matching
- Clear application process
- User-friendly interface
- Reliable data sources
- Regular updates

## Maintenance Plan

### Monthly Updates

- Check for new schemes
- Update eligibility criteria
- Verify contact information
- Add new state schemes
- Update financial benefits

### Quarterly Reviews

- Audit data quality
- User feedback analysis
- Performance optimization
- Feature enhancements

## Legal & Compliance

### Data Usage

- All data from public government sources
- Proper attribution to sources
- No copyrighted content
- Compliance with data.gov.in terms
- Privacy policy for user data

### Disclaimers

- Information for reference only
- Verify with official sources
- Not a government website
- No guarantee of accuracy
- Users responsible for verification

## Next Steps

1. **Immediate (This Week)**
   - Register for data.gov.in API key
   - Set up Python environment
   - Create initial scraping scripts
   - Collect first 100 schemes

2. **Short-term (Next 2 Weeks)**
   - Automate data collection
   - Build cleaning pipeline
   - Create database schema
   - Import first 500 schemes

3. **Medium-term (Next Month)**
   - Reach 1,000+ schemes
   - Complete Hindi translations
   - Deploy API endpoints
   - Launch beta version

## Resources Required

### Technical

- Python 3.9+
- PostgreSQL/MongoDB
- AWS OpenSearch
- AWS Lambda
- AWS S3
- Redis (caching)

### Human

- 1 Data Engineer (scraping, cleaning)
- 1 Backend Developer (API, database)
- 1 Translator (Hindi verification)
- 1 QA Tester (validation)

### Budget

- API costs: $0 (free tier)
- AWS costs: ~$50/month
- Translation API: ~$20/month
- Total: ~$70/month

---

**Status**: Ready to implement
**Priority**: High
**Estimated Completion**: 4 weeks
**Risk Level**: Low (all sources are public)
