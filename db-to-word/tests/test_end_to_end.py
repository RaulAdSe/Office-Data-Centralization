#!/usr/bin/env python3
"""
End-to-end test: Validate Excel export from database

Tests the db-to-word module with a properly initialized test database.
"""

import os
import sys
import tempfile
import sqlite3
import pytest
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from final_with_categories import generate_final_excel


@pytest.fixture
def test_db():
    """Create a temporary database with test data."""
    # Create temp file
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # Read schema from project
    schema_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "src", "schema.sql"
    )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Create schema
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    # Remove COMMENT statements (SQLite doesn't support them)
    import re
    schema_sql = re.sub(r'COMMENT ON TABLE.*?;', '', schema_sql, flags=re.IGNORECASE | re.DOTALL)
    conn.executescript(schema_sql)

    # Insert test data
    # 1. Project
    conn.execute("""
        INSERT INTO projects (project_code, project_name, status)
        VALUES ('TEST-PROJECT-001', 'Test Project', 'ACTIVE')
    """)
    project_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # 2. Element
    conn.execute("""
        INSERT INTO elements (element_code, element_name, category)
        VALUES ('EHV010', 'Viga de hormigón armado', 'ESTRUCTURA METALICA')
    """)
    element_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # 3. Variables
    conn.execute("""
        INSERT INTO element_variables (element_id, variable_name, variable_type, unit, default_value, display_order)
        VALUES (?, 'Resistencia', 'NUMERIC', 'N/mm²', '25', 1)
    """, (element_id,))
    var1_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    conn.execute("""
        INSERT INTO element_variables (element_id, variable_name, variable_type, default_value, display_order)
        VALUES (?, 'Tipo de hormigón', 'TEXT', 'HA-25', 2)
    """, (element_id,))
    var2_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # 4. Description version
    conn.execute("""
        INSERT INTO description_versions (element_id, description_template, state, is_active, version_number)
        VALUES (?, 'Viga de hormigón armado con resistencia {Resistencia} y tipo {Tipo de hormigón}.', 'S3', 1, 1)
    """, (element_id,))
    version_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # 5. Project element instance
    conn.execute("""
        INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name, location)
        VALUES (?, ?, ?, 'EHV010-001', 'Viga Principal', 'Planta Baja')
    """, (project_id, element_id, version_id))
    pe_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # 6. Project element values
    conn.execute("""
        INSERT INTO project_element_values (project_element_id, variable_id, value)
        VALUES (?, ?, '30')
    """, (pe_id, var1_id))
    conn.execute("""
        INSERT INTO project_element_values (project_element_id, variable_id, value)
        VALUES (?, ?, 'HA-30')
    """, (pe_id, var2_id))

    # 7. Rendered description
    conn.execute("""
        INSERT INTO rendered_descriptions (project_element_id, rendered_text)
        VALUES (?, 'Viga de hormigón armado con resistencia 30 N/mm² y tipo HA-30.')
    """, (pe_id,))

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    import tempfile
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_export_with_test_data(test_db, temp_output_dir):
    """Test Excel export with test database data."""
    print("🧪 Testing Excel export with test database...")

    # Generate Excel from test database
    output_file = generate_final_excel(
        db_path=test_db,
        project_code='TEST-PROJECT-001',
        output_dir=temp_output_dir
    )

    assert output_file is not None, "Export should return file path"
    assert os.path.exists(output_file), f"Export file should exist: {output_file}"

    print(f"✅ Export successful: {output_file}")

    # Validate Excel structure
    excel_file = pd.ExcelFile(output_file)
    sheets = excel_file.sheet_names

    print(f"📊 Sheets found: {', '.join(sheets)}")

    # Check required sheets
    required_sheets = ['ALL_ELEMENTS', 'PROJECT_OVERVIEW']
    for sheet in required_sheets:
        assert sheet in sheets, f"Missing required sheet: {sheet}"

    # Check ALL_ELEMENTS content
    df = pd.read_excel(output_file, sheet_name='ALL_ELEMENTS')
    print(f"📊 ALL_ELEMENTS: {len(df)} rows, {len(df.columns)} columns")

    # Check for required columns
    required_cols = ['Project_Name', 'Element_Code', 'Instance_Code', 'Rendered_Description']
    for col in required_cols:
        assert col in df.columns, f"Missing column: {col}"

    # Verify test data
    assert len(df) == 1, "Should have 1 element"
    assert df.iloc[0]['Element_Code'] == 'EHV010'
    assert df.iloc[0]['Instance_Code'] == 'EHV010-001'
    assert 'Viga de hormigón armado' in df.iloc[0]['Rendered_Description']

    # Check descriptions
    complete_descriptions = df['Rendered_Description'].notna().sum()
    print(f"📊 Complete descriptions: {complete_descriptions}/{len(df)}")

    print("✅ All tests passed!")


def test_export_empty_project(test_db, temp_output_dir):
    """Test export with non-existent project returns None."""
    result = generate_final_excel(
        db_path=test_db,
        project_code='NONEXISTENT-PROJECT',
        output_dir=temp_output_dir
    )
    assert result is None, "Should return None for non-existent project"


def test_export_variable_columns(test_db, temp_output_dir):
    """Test that variable columns are included in export."""
    output_file = generate_final_excel(
        db_path=test_db,
        project_code='TEST-PROJECT-001',
        output_dir=temp_output_dir
    )

    df = pd.read_excel(output_file, sheet_name='ALL_ELEMENTS')

    # Variables should be uppercase column names
    assert 'RESISTENCIA' in df.columns, "RESISTENCIA variable column should exist"
    assert 'TIPO_DE_HORMIGÓN' in df.columns, "TIPO_DE_HORMIGÓN variable column should exist"

    # Check values (may be numeric or string depending on pandas inference)
    assert str(df.iloc[0]['RESISTENCIA']) == '30'
    assert str(df.iloc[0]['TIPO_DE_HORMIGÓN']) == 'HA-30'


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
