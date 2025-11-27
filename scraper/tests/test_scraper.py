#!/usr/bin/env python3
"""
Test scraper with known URLs instead of crawling
"""

import sys
import os
from pathlib import Path

# Add src directory to path to import db_manager
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from element_extractor import extract_multiple_elements
from db_manager import DatabaseManager

def test_scraper_with_known_urls():
    """Test scraper with known working URLs"""
    
    # Known working element URLs
    test_urls = [
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html",
        "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Esmaltes/Esmalte_al_agua_para_madera.html",
    ]
    
    print("CYPE Scraper Test with Known URLs")
    print("="*80)
    
    # Extract element data
    print("Extracting element data...")
    elements = extract_multiple_elements(test_urls)
    
    if not elements:
        print("No element data extracted!")
        return
    
    print(f"Extracted {len(elements)} elements")
    
    # Store in database
    print("\nStoring in database...")
    db_manager = DatabaseManager("test_scraper.db")
    
    for element in elements:
        try:
            print(f"Storing {element.code}: {element.title}")
            
            # Create element in database
            element_id = db_manager.create_element(
                element_code=element.code,
                element_name=element.title,
                created_by="test_scraper"
            )
            
            # Add basic variables
            variables = [
                ("material", "TEXT", None, None, True, 1),
                ("dimensions", "TEXT", None, None, False, 2),
                ("finish", "TEXT", None, None, False, 3),
            ]
            
            for var_name, var_type, unit, default_value, required, display_order in variables:
                db_manager.add_variable(element_id, var_name, var_type, unit, default_value, required, display_order)
            
            # Create description version
            template = f"{element.title} - {{material}}"
            if element.price:
                template += f" - Price: €{element.price}"
            
            desc_version_id = db_manager.create_description_version(
                element_id=element_id,
                template=template,
                variables_data={"material": "standard"},
                created_by="test_scraper"
            )
            
            print(f"  ✓ Created element {element_id} with description {desc_version_id}")
            
        except Exception as e:
            print(f"  ✗ Error storing {element.code}: {e}")
    
    # Show results
    print(f"\n{'='*80}")
    print("STORED ELEMENTS:")
    print("="*80)
    
    for element in elements:
        db_element = db_manager.get_element_by_code(element.code)
        if db_element:
            print(f"Code: {db_element['element_code']}")
            print(f"Name: {db_element['element_name']}")
            print(f"ID: {db_element['element_id']}")
            
            # Get variables
            variables = db_manager.get_element_variables(db_element['element_id'])
            print(f"Variables: {[v['variable_name'] for v in variables]}")
            
            # Get active description version
            active_version = db_manager.get_active_version(db_element['element_id'])
            if active_version:
                print(f"Template: {active_version['description_template']}")
            else:
                print("Template: (none created)")
            
            print("-" * 40)
    
    print(f"Database saved as: test_scraper.db")

if __name__ == "__main__":
    test_scraper_with_known_urls()