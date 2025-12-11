"""
Database Manager for Element Description System

This module provides a comprehensive database manager for the SQLite-based
element description system, including all CRUD operations and workflow functions.

Refactored with dataclasses for type safety and clean API.
"""

import sqlite3
import re
import os
import bcrypt
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass, field


# ============================================================
# DATACLASSES - Clean, typed data structures
# ============================================================

@dataclass
class Element:
    """Represents a catalog element (e.g., 'Muro Cortina', 'Pilar')."""
    element_id: int
    element_code: str
    element_name: str
    category: str
    price: Optional[float] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None


@dataclass
class VariableOption:
    """An option for a dropdown variable."""
    option_id: int
    variable_id: int
    option_value: str
    display_order: int = 0


@dataclass
class Variable:
    """A variable belonging to an element (e.g., 'tipo_vidrio', 'espesor')."""
    variable_id: int
    element_id: int
    variable_name: str
    variable_type: str  # TEXT, NUMERIC, DATE
    unit: Optional[str] = None
    default_value: Optional[str] = None
    is_required: bool = True
    display_order: int = 0
    options: List[VariableOption] = field(default_factory=list)


@dataclass
class DescriptionVersion:
    """A version of a description template with approval state."""
    version_id: int
    element_id: int
    description_template: str
    state: str  # S0, S1, S2, S3, D
    is_active: bool
    version_number: int
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None


@dataclass
class Approval:
    """An approval vote for a description version."""
    approval_id: int
    version_id: int
    from_state: str
    to_state: str
    approved_by: str
    approver_role: str  # admin, editor
    approved_at: Optional[datetime] = None
    comments: Optional[str] = None


@dataclass
class User:
    """A system user with role-based permissions."""
    user_id: int
    username: str
    full_name: Optional[str]
    role: str  # admin, editor, viewer
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


@dataclass
class Project:
    """A construction project."""
    project_id: int
    project_code: str
    project_name: str
    status: str = 'PLANNING'
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None


@dataclass
class ProjectElement:
    """An instance of an element within a project."""
    project_element_id: int
    project_id: int
    element_id: int
    description_version_id: int
    instance_code: str
    instance_name: Optional[str] = None
    location: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    values: Dict[str, str] = field(default_factory=dict)
    rendered_description: Optional[str] = None


@dataclass
class VoteStatus:
    """Status of votes for a version."""
    version_id: int
    editor_votes: int
    admin_votes: int
    is_approved: bool

    @property
    def needs_editor(self) -> bool:
        """Returns True if the version still needs an editor's vote."""
        return self.editor_votes < 1

    @property
    def needs_admin(self) -> bool:
        """Returns True if the version still needs an admin's vote."""
        return self.admin_votes < 1


# ============================================================
# DATABASE MANAGER
# ============================================================

class DatabaseManager:
    """
    Manages database operations for the element description system.

    Features:
    - Element and variable management with dataclasses
    - User authentication with bcrypt
    - Role-based voting system (1 editor + 1 admin to approve)
    - Description versioning and approval workflow
    - Project and element instance management
    """

    def __init__(self, db_path: str = "office_data.db"):
        """Initialize the database manager."""
        self.db_path = db_path

    @contextmanager
    def get_connection(self):
        """Get a database connection with proper transaction handling."""
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
    # USER MANAGEMENT & AUTHENTICATION
    # ============================================================

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username and password.

        Args:
            username: The username
            password: The plain text password

        Returns:
            User object if authenticated, None otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE username = ? AND is_active = 1",
                (username,)
            )
            row = cursor.fetchone()

            if row:
                stored_hash = row['password_hash']
                # Handle both string and bytes storage (SQLite TEXT vs BLOB)
                if isinstance(stored_hash, str):
                    stored_hash = stored_hash.encode('utf-8')
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                    # Update last login
                    conn.execute(
                        "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?",
                        (row['user_id'],)
                    )
                    return User(
                        user_id=row['user_id'],
                        username=row['username'],
                        full_name=row['full_name'],
                        role=row['role'],
                        is_active=bool(row['is_active']),
                        created_at=row['created_at'],
                        last_login=datetime.now()
                    )
            return None

    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if row:
                return User(
                    user_id=row['user_id'],
                    username=row['username'],
                    full_name=row['full_name'],
                    role=row['role'],
                    is_active=bool(row['is_active']),
                    created_at=row['created_at'],
                    last_login=row['last_login']
                )
            return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            if row:
                return User(
                    user_id=row['user_id'],
                    username=row['username'],
                    full_name=row['full_name'],
                    role=row['role'],
                    is_active=bool(row['is_active']),
                    created_at=row['created_at'],
                    last_login=row['last_login']
                )
            return None

    def create_user(
        self,
        username: str,
        password: str,
        full_name: Optional[str] = None,
        role: str = 'editor'
    ) -> User:
        """
        Create a new user.

        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            full_name: Display name
            role: 'admin', 'editor', or 'viewer'

        Returns:
            Created User object
        """
        if role not in ('admin', 'editor', 'viewer'):
            raise ValueError(f"Invalid role: {role}. Must be admin, editor, or viewer.")

        # Check if username already exists
        if self.get_user_by_username(username):
            raise ValueError(f"Username '{username}' already exists.")

        # Store hash as string for SQLite TEXT column compatibility
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO users (username, password_hash, full_name, role)
                   VALUES (?, ?, ?, ?)""",
                (username, password_hash, full_name, role)
            )
            user_id = cursor.lastrowid

            return User(
                user_id=user_id,
                username=username,
                full_name=full_name,
                role=role,
                is_active=True
            )

    def list_users(self, include_inactive: bool = False) -> List[User]:
        """List all users."""
        with self.get_connection() as conn:
            if include_inactive:
                cursor = conn.execute("SELECT * FROM users ORDER BY username")
            else:
                cursor = conn.execute("SELECT * FROM users WHERE is_active = 1 ORDER BY username")

            return [
                User(
                    user_id=row['user_id'],
                    username=row['username'],
                    full_name=row['full_name'],
                    role=row['role'],
                    is_active=bool(row['is_active']),
                    created_at=row['created_at'],
                    last_login=row['last_login']
                )
                for row in cursor.fetchall()
            ]

    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user (soft delete)."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE users SET is_active = 0 WHERE user_id = ?",
                (user_id,)
            )
            return cursor.rowcount > 0

    # ============================================================
    # ELEMENT MANAGEMENT
    # ============================================================

    def get_element(self, element_id: int) -> Optional[Element]:
        """Get element by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM elements WHERE element_id = ?",
                (element_id,)
            )
            row = cursor.fetchone()
            if row:
                return Element(
                    element_id=row['element_id'],
                    element_code=row['element_code'],
                    element_name=row['element_name'],
                    category=row['category'],
                    price=row['price'] if 'price' in row.keys() else None,
                    created_at=row['created_at'],
                    created_by=row['created_by']
                )
            return None

    def get_element_by_code(self, element_code: str) -> Optional[Element]:
        """Get element by code."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM elements WHERE element_code = ?",
                (element_code,)
            )
            row = cursor.fetchone()
            if row:
                return Element(
                    element_id=row['element_id'],
                    element_code=row['element_code'],
                    element_name=row['element_name'],
                    category=row['category'],
                    price=row['price'] if 'price' in row.keys() else None,
                    created_at=row['created_at'],
                    created_by=row['created_by']
                )
            return None

    def list_elements(self) -> List[Element]:
        """List all elements."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM elements ORDER BY element_code")
            return [
                Element(
                    element_id=row['element_id'],
                    element_code=row['element_code'],
                    element_name=row['element_name'],
                    category=row['category'],
                    price=row['price'] if 'price' in row.keys() else None,
                    created_at=row['created_at'],
                    created_by=row['created_by']
                )
                for row in cursor.fetchall()
            ]

    def create_element(
        self,
        element_code: str,
        element_name: str,
        category: str,
        created_by: Optional[str] = None
    ) -> Element:
        """Create a new element."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO elements (element_code, element_name, category, created_by)
                   VALUES (?, ?, ?, ?)""",
                (element_code, element_name, category, created_by)
            )
            return Element(
                element_id=cursor.lastrowid,
                element_code=element_code,
                element_name=element_name,
                category=category,
                created_by=created_by
            )

    # ============================================================
    # VARIABLE MANAGEMENT
    # ============================================================

    def get_element_variables(self, element_id: int, include_options: bool = True) -> List[Variable]:
        """Get all variables for an element."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM element_variables
                   WHERE element_id = ?
                   ORDER BY display_order, variable_name""",
                (element_id,)
            )
            variables = []
            for row in cursor.fetchall():
                options = []
                if include_options:
                    options = self._get_variable_options(conn, row['variable_id'])

                variables.append(Variable(
                    variable_id=row['variable_id'],
                    element_id=row['element_id'],
                    variable_name=row['variable_name'],
                    variable_type=row['variable_type'],
                    unit=row['unit'],
                    default_value=row['default_value'],
                    is_required=bool(row['is_required']),
                    display_order=row['display_order'],
                    options=options
                ))
            return variables

    def _get_variable_options(self, conn, variable_id: int) -> List[VariableOption]:
        """Get options for a variable (internal method)."""
        cursor = conn.execute(
            """SELECT * FROM variable_options
               WHERE variable_id = ?
               ORDER BY display_order, option_value""",
            (variable_id,)
        )
        return [
            VariableOption(
                option_id=row['option_id'],
                variable_id=row['variable_id'],
                option_value=row['option_value'],
                display_order=row['display_order']
            )
            for row in cursor.fetchall()
        ]

    def get_variable_options(self, variable_id: int) -> List[VariableOption]:
        """Get options for a variable."""
        with self.get_connection() as conn:
            return self._get_variable_options(conn, variable_id)

    def add_variable(
        self,
        element_id: int,
        variable_name: str,
        variable_type: str,
        unit: Optional[str] = None,
        default_value: Optional[str] = None,
        is_required: bool = True,
        display_order: int = 0
    ) -> Variable:
        """Add a variable to an element."""
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
            return Variable(
                variable_id=cursor.lastrowid,
                element_id=element_id,
                variable_name=variable_name,
                variable_type=variable_type,
                unit=unit,
                default_value=default_value,
                is_required=is_required,
                display_order=display_order,
                options=[]
            )

    def add_variable_option(
        self,
        variable_id: int,
        option_value: str,
        display_order: int = 0
    ) -> VariableOption:
        """Add an option to a variable."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO variable_options (variable_id, option_value, display_order)
                   VALUES (?, ?, ?)""",
                (variable_id, option_value, display_order)
            )
            return VariableOption(
                option_id=cursor.lastrowid,
                variable_id=variable_id,
                option_value=option_value,
                display_order=display_order
            )

    # ============================================================
    # VERSION MANAGEMENT
    # ============================================================

    def get_version(self, version_id: int) -> Optional[DescriptionVersion]:
        """Get version by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM description_versions WHERE version_id = ?",
                (version_id,)
            )
            row = cursor.fetchone()
            if row:
                return DescriptionVersion(
                    version_id=row['version_id'],
                    element_id=row['element_id'],
                    description_template=row['description_template'],
                    state=row['state'],
                    is_active=bool(row['is_active']),
                    version_number=row['version_number'],
                    created_at=row['created_at'],
                    created_by=row['created_by'],
                    updated_at=row['updated_at']
                )
            return None

    def get_active_version(self, element_id: int) -> Optional[DescriptionVersion]:
        """Get the active version for an element."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM description_versions
                   WHERE element_id = ? AND is_active = 1""",
                (element_id,)
            )
            row = cursor.fetchone()
            if row:
                return DescriptionVersion(
                    version_id=row['version_id'],
                    element_id=row['element_id'],
                    description_template=row['description_template'],
                    state=row['state'],
                    is_active=bool(row['is_active']),
                    version_number=row['version_number'],
                    created_at=row['created_at'],
                    created_by=row['created_by'],
                    updated_at=row['updated_at']
                )
            return None

    def get_draft_versions(self, element_id: int) -> List[DescriptionVersion]:
        """Get all non-active versions (drafts) for an element."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM description_versions
                   WHERE element_id = ? AND is_active = 0
                   ORDER BY version_number DESC""",
                (element_id,)
            )
            return [
                DescriptionVersion(
                    version_id=row['version_id'],
                    element_id=row['element_id'],
                    description_template=row['description_template'],
                    state=row['state'],
                    is_active=bool(row['is_active']),
                    version_number=row['version_number'],
                    created_at=row['created_at'],
                    created_by=row['created_by'],
                    updated_at=row['updated_at']
                )
                for row in cursor.fetchall()
            ]

    def create_draft(
        self,
        element_id: int,
        description_template: str,
        created_by: Optional[str] = None
    ) -> DescriptionVersion:
        """Create a new draft version (S0 state)."""
        with self.get_connection() as conn:
            # Get next version number
            cursor = conn.execute(
                """SELECT COALESCE(MAX(version_number), 0) + 1
                   FROM description_versions WHERE element_id = ?""",
                (element_id,)
            )
            version_number = cursor.fetchone()[0]

            cursor = conn.execute(
                """INSERT INTO description_versions
                   (element_id, description_template, state, is_active, version_number, created_by)
                   VALUES (?, ?, 'S0', 0, ?, ?)""",
                (element_id, description_template, version_number, created_by)
            )

            return DescriptionVersion(
                version_id=cursor.lastrowid,
                element_id=element_id,
                description_template=description_template,
                state='S0',
                is_active=False,
                version_number=version_number,
                created_by=created_by
            )

    # ============================================================
    # ROLE-BASED VOTING SYSTEM
    # ============================================================

    def get_vote_status(self, version_id: int) -> VoteStatus:
        """
        Get the current vote status for a version.

        Returns:
            VoteStatus with editor_votes, admin_votes, and is_approved
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN approver_role = 'editor' THEN 1 ELSE 0 END), 0) as editor_votes,
                    COALESCE(SUM(CASE WHEN approver_role = 'admin' THEN 1 ELSE 0 END), 0) as admin_votes
                FROM approvals
                WHERE version_id = ?
            """, (version_id,))

            row = cursor.fetchone()
            editor_votes = row['editor_votes']
            admin_votes = row['admin_votes']
            is_approved = editor_votes >= 1 and admin_votes >= 1

            return VoteStatus(
                version_id=version_id,
                editor_votes=editor_votes,
                admin_votes=admin_votes,
                is_approved=is_approved
            )

    def can_user_vote(self, version_id: int, username: str, role: str) -> Tuple[bool, str]:
        """
        Check if a user can vote on a version.

        Args:
            version_id: The version to vote on
            username: The user's username
            role: The user's role

        Returns:
            Tuple of (can_vote, reason)
        """
        # Validate role parameter
        if role not in ('admin', 'editor', 'viewer'):
            return False, f"Rol invàlid: {role}"

        if role == 'viewer':
            return False, "Els viewers no tenen permís per votar."

        # Check version exists and is in valid state for voting
        version = self.get_version(version_id)
        if not version:
            return False, "Versió no trobada."
        if version.state != 'S0':
            return False, f"No es pot votar una versió en estat {version.state}. Només es pot votar en estat S0 (esborrany)."

        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT approval_id FROM approvals WHERE version_id = ? AND approved_by = ?",
                (version_id, username)
            )
            if cursor.fetchone():
                return False, "Ja has votat aquesta versió."

        return True, "OK"

    def vote_for_version(
        self,
        version_id: int,
        username: str,
        role: str
    ) -> Tuple[bool, str, Optional[VoteStatus]]:
        """
        Cast a vote for a version.

        Requires: 1 editor vote + 1 admin vote to approve.
        Viewers cannot vote.

        Args:
            version_id: The version to vote on
            username: The user's username
            role: The user's role (admin, editor, viewer)

        Returns:
            Tuple of (success, message, vote_status)
        """
        can_vote, reason = self.can_user_vote(version_id, username, role)
        if not can_vote:
            return False, reason, None

        with self.get_connection() as conn:
            # Insert vote
            conn.execute("""
                INSERT INTO approvals (version_id, from_state, to_state, approved_by, approver_role)
                VALUES (?, 'S0', 'S3', ?, ?)
            """, (version_id, username, role))

            # Get updated vote counts
            cursor = conn.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN approver_role = 'editor' THEN 1 ELSE 0 END), 0) as editor_votes,
                    COALESCE(SUM(CASE WHEN approver_role = 'admin' THEN 1 ELSE 0 END), 0) as admin_votes
                FROM approvals
                WHERE version_id = ?
            """, (version_id,))

            row = cursor.fetchone()
            editor_votes = row['editor_votes']
            admin_votes = row['admin_votes']

            vote_status = VoteStatus(
                version_id=version_id,
                editor_votes=editor_votes,
                admin_votes=admin_votes,
                is_approved=editor_votes >= 1 and admin_votes >= 1
            )

            # Check if approved (1 editor + 1 admin)
            if vote_status.is_approved:
                # Activate this version
                cursor = conn.execute(
                    "SELECT element_id FROM description_versions WHERE version_id = ?",
                    (version_id,)
                )
                element_id = cursor.fetchone()[0]

                # Deactivate old active version
                conn.execute(
                    "UPDATE description_versions SET is_active = 0 WHERE element_id = ?",
                    (element_id,)
                )

                # Activate new version
                conn.execute(
                    "UPDATE description_versions SET state = 'S3', is_active = 1 WHERE version_id = ?",
                    (version_id,)
                )

                message = "🎉 Aprovat! (1 editor + 1 admin). Aquesta versió ara és l'ACTIVA (S3)."
            else:
                message = f"✅ Vot registrat! 👷 Editors: {editor_votes}/1 | 👑 Admins: {admin_votes}/1"

            conn.commit()
            return True, message, vote_status

    def get_version_approvals(self, version_id: int) -> List[Approval]:
        """Get all approvals/votes for a version."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM approvals WHERE version_id = ? ORDER BY approved_at""",
                (version_id,)
            )
            return [
                Approval(
                    approval_id=row['approval_id'],
                    version_id=row['version_id'],
                    from_state=row['from_state'],
                    to_state=row['to_state'],
                    approved_by=row['approved_by'],
                    approver_role=row['approver_role'],
                    approved_at=row['approved_at'],
                    comments=row['comments']
                )
                for row in cursor.fetchall()
            ]

    # ============================================================
    # PROJECT MANAGEMENT
    # ============================================================

    def get_project(self, project_id: int) -> Optional[Project]:
        """Get project by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM projects WHERE project_id = ?",
                (project_id,)
            )
            row = cursor.fetchone()
            if row:
                return Project(
                    project_id=row['project_id'],
                    project_code=row['project_code'],
                    project_name=row['project_name'],
                    status=row['status'],
                    start_date=row['start_date'],
                    end_date=row['end_date'],
                    location=row['location'],
                    created_at=row['created_at'],
                    created_by=row['created_by']
                )
            return None

    def get_project_by_code(self, project_code: str) -> Optional[Project]:
        """Get project by code."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM projects WHERE project_code = ?",
                (project_code,)
            )
            row = cursor.fetchone()
            if row:
                return Project(
                    project_id=row['project_id'],
                    project_code=row['project_code'],
                    project_name=row['project_name'],
                    status=row['status'],
                    start_date=row['start_date'],
                    end_date=row['end_date'],
                    location=row['location'],
                    created_at=row['created_at'],
                    created_by=row['created_by']
                )
            return None

    def list_projects(self) -> List[Project]:
        """List all projects."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM projects ORDER BY project_code")
            return [
                Project(
                    project_id=row['project_id'],
                    project_code=row['project_code'],
                    project_name=row['project_name'],
                    status=row['status'],
                    start_date=row['start_date'],
                    end_date=row['end_date'],
                    location=row['location'],
                    created_at=row['created_at'],
                    created_by=row['created_by']
                )
                for row in cursor.fetchall()
            ]

    def create_project(
        self,
        project_code: str,
        project_name: str,
        status: str = 'PLANNING',
        location: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Project:
        """Create a new project."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO projects (project_code, project_name, status, location, created_by)
                   VALUES (?, ?, ?, ?, ?)""",
                (project_code, project_name, status, location, created_by)
            )
            return Project(
                project_id=cursor.lastrowid,
                project_code=project_code,
                project_name=project_name,
                status=status,
                location=location,
                created_by=created_by
            )

    # ============================================================
    # PROJECT ELEMENTS
    # ============================================================

    def get_project_elements(self, project_id: int) -> List[ProjectElement]:
        """Get all elements in a project."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM project_elements WHERE project_id = ? ORDER BY instance_code""",
                (project_id,)
            )
            elements = []
            for row in cursor.fetchall():
                # Get values for this element
                values = self._get_element_values(conn, row['project_element_id'])

                elements.append(ProjectElement(
                    project_element_id=row['project_element_id'],
                    project_id=row['project_id'],
                    element_id=row['element_id'],
                    description_version_id=row['description_version_id'],
                    instance_code=row['instance_code'],
                    instance_name=row['instance_name'],
                    location=row['location'],
                    created_at=row['created_at'],
                    created_by=row['created_by'],
                    values=values
                ))
            return elements

    def _get_element_values(self, conn, project_element_id: int) -> Dict[str, str]:
        """Get values for a project element (internal)."""
        cursor = conn.execute(
            """SELECT ev.variable_name, pev.value
               FROM project_element_values pev
               JOIN element_variables ev ON pev.variable_id = ev.variable_id
               WHERE pev.project_element_id = ?""",
            (project_element_id,)
        )
        return {row['variable_name']: row['value'] for row in cursor.fetchall()}

    def get_element_values(self, project_element_id: int) -> Dict[str, str]:
        """Get values for a project element."""
        with self.get_connection() as conn:
            return self._get_element_values(conn, project_element_id)

    def set_element_value(
        self,
        project_element_id: int,
        variable_id: int,
        value: str,
        updated_by: Optional[str] = None
    ):
        """Set a value for a project element variable."""
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO project_element_values
                   (project_element_id, variable_id, value, updated_by)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(project_element_id, variable_id)
                   DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP, updated_by = ?""",
                (project_element_id, variable_id, value, updated_by, value, updated_by)
            )

    # ============================================================
    # DESCRIPTION RENDERING
    # ============================================================

    def render_description(self, project_element_id: int) -> str:
        """
        Render a description for a project element.

        Replaces {placeholders} with actual values.
        """
        with self.get_connection() as conn:
            # Get template
            cursor = conn.execute(
                """SELECT dv.description_template
                   FROM project_elements pe
                   JOIN description_versions dv ON pe.description_version_id = dv.version_id
                   WHERE pe.project_element_id = ?""",
                (project_element_id,)
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Project element {project_element_id} not found")

            template = row['description_template']
            values = self._get_element_values(conn, project_element_id)

            # Replace placeholders
            def replace_placeholder(match):
                var_name = match.group(1)
                return values.get(var_name, f'[MISSING:{var_name}]')

            return re.sub(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', replace_placeholder, template)

    # ============================================================
    # UTILITY METHODS
    # ============================================================

    def extract_placeholders(self, template: str) -> List[str]:
        """Extract placeholder names from a template string."""
        pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
        return re.findall(pattern, template)

    # ============================================================
    # DATABASE INITIALIZATION
    # ============================================================

    @classmethod
    def initialize_database(
        cls,
        db_path: str = "office_data.db",
        schema_path: str = "schema.sql",
        seed_demo_data: bool = True
    ) -> 'DatabaseManager':
        """
        Initialize a fresh database with schema and optional demo data.

        This replaces the old gestor_db.py script.

        Args:
            db_path: Path to the database file
            schema_path: Path to the schema.sql file
            seed_demo_data: Whether to seed demo elements, projects, and users

        Returns:
            DatabaseManager instance connected to the new database

        Usage:
            python -c "from db_manager import DatabaseManager; DatabaseManager.initialize_database()"
        """
        # 1. Remove existing database
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"♻️  Base de dades anterior '{db_path}' eliminada.")

        # 2. Create new database with schema
        print("📜 Llegint schema.sql...")
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"❌ Error: No trobo el fitxer '{schema_path}'.")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        with open(schema_path, "r") as f:
            cursor.executescript(f.read())
        print("✅ Taules creades correctament.")

        if seed_demo_data:
            cls._seed_demo_data(cursor)

        conn.commit()
        conn.close()

        print("✅ BBDD Regenerada!")
        return cls(db_path)

    @classmethod
    def _seed_demo_data(cls, cursor):
        """Seed demo elements, projects, and users."""

        # ==============================================================================
        # ELEMENT 1: MURO CORTINA (ARQUITECTURA)
        # ==============================================================================
        cursor.execute(
            "INSERT INTO elements (element_code, element_name, category) VALUES (?, ?, ?)",
            ("MC-01", "Muro Cortina Vidrio", "ARQUITECTURA")
        )
        id_mc = cursor.lastrowid

        # Variables
        vars_mc = [
            (id_mc, "tipo_vidrio", "TEXT", None, "Templado"),
            (id_mc, "espesor_perfil", "NUMERIC", "mm", "50")
        ]
        cursor.executemany(
            "INSERT INTO element_variables (element_id, variable_name, variable_type, unit, default_value) VALUES (?, ?, ?, ?, ?)",
            vars_mc
        )

        cursor.execute(
            "SELECT variable_id FROM element_variables WHERE element_id=? AND variable_name='tipo_vidrio'",
            (id_mc,)
        )
        id_var_vidrio = cursor.fetchone()[0]

        # Options for tipo_vidrio
        opciones_vidrio = [
            (id_var_vidrio, "Templado", 0),
            (id_var_vidrio, "Laminado 4+4", 1),
            (id_var_vidrio, "Doble Bajo Emisivo", 2),
            (id_var_vidrio, "Control Solar", 3)
        ]
        cursor.executemany(
            "INSERT INTO variable_options (variable_id, option_value, display_order) VALUES (?, ?, ?)",
            opciones_vidrio
        )

        # Get variable IDs
        cursor.execute("SELECT variable_id, variable_name FROM element_variables WHERE element_id = ?", (id_mc,))
        dict_mc = {row[1]: row[0] for row in cursor.fetchall()}

        # Template (Active S3)
        txt_mc = "Muro cortina categoria Arquitectura amb vidre {tipo_vidrio} i perfil de {espesor_perfil} mm."
        cursor.execute(
            "INSERT INTO description_versions (element_id, description_template, state, is_active, version_number) VALUES (?, ?, 'S3', 1, 1)",
            (id_mc, txt_mc)
        )
        ver_mc = cursor.lastrowid

        # Mappings
        map_mc = [
            (ver_mc, dict_mc['tipo_vidrio'], '{tipo_vidrio}', 1),
            (ver_mc, dict_mc['espesor_perfil'], '{espesor_perfil}', 2)
        ]
        cursor.executemany(
            "INSERT INTO template_variable_mappings (version_id, variable_id, placeholder, position) VALUES (?, ?, ?, ?)",
            map_mc
        )

        # ==============================================================================
        # ELEMENT 2: PILAR (ESTRUCTURA)
        # ==============================================================================
        cursor.execute(
            "INSERT INTO elements (element_code, element_name, category) VALUES (?, ?, ?)",
            ("PIL-01", "Pilar Rectangular", "ESTRUCTURA")
        )
        id_pil = cursor.lastrowid

        vars_pil = [
            (id_pil, "resistencia_hormigon", "TEXT", None, "HA-25"),
            (id_pil, "recubrimiento", "NUMERIC", "mm", "30")
        ]
        cursor.executemany(
            "INSERT INTO element_variables (element_id, variable_name, variable_type, unit, default_value) VALUES (?, ?, ?, ?, ?)",
            vars_pil
        )

        cursor.execute("SELECT variable_id, variable_name FROM element_variables WHERE element_id = ?", (id_pil,))
        dict_pil = {row[1]: row[0] for row in cursor.fetchall()}

        txt_pil = "Pilar estructural de formigó {resistencia_hormigon} amb recobriment geomètric de {recubrimiento} mm."
        cursor.execute(
            "INSERT INTO description_versions (element_id, description_template, state, is_active, version_number) VALUES (?, ?, 'S3', 1, 1)",
            (id_pil, txt_pil)
        )
        ver_pil = cursor.lastrowid

        map_pil = [
            (ver_pil, dict_pil['resistencia_hormigon'], '{resistencia_hormigon}', 1),
            (ver_pil, dict_pil['recubrimiento'], '{recubrimiento}', 2)
        ]
        cursor.executemany(
            "INSERT INTO template_variable_mappings (version_id, variable_id, placeholder, position) VALUES (?, ?, ?, ?)",
            map_pil
        )

        # ==============================================================================
        # DEMO PROJECT
        # ==============================================================================
        cursor.execute(
            "INSERT INTO projects (project_code, project_name) VALUES (?, ?)",
            ("PROY-2025", "Torre Ejecutiva Norte")
        )
        id_proy = cursor.lastrowid

        # Project element instances
        cursor.execute(
            "INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name) VALUES (?, ?, ?, ?, ?)",
            (id_proy, id_mc, ver_mc, "FACH-SUR", "Fachada Principal")
        )
        id_inst_mc = cursor.lastrowid

        cursor.execute(
            "INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name) VALUES (?, ?, ?, ?, ?)",
            (id_proy, id_pil, ver_pil, "PIL-CEN", "Pilar Central 01")
        )
        id_inst_pil = cursor.lastrowid

        # Values
        vals = [
            (id_inst_mc, dict_mc['tipo_vidrio'], "Doble Bajo Emisivo"),
            (id_inst_mc, dict_mc['espesor_perfil'], "80"),
            (id_inst_pil, dict_pil['resistencia_hormigon'], "HA-30/F/20/IIa"),
            (id_inst_pil, dict_pil['recubrimiento'], "35")
        ]
        cursor.executemany(
            "INSERT INTO project_element_values (project_element_id, variable_id, value) VALUES (?, ?, ?)",
            vals
        )

        # Initialize rendered descriptions
        cursor.execute(
            "INSERT INTO rendered_descriptions (project_element_id, rendered_text, is_stale) VALUES (?, '', 1)",
            (id_inst_mc,)
        )
        cursor.execute(
            "INSERT INTO rendered_descriptions (project_element_id, rendered_text, is_stale) VALUES (?, '', 1)",
            (id_inst_pil,)
        )

        # ==============================================================================
        # USERS (PERMISSION SYSTEM)
        # ==============================================================================
        # Roles:
        # - viewer: Can only view, cannot vote
        # - editor: Can edit and vote (1 editor vote required)
        # - admin:  Can do everything and vote (1 admin vote required)
        # Approval: 1 editor + 1 admin vote
        # ==============================================================================
        print("🔐 Generant usuaris i encriptant contrasenyes...")

        def crear_usuari(username, password, full_name, role):
            # Store hash as string for SQLite TEXT column compatibility
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                (username, password_hash, full_name, role)
            )

        # Default users
        crear_usuari("admin", "1234", "Enginyer En Cap", "admin")
        crear_usuari("arq", "1234", "Arquitecte Projectista", "editor")
        crear_usuari("becari", "1234", "Becari en Pràctiques", "viewer")

        print("📋 Usuaris creats:")
        print("   👑 admin  (1234) - Admin: pot votar com a administrador")
        print("   👷 arq    (1234) - Editor: pot votar com a editor")
        print("   👁️  becari (1234) - Viewer: només lectura, no pot votar")
        print("🗳️ Per aprovar una versió cal: 1 vot d'editor + 1 vot d'admin")


# ============================================================
# CLI ENTRY POINT
# ============================================================

if __name__ == "__main__":
    DatabaseManager.initialize_database()
