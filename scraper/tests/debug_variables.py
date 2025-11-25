#!/usr/bin/env python3
"""
Debug script to explore CYPE variables/options structure
"""

from page_detector import fetch_page
from bs4 import BeautifulSoup
import re
import json

def debug_element_variables(url):
    """Debug an element page to find variables/options"""
    print(f"\n{'='*80}")
    print(f"DEBUGGING VARIABLES: {url}")
    print('='*80)
    
    try:
        html = fetch_page(url)
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)
        
        print(f"HTML length: {len(html)} characters")
        print(f"Text length: {len(text)} characters")
        
        # Look for form elements, dropdowns, inputs
        print("\n🔍 FORM ELEMENTS:")
        forms = soup.find_all('form')
        print(f"Forms found: {len(forms)}")
        
        selects = soup.find_all('select')
        print(f"Select dropdowns found: {len(selects)}")
        for i, select in enumerate(selects):
            print(f"  Select {i+1}: name='{select.get('name')}', id='{select.get('id')}'")
            options = select.find_all('option')
            print(f"    Options: {len(options)}")
            for opt in options[:5]:  # Show first 5
                print(f"      - {opt.get('value')}: {opt.get_text().strip()}")
            if len(options) > 5:
                print(f"      ... and {len(options)-5} more")
        
        inputs = soup.find_all('input')
        print(f"Input fields found: {len(inputs)}")
        for i, inp in enumerate(inputs[:10]):  # Show first 10
            print(f"  Input {i+1}: type='{inp.get('type')}', name='{inp.get('name')}', value='{inp.get('value')}'")
        
        # Look for JavaScript variables
        print("\n🔍 JAVASCRIPT VARIABLES:")
        scripts = soup.find_all('script')
        print(f"Script tags found: {len(scripts)}")
        
        for script in scripts:
            if script.string:
                script_text = script.string
                
                # Look for common patterns
                if 'var ' in script_text or 'let ' in script_text or 'const ' in script_text:
                    print("  Found variables in script:")
                    # Extract variable declarations
                    var_matches = re.findall(r'(var|let|const)\s+(\w+)\s*=\s*([^;]+);', script_text)
                    for match in var_matches[:5]:
                        print(f"    {match[0]} {match[1]} = {match[2][:50]}...")
                
                # Look for specific CYPE patterns
                if 'opciones' in script_text.lower() or 'variables' in script_text.lower():
                    print("  Found 'opciones' or 'variables' in script")
                    lines = script_text.split('\n')
                    for line in lines:
                        if 'opciones' in line.lower() or 'variables' in line.lower():
                            print(f"    {line.strip()[:100]}...")
        
        # Look for specific text patterns that might indicate variables
        print("\n🔍 TEXT PATTERNS:")
        
        # Look for "Incluye:" sections
        incluye_matches = re.findall(r'Incluye:([^A-Z]+?)(?:[A-Z]{3,}|$)', text, re.DOTALL)
        if incluye_matches:
            print("Found 'Incluye:' sections:")
            for match in incluye_matches:
                print(f"  {match.strip()[:200]}...")
        
        # Look for material/dimension options
        option_patterns = [
            r'Resistencia característica del hormigón[^\.]+',
            r'Acero[^\.]+',
            r'Tipo[^\.]+',
            r'Material[^\.]+',
            r'Dimensiones?[^\.]+',
            r'Espesor[^\.]+',
            r'Diámetro[^\.]+',
        ]
        
        for pattern in option_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                print(f"Pattern '{pattern}': {len(matches)} matches")
                for match in matches[:3]:
                    print(f"  {match}")
        
        # Look for specific HTML structures that might contain variables
        print("\n🔍 HTML STRUCTURES:")
        
        # Look for divs/spans with specific classes
        var_containers = soup.find_all(['div', 'span', 'td'], 
                                     class_=re.compile(r'(var|option|param|config)', re.I))
        if var_containers:
            print(f"Found {len(var_containers)} potential variable containers")
            for container in var_containers[:5]:
                print(f"  {container.name}.{container.get('class')}: {container.get_text()[:100]}...")
        
        # Look for data attributes
        data_elements = soup.find_all(attrs={'data-variable': True})
        data_elements.extend(soup.find_all(attrs={'data-option': True}))
        data_elements.extend(soup.find_all(attrs={'data-param': True}))
        
        if data_elements:
            print(f"Found {len(data_elements)} elements with data-* attributes")
            for elem in data_elements[:5]:
                attrs = {k: v for k, v in elem.attrs.items() if k.startswith('data-')}
                print(f"  {elem.name}: {attrs}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test with known element URLs
    urls = [
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html",
        "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Esmaltes/Esmalte_al_agua_para_madera.html",
    ]
    
    for url in urls:
        debug_element_variables(url)