#!/usr/bin/env python3
"""
Test script to understand Affinity API response structure
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('AFFINITY_API')
BASE_URL = "https://api.affinity.co"

def test_organizations_endpoint():
    """Test the organizations endpoint to understand response structure"""
    
    # Test basic endpoint
    url = f"{BASE_URL}/organizations"
    
    # Try with interaction data parameters
    params = {
        'with_interaction_dates': 'true',
        'with_interaction_persons': 'true'
    }
    
    print("Testing Affinity Organizations API...")
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    try:
        response = requests.get(
            url,
            auth=('', API_KEY),  # Affinity uses empty username with API key as password
            params=params
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            if 'organizations' in data and data['organizations']:
                print(f"Number of organizations: {len(data['organizations'])}")
                print("\nFirst organization structure:")
                print(json.dumps(data['organizations'][0], indent=2))
                
                # Check for pagination
                if 'next_page_token' in data:
                    print(f"\nPagination token present: {data['next_page_token']}")
            else:
                print("No organizations found in response")
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    test_organizations_endpoint()