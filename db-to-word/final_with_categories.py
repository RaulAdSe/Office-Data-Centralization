#!/usr/bin/env python3
"""
Database to Excel export for Word Mail Merge integration.
Exports project elements with fully rendered descriptions and variables.
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path

# Default paths - can be overridden via parameters
DEFAULT_DB_PATH = Path(__file__).parent.parent / "src" / "office_data.db"
DEFAULT_PROJECT_CODE = "MADRID-OFFICE-2024"

def generate_final_excel(db_path: str = None, project_code: str = None, output_dir: str = None):
    """
    Generate Excel with real database data for Mail Merge.

    Args:
        db_path: Path to SQLite database. Defaults to src/office_data.db
        project_code: Project code to export. Defaults to MADRID-OFFICE-2024
        output_dir: Output directory for Excel file. Defaults to excel_exports/

    Returns:
        Path to generated Excel file, or None if no data found
    """
    db_path = db_path or str(DEFAULT_DB_PATH)
    project_code = project_code or DEFAULT_PROJECT_CODE
    output_dir = output_dir or os.path.join(os.path.dirname(__file__), "excel_exports")

    print(f"🎯 Exporting project: {project_code}")

    conn = sqlite3.connect(db_path)
    
    # Main query to get all project data
    query = """
    SELECT 
        p.project_name,
        p.project_code,
        e.element_code,
        e.element_name,
        e.category,
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
    WHERE p.project_code = ?
    ORDER BY e.category, pe.instance_code, ev.display_order
    """
    
    df = pd.read_sql_query(query, conn, params=(project_code,))
    conn.close()

    if df.empty:
        print(f"❌ No data found for project {project_code}")
        return None
        
    print(f"📊 Found {len(df)} data rows")
    
    # Get all unique variables
    all_variables = sorted(df['variable_name'].dropna().unique())
    print(f"📊 Variables: {len(all_variables)}")
    
    # Get unique elements  
    elements = df['instance_code'].dropna().unique()
    print(f"📊 Elements: {len(elements)}")
    
    def create_element_rows(filtered_df):
        """Convert data to Mail Merge format"""
        element_instances = filtered_df['instance_code'].dropna().unique()
        rows = []
        
        for instance_code in element_instances:
            element_data = filtered_df[filtered_df['instance_code'] == instance_code]
            if element_data.empty:
                continue
                
            base_info = element_data.iloc[0]
            row = {
                'Project_Name': base_info['project_name'],
                'Project_Code': base_info['project_code'],
                'Element_Code': base_info['element_code'],
                'Element_Name': base_info['element_name'],
                'Category': base_info['category'],
                'Instance_Code': base_info['instance_code'],
                'Instance_Name': base_info['instance_name'] or '',
                'Location': base_info['location'] or '',
                'Rendered_Description': base_info['description'] or ''
            }
            
            # Add variables as columns
            for var_name in all_variables:
                clean_name = str(var_name).upper().replace(' ', '_')
                var_data = element_data[element_data['variable_name'] == var_name]
                if not var_data.empty and pd.notna(var_data.iloc[0]['variable_value']):
                    row[clean_name] = var_data.iloc[0]['variable_value']
                else:
                    row[clean_name] = ''
            
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    # Create main data
    df_all = create_element_rows(df)
    print(f"📊 Created {len(df_all)} rows with {len(df_all.columns)} columns")
    
    # Get categories from database
    categories = sorted(df['category'].unique())
    print(f"📂 Categories: {', '.join(categories)}")
    
    # Create output directory and clean it
    os.makedirs(output_dir, exist_ok=True)
    for file in os.listdir(output_dir):
        if file.endswith('.xlsx'):
            os.remove(os.path.join(output_dir, file))

    output_file = f"{output_dir}/{project_code}_FINAL_WITH_CATEGORIES.xlsx"
    
    # Create Excel
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # ALL_ELEMENTS sheet
        df_all.to_excel(writer, sheet_name="ALL_ELEMENTS", index=False)
        print(f"   ✅ ALL_ELEMENTS: {len(df_all)} elements")
        
        # Category sheets
        for category in categories:
            category_data = df[df['category'] == category]
            df_category = create_element_rows(category_data)
            
            if not df_category.empty:
                sheet_name = category.replace(' ', '_')[:31]  # Excel limit
                df_category.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"   ✅ {sheet_name}: {len(df_category)} elements")
        
        # Project overview
        if not df_all.empty:
            overview = {
                'Project_Name': [df_all.iloc[0]['Project_Name']],
                'Project_Code': [df_all.iloc[0]['Project_Code']],
                'Total_Elements': [len(df_all)],
                'Total_Categories': [len(categories)],
                'Export_Date': [pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')]
            }
            pd.DataFrame(overview).to_excel(writer, sheet_name="PROJECT_OVERVIEW", index=False)
            print(f"   ✅ PROJECT_OVERVIEW: Summary")
    
    # Verify quality
    complete_descriptions = sum(1 for _, row in df_all.iterrows() 
                               if pd.notna(row['Rendered_Description']) and 
                                  row['Rendered_Description'].strip() and
                                  '{' not in str(row['Rendered_Description']))
    
    print(f"\n✅ Export complete: {output_file}")
    print(f"📊 {len(df_all)} elements, {len(all_variables)} variables")
    print(f"📊 {complete_descriptions}/{len(df_all)} complete descriptions")
    print(f"📊 Categories: {', '.join(categories)}")
    
    return output_file

if __name__ == "__main__":
    generate_final_excel()