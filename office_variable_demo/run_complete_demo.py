#!/usr/bin/env python3
"""
Complete Demo of Office Variable System
Shows all features using real office_data.db with 75 elements
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from api.office_db_manager import OfficeDBManager
from datetime import datetime

def demo_complete_system():
    """Complete demonstration of the variable system"""
    
    db = OfficeDBManager()
    
    print("=" * 80)
    print("OFFICE VARIABLE SYSTEM - COMPLETE DEMO")
    print("=" * 80)
    print()
    
    # 1. Show database overview
    print("📊 DATABASE OVERVIEW")
    print("-" * 40)
    
    elements = db.get_all_elements()
    print(f"Total Elements: {len(elements)}")
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM element_variables")
        var_count = cursor.fetchone()[0]
        print(f"Total Variables: {var_count}")
        
        cursor.execute("SELECT COUNT(*) FROM description_versions WHERE is_active = 1")
        template_count = cursor.fetchone()[0]
        print(f"Active Templates: {template_count}")
        
        cursor.execute("SELECT COUNT(*) FROM projects")
        project_count = cursor.fetchone()[0]
        print(f"Existing Projects: {project_count}")
    
    print()
    
    # 2. Show sample elements with variables
    print("🏗️  SAMPLE ELEMENTS & THEIR VARIABLES")
    print("-" * 40)
    
    sample_elements = elements[:3]
    for element in sample_elements:
        print(f"\n🔹 {element.element_name}")
        print(f"   Code: {element.element_code}")
        if element.price:
            print(f"   Price: €{element.price:.2f}")
        
        variables = db.get_element_variables(element.element_id)
        print(f"   Variables: {len(variables)}")
        for var in variables:
            req = "Required" if var.is_required else "Optional"
            unit = f" [{var.unit}]" if var.unit else ""
            print(f"     • {var.variable_name} ({var.variable_type}){unit} - {req}")
        
        template = db.get_active_template(element.element_id)
        if template:
            preview = template[:100] + "..." if len(template) > 100 else template
            print(f"   Template: {preview}")
    
    print()
    
    # 3. Create a comprehensive demo project
    print("🚧 CREATING DEMO PROJECT")
    print("-" * 40)
    
    project_code = f"DEMO-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    project_id = db.create_project(
        project_code, 
        "Complete Demo Project", 
        "Demo Office Building"
    )
    print(f"✅ Created project: {project_code} (ID: {project_id})")
    
    # 4. Add multiple elements to project
    print("\n🏗️  ADDING ELEMENTS TO PROJECT")
    print("-" * 40)
    
    demo_elements = [
        ("CSL010_PROD_1764161964", "FOUNDATION-01", "Main Foundation"),
        ("EHM010_PROD_1764161964", "WALL-01", "Exterior Wall"),
        ("RMB025_PROD_1764161964", "FINISH-01", "Wood Finish"),
    ]
    
    project_element_ids = []
    
    for element_code, instance_code, instance_name in demo_elements:
        try:
            pe_id = db.add_project_element(project_id, element_code, instance_code, instance_name)
            project_element_ids.append(pe_id)
            
            element = db.get_element_by_code(element_code)
            print(f"✅ Added {element.element_name} as {instance_code}")
            
            # Show what variables need to be filled
            variables = db.get_element_variables(element.element_id)
            print(f"   Variables to fill: {[v.variable_name for v in variables]}")
            
        except Exception as e:
            print(f"❌ Error adding {element_code}: {e}")
    
    print()
    
    # 5. Fill variable values
    print("📝 FILLING VARIABLE VALUES")
    print("-" * 40)
    
    # Sample values for different element types
    sample_values = {
        "codigo": "IIa",
        "variable": "liso",
        "variable_2": "rugoso", 
        "dimension": "300x200"
    }
    
    for pe_id in project_element_ids:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pe.instance_code, e.element_name, e.element_id
                FROM project_elements pe
                JOIN elements e ON pe.element_id = e.element_id
                WHERE pe.project_element_id = ?
            """, (pe_id,))
            instance_info = cursor.fetchone()
        
        if instance_info:
            instance_code, element_name, element_id = instance_info
            variables = db.get_element_variables(element_id)
            
            print(f"\n🔹 {instance_code} ({element_name})")
            
            for var in variables:
                # Pick appropriate sample value
                value = sample_values.get(var.variable_name, f"demo_{var.variable_name}")
                
                try:
                    db.set_project_element_value(pe_id, var.variable_name, value)
                    print(f"   ✅ {var.variable_name} = {value}")
                except Exception as e:
                    print(f"   ❌ Failed to set {var.variable_name}: {e}")
    
    print()
    
    # 6. Render descriptions
    print("🎨 RENDERED DESCRIPTIONS")
    print("-" * 40)
    
    for pe_id in project_element_ids:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pe.instance_code, e.element_name
                FROM project_elements pe
                JOIN elements e ON pe.element_id = e.element_id
                WHERE pe.project_element_id = ?
            """, (pe_id,))
            instance_info = cursor.fetchone()
        
        if instance_info:
            instance_code, element_name = instance_info
            
            try:
                rendered = db.render_description(pe_id)
                print(f"\n🔹 {instance_code} - {element_name}")
                print("   Template Result:")
                print(f"   {rendered[:200]}{'...' if len(rendered) > 200 else ''}")
                
            except Exception as e:
                print(f"   ❌ Failed to render: {e}")
    
    print()
    
    # 7. Show project summary
    print("📋 PROJECT SUMMARY")
    print("-" * 40)
    
    project_elements = db.get_project_elements(project_id)
    
    print(f"Project: {project_code}")
    print(f"Total Elements: {len(project_elements)}")
    
    for pe in project_elements:
        print(f"\n• {pe.instance_code} ({pe.element_code})")
        print(f"  Variables: {list(pe.values.keys())}")
        print(f"  Values: {list(pe.values.values())}")
    
    print()
    
    # 8. Database statistics
    print("📊 FINAL STATISTICS")
    print("-" * 40)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM projects")
        final_projects = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM project_elements")
        final_pe = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM project_element_values")
        final_values = cursor.fetchone()[0]
    
    print(f"Projects: {final_projects}")
    print(f"Project Elements: {final_pe}")
    print(f"Variable Values: {final_values}")
    
    print()
    print("=" * 80)
    print("🎉 DEMO COMPLETE!")
    print(f"Demo project created: {project_code}")
    print("You can now:")
    print("1. Run 'python3 ui/app.py' to start the web interface")
    print("2. Browse to http://localhost:5000 to see the UI")
    print("3. Explore your 75 elements and create more projects!")
    print("=" * 80)

if __name__ == "__main__":
    demo_complete_system()