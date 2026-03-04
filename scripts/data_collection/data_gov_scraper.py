#!/usr/bin/env python3
"""
Data.gov.in API Scraper for Government Schemes
Collects government scheme data from India's Open Government Data Platform
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Optional

class DataGovIndiaScraper:
    """Scraper for data.gov.in API"""
    
    def __init__(self, api_key: str):
        """
        Initialize scraper with API key
        
        Args:
            api_key: 32-character hexadecimal API key from data.gov.in
        """
        self.api_key = api_key
        self.base_url = "https://api.data.gov.in/resource"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SarkariSaathi/1.0 (Government Scheme Navigator)'
        })
    
    def search_datasets(self, query: str, limit: int = 100) -> List[Dict]:
        """
        Search for datasets matching query
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of dataset records
        """
        params = {
            'api-key': self.api_key,
            'format': 'json',
            'filters[title]': query,
            'limit': limit
        }
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('records', [])
        except requests.exceptions.RequestException as e:
            print(f"Error searching datasets: {e}")
            return []
    
    def get_all_schemes(self, max_records: int = 5000) -> List[Dict]:
        """
        Get all government scheme datasets
        
        Args:
            max_records: Maximum number of records to fetch
            
        Returns:
            List of all scheme records
        """
        schemes = []
        offset = 0
        limit = 100
        
        print(f"Fetching schemes from data.gov.in...")
        
        while len(schemes) < max_records:
            params = {
                'api-key': self.api_key,
                'format': 'json',
                'offset': offset,
                'limit': limit,
                'filters[sector]': 'Social Welfare'  # Focus on welfare schemes
            }
            
            try:
                response = self.session.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                records = data.get('records', [])
                if not records:
                    print(f"No more records found. Total: {len(schemes)}")
                    break
                
                schemes.extend(records)
                print(f"Fetched {len(schemes)} schemes so far...")
                
                offset += limit
                time.sleep(1)  # Rate limiting - be respectful
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching schemes at offset {offset}: {e}")
                break
        
        return schemes[:max_records]
    
    def search_scheme_keywords(self) -> List[Dict]:
        """
        Search for schemes using common keywords
        
        Returns:
            Combined list of schemes from all keyword searches
        """
        keywords = [
            'scheme', 'yojana', 'pension', 'subsidy', 'welfare',
            'benefit', 'assistance', 'support', 'grant', 'loan',
            'insurance', 'health', 'education', 'housing', 'agriculture'
        ]
        
        all_schemes = []
        seen_ids = set()
        
        for keyword in keywords:
            print(f"Searching for keyword: {keyword}")
            results = self.search_datasets(keyword, limit=100)
            
            for record in results:
                record_id = record.get('id') or record.get('title')
                if record_id and record_id not in seen_ids:
                    all_schemes.append(record)
                    seen_ids.add(record_id)
            
            time.sleep(1)  # Rate limiting
        
        print(f"Total unique schemes found: {len(all_schemes)}")
        return all_schemes
    
    def save_to_json(self, schemes: List[Dict], filename: str):
        """
        Save schemes to JSON file
        
        Args:
            schemes: List of scheme records
            filename: Output filename
        """
        output_dir = 'data/raw'
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'source': 'data.gov.in',
                'fetched_at': datetime.now().isoformat(),
                'total_schemes': len(schemes),
                'schemes': schemes
            }, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(schemes)} schemes to {filepath}")


def main():
    """Main execution function"""
    
    # Get API key from environment or prompt
    api_key = os.getenv('DATA_GOV_IN_API_KEY')
    
    if not api_key:
        print("=" * 60)
        print("DATA.GOV.IN API KEY REQUIRED")
        print("=" * 60)
        print("\nTo get an API key:")
        print("1. Visit https://data.gov.in")
        print("2. Register for an account")
        print("3. Request API access")
        print("4. Copy your 32-character API key")
        print("\nSet the API key as environment variable:")
        print("export DATA_GOV_IN_API_KEY='your-api-key-here'")
        print("\nOr enter it now:")
        api_key = input("API Key: ").strip()
        
        if not api_key:
            print("No API key provided. Exiting.")
            return
    
    # Initialize scraper
    scraper = DataGovIndiaScraper(api_key)
    
    # Collect schemes
    print("\n" + "=" * 60)
    print("COLLECTING GOVERNMENT SCHEMES FROM DATA.GOV.IN")
    print("=" * 60 + "\n")
    
    # Method 1: Search by keywords
    print("Method 1: Searching by keywords...")
    keyword_schemes = scraper.search_scheme_keywords()
    scraper.save_to_json(keyword_schemes, 'data_gov_schemes_keywords.json')
    
    # Method 2: Get all welfare schemes
    print("\nMethod 2: Fetching all welfare schemes...")
    all_schemes = scraper.get_all_schemes(max_records=2000)
    scraper.save_to_json(all_schemes, 'data_gov_schemes_all.json')
    
    print("\n" + "=" * 60)
    print("DATA COLLECTION COMPLETE")
    print("=" * 60)
    print(f"\nTotal schemes collected: {len(set([s.get('id') or s.get('title') for s in keyword_schemes + all_schemes]))}")
    print("\nNext steps:")
    print("1. Review collected data in data/raw/")
    print("2. Run data cleaning script")
    print("3. Transform to standard schema")


if __name__ == "__main__":
    main()
