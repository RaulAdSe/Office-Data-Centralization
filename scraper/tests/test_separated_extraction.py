#!/usr/bin/env python3
"""
Test enhanced element extractor with separated price and description
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "core"))

from enhanced_element_extractor import EnhancedElementExtractor

def test_separated_extraction():
    """Test that price and description are properly separated"""
    
    print("🔍 TESTING SEPARATED PRICE AND DESCRIPTION EXTRACTION")
    print("=" * 70)
    
    # Test URLs
    urls = [
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html",
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_de_hormigon_armado.html"
    ]
    
    extractor = EnhancedElementExtractor()
    
    for i, url in enumerate(urls):
        print(f"\n{'='*20} ELEMENT {i+1}/2 {'='*20}")
        print(f"URL: {url}")
        
        try:
            # Extract element data with new separated extraction
            element = extractor.extract_element_data(url)
            
            if element:
                print(f"\n📊 EXTRACTED DATA SUMMARY:")
                print(f"   Code: {element.code}")
                print(f"   Title: {element.title}")
                print(f"   💰 Price: {element.price}€ (extracted separately)")
                print(f"   📏 Unit: {element.unit}")
                print(f"   🔧 Variables: {len(element.variables)}")
                
                print(f"\n📝 DESCRIPTION (price-free):")
                print(f"   Length: {len(element.description)} characters")
                print(f"   Content: \"{element.description}\"")
                
                # Verify price is not in description
                desc_lower = element.description.lower()
                has_price_in_desc = any(symbol in element.description for symbol in ['€', '₹', '$'])
                has_numbers_at_start = element.description[:20].strip()[0].isdigit() if element.description.strip() else False
                
                print(f"\n✅ VERIFICATION:")
                if element.price:
                    print(f"   ✅ Price extracted: {element.price}€")
                else:
                    print(f"   ❌ Price not extracted")
                
                if not has_price_in_desc:
                    print(f"   ✅ No price symbols in description")
                else:
                    print(f"   ❌ Price symbols still found in description")
                
                if not has_numbers_at_start:
                    print(f"   ✅ Description doesn't start with numbers")
                else:
                    print(f"   ⚠️  Description starts with numbers")
                
                # Check if description starts with construction term
                construction_start = any(element.description.startswith(term) for term in ['Viga', 'Columna', 'Pilar', 'Forjado'])
                if construction_start:
                    print(f"   ✅ Description starts with construction term")
                else:
                    print(f"   ⚠️  Description doesn't start with expected construction term")
                
                print(f"\n🔧 SAMPLE VARIABLES:")
                vars_with_options = [v for v in element.variables if v.options][:3]
                for var in vars_with_options:
                    print(f"   • {var.name}: {len(var.options)} options")
                    print(f"     Default: {var.default_value}")
                    print(f"     Options: {var.options[:2]}...")
            
            else:
                print(f"❌ Failed to extract element data")
        
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 SEPARATION TEST COMPLETE")
    print(f"   ✅ Price and description should now be properly separated")

if __name__ == "__main__":
    test_separated_extraction()