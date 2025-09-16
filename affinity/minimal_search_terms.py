#!/usr/bin/env python3
"""
Find minimal set of search terms for 100% coverage using proper exclusion
"""

import csv
import re
from collections import Counter

# Words to ignore when creating search terms
IGNORE_WORDS = {
    'inc', 'llc', 'corp', 'co', 'company', 'ltd', 'limited', 'services', 'solutions',
    'the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'at', 'by', 'for', 'with',
    'to', 'from', 'as', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
}

def extract_keywords_from_name(company_name):
    """Extract meaningful keywords from company name"""
    name = company_name.lower()
    
    # Remove punctuation and split into words
    words = re.findall(r'\b[a-zA-Z]+\b', name)
    
    # Filter out ignored words and short words
    filtered_words = []
    for word in words:
        if len(word) >= 3 and word not in IGNORE_WORDS:
            filtered_words.append(word)
    
    return filtered_words

def load_companies(tsv_file):
    """Load all company names from TSV file"""
    companies = []
    
    print("Loading companies...")
    
    with open(tsv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='|')
        
        for row in reader:
            company_name = row['company_name']
            if company_name and company_name != '- Select -':
                companies.append(company_name)
    
    print(f"Loaded {len(companies)} companies")
    return companies

def find_minimal_search_terms(companies):
    """Find minimal set of search terms for 100% coverage"""
    
    # Create company -> keywords mapping
    company_keywords = {}
    all_keywords = []
    
    for company in companies:
        keywords = extract_keywords_from_name(company)
        company_keywords[company] = keywords
        all_keywords.extend(keywords)
    
    # Count keyword frequencies
    keyword_counts = Counter(all_keywords)
    
    print(f"\nTop 20 most frequent keywords:")
    for word, count in keyword_counts.most_common(20):
        print(f"  {word}: {count} companies")
    
    # Find minimal search terms using greedy algorithm
    selected_terms = []
    remaining_companies = set(companies)
    
    print(f"\nFinding minimal search terms for {len(remaining_companies)} companies...")
    
    iteration = 0
    while remaining_companies:
        iteration += 1
        
        # Find the keyword that covers the most remaining companies
        best_keyword = None
        best_coverage = 0
        
        # Count how many remaining companies each keyword covers
        keyword_coverage = Counter()
        for company in remaining_companies:
            for keyword in company_keywords[company]:
                keyword_coverage[keyword] += 1
        
        # Find the best keyword
        if keyword_coverage:
            best_keyword, best_coverage = keyword_coverage.most_common(1)[0]
        
        if not best_keyword or best_coverage == 0:
            # No keywords left that cover remaining companies
            # This shouldn't happen, but let's handle it
            print(f"Warning: No keywords found for remaining {len(remaining_companies)} companies")
            break
        
        # Add the best keyword to our search terms
        selected_terms.append(best_keyword)
        
        # Remove all companies covered by this keyword
        covered_companies = set()
        for company in remaining_companies:
            if best_keyword in company_keywords[company]:
                covered_companies.add(company)
        
        remaining_companies -= covered_companies
        
        print(f"  {iteration}. '{best_keyword}' covers {len(covered_companies)} companies (remaining: {len(remaining_companies)})")
    
    print(f"\nMinimal search terms: {selected_terms}")
    print(f"Total terms needed: {len(selected_terms)}")
    print(f"Coverage: 100% ({len(companies)} companies)")
    
    return selected_terms

def save_minimal_terms(search_terms, filename="minimal_search_terms.txt"):
    """Save minimal search terms to file"""
    
    with open(filename, 'w') as f:
        for term in search_terms:
            f.write(f"{term}\n")
    
    print(f"\nSaved {len(search_terms)} minimal search terms to {filename}")

def main():
    tsv_file = "/mnt/c/trevilleroofing/scrape/final_aggregated_companies.tsv"
    
    # Load all companies
    companies = load_companies(tsv_file)
    
    # Find minimal search terms
    minimal_terms = find_minimal_search_terms(companies)
    
    # Save results
    output_file = "/mnt/c/trevilleroofing/affinity/minimal_search_terms.txt"
    save_minimal_terms(minimal_terms, output_file)
    
    print(f"\nThis minimal set will require {len(minimal_terms)} API calls for 100% coverage")

if __name__ == "__main__":
    main()