# Template Extraction System

This module extracts description templates from CYPE elements by analyzing how descriptions change with different variable combinations.

## Components

- `combination_generator.py` - Generates all possible variable combinations
- `description_collector.py` - Scrapes descriptions for different variable states  
- `pattern_analyzer.py` - Finds patterns and placeholders in descriptions
- `template_extractor.py` - Extracts final templates with dependencies
- `dependency_detector.py` - Handles complex variable dependencies
- `template_validator.py` - Tests extracted templates

## Process

1. Generate variable combinations for an element
2. Scrape description for each combination
3. Analyze patterns to find placeholders
4. Extract template with proper placeholder names
5. Detect and handle variable dependencies
6. Validate template accuracy