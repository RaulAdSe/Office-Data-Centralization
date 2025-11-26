#!/usr/bin/env python3
"""
Quick test to validate element discovery and processing pipeline
"""

import sys
from pathlib import Path
import time

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from enhanced_element_extractor import EnhancedElementExtractor
from page_detector import detect_page_type, fetch_page
import requests
from bs4 import BeautifulSoup

def discover_elements_from_specific_category(category_url: str, max_elements: int = 10):
    """Discover actual element URLs from a specific category"""
    
    print(f"🔍 Discovering elements from: {category_url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    element_urls = []
    
    try:
        response = session.get(category_url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Make absolute URL
            if href.startswith('/'):
                absolute_url = f"https://generadordeprecios.info{href}"
            elif href.startswith('http'):
                absolute_url = href
            else:
                continue
            
            # Skip non-CYPE URLs
            if 'generadordeprecios.info' not in absolute_url or '/obra_nueva/' not in absolute_url:
                continue
                
            # Skip obvious non-element URLs
            if any(ext in absolute_url for ext in ['.pdf', '.jpg', '.png', '.css', '.js']):
                continue
                
            # Look for element-like URLs (deeper and specific names)
            path_parts = absolute_url.split('/')
            if len(path_parts) >= 7:  # Deep enough to be an element
                last_part = path_parts[-1].replace('.html', '')
                
                # Check if it looks like an element
                element_indicators = [
                    'viga', 'pilar', 'muro', 'forjado', 'zapata', 'escalera',
                    'losa', 'esmalte', 'pintura', 'mortero', 'hormigon'
                ]
                
                if any(indicator in last_part.lower() for indicator in element_indicators):
                    print(f"  Testing potential element: {absolute_url}")
                    
                    # Test if it's actually an element
                    try:
                        html = fetch_page(absolute_url)
                        page_info = detect_page_type(html, absolute_url)
                        
                        if page_info['type'] == 'element':
                            element_urls.append(absolute_url)
                            print(f"    ✅ ELEMENT: {page_info.get('code')} - {page_info.get('title')}")
                            
                            if len(element_urls) >= max_elements:
                                break
                        else:
                            print(f"    ❌ Not element: {page_info['type']}")
                            
                        time.sleep(1)  # Respectful delay
                        
                    except Exception as e:
                        print(f"    ❌ Error: {e}")
        
    except Exception as e:
        print(f"Error processing category: {e}")
    
    return element_urls

def quick_pipeline_test():
    """Quick test of element discovery and processing"""
    
    print("🚀 QUICK CYPE ELEMENT PIPELINE TEST")
    print("=" * 60)
    
    # Test specific categories known to have elements
    test_categories = [
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Escaleras.html",
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas.html",
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Pilares.html"
    ]
    
    all_elements = []
    
    for category in test_categories:
        print(f"\n--- Testing Category ---")
        elements = discover_elements_from_specific_category(category, max_elements=3)
        all_elements.extend(elements)
        
        if len(all_elements) >= 5:  # Enough for testing
            break
    
    print(f"\n📊 DISCOVERY RESULTS:")
    print(f"   Found {len(all_elements)} element URLs")
    
    if not all_elements:
        print("   ❌ No elements discovered")
        return False
    
    # Test extraction on first element
    print(f"\n🏗️  TESTING EXTRACTION:")
    extractor = EnhancedElementExtractor()
    
    test_url = all_elements[0]
    print(f"   Extracting: {test_url}")
    
    try:
        element = extractor.extract_element_data(test_url)
        
        if element:
            print(f"   ✅ SUCCESS!")
            print(f"      Code: {element.code}")
            print(f"      Title: {element.title}")
            print(f"      Variables: {len(element.variables)}")
            print(f"      Price: {element.price}")
            
            return True
        else:
            print(f"   ❌ Extraction failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = quick_pipeline_test()
    
    if success:
        print(f"\n✅ QUICK PIPELINE TEST PASSED!")
        print(f"   Element discovery: Working")
        print(f"   Element extraction: Working")
        print(f"   Ready for full scale deployment")
    else:
        print(f"\n❌ QUICK PIPELINE TEST FAILED")
        print(f"   Need to debug discovery or extraction")