# Database Schema Documentation

## Overview

The Office Data Centralization system uses a SQLite database to manage parametric element descriptions with version control and approval workflows. The database consists of **9 tables** organized into logical groups.

## Database Structure

### 📐 Element Definitions

#### `elements`
Base element type definitions (e.g., Wall, Beam, Column).

- `element_id` (PK) - Unique identifier
- `element_code` (UK) - Unique code (e.g., 'WALL', 'BEAM')
- `element_name` - Display name
- `created_at`, `created_by` - Audit fields

#### `element_variables`
Variables/parameters for each element type (e.g., width, height, material).

- `variable_id` (PK) - Unique identifier
- `element_id` (FK) - References `elements`
- `variable_name` - Name of the variable
- `variable_type` - Type: 'TEXT', 'NUMERIC', or 'DATE'
- `unit` - Optional unit (e.g., 'cm', 'm', 'kg')
- `default_value` - Optional default value
- `is_required` - Whether variable is required
- `display_order` - Order for display

### 📝 Versioning & Workflow

#### `description_versions`
Versioned description templates with approval workflow states.

- `version_id` (PK) - Unique identifier
- `element_id` (FK) - References `elements`
- `description_template` - Template string with placeholders (e.g., "Wall {width} x {height}")
- `state` - Workflow state: 'S0' (draft), 'S1' (first approval), 'S2' (second approval), 'S3' (active), 'D' (rejected)
- `is_active` - Boolean flag (only S3 versions can be active)
- `version_number` - Sequential version number per element
- `created_at`, `created_by`, `updated_at` - Audit fields

**Workflow States:**
- **S0** → Initial proposal (draft)
- **S1** → First approval
- **S2** → Second approval
- **S3** → Final approval (becomes active)
- **D** → Rejected/deleted

#### `template_variable_mappings` ⭐
Explicit mappings between placeholders in templates and element variables.

- `mapping_id` (PK) - Unique identifier
- `version_id` (FK) - References `description_versions`
- `variable_id` (FK) - References `element_variables`
- `placeholder` - Placeholder name from template (e.g., 'width', 'height')
- `position` - Order of appearance in template (1, 2, 3...)
- `created_at` - Timestamp

**Purpose:** Ensures reliable placeholder replacement during rendering by maintaining explicit relationships between template placeholders and database variables.

#### `approvals`
Approval history tracking all state transitions.

- `approval_id` (PK) - Unique identifier
- `version_id` (FK) - References `description_versions`
- `from_state` - Previous state
- `to_state` - New state
- `approved_by` - User who approved/rejected
- `approved_at` - Timestamp
- `comments` - Optional comments

### 🏗️ Projects

#### `projects`
Project definitions.

- `project_id` (PK) - Unique identifier
- `project_code` (UK) - Unique project code
- `project_name` - Project name
- `status` - Status: 'PLANNING', 'ACTIVE', 'COMPLETED', 'CANCELLED'
- `start_date`, `end_date` - Project dates
- `location` - Project location
- `created_at`, `created_by` - Audit fields

### 📦 Project Instances

#### `project_elements`
Element instances within projects (concrete elements in a specific project).

- `project_element_id` (PK) - Unique identifier
- `project_id` (FK) - References `projects`
- `element_id` (FK) - References `elements`
- `description_version_id` (FK) 🔒 - References `description_versions` (version lock)
- `instance_code` (UK per project) - Unique instance code
- `instance_name` - Optional name
- `location` - Physical location
- `created_at`, `created_by` - Audit fields

**Version Lock:** Once a project element is created, it's locked to a specific description version, ensuring consistency even if the element's active version changes.

#### `project_element_values`
Actual values for element instance variables.

- `value_id` (PK) - Unique identifier
- `project_element_id` (FK) - References `project_elements`
- `variable_id` (FK) - References `element_variables`
- `value` - The actual value (stored as TEXT)
- `updated_at`, `updated_by` - Audit fields

### ⚙️ Rendering & Output

#### `rendered_descriptions`
Cached rendered descriptions for performance.

- `render_id` (PK) - Unique identifier
- `project_element_id` (FK, UK) - References `project_elements` (one-to-one)
- `rendered_text` - Final rendered description
- `is_stale` - Flag indicating if rendered text needs regeneration
- `rendered_at` - Timestamp of last render

**Stale Flag:** Automatically set to `true` when values change (via triggers), indicating the cached description needs regeneration.

## Relationships

```
elements
  ├── element_variables (1:N)
  └── description_versions (1:N)
       ├── template_variable_mappings (1:N) ⭐
       ├── approvals (1:N)
       └── project_elements (1:N) [version lock]
            ├── project_element_values (1:N)
            └── rendered_descriptions (1:1)

projects
  └── project_elements (1:N)
```

## Key Features

### 1. **Version Control**
- Multiple description versions per element
- Sequential version numbering
- Only one active version per element at a time

### 2. **Approval Workflow**
- Multi-stage approval process (S0 → S1 → S2 → S3)
- Complete audit trail of all approvals/rejections
- Cannot approve from invalid states

### 3. **Template Variable Mappings** ⭐
- Explicit mapping between placeholders and variables
- Position tracking for placeholder order
- Ensures reliable rendering

### 4. **Version Locking**
- Project elements are locked to specific description versions
- Ensures consistency even when active versions change
- Prevents breaking changes to existing project data

### 5. **Cached Rendering**
- Rendered descriptions are cached for performance
- Automatic stale flag management via triggers
- Efficient regeneration when needed

## Views

### `v_active_descriptions`
Shows all elements with their active description versions.

### `v_pending_proposals`
Lists all proposals pending approval (S0, S1, S2 states).

### `v_project_elements_rendered`
Complete view of project elements with their rendered descriptions.

### `v_element_variables_simple`
Simple view of all element variables.

### `v_template_variable_mappings`
View showing all template mappings with variable details.

## Indexes

The database includes indexes on:
- Foreign key columns for join performance
- State columns for workflow queries
- Unique constraint columns

## Data Flow

1. **Element Creation:** Create element type → Add variables
2. **Template Creation:** Create proposal with template → Mappings created automatically
3. **Approval:** Approve through workflow (S0 → S1 → S2 → S3)
4. **Project Use:** Create project → Create element instances → Set values
5. **Rendering:** System uses mappings to replace placeholders with values → Cache result

## Constraints

- **Unique Constraints:** Element codes, project codes, instance codes (per project)
- **Check Constraints:** State values, variable types, active state rules
- **Foreign Keys:** All relationships enforced with CASCADE/RESTRICT as appropriate
- **Version Lock:** Project elements cannot change their locked version

## Migration

The database automatically handles migration for existing databases:
- Detects if `template_variable_mappings` table exists
- Creates table and indexes if missing
- Backfills mappings for existing description versions
- Creates view if missing

## Example Usage

```python
from db_manager import DatabaseManager

db = DatabaseManager('elements.db')

# Create element
element_id = db.create_element('WALL', 'Wall', created_by='architect')
db.add_variable(element_id, 'width', 'NUMERIC', unit='cm', is_required=True)
db.add_variable(element_id, 'height', 'NUMERIC', unit='m', is_required=True)

# Create proposal (mappings created automatically)
version_id = db.create_proposal(
    element_id, 
    'Wall {width} cm x {height} m',
    created_by='architect'
)

# Approve through workflow
db.approve_proposal(version_id, 'reviewer1', 'S0->S1')
db.approve_proposal(version_id, 'reviewer2', 'S1->S2')
db.approve_proposal(version_id, 'reviewer3', 'S2->S3')  # Now active

# Use in project
project_id = db.create_project('PROJ_001', 'Building A', created_by='pm')
project_element_id = db.create_project_element(
    project_id, element_id, version_id, 'WALL_001', created_by='pm'
)

# Set values
variables = db.get_element_variables(element_id)
width_var = next(v for v in variables if v['variable_name'] == 'width')
height_var = next(v for v in variables if v['variable_name'] == 'height')

db.set_element_value(project_element_id, width_var['variable_id'], '30', 'pm')
db.set_element_value(project_element_id, height_var['variable_id'], '3.5', 'pm')

# Render (uses mappings automatically)
rendered = db.render_description(project_element_id)
# Result: "Wall 30 cm x 3.5 m"
```

## See Also

- `src/schema.sql` - Complete SQL schema definition
- `diagrams/complete_database_diagram.svg` - Visual database diagram
- `src/db_manager.py` - Database manager implementation
- `src/README.md` - Usage guide

