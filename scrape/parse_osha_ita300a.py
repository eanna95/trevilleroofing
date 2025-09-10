#!/usr/bin/env python3
"""
OSHA ITA300A CSV Parser

Parses large OSHA ITA300A CSV files and filters for a subset of companies.
Handles memory efficiently for files up to 100MB+.
"""

import argparse
import csv
import sys
from typing import Set, Dict, Any
import logging
from fuzzy_utils import normalize_company_name

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the columns we want to extract (removed establishment_name, aggregated by company)
OUTPUT_COLUMNS = [
    'company_name', 
    'state',
    'establishment_type',
    'size',
    'annual_average_employees',
    'total_hours_worked',
    'ein',
    'website',
    'match_company_name',
    'stripped_company_name',
    'company_name_multiple_match'
]

# Note: normalize_company_name function is now imported from fuzzy_utils

def aggregate_company_data(rows: list) -> Dict[str, Any]:
    """
    Aggregate multiple establishment rows for the same company.
    
    Args:
        rows: List of dictionaries representing establishment data for the same company
        
    Returns:
        Aggregated data dictionary
    """
    if not rows:
        return {}
    
    # Take the first row as base
    base_row = rows[0].copy()
    
    # Aggregate numeric columns
    total_size = 0
    total_employees = 0
    total_hours = 0
    
    # Collect unique values for ein and establishment_type
    unique_eins = set()
    unique_establishment_types = set()
    
    for row in rows:
        # Aggregate numeric fields (convert to int, handle empty/invalid values)
        try:
            size_val = int(row.get('size', 0) or 0)
            total_size += size_val
        except (ValueError, TypeError):
            pass
            
        try:
            emp_val = int(row.get('annual_average_employees', 0) or 0)
            total_employees += emp_val
        except (ValueError, TypeError):
            pass
            
        try:
            hours_val = int(row.get('total_hours_worked', 0) or 0)
            total_hours += hours_val
        except (ValueError, TypeError):
            pass
        
        # Collect unique values
        ein = row.get('ein', '').strip()
        if ein:
            unique_eins.add(ein)
        
        est_type = row.get('establishment_type', '').strip()
        if est_type:
            unique_establishment_types.add(est_type)
    
    # Update aggregated values
    base_row['size'] = str(total_size)
    base_row['annual_average_employees'] = str(total_employees)
    base_row['total_hours_worked'] = str(total_hours)
    
    # Handle unique values - if multiple, create comma-separated list
    base_row['ein'] = ', '.join(sorted(unique_eins)) if unique_eins else ''
    base_row['establishment_type'] = ', '.join(sorted(unique_establishment_types)) if unique_establishment_types else ''
    
    # Remove establishment_name if it exists
    if 'establishment_name' in base_row:
        del base_row['establishment_name']
    
    return base_row

def load_filter_companies(filter_file: str) -> tuple[Dict[str, list], Set[str], Dict[str, str]]:
    """
    Load company names from the filter file and create normalized mapping.
    
    Args:
        filter_file: Path to the pipe-delimited filter CSV file
        
    Returns:
        Tuple of (normalized_to_original_mapping, normalized_names_set, normalized_to_website_mapping)
    """
    normalized_to_original = {}
    normalized_names = set()
    normalized_to_website = {}
    
    logger.info(f"Loading company filter list from: {filter_file}")
    try:
        with open(filter_file, 'r', encoding='utf-8-sig') as f:  # Handle BOM
            reader = csv.DictReader(f, delimiter='|')
            row_count = 0
            empty_count = 0
            
            for row in reader:
                row_count += 1
                company_name = row.get('company_name', '').strip()
                website = row.get('website', '').strip()
                
                if not company_name:
                    empty_count += 1
                    if empty_count <= 5:  # Log first few empty entries for debugging
                        logger.debug(f"Row {row_count}: Empty company_name, full row: {dict(row)}")
                    continue
                    
                normalized = normalize_company_name(company_name)
                if normalized:
                    if normalized not in normalized_to_original:
                        normalized_to_original[normalized] = []
                    # Only add if not already in the list (avoid duplicates)
                    if company_name not in normalized_to_original[normalized]:
                        normalized_to_original[normalized].append(company_name)
                    normalized_names.add(normalized)
                    
                    # Store website if available (first one wins if multiple matches)
                    if website and normalized not in normalized_to_website:
                        normalized_to_website[normalized] = website
                else:
                    logger.warning(f"Could not normalize company name: '{company_name}'")
            
            logger.info(f"Filter file '{filter_file}': Processed {row_count} rows, {empty_count} had empty company names")
                    
        total_original = sum(len(originals) for originals in normalized_to_original.values())
        logger.info(f"Filter file '{filter_file}': Loaded {len(normalized_names)} normalized companies from {total_original} original names")
        logger.info(f"Filter file '{filter_file}': Loaded {len(normalized_to_website)} companies with website data")
        return normalized_to_original, normalized_names, normalized_to_website
        
    except FileNotFoundError:
        logger.error(f"Filter file not found: {filter_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading filter file: {e}")
        sys.exit(1)

def process_osha_data(input_file: str, output_file: str, normalized_to_original: Dict[str, list], normalized_names: Set[str], normalized_to_website: Dict[str, str]) -> None:
    """
    Process the OSHA data file and write filtered, aggregated results by company.
    
    Args:
        input_file: Path to the input OSHA CSV file
        output_file: Path to the output pipe-delimited CSV file
        normalized_to_original: Mapping from normalized names to original names
        normalized_names: Set of normalized company names to filter for
        normalized_to_website: Mapping from normalized names to websites
    """
    processed_count = 0
    matched_count = 0
    
    # Collect all matching rows grouped by company name
    company_rows = {}  # normalized_company_name -> [list of matching rows]
    
    try:
        # First pass: collect all matching rows
        with open(input_file, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            # Process each row
            for row in reader:
                processed_count += 1
                
                # Log progress every 10,000 rows
                if processed_count % 10000 == 0:
                    logger.info(f"OSHA file '{input_file}': Processed {processed_count} rows, matched {matched_count}")
                
                company_name = row.get('company_name', '').strip()
                
                # Normalize the OSHA company name for matching
                normalized_osha_name = normalize_company_name(company_name)
                
                # Check if this normalized company name is in our filter set
                if normalized_osha_name in normalized_names:
                    matched_count += 1
                    
                    # Get the original filter list company names that match
                    filter_list_names = normalized_to_original[normalized_osha_name]
                    # Use single quotes to avoid CSV escaping issues with double quotes
                    filter_list_company_name = ', '.join(f"'{name}'" for name in filter_list_names)
                    
                    # Determine if there are multiple matches (filter list has more than 1 company)
                    has_multiple_match = len(filter_list_names) > 1
                    
                    # Create enhanced row with metadata
                    enhanced_row = row.copy()
                    enhanced_row['match_company_name'] = filter_list_company_name
                    enhanced_row['stripped_company_name'] = normalized_osha_name
                    enhanced_row['company_name_multiple_match'] = str(has_multiple_match).lower()
                    enhanced_row['website'] = normalized_to_website.get(normalized_osha_name, '')
                    
                    # Group by normalized company name for aggregation
                    if normalized_osha_name not in company_rows:
                        company_rows[normalized_osha_name] = []
                    company_rows[normalized_osha_name].append(enhanced_row)
        
        logger.info(f"OSHA file '{input_file}': Processing complete. Processed {processed_count} total rows, matched {matched_count} establishments")
        logger.info(f"Found {len(company_rows)} unique companies after aggregation")
        
        # Second pass: aggregate and write results
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=OUTPUT_COLUMNS, delimiter='|')
            writer.writeheader()
            
            aggregated_companies = 0
            for normalized_name, rows in company_rows.items():
                # Aggregate the rows for this company
                aggregated_row = aggregate_company_data(rows)
                
                # Filter to only include OUTPUT_COLUMNS
                output_row = {}
                for col in OUTPUT_COLUMNS:
                    output_row[col] = aggregated_row.get(col, '')
                
                writer.writerow(output_row)
                aggregated_companies += 1
            
            logger.info(f"Wrote {aggregated_companies} aggregated company records to output file")
        
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        sys.exit(1)

def process_from_filter(input_file: str, output_file: str, normalized_to_original: Dict[str, list], normalized_names: Set[str], normalized_to_website: Dict[str, str], filter_file: str) -> None:
    """
    Process from filter list - create output rows for each filter company.
    
    Args:
        input_file: Path to the input OSHA CSV file
        output_file: Path to the output pipe-delimited CSV file
        normalized_to_original: Mapping from normalized names to original filter names
        normalized_names: Set of normalized company names from filter
        filter_file: Path to filter file (to get additional filter data)
    """
    # First, load all OSHA data into memory with normalized names
    osha_data = {}  # normalized_name -> [list of matching osha rows]
    all_osha_normalized = set()  # Track all normalized OSHA names
    
    logger.info(f"Loading OSHA data into memory from: {input_file}")
    total_osha_rows = 0
    matched_osha_rows = 0
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_osha_rows += 1
                company_name = row.get('company_name', '').strip()
                if company_name:
                    normalized_osha_name = normalize_company_name(company_name)
                    all_osha_normalized.add(normalized_osha_name)
                    
                    if normalized_osha_name in normalized_names:
                        matched_osha_rows += 1
                        if normalized_osha_name not in osha_data:
                            osha_data[normalized_osha_name] = []
                        osha_data[normalized_osha_name].append(row)
    except Exception as e:
        logger.error(f"Error reading OSHA data from '{input_file}': {e}")
        sys.exit(1)
    
    logger.info(f"OSHA file '{input_file}': Processed {total_osha_rows} total rows")
    logger.info(f"OSHA file '{input_file}': Found {len(all_osha_normalized)} unique normalized company names")
    logger.info(f"Filter matching: Found {len(normalized_names)} unique normalized company names in filter data")
    logger.info(f"Filter matching: Found {matched_osha_rows} OSHA establishment records matching filter companies")
    logger.info(f"Filter matching: These records represent {len(osha_data)} unique companies (by normalized name)")
    
    # Now process filter companies
    processed_filter_count = 0
    output_row_count = 0
    
    try:
        with open(filter_file, 'r', encoding='utf-8-sig') as filter_f, \
             open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            
            filter_reader = csv.DictReader(filter_f, delimiter='|')
            writer = csv.DictWriter(outfile, fieldnames=OUTPUT_COLUMNS, delimiter='|')
            writer.writeheader()
            
            for filter_row in filter_reader:
                processed_filter_count += 1
                filter_company_name = filter_row.get('company_name', '').strip()
                filter_state = filter_row.get('state', '').strip()
                
                if not filter_company_name:
                    continue
                
                normalized_filter_name = normalize_company_name(filter_company_name)
                
                # Get matching OSHA rows
                matching_osha_rows = osha_data.get(normalized_filter_name, [])
                
                if matching_osha_rows:
                    # Aggregate multiple OSHA rows for this company
                    osha_company_names = []
                    for osha_row in matching_osha_rows:
                        osha_company_names.append(osha_row.get('company_name', '').strip())
                    
                    has_multiple_match = len(set(osha_company_names)) > 1
                    
                    # Create enhanced rows with metadata for aggregation
                    enhanced_rows = []
                    for osha_row in matching_osha_rows:
                        enhanced_row = osha_row.copy()
                        enhanced_row['company_name'] = filter_company_name
                        enhanced_row['state'] = filter_state
                        enhanced_row['match_company_name'] = f"'{osha_row.get('company_name', '').strip()}'"
                        enhanced_row['stripped_company_name'] = normalized_filter_name
                        enhanced_row['company_name_multiple_match'] = str(has_multiple_match).lower()
                        enhanced_row['website'] = normalized_to_website.get(normalized_filter_name, '')
                        enhanced_rows.append(enhanced_row)
                    
                    # Aggregate the data
                    aggregated_row = aggregate_company_data(enhanced_rows)
                    
                    # Write aggregated row
                    output_row_count += 1
                    output_row = {}
                    for col in OUTPUT_COLUMNS:
                        output_row[col] = aggregated_row.get(col, '')
                    
                    writer.writerow(output_row)
                else:
                    # No OSHA matches - create blank row with filter info
                    output_row_count += 1
                    output_row = {}
                    
                    for col in OUTPUT_COLUMNS:
                        if col == 'company_name':
                            output_row[col] = filter_company_name
                        elif col == 'state':
                            output_row[col] = filter_state
                        elif col == 'match_company_name':
                            output_row[col] = ''
                        elif col == 'stripped_company_name':
                            output_row[col] = normalized_filter_name
                        elif col == 'company_name_multiple_match':
                            output_row[col] = 'false'
                        elif col == 'website':
                            output_row[col] = normalized_to_website.get(normalized_filter_name, '')
                        else:
                            output_row[col] = ''
                    
                    writer.writerow(output_row)
    
        logger.info(f"Filter processing complete. Processed {processed_filter_count} filter companies from '{filter_file}', created {output_row_count} aggregated company records")
        
    except Exception as e:
        logger.error(f"Error processing from filter: {e}")
        sys.exit(1)

def main():
    """Main function to parse arguments and execute the script."""
    parser = argparse.ArgumentParser(
        description="Parse OSHA ITA300A CSV file and filter for specific companies"
    )
    
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Input OSHA ITA300A CSV file path'
    )
    
    parser.add_argument(
        '--filter',
        required=True,
        help='Pipe-delimited CSV file containing companies to filter for'
    )
    
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output pipe-delimited CSV file path'
    )
    
    parser.add_argument(
        '--from',
        choices=['input', 'filter'],
        default='input',
        dest='from_source',
        help='Process from input file (default) or filter file companies'
    )
    
    args = parser.parse_args()
    
    logger.info("Starting OSHA ITA300A processing...")
    logger.info(f"Input file: {args.input}")
    logger.info(f"Filter file: {args.filter}")
    logger.info(f"Output file: {args.output}")
    
    # Load the companies to filter for
    normalized_to_original, normalized_names, normalized_to_website = load_filter_companies(args.filter)
    
    if not normalized_names:
        logger.error("No companies found in filter file")
        sys.exit(1)
    
    # Process the data based on the selected mode
    if args.from_source == 'filter':
        process_from_filter(args.input, args.output, normalized_to_original, normalized_names, normalized_to_website, args.filter)
    else:
        process_osha_data(args.input, args.output, normalized_to_original, normalized_names, normalized_to_website)
    
    logger.info("Processing completed successfully!")

if __name__ == '__main__':
    main()