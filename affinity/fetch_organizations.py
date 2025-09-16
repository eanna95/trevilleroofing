#!/usr/bin/env python3
"""
Fetch all organizations with interaction history from Affinity API
Saves org name, domain, latest interaction date and person ID to CSV
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

def fetch_all_organizations():
    """Fetch all organizations with interaction history from Affinity API"""
    
    organizations = []
    page_token = None
    page_count = 0
    total_orgs_processed = 0
    
    while True:
        page_count += 1
        print(f"Fetching page {page_count}...")
        
        # Setup parameters
        params = {
            'with_interaction_dates': 'true',
            'with_interaction_persons': 'true'
        }
        
        if page_token:
            params['page_token'] = page_token
        
        try:
            print(f"  Making API request...")
            start_request = time.time()
            
            response = requests.get(
                f"{BASE_URL}/organizations",
                auth=('', API_KEY),
                params=params,
                timeout=30  # Add timeout
            )
            
            request_time = time.time() - start_request
            print(f"  API request took {request_time:.2f} seconds")
            
            if response.status_code != 200:
                print(f"Error: {response.status_code} - {response.text}")
                break
                
            print(f"  Parsing response...")
            data = response.json()
            page_orgs = data.get('organizations', [])
            total_orgs_processed += len(page_orgs)
            
            print(f"  Processing {len(page_orgs)} organizations...")
            
            # Filter organizations that have interaction history
            filtered_orgs = []
            for i, org in enumerate(page_orgs):
                if i % 100 == 0 and i > 0:
                    print(f"    Processed {i}/{len(page_orgs)} orgs on this page...")
                    
                if org.get('interaction_dates') and org.get('interactions'):
                    # Extract latest interaction info
                    last_interaction = org['interactions'].get('last_interaction')
                    if last_interaction:
                        org_data = {
                            'name': org.get('name', ''),
                            'domain': org.get('domain', ''),
                            'latest_interaction_date': last_interaction.get('date', ''),
                            'latest_interaction_person_ids': ','.join(map(str, last_interaction.get('person_ids', [])))
                        }
                        filtered_orgs.append(org_data)
            
            organizations.extend(filtered_orgs)
            print(f"  Found {len(filtered_orgs)} organizations with interactions on this page")
            print(f"  Total orgs processed: {total_orgs_processed}")
            print(f"  Total with interactions: {len(organizations)}")
            
            # Check for next page
            page_token = data.get('next_page_token')
            if not page_token:
                print("  No more pages to fetch")
                break
            else:
                print(f"  Next page token: {page_token[:50]}...")
                
            # Rate limiting - be respectful to the API
            print(f"  Waiting 0.5s before next request...")
            time.sleep(0.5)
            
        except requests.exceptions.Timeout:
            print(f"Timeout on page {page_count}")
            break
        except Exception as e:
            print(f"Exception on page {page_count}: {e}")
            import traceback
            traceback.print_exc()
            break
    
    return organizations

def save_to_csv(organizations, filename="affinity_organizations.csv"):
    """Save organizations data to CSV file"""
    
    if not organizations:
        print("No organizations to save")
        return
    
    fieldnames = ['name', 'domain', 'latest_interaction_date', 'latest_interaction_person_ids']
    
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
    
    print("Starting Affinity organizations fetch...")
    print(f"API endpoint: {BASE_URL}/organizations")
    
    start_time = datetime.now()
    
    # Fetch all organizations
    organizations = fetch_all_organizations()
    
    if organizations:
        # Save to CSV
        csv_filename = f"affinity_organizations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        save_to_csv(organizations, csv_filename)
        
        # Print summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n=== Summary ===")
        print(f"Total organizations with interactions: {len(organizations)}")
        print(f"Time taken: {duration}")
        print(f"Output file: {csv_filename}")
        
        # Show sample of data
        if len(organizations) > 0:
            print(f"\nSample data (first 3 organizations):")
            for i, org in enumerate(organizations[:3]):
                print(f"{i+1}. {org['name']} ({org['domain']}) - Last interaction: {org['latest_interaction_date']}")
    else:
        print("No organizations found with interaction history")

if __name__ == "__main__":
    main()