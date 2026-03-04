# Government Scheme Data Collection Scripts

## Overview

Scripts to collect 1000+ government schemes from various official sources.

## Data Sources

### 1. data.gov.in (Official Open Data Platform)

- **Coverage**: 4,510+ schemes
- **Format**: JSON via API
- **Requires**: API Key (free registration)
- **Script**: `data_gov_scraper.py`

### 2. Web Scraping

- **Sources**: Wikipedia, official portals
- **Coverage**: 200+ verified schemes
- **Format**: HTML parsing
- **Script**: `web_scraper.py`

### 3. Manual Curation

- **Coverage**: Top 100 popular schemes
- **Quality**: Highest (manually verified)
- **Format**: JSON
- **File**: Included in `web_scraper.py`

## Setup

### Prerequisites

```bash
# Install Python 3.9+
python --version

# Install dependencies
pip install requests beautifulsoup4 lxml
```

### Get API Key (for data.gov.in)

1. Visit https://data.gov.in
2. Click "Register" → Create account
3. Go to "API" section → Request API access
4. Copy your 32-character API key
5. Set environment variable:

```bash
export DATA_GOV_IN_API_KEY='your-api-key-here'
```

## Usage

### Method 1: Collect from data.gov.in

```bash
cd scripts/data_collection
python data_gov_scraper.py
```

**Output**: `data/raw/data_gov_schemes_*.json`

### Method 2: Web Scraping

```bash
cd scripts/data_collection
python web_scraper.py
```

**Output**: `data/raw/web_scraped_schemes_*.json`

### Method 3: Run All

```bash
# Collect from all sources
python data_gov_scraper.py
python web_scraper.py

# Check results
ls -lh data/raw/
```

## Output Format

### Raw Data Structure

```json
{
  "source": "data.gov.in",
  "fetched_at": "2026-03-01T10:30:00",
  "total_schemes": 1500,
  "schemes": [
    {
      "name": "Scheme Name",
      "description": "Description",
      "ministry": "Ministry Name",
      "category": "Category",
      "type": "Central",
      "state": "All India",
      "eligibility": {...},
      "benefits": [...],
      "documents": [...],
      "website": "https://...",
      "helpline": "1800-xxx-xxx"
    }
  ]
}
```

## Data Processing Pipeline

### Step 1: Collection (This Script)

```
data.gov.in API → data/raw/data_gov_schemes_*.json
Web Scraping → data/raw/web_scraped_schemes_*.json
```

### Step 2: Cleaning (Next Script)

```
data/raw/*.json → data/cleaned/schemes_cleaned.json
- Remove duplicates
- Standardize fields
- Validate data
```

### Step 3: Enrichment (Next Script)

```
data/cleaned/*.json → data/enriched/schemes_enriched.json
- Add Hindi translations
- Add application process
- Add required documents
```

### Step 4: Database Import (Next Script)

```
data/enriched/*.json → PostgreSQL/MongoDB
- Import to database
- Create indexes
- Generate embeddings
```

## Expected Results

### Target Numbers

- **Total Schemes**: 1,000+
- **Central Schemes**: 400+
- **State Schemes**: 600+
- **Categories**: 10+
- **States Covered**: 29

### Data Quality

- **Completeness**: 95%+ fields populated
- **Accuracy**: Verified from official sources
- **Freshness**: Updated monthly
- **Multilingual**: English + Hindi

## Troubleshooting

### Issue: API Key Not Working

```bash
# Check if API key is set
echo $DATA_GOV_IN_API_KEY

# Test API key
curl "https://api.data.gov.in/resource?api-key=YOUR_KEY&format=json&limit=1"
```

### Issue: Rate Limiting

- Scripts include 1-second delays between requests
- If blocked, wait 5 minutes and retry
- Consider running during off-peak hours

### Issue: Network Errors

- Check internet connection
- Verify URLs are accessible
- Try with VPN if blocked

### Issue: No Data Returned

- Verify API key is valid
- Check if source website is up
- Review error messages in console

## Data Quality Checks

### Automated Checks

```python
# Check for required fields
required_fields = ['name', 'description', 'category', 'type']

# Check for duplicates
unique_schemes = len(set([s['name'] for s in schemes]))

# Check data completeness
completeness = sum([1 for s in schemes if all(s.get(f) for f in required_fields)]) / len(schemes)
```

### Manual Verification

1. Review first 10 schemes
2. Check official websites
3. Verify eligibility criteria
4. Confirm contact information

## Next Steps

After collecting raw data:

1. **Clean Data**

   ```bash
   python scripts/data_processing/clean_data.py
   ```

2. **Enrich Data**

   ```bash
   python scripts/data_processing/enrich_data.py
   ```

3. **Import to Database**

   ```bash
   python scripts/database/import_schemes.py
   ```

4. **Generate Embeddings**
   ```bash
   python scripts/ml/generate_embeddings.py
   ```

## Contributing

### Adding New Sources

1. Create new scraper class in `web_scraper.py`
2. Implement `scrape_*` method
3. Add to `main()` function
4. Test with small dataset first

### Improving Data Quality

1. Add validation rules
2. Enhance error handling
3. Add retry logic
4. Improve documentation

## Resources

### Official Sources

- data.gov.in: https://data.gov.in
- myScheme.gov.in: https://www.myscheme.gov.in
- Digital India: https://digitalindia.gov.in

### Documentation

- data.gov.in API Docs: https://data.gov.in/help/api
- Python Requests: https://requests.readthedocs.io
- BeautifulSoup: https://www.crummy.com/software/BeautifulSoup/

### Support

- Email: support-myscheme@digitalindia.gov.in
- Phone: (011) 24303714
- Hours: 9:00 AM to 5:30 PM IST

## License

Data collected from public government sources.

- Proper attribution required
- For non-commercial use
- Verify with official sources before use

## Changelog

### v1.0.0 (2026-03-01)

- Initial release
- data.gov.in API scraper
- Web scraping for Wikipedia
- Popular schemes curated list
- Basic error handling
- JSON output format

---

**Status**: Ready to use
**Tested**: Python 3.9+
**Platform**: Cross-platform (Windows, Linux, macOS)
