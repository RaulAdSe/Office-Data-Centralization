"""
Example usage of the DatabaseManager

This script demonstrates how to use the database manager for:
- Creating elements and variables
- Creating and approving description versions
- Creating projects and project elements
- Rendering descriptions
"""

from db_manager import DatabaseManager


def main():
    """Example usage of the database manager."""
    # Initialize database
    db = DatabaseManager('example_elements.db')
    
    print("=== Creating Element ===")
    # Create an element
    element_id = db.create_element(
        element_code='WALL',
        element_name='Wall',
        category='ESTRUCTURA PREFABRICADA',
        created_by='architect_1'
    )
    print(f"Created element with ID: {element_id}")
    
    # Add variables
    print("\n=== Adding Variables ===")
    db.add_variable(element_id, 'thickness', 'NUMERIC', unit='cm', is_required=True, display_order=1)
    db.add_variable(element_id, 'height', 'NUMERIC', unit='m', is_required=True, display_order=2)
    
    # Add material variable with dropdown options
    material_options = [
        {'option_value': 'concrete', 'option_label': 'Reinforced Concrete', 'display_order': 1, 'is_default': True},
        {'option_value': 'brick', 'option_label': 'Brick', 'display_order': 2},
        {'option_value': 'steel', 'option_label': 'Steel Frame', 'display_order': 3},
        {'option_value': 'wood', 'option_label': 'Wood', 'display_order': 4}
    ]
    db.add_variable(
        element_id, 
        'material', 
        'TEXT', 
        is_required=True, 
        display_order=3,
        options=material_options
    )
    
    # Add finish variable with dropdown options
    finish_options = [
        {'option_value': 'painted', 'option_label': 'Painted', 'display_order': 1, 'is_default': True},
        {'option_value': 'brick_cladding', 'option_label': 'Brick Cladding', 'display_order': 2},
        {'option_value': 'stone_cladding', 'option_label': 'Stone Cladding', 'display_order': 3},
        {'option_value': 'plaster', 'option_label': 'Plaster', 'display_order': 4}
    ]
    db.add_variable(
        element_id, 
        'finish', 
        'TEXT', 
        is_required=False, 
        display_order=4,
        options=finish_options
    )
    print("Added variables: thickness (numeric), height (numeric), material (dropdown), finish (dropdown)")
    
    # Create description version proposal
    print("\n=== Creating Description Proposal ===")
    version_id = db.create_proposal(
        element_id=element_id,
        description_template='Wall with thickness {thickness} cm, height {height} m, made of {material}.',
        created_by='architect_1'
    )
    print(f"Created proposal with version_id: {version_id}, state: S0")
    
    # Approve through workflow
    print("\n=== Approval Workflow ===")
    result = db.approve_proposal(version_id, 'reviewer_1', 'First approval')
    print(f"S0 -> S1: {result['message']}")
    
    result = db.approve_proposal(version_id, 'reviewer_2', 'Second approval')
    print(f"S1 -> S2: {result['message']}")
    
    result = db.approve_proposal(version_id, 'reviewer_3', 'Final approval')
    print(f"S2 -> S3: {result['message']}")
    print(f"Version is now active!")
    
    # Create project
    print("\n=== Creating Project ===")
    project_id = db.create_project(
        project_code='PROJ_001',
        project_name='Office Building A',
        status='ACTIVE',
        location='Madrid, Spain',
        created_by='project_manager'
    )
    print(f"Created project with ID: {project_id}")
    
    # Create project element instance
    print("\n=== Creating Project Element Instance ===")
    project_element_id = db.create_project_element(
        project_id=project_id,
        element_id=element_id,
        description_version_id=version_id,
        instance_code='WALL_001',
        instance_name='Exterior Wall North',
        location='Level 1, North facade',
        created_by='project_manager'
    )
    print(f"Created project element with ID: {project_element_id}")
    
    # Set values
    print("\n=== Setting Values ===")
    variables = db.get_element_variables(element_id, include_options=True)
    var_map = {v['variable_name']: v['variable_id'] for v in variables}
    
    db.set_element_value(project_element_id, var_map['thickness'], '30', 'project_manager')
    db.set_element_value(project_element_id, var_map['height'], '3.5', 'project_manager')
    # Use option values for dropdown variables
    db.set_element_value(project_element_id, var_map['material'], 'concrete', 'project_manager')
    db.set_element_value(project_element_id, var_map['finish'], 'brick_cladding', 'project_manager')
    print("Set values: thickness=30, height=3.5, material=concrete, finish=brick_cladding")
    
    # Show variable options
    print("\n=== Variable Options ===")
    for var in variables:
        if var['options']:
            print(f"\n{var['variable_name']} (dropdown):")
            for opt in var['options']:
                default_marker = " [DEFAULT]" if opt['is_default'] else ""
                print(f"  - {opt['option_value']}: {opt['option_label']}{default_marker}")
        else:
            print(f"{var['variable_name']}: free input ({var['variable_type']})")
    
    # Render description
    print("\n=== Rendering Description ===")
    rendered = db.render_description(project_element_id)
    print(f"Rendered description:\n{rendered}")
    
    # Store rendered description
    db.upsert_rendered_description(project_element_id)
    print("\nRendered description stored in database")
    
    print("\n=== Example Complete ===")
    print("Database file: example_elements.db")


if __name__ == '__main__':
    main()

