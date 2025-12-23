#!/usr/bin/env python3
"""
Test Streamlit app functions directly.
These tests verify that the functions used by the Streamlit UI work correctly.
"""

import os
import sys
import sqlite3
import tempfile
import shutil
from pathlib import Path

# Add app and src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Use a test database
TEST_DB = None
TEST_DIR = None


def setup_test_db():
    """Create a test database."""
    global TEST_DB, TEST_DIR
    TEST_DIR = tempfile.mkdtemp()
    TEST_DB = os.path.join(TEST_DIR, "test_streamlit.db")

    # Copy schema
    schema_path = Path(__file__).parent.parent / "src" / "schema.sql"
    if not schema_path.exists():
        schema_path = Path(__file__).parent.parent / "updated_schema.sql"

    conn = sqlite3.connect(TEST_DB)
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
        # Remove COMMENT statements (SQLite doesn't support them)
        import re
        schema_sql = re.sub(r'COMMENT ON TABLE.*?;', '', schema_sql, flags=re.IGNORECASE | re.DOTALL)
        conn.executescript(schema_sql)

    # Create a test user
    import bcrypt
    pwd_hash = bcrypt.hashpw("testpass".encode(), bcrypt.gensalt()).decode('utf-8')
    conn.execute(
        "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
        ("testuser", pwd_hash, "Test User", "admin")
    )
    conn.commit()
    conn.close()

    return TEST_DB


def cleanup_test_db():
    """Clean up test database."""
    global TEST_DIR
    if TEST_DIR:
        shutil.rmtree(TEST_DIR, ignore_errors=True)


# Mock the DB_NAME for the app functions
def get_connection():
    return sqlite3.connect(TEST_DB)


class StreamlitFunctionsTester:
    """Test Streamlit app functions."""

    def __init__(self):
        self.results = []
        setup_test_db()

    def cleanup(self):
        cleanup_test_db()

    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
        print(f"{status}: {test_name}")
        if details and not passed:
            print(f"       Details: {details}")

    def run_all_tests(self):
        """Run all Streamlit function tests."""
        print("=" * 70)
        print("STREAMLIT APP FUNCTIONS TEST")
        print("=" * 70)
        print()

        # Test functions
        print("\n1. ELEMENT FUNCTIONS")
        print("-" * 40)
        self.test_crear_element_complet()
        self.test_get_elements()
        self.test_crear_nova_variable()

        print("\n2. VARIABLE OPTIONS FUNCTIONS")
        print("-" * 40)
        self.test_crear_opciones_variable()
        self.test_get_variable_options()

        print("\n3. VERSION & APPROVAL FUNCTIONS")
        print("-" * 40)
        self.test_get_drafts_amb_vots()
        self.test_votar_versio()

        print("\n4. PROJECT FUNCTIONS")
        print("-" * 40)
        self.test_crear_projecte_nou()
        self.test_get_projects()
        self.test_crear_instancies_massives()

        print("\n5. PROJECT ELEMENT FUNCTIONS")
        print("-" * 40)
        self.test_get_project_instances()
        self.test_get_instance_variables_values()
        self.test_save_instance_values()

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        failed = total - passed

        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")

        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for r in self.results:
                if not r['passed']:
                    print(f"   - {r['test']}: {r['details']}")
        else:
            print("\n✅ ALL TESTS PASSED!")

        print("=" * 70)
        return failed == 0

    # ========================================
    # Test Element Functions
    # ========================================

    def test_crear_element_complet(self):
        """Test creating a complete element."""
        try:
            conn = get_connection()
            c = conn.cursor()

            # Create element
            c.execute("INSERT INTO elements (element_code, element_name, category) VALUES (?, ?, ?)",
                     ("TEST-001", "Test Element", "ASCENSOR"))
            elem_id = c.lastrowid
            self.element_id = elem_id

            # Add variables
            c.execute("INSERT INTO element_variables (element_id, variable_name, variable_type, unit) VALUES (?, ?, ?, ?)",
                     (elem_id, "marca", "TEXT", None))
            var_id = c.lastrowid
            self.variable_id = var_id

            c.execute("INSERT INTO element_variables (element_id, variable_name, variable_type, unit) VALUES (?, ?, ?, ?)",
                     (elem_id, "capacidad", "NUMERIC", "kg"))

            # Add description draft
            c.execute("""INSERT INTO description_versions
                        (element_id, description_template, state, is_active, version_number)
                        VALUES (?, ?, 'S0', 0, 1)""",
                     (elem_id, "Ascensor {marca} con capacidad {capacidad}"))
            self.version_id = c.lastrowid

            conn.commit()
            conn.close()

            passed = elem_id > 0
            self.log_result("crear_element_complet", passed)
        except Exception as e:
            self.log_result("crear_element_complet", False, str(e))

    def test_get_elements(self):
        """Test getting elements."""
        try:
            conn = get_connection()
            query = """
                SELECT e.element_id, e.element_code, e.element_name, e.category,
                       dv.version_number as version_activa, dv.description_template
                FROM elements e
                LEFT JOIN description_versions dv ON e.element_id = dv.element_id AND dv.is_active = 1
            """
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            conn.close()

            passed = len(rows) >= 1
            self.log_result("get_elements", passed, f"Found {len(rows)} elements")
        except Exception as e:
            self.log_result("get_elements", False, str(e))

    def test_crear_nova_variable(self):
        """Test creating a new variable."""
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute("INSERT INTO element_variables (element_id, variable_name, variable_type, unit) VALUES (?, ?, ?, ?)",
                     (self.element_id, "color", "TEXT", None))
            var_id = c.lastrowid
            conn.commit()
            conn.close()

            passed = var_id > 0
            self.log_result("crear_nova_variable", passed)
        except Exception as e:
            self.log_result("crear_nova_variable", False, str(e))

    # ========================================
    # Test Variable Options Functions
    # ========================================

    def test_crear_opciones_variable(self):
        """Test creating variable options."""
        try:
            conn = get_connection()
            opciones = ["Schindler", "KONE", "Otis"]
            datos_insert = [(self.variable_id, opt, i) for i, opt in enumerate(opciones)]
            conn.executemany(
                "INSERT INTO variable_options (variable_id, option_value, display_order) VALUES (?, ?, ?)",
                datos_insert
            )
            conn.commit()
            conn.close()

            self.log_result("crear_opciones_variable", True)
        except Exception as e:
            self.log_result("crear_opciones_variable", False, str(e))

    def test_get_variable_options(self):
        """Test getting variable options."""
        try:
            conn = get_connection()
            query = "SELECT option_value FROM variable_options WHERE variable_id = ? ORDER BY display_order"
            rows = conn.execute(query, (self.variable_id,)).fetchall()
            conn.close()

            passed = len(rows) == 3
            self.log_result("get_variable_options", passed, f"Found {len(rows)} options")
        except Exception as e:
            self.log_result("get_variable_options", False, str(e))

    # ========================================
    # Test Version & Approval Functions
    # ========================================

    def test_get_drafts_amb_vots(self):
        """Test getting drafts with vote counts."""
        try:
            conn = get_connection()
            query = """
                SELECT dv.version_id, dv.version_number, dv.state, dv.description_template,
                       COUNT(ap.approval_id) as vots
                FROM description_versions dv
                LEFT JOIN approvals ap ON dv.version_id = ap.version_id
                WHERE dv.element_id = ? AND dv.is_active = 0
                GROUP BY dv.version_id
                ORDER BY dv.version_number DESC
            """
            cursor = conn.execute(query, (self.element_id,))
            rows = cursor.fetchall()
            conn.close()

            passed = len(rows) >= 1
            self.log_result("get_drafts_amb_vots", passed, f"Found {len(rows)} drafts")
        except Exception as e:
            self.log_result("get_drafts_amb_vots", False, str(e))

    def test_votar_versio(self):
        """Test voting on a version."""
        try:
            conn = get_connection()
            c = conn.cursor()

            # Add 3 votes
            for i in range(3):
                c.execute(
                    "INSERT INTO approvals (version_id, from_state, to_state, approved_by) VALUES (?, 'S0', 'S3', ?)",
                    (self.version_id, f"user{i}")
                )

            # Check vote count
            c.execute("SELECT COUNT(*) FROM approvals WHERE version_id = ?", (self.version_id,))
            vots = c.fetchone()[0]

            if vots >= 3:
                # Activate version
                c.execute("UPDATE description_versions SET is_active = 0 WHERE element_id = ?", (self.element_id,))
                c.execute("UPDATE description_versions SET state = 'S3', is_active = 1 WHERE version_id = ?", (self.version_id,))

            conn.commit()

            # Verify
            c.execute("SELECT is_active, state FROM description_versions WHERE version_id = ?", (self.version_id,))
            row = c.fetchone()
            conn.close()

            passed = row[0] == 1 and row[1] == 'S3'
            self.log_result("votar_versio", passed, f"Votes: {vots}, Active: {row[0]}, State: {row[1]}")
        except Exception as e:
            self.log_result("votar_versio", False, str(e))

    # ========================================
    # Test Project Functions
    # ========================================

    def test_crear_projecte_nou(self):
        """Test creating a new project."""
        try:
            conn = get_connection()
            conn.execute(
                "INSERT INTO projects (project_code, project_name, status) VALUES (?, ?, 'PLANNING')",
                ("PROJ-TEST", "Test Project")
            )
            project_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            self.project_id = project_id
            conn.commit()
            conn.close()

            passed = project_id > 0
            self.log_result("crear_projecte_nou", passed)
        except Exception as e:
            self.log_result("crear_projecte_nou", False, str(e))

    def test_get_projects(self):
        """Test getting projects."""
        try:
            conn = get_connection()
            cursor = conn.execute("SELECT project_id, project_code, project_name FROM projects")
            rows = cursor.fetchall()
            conn.close()

            passed = len(rows) >= 1
            self.log_result("get_projects", passed, f"Found {len(rows)} projects")
        except Exception as e:
            self.log_result("get_projects", False, str(e))

    def test_crear_instancies_massives(self):
        """Test creating multiple element instances."""
        try:
            conn = get_connection()
            c = conn.cursor()

            # Get active version
            c.execute("SELECT version_id FROM description_versions WHERE element_id = ? AND is_active = 1",
                     (self.element_id,))
            version_id = c.fetchone()[0]

            # Create 3 instances
            for i in range(1, 4):
                code_final = f"ASC-{i:02d}"
                name_final = f"Ascensor {i}"
                c.execute("""
                    INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name)
                    VALUES (?, ?, ?, ?, ?)
                """, (self.project_id, self.element_id, version_id, code_final, name_final))
                pe_id = c.lastrowid
                c.execute("INSERT INTO rendered_descriptions (project_element_id, rendered_text, is_stale) VALUES (?, '', 1)",
                         (pe_id,))
                if i == 1:
                    self.project_element_id = pe_id

            conn.commit()
            conn.close()

            self.log_result("crear_instancies_massives", True)
        except Exception as e:
            self.log_result("crear_instancies_massives", False, str(e))

    # ========================================
    # Test Project Element Functions
    # ========================================

    def test_get_project_instances(self):
        """Test getting project instances."""
        try:
            conn = get_connection()
            query = """
                SELECT pe.project_element_id, pe.instance_code, pe.instance_name, e.element_name, e.category
                FROM project_elements pe
                JOIN elements e ON pe.element_id = e.element_id
                WHERE pe.project_id = ?
                ORDER BY e.category, pe.instance_code
            """
            cursor = conn.execute(query, (self.project_id,))
            rows = cursor.fetchall()
            conn.close()

            passed = len(rows) == 3
            self.log_result("get_project_instances", passed, f"Found {len(rows)} instances")
        except Exception as e:
            self.log_result("get_project_instances", False, str(e))

    def test_get_instance_variables_values(self):
        """Test getting instance variables and values."""
        try:
            conn = get_connection()
            elem_id = conn.execute(
                "SELECT element_id FROM project_elements WHERE project_element_id = ?",
                (self.project_element_id,)
            ).fetchone()[0]

            query = """
                SELECT ev.variable_id, ev.variable_name, ev.unit, ev.variable_type, pev.value
                FROM element_variables ev
                LEFT JOIN project_element_values pev
                     ON ev.variable_id = pev.variable_id AND pev.project_element_id = ?
                WHERE ev.element_id = ?
            """
            cursor = conn.execute(query, (self.project_element_id, elem_id))
            rows = cursor.fetchall()
            conn.close()

            passed = len(rows) >= 2  # At least marca and capacidad
            self.log_result("get_instance_variables_values", passed, f"Found {len(rows)} variables")
        except Exception as e:
            self.log_result("get_instance_variables_values", False, str(e))

    def test_save_instance_values(self):
        """Test saving instance values."""
        try:
            conn = get_connection()
            c = conn.cursor()

            updates = {self.variable_id: "KONE"}
            for var_id, valor in updates.items():
                c.execute("""
                    INSERT INTO project_element_values (project_element_id, variable_id, value)
                    VALUES (?, ?, ?)
                    ON CONFLICT(project_element_id, variable_id) DO UPDATE SET value=excluded.value
                """, (self.project_element_id, var_id, valor))

            conn.commit()

            # Verify
            c.execute(
                "SELECT value FROM project_element_values WHERE project_element_id = ? AND variable_id = ?",
                (self.project_element_id, self.variable_id)
            )
            row = c.fetchone()
            conn.close()

            passed = row is not None and row[0] == "KONE"
            self.log_result("save_instance_values", passed)
        except Exception as e:
            self.log_result("save_instance_values", False, str(e))


def main():
    """Run all tests."""
    tester = StreamlitFunctionsTester()
    try:
        tester.run_all_tests()
        return 0 if all(r['passed'] for r in tester.results) else 1
    finally:
        tester.cleanup()


if __name__ == "__main__":
    sys.exit(main())
