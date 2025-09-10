#!/usr/bin/env python3
"""
Fuzzy matching utilities for company name normalization and matching.

Contains shared functions for normalizing company names by removing
business suffixes, handling parentheses, and other text cleaning operations.
"""

import re
from typing import Set

# Comprehensive list of business suffixes to remove for matching
BUSINESS_SUFFIXES = [
    'LLC', 'INC', 'INCORPORATED', 'LTD', 'LIMITED', 'CORP', 'CORPORATION', 'CO', 'COMPANY',
    'LP', 'LLP', 'PLLC', 'PC', 'PA', 'PSC', 'LLLP', 'LC', 'HOLDINGS', 'GROUP', 'ENTERPRISES',
    'SOLUTIONS', 'SERVICES', 'SYSTEMS', 'TECHNOLOGIES', 'ASSOCIATES', 'PARTNERS', 'CONSULTING',
    'MANAGEMENT', 'ADVISORS', 'VENTURES', 'CAPITAL', 'INVESTMENTS', 'PROPERTIES', 'DEVELOPMENT',
    'CONSTRUCTION', 'CONTRACTORS', 'MANUFACTURING', 'INDUSTRIES', 'INTERNATIONAL', 'WORLDWIDE',
    'GLOBAL', 'NATIONAL', 'REGIONAL', 'LOCAL'
]

def normalize_company_name(company_name: str) -> str:
    """
    Normalize a company name by removing business suffixes and parenthetical content for matching.
    
    Args:
        company_name: Original company name
        
    Returns:
        Normalized company name with suffixes and parentheses removed
    """
    if not company_name:
        return ""
    
    # Strip and remove punctuation from the end, including quotes
    normalized = company_name.strip().rstrip('.,;!?').strip('"\'')
    
    # Also strip quotes from the beginning
    normalized = normalized.lstrip('"\'').strip()
    
    # Remove content in parentheses (e.g., "Apple Roofing (Roofing Services)" -> "Apple Roofing")
    normalized = re.sub(r'\s*\([^)]*\)\s*', ' ', normalized).strip()
    
    # Remove commas completely (makes "ABC Roofing, A Tecta America" -> "ABC Roofing A Tecta America")
    normalized = re.sub(r',', '', normalized)
    
    # Normalize 'and' and '&' to be interchangeable
    # Convert both 'and' and '&' to a consistent form (using '&')
    normalized = re.sub(r'\s+and\s+', ' & ', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\s*&\s*', ' & ', normalized)  # Ensure consistent spacing around &
    
    # Convert to uppercase for suffix matching
    name_upper = normalized.upper()
    
    # Remove suffixes that appear at the end (commas already removed above)
    words = name_upper.split()
    while words:
        # Clean punctuation from the last word
        last_word = words[-1].rstrip('.,;!?')
        if last_word in BUSINESS_SUFFIXES:
            words.pop()
        else:
            # Replace the last word with its cleaned version
            words[-1] = last_word
            break
    
    # Clean up trailing connectors like "&" that might be left after suffix removal
    result = ' '.join(words).lower().strip()
    result = re.sub(r'\s+&\s*$', '', result).strip()  # Remove trailing " &"
    result = re.sub(r'^&\s+', '', result).strip()     # Remove leading "& "
    
    return result

def create_fuzzy_matcher(company_names: list) -> dict:
    """
    Create a dictionary mapping normalized names to original names for fuzzy matching.
    
    Args:
        company_names: List of original company names
        
    Returns:
        Dictionary mapping normalized names to list of original names
    """
    normalized_to_original = {}
    
    for company_name in company_names:
        if not company_name:
            continue
            
        normalized = normalize_company_name(company_name)
        if normalized:
            if normalized not in normalized_to_original:
                normalized_to_original[normalized] = []
            if company_name not in normalized_to_original[normalized]:
                normalized_to_original[normalized].append(company_name)
    
    return normalized_to_original

def fuzzy_match(target_name: str, normalized_matcher: dict) -> list:
    """
    Find fuzzy matches for a target company name.
    
    Args:
        target_name: Company name to find matches for
        normalized_matcher: Dictionary from create_fuzzy_matcher
        
    Returns:
        List of matching original company names (empty if no match)
    """
    normalized_target = normalize_company_name(target_name)
    return normalized_matcher.get(normalized_target, [])