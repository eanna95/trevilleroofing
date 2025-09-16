#!/usr/bin/env python3
"""
Robust version that saves progress and can resume from interruptions
"""

import os
import requests
import csv
import time
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('AFFINITY_API')
BASE_URL = "https://api.affinity.co"

def load_search_terms():
    """Load search terms from file"""
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

def load_progress():
    """Load progress from previous run"""
    try:
        with open('search_progress.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"completed_terms": [], "all_organizations": []}

def save_progress(completed_terms, all_organizations):
    """Save current progress"""
    progress = {
        "completed_terms": completed_terms,
        "all_organizations": all_organizations,
        "last_updated": datetime.now().isoformat()
    }
    with open('search_progress.json', 'w') as f:
        json.dump(progress, f, indent=2)

def fetch_organizations_by_term(search_term):
    """Fetch organizations for a specific search term"""
    organizations = []
    page_token = None
    
    while True:
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
            for org in page_orgs:
                if org.get('interaction_dates') and org.get('interactions'):
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
                        organizations.append(org_data)
            
            page_token = data.get('next_page_token')
            if not page_token:
                break
                
            time.sleep(0.2)
            
        except Exception as e:
            print(f"    Exception: {e}")
            break
    
    return organizations

def deduplicate_organizations(all_organizations):
    """Remove duplicate organizations based on domain and name"""
    seen = set()
    unique_orgs = []
    
    for org in all_organizations:
        domain = org['domain'].lower().strip() if org['domain'] else ''
        name = org['name'].lower().strip() if org['name'] else ''
        key = f"{domain}|{name}"
        
        if key not in seen:
            seen.add(key)
            unique_orgs.append(org)
    
    return unique_orgs

def save_to_csv(organizations, filename):
    """Save organizations data to pipe-delimited file"""
    if not organizations:
        print("No organizations to save")
        return
    
    fieldnames = ['name', 'domain', 'latest_interaction_date', 'latest_interaction_person_ids', 'search_term', 'affinity_id']
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='|')
        writer.writeheader()
        writer.writerows(organizations)
    
    print(f"Saved {len(organizations)} organizations to {filename}")

def main():
    """Main function with progress tracking"""
    
    if not API_KEY:
        print("Error: AFFINITY_API key not found in .env file")
        return
    
    # Load search terms and progress
    search_terms = load_search_terms()
    progress = load_progress()
    
    completed_terms = set(progress["completed_terms"])
    all_organizations = progress["all_organizations"]
    
    remaining_terms = [term for term in search_terms if term not in completed_terms]
    
    print(f"Total search terms: {len(search_terms)}")
    print(f"Completed terms: {len(completed_terms)}")
    print(f"Remaining terms: {len(remaining_terms)}")
    print(f"Organizations collected so far: {len(all_organizations)}")
    
    if not remaining_terms:
        print("All terms completed! Finalizing results...")
    else:
        print(f"Resuming from term: {remaining_terms[0]}")
        
        # Process remaining terms
        for i, term in enumerate(remaining_terms):
            print(f"\n[{len(completed_terms)+i+1}/{len(search_terms)}] Searching for '{term}'...")
            
            try:
                term_orgs = fetch_organizations_by_term(term)
                all_organizations.extend(term_orgs)
                completed_terms.add(term)
                
                print(f"  Found {len(term_orgs)} organizations")
                print(f"  Total collected: {len(all_organizations)}")
                
                # Save progress every 10 terms
                if (len(completed_terms)) % 10 == 0:
                    save_progress(list(completed_terms), all_organizations)
                    print(f"  Progress saved at {len(completed_terms)} terms")
                
            except KeyboardInterrupt:
                print("\nInterrupted by user. Saving progress...")
                save_progress(list(completed_terms), all_organizations)
                return
            except Exception as e:
                print(f"  Error processing '{term}': {e}")
                continue
    
    # Final processing
    print(f"\n=== Deduplication ===")
    unique_organizations = deduplicate_organizations(all_organizations)
    
    # Save final results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f"roofing_organizations_100pct_{timestamp}.tsv"
    save_to_csv(unique_organizations, csv_filename)
    
    # Final save of progress
    save_progress(list(completed_terms), all_organizations)
    
    print(f"\n=== Final Summary ===")
    print(f"Completed terms: {len(completed_terms)}/{len(search_terms)}")
    print(f"Raw results: {len(all_organizations)} organizations")
    print(f"Unique organizations: {len(unique_organizations)}")
    print(f"Output file: {csv_filename}")

if __name__ == "__main__":
    main()