#!/usr/bin/env python3
"""
Test: Smart Variable Handling for Mail Merge
Tests different approaches to handle elements with different variable counts
"""

import os
import sys
import sqlite3
import pandas as pd
import json
from pathlib import Path

# Add directories to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'src'))

from src.db_manager import DatabaseManager

def test_smart_variable_handling():
    """
    Test multiple approaches to handle different variable counts per element
    """
    
    print("🧪 TESTING SMART VARIABLE HANDLING FOR MAIL MERGE")
    print("=" * 70)
    
    # Use existing test database
    test_db_path = "tests/test_e2e.db"
    
    if not os.path.exists(test_db_path):
        print("❌ Test database not found. Run test_end_to_end.py first.")
        return
    
    print("📊 Using existing test database...")
    
    def get_element_data(db_path, project_code):
        """Get organized element data from database"""
        conn = sqlite3.connect(db_path)
        
        # Get elements grouped by element type (not just category)
        query = """
        SELECT 
            p.project_name, p.project_code,
            e.element_id, e.element_code, e.element_name, e.category,
            pe.project_element_id, pe.instance_code, pe.instance_name, pe.location,
            dv.description_template, rd.rendered_text as description,
            ev.variable_name, ev.variable_type, ev.unit,
            COALESCE(pev.value, ev.default_value) as variable_value
        FROM project_elements pe
        JOIN projects p ON pe.project_id = p.project_id
        JOIN elements e ON pe.element_id = e.element_id
        JOIN description_versions dv ON pe.description_version_id = dv.version_id
        LEFT JOIN rendered_descriptions rd ON pe.project_element_id = rd.project_element_id
        LEFT JOIN element_variables ev ON e.element_id = ev.element_id
        LEFT JOIN project_element_values pev ON pe.project_element_id = pev.project_element_id 
                                            AND ev.variable_id = pev.variable_id
        WHERE p.project_code = ?
        ORDER BY e.element_code, pe.instance_code, ev.display_order
        """
        
        df = pd.read_sql_query(query, conn, params=(project_code,))
        conn.close()
        return df
    
    def approach1_element_type_sheets(df, output_file):
        """APPROACH 1: Separate sheet per element type with only their variables"""
        print("\n📋 APPROACH 1: Separate sheets per element type")
        
        element_types = df['element_code'].unique()
        
        with pd.ExcelWriter(f"excel_exports/{output_file}_APPROACH1.xlsx", engine='openpyxl') as writer:
            
            for element_code in element_types:
                element_data = df[df['element_code'] == element_code].copy()
                
                if element_data.empty:
                    continue
                
                # Get unique instances for this element type
                instances = element_data['project_element_id'].unique()
                rows = []
                
                # Get variables for this element type
                element_vars = element_data['variable_name'].dropna().unique()
                
                print(f"   📄 Element {element_code}: {len(instances)} instances, {len(element_vars)} variables")
                print(f"      Variables: {list(element_vars)}")
                
                for instance_id in instances:
                    instance_data = element_data[element_data['project_element_id'] == instance_id]
                    
                    # Base instance info
                    base_info = instance_data.iloc[0]
                    row = {
                        'Project_Name': base_info['project_name'],
                        'Project_Code': base_info['project_code'],
                        'Category': base_info['category'],
                        'Element_Code': base_info['element_code'],
                        'Element_Name': base_info['element_name'],
                        'Instance_Code': base_info['instance_code'],
                        'Instance_Name': base_info['instance_name'],
                        'Location': base_info['location'],
                        'Description': base_info['description'],
                    }
                    
                    # Add variables specific to this element type
                    for _, var_row in instance_data.iterrows():
                        if pd.notna(var_row['variable_name']) and pd.notna(var_row['variable_value']):
                            var_name = var_row['variable_name'].upper().replace(' ', '_')
                            var_value = var_row['variable_value']
                            if var_row['unit']:
                                row[f"{var_name}"] = var_value
                                row[f"{var_name}_UNIT"] = var_row['unit']
                            else:
                                row[f"{var_name}"] = var_value
                    
                    rows.append(row)
                
                if rows:
                    df_element = pd.DataFrame(rows)
                    sheet_name = f"ELEM_{element_code}"[:31]
                    df_element.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"      ✅ Sheet {sheet_name}: {len(df_element)} rows, {len(df_element.columns)} columns")
    
    def approach2_variables_as_json(df, output_file):
        """APPROACH 2: Variables as JSON text in single column"""
        print("\n📋 APPROACH 2: Variables as JSON in single column")
        
        instances = df['project_element_id'].unique()
        rows = []
        
        for instance_id in instances:
            instance_data = df[df['project_element_id'] == instance_id]
            base_info = instance_data.iloc[0]
            
            # Collect variables as dictionary
            variables = {}
            for _, var_row in instance_data.iterrows():
                if pd.notna(var_row['variable_name']) and pd.notna(var_row['variable_value']):
                    var_info = {
                        'value': var_row['variable_value'],
                        'type': var_row['variable_type'],
                        'unit': var_row['unit']
                    }
                    variables[var_row['variable_name']] = var_info
            
            row = {
                'Project_Name': base_info['project_name'],
                'Project_Code': base_info['project_code'],
                'Category': base_info['category'],
                'Element_Code': base_info['element_code'],
                'Element_Name': base_info['element_name'],
                'Instance_Code': base_info['instance_code'],
                'Instance_Name': base_info['instance_name'],
                'Location': base_info['location'],
                'Description': base_info['description'],
                'Variables_JSON': json.dumps(variables, ensure_ascii=False, indent=2),
                'Variables_Count': len(variables)
            }
            rows.append(row)
        
        df_json = pd.DataFrame(rows)
        
        with pd.ExcelWriter(f"excel_exports/{output_file}_APPROACH2.xlsx", engine='openpyxl') as writer:
            df_json.to_excel(writer, sheet_name="ALL_ELEMENTS", index=False)
            
            # Category sheets
            for category in df_json['Category'].unique():
                df_cat = df_json[df_json['Category'] == category]
                sheet_name = f"CAT_{category.replace(' ', '_')}"[:31]
                df_cat.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"   ✅ Created Excel with JSON variables")
        print(f"      • {len(df_json)} rows total")
        print(f"      • Variables stored as structured JSON")
        
        # Show sample JSON
        if len(df_json) > 0:
            sample_json = df_json.iloc[0]['Variables_JSON']
            print(f"      • Sample JSON: {sample_json[:100]}...")
    
    def approach3_key_value_rows(df, output_file):
        """APPROACH 3: Key-value pairs as separate rows"""
        print("\n📋 APPROACH 3: Key-value pairs as separate rows")
        
        instances = df['project_element_id'].unique()
        element_rows = []
        variable_rows = []
        
        for instance_id in instances:
            instance_data = df[df['project_element_id'] == instance_id]
            base_info = instance_data.iloc[0]
            
            # Element master row
            element_row = {
                'Type': 'ELEMENT',
                'Project_Name': base_info['project_name'],
                'Project_Code': base_info['project_code'],
                'Category': base_info['category'],
                'Element_Code': base_info['element_code'],
                'Element_Name': base_info['element_name'],
                'Instance_Code': base_info['instance_code'],
                'Instance_Name': base_info['instance_name'],
                'Location': base_info['location'],
                'Description': base_info['description'],
                'Variable_Name': None,
                'Variable_Value': None,
                'Variable_Unit': None
            }
            element_rows.append(element_row)
            
            # Variable rows
            for _, var_row in instance_data.iterrows():
                if pd.notna(var_row['variable_name']) and pd.notna(var_row['variable_value']):
                    var_detail_row = element_row.copy()
                    var_detail_row.update({
                        'Type': 'VARIABLE',
                        'Variable_Name': var_row['variable_name'],
                        'Variable_Value': var_row['variable_value'],
                        'Variable_Unit': var_row['unit']
                    })
                    variable_rows.append(var_detail_row)
        
        # Combine all rows
        all_rows = element_rows + variable_rows
        df_kv = pd.DataFrame(all_rows)
        
        with pd.ExcelWriter(f"excel_exports/{output_file}_APPROACH3.xlsx", engine='openpyxl') as writer:
            df_kv.to_excel(writer, sheet_name="ALL_DATA", index=False)
            
            # Elements only
            df_elements = df_kv[df_kv['Type'] == 'ELEMENT']
            df_elements.to_excel(writer, sheet_name="ELEMENTS_ONLY", index=False)
            
            # Variables only  
            df_variables = df_kv[df_kv['Type'] == 'VARIABLE']
            df_variables.to_excel(writer, sheet_name="VARIABLES_ONLY", index=False)
        
        print(f"   ✅ Created key-value structure")
        print(f"      • {len(element_rows)} element rows")
        print(f"      • {len(variable_rows)} variable rows")
        print(f"      • {len(all_rows)} total rows")
    
    # Get data and test approaches
    print("\n📈 Getting element data from database...")
    df = get_element_data(test_db_path, 'TEST-2025')
    
    print(f"   📊 Found data:")
    print(f"      • {len(df)} total rows")
    print(f"      • {df['element_code'].nunique()} element types")
    print(f"      • {df['project_element_id'].nunique()} element instances")
    print(f"      • {df['variable_name'].nunique()} unique variables")
    
    # Test all approaches
    approach1_element_type_sheets(df, "TEST-2025")
    approach2_variables_as_json(df, "TEST-2025")
    approach3_key_value_rows(df, "TEST-2025")
    
    print("\n🎯 APPROACH COMPARISON:")
    print("   1️⃣ Element Type Sheets:")
    print("      ✅ No empty columns - each sheet only has relevant variables")
    print("      ✅ Clean Mail Merge - predictable field names per element type")
    print("      ❌ More sheets to manage")
    print("      ❌ Need to know element type to pick sheet")
    
    print("   2️⃣ JSON Variables:")
    print("      ✅ Compact - all data in standard columns")
    print("      ✅ Flexible - can handle any variable structure")
    print("      ❌ JSON not Mail Merge friendly")
    print("      ❌ Needs parsing in Word")
    
    print("   3️⃣ Key-Value Rows:")
    print("      ✅ Normalized - no empty columns")
    print("      ✅ Can query specific variables easily")
    print("      ❌ Complex Mail Merge - need multiple data sources")
    print("      ❌ More rows to process")
    
    print("\n🏆 RECOMMENDATION: Approach 1 (Element Type Sheets)")
    print("   Best for Mail Merge: Each element type gets clean sheet with only its variables")
    
    return ["APPROACH1", "APPROACH2", "APPROACH3"]

if __name__ == "__main__":
    try:
        result = test_smart_variable_handling()
        print(f"\n🎉 SMART VARIABLE HANDLING TEST COMPLETED!")
        print(f"   📁 Generated approaches: {result}")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)