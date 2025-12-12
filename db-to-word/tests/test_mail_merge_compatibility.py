#!/usr/bin/env python3
"""
Mail Merge Compatibility Tests

Tests that the Excel export is properly formatted for Microsoft Word Mail Merge.
Validates the complete flow: Database → Excel → (ready for) Word Mail Merge
"""

import os
import sys
import tempfile
import sqlite3
import pytest
import pandas as pd
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from final_with_categories import generate_final_excel


@pytest.fixture
def populated_test_db():
    """Create a database with multiple elements across categories."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    schema_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "src", "schema.sql"
    )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    schema_sql = re.sub(r'COMMENT ON TABLE.*?;', '', schema_sql, flags=re.IGNORECASE | re.DOTALL)
    conn.executescript(schema_sql)

    # Project
    conn.execute("""
        INSERT INTO projects (project_code, project_name, status)
        VALUES ('OFFICE-2024', 'Madrid Office Project', 'ACTIVE')
    """)
    project_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Multiple elements with different categories
    elements_data = [
        ('EHV010', 'Viga de hormigón armado', 'ESTRUCTURA METALICA',
         'Viga de hormigón armado, realizada con hormigón {Resistencia}, acero {Tipo acero}.'),
        ('CSL010', 'Losa de cimentación', 'CIMENTACION',
         'Losa de cimentación de hormigón armado, de {Espesor} cm de espesor.'),
        ('EAS010', 'Pilar de acero', 'ESTRUCTURA METALICA',
         'Pilar de acero laminado {Perfil}, con {Tipo pintura}.'),
    ]

    for elem_code, elem_name, category, template in elements_data:
        conn.execute("""
            INSERT INTO elements (element_code, element_name, category)
            VALUES (?, ?, ?)
        """, (elem_code, elem_name, category))
        element_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Variables based on element type
        if elem_code == 'EHV010':
            vars_data = [
                ('Resistencia', 'NUMERIC', 'N/mm²', '25'),
                ('Tipo acero', 'TEXT', None, 'B 500 S'),
            ]
        elif elem_code == 'CSL010':
            vars_data = [
                ('Espesor', 'NUMERIC', 'cm', '40'),
            ]
        else:  # EAS010
            vars_data = [
                ('Perfil', 'TEXT', None, 'HEB 200'),
                ('Tipo pintura', 'TEXT', None, 'Intumescente'),
            ]

        var_ids = []
        for i, (var_name, var_type, unit, default) in enumerate(vars_data):
            conn.execute("""
                INSERT INTO element_variables (element_id, variable_name, variable_type, unit, default_value, display_order)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (element_id, var_name, var_type, unit, default, i+1))
            var_ids.append(conn.execute("SELECT last_insert_rowid()").fetchone()[0])

        # Description version
        conn.execute("""
            INSERT INTO description_versions (element_id, description_template, state, is_active, version_number)
            VALUES (?, ?, 'S3', 1, 1)
        """, (element_id, template))
        version_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Project element instances (2 per element type)
        for j in range(1, 3):
            instance_code = f'{elem_code}-{j:03d}'
            location = f'Planta {j}'

            conn.execute("""
                INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name, location)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (project_id, element_id, version_id, instance_code, f'{elem_name} {j}', location))
            pe_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            # Variable values
            for var_id in var_ids:
                var_info = conn.execute("SELECT default_value FROM element_variables WHERE variable_id = ?", (var_id,)).fetchone()
                conn.execute("""
                    INSERT INTO project_element_values (project_element_id, variable_id, value)
                    VALUES (?, ?, ?)
                """, (pe_id, var_id, var_info[0]))

            # Rendered description
            rendered = template
            for var_id in var_ids:
                var_info = conn.execute(
                    "SELECT variable_name, default_value FROM element_variables WHERE variable_id = ?",
                    (var_id,)
                ).fetchone()
                rendered = rendered.replace(f'{{{var_info[0]}}}', var_info[1] or '')

            conn.execute("""
                INSERT INTO rendered_descriptions (project_element_id, rendered_text)
                VALUES (?, ?)
            """, (pe_id, rendered))

    conn.commit()
    conn.close()

    yield db_path

    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestMailMergeCompatibility:
    """Tests for Word Mail Merge compatibility."""

    def test_excel_has_all_required_sheets(self, populated_test_db, temp_output_dir):
        """Verify Excel has ALL_ELEMENTS and PROJECT_OVERVIEW sheets."""
        output_file = generate_final_excel(
            db_path=populated_test_db,
            project_code='OFFICE-2024',
            output_dir=temp_output_dir
        )

        excel = pd.ExcelFile(output_file)
        sheets = excel.sheet_names

        assert 'ALL_ELEMENTS' in sheets, "ALL_ELEMENTS sheet required for comprehensive docs"
        assert 'PROJECT_OVERVIEW' in sheets, "PROJECT_OVERVIEW sheet required for summary"

    def test_excel_has_category_sheets(self, populated_test_db, temp_output_dir):
        """Verify category-specific sheets are created."""
        output_file = generate_final_excel(
            db_path=populated_test_db,
            project_code='OFFICE-2024',
            output_dir=temp_output_dir
        )

        excel = pd.ExcelFile(output_file)
        sheets = excel.sheet_names

        # Should have sheets for each category
        assert any('METALICA' in s or 'ESTRUCTURA' in s for s in sheets), "Should have structure category sheet"
        assert any('CIMENTACION' in s for s in sheets), "Should have foundation category sheet"

    def test_column_names_are_mail_merge_friendly(self, populated_test_db, temp_output_dir):
        """Verify column names work as Word merge fields."""
        output_file = generate_final_excel(
            db_path=populated_test_db,
            project_code='OFFICE-2024',
            output_dir=temp_output_dir
        )

        df = pd.read_excel(output_file, sheet_name='ALL_ELEMENTS')

        for col in df.columns:
            # Word merge fields can't have certain characters
            assert '\n' not in col, f"Column '{col}' has newline"
            assert len(col) <= 40, f"Column '{col}' too long for merge field"
            # Should be alphanumeric with underscores
            assert re.match(r'^[A-Za-z0-9_áéíóúñÁÉÍÓÚÑ]+$', col), f"Column '{col}' has invalid characters"

    def test_rendered_descriptions_are_complete(self, populated_test_db, temp_output_dir):
        """Verify no unresolved placeholders in descriptions."""
        output_file = generate_final_excel(
            db_path=populated_test_db,
            project_code='OFFICE-2024',
            output_dir=temp_output_dir
        )

        df = pd.read_excel(output_file, sheet_name='ALL_ELEMENTS')

        for idx, row in df.iterrows():
            desc = str(row['Rendered_Description'])
            # No unresolved {placeholder} syntax
            placeholders = re.findall(r'\{[^}]+\}', desc)
            assert len(placeholders) == 0, f"Row {idx} has unresolved placeholders: {placeholders}"

    def test_all_elements_have_required_fields(self, populated_test_db, temp_output_dir):
        """Verify all elements have the basic required fields."""
        output_file = generate_final_excel(
            db_path=populated_test_db,
            project_code='OFFICE-2024',
            output_dir=temp_output_dir
        )

        df = pd.read_excel(output_file, sheet_name='ALL_ELEMENTS')

        required_fields = [
            'Project_Name', 'Project_Code', 'Element_Code', 'Element_Name',
            'Category', 'Instance_Code', 'Instance_Name', 'Location',
            'Rendered_Description'
        ]

        for field in required_fields:
            assert field in df.columns, f"Missing required field: {field}"

        # All rows should have values for core fields
        for field in ['Element_Code', 'Instance_Code', 'Rendered_Description']:
            assert df[field].notna().all(), f"Field '{field}' has null values"

    def test_variable_columns_are_uppercase(self, populated_test_db, temp_output_dir):
        """Verify variable columns follow naming convention."""
        output_file = generate_final_excel(
            db_path=populated_test_db,
            project_code='OFFICE-2024',
            output_dir=temp_output_dir
        )

        df = pd.read_excel(output_file, sheet_name='ALL_ELEMENTS')

        # Variable columns (not base fields) should be uppercase
        base_fields = {'Project_Name', 'Project_Code', 'Element_Code', 'Element_Name',
                       'Category', 'Instance_Code', 'Instance_Name', 'Location',
                       'Rendered_Description'}

        variable_cols = [c for c in df.columns if c not in base_fields]

        for col in variable_cols:
            assert col == col.upper(), f"Variable column '{col}' should be uppercase"

    def test_multiple_elements_per_category(self, populated_test_db, temp_output_dir):
        """Verify multiple instances per category are exported."""
        output_file = generate_final_excel(
            db_path=populated_test_db,
            project_code='OFFICE-2024',
            output_dir=temp_output_dir
        )

        df = pd.read_excel(output_file, sheet_name='ALL_ELEMENTS')

        # Should have 6 elements total (2 per element type × 3 types)
        assert len(df) == 6, f"Expected 6 elements, got {len(df)}"

        # Each element code should appear twice
        for code in ['EHV010', 'CSL010', 'EAS010']:
            count = df['Element_Code'].value_counts().get(code, 0)
            assert count == 2, f"Element {code} should have 2 instances, got {count}"

    def test_project_overview_has_summary(self, populated_test_db, temp_output_dir):
        """Verify PROJECT_OVERVIEW sheet has summary info."""
        output_file = generate_final_excel(
            db_path=populated_test_db,
            project_code='OFFICE-2024',
            output_dir=temp_output_dir
        )

        df = pd.read_excel(output_file, sheet_name='PROJECT_OVERVIEW')

        assert 'Project_Name' in df.columns
        assert 'Total_Elements' in df.columns
        assert 'Export_Date' in df.columns

        assert df.iloc[0]['Total_Elements'] == 6


class TestDataIntegrity:
    """Tests for data integrity in the export."""

    def test_instance_codes_are_unique(self, populated_test_db, temp_output_dir):
        """Verify instance codes are unique."""
        output_file = generate_final_excel(
            db_path=populated_test_db,
            project_code='OFFICE-2024',
            output_dir=temp_output_dir
        )

        df = pd.read_excel(output_file, sheet_name='ALL_ELEMENTS')

        assert df['Instance_Code'].is_unique, "Instance codes must be unique"

    def test_descriptions_contain_expected_content(self, populated_test_db, temp_output_dir):
        """Verify descriptions contain expected technical content."""
        output_file = generate_final_excel(
            db_path=populated_test_db,
            project_code='OFFICE-2024',
            output_dir=temp_output_dir
        )

        df = pd.read_excel(output_file, sheet_name='ALL_ELEMENTS')

        # Check each element type has appropriate description
        ehv_rows = df[df['Element_Code'] == 'EHV010']
        for _, row in ehv_rows.iterrows():
            desc = row['Rendered_Description']
            assert 'hormigón' in desc.lower(), "Beam description should mention concrete"
            assert '25' in desc or 'B 500' in desc, "Should have variable values"

        csl_rows = df[df['Element_Code'] == 'CSL010']
        for _, row in csl_rows.iterrows():
            desc = row['Rendered_Description']
            assert 'cimentación' in desc.lower(), "Foundation description should mention foundation"
            assert '40' in desc, "Should have thickness value"


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
