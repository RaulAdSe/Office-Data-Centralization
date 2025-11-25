"""
Comprehensive tests for the approval workflow

Tests the complete approval workflow:
- Creating proposals (S0)
- Approving through states (S0 -> S1 -> S2 -> S3)
- Rejecting proposals
- Multiple versions per element
- Active version management
- Approval history
"""

import pytest
import os
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from db_manager import DatabaseManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    db = DatabaseManager(path)
    yield db
    os.unlink(path)


@pytest.fixture
def test_element(temp_db):
    """Create a test element with variables."""
    element_id = temp_db.create_element(
        element_code='TEST_ELEM',
        element_name='Test Element',
        created_by='test_creator'
    )
    
    # Add required variables
    temp_db.add_variable(element_id, 'width', 'NUMERIC', unit='cm', is_required=True, display_order=1)
    temp_db.add_variable(element_id, 'height', 'NUMERIC', unit='cm', is_required=True, display_order=2)
    temp_db.add_variable(element_id, 'material', 'TEXT', is_required=True, display_order=3)
    temp_db.add_variable(element_id, 'finish', 'TEXT', is_required=False, display_order=4)
    
    return element_id


class TestProposalCreation:
    """Tests for creating proposals."""
    
    def test_create_proposal_initial_state(self, temp_db, test_element):
        """Test that new proposals start in S0 state."""
        version_id = temp_db.create_proposal(
            element_id=test_element,
            description_template='Element {width} x {height}, {material}',
            created_by='architect_1'
        )
        
        version = temp_db.get_version(version_id)
        assert version['state'] == 'S0'
        assert version['is_active'] == 0
        assert version['version_number'] == 1
        assert version['created_by'] == 'architect_1'
    
    def test_create_multiple_proposals(self, temp_db, test_element):
        """Test creating multiple proposals for the same element."""
        # First proposal
        v1 = temp_db.create_proposal(
            test_element, 'Element {width} x {height}', 'architect_1'
        )
        assert temp_db.get_version(v1)['version_number'] == 1
        
        # Second proposal
        v2 = temp_db.create_proposal(
            test_element, 'Element {width} x {height}, {material}', 'architect_2'
        )
        assert temp_db.get_version(v2)['version_number'] == 2
        
        # Third proposal
        v3 = temp_db.create_proposal(
            test_element, 'Element {width} x {height}, {material}, finish: {finish}', 'architect_3'
        )
        assert temp_db.get_version(v3)['version_number'] == 3
    
    def test_create_proposal_invalid_template(self, temp_db, test_element):
        """Test that invalid templates are rejected."""
        # Missing required variable
        with pytest.raises(ValueError, match='missing required'):
            temp_db.create_proposal(
                test_element, 'Element {width}', 'architect_1'
            )
        
        # Undefined placeholder
        with pytest.raises(ValueError, match='undefined placeholders'):
            temp_db.create_proposal(
                test_element, 'Element {width} x {height} x {unknown}', 'architect_1'
            )


class TestApprovalWorkflow:
    """Tests for the approval workflow state transitions."""
    
    def test_approve_s0_to_s1(self, temp_db, test_element):
        """Test approving from S0 to S1."""
        version_id = temp_db.create_proposal(
            test_element, 'Element {width} x {height}, {material}', 'architect_1'
        )
        
        result = temp_db.approve_proposal(
            version_id=version_id,
            approved_by='reviewer_1',
            comments='Initial review approved'
        )
        
        assert result['success'] is True
        assert result['new_state'] == 'S1'
        assert result['message'] == 'Approved'
        
        version = temp_db.get_version(version_id)
        assert version['state'] == 'S1'
        assert version['is_active'] == 0
    
    def test_approve_s1_to_s2(self, temp_db, test_element):
        """Test approving from S1 to S2."""
        version_id = temp_db.create_proposal(
            test_element, 'Element {width} x {height}, {material}', 'architect_1'
        )
        
        # Approve to S1
        temp_db.approve_proposal(version_id, 'reviewer_1', 'S0->S1')
        
        # Approve to S2
        result = temp_db.approve_proposal(
            version_id=version_id,
            approved_by='reviewer_2',
            comments='Second review approved'
        )
        
        assert result['success'] is True
        assert result['new_state'] == 'S2'
        
        version = temp_db.get_version(version_id)
        assert version['state'] == 'S2'
        assert version['is_active'] == 0
    
    def test_approve_s2_to_s3(self, temp_db, test_element):
        """Test approving from S2 to S3 (becomes active)."""
        version_id = temp_db.create_proposal(
            test_element, 'Element {width} x {height}, {material}', 'architect_1'
        )
        
        # Approve through all states
        temp_db.approve_proposal(version_id, 'reviewer_1', 'S0->S1')
        temp_db.approve_proposal(version_id, 'reviewer_2', 'S1->S2')
        
        # Final approval to S3
        result = temp_db.approve_proposal(
            version_id=version_id,
            approved_by='reviewer_3',
            comments='Final approval'
        )
        
        assert result['success'] is True
        assert result['new_state'] == 'S3'
        
        version = temp_db.get_version(version_id)
        assert version['state'] == 'S3'
        assert version['is_active'] == 1
    
    def test_approve_invalid_state(self, temp_db, test_element):
        """Test that approving from invalid states fails."""
        version_id = temp_db.create_proposal(
            test_element, 'Element {width} x {height}, {material}', 'architect_1'
        )
        
        # Approve to S3
        temp_db.approve_proposal(version_id, 'reviewer_1', 'S0->S1')
        temp_db.approve_proposal(version_id, 'reviewer_2', 'S1->S2')
        temp_db.approve_proposal(version_id, 'reviewer_3', 'S2->S3')
        
        # Try to approve from S3 (should fail)
        result = temp_db.approve_proposal(version_id, 'reviewer_4', 'S3->?')
        assert result['success'] is False
        assert 'Cannot approve from state' in result['message']
    
    def test_complete_workflow(self, temp_db, test_element):
        """Test complete workflow from proposal to active."""
        version_id = temp_db.create_proposal(
            test_element, 'Element {width} x {height}, {material}', 'architect_1'
        )
        
        # Verify initial state
        version = temp_db.get_version(version_id)
        assert version['state'] == 'S0'
        assert version['is_active'] == 0
        
        # Step 1: S0 -> S1
        result1 = temp_db.approve_proposal(version_id, 'reviewer_1', 'First approval')
        assert result1['success'] is True
        assert result1['new_state'] == 'S1'
        
        # Step 2: S1 -> S2
        result2 = temp_db.approve_proposal(version_id, 'reviewer_2', 'Second approval')
        assert result2['success'] is True
        assert result2['new_state'] == 'S2'
        
        # Step 3: S2 -> S3 (becomes active)
        result3 = temp_db.approve_proposal(version_id, 'reviewer_3', 'Final approval')
        assert result3['success'] is True
        assert result3['new_state'] == 'S3'
        
        # Verify final state
        version = temp_db.get_version(version_id)
        assert version['state'] == 'S3'
        assert version['is_active'] == 1
        
        # Verify it's the active version
        active = temp_db.get_active_version(test_element)
        assert active is not None
        assert active['version_id'] == version_id


class TestActiveVersionManagement:
    """Tests for managing active versions."""
    
    def test_only_one_active_version(self, temp_db, test_element):
        """Test that only one version can be active at a time."""
        # Create and activate first version
        v1 = temp_db.create_proposal(
            test_element, 'Element {width} x {height}', 'architect_1'
        )
        temp_db.approve_proposal(v1, 'r1', 'S0->S1')
        temp_db.approve_proposal(v1, 'r2', 'S1->S2')
        temp_db.approve_proposal(v1, 'r3', 'S2->S3')
        
        # Verify v1 is active
        active = temp_db.get_active_version(test_element)
        assert active['version_id'] == v1
        
        # Create and activate second version
        v2 = temp_db.create_proposal(
            test_element, 'Element {width} x {height}, {material}', 'architect_2'
        )
        temp_db.approve_proposal(v2, 'r1', 'S0->S1')
        temp_db.approve_proposal(v2, 'r2', 'S1->S2')
        temp_db.approve_proposal(v2, 'r3', 'S2->S3')
        
        # Verify v2 is now active and v1 is not
        active = temp_db.get_active_version(test_element)
        assert active['version_id'] == v2
        
        v1_version = temp_db.get_version(v1)
        assert v1_version['is_active'] == 0
    
    def test_multiple_versions_different_states(self, temp_db, test_element):
        """Test having multiple versions in different states."""
        # Version 1: Active (S3)
        v1 = temp_db.create_proposal(test_element, 'Element {width} x {height}', 'architect_1')
        temp_db.approve_proposal(v1, 'r1', 'S0->S1')
        temp_db.approve_proposal(v1, 'r2', 'S1->S2')
        temp_db.approve_proposal(v1, 'r3', 'S2->S3')
        
        # Version 2: Pending (S2)
        v2 = temp_db.create_proposal(test_element, 'Element {width} x {height}, {material}', 'architect_2')
        temp_db.approve_proposal(v2, 'r1', 'S0->S1')
        temp_db.approve_proposal(v2, 'r2', 'S1->S2')
        
        # Version 3: Pending (S0)
        v3 = temp_db.create_proposal(test_element, 'Element {width} x {height}, {material}, finish: {finish}', 'architect_3')
        
        # Verify states
        assert temp_db.get_version(v1)['state'] == 'S3'
        assert temp_db.get_version(v1)['is_active'] == 1
        assert temp_db.get_version(v2)['state'] == 'S2'
        assert temp_db.get_version(v2)['is_active'] == 0
        assert temp_db.get_version(v3)['state'] == 'S0'
        assert temp_db.get_version(v3)['is_active'] == 0
        
        # Verify active version
        active = temp_db.get_active_version(test_element)
        assert active['version_id'] == v1


class TestRejectionWorkflow:
    """Tests for rejecting proposals."""
    
    def test_reject_proposal(self, temp_db, test_element):
        """Test rejecting a proposal."""
        version_id = temp_db.create_proposal(
            test_element, 'Element {width} x {height}, {material}', 'architect_1'
        )
        
        # Reject the proposal
        result = temp_db.reject_proposal(
            version_id=version_id,
            rejected_by='reviewer_1',
            reason='Template does not meet requirements'
        )
        
        assert result is True
        
        version = temp_db.get_version(version_id)
        assert version['state'] == 'D'
    
    def test_reject_from_different_states(self, temp_db, test_element):
        """Test rejecting proposals from different states."""
        # Reject from S0
        v1 = temp_db.create_proposal(test_element, 'Element {width} x {height}, {material}', 'architect_1')
        temp_db.reject_proposal(v1, 'reviewer', 'Rejected from S0')
        assert temp_db.get_version(v1)['state'] == 'D'
        
        # Reject from S1
        v2 = temp_db.create_proposal(test_element, 'Element {width} x {height}, {material}', 'architect_2')
        temp_db.approve_proposal(v2, 'reviewer', 'S0->S1')
        temp_db.reject_proposal(v2, 'reviewer', 'Rejected from S1')
        assert temp_db.get_version(v2)['state'] == 'D'
        
        # Reject from S2
        v3 = temp_db.create_proposal(test_element, 'Element {width} x {height}, {material}', 'architect_3')
        temp_db.approve_proposal(v3, 'reviewer', 'S0->S1')
        temp_db.approve_proposal(v3, 'reviewer', 'S1->S2')
        temp_db.reject_proposal(v3, 'reviewer', 'Rejected from S2')
        assert temp_db.get_version(v3)['state'] == 'D'
    
    def test_cannot_reject_active_version(self, temp_db, test_element):
        """Test that active versions (S3) cannot be rejected."""
        version_id = temp_db.create_proposal(
            test_element, 'Element {width} x {height}, {material}', 'architect_1'
        )
        
        # Approve to S3
        temp_db.approve_proposal(version_id, 'r1', 'S0->S1')
        temp_db.approve_proposal(version_id, 'r2', 'S1->S2')
        temp_db.approve_proposal(version_id, 'r3', 'S2->S3')
        
        # Try to reject (should fail)
        with pytest.raises(ValueError, match='Cannot reject version in state'):
            temp_db.reject_proposal(version_id, 'reviewer', 'Trying to reject active version')
    
    def test_cannot_reject_already_rejected(self, temp_db, test_element):
        """Test that already rejected versions cannot be rejected again."""
        version_id = temp_db.create_proposal(
            test_element, 'Element {width} x {height}, {material}', 'architect_1'
        )
        
        # Reject once
        temp_db.reject_proposal(version_id, 'reviewer', 'First rejection')
        
        # Try to reject again (should fail)
        with pytest.raises(ValueError, match='Cannot reject version in state'):
            temp_db.reject_proposal(version_id, 'reviewer', 'Second rejection')


class TestApprovalHistory:
    """Tests for approval history tracking."""
    
    def test_approval_records_created(self, temp_db, test_element):
        """Test that approval records are created."""
        version_id = temp_db.create_proposal(
            test_element, 'Element {width} x {height}, {material}', 'architect_1'
        )
        
        # Approve through all states
        temp_db.approve_proposal(version_id, 'reviewer_1', 'S0->S1')
        temp_db.approve_proposal(version_id, 'reviewer_2', 'S1->S2')
        temp_db.approve_proposal(version_id, 'reviewer_3', 'S2->S3')
        
        # Check approval records
        with temp_db.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM approvals WHERE version_id = ? ORDER BY approved_at""",
                (version_id,)
            )
            approvals = [dict(row) for row in cursor.fetchall()]
        
        assert len(approvals) == 3
        
        # Check first approval
        assert approvals[0]['from_state'] == 'S0'
        assert approvals[0]['to_state'] == 'S1'
        assert approvals[0]['approved_by'] == 'reviewer_1'
        
        # Check second approval
        assert approvals[1]['from_state'] == 'S1'
        assert approvals[1]['to_state'] == 'S2'
        assert approvals[1]['approved_by'] == 'reviewer_2'
        
        # Check third approval
        assert approvals[2]['from_state'] == 'S2'
        assert approvals[2]['to_state'] == 'S3'
        assert approvals[2]['approved_by'] == 'reviewer_3'
    
    def test_rejection_record_created(self, temp_db, test_element):
        """Test that rejection records are created."""
        version_id = temp_db.create_proposal(
            test_element, 'Element {width} x {height}, {material}', 'architect_1'
        )
        
        temp_db.approve_proposal(version_id, 'reviewer', 'S0->S1')
        
        # Reject
        temp_db.reject_proposal(version_id, 'reviewer_2', 'Rejection reason')
        
        # Check rejection record
        with temp_db.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM approvals WHERE version_id = ? ORDER BY approved_at""",
                (version_id,)
            )
            approvals = [dict(row) for row in cursor.fetchall()]
        
        assert len(approvals) == 2
        assert approvals[1]['from_state'] == 'S1'
        assert approvals[1]['to_state'] == 'D'
        assert approvals[1]['approved_by'] == 'reviewer_2'
        assert 'Rejection reason' in approvals[1]['comments']


class TestPendingProposals:
    """Tests for pending proposals view."""
    
    def test_get_pending_proposals(self, temp_db, test_element):
        """Test getting pending proposals."""
        # Create proposals in different states
        v1 = temp_db.create_proposal(test_element, 'Element {width} x {height}', 'architect_1')
        v2 = temp_db.create_proposal(test_element, 'Element {width} x {height}, {material}', 'architect_2')
        v3 = temp_db.create_proposal(test_element, 'Element {width} x {height}, {material}, {finish}', 'architect_3')
        
        # Move some through workflow
        temp_db.approve_proposal(v1, 'r1', 'S0->S1')
        temp_db.approve_proposal(v1, 'r2', 'S1->S2')
        temp_db.approve_proposal(v1, 'r3', 'S2->S3')  # Not pending anymore
        
        temp_db.approve_proposal(v2, 'r1', 'S0->S1')
        
        # v3 is still in S0
        
        # Get pending proposals
        pending = temp_db.get_pending_proposals()
        
        # Should have v2 (S1) and v3 (S0), but not v1 (S3)
        pending_ids = [p['version_id'] for p in pending]
        assert v2 in pending_ids
        assert v3 in pending_ids
        assert v1 not in pending_ids


class TestComplexWorkflowScenarios:
    """Tests for complex workflow scenarios."""
    
    def test_replace_active_version(self, temp_db, test_element):
        """Test replacing an active version with a new one."""
        # Create and activate first version
        v1 = temp_db.create_proposal(test_element, 'Element {width} x {height}', 'architect_1')
        temp_db.approve_proposal(v1, 'r1', 'S0->S1')
        temp_db.approve_proposal(v1, 'r2', 'S1->S2')
        temp_db.approve_proposal(v1, 'r3', 'S2->S3')
        
        assert temp_db.get_active_version(test_element)['version_id'] == v1
        
        # Create and activate second version
        v2 = temp_db.create_proposal(test_element, 'Element {width} x {height}, {material}', 'architect_2')
        temp_db.approve_proposal(v2, 'r1', 'S0->S1')
        temp_db.approve_proposal(v2, 'r2', 'S1->S2')
        temp_db.approve_proposal(v2, 'r3', 'S2->S3')
        
        # v2 should now be active, v1 should be inactive
        assert temp_db.get_active_version(test_element)['version_id'] == v2
        assert temp_db.get_version(v1)['is_active'] == 0
    
    def test_multiple_elements_independent_workflows(self, temp_db):
        """Test that workflows for different elements are independent."""
        # Create two elements
        elem1 = temp_db.create_element('ELEM_1', 'Element 1', created_by='test')
        temp_db.add_variable(elem1, 'width', 'NUMERIC', is_required=True)
        
        elem2 = temp_db.create_element('ELEM_2', 'Element 2', created_by='test')
        temp_db.add_variable(elem2, 'height', 'NUMERIC', is_required=True)
        
        # Create and activate version for elem1
        v1 = temp_db.create_proposal(elem1, 'Element {width}', 'architect')
        temp_db.approve_proposal(v1, 'r1', 'S0->S1')
        temp_db.approve_proposal(v1, 'r2', 'S1->S2')
        temp_db.approve_proposal(v1, 'r3', 'S2->S3')
        
        # Create version for elem2 (still in S0)
        v2 = temp_db.create_proposal(elem2, 'Element {height}', 'architect')
        
        # Verify independent states
        assert temp_db.get_version(v1)['state'] == 'S3'
        assert temp_db.get_version(v1)['is_active'] == 1
        assert temp_db.get_version(v2)['state'] == 'S0'
        assert temp_db.get_version(v2)['is_active'] == 0
        
        # Verify active versions
        assert temp_db.get_active_version(elem1)['version_id'] == v1
        assert temp_db.get_active_version(elem2) is None

