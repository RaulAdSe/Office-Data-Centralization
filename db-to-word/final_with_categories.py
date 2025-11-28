#!/usr/bin/env python3
"""
FINAL EXPORT: Optimal structure with category sheets
- ALL_ELEMENTS sheet (all elements together)
- Category sheets (elements grouped by construction type)
- All with fully rendered descriptions and named variable columns
"""

import sqlite3
import pandas as pd
import os
import re

DB_NAME = "/Users/rauladell/Work/Office-Data-Centralization/src/office_data.db"

def generate_final_excel_with_categories():
    """Generate final Excel with both ALL_ELEMENTS and category sheets"""
    print("🎯 FINAL EXCEL WITH CATEGORIES")
    print("=" * 50)
    
    conn = sqlite3.connect(DB_NAME)
    
    # Get all data
    query = """
    SELECT 
        p.project_name,
        p.project_code,
        e.element_code,
        e.element_name,
        pe.instance_code,
        pe.instance_name,
        pe.location,
        rd.rendered_text as description,
        ev.variable_name,
        COALESCE(pev.value, ev.default_value, '') as variable_value
        
    FROM project_elements pe
    JOIN projects p ON pe.project_id = p.project_id
    JOIN elements e ON pe.element_id = e.element_id
    LEFT JOIN rendered_descriptions rd ON pe.project_element_id = rd.project_element_id
    LEFT JOIN element_variables ev ON e.element_id = ev.element_id
    LEFT JOIN project_element_values pev ON pe.project_element_id = pev.project_element_id 
                                        AND ev.variable_id = pev.variable_id
    WHERE p.project_code = 'MADRID-OFFICE-2024'
    ORDER BY pe.instance_code, ev.display_order
    """
    
    df = pd.read_sql_query(query, conn, params=())
    conn.close()
    
    print(f"📊 Raw data: {len(df)} rows")
    
    # Get all unique variables (sorted for consistency)
    all_variables = sorted(df['variable_name'].dropna().unique())
    print(f"📊 Unique variables: {len(all_variables)}")
    
    # Get unique elements
    elements = df['instance_code'].dropna().unique()
    print(f"📊 Elements: {len(elements)}")
    
    def create_element_rows(filtered_df):
        """Create rows for a subset of elements with optimal structure"""
        element_instances = filtered_df['instance_code'].dropna().unique()
        rows = []
        
        for instance_code in element_instances:
            element_data = filtered_df[filtered_df['instance_code'] == instance_code]
            
            if element_data.empty:
                continue
                
            # Base element info
            base_info = element_data.iloc[0]
            row = {
                'Project_Name': base_info['project_name'],
                'Project_Code': base_info['project_code'],
                'Element_Code': base_info['element_code'],
                'Element_Name': base_info['element_name'],
                'Instance_Code': base_info['instance_code'],
                'Instance_Name': base_info['instance_name'],
                'Location': base_info['location'],
            }
            
            # Add all possible variables as columns
            for var_name in all_variables:
                clean_var_name = str(var_name).upper().replace(' ', '_')
                
                # Find value for this variable for this element
                var_data = element_data[element_data['variable_name'] == var_name]
                if not var_data.empty and pd.notna(var_data.iloc[0]['variable_value']):
                    row[clean_var_name] = var_data.iloc[0]['variable_value']
                else:
                    row[clean_var_name] = ''  # Empty if element doesn't have this variable
            
            # Add description at the end
            row['Rendered_Description'] = base_info['description'] if pd.notna(base_info['description']) else ''
            
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    # Create ALL_ELEMENTS sheet (same as optimal)
    print(f"\n📄 Creating ALL_ELEMENTS sheet...")
    df_all = create_element_rows(df)
    print(f"   ✅ {len(df_all)} rows, {len(df_all.columns)} columns")
    
    # Determine categories based on element codes
    def get_category(element_code):
        """Determine category from element code prefix"""
        if element_code.startswith('CS'):
            return 'FOUNDATIONS'
        elif element_code.startswith('EH'):
            return 'CONCRETE_STRUCTURE'
        elif element_code.startswith('EA'):
            return 'STEEL_STRUCTURE'
        elif element_code.startswith('RM') or element_code.startswith('RMB'):
            return 'FINISHES'
        elif element_code.startswith('EM'):
            return 'WOOD_STRUCTURE'
        elif element_code.startswith('IE'):
            return 'INSTALLATIONS'
        else:
            return 'OTHER'
    
    # Group elements by category
    df['category'] = df['element_code'].apply(get_category)
    categories = df['category'].unique()
    
    print(f"\n📂 Found categories: {list(categories)}")
    
    # Create Excel with multiple sheets
    output_file = "excel_exports/MADRID-OFFICE-2024_FINAL_WITH_CATEGORIES.xlsx"
    os.makedirs("excel_exports", exist_ok=True)
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        
        # ALL_ELEMENTS sheet
        df_all.to_excel(writer, sheet_name="ALL_ELEMENTS", index=False)
        print(f"   📄 ALL_ELEMENTS: {len(df_all)} rows")
        
        # Category sheets
        for category in sorted(categories):
            category_data = df[df['category'] == category]
            
            if category_data.empty:
                continue
            
            df_category = create_element_rows(category_data)
            
            if not df_category.empty:
                # Clean sheet name
                sheet_name = category[:31]  # Excel limit
                df_category.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"   📄 {sheet_name}: {len(df_category)} rows")
                
                # Show elements in this category
                elements_in_category = df_category['Instance_Code'].tolist()
                print(f"      Elements: {', '.join(elements_in_category)}")
        
        # PROJECT_OVERVIEW sheet
        if not df_all.empty:
            project_info = {
                'Project_Name': [df_all.iloc[0]['Project_Name']],
                'Project_Code': [df_all.iloc[0]['Project_Code']],
                'Total_Elements': [len(df_all)],
                'Total_Categories': [len(categories)],
                'Total_Variables': [len(all_variables)],
                'Categories_Present': [', '.join(sorted(categories))]
            }
            pd.DataFrame(project_info).to_excel(writer, sheet_name="PROJECT_OVERVIEW", index=False)
            print(f"   📄 PROJECT_OVERVIEW: Project summary")
    
    print(f"\n✅ Generated: {output_file}")
    
    # Show structure summary
    print(f"\n📊 FINAL STRUCTURE:")
    print(f"   📄 ALL_ELEMENTS: All {len(df_all)} elements in one sheet")
    print(f"   📂 Category sheets: {len(categories)} categories")
    print(f"   🔧 Variables: {len(all_variables)} named columns in each sheet")
    print(f"   📝 Descriptions: Fully rendered with variable values")
    
    # Verify descriptions
    complete_descriptions = sum(1 for _, row in df_all.iterrows() 
                               if pd.notna(row['Rendered_Description']) and 
                                  str(row['Rendered_Description']).strip() != '' and
                                  '{' not in str(row['Rendered_Description']))
    
    print(f"\n🎯 QUALITY VERIFICATION:")
    print(f"   ✅ Complete descriptions: {complete_descriptions}/{len(df_all)} ({(complete_descriptions/len(df_all)*100):.1f}%)")
    
    print(f"\n🎯 USAGE OPTIONS:")
    print(f"   📋 General report: Use ALL_ELEMENTS sheet")
    print(f"   🏗️  Foundation report: Use FOUNDATIONS sheet") 
    print(f"   🔩 Steel report: Use STEEL_STRUCTURE sheet")
    print(f"   🧱 Concrete report: Use CONCRETE_STRUCTURE sheet")
    print(f"   🎨 Finishes report: Use FINISHES sheet")
    
    return output_file

if __name__ == "__main__":
    generate_final_excel_with_categories()