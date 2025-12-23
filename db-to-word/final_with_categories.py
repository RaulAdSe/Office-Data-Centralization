#!/usr/bin/env python3
"""
Database to Excel export for Word Mail Merge integration.
Exports project elements with fully rendered descriptions and variables.
Renders descriptions on-the-fly from templates.
"""

import sqlite3
import pandas as pd
import os
import re
from pathlib import Path

# Default paths - can be overridden via parameters
DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "office_data.db"
DEFAULT_PROJECT_CODE = "MADRID-OFFICE-2024"

# Category mapping based on CYPE element code prefixes
CATEGORY_MAP = {
    'CS': 'FOUNDATIONS',           # CSL, CSZ, CSV - foundation elements
    'EH': 'CONCRETE_STRUCTURE',    # EHV, EHL, EHM, EHE - concrete elements
    'EA': 'STEEL_STRUCTURE',       # EAS, EAV - steel elements
    'RM': 'FINISHES',              # RMB - finishes and coatings
    'EE': 'STAIRS',                # EEH, EEM - stairs
    'FF': 'FACADES',               # Facade elements
    'CU': 'ROOFING',               # Roofing elements
}


def get_category_from_code(element_code: str) -> str:
    """Derive category from element code prefix."""
    if not element_code:
        return 'OTHER'
    # Get first 2 characters as prefix
    prefix = element_code[:2].upper()
    return CATEGORY_MAP.get(prefix, 'OTHER')


def render_description(template: str, variables: dict) -> str:
    """
    Render a description template by substituting placeholders.

    Args:
        template: Description template with {placeholder} syntax
        variables: Dict mapping placeholder names (with or without braces) to values

    Returns:
        Rendered description with all placeholders replaced
    """
    if not template:
        return ''

    rendered = template
    for placeholder, value in variables.items():
        if value:
            # If placeholder already has braces, use it directly
            if placeholder.startswith('{') and placeholder.endswith('}'):
                # Case-insensitive replace for {placeholder}
                pattern = re.compile(re.escape(placeholder), re.IGNORECASE)
                rendered = pattern.sub(str(value), rendered)
            else:
                # Add braces and replace
                pattern = re.compile(rf'\{{{re.escape(placeholder)}\}}', re.IGNORECASE)
                rendered = pattern.sub(str(value), rendered)
    return rendered


def generate_final_excel(db_path: str = None, project_code: str = None, output_dir: str = None):
    """
    Generate Excel with real database data for Mail Merge.
    Renders descriptions on-the-fly from templates.

    Args:
        db_path: Path to SQLite database. Defaults to data/office_data.db
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
    conn.row_factory = sqlite3.Row

    # Query to get project elements with their templates and variables
    query = """
    SELECT
        p.project_name,
        p.project_code,
        e.element_code,
        e.element_name,
        e.category as db_category,
        pe.project_element_id,
        pe.instance_code,
        pe.instance_name,
        pe.location,
        dv.description_template,
        ev.variable_name,
        tvm.placeholder,
        COALESCE(pev.value, ev.default_value, '') as variable_value
    FROM project_elements pe
    JOIN projects p ON pe.project_id = p.project_id
    JOIN elements e ON pe.element_id = e.element_id
    LEFT JOIN description_versions dv ON pe.description_version_id = dv.version_id
    LEFT JOIN element_variables ev ON e.element_id = ev.element_id
    LEFT JOIN template_variable_mappings tvm ON dv.version_id = tvm.version_id
                                             AND ev.variable_id = tvm.variable_id
    LEFT JOIN project_element_values pev ON pe.project_element_id = pev.project_element_id
                                        AND ev.variable_id = pev.variable_id
    WHERE p.project_code = ?
    ORDER BY e.element_code, pe.instance_code, ev.display_order
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
        """Convert data to Mail Merge format with on-the-fly rendering"""
        element_instances = filtered_df['instance_code'].dropna().unique()
        rows = []

        for instance_code in element_instances:
            element_data = filtered_df[filtered_df['instance_code'] == instance_code]
            if element_data.empty:
                continue

            base_info = element_data.iloc[0]

            # Build variables dict for rendering
            variables = {}
            for _, var_row in element_data.iterrows():
                placeholder = var_row['placeholder'] or var_row['variable_name']
                if placeholder and var_row['variable_value']:
                    variables[placeholder] = var_row['variable_value']

            # Render description on-the-fly
            template = base_info['description_template'] or ''
            rendered_desc = render_description(template, variables)

            # Get category from DB or derive from element code
            category = base_info['db_category']
            if not category or pd.isna(category):
                category = get_category_from_code(base_info['element_code'])

            row = {
                'Project_Name': base_info['project_name'],
                'Project_Code': base_info['project_code'],
                'Element_Code': base_info['element_code'],
                'Element_Name': base_info['element_name'],
                'Category': category,
                'Instance_Code': base_info['instance_code'],
                'Instance_Name': base_info['instance_name'] or '',
                'Location': base_info['location'] or '',
                'Rendered_Description': rendered_desc
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

    # Get categories (now derived from element codes if not in DB)
    categories = sorted([c for c in df_all['Category'].unique() if c and c != 'OTHER'])
    if 'OTHER' in df_all['Category'].values:
        categories.append('OTHER')
    print(f"📂 Categories: {', '.join(categories) if categories else 'None'}")

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
            df_category = df_all[df_all['Category'] == category]

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

    # Verify quality - check for unresolved placeholders
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
