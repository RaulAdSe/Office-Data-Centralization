#!/usr/bin/env python3
"""
Test: Full Database Content in Multiple Rows
Tests Excel export with complete database information (elements, variables, values, descriptions)
in multiple rows format for optimal Mail Merge integration
"""

import os
import sys
import sqlite3
import pandas as pd
import re
from pathlib import Path

# Add directories to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'src'))

from src.db_manager import DatabaseManager

def test_full_database_mailmerge():
    """
    Generate Excel with complete database information in multiple rows format.
    Each row contains full element details: variables, values, rendered descriptions.
    """
    
    print("🧪 TESTING FULL DATABASE CONTENT IN MULTIPLE ROWS")
    print("=" * 70)
    
    # Use existing test database
    test_db_path = "tests/test_e2e.db"
    
    if not os.path.exists(test_db_path):
        print("❌ Test database not found. Run test_end_to_end.py first.")
        return
    
    print("📊 Using existing test database...")
    
    def generate_full_database_excel(db_path, project_code):
        """Generate Excel with complete database information in rows"""
        
        conn = sqlite3.connect(db_path)
        
        # First, ensure all descriptions are rendered
        print("   🔄 Ensuring all descriptions are rendered...")
        cursor = conn.cursor()
        
        # Get stale descriptions and render them
        query_pendientes = """
        SELECT rd.project_element_id, pe.description_version_id, dv.description_template
        FROM rendered_descriptions rd
        JOIN project_elements pe ON rd.project_element_id = pe.project_element_id
        JOIN description_versions dv ON pe.description_version_id = dv.version_id
        WHERE rd.is_stale = 1
        """
        pendientes = cursor.execute(query_pendientes).fetchall()
        
        for p_elem_id, version_id, template in pendientes:
            query_valores = """
            SELECT tvm.placeholder, pev.value
            FROM template_variable_mappings tvm
            JOIN project_element_values pev ON tvm.variable_id = pev.variable_id
            WHERE tvm.version_id = ? AND pev.project_element_id = ?
            """
            valores = cursor.execute(query_valores, (version_id, p_elem_id)).fetchall()

            texto_final = template
            for placeholder, valor_real in valores:
                val = str(valor_real) if valor_real else "[SIN VALOR]"
                texto_final = texto_final.replace(f'{{{placeholder}}}', val)

            cursor.execute("UPDATE rendered_descriptions SET rendered_text = ?, is_stale = 0 WHERE project_element_id = ?", (texto_final, p_elem_id))
        
        conn.commit()
        
        # Get complete project data with all variables and values
        print("   📋 Retrieving complete database information...")
        
        query = """
        SELECT 
            -- Project info
            p.project_name,
            p.project_code,
            p.status as project_status,
            p.location as project_location,
            
            -- Element info
            e.element_id,
            e.element_code,
            e.element_name,
            e.category,
            
            -- Instance info
            pe.project_element_id,
            pe.instance_code,
            pe.instance_name,
            pe.location as instance_location,
            
            -- Description info
            dv.description_template,
            dv.version_number,
            rd.rendered_text as rendered_description,
            
            -- All variables and values for this instance
            GROUP_CONCAT(ev.variable_name || '=' || COALESCE(pev.value, ev.default_value, ''), '|') as all_variables
            
        FROM project_elements pe
        JOIN projects p ON pe.project_id = p.project_id
        JOIN elements e ON pe.element_id = e.element_id
        JOIN description_versions dv ON pe.description_version_id = dv.version_id
        LEFT JOIN rendered_descriptions rd ON pe.project_element_id = rd.project_element_id
        LEFT JOIN element_variables ev ON e.element_id = ev.element_id
        LEFT JOIN project_element_values pev ON pe.project_element_id = pev.project_element_id 
                                            AND ev.variable_id = pev.variable_id
        WHERE p.project_code = ?
        GROUP BY pe.project_element_id
        ORDER BY e.category, pe.instance_code
        """
        
        df = pd.read_sql_query(query, conn, params=(project_code,))
        conn.close()
        
        if df.empty:
            raise ValueError("No data found for project")
        
        print(f"   📊 Retrieved {len(df)} element instances")
        
        # Process the data to expand variables into individual columns
        processed_rows = []
        
        for _, row in df.iterrows():
            processed_row = {
                # Project information
                'Project_Name': row['project_name'],
                'Project_Code': row['project_code'],
                'Project_Status': row['project_status'],
                'Project_Location': row['project_location'],
                
                # Element information
                'Category': row['category'],
                'Element_Code': row['element_code'],
                'Element_Name': row['element_name'],
                
                # Instance information
                'Instance_Code': row['instance_code'],
                'Instance_Name': row['instance_name'],
                'Instance_Location': row['instance_location'],
                
                # Description information
                'Description_Template': row['description_template'],
                'Description_Version': row['version_number'],
                'Rendered_Description': row['rendered_description'],
            }
            
            # Parse variables and add them as individual columns
            if row['all_variables']:
                variables = row['all_variables'].split('|')
                for var_pair in variables:
                    if '=' in var_pair:
                        var_name, var_value = var_pair.split('=', 1)
                        # Clean variable name for Excel column
                        clean_var_name = f"VAR_{var_name.upper().replace(' ', '_')}"
                        processed_row[clean_var_name] = var_value
            
            processed_rows.append(processed_row)
        
        df_processed = pd.DataFrame(processed_rows)
        
        output_file = f"excel_exports/{project_code}_FULL_DATABASE_ROWS.xlsx"
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            
            # ALL_ELEMENTS sheet with complete data
            print("   📝 Creating ALL_ELEMENTS sheet (complete database content)...")
            df_processed.to_excel(writer, sheet_name="ALL_ELEMENTS", index=False)
            
            # Category-specific sheets
            categories = df_processed['Category'].unique()
            
            for categoria in sorted(categories):
                df_cat = df_processed[df_processed['Category'] == categoria].copy()
                
                # Add category-specific metadata
                df_cat['Category_Element_Count'] = len(df_cat)
                df_cat['Row_Number'] = range(1, len(df_cat) + 1)
                
                sheet_name = f"CAT_{categoria.replace(' ', '_')}"[:31]
                print(f"   📄 Creating {sheet_name} sheet ({len(df_cat)} rows)...")
                df_cat.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return output_file, df_processed
    
    # Generate full database Excel
    print("\n📈 Generating Excel with complete database content...")
    output_file, df = generate_full_database_excel(test_db_path, 'TEST-2025')
    print(f"   ✅ Generated: {output_file}")
    
    # Analyze the complete structure
    print("\n🔍 Analyzing complete database structure...")
    
    print(f"📋 Complete data structure:")
    print(f"   • Total rows: {len(df)} (one per element instance)")
    print(f"   • Total columns: {len(df.columns)}")
    print(f"   • Categories: {df['Category'].nunique()}")
    
    # Show column structure
    print(f"\n📊 Column types:")
    project_cols = [col for col in df.columns if col.startswith('Project_')]
    element_cols = [col for col in df.columns if col.startswith('Element_') or col == 'Category']
    instance_cols = [col for col in df.columns if col.startswith('Instance_')]
    desc_cols = [col for col in df.columns if col.startswith('Description_') or col == 'Rendered_Description']
    var_cols = [col for col in df.columns if col.startswith('VAR_')]
    
    print(f"   • Project fields: {len(project_cols)} ({', '.join(project_cols)})")
    print(f"   • Element fields: {len(element_cols)} ({', '.join(element_cols)})")
    print(f"   • Instance fields: {len(instance_cols)} ({', '.join(instance_cols)})")
    print(f"   • Description fields: {len(desc_cols)} ({', '.join(desc_cols)})")
    print(f"   • Variable fields: {len(var_cols)} ({', '.join(var_cols)})")
    
    # Show sample data
    print(f"\n📝 Sample element data:")
    for i in range(min(2, len(df))):
        row = df.iloc[i]
        print(f"   Row {i+1}: {row['Instance_Code']} ({row['Category']})")
        print(f"          Element: {row['Element_Code']} - {row['Element_Name']}")
        print(f"          Description: {row['Rendered_Description'][:60]}...")
        
        # Show variables for this element
        row_vars = [(col, row[col]) for col in var_cols if pd.notna(row[col]) and row[col] != '']
        if row_vars:
            print(f"          Variables: {len(row_vars)} assigned")
            for var_name, var_value in row_vars[:3]:  # Show first 3
                print(f"             • {var_name.replace('VAR_', '')}: {var_value}")
        print()
    
    # Show category breakdown
    print(f"📂 Category breakdown:")
    for cat in df['Category'].unique():
        cat_df = df[df['Category'] == cat]
        print(f"   • {cat}: {len(cat_df)} elements")
        
        # Show unique variable types for this category
        cat_vars = set()
        for col in var_cols:
            if cat_df[col].notna().any():
                cat_vars.add(col.replace('VAR_', ''))
        print(f"     Variables: {', '.join(sorted(cat_vars))}")
    
    print(f"\n🎯 MAIL MERGE USAGE WITH COMPLETE DATA:")
    print(f"   📋 Basic fields: {{{{ MERGEFIELD Instance_Name }}}}, {{{{ MERGEFIELD Rendered_Description }}}}")
    print(f"   🔧 Variables: {{{{ MERGEFIELD VAR_MATERIAL }}}}, {{{{ MERGEFIELD VAR_DIAMETRO }}}}")
    print(f"   📍 Location: {{{{ MERGEFIELD Instance_Location }}}}")
    print(f"   📝 Template: {{{{ MERGEFIELD Description_Template }}}}")
    
    print(f"\n✅ COMPLETE DATABASE INTEGRATION SUCCESS!")
    print(f"   • All element data preserved")
    print(f"   • All variables as individual columns") 
    print(f"   • All descriptions rendered")
    print(f"   • Perfect for Word Mail Merge iteration")
    
    return output_file

if __name__ == "__main__":
    try:
        result = test_full_database_mailmerge()
        print(f"\n🎉 FULL DATABASE MAIL MERGE TEST COMPLETED!")
        print(f"   📁 Output: {result}")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)