#!/usr/bin/env python3
"""
Test: Multiple Rows for Mail Merge
Tests Excel export with multiple rows (one per element) for better Word Mail Merge iteration
"""

import os
import sys
import sqlite3
import pandas as pd
from pathlib import Path

# Add directories to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'src'))

from src.db_manager import DatabaseManager

def test_mailmerge_rows_structure():
    """
    Test Excel export with multiple rows for Mail Merge compatibility.
    Each row represents one element instance for easy iteration in Word.
    """
    
    print("🧪 TESTING MAIL MERGE MULTIPLE ROWS STRUCTURE")
    print("=" * 60)
    
    # Use existing test database
    test_db_path = "tests/test_e2e.db"
    
    if not os.path.exists(test_db_path):
        print("❌ Test database not found. Run test_end_to_end.py first.")
        return
    
    print("📊 Using existing test database...")
    
    def generate_mailmerge_excel(db_path, project_code):
        """Generate Excel with multiple rows structure for Mail Merge"""
        
        conn = sqlite3.connect(db_path)
        
        # Get project data with one row per element instance
        query = """
        SELECT 
            p.project_name,
            p.project_code,
            e.category,
            e.element_code,
            e.element_name AS element_type,
            pe.instance_code,
            pe.instance_name,
            pe.location,
            rd.rendered_text AS description
        FROM project_elements pe
        JOIN projects p ON pe.project_id = p.project_id
        JOIN elements e ON pe.element_id = e.element_id
        LEFT JOIN rendered_descriptions rd ON pe.project_element_id = rd.project_element_id
        WHERE p.project_code = ?
        ORDER BY e.category, pe.instance_code
        """
        df = pd.read_sql_query(query, conn, params=(project_code,))
        conn.close()
        
        if df.empty:
            raise ValueError("No data found for project")
        
        output_file = f"excel_exports/{project_code}_MAILMERGE_ROWS.xlsx"
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            
            # OPTION 1: All elements in one sheet with multiple rows
            print("   📝 Creating ALL_ELEMENTS sheet (multiple rows)...")
            df_all = df.copy()
            df_all.columns = [
                'Project_Name', 'Project_Code', 'Category', 'Element_Code', 
                'Element_Type', 'Instance_Code', 'Instance_Name', 'Location', 'Description'
            ]
            df_all.to_excel(writer, sheet_name="ALL_ELEMENTS", index=False)
            
            # OPTION 2: Category-specific sheets with multiple rows each
            categories = df['category'].unique()
            
            for categoria in sorted(categories):
                df_cat = df[df['category'] == categoria].copy()
                
                # Clean column names for Mail Merge
                df_cat.columns = [
                    'Project_Name', 'Project_Code', 'Category', 'Element_Code',
                    'Element_Type', 'Instance_Code', 'Instance_Name', 'Location', 'Description'
                ]
                
                # Add category-specific fields
                df_cat['Category_Count'] = len(df_cat)
                df_cat['Row_Number'] = range(1, len(df_cat) + 1)
                
                sheet_name = f"ROWS_{categoria.replace(' ', '_')}"[:31]
                print(f"   📄 Creating {sheet_name} sheet ({len(df_cat)} rows)...")
                df_cat.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return output_file, df
    
    # Generate Mail Merge Excel
    print("\n📈 Generating Mail Merge Excel with multiple rows...")
    output_file, df = generate_mailmerge_excel(test_db_path, 'TEST-2025')
    print(f"   ✅ Generated: {output_file}")
    
    # Analyze structure
    print("\n🔍 Analyzing Excel structure...")
    excel_file = pd.ExcelFile(output_file)
    print(f"   📊 Sheets: {excel_file.sheet_names}")
    
    # Test ALL_ELEMENTS sheet
    df_all = pd.read_excel(output_file, sheet_name='ALL_ELEMENTS')
    print(f"\n📋 ALL_ELEMENTS sheet:")
    print(f"   • Rows: {len(df_all)} (one per element instance)")
    print(f"   • Columns: {len(df_all.columns)} (standard fields)")
    print(f"   • Categories: {df_all['Category'].nunique()}")
    
    print(f"\n📝 Sample rows from ALL_ELEMENTS:")
    for i in range(min(3, len(df_all))):
        row = df_all.iloc[i]
        print(f"   Row {i+1}: {row['Instance_Code']} ({row['Category']}) - {row['Instance_Name']}")
    
    # Test category-specific sheets
    print(f"\n📂 Category-specific sheets:")
    for sheet in excel_file.sheet_names:
        if sheet.startswith('ROWS_'):
            df_sheet = pd.read_excel(output_file, sheet_name=sheet)
            category = sheet.replace('ROWS_', '').replace('_', ' ')
            print(f"   • {sheet}: {len(df_sheet)} rows for {category}")
            
            # Show sample data
            if len(df_sheet) > 0:
                print(f"     Sample: {df_sheet.iloc[0]['Instance_Code']} - {df_sheet.iloc[0]['Description'][:50]}...")
    
    # Compare with current horizontal structure
    print(f"\n⚖️  COMPARISON:")
    print(f"   🔄 CURRENT (Horizontal): 1 row × many columns per category")
    print(f"   ✅ NEW (Vertical): {len(df_all)} rows × {len(df_all.columns)} columns total")
    
    print(f"\n📋 MAIL MERGE BENEFITS:")
    print(f"   ✅ Easy iteration: {{{{ MERGEFIELD Instance_Name }}}}")
    print(f"   ✅ Word can loop through multiple elements automatically")
    print(f"   ✅ Standard column names across all rows")
    print(f"   ✅ Better for tables and lists in Word documents")
    
    print(f"\n🎯 WORD MAIL MERGE USAGE:")
    print(f"   1. Select sheet: ALL_ELEMENTS (all categories) or ROWS_[CATEGORY] (specific)")
    print(f"   2. Insert fields: {{{{ MERGEFIELD Instance_Name }}}}, {{{{ MERGEFIELD Description }}}}")
    print(f"   3. Word will create one entry per row automatically")
    
    return output_file

if __name__ == "__main__":
    try:
        result = test_mailmerge_rows_structure()
        print(f"\n🎉 MAIL MERGE ROWS TEST COMPLETED!")
        print(f"   📁 Output: {result}")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)