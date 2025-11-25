"""
Comprehensive tests for DatabaseManager

Tests all CRUD operations, validation, and core functionality.
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


class TestElementManagement:
    """Tests for element management."""
    
    def test_create_element(self, temp_db):
        """Test creating an element."""
        element_id = temp_db.create_element(
            element_code='TEST_ELEM',
            element_name='Test Element',
            created_by='test_user'
        )
        assert element_id is not None
        assert element_id > 0
    
    def test_get_element(self, temp_db):
        """Test retrieving an element."""
        element_id = temp_db.create_element(
            element_code='TEST_ELEM',
            element_name='Test Element',
            created_by='test_user'
        )
        
        element = temp_db.get_element(element_id)
        assert element is not None
        assert element['element_code'] == 'TEST_ELEM'
        assert element['element_name'] == 'Test Element'
        assert element['created_by'] == 'test_user'
    
    def test_get_element_by_code(self, temp_db):
        """Test retrieving element by code."""
        temp_db.create_element(
            element_code='TEST_ELEM',
            element_name='Test Element',
            created_by='test_user'
        )
        
        element = temp_db.get_element_by_code('TEST_ELEM')
        assert element is not None
        assert element['element_code'] == 'TEST_ELEM'
    
    def test_list_elements(self, temp_db):
        """Test listing all elements."""
        temp_db.create_element('ELEM_1', 'Element 1', created_by='test')
        temp_db.create_element('ELEM_2', 'Element 2', created_by='test')
        
        elements = temp_db.list_elements()
        assert len(elements) == 2
        codes = [e['element_code'] for e in elements]
        assert 'ELEM_1' in codes
        assert 'ELEM_2' in codes
    
    def test_duplicate_element_code(self, temp_db):
        """Test that duplicate element codes are rejected."""
        temp_db.create_element('TEST_ELEM', 'Test Element', created_by='test')
        
        with pytest.raises(Exception):  # Should raise integrity error
            temp_db.create_element('TEST_ELEM', 'Another Element', created_by='test')


class TestVariableManagement:
    """Tests for variable management."""
    
    def test_add_variable(self, temp_db):
        """Test adding a variable to an element."""
        element_id = temp_db.create_element('TEST_ELEM', 'Test Element', created_by='test')
        
        variable_id = temp_db.add_variable(
            element_id=element_id,
            variable_name='width',
            variable_type='NUMERIC',
            unit='cm',
            is_required=True,
            display_order=1
        )
        assert variable_id is not None
        assert variable_id > 0
    
    def test_get_element_variables(self, temp_db):
        """Test retrieving variables for an element."""
        element_id = temp_db.create_element('TEST_ELEM', 'Test Element', created_by='test')
        
        temp_db.add_variable(element_id, 'width', 'NUMERIC', unit='cm', is_required=True)
        temp_db.add_variable(element_id, 'material', 'TEXT', is_required=True)
        
        variables = temp_db.get_element_variables(element_id)
        assert len(variables) == 2
        var_names = [v['variable_name'] for v in variables]
        assert 'width' in var_names
        assert 'material' in var_names
    
    def test_invalid_variable_type(self, temp_db):
        """Test that invalid variable types are rejected."""
        element_id = temp_db.create_element('TEST_ELEM', 'Test Element', created_by='test')
        
        with pytest.raises(ValueError):
            temp_db.add_variable(element_id, 'test', 'INVALID_TYPE')
    
    def test_duplicate_variable_name(self, temp_db):
        """Test that duplicate variable names are rejected."""
        element_id = temp_db.create_element('TEST_ELEM', 'Test Element', created_by='test')
        
        temp_db.add_variable(element_id, 'width', 'NUMERIC')
        
        with pytest.raises(Exception):  # Should raise integrity error
            temp_db.add_variable(element_id, 'width', 'TEXT')


class TestTemplateValidation:
    """Tests for template validation."""
    
    def test_extract_placeholders(self, temp_db):
        """Test extracting placeholders from template."""
        template = 'Element with {width} and {height} and {width} again'
        placeholders = temp_db.extract_placeholders(template)
        
        assert len(placeholders) == 2  # Should be unique
        assert 'width' in placeholders
        assert 'height' in placeholders
    
    def test_validate_template_valid(self, temp_db):
        """Test validating a valid template."""
        element_id = temp_db.create_element('TEST_ELEM', 'Test Element', created_by='test')
        temp_db.add_variable(element_id, 'width', 'NUMERIC', is_required=True)
        temp_db.add_variable(element_id, 'height', 'NUMERIC', is_required=True)
        
        template = 'Element {width} x {height}'
        result = temp_db.validate_template_placeholders(element_id, template)
        
        assert result['is_valid'] is True
        assert len(result['missing_variables']) == 0
        assert len(result['undefined_placeholders']) == 0
    
    def test_validate_template_missing_required(self, temp_db):
        """Test validating template with missing required variables."""
        element_id = temp_db.create_element('TEST_ELEM', 'Test Element', created_by='test')
        temp_db.add_variable(element_id, 'width', 'NUMERIC', is_required=True)
        temp_db.add_variable(element_id, 'height', 'NUMERIC', is_required=True)
        
        template = 'Element {width}'
        result = temp_db.validate_template_placeholders(element_id, template)
        
        assert result['is_valid'] is False
        assert 'height' in result['missing_variables']
    
    def test_validate_template_undefined_placeholder(self, temp_db):
        """Test validating template with undefined placeholders."""
        element_id = temp_db.create_element('TEST_ELEM', 'Test Element', created_by='test')
        temp_db.add_variable(element_id, 'width', 'NUMERIC', is_required=True)
        
        template = 'Element {width} x {unknown}'
        result = temp_db.validate_template_placeholders(element_id, template)
        
        assert result['is_valid'] is False
        assert 'unknown' in result['undefined_placeholders']


class TestVersionManagement:
    """Tests for version management."""
    
    def test_create_proposal(self, temp_db):
        """Test creating a description version proposal."""
        element_id = temp_db.create_element('TEST_ELEM', 'Test Element', created_by='test')
        temp_db.add_variable(element_id, 'width', 'NUMERIC', is_required=True)
        temp_db.add_variable(element_id, 'height', 'NUMERIC', is_required=True)
        
        version_id = temp_db.create_proposal(
            element_id=element_id,
            description_template='Element {width} x {height}',
            created_by='test_user'
        )
        
        assert version_id is not None
        assert version_id > 0
        
        version = temp_db.get_version(version_id)
        assert version is not None
        assert version['state'] == 'S0'
        assert version['is_active'] == 0
        assert version['version_number'] == 1
    
    def test_create_proposal_invalid_template(self, temp_db):
        """Test creating proposal with invalid template."""
        element_id = temp_db.create_element('TEST_ELEM', 'Test Element', created_by='test')
        temp_db.add_variable(element_id, 'width', 'NUMERIC', is_required=True)
        
        with pytest.raises(ValueError):
            temp_db.create_proposal(
                element_id=element_id,
                description_template='Element {width} x {unknown}',
                created_by='test_user'
            )
    
    def test_get_next_version_number(self, temp_db):
        """Test getting next version number."""
        element_id = temp_db.create_element('TEST_ELEM', 'Test Element', created_by='test')
        temp_db.add_variable(element_id, 'width', 'NUMERIC', is_required=True)
        
        # First version
        assert temp_db.get_next_version_number(element_id) == 1
        
        temp_db.create_proposal(element_id, 'Element {width}', 'test')
        
        # Second version
        assert temp_db.get_next_version_number(element_id) == 2
        
        temp_db.create_proposal(element_id, 'Element {width}', 'test')
        
        # Third version
        assert temp_db.get_next_version_number(element_id) == 3
    
    def test_get_active_version(self, temp_db):
        """Test getting active version."""
        element_id = temp_db.create_element('TEST_ELEM', 'Test Element', created_by='test')
        temp_db.add_variable(element_id, 'width', 'NUMERIC', is_required=True)
        
        # No active version initially
        assert temp_db.get_active_version(element_id) is None
        
        # Create and approve to S3
        version_id = temp_db.create_proposal(element_id, 'Element {width}', 'test')
        temp_db.approve_proposal(version_id, 'approver', 'S0->S1')
        temp_db.approve_proposal(version_id, 'approver', 'S1->S2')
        temp_db.approve_proposal(version_id, 'approver', 'S2->S3')
        
        active = temp_db.get_active_version(element_id)
        assert active is not None
        assert active['version_id'] == version_id
        assert active['is_active'] == 1


class TestProjectManagement:
    """Tests for project management."""
    
    def test_create_project(self, temp_db):
        """Test creating a project."""
        project_id = temp_db.create_project(
            project_code='PROJ_001',
            project_name='Test Project',
            status='PLANNING',
            created_by='test_user'
        )
        
        assert project_id is not None
        assert project_id > 0
    
    def test_get_project(self, temp_db):
        """Test retrieving a project."""
        project_id = temp_db.create_project(
            project_code='PROJ_001',
            project_name='Test Project',
            created_by='test_user'
        )
        
        project = temp_db.get_project(project_id)
        assert project is not None
        assert project['project_code'] == 'PROJ_001'
        assert project['project_name'] == 'Test Project'
    
    def test_get_project_by_code(self, temp_db):
        """Test retrieving project by code."""
        temp_db.create_project('PROJ_001', 'Test Project', created_by='test')
        
        project = temp_db.get_project_by_code('PROJ_001')
        assert project is not None
        assert project['project_code'] == 'PROJ_001'


class TestProjectElements:
    """Tests for project element instances."""
    
    def test_create_project_element(self, temp_db):
        """Test creating a project element instance."""
        # Setup
        element_id = temp_db.create_element('TEST_ELEM', 'Test Element', created_by='test')
        temp_db.add_variable(element_id, 'width', 'NUMERIC', is_required=True)
        
        version_id = temp_db.create_proposal(element_id, 'Element {width}', 'test')
        temp_db.approve_proposal(version_id, 'approver', 'S0->S1')
        temp_db.approve_proposal(version_id, 'approver', 'S1->S2')
        temp_db.approve_proposal(version_id, 'approver', 'S2->S3')
        
        project_id = temp_db.create_project('PROJ_001', 'Test Project', created_by='test')
        
        # Create project element
        project_element_id = temp_db.create_project_element(
            project_id=project_id,
            element_id=element_id,
            description_version_id=version_id,
            instance_code='INST_001',
            instance_name='Test Instance',
            created_by='test'
        )
        
        assert project_element_id is not None
        assert project_element_id > 0
    
    def test_set_element_value(self, temp_db):
        """Test setting element values."""
        # Setup
        element_id = temp_db.create_element('TEST_ELEM', 'Test Element', created_by='test')
        variable_id = temp_db.add_variable(element_id, 'width', 'NUMERIC', is_required=True)
        
        version_id = temp_db.create_proposal(element_id, 'Element {width}', 'test')
        temp_db.approve_proposal(version_id, 'approver', 'S0->S1')
        temp_db.approve_proposal(version_id, 'approver', 'S1->S2')
        temp_db.approve_proposal(version_id, 'approver', 'S2->S3')
        
        project_id = temp_db.create_project('PROJ_001', 'Test Project', created_by='test')
        project_element_id = temp_db.create_project_element(
            project_id, element_id, version_id, 'INST_001', created_by='test'
        )
        
        # Set value
        temp_db.set_element_value(project_element_id, variable_id, '50', 'test')
        
        values = temp_db.get_element_values(project_element_id)
        assert 'width' in values
        assert values['width'] == '50'
    
    def test_update_element_value(self, temp_db):
        """Test updating an existing element value."""
        # Setup
        element_id = temp_db.create_element('TEST_ELEM', 'Test Element', created_by='test')
        variable_id = temp_db.add_variable(element_id, 'width', 'NUMERIC', is_required=True)
        
        version_id = temp_db.create_proposal(element_id, 'Element {width}', 'test')
        temp_db.approve_proposal(version_id, 'approver', 'S0->S1')
        temp_db.approve_proposal(version_id, 'approver', 'S1->S2')
        temp_db.approve_proposal(version_id, 'approver', 'S2->S3')
        
        project_id = temp_db.create_project('PROJ_001', 'Test Project', created_by='test')
        project_element_id = temp_db.create_project_element(
            project_id, element_id, version_id, 'INST_001', created_by='test'
        )
        
        # Set initial value
        temp_db.set_element_value(project_element_id, variable_id, '50', 'test')
        
        # Update value
        temp_db.set_element_value(project_element_id, variable_id, '75', 'test')
        
        values = temp_db.get_element_values(project_element_id)
        assert values['width'] == '75'


class TestDescriptionRendering:
    """Tests for description rendering."""
    
    def test_render_description(self, temp_db):
        """Test rendering a description."""
        # Setup
        element_id = temp_db.create_element('TEST_ELEM', 'Test Element', created_by='test')
        variable_id = temp_db.add_variable(element_id, 'width', 'NUMERIC', is_required=True)
        temp_db.add_variable(element_id, 'height', 'NUMERIC', is_required=True)
        
        version_id = temp_db.create_proposal(
            element_id, 'Element {width} x {height}', 'test'
        )
        temp_db.approve_proposal(version_id, 'approver', 'S0->S1')
        temp_db.approve_proposal(version_id, 'approver', 'S1->S2')
        temp_db.approve_proposal(version_id, 'approver', 'S2->S3')
        
        project_id = temp_db.create_project('PROJ_001', 'Test Project', created_by='test')
        project_element_id = temp_db.create_project_element(
            project_id, element_id, version_id, 'INST_001', created_by='test'
        )
        
        # Set values
        temp_db.set_element_value(project_element_id, variable_id, '50', 'test')
        height_var = temp_db.get_element_variables(element_id)[1]
        temp_db.set_element_value(project_element_id, height_var['variable_id'], '100', 'test')
        
        # Render
        rendered = temp_db.render_description(project_element_id)
        assert '50' in rendered
        assert '100' in rendered
        assert 'Element' in rendered
    
    def test_upsert_rendered_description(self, temp_db):
        """Test storing rendered description."""
        # Setup
        element_id = temp_db.create_element('TEST_ELEM', 'Test Element', created_by='test')
        variable_id = temp_db.add_variable(element_id, 'width', 'NUMERIC', is_required=True)
        
        version_id = temp_db.create_proposal(element_id, 'Element {width}', 'test')
        temp_db.approve_proposal(version_id, 'approver', 'S0->S1')
        temp_db.approve_proposal(version_id, 'approver', 'S1->S2')
        temp_db.approve_proposal(version_id, 'approver', 'S2->S3')
        
        project_id = temp_db.create_project('PROJ_001', 'Test Project', created_by='test')
        project_element_id = temp_db.create_project_element(
            project_id, element_id, version_id, 'INST_001', created_by='test'
        )
        
        temp_db.set_element_value(project_element_id, variable_id, '50', 'test')
        
        # Upsert rendered description
        temp_db.upsert_rendered_description(project_element_id)
        
        rendered = temp_db.get_rendered_description(project_element_id)
        assert rendered is not None
        assert rendered['is_stale'] == 0
        assert '50' in rendered['rendered_text']

