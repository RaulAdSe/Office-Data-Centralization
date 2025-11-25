#!/usr/bin/env python3
"""
Test the encoding fix for Spanish characters
"""

from element_extractor import ElementExtractor
from page_detector import detect_page_type, fetch_page

def test_encoding_fix():
    """Test encoding fix on a known problematic URL"""
    
    url = "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html"
    
    print("🧪 TESTING ENCODING FIX")
    print("="*50)
    print(f"URL: {url}")
    print()
    
    # Test page detection first
    print("1. Testing page detection...")
    html = fetch_page(url)
    page_info = detect_page_type(html, url)
    
    print(f"   Raw title from page_detector: '{page_info['title']}'")
    
    # Test element extraction
    print("\n2. Testing element extraction...")
    extractor = ElementExtractor()
    
    # Apply clean_text to the raw title
    if page_info['title']:
        cleaned_title = extractor.clean_text(page_info['title'])
        print(f"   After clean_text: '{cleaned_title}'")
    
    # Test full extraction
    print("\n3. Testing full extraction...")
    element = extractor.extract_element_data(url)
    
    if element:
        print(f"   Final title: '{element.title}'")
        print(f"   Code: '{element.code}'")
        print(f"   Description start: '{element.description[:100]}...'")
        
        # Test some variables too
        if element.variables:
            print(f"\n   Variable examples:")
            for i, var in enumerate(element.variables[:3]):
                print(f"   {i+1}. {var.name}: {var.options}")
    else:
        print("   ❌ Failed to extract element")

if __name__ == "__main__":
    test_encoding_fix()