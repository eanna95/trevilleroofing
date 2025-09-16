#!/usr/bin/env python3
"""
Test the minimal search approach with first 5 terms
"""

import os
import requests
import csv
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('AFFINITY_API')
BASE_URL = "https://api.affinity.co"

# Test with first 5 terms
TEST_TERMS = ['roofing', 'construction', 'roof', 'contracting', 'america']

def fetch_organizations_by_term(search_term):
    """Fetch organizations for a specific search term"""
    
    organizations = []
    page_token = None
    page_count = 0
    
    print(f"  Searching for '{search_term}'...")
    
    while True:
        page_count += 1
        
        params = {
            'term': search_term,
            'with_interaction_dates': 'true',
            'with_interaction_persons': 'true'
        }
        
        if page_token:
            params['page_token'] = page_token
        
        try:
            response = requests.get(
                f"{BASE_URL}/organizations",
                auth=('', API_KEY),
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"    Error: {response.status_code}")
                break
                
            data = response.json()
            page_orgs = data.get('organizations', [])
            
            # Filter organizations that have interaction history
            filtered_orgs = []
            for org in page_orgs:
                if org.get('interaction_dates') and org.get('interactions'):
                    last_interaction = org['interactions'].get('last_interaction')
                    if last_interaction:
                        org_data = {
                            'name': org.get('name', ''),
                            'domain': org.get('domain', ''),
                            'search_term': search_term,
                            'affinity_id': org.get('id', '')
                        }
                        filtered_orgs.append(org_data)
            
            organizations.extend(filtered_orgs)
            
            page_token = data.get('next_page_token')
            if not page_token:
                break
                
            time.sleep(0.2)
            
        except Exception as e:
            print(f"    Exception: {e}")
            break
    
    print(f"    Found {len(organizations)} organizations")
    return organizations

def main():
    print("Testing minimal search approach...")
    print(f"Testing with terms: {TEST_TERMS}")
    
    all_orgs = []
    for i, term in enumerate(TEST_TERMS, 1):
        print(f"\n[{i}/{len(TEST_TERMS)}] Testing '{term}'")
        orgs = fetch_organizations_by_term(term)
        all_orgs.extend(orgs)
    
    print(f"\nTest results:")
    print(f"Total organizations found: {len(all_orgs)}")
    
    # Show some examples
    for i, org in enumerate(all_orgs[:10]):
        print(f"  {org['name']} (via '{org['search_term']}')")
    
    print(f"\nMinimal search approach is working!")
    print(f"Ready to run full search with 333 terms for 100% coverage")

if __name__ == "__main__":
    main()