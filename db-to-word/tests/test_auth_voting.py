#!/usr/bin/env python3
"""
Tests for authentication and role-based voting system.

Tests cover:
- User creation with bcrypt password hashing
- User authentication (login success/failure)
- Role-based voting permissions
- Version state validation for voting
- Approval workflow (1 editor + 1 admin to approve)
"""

import os
import sys
import tempfile
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_manager import DatabaseManager, User, VoteStatus


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    # Create schema file path
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema.sql')

    # Initialize database with demo data
    manager = DatabaseManager.initialize_database(
        db_path=db_path,
        schema_path=schema_path,
        seed_demo_data=True
    )

    yield manager

    # Cleanup
    os.unlink(db_path)


class TestUserAuthentication:
    """Tests for user authentication with bcrypt."""

    def test_authenticate_valid_user(self, db):
        """Test successful authentication with correct password."""
        user = db.authenticate_user('admin', '1234')
        assert user is not None
        assert user.username == 'admin'
        assert user.role == 'admin'

    def test_authenticate_invalid_password(self, db):
        """Test authentication fails with wrong password."""
        user = db.authenticate_user('admin', 'wrongpassword')
        assert user is None

    def test_authenticate_nonexistent_user(self, db):
        """Test authentication fails for non-existent user."""
        user = db.authenticate_user('nonexistent', 'password')
        assert user is None

    def test_authenticate_editor(self, db):
        """Test editor user authentication."""
        user = db.authenticate_user('arq', '1234')
        assert user is not None
        assert user.role == 'editor'

    def test_authenticate_viewer(self, db):
        """Test viewer user authentication."""
        user = db.authenticate_user('becari', '1234')
        assert user is not None
        assert user.role == 'viewer'


class TestUserCreation:
    """Tests for user creation."""

    def test_create_user_valid(self, db):
        """Test creating a new user."""
        user = db.create_user('newuser', 'password123', 'New User', 'editor')
        assert user is not None
        assert user.username == 'newuser'
        assert user.full_name == 'New User'
        assert user.role == 'editor'

    def test_create_user_duplicate_username(self, db):
        """Test that duplicate usernames are rejected."""
        with pytest.raises(ValueError, match="already exists"):
            db.create_user('admin', 'password', 'Another Admin', 'admin')

    def test_create_user_invalid_role(self, db):
        """Test that invalid roles are rejected."""
        with pytest.raises(ValueError, match="Invalid role"):
            db.create_user('testuser', 'password', 'Test', 'superuser')

    def test_created_user_can_authenticate(self, db):
        """Test that newly created user can authenticate."""
        db.create_user('newuser', 'mypassword', 'New User', 'editor')
        user = db.authenticate_user('newuser', 'mypassword')
        assert user is not None
        assert user.username == 'newuser'


class TestRoleBasedVoting:
    """Tests for role-based voting system."""

    def test_viewer_cannot_vote(self, db):
        """Test that viewers cannot vote."""
        # Get a draft version
        elements = db.list_elements()
        element = elements[0]
        draft = db.create_draft(element.element_id, "Test template {tipo_vidrio}", 'testuser')

        can_vote, reason = db.can_user_vote(draft.version_id, 'becari', 'viewer')
        assert can_vote is False
        assert "viewer" in reason.lower() or "permís" in reason.lower()

    def test_editor_can_vote(self, db):
        """Test that editors can vote on drafts."""
        elements = db.list_elements()
        element = elements[0]
        draft = db.create_draft(element.element_id, "Test template {tipo_vidrio}", 'testuser')

        can_vote, reason = db.can_user_vote(draft.version_id, 'arq', 'editor')
        assert can_vote is True

    def test_admin_can_vote(self, db):
        """Test that admins can vote on drafts."""
        elements = db.list_elements()
        element = elements[0]
        draft = db.create_draft(element.element_id, "Test template {tipo_vidrio}", 'testuser')

        can_vote, reason = db.can_user_vote(draft.version_id, 'admin', 'admin')
        assert can_vote is True

    def test_cannot_vote_twice(self, db):
        """Test that users cannot vote twice on the same version."""
        elements = db.list_elements()
        element = elements[0]
        draft = db.create_draft(element.element_id, "Test template {tipo_vidrio}", 'testuser')

        # First vote
        success, message, status = db.vote_for_version(draft.version_id, 'arq', 'editor')
        assert success is True

        # Second vote should fail
        can_vote, reason = db.can_user_vote(draft.version_id, 'arq', 'editor')
        assert can_vote is False
        assert "votat" in reason.lower()

    def test_invalid_role_rejected(self, db):
        """Test that invalid roles are rejected in voting."""
        elements = db.list_elements()
        element = elements[0]
        draft = db.create_draft(element.element_id, "Test template {tipo_vidrio}", 'testuser')

        can_vote, reason = db.can_user_vote(draft.version_id, 'user', 'superadmin')
        assert can_vote is False
        assert "invàlid" in reason.lower()


class TestVersionStateValidation:
    """Tests for version state validation before voting."""

    def test_cannot_vote_on_approved_version(self, db):
        """Test that voting on approved (S3) versions is rejected."""
        # Get an active (S3) version
        elements = db.list_elements()
        element = elements[0]
        active_version = db.get_active_version(element.element_id)

        assert active_version is not None
        assert active_version.state == 'S3'

        can_vote, reason = db.can_user_vote(active_version.version_id, 'arq', 'editor')
        assert can_vote is False
        assert "S3" in reason or "S0" in reason

    def test_can_vote_on_draft(self, db):
        """Test that voting on drafts (S0) is allowed."""
        elements = db.list_elements()
        element = elements[0]
        draft = db.create_draft(element.element_id, "Test template {tipo_vidrio}", 'testuser')

        assert draft.state == 'S0'

        can_vote, reason = db.can_user_vote(draft.version_id, 'arq', 'editor')
        assert can_vote is True

    def test_nonexistent_version(self, db):
        """Test that voting on non-existent versions is rejected."""
        can_vote, reason = db.can_user_vote(99999, 'arq', 'editor')
        assert can_vote is False
        assert "no trobada" in reason.lower() or "not found" in reason.lower()


class TestApprovalWorkflow:
    """Tests for the full approval workflow."""

    def test_single_editor_vote_not_approved(self, db):
        """Test that a single editor vote doesn't approve."""
        elements = db.list_elements()
        element = elements[0]
        draft = db.create_draft(element.element_id, "Test template {tipo_vidrio}", 'testuser')

        success, message, status = db.vote_for_version(draft.version_id, 'arq', 'editor')

        assert success is True
        assert status.editor_votes == 1
        assert status.admin_votes == 0
        assert status.is_approved is False

    def test_single_admin_vote_not_approved(self, db):
        """Test that a single admin vote doesn't approve."""
        elements = db.list_elements()
        element = elements[0]
        draft = db.create_draft(element.element_id, "Test template {tipo_vidrio}", 'testuser')

        success, message, status = db.vote_for_version(draft.version_id, 'admin', 'admin')

        assert success is True
        assert status.editor_votes == 0
        assert status.admin_votes == 1
        assert status.is_approved is False

    def test_editor_plus_admin_approves(self, db):
        """Test that 1 editor + 1 admin vote approves the version."""
        elements = db.list_elements()
        element = elements[0]
        draft = db.create_draft(element.element_id, "Test template {tipo_vidrio}", 'testuser')

        # Editor vote
        success1, msg1, status1 = db.vote_for_version(draft.version_id, 'arq', 'editor')
        assert success1 is True
        assert status1.is_approved is False

        # Admin vote
        success2, msg2, status2 = db.vote_for_version(draft.version_id, 'admin', 'admin')
        assert success2 is True
        assert status2.editor_votes == 1
        assert status2.admin_votes == 1
        assert status2.is_approved is True

        # Version should now be active
        updated_version = db.get_version(draft.version_id)
        assert updated_version.state == 'S3'
        assert updated_version.is_active is True

    def test_vote_status_properties(self, db):
        """Test VoteStatus helper properties."""
        status = VoteStatus(
            version_id=1,
            editor_votes=0,
            admin_votes=0,
            is_approved=False
        )

        assert status.needs_editor is True
        assert status.needs_admin is True

        status2 = VoteStatus(
            version_id=1,
            editor_votes=1,
            admin_votes=1,
            is_approved=True
        )

        assert status2.needs_editor is False
        assert status2.needs_admin is False


class TestDeactivateUser:
    """Tests for user deactivation."""

    def test_deactivate_user(self, db):
        """Test that deactivated users cannot authenticate."""
        # Create a user
        user = db.create_user('tempuser', 'password', 'Temp User', 'editor')

        # Verify can authenticate
        auth_user = db.authenticate_user('tempuser', 'password')
        assert auth_user is not None

        # Deactivate
        result = db.deactivate_user(user.user_id)
        assert result is True

        # Cannot authenticate anymore
        auth_user = db.authenticate_user('tempuser', 'password')
        assert auth_user is None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
