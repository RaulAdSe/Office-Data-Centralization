#!/usr/bin/env python3
"""
Carefully test if CYPE descriptions actually change with different variable selections
"""

import requests
from bs4 import BeautifulSoup
import time
import urllib.parse

def test_variable_changes(url):
    """Test if descriptions change when we modify variables"""
    
    print(f"🔍 TESTING VARIABLE CHANGES ON CYPE")
    print(f"URL: {url}")
    print("=" * 80)
    
    # First, get the base page to understand the form structure
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("📋 STEP 1: Analyze form structure")
        
        # Look for form elements
        forms = soup.find_all('form')
        print(f"   Found {len(forms)} forms on page")
        
        # Look for select elements (dropdowns)
        selects = soup.find_all('select')
        print(f"   Found {len(selects)} select elements")
        
        # Look for input elements
        inputs = soup.find_all('input')
        print(f"   Found {len(inputs)} input elements")
        
        # Get current description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            base_description = meta_desc['content'].strip()
            print(f"\n📄 BASE DESCRIPTION:")
            print(f"   {base_description[:100]}...")
        else:
            print("❌ No meta description found")
            return
        
        # Analyze select elements to find variables
        print(f"\n🔧 VARIABLE CONTROLS FOUND:")
        variables_found = {}
        
        for select in selects:
            name = select.get('name', '')
            if name and len(name) > 2:  # Skip very short names
                options = select.find_all('option')
                option_values = []
                for option in options:
                    value = option.get('value', '')
                    text = option.get_text().strip()
                    if value and text and value != '':
                        option_values.append((value, text))
                
                if option_values:
                    variables_found[name] = option_values
                    print(f"   {name}: {len(option_values)} options")
                    for value, text in option_values[:3]:  # Show first 3
                        print(f"     • {value}: {text}")
                    if len(option_values) > 3:
                        print(f"     ... and {len(option_values) - 3} more")
        
        if not variables_found:
            print("❌ No variable controls found")
            return
        
        # Test with different variable combinations
        print(f"\n🧪 TESTING DIFFERENT COMBINATIONS:")
        
        # Get a few key variables to test
        test_variables = list(variables_found.keys())[:3]  # Test first 3 variables
        
        descriptions = []
        
        for i in range(3):  # Test 3 different combinations
            print(f"\n--- Test {i+1}/3 ---")
            
            # Build parameter combination
            params = {}
            for var_name in test_variables:
                options = variables_found[var_name]
                if options:
                    # Use different option for each test
                    option_index = i % len(options)
                    value, text = options[option_index]
                    params[var_name] = value
                    print(f"   {var_name} = {value} ({text})")
            
            # Make request with parameters
            if params:
                try:
                    # Try POST request (most CYPE forms use POST)
                    test_response = requests.post(url, data=params, timeout=10)
                    if test_response.status_code != 200:
                        # Try GET request as fallback
                        query_string = urllib.parse.urlencode(params)
                        test_url = f"{url}?{query_string}"
                        test_response = requests.get(test_url, timeout=10)
                    
                    if test_response.status_code == 200:
                        test_soup = BeautifulSoup(test_response.content, 'html.parser')
                        test_meta = test_soup.find('meta', attrs={'name': 'description'})
                        
                        if test_meta and test_meta.get('content'):
                            test_description = test_meta['content'].strip()
                            descriptions.append({
                                'params': params,
                                'description': test_description
                            })
                            print(f"   Description: {test_description[:80]}...")
                        else:
                            print(f"   ❌ No description in response")
                    else:
                        print(f"   ❌ HTTP {test_response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Error: {e}")
            
            time.sleep(1)  # Be respectful
        
        # Analyze if descriptions changed
        print(f"\n🔍 ANALYSIS:")
        print(f"   Got {len(descriptions)} descriptions")
        
        if len(descriptions) >= 2:
            unique_descriptions = set(d['description'] for d in descriptions)
            print(f"   Unique descriptions: {len(unique_descriptions)}")
            
            if len(unique_descriptions) > 1:
                print(f"   ✅ DESCRIPTIONS DO CHANGE WITH VARIABLES!")
                
                print(f"\n📋 DIFFERENT DESCRIPTIONS FOUND:")
                for i, desc_text in enumerate(unique_descriptions):
                    print(f"   {i+1}. {desc_text[:100]}...")
                
                # Look for variable values in descriptions
                print(f"\n🔍 CHECKING FOR VARIABLE VALUES IN DESCRIPTIONS:")
                for desc_data in descriptions:
                    desc_text = desc_data['description']
                    params = desc_data['params']
                    
                    print(f"\n   Parameters: {params}")
                    for param_name, param_value in params.items():
                        if param_value.lower() in desc_text.lower():
                            print(f"     ✅ Found '{param_value}' in description")
                        else:
                            print(f"     ❌ '{param_value}' not found in description")
            else:
                print(f"   ❌ All descriptions are identical")
                print(f"   → Descriptions don't change with variables")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Test both URLs"""
    
    urls = [
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html",
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_de_hormigon_armado.html"
    ]
    
    for i, url in enumerate(urls):
        print(f"\n{'='*20} ELEMENT {i+1}/2 {'='*20}")
        test_variable_changes(url)

if __name__ == "__main__":
    main()