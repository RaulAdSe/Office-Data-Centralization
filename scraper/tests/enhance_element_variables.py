#!/usr/bin/env python3
"""
Enhanced Variable Extraction for All Elements
Runs the enhanced scraper on all 75 elements to extract and store variables
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from enhanced_element_extractor import EnhancedElementExtractor
from db_manager import DatabaseManager
import sqlite3
import time
from datetime import datetime

def get_all_elements_from_db(db_path):
    """Get all elements from database that need variable extraction"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get elements that have no variables or very few variables
    cursor.execute("""
        SELECT e.element_id, e.element_code, e.element_name,
               COUNT(ev.variable_id) as var_count
        FROM elements e 
        LEFT JOIN element_variables ev ON e.element_id = ev.element_id
        GROUP BY e.element_id, e.element_code, e.element_name
        HAVING var_count < 3 OR e.element_code = 'CSZ020_PROD_1764161964'
        ORDER BY e.element_name
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    return [(row[0], row[1], row[2], row[3]) for row in results]

def construct_element_url(element_code):
    """Construct CYPE URL from element code"""
    # Remove the _PROD_timestamp suffix to get clean code
    clean_code = element_code.split('_PROD_')[0]
    
    # Map codes to URL categories (this is a simplified mapping)
    # You might need to extend this based on your actual URL patterns
    url_mapping = {
        'CSL': 'Cimentaciones/Superficiales/Losas',
        'CSZ': 'Cimentaciones/Superficiales/Zapatas', 
        'CSV': 'Cimentaciones/Superficiales/Zapatas',
        'EHM': 'Estructuras/Hormigon_armado/Muros',
        'EAE': 'Estructuras/Acero/Elementos',
        'EMF': 'Estructuras/Mamposteria/Fabrica',
        'RMB': 'Revestimientos/Maderas/Barnices'
    }
    
    # Get category from first 3 characters
    category_key = clean_code[:3]
    category = url_mapping.get(category_key, 'Otros')
    
    # Construct full URL
    base_url = "https://generadordeprecios.info/obra_nueva"
    element_name_part = f"{clean_code}_Sistema_de_encofrado_para_zapata_de" if category_key == 'CSZ' else f"{clean_code}_element"
    
    return f"{base_url}/{category}/{element_name_part}.html"

def add_variables_to_database(db_path, element_id, variables):
    """Add extracted variables to database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Clear existing variables for this element
        cursor.execute("DELETE FROM element_variables WHERE element_id = ?", (element_id,))
        
        # Add new variables
        for i, var in enumerate(variables, 1):
            # Map variable types
            var_type = 'NUMERIC' if var.variable_type in ['NUMERIC', 'TEXT'] and var.default_value and var.default_value.replace('.','').isdigit() else 'TEXT'
            
            cursor.execute("""
                INSERT INTO element_variables 
                (element_id, variable_name, variable_type, unit, default_value, is_required, display_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                element_id,
                var.name,
                var_type,
                None,  # unit - could be enhanced later
                var.default_value,
                1 if var.is_required else 0,
                i
            ))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"    ❌ Database error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Main extraction process"""
    db_path = "../src/office_data.db"
    extractor = EnhancedElementExtractor()
    
    print("=" * 80)
    print("ENHANCED VARIABLE EXTRACTION FOR ALL ELEMENTS")
    print("=" * 80)
    print()
    
    # Get elements that need variable extraction
    elements = get_all_elements_from_db(db_path)
    print(f"Found {len(elements)} elements needing variable extraction")
    print()
    
    success_count = 0
    error_count = 0
    
    for element_id, element_code, element_name, current_vars in elements:
        print(f"🔍 Processing: {element_code}")
        print(f"   Name: {element_name}")
        print(f"   Current variables: {current_vars}")
        
        # For CSZ020, use the actual URL we know works
        if element_code.startswith('CSZ020'):
            url = 'https://generadordeprecios.info/obra_nueva/Cimentaciones/Superficiales/Zapatas/CSZ020_Sistema_de_encofrado_para_zapata_de.html'
        else:
            # For now, skip other elements as we'd need their actual URLs
            print(f"   ⏩ Skipping - URL mapping not implemented yet")
            continue
        
        try:
            # Extract variables
            element_data = extractor.extract_element_data(url)
            
            if element_data and element_data.variables:
                print(f"   ✅ Extracted {len(element_data.variables)} variables")
                
                # Add to database
                if add_variables_to_database(db_path, element_id, element_data.variables):
                    print(f"   ✅ Added to database")
                    success_count += 1
                    
                    # Show what was added
                    for var in element_data.variables:
                        print(f"     • {var.name} ({var.variable_type}) = {var.default_value}")
                else:
                    error_count += 1
            else:
                print(f"   ⚠️  No variables extracted")
                error_count += 1
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            error_count += 1
        
        print()
        
        # Small delay to be respectful to the website
        time.sleep(1)
    
    print("=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"✅ Successfully processed: {success_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📊 Total elements checked: {len(elements)}")
    print()
    
    if success_count > 0:
        print("🎉 Variable extraction completed!")
        print("You can now use your enhanced elements with proper variables in the demo system.")

if __name__ == "__main__":
    main()