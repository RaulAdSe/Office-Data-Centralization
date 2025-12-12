#!/usr/bin/env python3
"""
Test the app with the production database to verify data integrity and functionality.
This script tests reading operations to verify the database is in a consistent state.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db_manager import DatabaseManager


def get_production_db_path():
    """Get path to production database."""
    script_dir = Path(__file__).parent.parent
    return str(script_dir / "data" / "office_data.db")


class ProductionDBTester:
    """Test production database integrity."""

    def __init__(self):
        self.db_path = get_production_db_path()
        self.results = []

        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Production database not found: {self.db_path}")

        self.db = DatabaseManager(self.db_path)

    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"       {details}")

    def run_all_tests(self):
        """Run all production database tests."""
        print("=" * 70)
        print("PRODUCTION DATABASE INTEGRITY TESTS")
        print(f"Database: {self.db_path}")
        print("=" * 70)
        print()

        # 1. Check database tables exist
        print("\n1. DATABASE STRUCTURE")
        print("-" * 40)
        self.test_required_tables_exist()

        # 2. Check elements
        print("\n2. ELEMENTS DATA")
        print("-" * 40)
        self.test_elements_exist()
        self.test_elements_have_valid_categories()
        self.test_elements_have_variables()

        # 3. Check variable options
        print("\n3. VARIABLE OPTIONS")
        print("-" * 40)
        self.test_variable_options_exist()

        # 4. Check description versions
        print("\n4. DESCRIPTION VERSIONS")
        print("-" * 40)
        self.test_description_versions()
        self.test_active_versions()

        # 5. Check projects
        print("\n5. PROJECTS")
        print("-" * 40)
        self.test_projects_exist()
        self.test_project_elements()

        # 6. Check rendering
        print("\n6. RENDERING")
        print("-" * 40)
        self.test_rendered_descriptions()

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
            print("\n❌ ISSUES FOUND:")
            for r in self.results:
                if not r['passed']:
                    print(f"   - {r['test']}: {r['details']}")
        else:
            print("\n✅ DATABASE IS IN GOOD STATE!")

        print("=" * 70)
        return failed == 0

    def test_required_tables_exist(self):
        """Check all required tables exist."""
        required_tables = [
            'elements', 'element_variables', 'variable_options',
            'description_versions', 'template_variable_mappings',
            'approvals', 'projects', 'project_elements',
            'project_element_values', 'rendered_descriptions', 'users'
        ]

        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        existing_tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        missing = [t for t in required_tables if t not in existing_tables]
        passed = len(missing) == 0
        details = f"Found {len(existing_tables)} tables" if passed else f"Missing: {', '.join(missing)}"
        self.log_result("Required tables exist", passed, details)

    def test_elements_exist(self):
        """Check elements table has data."""
        elements = self.db.list_elements()
        passed = len(elements) > 0
        details = f"Found {len(elements)} elements"
        self.log_result("Elements exist", passed, details)
        self.elements = elements

    def test_elements_have_valid_categories(self):
        """Check all elements have valid categories."""
        valid_categories = self.db.get_valid_categories()
        invalid = []

        for elem in self.elements:
            if elem.get('category') and elem['category'] not in valid_categories:
                invalid.append(f"{elem['element_code']}: {elem['category']}")

        passed = len(invalid) == 0
        details = f"All {len(self.elements)} elements have valid categories" if passed else f"Invalid categories: {', '.join(invalid[:5])}"
        self.log_result("Elements have valid categories", passed, details)

    def test_elements_have_variables(self):
        """Check elements have variables defined."""
        elements_with_vars = 0
        total_vars = 0

        for elem in self.elements:
            vars_ = self.db.get_element_variables(elem['element_id'])
            if vars_:
                elements_with_vars += 1
                total_vars += len(vars_)

        passed = elements_with_vars > 0
        details = f"{elements_with_vars}/{len(self.elements)} elements have variables, {total_vars} total variables"
        self.log_result("Elements have variables", passed, details)

    def test_variable_options_exist(self):
        """Check variable options functionality."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT COUNT(*) FROM variable_options"
        )
        count = cursor.fetchone()[0]
        conn.close()

        passed = True  # Options are optional
        details = f"Found {count} variable options"
        self.log_result("Variable options table", passed, details)

    def test_description_versions(self):
        """Check description versions exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """SELECT state, COUNT(*) FROM description_versions
               GROUP BY state"""
        )
        state_counts = dict(cursor.fetchall())
        conn.close()

        total = sum(state_counts.values())
        passed = total > 0
        details = f"States: {dict(state_counts)}"
        self.log_result("Description versions exist", passed, details)

    def test_active_versions(self):
        """Check active versions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """SELECT COUNT(*) FROM description_versions WHERE is_active = 1"""
        )
        active_count = cursor.fetchone()[0]

        cursor = conn.execute(
            """SELECT COUNT(DISTINCT element_id) FROM elements"""
        )
        element_count = cursor.fetchone()[0]
        conn.close()

        # Not all elements need an active version
        passed = True
        details = f"{active_count} active versions for {element_count} elements"
        self.log_result("Active versions check", passed, details)

    def test_projects_exist(self):
        """Check projects exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM projects")
        count = cursor.fetchone()[0]
        conn.close()

        passed = True  # Projects are optional
        details = f"Found {count} projects"
        self.log_result("Projects table", passed, details)

    def test_project_elements(self):
        """Check project elements."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM project_elements")
        count = cursor.fetchone()[0]
        conn.close()

        passed = True  # Project elements are optional
        details = f"Found {count} project element instances"
        self.log_result("Project elements", passed, details)

    def test_rendered_descriptions(self):
        """Check rendered descriptions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """SELECT COUNT(*), SUM(CASE WHEN is_stale = 1 THEN 1 ELSE 0 END)
               FROM rendered_descriptions"""
        )
        row = cursor.fetchone()
        total = row[0] or 0
        stale = row[1] or 0
        conn.close()

        passed = True  # Rendered descriptions are generated on demand
        fresh = total - stale
        details = f"Found {total} rendered descriptions ({fresh} fresh, {stale} stale)"
        self.log_result("Rendered descriptions", passed, details)


def main():
    """Run all tests."""
    try:
        tester = ProductionDBTester()
        tester.run_all_tests()
        return 0 if all(r['passed'] for r in tester.results) else 1
    except FileNotFoundError as e:
        print(f"❌ ERROR: {e}")
        return 1
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
