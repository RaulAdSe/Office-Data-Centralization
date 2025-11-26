#!/usr/bin/env python3
"""
Test same element with different variable combinations to see if descriptions change
"""

import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import re

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "core"))

def test_same_element_different_variables():
    """Test if descriptions change for same element with different variables"""
    
    print("🔍 TESTING SAME ELEMENT WITH DIFFERENT VARIABLES")
    print("=" * 60)
    
    # Find an element and test different variable combinations
    base_url = "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html"
    
    print(f"🌐 Base URL: {base_url}")
    
    # Extract base element data
    base_data = extract_element_data(base_url)
    
    if not base_data:
        print("❌ Failed to extract base element")
        return
    
    print(f"✅ Base Element:")
    print(f"   Code: {base_data['code']}")
    print(f"   Title: {base_data['title']}")
    print(f"   Description length: {len(base_data['description'])}")
    print(f"   Variables found: {len(base_data['variables'])}")
    
    # Show first few variables
    print(f"\n📋 Available Variables:")
    for i, var in enumerate(base_data['variables'][:5]):
        print(f"   {i+1}. {var['name']}: {var.get('options', [])[0] if var.get('options') else 'No options'}")
    
    # Test different variable combinations by modifying form data
    test_combinations = generate_test_combinations(base_data['variables'])
    
    print(f"\n🔧 Testing {len(test_combinations)} variable combinations...")
    
    results = []
    
    for i, combination in enumerate(test_combinations):
        print(f"\n--- Combination {i+1}/{len(test_combinations)} ---")
        
        # Extract with this combination
        result = extract_with_combination(base_url, combination)
        
        if result:
            results.append(result)
            print(f"   ✅ Success")
            print(f"   Code: {result['code']}")
            print(f"   Title: {result['title']}")
            print(f"   Description length: {len(result['description'])}")
            print(f"   Variables: {[f'{k}={v}' for k, v in combination.items()][:3]}")
        else:
            print(f"   ❌ Failed")
    
    # Compare descriptions
    if len(results) > 1:
        compare_descriptions(results)
    else:
        print(f"\n❌ Not enough successful extractions to compare")

def extract_element_data(url):
    """Extract element data from URL"""
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract code
        code_pattern = r'([A-Z]{2,3}\d{3})'
        code_match = re.search(code_pattern, response.text)
        code = code_match.group(1) if code_match else "UNKNOWN"
        
        # Extract title
        title_elem = soup.find('h1')
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
        
        # Extract description
        description = extract_description(soup)
        
        # Extract variables from form
        variables = extract_form_variables(soup)
        
        return {
            'code': code,
            'title': title,
            'description': description,
            'variables': variables
        }
        
    except Exception as e:
        print(f"   Error extracting element: {e}")
        return None

def extract_description(soup):
    """Extract description from page"""
    
    # Look for description in common places
    description_selectors = [
        '.descripcionUnidad',
        '.descripcion',
        'p.descripcion',
        'div.descripcion',
        '.texto_descripcion'
    ]
    
    for selector in description_selectors:
        desc_elem = soup.select_one(selector)
        if desc_elem:
            text = desc_elem.get_text(strip=True)
            if len(text) > 50:  # Meaningful description
                return text
    
    # Fallback: look for large text blocks
    for p in soup.find_all('p'):
        text = p.get_text(strip=True)
        if len(text) > 100 and any(word in text.lower() for word in ['hormigón', 'madera', 'acero', 'aplicación']):
            return text
    
    return "No description found"

def extract_form_variables(soup):
    """Extract variables from form inputs"""
    
    variables = []
    
    # Find all select elements
    for select in soup.find_all('select'):
        name = select.get('name', '')
        if not name:
            continue
        
        options = []
        for option in select.find_all('option'):
            value = option.get('value', '')
            text = option.get_text(strip=True)
            if value and text and value != '0':
                options.append(value)
        
        if options:
            variables.append({
                'name': name,
                'options': options,
                'type': 'select'
            })
    
    # Find text inputs and other inputs
    for input_elem in soup.find_all('input'):
        input_type = input_elem.get('type', 'text')
        name = input_elem.get('name', '')
        value = input_elem.get('value', '')
        
        if name and input_type in ['text', 'number', 'hidden']:
            variables.append({
                'name': name,
                'options': [value] if value else [],
                'type': input_type
            })
    
    return variables

def generate_test_combinations(variables):
    """Generate test combinations from available variables"""
    
    # Select variables with multiple options
    multi_option_vars = [v for v in variables if len(v.get('options', [])) > 1]
    
    if not multi_option_vars:
        return []
    
    # Create 3 strategic combinations
    combinations = []
    
    # Combination 1: First option for each variable
    combo1 = {}
    for var in multi_option_vars:
        if var['options']:
            combo1[var['name']] = var['options'][0]
    combinations.append(combo1)
    
    # Combination 2: Last option for each variable
    combo2 = {}
    for var in multi_option_vars:
        if var['options']:
            combo2[var['name']] = var['options'][-1]
    combinations.append(combo2)
    
    # Combination 3: Middle options
    combo3 = {}
    for var in multi_option_vars:
        options = var['options']
        if len(options) > 2:
            combo3[var['name']] = options[len(options)//2]
        elif len(options) == 2:
            combo3[var['name']] = options[1]
    if combo3:
        combinations.append(combo3)
    
    return combinations

def extract_with_combination(base_url, combination):
    """Extract element with specific variable combination"""
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make POST request with form data
        response = requests.post(base_url, data=combination, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract same data as before
        code_pattern = r'([A-Z]{2,3}\d{3})'
        code_match = re.search(code_pattern, response.text)
        code = code_match.group(1) if code_match else "UNKNOWN"
        
        title_elem = soup.find('h1')
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
        
        description = extract_description(soup)
        
        return {
            'code': code,
            'title': title,
            'description': description,
            'combination': combination.copy()
        }
        
    except Exception as e:
        print(f"     Error with combination: {e}")
        return None

def compare_descriptions(results):
    """Compare descriptions from different combinations"""
    
    print(f"\n📊 COMPARING DESCRIPTIONS FROM {len(results)} COMBINATIONS:")
    print("=" * 60)
    
    # Check if all have same code and title
    codes = [r['code'] for r in results]
    titles = [r['title'] for r in results]
    
    print(f"Element codes: {set(codes)}")
    print(f"Element titles: {len(set(titles))} unique")
    
    if len(set(codes)) == 1 and len(set(titles)) == 1:
        print(f"✅ All combinations are the same element: {codes[0]}")
    else:
        print(f"⚠️  Different elements detected")
    
    # Compare descriptions
    descriptions = [r['description'] for r in results]
    unique_descriptions = set(descriptions)
    
    print(f"\nDescription analysis:")
    print(f"   Total descriptions: {len(descriptions)}")
    print(f"   Unique descriptions: {len(unique_descriptions)}")
    print(f"   Description lengths: {[len(d) for d in descriptions]}")
    
    if len(unique_descriptions) > 1:
        print(f"✅ DESCRIPTIONS CHANGE WITH VARIABLES!")
        
        # Show differences
        for i, result in enumerate(results):
            print(f"\n--- Combination {i+1} ---")
            print(f"Variables: {[f'{k}={v}' for k, v in result['combination'].items()][:3]}")
            print(f"Description: {result['description'][:100]}...")
        
        # Find what changes
        find_description_patterns(results)
        
    else:
        print(f"❌ All descriptions are identical")
        print(f"Description: {descriptions[0][:100]}...")

def find_description_patterns(results):
    """Find patterns in description changes"""
    
    print(f"\n🔍 FINDING DESCRIPTION PATTERNS:")
    
    descriptions = [r['description'] for r in results]
    
    # Split descriptions into words
    word_sets = [set(desc.split()) for desc in descriptions]
    
    # Find common words
    common_words = word_sets[0]
    for word_set in word_sets[1:]:
        common_words &= word_set
    
    # Find unique words per description
    unique_words = []
    for i, word_set in enumerate(word_sets):
        unique = word_set - common_words
        unique_words.append(unique)
        print(f"   Combination {i+1} unique words: {sorted(list(unique))[:5]}")
    
    # Try to correlate with variables
    for i, result in enumerate(results):
        print(f"\n   Combination {i+1}:")
        for var_name, var_value in result['combination'].items():
            # Check if variable value appears in description
            if var_value in result['description']:
                print(f"     ✅ {var_name}={var_value} found in description")

if __name__ == "__main__":
    test_same_element_different_variables()