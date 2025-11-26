#!/usr/bin/env python3
"""
Test single element integration and show exactly what gets stored
"""

import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent / "integrations"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database_integrator import CYPEDatabaseIntegrator
from db_manager import DatabaseManager
import json

def test_single_element():
    """Test integration of one element and show database contents"""
    
    # Use paint element (simpler than concrete)
    test_url = "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Esmaltes/Esmalte_al_agua_para_madera.html"
    
    print("🧪 TESTING SINGLE ELEMENT INTEGRATION")
    print("="*60)
    print(f"URL: {test_url}")
    print()
    
    # Clean database for fresh test
    db_path = "test_single.db"
    import os
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Initialize integrator
    integrator = CYPEDatabaseIntegrator(db_path)
    
    # Scrape and integrate one element
    results = integrator.integrate_scraped_elements([test_url], created_by="test_user")
    
    if results["integrated_count"] == 0:
        print("❌ Integration failed!")
        return
    
    print(f"\n✅ Integration successful!")
    print(f"Element code: {results['element_codes'][0]}")
    
    # Now show what's in the database
    show_database_contents(db_path, results['element_codes'][0])

def show_database_contents(db_path: str, element_code: str):
    """Show exactly what was stored in each table"""
    
    db = DatabaseManager(db_path)
    
    print(f"\n📊 DATABASE CONTENTS FOR {element_code}")
    print("="*60)
    
    # 1. Elements table
    print("1️⃣ ELEMENTS TABLE:")
    print("-" * 30)
    element = db.get_element_by_code(element_code)
    print(f"   element_id: {element['element_id']}")
    print(f"   element_code: {element['element_code']}")
    print(f"   element_name: {element['element_name']}")
    print(f"   created_at: {element['created_at']}")
    print(f"   created_by: {element['created_by']}")
    print()
    
    # 2. Element variables table
    print("2️⃣ ELEMENT_VARIABLES TABLE:")
    print("-" * 35)
    variables = db.get_element_variables(element['element_id'], include_options=False)
    
    for i, var in enumerate(variables, 1):
        print(f"   Variable {i}:")
        print(f"     variable_id: {var['variable_id']}")
        print(f"     element_id: {var['element_id']}")
        print(f"     variable_name: {var['variable_name']}")
        print(f"     variable_type: {var['variable_type']}")
        print(f"     default_value: {var['default_value']}")
        print(f"     is_required: {var['is_required']}")
        print()
    
    # 3. Variable options table
    print("3️⃣ VARIABLE_OPTIONS TABLE:")
    print("-" * 32)
    
    for var in variables:
        options = db.get_variable_options(var['variable_id'])
        if options:
            print(f"   Options for '{var['variable_name']}':")
            for opt in options:
                print(f"     option_id: {opt['option_id']}")
                print(f"     variable_id: {opt['variable_id']}")
                print(f"     option_value: {opt['option_value']}")
                print(f"     option_label: {opt['option_label']}")
                print(f"     display_order: {opt['display_order']}")
                print(f"     is_default: {opt['is_default']}")
                print("     ---")
            print()
        else:
            print(f"   '{var['variable_name']}': No options (free text input)")
            print()
    
    # 4. Summary statistics
    print("📈 SUMMARY:")
    print("-" * 15)
    total_variables = len(variables)
    total_options = sum(len(db.get_variable_options(v['variable_id'])) for v in variables)
    variables_with_options = len([v for v in variables if db.get_variable_options(v['variable_id'])])
    
    print(f"   Total variables: {total_variables}")
    print(f"   Variables with options: {variables_with_options}")
    print(f"   Total options: {total_options}")
    print(f"   Database file: {db_path}")

if __name__ == "__main__":
    test_single_element()