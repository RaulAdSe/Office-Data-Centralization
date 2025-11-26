#!/usr/bin/env python3
"""
Test Intelligent "Opciones" Section Parsing
Extract variable names directly from CYPE's HTML structure
"""

import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# Add paths  
sys.path.insert(0, str(Path(__file__).parent / "core"))

def analyze_cype_opciones_structure():
    """Analyze how CYPE structures the Opciones section"""
    
    print("🔍 ANALYZING CYPE 'OPCIONES' SECTION STRUCTURE")
    print("=" * 60)
    
    # Test with a known working URL
    test_urls = [
        'https://generadordeprecios.info/obra_nueva/Cimentaciones/Superficiales/Zapatas/CSZ020_Sistema_de_encofrado_para_zapata_de.html',
        'https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Muros/EHM010_Muro_de_hormigon.html'
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept-Language': 'es-ES,es;q=0.9'
    })
    
    for url in test_urls:
        print(f"\n🌐 Analyzing: {url.split('/')[-1]}")
        print("-" * 50)
        
        try:
            response = session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for "Opciones" section
                opciones_indicators = [
                    soup.find('h2', string=lambda text: text and 'opciones' in text.lower()),
                    soup.find('h3', string=lambda text: text and 'opciones' in text.lower()),
                    soup.find(string=lambda text: text and 'opciones' in text.lower()),
                ]
                
                for indicator in opciones_indicators:
                    if indicator:
                        print(f"✅ Found 'Opciones' indicator: {indicator}")
                        
                        # Find the parent container
                        parent = indicator.parent if hasattr(indicator, 'parent') else indicator
                        
                        # Look for form elements near this section
                        if parent:
                            # Look for nearby form inputs
                            form_inputs = []
                            
                            # Search in parent and siblings
                            container = parent.parent if parent.parent else parent
                            inputs = container.find_all(['input', 'select', 'textarea'])
                            
                            for inp in inputs[:10]:  # Limit to first 10
                                input_type = inp.get('type', inp.name)
                                value = inp.get('value', '')
                                name = inp.get('name', inp.get('id', ''))
                                
                                # Find associated label
                                label = find_label_for_input(inp, soup)
                                
                                form_inputs.append({
                                    'type': input_type,
                                    'name': name,
                                    'value': value,
                                    'label': label
                                })
                            
                            if form_inputs:
                                print(f"📝 Found {len(form_inputs)} form inputs:")
                                for inp in form_inputs:
                                    print(f"   • {inp['type']}: {inp['label']} = {inp['value']}")
                        break
                
                # Also look for table structures with variables
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    if len(rows) > 1:  # Has content
                        print(f"\n📊 Found table with {len(rows)} rows:")
                        for row in rows[:3]:  # Show first 3 rows
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 2:
                                label = cells[0].get_text(strip=True)
                                value = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                                if label and len(label) < 100:  # Reasonable label length
                                    print(f"   • {label}: {value}")
                
        except Exception as e:
            print(f"❌ Error analyzing {url}: {e}")

def find_label_for_input(inp, soup):
    """Find label text for an input element"""
    # Method 1: Look for <label> with for attribute
    input_id = inp.get('id')
    if input_id:
        label = soup.find('label', {'for': input_id})
        if label:
            return label.get_text(strip=True)
    
    # Method 2: Look for parent label
    parent = inp.parent
    if parent and parent.name == 'label':
        return parent.get_text(strip=True)
    
    # Method 3: Look for preceding text
    prev_sibling = inp.previous_sibling
    if prev_sibling and hasattr(prev_sibling, 'strip'):
        text = prev_sibling.strip()
        if text and len(text) < 100:
            return text
    
    # Method 4: Look in table cell
    td_parent = inp.find_parent('td')
    if td_parent:
        row = td_parent.find_parent('tr')
        if row:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2 and cells[1] == td_parent:
                return cells[0].get_text(strip=True)
    
    return "Unknown"

if __name__ == "__main__":
    analyze_cype_opciones_structure()