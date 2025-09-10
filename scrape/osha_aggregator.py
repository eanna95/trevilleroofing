#!/usr/bin/env python3
"""
OSHA Multi-Year Aggregator Script

Aggregates multiple years of OSHA data into a single file with year-over-year employment metrics.
Uses fuzzy matching to consolidate companies across different years.
"""

import argparse
import csv
import sys
import os
import re
import logging
from typing import Dict, List, Set, Any, Tuple
from fuzzy_utils import normalize_company_name, create_fuzzy_matcher, fuzzy_match

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_year_from_filename(filename: str) -> str:
    """
    Extract year from filename pattern <something>_<year>.csv
    
    Args:
        filename: Path to file
        
    Returns:
        Year as string, or filename without extension if no year found
    """
    basename = os.path.splitext(os.path.basename(filename))[0]
    # Look for 4-digit year at the end after underscore
    match = re.search(r'_(\d{4})$', basename)
    if match:
        return match.group(1)
    else:
        # Fallback to full basename if no year pattern found
        logger.warning(f"Could not extract year from filename: {filename}, using basename: {basename}")
        return basename

def aggregate_single_year_data(osha_file: str) -> Tuple[str, Dict[str, Dict[str, Any]]]:
    """
    Aggregate OSHA data by company name for a single year.
    
    Args:
        osha_file: Path to the OSHA CSV file
        
    Returns:
        Tuple of (year, dictionary mapping normalized company names to aggregated data)
    """
    year = extract_year_from_filename(osha_file)
    logger.info(f"Loading and aggregating OSHA data from: {osha_file} (year: {year})")
    
    # Group rows by company name for aggregation
    company_rows = {}  # company_name -> [list of establishment rows]
    total_rows = 0
    
    try:
        # Determine delimiter based on file extension
        delimiter = '|' if osha_file.endswith('.tsv') else ','
        
        with open(osha_file, 'r', encoding='utf-8-sig') as f:  # Handle BOM
            reader = csv.DictReader(f, delimiter=delimiter)
            
            for row in reader:
                total_rows += 1
                company_name = row.get('company_name', '').strip()
                
                if company_name:
                    if company_name not in company_rows:
                        company_rows[company_name] = []
                    company_rows[company_name].append(row)
                
                # Log progress every 10000 rows
                if total_rows % 10000 == 0:
                    logger.info(f"Year {year}: Processed {total_rows} rows...")
        
        logger.info(f"Year {year}: Processed {total_rows} total rows")
        logger.info(f"Year {year}: Found {len(company_rows)} unique companies")
        
        # Aggregate each company's data
        aggregated_companies = {}
        
        for company_name, rows in company_rows.items():
            # Aggregate numeric fields
            total_employees = 0
            total_hours = 0
            unique_eins = set()
            
            for row in rows:
                # Aggregate annual_average_employees
                try:
                    emp_str = row.get('annual_average_employees', 0) or 0
                    emp_val = int(float(emp_str))  # Convert to float first to handle decimals, then to int
                    total_employees += emp_val
                except (ValueError, TypeError):
                    pass
                
                # Aggregate total_hours_worked
                try:
                    hours_str = row.get('total_hours_worked', 0) or 0
                    hours_val = int(float(hours_str))  # Convert to float first to handle decimals, then to int
                    total_hours += hours_val
                except (ValueError, TypeError):
                    pass
                
                # Collect unique EINs
                ein = row.get('ein', '').strip()
                if ein:
                    unique_eins.add(ein)
            
            # Create normalized key for matching
            normalized_name = normalize_company_name(company_name)
            
            # Store aggregated data
            aggregated_companies[normalized_name] = {
                'company_name': company_name,
                'annual_average_employees': total_employees,
                'total_hours_worked': total_hours,
                'ein': ', '.join(sorted(unique_eins)) if unique_eins else '',
                'stripped_company_name': normalized_name,
                'year': year
            }
        
        logger.info(f"Year {year}: Aggregation complete - {len(aggregated_companies)} unique companies")
        return year, aggregated_companies
        
    except FileNotFoundError:
        logger.error(f"OSHA file not found: {osha_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error processing OSHA file {osha_file}: {e}")
        sys.exit(1)

def consolidate_multi_year_data(year_data: Dict[str, Dict[str, Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """
    Consolidate companies across multiple years using EIN matching first, then fuzzy matching.
    
    Args:
        year_data: Dictionary mapping year -> {normalized_name -> company_data}
        
    Returns:
        Dictionary mapping consolidated_normalized_name -> complete multi-year record
    """
    logger.info("Consolidating companies across years using EIN matching (with fuzzy fallback)...")
    
    # Log summary of input data
    total_companies_across_years = 0
    for year, companies in year_data.items():
        logger.info(f"Year {year}: {len(companies)} unique companies")
        total_companies_across_years += len(companies)
    
    logger.info(f"Total company-year records before consolidation: {total_companies_across_years}")
    
    # Create EIN-based index for faster matching
    ein_to_companies = {}  # EIN -> [(year, normalized_name, company_data), ...]
    for year, companies in year_data.items():
        for normalized_name, company_data in companies.items():
            ein = company_data['ein'].strip()
            if ein:  # Only index companies with EINs
                if ein not in ein_to_companies:
                    ein_to_companies[ein] = []
                ein_to_companies[ein].append((year, normalized_name, company_data))
    
    logger.info(f"Found {len(ein_to_companies)} unique EINs across all years")
    
    # Create fuzzy matcher for companies without EINs
    all_company_names = []
    for year, companies in year_data.items():
        for normalized_name, company_data in companies.items():
            if not company_data['ein'].strip():  # Only include companies without EINs for fuzzy matching
                all_company_names.append(company_data['company_name'])
    
    fuzzy_matcher = create_fuzzy_matcher(all_company_names)
    logger.info(f"Created fuzzy matcher for {len(all_company_names)} companies without EINs")
    
    # Final consolidated data
    consolidated_companies = {}  # consolidated_normalized_name -> multi-year record
    processed_companies = set()  # Track which companies we've already processed
    
    # Get sorted years for consistent processing
    sorted_years = sorted(year_data.keys())
    
    # Phase 1: Process companies with EINs using EIN-based matching
    ein_matches_found = 0
    for ein, company_list in ein_to_companies.items():
        if len(company_list) == 1:
            continue  # Skip single-year companies for now, process in phase 2
            
        ein_matches_found += 1
        # Use the first company's normalized name as the consolidated key
        first_year, first_normalized_name, first_company_data = company_list[0]
        consolidated_normalized_name = first_normalized_name
        
        # Create consolidated record
        consolidated_companies[consolidated_normalized_name] = {
            'company_name': '',  # Will be set to latest year
            'ein': ein,
            'stripped_company_name': normalize_company_name(first_company_data['company_name'])
        }
        
        # Initialize all year columns to 0
        for init_year in sorted_years:
            consolidated_companies[consolidated_normalized_name][f'annual_average_employees_{init_year}'] = 0
            consolidated_companies[consolidated_normalized_name][f'total_hours_worked_{init_year}'] = 0
        
        # Process all companies with this EIN across all years
        latest_year = None
        for check_year, normalized_name, company_data in company_list:
            # Update year-specific data
            consolidated_companies[consolidated_normalized_name][f'annual_average_employees_{check_year}'] = company_data['annual_average_employees']
            consolidated_companies[consolidated_normalized_name][f'total_hours_worked_{check_year}'] = company_data['total_hours_worked']
            
            # Track latest year for setting company name
            if latest_year is None or check_year > latest_year:
                latest_year = check_year
                consolidated_companies[consolidated_normalized_name]['company_name'] = company_data['company_name']
                consolidated_companies[consolidated_normalized_name]['stripped_company_name'] = normalize_company_name(company_data['company_name'])
            
            # Mark as processed
            processed_companies.add((normalized_name, check_year))
    
    logger.info(f"EIN matching: Found {ein_matches_found} companies appearing in multiple years")
    
    # Phase 2: Process remaining companies (single-year EIN companies + companies without EINs)
    fuzzy_matches_found = 0
    for year in sorted_years:
        logger.info(f"Processing remaining companies for year {year}...")
        
        for normalized_name, company_data in year_data[year].items():
            # Skip if already processed in EIN matching phase
            if (normalized_name, year) in processed_companies:
                continue
            
            company_name = company_data['company_name']
            ein = company_data['ein'].strip()
            
            # For companies without EIN, try fuzzy matching
            if not ein:
                matches = fuzzy_match(company_name, fuzzy_matcher)
                
                if len(matches) > 1:
                    fuzzy_matches_found += 1
                    logger.info(f"Fuzzy match found for '{company_name}': {len(matches)} matches")
                
                # Check if any matches are already consolidated
                existing_consolidated_name = None
                for match_name in matches:
                    match_normalized = normalize_company_name(match_name)
                    if match_normalized in consolidated_companies:
                        existing_consolidated_name = match_normalized
                        break
                
                if existing_consolidated_name:
                    # Update existing record
                    consolidated_normalized_name = existing_consolidated_name
                else:
                    # Create new consolidated record
                    consolidated_normalized_name = normalized_name
                    consolidated_companies[consolidated_normalized_name] = {
                        'company_name': company_name,
                        'ein': ein,
                        'stripped_company_name': normalize_company_name(company_name)
                    }
                    # Initialize all year columns to 0
                    for init_year in sorted_years:
                        consolidated_companies[consolidated_normalized_name][f'annual_average_employees_{init_year}'] = 0
                        consolidated_companies[consolidated_normalized_name][f'total_hours_worked_{init_year}'] = 0
                
                # Process all fuzzy matches
                for match_name in matches:
                    match_normalized = normalize_company_name(match_name)
                    for check_year, check_companies in year_data.items():
                        if match_normalized in check_companies and (match_normalized, check_year) not in processed_companies:
                            match_company_data = check_companies[match_normalized]
                            
                            # Update year-specific data
                            consolidated_companies[consolidated_normalized_name][f'annual_average_employees_{check_year}'] = match_company_data['annual_average_employees']
                            consolidated_companies[consolidated_normalized_name][f'total_hours_worked_{check_year}'] = match_company_data['total_hours_worked']
                            
                            # Update company name to latest year
                            if check_year >= year:
                                consolidated_companies[consolidated_normalized_name]['company_name'] = match_company_data['company_name']
                                consolidated_companies[consolidated_normalized_name]['stripped_company_name'] = normalize_company_name(match_company_data['company_name'])
                            
                            # Mark as processed
                            processed_companies.add((match_normalized, check_year))
            else:
                # Single-year company with EIN - create individual record
                consolidated_normalized_name = normalized_name
                consolidated_companies[consolidated_normalized_name] = {
                    'company_name': company_name,
                    'ein': ein,
                    'stripped_company_name': normalize_company_name(company_name)
                }
                # Initialize all year columns to 0
                for init_year in sorted_years:
                    consolidated_companies[consolidated_normalized_name][f'annual_average_employees_{init_year}'] = 0
                    consolidated_companies[consolidated_normalized_name][f'total_hours_worked_{init_year}'] = 0
                
                # Set data for this year only
                consolidated_companies[consolidated_normalized_name][f'annual_average_employees_{year}'] = company_data['annual_average_employees']
                consolidated_companies[consolidated_normalized_name][f'total_hours_worked_{year}'] = company_data['total_hours_worked']
                
                processed_companies.add((normalized_name, year))
    
    logger.info(f"Fuzzy matching: Found {fuzzy_matches_found} additional multi-year matches")
    
    logger.info(f"Consolidation complete: {len(consolidated_companies)} unique companies across all years")
    
    # Calculate consolidation stats
    companies_with_multiple_years = 0
    for company_data in consolidated_companies.values():
        years_with_data = 0
        for year in sorted(year_data.keys()):
            if company_data.get(f'annual_average_employees_{year}', 0) > 0:
                years_with_data += 1
        if years_with_data > 1:
            companies_with_multiple_years += 1
    
    logger.info(f"Companies appearing in multiple years: {companies_with_multiple_years}")
    logger.info(f"Companies appearing in only one year: {len(consolidated_companies) - companies_with_multiple_years}")
    
    return consolidated_companies

def process_multi_year_aggregation(osha_files: List[str], output_file: str) -> None:
    """
    Main processing function to aggregate multi-year OSHA data.
    
    Args:
        osha_files: List of paths to OSHA files
        output_file: Path to output file
    """
    # Step 1: Load and aggregate data for each year
    year_data = {}  # year -> {normalized_name -> company_data}
    
    for osha_file in osha_files:
        year, companies = aggregate_single_year_data(osha_file)
        year_data[year] = companies
    
    # Step 2: Consolidate companies across years
    consolidated_companies = consolidate_multi_year_data(year_data)
    
    # Step 3: Create output columns
    sorted_years = sorted(year_data.keys())
    
    base_columns = ['company_name', 'ein', 'stripped_company_name']
    
    # Create year columns grouped by metric type
    employee_columns = [f'annual_average_employees_{year}' for year in sorted_years]
    hours_columns = [f'total_hours_worked_{year}' for year in sorted_years]
    year_columns = employee_columns + hours_columns
    
    all_columns = base_columns + year_columns
    
    # Step 4: Write output file
    logger.info(f"Writing consolidated results to: {output_file}")
    
    try:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_columns, delimiter='|', quoting=csv.QUOTE_NONE, escapechar='\\')
            writer.writeheader()
            
            # Sort by company name for consistent output
            sorted_companies = sorted(consolidated_companies.items(), 
                                    key=lambda x: x[1]['company_name'].lower())
            
            for consolidated_name, company_data in sorted_companies:
                # Create output row with all required columns
                output_row = {}
                for col in all_columns:
                    value = company_data.get(col, 0 if col.startswith(('annual_average_employees_', 'total_hours_worked_')) else '')
                    # Strip quotes and clean up text values
                    if isinstance(value, str):
                        value = value.strip('"').strip("'")
                    output_row[col] = value
                
                writer.writerow(output_row)
        
        logger.info(f"Output complete: {len(consolidated_companies)} companies written")
        
        # Summary statistics
        total_company_years = 0
        for company_data in consolidated_companies.values():
            for year in sorted_years:
                if company_data.get(f'annual_average_employees_{year}', 0) > 0:
                    total_company_years += 1
        
        logger.info(f"Summary: {len(consolidated_companies)} unique companies across {len(sorted_years)} years")
        logger.info(f"Total company-year data points: {total_company_years}")
        
    except Exception as e:
        logger.error(f"Error writing output file: {e}")
        sys.exit(1)

def main():
    """Main function to parse arguments and execute the script."""
    parser = argparse.ArgumentParser(
        description="Aggregate multi-year OSHA data with fuzzy company matching"
    )
    
    parser.add_argument(
        '-i', '--input',
        required=True,
        nargs='+',
        help='Path(s) to OSHA CSV files for multiple years'
    )
    
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Path to output file (pipe-delimited)'
    )
    
    args = parser.parse_args()
    
    logger.info("Starting Multi-Year OSHA Aggregation...")
    logger.info(f"Input files: {', '.join(args.input)}")
    logger.info(f"Output file: {args.output}")
    
    # Validate input files exist
    for input_file in args.input:
        if not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            sys.exit(1)
    
    # Process the aggregation
    process_multi_year_aggregation(args.input, args.output)
    
    logger.info("Multi-year OSHA aggregation completed successfully!")

if __name__ == '__main__':
    main()