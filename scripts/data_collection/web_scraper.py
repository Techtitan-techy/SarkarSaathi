#!/usr/bin/env python3
"""
Web Scraper for Government Scheme Websites
Collects scheme data from various government portals
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Optional
import re

class GovernmentSchemeScraper:
    """Scraper for government scheme websites"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.schemes = []
    
    def scrape_wikipedia_schemes(self) -> List[Dict]:
        """
        Scrape schemes from Wikipedia's comprehensive list
        
        Returns:
            List of scheme dictionaries
        """
        url = "https://en.wikipedia.org/wiki/List_of_schemes_of_the_government_of_India"
        
        print(f"Scraping Wikipedia: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            schemes = []
            
            # Find all tables with scheme information
            tables = soup.find_all('table', {'class': 'wikitable'})
            
            for table in tables:
                rows = table.find_all('tr')[1:]  # Skip header
                
                for row in rows:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 2:
                        scheme_name = cols[0].get_text(strip=True)
                        description = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                        ministry = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                        
                        if scheme_name and scheme_name != "Scheme":
                            schemes.append({
                                'name': scheme_name,
                                'description': description,
                                'ministry': ministry,
                                'source': 'Wikipedia',
                                'type': 'Central',
                                'state': 'All India'
                            })
            
            print(f"Found {len(schemes)} schemes from Wikipedia")
            return schemes
            
        except Exception as e:
            print(f"Error scraping Wikipedia: {e}")
            return []
    
    def scrape_popular_schemes(self) -> List[Dict]:
        """
        Manually curated list of popular schemes with complete details
        
        Returns:
            List of popular scheme dictionaries
        """
        popular_schemes = [
            {
                "name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
                "category": "Agriculture",
                "type": "Central",
                "state": "All India",
                "ministry": "Ministry of Agriculture & Farmers Welfare",
                "description": "Direct income support of ₹6,000 per year to landholding farmer families",
                "eligibility": {
                    "ageRange": {"min": 18, "max": 999},
                    "incomeRange": {"min": 0, "max": 999999999},
                    "occupation": ["Farmer", "Agricultural Worker"]
                },
                "benefits": ["₹6,000 per year in 3 installments", "Direct Bank Transfer"],
                "documents": ["Aadhaar Card", "Bank Account", "Land Records"],
                "website": "https://pmkisan.gov.in",
                "helpline": "155261"
            },
            {
                "name": "Ayushman Bharat - PM Jan Arogya Yojana (PM-JAY)",
                "category": "Healthcare",
                "type": "Central",
                "state": "All India",
                "ministry": "National Health Authority",
                "description": "Health insurance of ₹5 lakh per family per year",
                "eligibility": {
                    "ageRange": {"min": 0, "max": 999},
                    "incomeRange": {"min": 0, "max": 999999999}
                },
                "benefits": ["₹5 lakh health coverage", "Cashless treatment", "1,949 procedures covered"],
                "documents": ["Aadhaar Card", "Ration Card"],
                "website": "https://pmjay.gov.in",
                "helpline": "14555"
            },
            {
                "name": "Pradhan Mantri Awas Yojana - Urban (PMAY-U)",
                "category": "Housing",
                "type": "Central",
                "state": "All India",
                "ministry": "Ministry of Housing & Urban Affairs",
                "description": "Affordable housing for urban poor with interest subsidy",
                "eligibility": {
                    "ageRange": {"min": 18, "max": 999},
                    "incomeRange": {"min": 0, "max": 1800000}
                },
                "benefits": ["Interest subsidy up to ₹2.67 lakh", "Direct assistance"],
                "documents": ["Aadhaar", "Income Certificate", "Property Documents"],
                "website": "https://pmaymis.gov.in",
                "helpline": "1800-11-6163"
            },
            {
                "name": "Pradhan Mantri Awas Yojana - Gramin (PMAY-G)",
                "category": "Housing",
                "type": "Central",
                "state": "All India",
                "ministry": "Ministry of Rural Development",
                "description": "Housing for rural poor with financial assistance",
                "eligibility": {
                    "ageRange": {"min": 18, "max": 999},
                    "incomeRange": {"min": 0, "max": 200000}
                },
                "benefits": ["₹1.2-1.3 lakh assistance", "Toilet assistance ₹12,000"],
                "documents": ["Aadhaar", "BPL Card", "Bank Account"],
                "website": "https://pmayg.nic.in",
                "helpline": "1800-11-6446"
            },
            {
                "name": "Mahatma Gandhi National Rural Employment Guarantee Act (MGNREGA)",
                "category": "Employment",
                "type": "Central",
                "state": "All India",
                "ministry": "Ministry of Rural Development",
                "description": "100 days guaranteed wage employment per rural household",
                "eligibility": {
                    "ageRange": {"min": 18, "max": 999},
                    "incomeRange": {"min": 0, "max": 999999999}
                },
                "benefits": ["100 days employment", "₹221-357 per day wages"],
                "documents": ["Aadhaar", "Address Proof", "Photo"],
                "website": "https://nrega.nic.in",
                "helpline": "1800-345-22-44"
            },
            {
                "name": "Sukanya Samriddhi Yojana (SSY)",
                "category": "Women & Child",
                "type": "Central",
                "state": "All India",
                "ministry": "Ministry of Finance",
                "description": "Savings scheme for girl child with 8.2% interest",
                "eligibility": {
                    "ageRange": {"min": 0, "max": 10},
                    "incomeRange": {"min": 0, "max": 999999999}
                },
                "benefits": ["8.2% interest rate", "Tax benefits under 80C", "Maturity after 21 years"],
                "documents": ["Birth Certificate", "Parent's Aadhaar", "PAN Card"],
                "website": "https://www.indiapost.gov.in",
                "helpline": "1800-11-2011"
            },
            {
                "name": "Pradhan Mantri MUDRA Yojana (PMMY)",
                "category": "Employment",
                "type": "Central",
                "state": "All India",
                "ministry": "Ministry of Finance",
                "description": "Collateral-free loans up to ₹20 lakh for micro-enterprises",
                "eligibility": {
                    "ageRange": {"min": 18, "max": 999},
                    "incomeRange": {"min": 0, "max": 999999999},
                    "occupation": ["Self-Employed", "Entrepreneur"]
                },
                "benefits": ["Loans up to ₹20 lakh", "No collateral", "3 categories: Shishu/Kishore/Tarun"],
                "documents": ["Aadhaar", "PAN", "Business Plan", "Bank Account"],
                "website": "https://udyamimitra.in",
                "helpline": "1800-180-1111"
            },
            {
                "name": "Atal Pension Yojana (APY)",
                "category": "Social Security",
                "type": "Central",
                "state": "All India",
                "ministry": "PFRDA",
                "description": "Guaranteed pension of ₹1,000-5,000 after 60 years",
                "eligibility": {
                    "ageRange": {"min": 18, "max": 40},
                    "incomeRange": {"min": 0, "max": 999999999}
                },
                "benefits": ["Guaranteed monthly pension", "Government co-contribution", "Spouse benefit"],
                "documents": ["Aadhaar", "Bank Account", "Mobile Number"],
                "website": "https://www.npscra.nsdl.co.in",
                "helpline": "1800-110-001"
            },
            {
                "name": "Pradhan Mantri Ujjwala Yojana (PMUY)",
                "category": "Energy",
                "type": "Central",
                "state": "All India",
                "ministry": "Ministry of Petroleum & Natural Gas",
                "description": "Free LPG connection for BPL households",
                "eligibility": {
                    "ageRange": {"min": 18, "max": 999},
                    "incomeRange": {"min": 0, "max": 999999999}
                },
                "benefits": ["Free LPG connection", "Deposit-free cylinder", "Safety equipment"],
                "documents": ["Aadhaar", "BPL Card", "Bank Account", "Address Proof"],
                "website": "https://www.pmuy.gov.in",
                "helpline": "1906"
            },
            {
                "name": "Pradhan Mantri Jan Dhan Yojana (PMJDY)",
                "category": "Financial Inclusion",
                "type": "Central",
                "state": "All India",
                "ministry": "Ministry of Finance",
                "description": "Zero-balance bank account with RuPay debit card",
                "eligibility": {
                    "ageRange": {"min": 10, "max": 999},
                    "incomeRange": {"min": 0, "max": 999999999}
                },
                "benefits": ["Zero-balance account", "RuPay debit card", "₹10,000 overdraft", "₹2 lakh insurance"],
                "documents": ["Aadhaar", "Address Proof", "Photo"],
                "website": "https://pmjdy.gov.in",
                "helpline": "1800-11-0001"
            }
        ]
        
        print(f"Loaded {len(popular_schemes)} popular schemes")
        return popular_schemes
    
    def save_to_json(self, schemes: List[Dict], filename: str):
        """Save schemes to JSON file"""
        output_dir = 'data/raw'
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'source': 'Web Scraping',
                'fetched_at': datetime.now().isoformat(),
                'total_schemes': len(schemes),
                'schemes': schemes
            }, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(schemes)} schemes to {filepath}")


def main():
    """Main execution function"""
    
    print("=" * 60)
    print("WEB SCRAPING FOR GOVERNMENT SCHEMES")
    print("=" * 60 + "\n")
    
    scraper = GovernmentSchemeScraper()
    
    # Collect from various sources
    all_schemes = []
    
    # 1. Popular schemes (curated)
    print("1. Loading popular schemes...")
    popular = scraper.scrape_popular_schemes()
    all_schemes.extend(popular)
    scraper.save_to_json(popular, 'popular_schemes.json')
    
    # 2. Wikipedia schemes
    print("\n2. Scraping Wikipedia...")
    wikipedia = scraper.scrape_wikipedia_schemes()
    all_schemes.extend(wikipedia)
    scraper.save_to_json(wikipedia, 'wikipedia_schemes.json')
    
    # 3. Save combined
    print("\n3. Saving combined dataset...")
    scraper.save_to_json(all_schemes, 'web_scraped_schemes_all.json')
    
    print("\n" + "=" * 60)
    print("WEB SCRAPING COMPLETE")
    print("=" * 60)
    print(f"\nTotal schemes collected: {len(all_schemes)}")
    print(f"- Popular schemes: {len(popular)}")
    print(f"- Wikipedia schemes: {len(wikipedia)}")
    print("\nFiles saved in data/raw/")


if __name__ == "__main__":
    main()
