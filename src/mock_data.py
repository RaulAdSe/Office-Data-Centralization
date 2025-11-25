"""
Mock Data Generator for Element Description System

Generates comprehensive test data including:
- Multiple element types with variables
- Description versions in various states
- Projects and project element instances
- Complete approval workflow examples
"""

import sys
from pathlib import Path

# Add src to path for imports
if Path(__file__).parent not in [Path(p) for p in sys.path]:
    sys.path.insert(0, str(Path(__file__).parent))

from db_manager import DatabaseManager
from typing import List, Dict, Any


class MockDataGenerator:
    """Generates mock data for testing and development."""
    
    def __init__(self, db_path: str = "test_elements.db"):
        """Initialize the mock data generator."""
        self.db = DatabaseManager(db_path)
    
    def generate_all(self):
        """Generate all mock data."""
        print("Generating mock data...")
        
        # Generate elements and variables
        elements = self.generate_elements()
        print(f"Generated {len(elements)} elements")
        
        # Generate description versions
        versions = self.generate_description_versions(elements)
        print(f"Generated {len(versions)} description versions")
        
        # Generate projects
        projects = self.generate_projects()
        print(f"Generated {len(projects)} projects")
        
        # Generate project elements
        project_elements = self.generate_project_elements(projects, elements, versions)
        print(f"Generated {len(project_elements)} project element instances")
        
        print("Mock data generation complete!")
        return {
            'elements': elements,
            'versions': versions,
            'projects': projects,
            'project_elements': project_elements
        }
    
    def generate_elements(self) -> List[Dict[str, Any]]:
        """Generate element types with their variables."""
        elements_data = [
            {
                'code': 'WALL',
                'name': 'Wall',
                'variables': [
                    {'name': 'thickness', 'type': 'NUMERIC', 'unit': 'cm', 'required': True, 'order': 1},
                    {'name': 'height', 'type': 'NUMERIC', 'unit': 'm', 'required': True, 'order': 2},
                    {'name': 'length', 'type': 'NUMERIC', 'unit': 'm', 'required': True, 'order': 3},
                    {'name': 'material', 'type': 'TEXT', 'required': True, 'order': 4},
                    {'name': 'finish', 'type': 'TEXT', 'required': False, 'order': 5},
                ]
            },
            {
                'code': 'COLUMN',
                'name': 'Column',
                'variables': [
                    {'name': 'width', 'type': 'NUMERIC', 'unit': 'cm', 'required': True, 'order': 1},
                    {'name': 'depth', 'type': 'NUMERIC', 'unit': 'cm', 'required': True, 'order': 2},
                    {'name': 'height', 'type': 'NUMERIC', 'unit': 'm', 'required': True, 'order': 3},
                    {'name': 'material', 'type': 'TEXT', 'required': True, 'order': 4},
                    {'name': 'reinforcement', 'type': 'TEXT', 'required': False, 'order': 5},
                ]
            },
            {
                'code': 'BEAM',
                'name': 'Beam',
                'variables': [
                    {'name': 'width', 'type': 'NUMERIC', 'unit': 'cm', 'required': True, 'order': 1},
                    {'name': 'height', 'type': 'NUMERIC', 'unit': 'cm', 'required': True, 'order': 2},
                    {'name': 'length', 'type': 'NUMERIC', 'unit': 'm', 'required': True, 'order': 3},
                    {'name': 'material', 'type': 'TEXT', 'required': True, 'order': 4},
                    {'name': 'load_capacity', 'type': 'NUMERIC', 'unit': 'kN/m', 'required': False, 'order': 5},
                ]
            },
            {
                'code': 'DOOR',
                'name': 'Door',
                'variables': [
                    {'name': 'width', 'type': 'NUMERIC', 'unit': 'cm', 'required': True, 'order': 1},
                    {'name': 'height', 'type': 'NUMERIC', 'unit': 'cm', 'required': True, 'order': 2},
                    {'name': 'material', 'type': 'TEXT', 'required': True, 'order': 3},
                    {'name': 'type', 'type': 'TEXT', 'required': True, 'order': 4},
                    {'name': 'fire_rating', 'type': 'TEXT', 'required': False, 'order': 5},
                ]
            },
            {
                'code': 'WINDOW',
                'name': 'Window',
                'variables': [
                    {'name': 'width', 'type': 'NUMERIC', 'unit': 'cm', 'required': True, 'order': 1},
                    {'name': 'height', 'type': 'NUMERIC', 'unit': 'cm', 'required': True, 'order': 2},
                    {'name': 'frame_material', 'type': 'TEXT', 'required': True, 'order': 3},
                    {'name': 'glazing_type', 'type': 'TEXT', 'required': True, 'order': 4},
                    {'name': 'u_value', 'type': 'NUMERIC', 'unit': 'W/m²K', 'required': False, 'order': 5},
                ]
            },
        ]
        
        created_elements = []
        for elem_data in elements_data:
            element_id = self.db.create_element(
                element_code=elem_data['code'],
                element_name=elem_data['name'],
                created_by='mock_generator'
            )
            
            # Add variables
            for var in elem_data['variables']:
                self.db.add_variable(
                    element_id=element_id,
                    variable_name=var['name'],
                    variable_type=var['type'],
                    unit=var.get('unit'),
                    is_required=var['required'],
                    display_order=var['order']
                )
            
            created_elements.append({
                'element_id': element_id,
                'code': elem_data['code'],
                'name': elem_data['name']
            })
        
        return created_elements
    
    def generate_description_versions(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate description versions in various states."""
        templates = {
            'WALL': [
                {
                    'template': 'Wall with thickness {thickness} cm, height {height} m, length {length} m, made of {material}.',
                    'state': 'S3',  # Active
                    'created_by': 'architect_1'
                },
                {
                    'template': 'Wall element: {thickness} cm thick, {height} m high, {length} m long, {material} material. Finish: {finish}.',
                    'state': 'S2',  # Pending final approval
                    'created_by': 'architect_2'
                },
            ],
            'COLUMN': [
                {
                    'template': 'Column {width} cm x {depth} cm, height {height} m, made of {material}.',
                    'state': 'S3',  # Active
                    'created_by': 'engineer_1'
                },
            ],
            'BEAM': [
                {
                    'template': 'Beam {width} cm x {height} cm, length {length} m, {material} material.',
                    'state': 'S3',  # Active
                    'created_by': 'engineer_1'
                },
                {
                    'template': 'Beam element: {width} cm x {height} cm cross-section, {length} m span, {material}. Load capacity: {load_capacity} kN/m.',
                    'state': 'S0',  # New proposal
                    'created_by': 'engineer_2'
                },
            ],
            'DOOR': [
                {
                    'template': 'Door {width} cm x {height} cm, {type} type, {material} material.',
                    'state': 'S3',  # Active
                    'created_by': 'architect_1'
                },
            ],
            'WINDOW': [
                {
                    'template': 'Window {width} cm x {height} cm, {frame_material} frame, {glazing_type} glazing.',
                    'state': 'S1',  # First approval
                    'created_by': 'architect_1'
                },
            ],
        }
        
        created_versions = []
        element_map = {e['code']: e['element_id'] for e in elements}
        
        for code, version_templates in templates.items():
            element_id = element_map.get(code)
            if not element_id:
                continue
            
            for template_data in version_templates:
                # Create proposal
                version_id = self.db.create_proposal(
                    element_id=element_id,
                    description_template=template_data['template'],
                    created_by=template_data['created_by']
                )
                
                # Move to target state
                target_state = template_data['state']
                current_state = 'S0'
                
                # Approve through states
                while current_state != target_state and current_state in ('S0', 'S1', 'S2'):
                    result = self.db.approve_proposal(
                        version_id=version_id,
                        approved_by=f'approver_{current_state}',
                        comments=f'Moving from {current_state} to {target_state}'
                    )
                    if result['success']:
                        current_state = result['new_state']
                    else:
                        break
                
                created_versions.append({
                    'version_id': version_id,
                    'element_id': element_id,
                    'element_code': code,
                    'state': current_state
                })
        
        return created_versions
    
    def generate_projects(self) -> List[Dict[str, Any]]:
        """Generate test projects."""
        projects_data = [
            {
                'code': 'PROJ_001',
                'name': 'Office Building A',
                'status': 'ACTIVE',
                'start_date': '2024-01-15',
                'end_date': '2024-12-31',
                'location': 'Madrid, Spain'
            },
            {
                'code': 'PROJ_002',
                'name': 'Residential Complex B',
                'status': 'PLANNING',
                'start_date': '2024-06-01',
                'end_date': '2025-06-30',
                'location': 'Barcelona, Spain'
            },
            {
                'code': 'PROJ_003',
                'name': 'Commercial Center C',
                'status': 'ACTIVE',
                'start_date': '2024-03-01',
                'end_date': None,
                'location': 'Valencia, Spain'
            },
        ]
        
        created_projects = []
        for proj_data in projects_data:
            project_id = self.db.create_project(
                project_code=proj_data['code'],
                project_name=proj_data['name'],
                status=proj_data['status'],
                start_date=proj_data['start_date'],
                end_date=proj_data.get('end_date'),
                location=proj_data['location'],
                created_by='project_manager'
            )
            created_projects.append({
                'project_id': project_id,
                'code': proj_data['code']
            })
        
        return created_projects
    
    def generate_project_elements(
        self,
        projects: List[Dict[str, Any]],
        elements: List[Dict[str, Any]],
        versions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate project element instances with values."""
        # Get active versions for each element
        active_versions = {}
        for version in versions:
            if version['state'] == 'S3':
                element_code = version['element_code']
                if element_code not in active_versions:
                    active_versions[element_code] = version['version_id']
        
        element_map = {e['code']: e['element_id'] for e in elements}
        project_map = {p['code']: p['project_id'] for p in projects}
        
        instances_data = [
            # Project 1 - Office Building A
            {
                'project_code': 'PROJ_001',
                'element_code': 'WALL',
                'instance_code': 'WALL_001',
                'instance_name': 'Exterior Wall North',
                'location': 'Level 1, North facade',
                'values': {
                    'thickness': '30',
                    'height': '3.5',
                    'length': '15.0',
                    'material': 'Reinforced concrete',
                    'finish': 'Brick cladding'
                }
            },
            {
                'project_code': 'PROJ_001',
                'element_code': 'COLUMN',
                'instance_code': 'COL_001',
                'instance_name': 'Column C1',
                'location': 'Level 1, Grid A-1',
                'values': {
                    'width': '40',
                    'depth': '40',
                    'height': '3.5',
                    'material': 'Reinforced concrete',
                    'reinforcement': '8xØ16mm'
                }
            },
            {
                'project_code': 'PROJ_001',
                'element_code': 'BEAM',
                'instance_code': 'BEAM_001',
                'instance_name': 'Main Beam B1',
                'location': 'Level 1, Span A-B',
                'values': {
                    'width': '30',
                    'height': '50',
                    'length': '6.0',
                    'material': 'Reinforced concrete',
                    'load_capacity': '25.5'
                }
            },
            {
                'project_code': 'PROJ_001',
                'element_code': 'DOOR',
                'instance_code': 'DOOR_001',
                'instance_name': 'Main Entrance Door',
                'location': 'Level 1, Main entrance',
                'values': {
                    'width': '120',
                    'height': '210',
                    'material': 'Aluminum',
                    'type': 'Sliding'
                }
            },
            # Project 2 - Residential Complex B
            {
                'project_code': 'PROJ_002',
                'element_code': 'WALL',
                'instance_code': 'WALL_002',
                'instance_name': 'Interior Partition',
                'location': 'Level 2, Unit 201',
                'values': {
                    'thickness': '15',
                    'height': '2.7',
                    'length': '4.5',
                    'material': 'Drywall',
                    'finish': 'Painted'
                }
            },
            {
                'project_code': 'PROJ_002',
                'element_code': 'WINDOW',
                'instance_code': 'WIN_001',
                'instance_name': 'Living Room Window',
                'location': 'Level 2, Unit 201, South facade',
                'values': {
                    'width': '150',
                    'height': '120',
                    'frame_material': 'PVC',
                    'glazing_type': 'Double glazing',
                    'u_value': '1.2'
                }
            },
        ]
        
        created_instances = []
        for inst_data in instances_data:
            project_id = project_map.get(inst_data['project_code'])
            element_id = element_map.get(inst_data['element_code'])
            version_id = active_versions.get(inst_data['element_code'])
            
            if not all([project_id, element_id, version_id]):
                continue
            
            # Create project element
            project_element_id = self.db.create_project_element(
                project_id=project_id,
                element_id=element_id,
                description_version_id=version_id,
                instance_code=inst_data['instance_code'],
                instance_name=inst_data['instance_name'],
                location=inst_data['location'],
                created_by='project_manager'
            )
            
            # Get variables for this element
            variables = self.db.get_element_variables(element_id)
            var_map = {v['variable_name']: v['variable_id'] for v in variables}
            
            # Set values
            for var_name, value in inst_data['values'].items():
                if var_name in var_map:
                    self.db.set_element_value(
                        project_element_id=project_element_id,
                        variable_id=var_map[var_name],
                        value=value,
                        updated_by='project_manager'
                    )
            
            # Render description
            self.db.upsert_rendered_description(project_element_id)
            
            created_instances.append({
                'project_element_id': project_element_id,
                'instance_code': inst_data['instance_code']
            })
        
        return created_instances


if __name__ == '__main__':
    generator = MockDataGenerator('test_elements.db')
    generator.generate_all()

