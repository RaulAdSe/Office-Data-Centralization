#!/usr/bin/env python3
"""
Test script: Scrape a single CYPE element and show all data that would go to the database.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from scraper.template_extraction import CYPEExtractor


async def scrape_single_element(url: str):
    """Scrape a single element and return all extracted data."""

    print("=" * 80)
    print(f"SCRAPING: {url}")
    print("=" * 80)

    async with CYPEExtractor(headless=True, max_combinations=4) as extractor:
        variables, results = await extractor.extract(url)

        return variables, results


def format_for_database(url: str, variables: list, results: list) -> dict:
    """Format extracted data as it would be stored in the database."""

    # Extract element code from URL (last part before .html)
    import re
    # Get the last path segment as the element name/code
    last_segment = url.rstrip('/').split('/')[-1].replace('.html', '')
    element_code = last_segment.replace('_', ' ').title()[:50]  # Clean up for display

    # Determine category from URL
    url_lower = url.lower()
    category_mapping = {
        '/estructuras/hormigon': 'ESTRUCTURA PREFABRICADA',
        '/estructuras/acero': 'ESTRUCTURA METALICA',
        '/cimentaciones/': 'CIMENTACION',
        '/instalaciones/': 'INSTALACION BT',
        '/revestimientos/': 'CUBIERTAS Y FACHADAS',
    }
    category = 'OBRA CIVIL'
    for pattern, cat in category_mapping.items():
        if pattern in url_lower:
            category = cat
            break

    # Format variables for database
    db_variables = []
    for i, var in enumerate(variables):
        var_type = var.variable_type.value if hasattr(var.variable_type, 'value') else str(var.variable_type)

        # Format options
        options = []
        for j, opt in enumerate(var.options):
            options.append({
                'option_value': opt,
                'option_label': opt,
                'is_default': (j == 0),  # First option is default
                'display_order': j
            })

        db_variables.append({
            'variable_name': var.name,
            'variable_type': 'TEXT',  # Database uses TEXT for options stored separately
            'unit': var.unit,
            'default_value': var.default_value,
            'is_required': var.is_required,
            'display_order': i,
            'options': options
        })

    # Format descriptions from combination results
    descriptions = []
    for r in results:
        if r.success and r.description:
            descriptions.append({
                'combination': r.combination.values,
                'strategy': r.combination.strategy,
                'description_text': r.description[:500] + '...' if len(r.description) > 500 else r.description,
                'full_length': len(r.description)
            })

    return {
        'element': {
            'element_code': element_code,
            'element_name': element_code,  # Would be extracted from page title
            'category': category,
            'created_by': 'pipeline'
        },
        'variables': db_variables,
        'description_versions': descriptions
    }


def print_database_data(data: dict):
    """Pretty print the database data."""

    print("\n" + "=" * 80)
    print("DATA FOR DATABASE")
    print("=" * 80)

    # Element table
    print("\n┌─────────────────────────────────────────────────────────────────┐")
    print("│ TABLE: elements                                                 │")
    print("├─────────────────────────────────────────────────────────────────┤")
    elem = data['element']
    print(f"│ element_code: {elem['element_code']:<48} │")
    print(f"│ element_name: {elem['element_name']:<48} │")
    print(f"│ category:     {elem['category']:<48} │")
    print(f"│ created_by:   {elem['created_by']:<48} │")
    print("└─────────────────────────────────────────────────────────────────┘")

    # Variables table
    print("\n┌─────────────────────────────────────────────────────────────────┐")
    print("│ TABLE: element_variables                                        │")
    print("├─────────────────────────────────────────────────────────────────┤")
    for var in data['variables']:
        print(f"│ variable_name:  {var['variable_name'][:45]:<45} │")
        print(f"│ variable_type:  {var['variable_type']:<45} │")
        print(f"│ default_value:  {str(var['default_value'])[:45]:<45} │")
        print(f"│ display_order:  {var['display_order']:<45} │")
        print(f"│ options_count:  {len(var['options']):<45} │")
        print("├─────────────────────────────────────────────────────────────────┤")
    print("└─────────────────────────────────────────────────────────────────┘")

    # Variable options table
    print("\n┌─────────────────────────────────────────────────────────────────┐")
    print("│ TABLE: variable_options                                         │")
    print("├─────────────────────────────────────────────────────────────────┤")
    for var in data['variables']:
        print(f"│ For variable: {var['variable_name'][:48]:<48} │")
        for opt in var['options'][:5]:  # Show first 5 options
            default_mark = "✓" if opt['is_default'] else " "
            print(f"│   [{default_mark}] {opt['option_value'][:55]:<55} │")
        if len(var['options']) > 5:
            print(f"│   ... and {len(var['options']) - 5} more options                                  │")
        print("├─────────────────────────────────────────────────────────────────┤")
    print("└─────────────────────────────────────────────────────────────────┘")

    # Description versions table
    print("\n┌─────────────────────────────────────────────────────────────────┐")
    print("│ TABLE: description_versions                                      │")
    print("├─────────────────────────────────────────────────────────────────┤")
    for i, desc in enumerate(data['description_versions'], 1):
        print(f"│ Combination {i} ({desc['strategy']}):                                   │")
        print(f"│ Values: {str(desc['combination'])[:54]:<54} │")
        print(f"│ Description ({desc['full_length']} chars):                                   │")
        # Wrap description text
        text = desc['description_text']
        for line in [text[j:j+61] for j in range(0, len(text), 61)][:4]:
            print(f"│   {line:<60} │")
        if len(text) > 244:
            print(f"│   ...                                                         │")
        print("├─────────────────────────────────────────────────────────────────┤")
    print("└─────────────────────────────────────────────────────────────────┘")


async def main():
    # Test with EHS010 - concrete pillar with many configuration variables
    url = "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Pilares/EHS010_Pilar_rectangular_o_cuadrado_de_hor.html"

    try:
        variables, results = await scrape_single_element(url)

        print(f"\n✓ Extracted {len(variables)} variables")
        print(f"✓ Generated {len(results)} combination results")

        # Format for database
        db_data = format_for_database(url, variables, results)

        # Pretty print
        print_database_data(db_data)

        # Also output raw JSON
        print("\n" + "=" * 80)
        print("RAW JSON (for programmatic use)")
        print("=" * 80)

        # Convert to JSON-serializable format
        json_data = {
            'element': db_data['element'],
            'variables': db_data['variables'],
            'descriptions': [
                {
                    'combination': d['combination'],
                    'strategy': d['strategy'],
                    'text_preview': d['description_text'][:200] + '...' if len(d['description_text']) > 200 else d['description_text'],
                    'full_length': d['full_length']
                }
                for d in db_data['description_versions']
            ]
        }
        print(json.dumps(json_data, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
