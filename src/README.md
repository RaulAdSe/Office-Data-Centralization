# Database Manager for Element Description System

This module provides a complete SQLite-based database manager for the parametric element description system.

## Files

- `schema.sql` - SQLite database schema
- `db_manager.py` - Main database manager class with all CRUD operations
- `mock_data.py` - Mock data generator for testing
- `example_usage.py` - Example script demonstrating usage

## Quick Start

### Basic Usage

```python
from db_manager import DatabaseManager

# Initialize database (creates schema if needed)
db = DatabaseManager('elements.db')

# Create an element
element_id = db.create_element(
    element_code='WALL',
    element_name='Wall',
    created_by='architect'
)

# Add variables
db.add_variable(element_id, 'thickness', 'NUMERIC', unit='cm', is_required=True)
db.add_variable(element_id, 'material', 'TEXT', is_required=True)

# Create description proposal
version_id = db.create_proposal(
    element_id=element_id,
    description_template='Wall {thickness} cm, {material}',
    created_by='architect'
)

# Approve through workflow
db.approve_proposal(version_id, 'reviewer_1', 'S0->S1')
db.approve_proposal(version_id, 'reviewer_2', 'S1->S2')
db.approve_proposal(version_id, 'reviewer_3', 'S2->S3')  # Becomes active
```

### Approval Workflow

The approval workflow has the following states:
- **S0** - Initial proposal (draft)
- **S1** - First approval
- **S2** - Second approval
- **S3** - Final approval (active version)
- **D** - Rejected/deleted

State transitions:
- S0 → S1 → S2 → S3 (via approvals)
- S0/S1/S2 → D (via rejection)

Only one version per element can be active (S3) at a time.

### Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_approval_workflow.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Generating Mock Data

```bash
cd src
python mock_data.py
```

This creates `test_elements.db` with sample data including:
- 5 element types (Wall, Column, Beam, Door, Window)
- Multiple description versions in various states
- 3 projects
- Project element instances with values

## Key Features

- **Element Management**: Create and manage element types with variables
- **Template Validation**: Validates description templates against element variables
- **Version Control**: Track multiple versions of descriptions per element
- **Approval Workflow**: Multi-stage approval process (S0 → S1 → S2 → S3)
- **Active Version Management**: Only one active version per element
- **Project Management**: Create projects and element instances
- **Description Rendering**: Render descriptions by replacing placeholders with values
- **Approval History**: Track all approval and rejection actions

## Database Schema

The schema includes:
- `elements` - Element type definitions
- `element_variables` - Variables for each element type
- `description_versions` - Versioned description templates
- `approvals` - Approval history
- `projects` - Project definitions
- `project_elements` - Element instances in projects
- `project_element_values` - Values for element instances
- `rendered_descriptions` - Cached rendered descriptions

See `schema.sql` for complete schema definition.


