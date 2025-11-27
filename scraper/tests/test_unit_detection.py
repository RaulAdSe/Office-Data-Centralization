#!/usr/bin/env python3
"""
Test Unit Detection in CYPE HTML
Analyze what units are actually present in CYPE pages
"""

import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import re

def test_unit_detection():
    """Test unit detection across different CYPE elements"""
    
    print("🔍 TESTING UNIT DETECTION IN CYPE HTML")
    print("=" * 50)
    
    test_urls = [
        'https://generadordeprecios.info/obra_nueva/Cimentaciones/Superficiales/Zapatas/CSZ020_Sistema_de_encofrado_para_zapata_de.html',
        'https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Muros/EHM010_Muro_de_hormigon.html'
    ]
    
    unit_patterns = [
        r'\(kg/m²\)', r'\(kg/m\)', r'\(t/m³\)',  # Weight/density
        r'\(m³/m²\)', r'\(m³/m\)', r'\(l/m²\)',   # Volume
        r'\(cm\)', r'\(mm\)', r'\(m\)',           # Length
        r'\(MPa\)', r'\(N/mm²\)',                 # Pressure/strength
        r'\(°C\)', r'\(%\)', r'\(€\)',            # Temperature/percentage/currency
        r'\(h\)', r'\(min\)', r'\(s\)',           # Time
        r'\(usos\)', r'\(años\)',                 # Usage/time
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept-Language': 'es-ES,es;q=0.9'
    })
    
    for url in test_urls:
        element_name = url.split('/')[-1].replace('.html', '')
        print(f"\n🌐 Analyzing: {element_name}")
        print("-" * 40)
        
        try:
            response = session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Search for each unit pattern
                found_units = []
                
                for pattern in unit_patterns:
                    matches = soup.find_all(string=re.compile(pattern, re.IGNORECASE))
                    
                    for match in matches:
                        unit_text = str(match).strip()
                        if len(unit_text) < 200:  # Reasonable length
                            found_units.append({
                                'pattern': pattern,
                                'text': unit_text,
                                'unit': re.search(pattern, unit_text, re.IGNORECASE).group().strip('()')
                            })
                
                if found_units:
                    print(f"✅ Found {len(found_units)} text elements with units:")
                    for unit_info in found_units[:10]:  # Show first 10
                        print(f"   • {unit_info['unit']}: {unit_info['text'][:60]}...")
                        
                        # Look for nearby inputs
                        parent = None
                        for element in soup.find_all(string=unit_info['text']):
                            if hasattr(element, 'parent'):
                                parent = element.parent
                                break
                        
                        if parent:
                            inputs = parent.find_parent().find_all('input', type='text') if parent.find_parent() else []
                            if inputs:
                                print(f"     → Found {len(inputs)} nearby inputs")
                                for inp in inputs[:3]:
                                    value = inp.get('value', '')
                                    if value:
                                        print(f"       Input value: {value}")
                else:
                    print("❌ No units found")
                
                # Also check for any parentheses that might contain units we missed
                all_parentheses = soup.find_all(string=re.compile(r'\([^)]+\)'))
                unknown_units = []
                for match in all_parentheses:
                    text = str(match).strip()
                    # Check if it's not already in our patterns
                    found = False
                    for pattern in unit_patterns:
                        if re.search(pattern, text, re.IGNORECASE):
                            found = True
                            break
                    
                    if not found and len(text) < 50:
                        parentheses_content = re.findall(r'\(([^)]+)\)', text)
                        for content in parentheses_content:
                            if content not in [u['unit'] for u in found_units]:
                                unknown_units.append(content)
                
                if unknown_units:
                    print(f"\n🔍 Other parenthetical content (potential units):")
                    unique_units = list(set(unknown_units))[:10]
                    for unit in unique_units:
                        print(f"   • ({unit})")
                        
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_unit_detection()