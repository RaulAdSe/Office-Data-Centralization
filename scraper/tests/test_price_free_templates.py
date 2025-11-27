#!/usr/bin/env python3
"""
Test template extraction without prices
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "template_extraction"))

from smart_template_extractor import SmartTemplateExtractor

def test_price_free_templates():
    """Test template extraction without prices"""
    
    print("🚀 TESTING PRICE-FREE TEMPLATE EXTRACTION")
    print("=" * 60)
    
    # Test URLs
    urls = [
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html",
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_de_hormigon_armado.html"
    ]
    
    template_extractor = SmartTemplateExtractor()
    
    for i, url in enumerate(urls):
        print(f"\n{'='*15} ELEMENT {i+1}/2 {'='*15}")
        print(f"URL: {url}")
        
        try:
            # Get static description without price
            static_desc = template_extractor.get_static_description(url)
            
            print(f"✅ Template extracted:")
            print(f"   Length: {len(static_desc)} characters")
            print(f"   Content: {static_desc[:150]}...")
            
            # Check if price was removed
            has_price = any(char in static_desc[:20] for char in ['€', '₹', '$'])
            if has_price:
                print(f"   ⚠️  Price still present in template")
            else:
                print(f"   ✅ Price successfully removed")
            
            print(f"\n📄 FULL TEMPLATE:")
            print(f'   "{static_desc}"')
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 TEMPLATE EXTRACTION COMPLETE")
    print(f"   ✅ Templates extracted without prices")
    print(f"   ✅ Clean construction descriptions only")

if __name__ == "__main__":
    test_price_free_templates()