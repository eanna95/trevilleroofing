#!/usr/bin/env python3
"""
Analyze roofing company names to find optimal search terms for Affinity API
"""

import csv
import re
from collections import Counter, defaultdict
import pandas as pd

def extract_keywords_from_name(company_name):
    """Extract meaningful keywords from company name"""
    # Clean the name
    name = company_name.lower()
    
    # Remove common suffixes and prefixes
    suffixes = ['inc', 'llc', 'corp', 'co', 'company', 'ltd', 'limited', 'services', 'solutions']
    prefixes = ['the', 'a', 'an']
    
    # Split into words and clean
    words = re.findall(r'\b[a-zA-Z]+\b', name)
    
    # Filter out common words and short words
    filtered_words = []
    for word in words:
        if len(word) >= 3 and word not in suffixes and word not in prefixes:
            filtered_words.append(word)
    
    return filtered_words

def analyze_company_names(tsv_file):
    """Analyze all company names to find most common terms"""
    
    all_keywords = []
    company_keywords = {}
    
    print("Reading company names...")
    
    with open(tsv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='|')
        
        for i, row in enumerate(reader):
            if i % 500 == 0:
                print(f"  Processed {i} companies...")
                
            company_name = row['company_name']
            if company_name and company_name != '- Select -':
                keywords = extract_keywords_from_name(company_name)
                all_keywords.extend(keywords)
                company_keywords[company_name] = keywords
    
    print(f"Analyzed {len(company_keywords)} companies")
    
    # Count frequency of all keywords
    keyword_counts = Counter(all_keywords)
    
    return company_keywords, keyword_counts

def find_optimal_search_terms(company_keywords, keyword_counts, target_coverage=100, max_terms=50):
    """Find the minimal set of search terms that cover target % of companies"""
    
    print(f"\nTop 30 most common keywords:")
    for word, count in keyword_counts.most_common(30):
        print(f"  {word}: {count} companies")
    
    # Find coverage for each keyword (lowered threshold for 100% coverage)
    keyword_coverage = {}
    for keyword, count in keyword_counts.items():
        if count >= 1:  # Include all keywords that appear at least once
            covered_companies = set()
            for company, keywords in company_keywords.items():
                if keyword in keywords:
                    covered_companies.add(company)
            keyword_coverage[keyword] = covered_companies
    
    # Greedy algorithm to find minimal set
    selected_terms = []
    covered_companies = set()
    remaining_companies = set(company_keywords.keys())
    target_count = int(len(company_keywords) * target_coverage / 100)
    
    print(f"\nFinding search terms to cover {target_count}/{len(company_keywords)} companies ({target_coverage}%)...")
    
    while len(selected_terms) < max_terms and len(covered_companies) < target_count and remaining_companies:
        best_term = None
        best_new_coverage = 0
        
        for term, companies in keyword_coverage.items():
            if term not in selected_terms:
                new_coverage = len(companies - covered_companies)
                if new_coverage > best_new_coverage:
                    best_new_coverage = new_coverage
                    best_term = term
        
        if best_term and best_new_coverage > 0:
            selected_terms.append(best_term)
            new_companies = keyword_coverage[best_term] - covered_companies
            covered_companies.update(new_companies)
            remaining_companies -= new_companies
            
            print(f"  {len(selected_terms)}. '{best_term}' covers {best_new_coverage} new companies (total: {len(covered_companies)})")
        else:
            # No more terms can add coverage, add individual company names for remaining
            if remaining_companies and len(selected_terms) < max_terms:
                # Add the first few company names directly as search terms
                remaining_list = list(remaining_companies)[:max_terms - len(selected_terms)]
                for company in remaining_list:
                    # Use the first meaningful word from company name
                    words = extract_keywords_from_name(company)
                    if words:
                        search_term = words[0]
                        selected_terms.append(search_term)
                        covered_companies.add(company)
                        remaining_companies.remove(company)
                        print(f"  {len(selected_terms)}. '{search_term}' (from '{company}') covers 1 new company (total: {len(covered_companies)})")
            break
    
    print(f"\nOptimal search terms: {selected_terms}")
    print(f"Coverage: {len(covered_companies)}/{len(company_keywords)} companies ({len(covered_companies)/len(company_keywords)*100:.1f}%)")
    print(f"Uncovered: {len(remaining_companies)} companies")
    
    return selected_terms, covered_companies, remaining_companies

def analyze_uncovered_companies(remaining_companies, company_keywords):
    """Analyze companies not covered by search terms"""
    
    if not remaining_companies:
        print("\nAll companies are covered!")
        return
    
    print(f"\nAnalyzing {len(remaining_companies)} uncovered companies:")
    
    uncovered_keywords = []
    for company in list(remaining_companies)[:20]:  # Show first 20
        keywords = company_keywords.get(company, [])
        print(f"  {company}: {keywords}")
        uncovered_keywords.extend(keywords)
    
    if len(remaining_companies) > 20:
        print(f"  ... and {len(remaining_companies) - 20} more")
    
    # Find common patterns in uncovered companies
    uncovered_counts = Counter(uncovered_keywords)
    print(f"\nMost common keywords in uncovered companies:")
    for word, count in uncovered_counts.most_common(10):
        print(f"  {word}: {count}")

def main():
    tsv_file = "/mnt/c/trevilleroofing/scrape/final_aggregated_companies.tsv"
    
    # Analyze company names
    company_keywords, keyword_counts = analyze_company_names(tsv_file)
    
    # Find optimal search terms for 100% coverage
    selected_terms, covered_companies, remaining_companies = find_optimal_search_terms(
        company_keywords, keyword_counts, target_coverage=100, max_terms=50
    )
    
    # Analyze what's not covered
    analyze_uncovered_companies(remaining_companies, company_keywords)
    
    # Save results
    print(f"\nSaving results...")
    
    # Save search terms
    with open('/mnt/c/trevilleroofing/affinity/optimal_search_terms.txt', 'w') as f:
        for term in selected_terms:
            f.write(f"{term}\n")
    
    # Save coverage analysis
    with open('/mnt/c/trevilleroofing/affinity/coverage_analysis.txt', 'w') as f:
        f.write(f"Optimal Search Terms Analysis\n")
        f.write(f"============================\n\n")
        f.write(f"Selected terms: {', '.join(selected_terms)}\n")
        f.write(f"Coverage: {len(covered_companies)}/{len(company_keywords)} companies ({len(covered_companies)/len(company_keywords)*100:.1f}%)\n")
        f.write(f"Uncovered: {len(remaining_companies)} companies\n\n")
        
        f.write(f"Top keywords by frequency:\n")
        for word, count in keyword_counts.most_common(20):
            f.write(f"  {word}: {count} companies\n")
    
    print(f"Results saved to:")
    print(f"  - optimal_search_terms.txt")
    print(f"  - coverage_analysis.txt")

if __name__ == "__main__":
    main()