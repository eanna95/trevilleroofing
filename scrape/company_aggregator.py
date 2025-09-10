#!/usr/bin/env python3
"""
Company Aggregator Script

Aggregates company data from OSHA file and matches with additional company files using fuzzy logic.
Combines data from multiple sources while avoiding duplicates through intelligent matching.
"""

import argparse
import csv
import sys
import os
import logging
from typing import Dict, List, Set, Any
from fuzzy_utils import normalize_company_name, create_fuzzy_matcher, fuzzy_match

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def aggregate_osha_data(osha_file: str) -> Dict[str, Dict[str, Any]]:
    """
    Load consolidated OSHA data (from osha_aggregator.py output or single-year data).
    
    Args:
        osha_file: Path to the OSHA CSV file (consolidated or single-year)
        
    Returns:
        Dictionary mapping normalized company names to aggregated data
    """
    logger.info(f"Loading OSHA data from: {osha_file}")
    
    total_rows = 0
    companies = {}
    
    try:
        # Determine delimiter based on file extension
        osha_delimiter = '|' if osha_file.endswith('.tsv') else ','
        logger.info(f"Using delimiter '{osha_delimiter}' for OSHA file (detected from extension)")
        
        with open(osha_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=osha_delimiter)
            
            # Check if this is consolidated multi-year data or single-year data
            fieldnames = reader.fieldnames or []
            is_consolidated = any('annual_average_employees_' in col for col in fieldnames)
            
            if is_consolidated:
                logger.info("Detected consolidated multi-year OSHA data format")
                logger.info(f"Sample columns: {fieldnames[:5]}...")
            else:
                logger.info("Detected single-year OSHA data format")
            
            for row in reader:
                total_rows += 1
                company_name = row.get('company_name', '').strip()
                
                if not company_name:
                    continue
                
                # Create normalized key for matching
                normalized_name = normalize_company_name(company_name)
                
                if is_consolidated:
                    # Multi-year consolidated data - keep all original columns only
                    company_data = dict(row)  # Copy all columns exactly as they are
                    company_data['osha_company_name'] = company_name
                    
                    # Don't add calculated totals - just use the data as-is
                    
                else:
                    # Single-year data - aggregate by company name first
                    if normalized_name not in companies:
                        companies[normalized_name] = {
                            'rows': [],
                            'company_name': company_name
                        }
                    companies[normalized_name]['rows'].append(row)
                    continue  # Skip to next row, we'll process later
                
                companies[normalized_name] = company_data
                
                # Log progress every 1000 rows
                if total_rows % 1000 == 0:
                    logger.info(f"Processed {total_rows} OSHA rows...")
        
        # If single-year data, aggregate it now
        if not is_consolidated:
            logger.info("Aggregating single-year data by company name...")
            aggregated_companies = {}
            
            for normalized_name, company_info in companies.items():
                company_name = company_info['company_name']
                rows = company_info['rows']
                
                # Aggregate numeric fields
                total_employees = 0
                total_hours = 0
                unique_eins = set()
                
                for row in rows:
                    # Aggregate annual_average_employees
                    try:
                        emp_val = int(float(row.get('annual_average_employees', 0) or 0))
                        total_employees += emp_val
                    except (ValueError, TypeError):
                        pass
                    
                    # Aggregate total_hours_worked
                    try:
                        hours_val = int(float(row.get('total_hours_worked', 0) or 0))
                        total_hours += hours_val
                    except (ValueError, TypeError):
                        pass
                    
                    # Collect unique EINs
                    ein = row.get('ein', '').strip()
                    if ein:
                        unique_eins.add(ein)
                
                # Store aggregated data
                aggregated_companies[normalized_name] = {
                    'osha_company_name': company_name,
                    'annual_average_employees': total_employees,
                    'total_hours_worked': total_hours,
                    'total_annual_average_employees': total_employees,
                    'total_total_hours_worked': total_hours,
                    'ein': ', '.join(sorted(unique_eins)) if unique_eins else '',
                    'stripped_company_name': normalized_name
                }
            
            companies = aggregated_companies
        
        logger.info(f"OSHA file: Processed {total_rows} total rows")
        logger.info(f"OSHA file: Found {len(companies)} unique companies")
        
        return companies
        
    except FileNotFoundError:
        logger.error(f"OSHA file not found: {osha_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error processing OSHA file: {e}")
        sys.exit(1)

def load_added_file(added_file: str) -> List[Dict[str, str]]:
    """
    Load an additional company file.
    
    Args:
        added_file: Path to the additional company file
        
    Returns:
        List of company records
    """
    logger.info(f"Loading additional company file: {added_file}")
    
    companies = []
    
    try:
        # Determine delimiter based on file extension
        delimiter = '|' if added_file.endswith('.tsv') else ','
        logger.info(f"Using delimiter '{delimiter}' for added file (detected from extension)")
        
        with open(added_file, 'r', encoding='utf-8-sig') as f:  # Handle BOM
            reader = csv.DictReader(f, delimiter=delimiter)
            
            # Log detected columns for debugging
            logger.info(f"Detected columns in '{added_file}': {reader.fieldnames}")
            
            total_rows = 0
            empty_rows = 0
            
            for row in reader:
                total_rows += 1
                company_name = row.get('company_name', '').strip()
                
                if not company_name:
                    empty_rows += 1
                    # Log first few empty rows for debugging
                    if empty_rows <= 10:
                        logger.debug(f"Empty company_name in row {total_rows}: {dict(row)}")
                    continue
                
                companies.append({
                    'company_name': company_name,
                    'website': row.get('website', '').strip()
                })
            
            logger.info(f"Added file '{added_file}': Processed {total_rows} total rows, {empty_rows} empty, {len(companies)} valid companies")
        
        logger.info(f"Added file '{added_file}': Loaded {len(companies)} companies")
        return companies
        
    except FileNotFoundError:
        logger.error(f"Added file not found: {added_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading added file '{added_file}': {e}")
        sys.exit(1)

def process_company_aggregation(osha_file: str, added_files: List[str], combine_files: List[str], output_file: str) -> None:
    """
    Main processing function to aggregate and match company data.
    
    Args:
        osha_file: Path to OSHA file
        added_files: List of paths to additional company files (creates new rows for unmatched)
        combine_files: List of paths to combine files (only updates existing rows)
        output_file: Path to output file
    """
    # Step 1: Aggregate OSHA data
    osha_companies = aggregate_osha_data(osha_file)
    
    # Step 2: Load all added and combine files
    added_data = {}  # file_prefix -> list of companies
    combine_data = {}  # file_prefix -> list of companies
    
    for added_file in added_files:
        file_prefix = os.path.splitext(os.path.basename(added_file))[0]
        added_data[file_prefix] = load_added_file(added_file)
    
    for combine_file in combine_files:
        file_prefix = os.path.splitext(os.path.basename(combine_file))[0]
        combine_data[file_prefix] = load_added_file(combine_file)
    
    # Step 3: Create fuzzy matcher for OSHA companies
    osha_company_names = [data['osha_company_name'] for data in osha_companies.values()]
    osha_matcher = create_fuzzy_matcher(osha_company_names)
    
    # Step 4: Create dynamic column list based on OSHA data format
    
    # Detect all OSHA columns from first company
    sample_osha_data = next(iter(osha_companies.values())) if osha_companies else {}
    
    # Get all OSHA columns exactly as they appear in the data
    all_osha_columns = list(sample_osha_data.keys()) if sample_osha_data else []
    
    # Separate different types of columns for proper ordering
    base_cols = []
    year_cols = []
    other_cols = []
    
    for col in all_osha_columns:
        if col in ['company_name', 'ein']:
            base_cols.append(col)
        elif 'annual_average_employees_' in col or 'total_hours_worked_' in col:
            year_cols.append(col)
        else:
            other_cols.append(col)
    
    # Sort year columns to maintain consistent order
    year_cols.sort()
    
    # Create ordered OSHA columns: company_name, ein, year columns, other columns
    osha_columns = []
    if 'company_name' in base_cols:
        osha_columns.append('company_name')
    if 'ein' in base_cols:
        osha_columns.append('ein')
    osha_columns.extend(year_cols)
    
    year_columns = year_cols
    
    # Create file-specific columns in the requested order
    website_columns = []
    file_company_columns = []
    all_file_data = {**added_data, **combine_data}  # Merge both dictionaries
    
    # First collect all website columns
    for file_prefix in all_file_data.keys():
        has_website = any(company.get('website') for company in all_file_data[file_prefix])
        if has_website:
            website_columns.append(f"{file_prefix}_website")
    
    # Then collect all company name columns
    for file_prefix in all_file_data.keys():
        file_company_columns.append(f"{file_prefix}_company_name")
    
    # Final column order: company_name, ein, year columns, websites, file company names, everything else, stripped_company_name
    final_columns = osha_columns  # starts with company_name, ein, year columns
    final_columns.extend(website_columns)
    final_columns.extend(file_company_columns)
    
    # Add remaining columns (except stripped_company_name)
    remaining_cols = [col for col in other_cols if col != 'stripped_company_name']
    final_columns.extend(remaining_cols)
    
    # Add stripped_company_name last
    if 'stripped_company_name' in other_cols:
        final_columns.append('stripped_company_name')
    
    all_columns = final_columns
    dynamic_columns = website_columns + file_company_columns
    
    logger.info(f"Output columns: {len(all_columns)} total columns")
    if year_columns:
        logger.info(f"Multi-year columns detected: {len(year_columns)} year-specific columns")
    
    # Step 5: Process matches and create final dataset
    final_companies = {}  # normalized_name -> complete record
    matched_companies = set()  # Track which added companies were matched
    
    # Start with OSHA companies
    for normalized_name, osha_data in osha_companies.items():
        final_companies[normalized_name] = osha_data.copy()
        
        # Initialize the consolidated company_name column (will be set later)
        final_companies[normalized_name]['company_name'] = ''
        
        # Initialize all dynamic columns to empty
        for col in dynamic_columns:
            final_companies[normalized_name][col] = ''
    
    # Step 6: Match added companies to OSHA companies (can create new rows)
    for file_prefix, companies in added_data.items():
        logger.info(f"Matching companies from added file: {file_prefix}")
        
        matched_in_this_file = 0
        new_companies_in_this_file = 0
        
        for company in companies:
            company_name = company['company_name']
            website = company.get('website', '')
            
            # Try to find fuzzy match with OSHA companies
            matches = fuzzy_match(company_name, osha_matcher)
            
            if matches:
                # Found match - update existing OSHA company
                matched_in_this_file += 1
                
                # Find the normalized name for this match
                for norm_name, osha_data in osha_companies.items():
                    if osha_data['osha_company_name'] in matches:
                        final_companies[norm_name][f"{file_prefix}_company_name"] = company_name
                        if website and f"{file_prefix}_website" in dynamic_columns:
                            final_companies[norm_name][f"{file_prefix}_website"] = website
                        break
                
                matched_companies.add(company_name)
            else:
                # No match found - create new company row
                new_companies_in_this_file += 1
                normalized_name = normalize_company_name(company_name)
                
                if normalized_name not in final_companies:
                    # Create new company record with same structure as OSHA data
                    new_record = {
                        'company_name': '',  # Will be set later
                        'osha_company_name': '',
                        'ein': '',
                        'stripped_company_name': normalized_name
                    }
                    
                    # Initialize all OSHA columns that exist in the data to empty/0
                    if sample_osha_data:
                        for col in sample_osha_data.keys():
                            if col not in ['company_name', 'osha_company_name', 'ein', 'stripped_company_name']:
                                # Initialize numeric columns to 0, others to empty string
                                if 'annual_average_employees' in col or 'total_hours_worked' in col:
                                    new_record[col] = 0
                                else:
                                    new_record[col] = ''
                    
                    # Initialize all dynamic columns to empty
                    for col in dynamic_columns:
                        new_record[col] = ''
                    
                    # Set the specific columns for this file
                    new_record[f"{file_prefix}_company_name"] = company_name
                    if website and f"{file_prefix}_website" in dynamic_columns:
                        new_record[f"{file_prefix}_website"] = website
                    
                    final_companies[normalized_name] = new_record
                else:
                    # Update existing record (in case multiple added files have same company)
                    final_companies[normalized_name][f"{file_prefix}_company_name"] = company_name
                    if website and f"{file_prefix}_website" in dynamic_columns:
                        final_companies[normalized_name][f"{file_prefix}_website"] = website
        
        logger.info(f"Added file '{file_prefix}': Matched {matched_in_this_file} companies to existing data")
        logger.info(f"Added file '{file_prefix}': Added {new_companies_in_this_file} new companies")
    
    # Step 6b: Match combine companies to existing companies (no new rows)
    for file_prefix, companies in combine_data.items():
        logger.info(f"Matching companies from combine file: {file_prefix}")
        
        matched_in_this_file = 0
        
        for company in companies:
            company_name = company['company_name']
            website = company.get('website', '')
            
            # Try to find fuzzy match with existing companies
            matches = fuzzy_match(company_name, osha_matcher)
            
            if matches:
                # Found match - update existing company
                matched_in_this_file += 1
                
                # Find the normalized name for this match
                for norm_name, existing_data in final_companies.items():
                    if existing_data['osha_company_name'] in matches:
                        final_companies[norm_name][f"{file_prefix}_company_name"] = company_name
                        if website and f"{file_prefix}_website" in dynamic_columns:
                            final_companies[norm_name][f"{file_prefix}_website"] = website
                        break
            # NOTE: No else clause - combine files don't create new rows for unmatched companies
        
        logger.info(f"Combine file '{file_prefix}': Matched {matched_in_this_file} companies to existing data")
        logger.info(f"Combine file '{file_prefix}': Skipped {len(companies) - matched_in_this_file} unmatched companies (no new rows created)")
    
    # Step 7: Ensure every row has a company_name
    logger.info("Ensuring all companies have primary company_name...")
    
    for normalized_name, company_data in final_companies.items():
        # Priority order for company_name: existing company_name, osha_company_name, then added file names
        if not company_data.get('company_name', '').strip():
            # Try osha_company_name first
            if company_data.get('osha_company_name', '').strip():
                final_companies[normalized_name]['company_name'] = company_data['osha_company_name'].strip()
            else:
                # Find first non-empty company name from added files
                for file_prefix in added_data.keys():
                    col = f"{file_prefix}_company_name"
                    if col in company_data and company_data[col].strip():
                        final_companies[normalized_name]['company_name'] = company_data[col].strip()
                        break
    
    # Step 8: Write output file
    logger.info(f"Writing aggregated results to: {output_file}")
    
    try:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_columns, delimiter='|')
            writer.writeheader()
            
            # Sort by company name for consistent output
            sorted_companies = sorted(final_companies.items(), 
                                    key=lambda x: x[1].get('osha_company_name') or x[1].get('stripped_company_name'))
            
            for normalized_name, company_data in sorted_companies:
                writer.writerow(company_data)
        
        logger.info(f"Output complete: {len(final_companies)} total companies written")
        
        # Summary statistics
        osha_only = sum(1 for data in final_companies.values() if data['osha_company_name'])
        added_only = sum(1 for data in final_companies.values() if not data['osha_company_name'])
        
        logger.info(f"Summary: {osha_only} companies from OSHA data, {added_only} companies added from additional files")
        
    except Exception as e:
        logger.error(f"Error writing output file: {e}")
        sys.exit(1)

def main():
    """Main function to parse arguments and execute the script."""
    parser = argparse.ArgumentParser(
        description="Aggregate company data from OSHA file and additional company files using fuzzy matching"
    )
    
    parser.add_argument(
        '-o', '--osha',
        required=True,
        help='Path to OSHA CSV file (pipe-delimited)'
    )
    
    parser.add_argument(
        '-a', '--added',
        nargs='*',
        default=[],
        help='Path(s) to additional company files (CSV or pipe-delimited) - will add new rows for unmatched companies'
    )
    
    parser.add_argument(
        '-c', '--combine',
        nargs='*',
        default=[],
        help='Path(s) to company files to combine (CSV or pipe-delimited) - will NOT add new rows for unmatched companies, only update existing ones'
    )
    
    parser.add_argument(
        '--output',
        required=True,
        help='Path to output file (pipe-delimited)'
    )
    
    args = parser.parse_args()
    
    logger.info("Starting Company Aggregation...")
    logger.info(f"OSHA file: {args.osha}")
    logger.info(f"Added files: {', '.join(args.added) if args.added else 'None'}")
    logger.info(f"Combine files: {', '.join(args.combine) if args.combine else 'None'}")
    logger.info(f"Output file: {args.output}")
    
    # Validate that at least one of added or combine is specified
    if not args.added and not args.combine:
        logger.error("Must specify at least one of --added (-a) or --combine (-c) files")
        sys.exit(1)
    
    # Validate input files exist
    if not os.path.exists(args.osha):
        logger.error(f"OSHA file not found: {args.osha}")
        sys.exit(1)
    
    for added_file in args.added:
        if not os.path.exists(added_file):
            logger.error(f"Added file not found: {added_file}")
            sys.exit(1)
    
    for combine_file in args.combine:
        if not os.path.exists(combine_file):
            logger.error(f"Combine file not found: {combine_file}")
            sys.exit(1)
    
    # Process the aggregation
    process_company_aggregation(args.osha, args.added, args.combine, args.output)
    
    logger.info("Company aggregation completed successfully!")

if __name__ == '__main__':
    main()