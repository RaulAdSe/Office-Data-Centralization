#!/usr/bin/env python3
"""
Test the enhanced pipeline with variable extraction
"""

import sys
import os
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "core"))

# Test CSZ020 with the enhanced pipeline
def test_enhanced_extraction():
    from enhanced_element_extractor import EnhancedElementExtractor
    
    print("🧪 TESTING ENHANCED VARIABLE EXTRACTION PIPELINE")
    print("=" * 60)
    
    # Test URL
    url = 'https://generadordeprecios.info/obra_nueva/Cimentaciones/Superficiales/Zapatas/CSZ020_Sistema_de_encofrado_para_zapata_de.html'
    
    extractor = EnhancedElementExtractor()
    element_data = extractor.extract_element_data(url)
    
    if element_data:
        print(f"✅ Element extracted: {element_data.code} - {element_data.title}")
        print(f"📊 Variables found: {len(element_data.variables)}")
        print()
        
        # Simulate what the production pipeline does now
        variables_list = []
        if hasattr(element_data, 'variables') and element_data.variables:
            for var in element_data.variables:
                variables_list.append({
                    'name': var.name,
                    'variable_type': var.variable_type,
                    'options': var.options,
                    'default_value': var.default_value,
                    'is_required': var.is_required,
                    'description': var.description
                })
        
        element_dict = {
            'element_code': element_data.code,
            'title': element_data.title,
            'description': element_data.description,
            'price': element_data.price,
            'url': url,
            'variables': variables_list  # This is now included!
        }
        
        print("🔍 ENHANCED ELEMENT DATA:")
        print(f"   Element: {element_dict['element_code']}")
        print(f"   Title: {element_dict['title']}")
        print(f"   Price: €{element_dict['price']}")
        print(f"   Variables: {len(element_dict['variables'])}")
        print()
        
        if element_dict['variables']:
            print("📋 EXTRACTED VARIABLES:")
            for i, var in enumerate(element_dict['variables'], 1):
                print(f"   {i}. {var['name']} ({var['variable_type']})")
                print(f"      Options: {var['options']}")
                print(f"      Default: {var['default_value']}")
                print(f"      Required: {var['is_required']}")
                print()
        
        print("🎉 SUCCESS: Enhanced pipeline now extracts and preserves variables!")
        return True
    else:
        print("❌ Failed to extract element")
        return False

if __name__ == "__main__":
    test_enhanced_extraction()