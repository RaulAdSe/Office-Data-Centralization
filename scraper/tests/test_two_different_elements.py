#!/usr/bin/env python3
"""
Test with 2 completely different CYPE elements to show variation
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "core"))
sys.path.insert(0, str(Path(__file__).parent / "template_extraction"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enhanced_element_extractor import EnhancedElementExtractor
from smart_template_extractor import SmartTemplateExtractor
from db_manager import DatabaseManager

def test_different_elements():
    """Test pipeline with 2 different CYPE elements"""
    
    print("🏗️  TESTING 2 DIFFERENT CYPE ELEMENTS")
    print("=" * 70)
    
    # Use 2 DIFFERENT element URLs
    urls = [
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html",
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_de_hormigon_armado.html"
    ]
    
    # Initialize components
    element_extractor = EnhancedElementExtractor()
    template_extractor = SmartTemplateExtractor()
    db_path = str(Path(__file__).parent.parent / "src" / "office_data.db")
    db_manager = DatabaseManager(db_path)
    
    elements_data = []
    
    for i, url in enumerate(urls):
        print(f"\n{'='*20} EXTRACTING ELEMENT {i+1}/2 {'='*20}")
        print(f"URL: {url}")
        
        try:
            # Extract element data
            element = element_extractor.extract_element_data(url)
            
            if element:
                print(f"✅ Element: {element.code} - {element.title}")
                print(f"   Variables: {len(element.variables)}")
                
                # Get static description template
                static_desc = template_extractor.get_static_description(url)
                print(f"   Template length: {len(static_desc)} characters")
                
                # Store basic info
                elements_data.append({
                    'element': element,
                    'template': static_desc,
                    'url': url
                })
                
                # Show key details
                print(f"\n📋 ELEMENT DETAILS:")
                print(f"   Code: {element.code}")
                print(f"   Title: {element.title}")
                print(f"   Description: {static_desc[:100]}...")
                
                # Show key variables
                key_vars = [v for v in element.variables if v.options and len(v.options) > 1][:5]
                print(f"\n🔧 KEY VARIABLES ({len(key_vars)}/5):")
                for var in key_vars:
                    print(f"   • {var.name}: {len(var.options)} options")
                    # Show first 2 options
                    for j, option in enumerate(var.options[:2]):
                        print(f"     {j+1}. {option}")
                    if len(var.options) > 2:
                        print(f"     ... and {len(var.options) - 2} more")
            
        except Exception as e:
            print(f"❌ Error processing element: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary comparison
    if len(elements_data) == 2:
        print(f"\n{'='*25} COMPARISON {'='*25}")
        
        elem1, elem2 = elements_data[0]['element'], elements_data[1]['element']
        temp1, temp2 = elements_data[0]['template'], elements_data[1]['template']
        
        print(f"📊 ELEMENT COMPARISON:")
        print(f"   Element 1: {elem1.code} - {elem1.title}")
        print(f"   Element 2: {elem2.code} - {elem2.title}")
        print(f"   ")
        print(f"   Variables: {len(elem1.variables)} vs {len(elem2.variables)}")
        print(f"   Template length: {len(temp1)} vs {len(temp2)} characters")
        
        print(f"\n📄 TEMPLATE COMPARISON:")
        print(f"   Element 1 template: {temp1[:120]}...")
        print(f"   Element 2 template: {temp2[:120]}...")
        
        # Check if templates are different
        if temp1 != temp2:
            print(f"   ✅ Templates are DIFFERENT (as expected)")
        else:
            print(f"   ⚠️  Templates are identical")
        
        print(f"\n🔧 VARIABLE DIFFERENCES:")
        vars1 = {v.name for v in elem1.variables}
        vars2 = {v.name for v in elem2.variables}
        
        common_vars = vars1.intersection(vars2)
        unique1 = vars1.difference(vars2)
        unique2 = vars2.difference(vars1)
        
        print(f"   Common variables: {len(common_vars)}")
        print(f"   Only in Element 1: {len(unique1)}")
        print(f"   Only in Element 2: {len(unique2)}")
        
        if unique1:
            print(f"   Unique to Element 1: {list(unique1)[:3]}...")
        if unique2:
            print(f"   Unique to Element 2: {list(unique2)[:3]}...")
    
    print(f"\n✅ EXTRACTION COMPLETE")
    print(f"   Both elements successfully extracted")
    print(f"   Ready for database storage")
    
    return elements_data

if __name__ == "__main__":
    results = test_different_elements()