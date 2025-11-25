#!/usr/bin/env python3
"""
Debug script to see what's happening with real pages
"""

from page_detector import fetch_page, detect_page_type
import re

def debug_page(url):
    """Debug a specific page"""
    print(f"\n{'='*80}")
    print(f"DEBUGGING: {url}")
    print('='*80)
    
    try:
        html = fetch_page(url)
        print(f"HTML length: {len(html)} characters")
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)
        
        print(f"Text length: {len(text)} characters")
        print("\nFirst 500 characters of text:")
        print("-" * 40)
        print(text[:500])
        print("-" * 40)
        
        # Look for code patterns
        code_patterns = [
            r'([A-Z]{2,4}\d{3})\s*\|\s*([^|]+)\s*\|',
            r'([A-Z]{2,4}\d{3})',
            r'UNIDAD DE OBRA\s+([A-Z]{2,4}\d{3})',
        ]
        
        print("\nLooking for code patterns:")
        for i, pattern in enumerate(code_patterns):
            matches = re.findall(pattern, text)
            print(f"  Pattern {i+1}: {pattern}")
            print(f"  Matches: {matches}")
        
        # Look for key phrases
        key_phrases = [
            'UNIDAD DE OBRA',
            'CARACTERÍSTICAS TÉCNICAS', 
            'Precio',
            'Unidades de obra'
        ]
        
        print("\nLooking for key phrases:")
        for phrase in key_phrases:
            found = phrase in text
            print(f"  '{phrase}': {'✓' if found else '✗'}")
            if found:
                # Show context
                idx = text.find(phrase)
                context = text[max(0, idx-50):idx+len(phrase)+50]
                print(f"    Context: ...{context}...")
        
        result = detect_page_type(html, url)
        print(f"\nDETECTION RESULT:")
        print(f"  Type: {result['type']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Code: {result['code']}")
        print(f"  Title: {result['title']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Debug the first element URL
    url = "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html"
    debug_page(url)