#!/usr/bin/env python3
"""
Test related CYPE elements to understand if they're variations of same element or different elements
"""

import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import re

# Add paths  
sys.path.insert(0, str(Path(__file__).parent / "core"))

def test_related_cype_elements():
    """Test related elements from same category to understand CYPE structure"""
    
    print("🔍 TESTING RELATED CYPE ELEMENTS")
    print("=" * 60)
    
    # Related viga (beam) elements from the inspection
    related_urls = [
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html",
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_de_hormigon_armado.html", 
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Sistema_de_encofrado_para_viga.html"
    ]
    
    print(f"🌐 Testing {len(related_urls)} related elements:")
    
    results = []
    
    for i, url in enumerate(related_urls):
        print(f"\n--- Element {i+1}/{len(related_urls)} ---")
        print(f"URL: {url.split('/')[-1]}")
        
        element_data = extract_element_data(url)
        
        if element_data:
            results.append(element_data)
            print(f"✅ Success")
            print(f"   Code: {element_data['code']}")
            print(f"   Title: {element_data['title']}")
            print(f"   Price: {element_data.get('price', 'N/A')}")
            print(f"   Description length: {len(element_data['description'])}")
            
            # Show key variables if any
            if element_data.get('variables'):
                var_names = [v['name'] for v in element_data['variables'][:3]]
                print(f"   Variables: {var_names}")
                
        else:
            print(f"❌ Failed to extract")
    
    # Analyze results
    if len(results) >= 2:
        analyze_element_relationships(results)
    
    # Test if elements have actual variable configurations within the page
    print(f"\n🔧 TESTING INTERNAL VARIABLE CONFIGURATIONS:")
    test_internal_variables(related_urls[0])  # Test first element

def extract_element_data(url):
    """Extract comprehensive element data"""
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract element code
        code_pattern = r'([A-Z]{2,3}\d{3})'
        code_match = re.search(code_pattern, response.text)
        code = code_match.group(1) if code_match else "UNKNOWN"
        
        # Extract title
        title_elem = soup.find('h1')
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
        
        # Extract description (look for technical description)
        description = extract_technical_description(soup)
        
        # Extract price
        price = extract_price(soup)
        
        # Look for actual variable configuration elements (not navigation)
        variables = find_configuration_variables(soup)
        
        return {
            'url': url,
            'code': code,
            'title': title,
            'description': description,
            'price': price,
            'variables': variables
        }
        
    except Exception as e:
        print(f"   Error: {e}")
        return None

def extract_technical_description(soup):
    """Extract the technical description from CYPE page"""
    
    # Common CYPE description patterns
    description_patterns = [
        # Direct description text
        lambda s: s.find('div', class_='descripcion'),
        lambda s: s.find('p', class_='descripcion'),
        lambda s: s.find('td', class_='descripcion'),
        
        # Look for large text blocks with construction terms
        lambda s: find_construction_description(s),
        
        # Look for price table descriptions
        lambda s: find_price_table_description(s)
    ]
    
    for pattern in description_patterns:
        try:
            elem = pattern(soup)
            if elem:
                text = elem.get_text(strip=True)
                if len(text) > 50:  # Meaningful description
                    return clean_description(text)
        except:
            continue
    
    return "No technical description found"

def find_construction_description(soup):
    """Find description containing construction terms"""
    
    construction_terms = [
        'hormigón', 'acero', 'madera', 'aplicación', 'ejecución', 
        'encofrado', 'armado', 'viga', 'pilar', 'forjado'
    ]
    
    # Look in all text elements
    for elem in soup.find_all(['p', 'div', 'td', 'span']):
        text = elem.get_text(strip=True).lower()
        if len(text) > 100 and any(term in text for term in construction_terms):
            return elem
    
    return None

def find_price_table_description(soup):
    """Find description in price tables"""
    
    # Look for tables with price information
    tables = soup.find_all('table')
    
    for table in tables:
        # Look for cells with euros symbol or price patterns
        for cell in table.find_all('td'):
            text = cell.get_text(strip=True)
            if '€' in text or 'precio' in text.lower():
                # Check nearby cells for description
                row = cell.find_parent('tr')
                if row:
                    for sibling in row.find_all('td'):
                        desc_text = sibling.get_text(strip=True)
                        if len(desc_text) > 50 and not '€' in desc_text:
                            return sibling
    
    return None

def extract_price(soup):
    """Extract price from CYPE page"""
    
    # Look for price patterns
    price_patterns = [
        r'(\d+[.,]\d+)\s*€',
        r'(\d+[.,]\d+)\s*EUR',
        r'precio.*?(\d+[.,]\d+)',
    ]
    
    text = soup.get_text()
    
    for pattern in price_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            price_str = matches[0].replace(',', '.')
            try:
                return float(price_str)
            except ValueError:
                continue
    
    return None

def find_configuration_variables(soup):
    """Find actual configuration variables (not navigation selects)"""
    
    variables = []
    
    # Look for forms with variable configurations
    forms = soup.find_all('form')
    
    for form in forms:
        # Skip login/navigation forms
        action = form.get('action', '').lower()
        if 'login' in action or 'remote' in action:
            continue
        
        # Find configuration inputs
        for input_elem in form.find_all(['input', 'select']):
            name = input_elem.get('name', '')
            input_type = input_elem.get('type', input_elem.name)
            
            # Skip navigation selects (they change location)
            onchange = input_elem.get('onchange', '')
            if 'location' in onchange:
                continue
            
            # This might be a configuration variable
            if name and input_type in ['select', 'text', 'number', 'hidden']:
                variable = {
                    'name': name,
                    'type': input_type,
                    'onchange': onchange
                }
                
                if input_elem.name == 'select':
                    options = []
                    for option in input_elem.find_all('option'):
                        value = option.get('value', '')
                        text = option.get_text(strip=True)
                        if value and text:
                            options.append({'value': value, 'text': text})
                    variable['options'] = options
                
                variables.append(variable)
    
    return variables

def clean_description(text):
    """Clean and fix description text"""
    
    # Fix encoding issues
    text = text.replace('Ă', 'í').replace('Ă˛', 'ó').replace('Ăą', 'ñ')
    text = text.replace('Ă­', 'í').replace('Ă©', 'é').replace('Ăş', 'ú')
    
    # Clean formatting
    text = re.sub(r'\s+', ' ', text.strip())
    
    return text

def analyze_element_relationships(results):
    """Analyze relationships between extracted elements"""
    
    print(f"\n📊 ANALYZING ELEMENT RELATIONSHIPS:")
    print("=" * 50)
    
    codes = [r['code'] for r in results]
    titles = [r['title'] for r in results] 
    descriptions = [r['description'] for r in results]
    
    print(f"Element codes: {codes}")
    print(f"Same element code: {len(set(codes)) == 1}")
    
    if len(set(codes)) == 1:
        print(f"✅ All elements share code '{codes[0]}' - these might be variable combinations!")
        
        # Check description differences
        unique_descriptions = set(descriptions)
        print(f"Unique descriptions: {len(unique_descriptions)}")
        
        if len(unique_descriptions) > 1:
            print(f"✅ DESCRIPTIONS VARY - this supports variable combinations theory")
            
            # Show differences
            for i, result in enumerate(results):
                print(f"\n   Variation {i+1}:")
                print(f"     URL: {result['url'].split('/')[-1]}")
                print(f"     Description: {result['description'][:100]}...")
        else:
            print(f"❌ All descriptions identical")
    else:
        print(f"❌ Different element codes - these are different elements:")
        for i, result in enumerate(results):
            print(f"   {i+1}. {result['code']}: {result['title']}")

def test_internal_variables(url):
    """Test if an element page has internal variable configuration that changes description"""
    
    print(f"Testing internal variables for: {url.split('/')[-1]}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for JavaScript that might handle variable changes
        scripts = soup.find_all('script')
        
        variable_handling = False
        
        for script in scripts:
            if script.string:
                script_text = script.string.lower()
                
                # Look for price/description change handlers
                if any(term in script_text for term in ['precio', 'descripcion', 'onchange', 'variable']):
                    print(f"   🔧 Found potential variable handling in JavaScript")
                    variable_handling = True
                    
                    # Extract relevant lines
                    lines = script.string.split('\n')
                    relevant_lines = [line for line in lines if any(term in line.lower() for term in ['precio', 'descripcion'])]
                    
                    for line in relevant_lines[:3]:
                        print(f"     {line.strip()}")
        
        if not variable_handling:
            print(f"   ❌ No internal variable handling found")
        
        # Look for AJAX endpoints that might provide variable-based content
        ajax_patterns = [
            r'ajax.*\.php',
            r'remote\.asp',
            r'precio.*\.asp',
            r'descripcion.*\.php'
        ]
        
        text = response.text
        for pattern in ajax_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                print(f"   🌐 Found AJAX endpoint: {matches[0]}")
        
    except Exception as e:
        print(f"   Error testing variables: {e}")

if __name__ == "__main__":
    test_related_cype_elements()