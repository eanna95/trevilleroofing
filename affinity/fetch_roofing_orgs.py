#!/usr/bin/env python3
"""
Fetch roofing organizations from Affinity API using optimized search terms
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

# Load minimal search terms for 100% coverage
def load_search_terms():
    """Load minimal search terms from file"""
    terms = []
    try:
        with open('/mnt/c/trevilleroofing/affinity/minimal_search_terms.txt', 'r') as f:
            for line in f:
                term = line.strip()
                if term:
                    terms.append(term)
    except FileNotFoundError:
        print("Error: minimal_search_terms.txt not found")
        return []
    
    return terms

SEARCH_TERMS = load_search_terms()

def fetch_organizations_by_term(search_term):
    """Fetch organizations for a specific search term"""
    
    organizations = []
    page_token = None
    page_count = 0
    
    print(f"Searching for '{search_term}'...")
    
    while True:
        page_count += 1
        
        # Setup parameters
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
                print(f"  Error: {response.status_code} - {response.text}")
                break
                
            data = response.json()
            page_orgs = data.get('organizations', [])
            
            # Filter organizations that have interaction history
            filtered_orgs = []
            for org in page_orgs:
                if org.get('interaction_dates') and org.get('interactions'):
                    # Extract latest interaction info
                    last_interaction = org['interactions'].get('last_interaction')
                    if last_interaction:
                        org_data = {
                            'name': org.get('name', ''),
                            'domain': org.get('domain', ''),
                            'latest_interaction_date': last_interaction.get('date', ''),
                            'latest_interaction_person_ids': ','.join(map(str, last_interaction.get('person_ids', []))),
                            'search_term': search_term,
                            'affinity_id': org.get('id', '')
                        }
                        filtered_orgs.append(org_data)
            
            organizations.extend(filtered_orgs)
            print(f"  Page {page_count}: Found {len(filtered_orgs)} organizations with interactions")
            
            # Check for next page
            page_token = data.get('next_page_token')
            if not page_token:
                break
                
            # Rate limiting
            time.sleep(0.3)
            
        except Exception as e:
            print(f"  Exception on page {page_count}: {e}")
            break
    
    print(f"  Total for '{search_term}': {len(organizations)} organizations")
    return organizations

def deduplicate_organizations(all_organizations):
    """Remove duplicate organizations based on domain and name"""
    
    seen = set()
    unique_orgs = []
    
    for org in all_organizations:
        # Create a key for deduplication (domain + name)
        domain = org['domain'].lower().strip() if org['domain'] else ''
        name = org['name'].lower().strip() if org['name'] else ''
        
        key = f"{domain}|{name}"
        
        if key not in seen:
            seen.add(key)
            unique_orgs.append(org)
    
    print(f"Deduplicated: {len(all_organizations)} -> {len(unique_orgs)} organizations")
    return unique_orgs

def save_to_csv(organizations, filename="roofing_organizations.csv"):
    """Save organizations data to CSV file"""
    
    if not organizations:
        print("No organizations to save")
        return
    
    fieldnames = ['name', 'domain', 'latest_interaction_date', 'latest_interaction_person_ids', 'search_term', 'affinity_id']
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(organizations)
    
    print(f"Saved {len(organizations)} organizations to {filename}")

def main():
    """Main function"""
    
    if not API_KEY:
        print("Error: AFFINITY_API key not found in .env file")
        return
    
    print("Starting complete roofing organizations fetch...")
    print(f"Number of search terms: {len(SEARCH_TERMS)}")
    print(f"Expected coverage: 100% of roofing companies")
    
    start_time = datetime.now()
    all_organizations = []
    
    # Search for each term
    for i, term in enumerate(SEARCH_TERMS, 1):
        print(f"\n[{i}/{len(SEARCH_TERMS)}] Searching for '{term}'...")
        term_orgs = fetch_organizations_by_term(term)
        all_organizations.extend(term_orgs)
        
        print(f"Progress: {i}/{len(SEARCH_TERMS)} terms completed")
        print(f"Total collected so far: {len(all_organizations)} organizations")
    
    print(f"\n=== Deduplication ===")
    unique_organizations = deduplicate_organizations(all_organizations)
    
    if unique_organizations:
        # Save to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f"roofing_organizations_100pct_{timestamp}.csv"
        save_to_csv(unique_organizations, csv_filename)
        
        # Print summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n=== Summary ===")
        print(f"Search terms used: {len(SEARCH_TERMS)}")
        print(f"Total API calls: ~{sum([1 for term in SEARCH_TERMS])} terms")
        print(f"Raw results: {len(all_organizations)} organizations")
        print(f"Unique organizations: {len(unique_organizations)}")
        print(f"Time taken: {duration}")
        print(f"Output file: {csv_filename}")
        
        # Show sample of data
        if len(unique_organizations) > 0:
            print(f"\nSample data (first 5 organizations):")
            for i, org in enumerate(unique_organizations[:5]):
                print(f"{i+1}. {org['name']} ({org['domain']}) - Found via: '{org['search_term']}'")
        
        # Show search term distribution
        term_counts = {}
        for org in unique_organizations:
            term = org['search_term']
            term_counts[term] = term_counts.get(term, 0) + 1
        
        print(f"\nResults by search term:")
        for term in SEARCH_TERMS:
            count = term_counts.get(term, 0)
            print(f"  {term}: {count} organizations")
            
    else:
        print("No organizations found")

if __name__ == "__main__":
    main()