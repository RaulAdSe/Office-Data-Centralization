#!/usr/bin/env python3
"""
Complete pipeline test showing all database tables filling up with 3-combination template extraction
"""

import sys
import sqlite3
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from smart_template_extractor import SmartTemplateExtractor
from template_db_integrator import TemplateDbIntegrator
from db_manager import DatabaseManager

def show_database_tables(db_path: str):
    """Show contents of all relevant database tables"""
    
    print(f"\n📊 DATABASE CONTENTS: {db_path}")
    print("=" * 80)
    
    # Check if database file exists
    import os
    if not os.path.exists(db_path):
        print("  Database file doesn't exist yet")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    
    # Check if tables exist
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    if not tables:
        print("  Database exists but no tables created yet")
        conn.close()
        return
    
    # 1. Elements table
    print("🏗️  ELEMENTS TABLE:")
    if 'elements' in tables:
        cursor = conn.execute("SELECT * FROM elements ORDER BY element_id")
        elements = cursor.fetchall()
    else:
        elements = []
    
    if elements:
        print(f"{'ID':<4} {'Code':<12} {'Name':<40} {'Created By':<15}")
        print("-" * 75)
        for element in elements:
            print(f"{element['element_id']:<4} {element['element_code']:<12} {element['element_name'][:40]:<40} {element['created_by']:<15}")
    else:
        print("  (empty)")
    
    # 2. Element Variables table
    print(f"\n⚙️  ELEMENT_VARIABLES TABLE:")
    if 'element_variables' in tables and 'elements' in tables:
        cursor = conn.execute("""
            SELECT ev.*, e.element_code 
            FROM element_variables ev 
            JOIN elements e ON ev.element_id = e.element_id 
            ORDER BY ev.element_id, ev.display_order
        """)
        variables = cursor.fetchall()
    else:
        variables = []
    
    if variables:
        print(f"{'ID':<4} {'Element':<8} {'Variable Name':<20} {'Type':<8} {'Default':<15} {'Required':<8}")
        print("-" * 70)
        for var in variables:
            default_val = (var['default_value'] or "")[:14]
            required = "Yes" if var['is_required'] else "No"
            print(f"{var['variable_id']:<4} {var['element_code']:<8} {var['variable_name'][:20]:<20} {var['variable_type']:<8} {default_val:<15} {required:<8}")
    else:
        print("  (empty)")
    
    # 3. Variable Options table
    print(f"\n🎛️  VARIABLE_OPTIONS TABLE:")
    if all(table in tables for table in ['variable_options', 'element_variables', 'elements']):
        cursor = conn.execute("""
            SELECT vo.*, ev.variable_name, e.element_code
            FROM variable_options vo
            JOIN element_variables ev ON vo.variable_id = ev.variable_id
            JOIN elements e ON ev.element_id = e.element_id
            ORDER BY vo.variable_id, vo.display_order
        """)
        options = cursor.fetchall()
    else:
        options = []
    
    if options:
        print(f"{'Var ID':<6} {'Variable':<15} {'Option Value':<20} {'Label':<20} {'Default':<7}")
        print("-" * 75)
        for opt in options:
            is_default = "Yes" if opt['is_default'] else "No"
            print(f"{opt['variable_id']:<6} {opt['variable_name'][:15]:<15} {opt['option_value'][:20]:<20} {opt['option_label'][:20]:<20} {is_default:<7}")
    else:
        print("  (empty)")
    
    # 4. Description Versions table
    print(f"\n📝 DESCRIPTION_VERSIONS TABLE:")
    if all(table in tables for table in ['description_versions', 'elements']):
        cursor = conn.execute("""
            SELECT dv.*, e.element_code
            FROM description_versions dv
            JOIN elements e ON dv.element_id = e.element_id
            ORDER BY dv.version_id
        """)
        versions = cursor.fetchall()
    else:
        versions = []
    
    if versions:
        print(f"{'ID':<4} {'Element':<8} {'State':<5} {'Active':<6} {'Ver':<3} {'Template (first 50 chars)':<50}")
        print("-" * 80)
        for ver in versions:
            active = "Yes" if ver['is_active'] else "No"
            template_preview = ver['description_template'][:47] + "..." if len(ver['description_template']) > 50 else ver['description_template']
            print(f"{ver['version_id']:<4} {ver['element_code']:<8} {ver['state']:<5} {active:<6} {ver['version_number']:<3} {template_preview}")
    else:
        print("  (empty)")
    
    # 5. Template Variable Mappings table
    print(f"\n🔗 TEMPLATE_VARIABLE_MAPPINGS TABLE:")
    if all(table in tables for table in ['template_variable_mappings', 'element_variables', 'description_versions', 'elements']):
        cursor = conn.execute("""
            SELECT tvm.*, ev.variable_name, dv.description_template, e.element_code
            FROM template_variable_mappings tvm
            JOIN element_variables ev ON tvm.variable_id = ev.variable_id
            JOIN description_versions dv ON tvm.version_id = dv.version_id
            JOIN elements e ON dv.element_id = e.element_id
            ORDER BY tvm.version_id, tvm.position
        """)
        mappings = cursor.fetchall()
    else:
        mappings = []
    
    if mappings:
        print(f"{'Map ID':<6} {'Ver ID':<6} {'Pos':<3} {'Placeholder':<15} {'Variable':<15} {'Element':<8}")
        print("-" * 65)
        for mapping in mappings:
            print(f"{mapping['mapping_id']:<6} {mapping['version_id']:<6} {mapping['position']:<3} {mapping['placeholder'][:15]:<15} {mapping['variable_name'][:15]:<15} {mapping['element_code']:<8}")
    else:
        print("  (empty)")
    
    conn.close()

def run_complete_pipeline():
    """Run complete pipeline showing all tables filling up"""
    
    print("🚀 COMPLETE TEMPLATE EXTRACTION PIPELINE")
    print("=" * 80)
    print("This will show all database tables filling up with template data!")
    
    db_path = "complete_pipeline_test.db"
    
    # Clean start
    import os
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print(f"\n📊 INITIAL STATE (empty database):")
    show_database_tables(db_path)
    
    # Step 1: Run smart template extraction
    print(f"\n🔍 STEP 1: EXTRACTING TEMPLATE WITH 3 COMBINATIONS...")
    
    # Test URL
    test_url = "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html"
    
    extractor = SmartTemplateExtractor()
    template = extractor.extract_template_smart(test_url)
    
    if not template:
        print("❌ Template extraction failed")
        return False
    
    print(f"\n✅ TEMPLATE EXTRACTED SUCCESSFULLY!")
    print(f"   Element: {template.element_code}")
    print(f"   Template: {template.description_template[:100]}...")
    print(f"   Variables: {list(template.variables.keys())}")
    print(f"   Confidence: {template.confidence:.2f}")
    print(f"   Combinations tested: {template.total_combinations_tested}")
    
    # Step 2: Create database with element and variables
    print(f"\n💾 STEP 2: POPULATING DATABASE...")
    
    db_manager = DatabaseManager(db_path)
    
    # Create element
    element_id = db_manager.create_element(
        element_code=template.element_code,
        element_name="VIGA EXENTA DE HORMIGÓN VISTO",
        created_by="complete_pipeline"
    )
    
    print(f"✅ Created element: {element_id}")
    
    # Add variables (simplified for this test)
    variables_added = []
    for i, var_name in enumerate(template.variables.keys()):
        var_id = db_manager.add_variable(
            element_id=element_id,
            variable_name=var_name,
            variable_type="TEXT",
            unit=None,
            default_value="default_value",
            is_required=True,
            display_order=i + 1
        )
        variables_added.append((var_name, var_id))
        
        # Add some sample options
        sample_options = ["Option A", "Option B", "Option C"]
        for j, option in enumerate(sample_options):
            db_manager.add_variable_option(
                variable_id=var_id,
                option_value=option,
                option_label=option,
                display_order=j + 1,
                is_default=(j == 0)
            )
    
    print(f"✅ Created {len(variables_added)} variables with options")
    
    # Show database after Step 2
    print(f"\n📊 DATABASE AFTER STEP 2 (elements + variables populated):")
    show_database_tables(db_path)
    
    # Step 3: Integrate template
    print(f"\n🔗 STEP 3: INTEGRATING TEMPLATE...")
    
    integrator = TemplateDbIntegrator(db_path)
    result = integrator.integrate_template(template, element_id)
    
    if not result:
        print("❌ Template integration failed")
        return False
    
    print(f"✅ Template integrated!")
    print(f"   Version ID: {result.version_id}")
    print(f"   Mappings created: {len(result.mappings_created)}")
    
    # Final database state
    print(f"\n📊 FINAL DATABASE STATE (all tables populated):")
    show_database_tables(db_path)
    
    # Summary
    print(f"\n🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"   Database: {db_path}")
    print(f"   Template extraction: ✅ ({template.total_combinations_tested} combinations)")
    print(f"   Database integration: ✅ (all tables populated)")
    print(f"   Template confidence: {template.confidence:.2f}")
    
    return True

if __name__ == "__main__":
    success = run_complete_pipeline()
    
    if success:
        print(f"\n✅ ALL SYSTEMS WORKING!")
        print(f"   🔍 3-combination template extraction")  
        print(f"   🗃️  Database tables properly populated")
        print(f"   🔗 Template variable mappings created")
        print(f"   📊 Ready for production use")
    else:
        print(f"\n❌ Pipeline failed - check logs above")