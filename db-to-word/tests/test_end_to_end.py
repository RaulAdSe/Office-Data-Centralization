#!/usr/bin/env python3
"""
End-to-end test: Validate Excel export from real database
"""

import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from final_with_categories import generate_final_excel

def test_export():
    """Test Excel export from real database"""
    print("🧪 Testing Excel export...")
    
    # Generate Excel from real database
    output_file = generate_final_excel()
    
    if not output_file or not os.path.exists(output_file):
        print("❌ Export failed")
        return False
        
    print(f"✅ Export successful: {output_file}")
    
    # Validate Excel structure
    excel_file = pd.ExcelFile(output_file)
    sheets = excel_file.sheet_names
    
    print(f"📊 Sheets found: {', '.join(sheets)}")
    
    # Check required sheets
    required_sheets = ['ALL_ELEMENTS', 'PROJECT_OVERVIEW']
    for sheet in required_sheets:
        if sheet not in sheets:
            print(f"❌ Missing required sheet: {sheet}")
            return False
    
    # Check ALL_ELEMENTS content
    df = pd.read_excel(output_file, sheet_name='ALL_ELEMENTS')
    print(f"📊 ALL_ELEMENTS: {len(df)} rows, {len(df.columns)} columns")
    
    # Check for required columns
    required_cols = ['Project_Name', 'Element_Code', 'Instance_Code', 'Rendered_Description']
    for col in required_cols:
        if col not in df.columns:
            print(f"❌ Missing column: {col}")
            return False
    
    # Check descriptions
    complete_descriptions = df['Rendered_Description'].notna().sum()
    print(f"📊 Complete descriptions: {complete_descriptions}/{len(df)}")
    
    print("✅ All tests passed!")
    return True

if __name__ == "__main__":
    test_export()