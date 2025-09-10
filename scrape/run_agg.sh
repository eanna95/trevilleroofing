#!/bin/bash

# Company Aggregation Runner Script
# Aggregates OSHA data with multiple company lists

echo "Starting company aggregation..."

python3 company_aggregator.py \
    -o ITA_Roofing_2024.csv \
    -a pitchbook_list.tsv top100.tsv \
    -c nrca_list.tsv \
    --output aggregated_companies.tsv

echo "Aggregation complete!"