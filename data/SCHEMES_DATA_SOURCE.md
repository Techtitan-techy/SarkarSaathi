# Government Schemes Data - Sources and Updates

## Overview

SarkariSaathi uses comprehensive, real government scheme data sourced from official portals and verified sources. The scheme database is regularly updated to ensure accuracy.

---

## Data Sources

### Primary Sources

1. **myScheme.gov.in** - Official Government Schemes Portal
   - URL: https://www.myscheme.gov.in/
   - Managed by: Digital India Corporation (DIC), Ministry of Electronics & IT
   - Coverage: 1000+ Central and State schemes

2. **Individual Scheme Portals**
   - PM-KISAN: https://pmkisan.gov.in/
   - Ayushman Bharat: https://pmjay.gov.in/
   - PMAY: https://pmaymis.gov.in/
   - PMAY-Gramin: https://pmayg.nic.in/
   - MUDRA: https://www.mudra.org.in/

3. **Ministry Websites**
   - Ministry of Agriculture & Farmers Welfare
   - Ministry of Health & Family Welfare
   - Ministry of Housing & Urban Affairs
   - Ministry of Rural Development
   - Ministry of Finance

---

## Current Scheme Database (8 Schemes)

### 1. PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)

- **Category**: Agriculture
- **Type**: Central Scheme
- **Benefits**: ₹6,000/year in 3 installments
- **Eligibility**: Small and marginal farmers
- **Source**: https://pmkisan.gov.in/
- **Last Verified**: 2026-02-28

### 2. Ayushman Bharat (PM-JAY)

- **Category**: Healthcare
- **Type**: Central Scheme
- **Benefits**: ₹5 lakh health coverage per family/year
- **Eligibility**: EWS, BPL, Senior Citizens 70+
- **Source**: https://pmjay.gov.in/
- **Last Verified**: 2026-02-28

### 3. PMAY-Urban

- **Category**: Housing
- **Type**: Central Scheme
- **Benefits**: Interest subsidy up to ₹2.67 lakh
- **Eligibility**: EWS, LIG, MIG (income up to ₹18 lakh)
- **Source**: https://pmaymis.gov.in/
- **Last Verified**: 2026-02-28

### 4. Kisan Credit Card (KCC)

- **Category**: Agriculture
- **Type**: Central Scheme
- **Benefits**: 4% interest rate (after subsidy)
- **Eligibility**: Farmers, tenant farmers, sharecroppers
- **Source**: RBI Guidelines 2026
- **Last Verified**: 2026-02-28

### 5. PMAY-Gramin

- **Category**: Housing
- **Type**: Central Scheme
- **Benefits**: ₹1.2-1.3 lakh for house construction
- **Eligibility**: Rural BPL families
- **Source**: https://pmayg.nic.in/
- **Last Verified**: 2026-02-28

### 6. Pradhan Mantri MUDRA Yojana

- **Category**: Employment
- **Type**: Central Scheme
- **Benefits**: Loans up to ₹10 lakh
- **Eligibility**: Small/micro enterprises
- **Source**: https://www.mudra.org.in/
- **Last Verified**: 2026-02-28

### 7. Sukanya Samriddhi Yojana

- **Category**: Women & Child
- **Type**: Central Scheme
- **Benefits**: 8.2% interest rate, tax benefits
- **Eligibility**: Girl child (0-10 years)
- **Source**: India Post
- **Last Verified**: 2026-02-28

### 8. Atal Pension Yojana

- **Category**: Social Security
- **Type**: Central Scheme
- **Benefits**: ₹1,000-5,000/month pension
- **Eligibility**: Unorganized sector workers (18-40 years)
- **Source**: PFRDA
- **Last Verified**: 2026-02-28

---

## Data Collection Methodology

### Manual Curation (Current)

- Research from official government portals
- Verification from multiple sources
- Cross-reference with myScheme.gov.in
- Regular updates based on government announcements

### Automated Scraping (Future)

A Python script (`scripts/scrape_schemes.py`) is provided for automated data collection:

```bash
cd scripts
python scrape_schemes.py
```

**Features:**

- Scrapes myScheme.gov.in API
- Fetches individual scheme details
- Updates JSON database
- Validates data integrity

---

## Data Structure

Each scheme contains:

```json
{
  "id": "unique-scheme-id",
  "name": "Scheme Name (English)",
  "nameHi": "योजना का नाम (हिंदी)",
  "category": "Agriculture|Healthcare|Housing|Employment|Women & Child|Social Security",
  "type": "Central|State",
  "ministry": "Responsible Ministry",
  "description": "Detailed description",
  "descriptionHi": "विस्तृत विवरण",
  "benefits": ["Benefit 1", "Benefit 2"],
  "benefitsHi": ["लाभ 1", "लाभ 2"],
  "eligibility": {
    "minAge": 18,
    "maxAge": 100,
    "minIncome": 0,
    "maxIncome": 500000,
    "states": ["all"],
    "occupation": ["farmer"],
    "categories": ["EWS", "BPL"]
  },
  "documents": ["Aadhaar", "Bank Account"],
  "officialWebsite": "https://scheme-url.gov.in/",
  "lastUpdated": "2026-02-28"
}
```

---

## Update Schedule

### Regular Updates

- **Weekly**: Check for new scheme announcements
- **Monthly**: Verify eligibility criteria changes
- **Quarterly**: Full database audit

### Immediate Updates

- New scheme launches
- Major policy changes
- Eligibility criteria modifications
- Benefit amount revisions

---

## How to Add New Schemes

### Manual Addition

1. Research the scheme from official sources
2. Collect all required information
3. Add to `data/schemes_database.json`
4. Update `frontend/src/services/schemeService.js`
5. Test eligibility matching logic

### Automated Addition

1. Update `scripts/scrape_schemes.py` with new source
2. Run the scraper
3. Review and validate new data
4. Deploy updated database

---

## State-Specific Schemes (Future Enhancement)

Currently focusing on Central schemes. State schemes will be added in phases:

**Priority States:**

1. Punjab - Agriculture schemes
2. Maharashtra - Employment schemes
3. Uttar Pradesh - Housing schemes
4. Bihar - Social welfare schemes
5. Rajasthan - Women empowerment schemes

---

## Data Accuracy and Disclaimer

### Verification Process

- All data sourced from official government portals
- Cross-verified with multiple sources
- Regular updates based on official announcements
- User feedback incorporated for corrections

### Disclaimer

While we strive for accuracy, users should:

- Verify eligibility from official websites
- Check current benefit amounts
- Confirm application procedures
- Contact scheme authorities for final confirmation

---

## API Integration (Future)

### myScheme.gov.in API

- Endpoint discovery in progress
- Authentication requirements being analyzed
- Real-time scheme data integration planned

### Government Data APIs

- Exploring APIs from various ministries
- Integration with DigiLocker for document verification
- Aadhaar-based eligibility checking

---

## Contributing

### Report Inaccuracies

If you find any incorrect information:

1. Email: support@sarkarisaathi.in
2. Provide scheme name and incorrect detail
3. Include official source link

### Suggest New Schemes

To suggest adding a new scheme:

1. Provide official scheme URL
2. Share eligibility criteria
3. Include benefit details

---

## Technical Implementation

### Frontend

- **File**: `frontend/src/services/schemeService.js`
- **Format**: JavaScript array of scheme objects
- **Features**: Eligibility matching, language detection, response generation

### Backend (Future)

- **File**: `lambda/scheme_handler.py`
- **Database**: DynamoDB for scalable storage
- **Search**: Amazon OpenSearch for semantic search

### Data Storage

- **Current**: JSON file (`data/schemes_database.json`)
- **Future**: DynamoDB + OpenSearch

---

## References

1. myScheme Portal: https://www.myscheme.gov.in/
2. Digital India: https://www.digitalindia.gov.in/
3. PM-KISAN: https://pmkisan.gov.in/
4. Ayushman Bharat: https://pmjay.gov.in/
5. PMAY: https://pmaymis.gov.in/
6. RBI KCC Guidelines: https://www.rbi.org.in/

---

**Last Updated**: February 28, 2026

**Data Version**: 1.0

**Total Schemes**: 8 Central Schemes

**Next Update**: March 7, 2026
