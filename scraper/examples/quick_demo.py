#!/usr/bin/env python3
"""
Quick demonstration of the organized CYPE scraper
"""

import sys
from pathlib import Path

# Add core modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from element_extractor import extract_multiple_elements
import json

def quick_demo():
    """Demonstrate the organized scraper usage"""
    
    print("🎯 CYPE SCRAPER QUICK DEMO")
    print("="*40)
    
    # Demo URL (known working)
    demo_url = "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Esmaltes/Esmalte_al_agua_para_madera.html"
    
    print(f"Scraping: {demo_url}")
    print()
    
    # Extract element
    elements = extract_multiple_elements([demo_url])
    
    if not elements:
        print("❌ No elements extracted")
        return
    
    element = elements[0]
    
    # Show extracted data
    print("✅ EXTRACTED ELEMENT:")
    print(f"   📝 Code: {element.code}")
    print(f"   🏷️  Title: {element.title}")
    print(f"   💰 Price: €{element.price}")
    print(f"   📏 Unit: {element.unit}")
    print(f"   🔧 Variables: {len(element.variables)}")
    print()
    
    # Show variable types
    text_vars = [v for v in element.variables if v.variable_type == 'TEXT']
    radio_vars = [v for v in element.variables if v.variable_type == 'RADIO']
    checkbox_vars = [v for v in element.variables if v.variable_type == 'CHECKBOX']
    
    print("🔧 VARIABLE BREAKDOWN:")
    print(f"   📝 Text inputs: {len(text_vars)}")
    print(f"   🔘 Radio options: {len(radio_vars)}")
    print(f"   ☑️  Checkboxes: {len(checkbox_vars)}")
    print()
    
    # Show sample variables
    print("📋 SAMPLE VARIABLES:")
    for i, var in enumerate(element.variables[:5]):
        options_str = f"{var.options[:2]}..." if len(var.options) > 2 else str(var.options)
        print(f"   {i+1}. {var.name} ({var.variable_type}): {options_str}")
    
    print()
    print(f"🎉 Demo complete! Element {element.code} successfully scraped with clean Spanish encoding.")
    
    return element

if __name__ == "__main__":
    quick_demo()