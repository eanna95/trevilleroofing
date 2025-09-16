#!/usr/bin/env python3
"""
Get comprehensive search terms to cover 100% of roofing companies
"""

import csv
import re
from collections import Counter

def get_all_meaningful_terms(tsv_file):
    """Extract ALL meaningful search terms from company names"""
    
    all_terms = set()
    company_count = 0
    
    print("Extracting all meaningful terms...")
    
    with open(tsv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='|')
        
        for row in reader:
            company_name = row['company_name']
            if company_name and company_name != '- Select -':
                company_count += 1
                
                # Extract various search patterns
                name = company_name.lower()
                
                # Remove common suffixes
                suffixes = ['inc', 'llc', 'corp', 'co', 'company', 'ltd', 'limited']
                for suffix in suffixes:
                    name = re.sub(rf'\b{suffix}\.?\b', '', name)
                
                # Get all words 3+ characters
                words = re.findall(r'\b[a-zA-Z]{3,}\b', name)
                for word in words:
                    if word not in ['the', 'and', 'for', 'with']:
                        all_terms.add(word)
                
                # Get first word(s) as potential search terms
                first_words = re.findall(r'^([a-zA-Z]+)', name.strip())
                if first_words:
                    all_terms.add(first_words[0])
                
                # Get distinctive patterns (like "A&A", "ABC")
                patterns = re.findall(r'\b[a-zA-Z]\s*&\s*[a-zA-Z]\b', company_name)
                for pattern in patterns:
                    clean_pattern = re.sub(r'\s', '', pattern.lower())
                    all_terms.add(clean_pattern)
    
    # Convert to sorted list
    search_terms = sorted(list(all_terms))
    
    print(f"Found {len(search_terms)} unique search terms from {company_count} companies")
    return search_terms

def save_comprehensive_terms(search_terms, filename="comprehensive_search_terms.txt"):
    """Save all search terms to file"""
    
    with open(filename, 'w') as f:
        for term in search_terms:
            f.write(f"{term}\n")
    
    print(f"Saved {len(search_terms)} search terms to {filename}")

def main():
    tsv_file = "/mnt/c/trevilleroofing/scrape/final_aggregated_companies.tsv"
    
    # Get all meaningful search terms
    all_terms = get_all_meaningful_terms(tsv_file)
    
    # Save comprehensive list
    output_file = "/mnt/c/trevilleroofing/affinity/comprehensive_search_terms.txt"
    save_comprehensive_terms(all_terms, output_file)
    
    print(f"\nThis comprehensive list should cover 100% of your companies.")
    print(f"However, it will require {len(all_terms)} API calls.")
    print(f"Consider using this for complete coverage or stick with the 89% solution using 50 terms.")

if __name__ == "__main__":
    main()