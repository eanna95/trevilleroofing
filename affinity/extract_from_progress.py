#!/usr/bin/env python3
"""
Extract clean pipe-delimited data from the progress file
"""

import json
import csv
from datetime import datetime

def extract_and_save():
    """Extract data from progress file and save as pipe-delimited"""
    
    # Load the progress data
    with open('search_progress.json', 'r') as f:
        progress = json.load(f)
    
    all_organizations = progress["all_organizations"]
    
    # Deduplicate based on domain + name
    seen = set()
    unique_orgs = []
    
    for org in all_organizations:
        domain = org['domain'].lower().strip() if org['domain'] else ''
        name = org['name'].lower().strip() if org['name'] else ''
        key = f"{domain}|{name}"
        
        if key not in seen:
            seen.add(key)
            unique_orgs.append(org)
    
    # Save as pipe-delimited
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"roofing_organizations_100pct_{timestamp}.tsv"
    
    fieldnames = ['name', 'domain', 'latest_interaction_date', 'latest_interaction_person_ids', 'search_term', 'affinity_id']
    
    with open(filename, 'w', newline='', encoding='utf-8') as tsvfile:
        writer = csv.DictWriter(tsvfile, fieldnames=fieldnames, delimiter='|')
        writer.writeheader()
        
        # Write each row manually to control quoting of person IDs
        for org in unique_orgs:
            # Pre-quote the person IDs field for safety
            if org['latest_interaction_person_ids']:
                org['latest_interaction_person_ids'] = f'"{org["latest_interaction_person_ids"]}"'
            writer.writerow(org)
    
    print(f"Extracted {len(unique_orgs)} unique organizations to {filename}")
    
    # Show sample
    print(f"\nSample data:")
    for i, org in enumerate(unique_orgs[:3]):
        print(f"{i+1}. {org['name']} | {org['domain']}")

if __name__ == "__main__":
    extract_and_save()