#!/usr/bin/env python3
"""
Test Enhanced Variable Extraction on EHX005 - Losa mixta con chapa colaborante
Based on user's screenshot showing specific CYPE interface variables
"""

import sys
import os
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "core"))

def test_ehx005_enhanced_extraction():
    """Test EHX005 with enhanced patterns for composite steel/concrete elements"""
    from enhanced_element_extractor import EnhancedElementExtractor
    
    print("🧪 TESTING ENHANCED EHX005 VARIABLE EXTRACTION")
    print("=" * 60)
    print("Element: EHX005 - Losa mixta con chapa colaborante")
    print()
    
    # URL from the screenshot
    url = 'https://generadordeprecios.info/obra_nueva/calculoprecio.aspx?Valor=10_0_4_0_0_0_0_0[EHX005]ehx_005c3_0_10c1_0_2_0_0_1_2c1_0_2_4_3_3c5_0_5c5_0_2_0_0_1_2_1c3_0'
    
    extractor = EnhancedElementExtractor()
    
    try:
        element_data = extractor.extract_element_data(url)
        
        if element_data:
            print(f"✅ Element extracted: {element_data.code} - {element_data.title}")
            print(f"📊 Variables found: {len(element_data.variables)}")
            print(f"💰 Price: €{element_data.price}")
            print()
            
            if element_data.variables:
                print("🔍 ENHANCED VARIABLES EXTRACTED:")
                print("-" * 40)
                
                for i, var in enumerate(element_data.variables, 1):
                    print(f"{i}. {var.name} ({var.variable_type})")
                    print(f"   Default: {var.default_value}")
                    if var.options:
                        print(f"   Options: {var.options}")
                    print(f"   Required: {var.is_required}")
                    print(f"   Description: {var.description}")
                    print()
                
                # Check for specific enhanced patterns we expect
                variable_names = [var.name for var in element_data.variables]
                
                print("🎯 ENHANCED PATTERN ANALYSIS:")
                print("-" * 40)
                
                expected_patterns = [
                    'cuantia_acero_negativos', 'cuantia_acero_positivos', 
                    'volumen_hormigon', 'canto_losa', 'altura_perfil', 
                    'intereje', 'espesor_chapa', 'prelacado', 'tipo_chapa'
                ]
                
                found_patterns = []
                for pattern in expected_patterns:
                    if pattern in variable_names:
                        found_patterns.append(pattern)
                        print(f"   ✅ Found: {pattern}")
                    else:
                        print(f"   ❌ Missing: {pattern}")
                
                print()
                print(f"📊 PATTERN MATCH SCORE: {len(found_patterns)}/{len(expected_patterns)} ({len(found_patterns)*100//len(expected_patterns)}%)")
                
                if len(found_patterns) > 0:
                    print("🎉 Enhanced patterns are working!")
                else:
                    print("⚠️ No enhanced patterns found - may need more specific keywords")
                    
            else:
                print("❌ No variables extracted")
                
        else:
            print("❌ Failed to extract element data")
            
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ehx005_enhanced_extraction()