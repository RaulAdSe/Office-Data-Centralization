"""
Database Manager for Element Description System

This module provides a comprehensive database manager for the SQLite-based
element description system, including all CRUD operations and workflow functions.
"""

import sqlite3
import re
from typing import Optional, List, Dict, Tuple, Any
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager


class DatabaseManager:
    """
    Manages database operations for the element description system.
    
    Handles:
    - Database initialization and schema setup
    - Element and variable management
    - Description versioning and approval workflow
    - Project and element instance management
    - Description rendering
    """
    
    def __init__(self, db_path: str = "elements.db"):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._ensure_database()
    
    def _ensure_database(self):
        """Create database and tables if they don't exist."""
        # Try updated_schema.sql first, fall back to schema.sql
        schema_path = Path(__file__).parent.parent / "updated_schema.sql"
        if not schema_path.exists():
            schema_path = Path(__file__).parent / "schema.sql"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with self.get_connection() as conn:
            # Check if database is new (no tables exist)
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='elements'"
            )
            is_new_db = cursor.fetchone() is None
            
            if is_new_db:
                # New database - create all tables
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                # Remove COMMENT statements (SQLite doesn't support them)
                schema_sql = re.sub(r'COMMENT ON TABLE.*?;', '', schema_sql, flags=re.IGNORECASE | re.DOTALL)
                conn.executescript(schema_sql)
                conn.commit()
            else:
                # Existing database - migrate if needed
                self._migrate_database(conn)
    
    def _migrate_database(self, conn: sqlite3.Connection):
        """
        Migrate existing database to add new tables/views if needed.
        
        Args:
            conn: Database connection
        """
        # Check if price column exists in elements table
        cursor = conn.execute("PRAGMA table_info(elements)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'price' not in columns:
            conn.execute("ALTER TABLE elements ADD COLUMN price REAL")
            conn.commit()
            
        # Check if category column exists in elements table
        if 'category' not in columns:
            conn.execute("ALTER TABLE elements ADD COLUMN category VARCHAR(50)")
            conn.commit()
            
        # Check if construction_categories table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='construction_categories'"
        )
        if cursor.fetchone() is None:
            # Create the construction categories reference table
            self._create_construction_categories_table(conn)
        
        # Check if template_variable_mappings table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='template_variable_mappings'"
        )
        if cursor.fetchone() is None:
            # Create the new table
            conn.execute("""
                CREATE TABLE template_variable_mappings (
                    mapping_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_id      INTEGER NOT NULL REFERENCES description_versions(version_id) ON DELETE CASCADE,
                    variable_id     INTEGER NOT NULL REFERENCES element_variables(variable_id) ON DELETE CASCADE,
                    placeholder     VARCHAR(100) NOT NULL,
                    position        INTEGER NOT NULL,
                    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
                    
                    UNIQUE (version_id, placeholder),
                    UNIQUE (version_id, position)
                )
            """)
            conn.execute("CREATE INDEX idx_template_mappings_version ON template_variable_mappings(version_id)")
            conn.execute("CREATE INDEX idx_template_mappings_variable ON template_variable_mappings(variable_id)")
            
            # Create mappings for existing description versions
            cursor = conn.execute("SELECT version_id, element_id, description_template FROM description_versions")
            for row in cursor.fetchall():
                version_id = row['version_id']
                element_id = row['element_id']
                template = row['description_template']
                
                # Extract placeholders
                placeholders = self.extract_placeholders(template)
                unique_placeholders = []
                seen = set()
                for p in placeholders:
                    if p not in seen:
                        unique_placeholders.append(p)
                        seen.add(p)
                
                # Get variables for this element
                var_cursor = conn.execute(
                    "SELECT variable_id, variable_name FROM element_variables WHERE element_id = ?",
                    (element_id,)
                )
                var_map = {row['variable_name']: row['variable_id'] for row in var_cursor.fetchall()}
                
                # Create mappings
                position = 1
                for placeholder in unique_placeholders:
                    if placeholder in var_map:
                        conn.execute(
                            """INSERT INTO template_variable_mappings 
                               (version_id, variable_id, placeholder, position)
                               VALUES (?, ?, ?, ?)""",
                            (version_id, var_map[placeholder], placeholder, position)
                        )
                        position += 1
            
            conn.commit()
        
        # variable_options table is part of the main schema now
        
        # Check if view exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='view' AND name='v_template_variable_mappings'"
        )
        if cursor.fetchone() is None:
            conn.execute("""
                CREATE VIEW v_template_variable_mappings AS
                SELECT 
                    e.element_code,
                    dv.version_id,
                    dv.version_number,
                    dv.description_template,
                    dv.state,
                    tvm.placeholder,
                    tvm.position,
                    ev.variable_name,
                    ev.variable_type,
                    ev.unit
                FROM template_variable_mappings tvm
                JOIN description_versions dv ON tvm.version_id = dv.version_id
                JOIN elements e ON dv.element_id = e.element_id
                JOIN element_variables ev ON tvm.variable_id = ev.variable_id
                ORDER BY dv.version_id, tvm.position
            """)
            conn.commit()
        
        # Check if v_element_variables_with_options view exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='view' AND name='v_element_variables_with_options'"
        )
        if cursor.fetchone() is None:
            conn.execute("""
                CREATE VIEW v_element_variables_with_options AS
                SELECT 
                    e.element_code,
                    e.element_name,
                    ev.variable_id,
                    ev.variable_name,
                    ev.variable_type,
                    ev.unit,
                    ev.default_value,
                    ev.is_required,
                    ev.display_order,
                    CASE 
                        WHEN EXISTS (SELECT 1 FROM variable_options WHERE variable_id = ev.variable_id)
                        THEN 'DROPDOWN'
                        ELSE 'FREE_INPUT'
                    END AS input_type,
                    (SELECT COUNT(*) FROM variable_options WHERE variable_id = ev.variable_id) AS option_count
                FROM elements e
                JOIN element_variables ev ON e.element_id = ev.element_id
                ORDER BY e.element_code, ev.display_order
            """)
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """
        Get a database connection with proper transaction handling.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # ============================================================
    # ELEMENT MANAGEMENT
    # ============================================================
    
    def create_element(
        self,
        element_code: str,
        element_name: str,
        category: str,  # Required category parameter
        created_by: Optional[str] = None
    ) -> int:
        """
        Create a new element.
        
        Args:
            element_code: Unique code for the element
            element_name: Name of the element
            category: Construction category (must be from the 33 official categories)
            created_by: User who created the element
            
        Returns:
            element_id of the created element
            
        Raises:
            ValueError: If category is not valid
        """
        # Validate category
        if not self.validate_category(category):
            valid_categories = self.get_valid_categories()
            raise ValueError(
                f"Invalid category '{category}'. Must be one of: {', '.join(valid_categories)}"
            )
            
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO elements (element_code, element_name, category, created_by)
                   VALUES (?, ?, ?, ?)""",
                (element_code, element_name, category, created_by)
            )
            return cursor.lastrowid
    
    def get_element(self, element_id: int) -> Optional[Dict[str, Any]]:
        """Get element by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM elements WHERE element_id = ?",
                (element_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_element_by_code(self, element_code: str) -> Optional[Dict[str, Any]]:
        """Get element by code."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM elements WHERE element_code = ?",
                (element_code,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_elements(self) -> List[Dict[str, Any]]:
        """List all elements."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM elements ORDER BY element_code")
            return [dict(row) for row in cursor.fetchall()]
    
    def update_element_price(self, element_id: int, price: Optional[float]) -> bool:
        """
        Update the price of an element.
        
        Args:
            element_id: ID of the element
            price: New price value (None to clear the price)
            
        Returns:
            True if successful
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE elements SET price = ? WHERE element_id = ?",
                (price, element_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    # ============================================================
    # VARIABLE MANAGEMENT
    # ============================================================
    
    def add_variable(
        self,
        element_id: int,
        variable_name: str,
        variable_type: str,
        unit: Optional[str] = None,
        default_value: Optional[str] = None,
        is_required: bool = True,
        display_order: int = 0,
        options: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        """
        Add a variable to an element.
        
        Args:
            element_id: ID of the element
            variable_name: Name of the variable
            variable_type: Type (TEXT, NUMERIC, DATE)
            unit: Optional unit
            default_value: Optional default value
            is_required: Whether the variable is required
            display_order: Display order
            options: Optional list of option dictionaries with keys:
                     - option_value (required): The value
                     - option_label (optional): Display label
                     - display_order (optional): Order for display
                     - is_default (optional): Whether this is the default option
            
        Returns:
            variable_id of the created variable
        """
        if variable_type not in ('TEXT', 'NUMERIC', 'DATE'):
            raise ValueError(f"Invalid variable_type: {variable_type}")
        
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO element_variables 
                   (element_id, variable_name, variable_type, unit, default_value, is_required, display_order)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (element_id, variable_name, variable_type, unit, default_value, 
                 int(is_required), display_order)
            )
            variable_id = cursor.lastrowid
            
            # Add options to variable_options table if provided
            if options:
                for opt in options:
                    conn.execute(
                        """INSERT INTO variable_options 
                           (variable_id, option_value, option_label, display_order, is_default)
                           VALUES (?, ?, ?, ?, ?)""",
                        (variable_id, opt['option_value'], opt.get('option_label'),
                         opt.get('display_order', 0), int(opt.get('is_default', False)))
                    )
            
            conn.commit()
            return variable_id
    
    def get_element_variables(self, element_id: int, include_options: bool = True) -> List[Dict[str, Any]]:
        """
        Get all variables for an element.
        
        Args:
            element_id: ID of the element
            include_options: Whether to include options for each variable
            
        Returns:
            List of variable dictionaries, each optionally including an 'options' key
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM element_variables 
                   WHERE element_id = ? 
                   ORDER BY display_order, variable_name""",
                (element_id,)
            )
            variables = [dict(row) for row in cursor.fetchall()]
            
            # Add options if requested
            if include_options:
                for var in variables:
                    var['options'] = self.get_variable_options(var['variable_id'])
            
            return variables
    
    # ============================================================
    # VARIABLE OPTIONS MANAGEMENT
    # ============================================================
    
    def add_variable_option(
        self,
        variable_id: int,
        option_value: str,
        option_label: Optional[str] = None,
        display_order: int = 0,
        is_default: bool = False
    ) -> int:
        """
        Add an option to a variable.
        
        Args:
            variable_id: ID of the variable
            option_value: The option value (required, must be unique per variable)
            option_label: Optional display label
            display_order: Display order
            is_default: Whether this is the default option
            
        Returns:
            option_id of the created option
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO variable_options 
                   (variable_id, option_value, option_label, display_order, is_default)
                   VALUES (?, ?, ?, ?, ?)""",
                (variable_id, option_value, option_label, display_order, int(is_default))
            )
            return cursor.lastrowid
    
    def get_variable_options(self, variable_id: int) -> List[Dict[str, Any]]:
        """
        Get all options for a variable.
        
        Args:
            variable_id: ID of the variable
            
        Returns:
            List of option dictionaries ordered by display_order
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM variable_options 
                   WHERE variable_id = ? 
                   ORDER BY display_order, option_value""",
                (variable_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def update_variable_option(
        self,
        option_id: int,
        option_value: Optional[str] = None,
        option_label: Optional[str] = None,
        display_order: Optional[int] = None,
        is_default: Optional[bool] = None
    ) -> bool:
        """
        Update an existing variable option.
        
        Args:
            option_id: ID of the option to update
            option_value: New option value (if provided)
            option_label: New option label (if provided)
            display_order: New display order (if provided)
            is_default: New default flag (if provided)
            
        Returns:
            True if successful
        """
        updates = []
        params = []
        
        if option_value is not None:
            updates.append("option_value = ?")
            params.append(option_value)
        if option_label is not None:
            updates.append("option_label = ?")
            params.append(option_label)
        if display_order is not None:
            updates.append("display_order = ?")
            params.append(display_order)
        if is_default is not None:
            updates.append("is_default = ?")
            params.append(int(is_default))
        
        if not updates:
            return False
        
        params.append(option_id)
        
        with self.get_connection() as conn:
            sql = "UPDATE variable_options SET " + ', '.join(updates) + " WHERE option_id = ?"
            conn.execute(
                sql,
                params
            )
            conn.commit()
            return True
    
    def delete_variable_option(self, option_id: int) -> bool:
        """
        Delete a variable option.
        
        Args:
            option_id: ID of the option to delete
            
        Returns:
            True if successful
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM variable_options WHERE option_id = ?",
                (option_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def set_variable_default_option(self, variable_id: int, option_value: str) -> bool:
        """
        Set the default option for a variable.
        First clears all defaults for the variable, then sets the specified option as default.
        
        Args:
            variable_id: ID of the variable
            option_value: Value of the option to set as default
            
        Returns:
            True if successful
        """
        with self.get_connection() as conn:
            # Clear all defaults for this variable
            conn.execute(
                "UPDATE variable_options SET is_default = 0 WHERE variable_id = ?",
                (variable_id,)
            )
            
            # Set the specified option as default
            cursor = conn.execute(
                "UPDATE variable_options SET is_default = 1 WHERE variable_id = ? AND option_value = ?",
                (variable_id, option_value)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def get_variable_with_options(self, variable_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a variable with its options.
        
        Args:
            variable_id: ID of the variable
            
        Returns:
            Dictionary with variable info and options, or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM element_variables WHERE variable_id = ?",
                (variable_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            
            var_dict = dict(row)
            var_dict['options'] = self.get_variable_options(variable_id)
            return var_dict
    
    # ============================================================
    # TEMPLATE VALIDATION
    # ============================================================
    
    def extract_placeholders(self, template: str) -> List[str]:
        """
        Extract placeholder names from a template string.
        
        Args:
            template: Template string with {placeholder} syntax
            
        Returns:
            List of placeholder names in order of appearance
        """
        pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
        matches = re.findall(pattern, template)
        # Return in order of appearance, preserving duplicates for position tracking
        return matches
    
    def _create_template_mappings(
        self,
        conn: sqlite3.Connection,
        version_id: int,
        element_id: int,
        template: str
    ):
        """
        Create template variable mappings for a version.
        
        Args:
            conn: Database connection
            version_id: ID of the description version
            element_id: ID of the element
            template: Template string
        """
        # Get all placeholders in order of appearance
        placeholders = self.extract_placeholders(template)
        
        # Get variables for this element
        variables = self.get_element_variables(element_id)
        var_map = {v['variable_name']: v['variable_id'] for v in variables}
        
        # Create mappings with position
        position = 1
        seen_placeholders = set()
        for placeholder in placeholders:
            # Skip if we've already mapped this placeholder (duplicate in template)
            if placeholder in seen_placeholders:
                continue
            
            if placeholder not in var_map:
                # This should not happen if validation passed, but handle gracefully
                continue
            
            variable_id = var_map[placeholder]
            conn.execute(
                """INSERT INTO template_variable_mappings 
                   (version_id, variable_id, placeholder, position)
                   VALUES (?, ?, ?, ?)""",
                (version_id, variable_id, placeholder, position)
            )
            seen_placeholders.add(placeholder)
            position += 1
    
    def validate_template_placeholders(
        self,
        element_id: int,
        template: str
    ) -> Dict[str, Any]:
        """
        Validate that all placeholders in template match element variables.
        
        Args:
            element_id: ID of the element
            template: Template string to validate
            
        Returns:
            Dictionary with is_valid, message, missing_variables, undefined_placeholders
        """
        placeholders = self.extract_placeholders(template)
        # Use set to get unique placeholders for validation
        unique_placeholders = set(placeholders)
        variables = self.get_element_variables(element_id)
        variable_names = [v['variable_name'] for v in variables]
        required_variables = [v['variable_name'] for v in variables if v['is_required']]
        
        undefined = [p for p in unique_placeholders if p not in variable_names]
        missing = [v for v in required_variables if v not in unique_placeholders]
        
        if undefined:
            return {
                'is_valid': False,
                'message': 'Template contains undefined placeholders',
                'missing_variables': missing,
                'undefined_placeholders': undefined
            }
        
        if missing:
            return {
                'is_valid': False,
                'message': 'Template missing required variables',
                'missing_variables': missing,
                'undefined_placeholders': undefined
            }
        
        return {
            'is_valid': True,
            'message': 'Valid',
            'missing_variables': [],
            'undefined_placeholders': []
        }
    
    # ============================================================
    # VERSION MANAGEMENT
    # ============================================================
    
    def get_next_version_number(self, element_id: int) -> int:
        """Get the next version number for an element."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT COALESCE(MAX(version_number), 0) + 1 
                   FROM description_versions 
                   WHERE element_id = ?""",
                (element_id,)
            )
            return cursor.fetchone()[0]
    
    def create_proposal(
        self,
        element_id: int,
        description_template: str,
        created_by: str
    ) -> int:
        """
        Create a new description version proposal.
        
        Args:
            element_id: ID of the element
            description_template: Template string
            created_by: User creating the proposal
            
        Returns:
            version_id of the created proposal
            
        Raises:
            ValueError: If element doesn't exist or template is invalid
        """
        if not self.get_element(element_id):
            raise ValueError(f"Element {element_id} does not exist")
        
        validation = self.validate_template_placeholders(element_id, description_template)
        if not validation['is_valid']:
            raise ValueError(
                f"Invalid template: {validation['message']}. "
                f"Missing: {', '.join(validation['missing_variables'])}. "
                f"Undefined: {', '.join(validation['undefined_placeholders'])}"
            )
        
        version_number = self.get_next_version_number(element_id)
        
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO description_versions 
                   (element_id, description_template, state, is_active, version_number, created_by)
                   VALUES (?, ?, 'S0', 0, ?, ?)""",
                (element_id, description_template, version_number, created_by)
            )
            version_id = cursor.lastrowid
            
            # Create template variable mappings
            self._create_template_mappings(conn, version_id, element_id, description_template)
            conn.commit()
            
            return version_id
    
    def get_version(self, version_id: int) -> Optional[Dict[str, Any]]:
        """Get version by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM description_versions WHERE version_id = ?""",
                (version_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_active_version(self, element_id: int) -> Optional[Dict[str, Any]]:
        """Get the active version for an element."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM description_versions 
                   WHERE element_id = ? AND is_active = 1""",
                (element_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # ============================================================
    # APPROVAL WORKFLOW
    # ============================================================
    
    def approve_proposal(
        self,
        version_id: int,
        approved_by: str,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve a proposal, moving it to the next state.
        
        State transitions:
        - S0 -> S1
        - S1 -> S2
        - S2 -> S3 (becomes active)
        
        Args:
            version_id: ID of the version to approve
            approved_by: User approving the proposal
            comments: Optional comments
            
        Returns:
            Dictionary with success, message, and new_state
        """
        version = self.get_version(version_id)
        if not version:
            return {
                'success': False,
                'message': 'Version not found',
                'new_state': None
            }
        
        current_state = version['state']
        state_transitions = {
            'S0': 'S1',
            'S1': 'S2',
            'S2': 'S3'
        }
        
        if current_state not in state_transitions:
            return {
                'success': False,
                'message': f'Cannot approve from state {current_state}',
                'new_state': None
            }
        
        next_state = state_transitions[current_state]
        element_id = version['element_id']
        
        with self.get_connection() as conn:
            # If moving to S3, deactivate old active version
            if next_state == 'S3':
                conn.execute(
                    """UPDATE description_versions 
                       SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                       WHERE element_id = ? AND is_active = 1""",
                    (element_id,)
                )
                
                # Set new version as active
                conn.execute(
                    """UPDATE description_versions 
                       SET state = ?, is_active = 1, updated_at = CURRENT_TIMESTAMP
                       WHERE version_id = ?""",
                    (next_state, version_id)
                )
            else:
                # Just update state
                conn.execute(
                    """UPDATE description_versions 
                       SET state = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE version_id = ?""",
                    (next_state, version_id)
                )
            
            # Record approval
            conn.execute(
                """INSERT INTO approvals (version_id, from_state, to_state, approved_by, comments)
                   VALUES (?, ?, ?, ?, ?)""",
                (version_id, current_state, next_state, approved_by, comments)
            )
            conn.commit()
        
        return {
            'success': True,
            'message': 'Approved',
            'new_state': next_state
        }
    
    def reject_proposal(
        self,
        version_id: int,
        rejected_by: str,
        reason: str
    ) -> bool:
        """
        Reject a proposal, moving it to state 'D' (deleted).
        
        Args:
            version_id: ID of the version to reject
            rejected_by: User rejecting the proposal
            reason: Reason for rejection
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If version not found or in invalid state
        """
        version = self.get_version(version_id)
        if not version:
            raise ValueError(f"Version {version_id} not found")
        
        current_state = version['state']
        if current_state in ('S3', 'D'):
            raise ValueError(f"Cannot reject version in state {current_state}")
        
        with self.get_connection() as conn:
            conn.execute(
                """UPDATE description_versions 
                   SET state = 'D', updated_at = CURRENT_TIMESTAMP
                   WHERE version_id = ?""",
                (version_id,)
            )
            
            conn.execute(
                """INSERT INTO approvals (version_id, from_state, to_state, approved_by, comments)
                   VALUES (?, ?, 'D', ?, ?)""",
                (version_id, current_state, rejected_by, reason)
            )
            conn.commit()
        
        return True
    
    def get_pending_proposals(self) -> List[Dict[str, Any]]:
        """Get all pending proposals (S0, S1, S2)."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM v_pending_proposals 
                   ORDER BY element_code, state DESC, created_at"""
            )
            return [dict(row) for row in cursor.fetchall()]
    
    # ============================================================
    # PROJECT MANAGEMENT
    # ============================================================
    
    def create_project(
        self,
        project_code: str,
        project_name: str,
        status: str = 'PLANNING',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        location: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> int:
        """Create a new project."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO projects 
                   (project_code, project_name, status, start_date, end_date, location, created_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (project_code, project_name, status, start_date, end_date, location, created_by)
            )
            return cursor.lastrowid
    
    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get project by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM projects WHERE project_id = ?",
                (project_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_project_by_code(self, project_code: str) -> Optional[Dict[str, Any]]:
        """Get project by code."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM projects WHERE project_code = ?",
                (project_code,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # ============================================================
    # PROJECT ELEMENT INSTANCES
    # ============================================================
    
    def create_project_element(
        self,
        project_id: int,
        element_id: int,
        description_version_id: int,
        instance_code: str,
        instance_name: Optional[str] = None,
        location: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> int:
        """
        Create a project element instance.
        
        Args:
            project_id: ID of the project
            element_id: ID of the element type
            description_version_id: ID of the description version to use
            instance_code: Unique code for this instance
            instance_name: Optional name
            location: Optional location
            created_by: User creating the instance
            
        Returns:
            project_element_id
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO project_elements 
                   (project_id, element_id, description_version_id, instance_code, 
                    instance_name, location, created_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (project_id, element_id, description_version_id, instance_code,
                 instance_name, location, created_by)
            )
            return cursor.lastrowid
    
    def set_element_value(
        self,
        project_element_id: int,
        variable_id: int,
        value: str,
        updated_by: Optional[str] = None
    ):
        """
        Set a value for a project element variable.
        
        Args:
            project_element_id: ID of the project element
            variable_id: ID of the variable
            value: Value to set
            updated_by: User updating the value
        """
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO project_element_values 
                   (project_element_id, variable_id, value, updated_by)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(project_element_id, variable_id) 
                   DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP, updated_by = ?""",
                (project_element_id, variable_id, value, updated_by, value, updated_by)
            )
            conn.commit()
    
    def get_element_values(self, project_element_id: int) -> Dict[str, str]:
        """
        Get all values for a project element.
        
        Returns:
            Dictionary mapping variable_name to value
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT ev.variable_name, pev.value
                   FROM project_element_values pev
                   JOIN element_variables ev ON pev.variable_id = ev.variable_id
                   WHERE pev.project_element_id = ?""",
                (project_element_id,)
            )
            return {row['variable_name']: row['value'] for row in cursor.fetchall()}
    
    # ============================================================
    # DESCRIPTION RENDERING
    # ============================================================
    
    def render_description(self, project_element_id: int) -> str:
        """
        Render a description for a project element.
        
        Uses explicit template variable mappings to replace placeholders.
        
        Args:
            project_element_id: ID of the project element
            
        Returns:
            Rendered description text
        """
        with self.get_connection() as conn:
            # Get template and version_id
            cursor = conn.execute(
                """SELECT dv.description_template, dv.version_id
                   FROM project_elements pe
                   JOIN description_versions dv ON pe.description_version_id = dv.version_id
                   WHERE pe.project_element_id = ?""",
                (project_element_id,)
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Project element {project_element_id} not found")
            
            template = row['description_template']
            version_id = row['version_id']
            
            # Get mappings for this version
            cursor = conn.execute(
                """SELECT tvm.placeholder, ev.variable_name
                   FROM template_variable_mappings tvm
                   JOIN element_variables ev ON tvm.variable_id = ev.variable_id
                   WHERE tvm.version_id = ?
                   ORDER BY tvm.position""",
                (version_id,)
            )
            mappings = {row['placeholder']: row['variable_name'] for row in cursor.fetchall()}
            
            # Get values
            values = self.get_element_values(project_element_id)
            
            # Replace placeholders using mappings
            rendered = template
            for placeholder, var_name in mappings.items():
                if var_name in values:
                    rendered = rendered.replace(f'{{{placeholder}}}', values[var_name])
            
            return rendered
    
    def upsert_rendered_description(self, project_element_id: int):
        """
        Render and store the description for a project element.
        
        Args:
            project_element_id: ID of the project element
        """
        rendered = self.render_description(project_element_id)
        
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO rendered_descriptions 
                   (project_element_id, rendered_text, is_stale, rendered_at)
                   VALUES (?, ?, 0, CURRENT_TIMESTAMP)
                   ON CONFLICT(project_element_id) 
                   DO UPDATE SET 
                       rendered_text = ?,
                       is_stale = 0,
                       rendered_at = CURRENT_TIMESTAMP""",
                (project_element_id, rendered, rendered)
            )
            conn.commit()
    
    def get_rendered_description(self, project_element_id: int) -> Optional[Dict[str, Any]]:
        """Get rendered description for a project element."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM rendered_descriptions 
                   WHERE project_element_id = ?""",
                (project_element_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # ============================================================
    # CATEGORY MANAGEMENT
    # ============================================================
    
    def _create_construction_categories_table(self, conn: sqlite3.Connection):
        """
        Create the construction_categories reference table with 33 categories.
        
        Args:
            conn: Database connection
        """
        # Import the official 33 categories
        from construction_categories import DATABASE_CATEGORIES, CATEGORY_GROUPS
        
        # Create table
        conn.execute("""
            CREATE TABLE construction_categories (
                category_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name   VARCHAR(50) NOT NULL UNIQUE,
                display_order   INTEGER NOT NULL,
                logical_group   VARCHAR(50),
                description     TEXT,
                created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index
        conn.execute("CREATE INDEX idx_construction_categories_name ON construction_categories(category_name)")
        
        # Insert all 33 categories with logical groups
        for order, category in enumerate(DATABASE_CATEGORIES, 1):
            # Find logical group for this category
            logical_group = None
            for group_name, categories in CATEGORY_GROUPS.items():
                if category in categories:
                    logical_group = group_name
                    break
            
            description = f'Elementos de {category.lower()}'
            
            conn.execute(
                """INSERT INTO construction_categories 
                   (category_name, display_order, logical_group, description) 
                   VALUES (?, ?, ?, ?)""",
                (category, order, logical_group, description)
            )
        
        conn.commit()
    
    def validate_category(self, category: str) -> bool:
        """
        Validate that a category is one of the 33 official categories.
        
        Args:
            category: Category name to validate
            
        Returns:
            True if valid, False otherwise
        """
        valid_categories = self.get_valid_categories()
        return category in valid_categories
    
    def get_valid_categories(self) -> List[str]:
        """
        Get list of valid construction categories.
        
        Returns:
            List of valid category names
        """
        from construction_categories import DATABASE_CATEGORIES
        return DATABASE_CATEGORIES.copy()
    
    def get_categories_by_group(self) -> Dict[str, List[str]]:
        """
        Get categories organized by logical groups.
        
        Returns:
            Dictionary mapping group names to category lists
        """
        from construction_categories import CATEGORY_GROUPS
        return CATEGORY_GROUPS.copy()
    
    def get_category_info(self, category: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a category.
        
        Args:
            category: Category name
            
        Returns:
            Dictionary with category info or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM construction_categories 
                   WHERE category_name = ?""",
                (category,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_template_mappings(self, version_id: int) -> List[Dict[str, Any]]:
        """
        Get template variable mappings for a version.
        
        Args:
            version_id: ID of the description version
            
        Returns:
            List of mapping dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT tvm.*, ev.variable_name, ev.variable_type, ev.unit
                   FROM template_variable_mappings tvm
                   JOIN element_variables ev ON tvm.variable_id = ev.variable_id
                   WHERE tvm.version_id = ?
                   ORDER BY tvm.position""",
                (version_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

