#!/usr/bin/env python3
"""
Analyze the actual HTML structure to understand variable grouping
"""

import sys
sys.path.insert(0, 'core')

from page_detector import fetch_page
from bs4 import BeautifulSoup

def analyze_variable_structure():
    """Analyze how variables are structured in the HTML"""
    
    url = "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Esmaltes/Esmalte_al_agua_para_madera.html"
    
    print("🔍 ANALYZING VARIABLE HTML STRUCTURE")
    print("="*60)
    print(f"URL: {url}")
    print()
    
    # Fetch page
    html = fetch_page(url)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all radio buttons and group them
    print("📋 RADIO BUTTON ANALYSIS:")
    print("-" * 40)
    
    radio_inputs = soup.find_all('input', type='radio')
    radio_groups = {}
    
    for radio in radio_inputs:
        name = radio.get('name', 'unnamed')
        value = radio.get('value')
        
        if name not in radio_groups:
            radio_groups[name] = []
        
        # Try to find the label for this radio button
        label_text = find_radio_label(radio, soup)
        
        radio_groups[name].append({
            'value': value,
            'label': label_text,
            'checked': radio.has_attr('checked')
        })
    
    # Show radio groups
    for group_name, options in radio_groups.items():
        print(f"\n🔘 Group '{group_name}': {len(options)} options")
        for i, option in enumerate(options, 1):
            checked = "✓" if option['checked'] else " "
            print(f"   {i}. [{checked}] {option['value']} - {option['label'][:50]}...")
    
    print(f"\nFound {len(radio_groups)} radio groups with {sum(len(opts) for opts in radio_groups.values())} total options")
    
    return radio_groups

def find_radio_label(input_elem, soup):
    """Find label text for a radio input"""
    # Method 1: Look for <label> tag
    label = soup.find('label', {'for': input_elem.get('id')}) if input_elem.get('id') else None
    if label:
        return label.get_text(strip=True)
    
    # Method 2: Look for parent label
    parent = input_elem.parent
    if parent and parent.name == 'label':
        return parent.get_text(strip=True)
    
    # Method 3: Look for sibling text
    next_sibling = input_elem.next_sibling
    if next_sibling and hasattr(next_sibling, 'strip'):
        text = next_sibling.strip()
        if text:
            return text
    
    # Method 4: Look in parent context
    if parent:
        parent_text = parent.get_text(strip=True)
        if parent_text and len(parent_text) < 100:  # Reasonable length
            return parent_text
    
    return "Unknown"

if __name__ == "__main__":
    analyze_variable_structure()