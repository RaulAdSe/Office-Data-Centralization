#!/usr/bin/env python3
"""
Office Database Manager - API for Variable System
Uses the real office_data.db with 75 existing elements
"""

import sqlite3
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Element:
    element_id: int
    element_code: str
    element_name: str
    price: Optional[float] = None

@dataclass
class Variable:
    variable_id: int
    variable_name: str
    variable_type: str
    unit: Optional[str] = None
    is_required: bool = True
    default_value: Optional[str] = None
    options: List[str] = None

@dataclass
class ProjectElement:
    project_element_id: int
    instance_code: str
    instance_name: str
    element_code: str
    values: Dict[str, str]
    rendered_description: Optional[str] = None

class OfficeDBManager:
    def __init__(self, db_path: str = "office_data.db"):
        self.db_path = db_path
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_all_elements(self) -> List[Element]:
        """Get all elements from the database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT element_id, element_code, element_name, price 
                FROM elements 
                ORDER BY element_code
            """)
            return [Element(*row) for row in cursor.fetchall()]
    
    def get_element_variables(self, element_id: int) -> List[Variable]:
        """Get all variables for an element with their options"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT variable_id, variable_name, variable_type, unit, is_required, default_value
                FROM element_variables
                WHERE element_id = ?
                ORDER BY display_order
            """, (element_id,))
            
            variables = []
            for row in cursor.fetchall():
                var_id = row[0]
                
                # Get options for this variable
                cursor.execute("""
                    SELECT option_value 
                    FROM variable_options 
                    WHERE variable_id = ? 
                    ORDER BY is_default DESC, option_value
                """, (var_id,))
                options = [opt[0] for opt in cursor.fetchall()]
                
                variables.append(Variable(*row, options=options if options else None))
                
            return variables
    
    def get_element_by_code(self, element_code: str) -> Optional[Element]:
        """Get element by code"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT element_id, element_code, element_name, price 
                FROM elements 
                WHERE element_code = ?
            """, (element_code,))
            row = cursor.fetchone()
            return Element(*row) if row else None
    
    def get_active_template(self, element_id: int) -> Optional[str]:
        """Get active description template for element"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT description_template 
                FROM description_versions 
                WHERE element_id = ? AND is_active = 1
            """, (element_id,))
            row = cursor.fetchone()
            return row[0] if row else None
    
    def create_project(self, project_code: str, project_name: str, location: str = None) -> int:
        """Create a new project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO projects (project_code, project_name, location, created_by)
                VALUES (?, ?, ?, ?)
            """, (project_code, project_name, location, 'api_user'))
            return cursor.lastrowid
    
    def add_project_element(self, project_id: int, element_code: str, 
                           instance_code: str, instance_name: str = None) -> int:
        """Add element to project"""
        element = self.get_element_by_code(element_code)
        if not element:
            raise ValueError(f"Element {element_code} not found")
        
        # Get active template version
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT version_id FROM description_versions 
                WHERE element_id = ? AND is_active = 1
            """, (element.element_id,))
            version_row = cursor.fetchone()
            if not version_row:
                raise ValueError(f"No active template for element {element_code}")
            
            cursor.execute("""
                INSERT INTO project_elements 
                (project_id, element_id, description_version_id, instance_code, instance_name, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (project_id, element.element_id, version_row[0], instance_code, instance_name, 'api_user'))
            return cursor.lastrowid
    
    def set_project_element_value(self, project_element_id: int, variable_name: str, value: str):
        """Set variable value for project element"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Get variable_id from variable name and project element
            cursor.execute("""
                SELECT ev.variable_id 
                FROM element_variables ev
                JOIN project_elements pe ON ev.element_id = pe.element_id
                WHERE pe.project_element_id = ? AND ev.variable_name = ?
            """, (project_element_id, variable_name))
            var_row = cursor.fetchone()
            if not var_row:
                raise ValueError(f"Variable {variable_name} not found for this element")
            
            # Insert or update value
            cursor.execute("""
                INSERT OR REPLACE INTO project_element_values 
                (project_element_id, variable_id, value, updated_by)
                VALUES (?, ?, ?, ?)
            """, (project_element_id, var_row[0], value, 'api_user'))
    
    def render_description(self, project_element_id: int) -> str:
        """Render description template with variable values"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get template
            cursor.execute("""
                SELECT dv.description_template
                FROM project_elements pe
                JOIN description_versions dv ON pe.description_version_id = dv.version_id
                WHERE pe.project_element_id = ?
            """, (project_element_id,))
            template_row = cursor.fetchone()
            if not template_row:
                return "Template not found"
            
            template = template_row[0]
            
            # Get all variable values
            cursor.execute("""
                SELECT ev.variable_name, pev.value
                FROM project_element_values pev
                JOIN element_variables ev ON pev.variable_id = ev.variable_id
                WHERE pev.project_element_id = ?
            """, (project_element_id,))
            
            values = dict(cursor.fetchall())
            
            # Get ALL available variables for this element (including unset ones)
            cursor.execute("""
                SELECT ev.variable_name, COALESCE(pev.value, ev.default_value, '') as value
                FROM element_variables ev
                LEFT JOIN project_element_values pev ON ev.variable_id = pev.variable_id 
                    AND pev.project_element_id = ?
                JOIN project_elements pe ON ev.element_id = pe.element_id
                WHERE pe.project_element_id = ?
            """, (project_element_id, project_element_id))
            
            all_values = dict(cursor.fetchall())
            values.update(all_values)  # Merge with existing values
            
            # Replace placeholders (enhanced regex to handle underscores and numbers)
            def replace_placeholder(match):
                var_name = match.group(1)
                # Try exact match first
                if var_name in values and values[var_name]:
                    return values[var_name]
                
                # Try without trailing numbers (sistema_encofrado_1 → sistema_encofrado)
                base_name = re.sub(r'_\d+$', '', var_name)
                if base_name in values and values[base_name]:
                    return values[base_name]
                
                # Try without trailing _1 specifically  
                if var_name.endswith('_1') and var_name[:-2] in values and values[var_name[:-2]]:
                    return values[var_name[:-2]]
                    
                return ""  # Remove placeholder if no value found
            
            rendered = re.sub(r'\{([^}]+)\}', replace_placeholder, template)
            
            # Store rendered description
            cursor.execute("""
                INSERT OR REPLACE INTO rendered_descriptions 
                (project_element_id, rendered_text, is_stale)
                VALUES (?, ?, 0)
            """, (project_element_id, rendered))
            
            return rendered
    
    def get_project_elements(self, project_id: int) -> List[ProjectElement]:
        """Get all project elements with their values"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get project elements
            cursor.execute("""
                SELECT pe.project_element_id, pe.instance_code, pe.instance_name, e.element_code
                FROM project_elements pe
                JOIN elements e ON pe.element_id = e.element_id
                WHERE pe.project_id = ?
                ORDER BY pe.instance_code
            """, (project_id,))
            
            elements = []
            for pe_id, instance_code, instance_name, element_code in cursor.fetchall():
                # Get values for this element
                cursor.execute("""
                    SELECT ev.variable_name, pev.value
                    FROM project_element_values pev
                    JOIN element_variables ev ON pev.variable_id = ev.variable_id
                    WHERE pev.project_element_id = ?
                """, (pe_id,))
                
                values = dict(cursor.fetchall())
                rendered = self.render_description(pe_id)
                
                elements.append(ProjectElement(
                    project_element_id=pe_id,
                    instance_code=instance_code,
                    instance_name=instance_name or "",
                    element_code=element_code,
                    values=values,
                    rendered_description=rendered
                ))
            
            return elements

def main():
    """Demo the API with real data"""
    db = OfficeDBManager()
    
    print("=== OFFICE DATABASE DEMO ===\n")
    
    # Show available elements
    print("Available Elements (first 10):")
    elements = db.get_all_elements()[:10]
    for elem in elements:
        print(f"  {elem.element_code}: {elem.element_name}")
    
    print(f"\nTotal elements in database: {len(db.get_all_elements())}")
    
    # Pick an element and show its variables
    test_element = elements[0]
    print(f"\nVariables for {test_element.element_code}:")
    variables = db.get_element_variables(test_element.element_id)
    for var in variables:
        print(f"  {var.variable_name} ({var.variable_type}) - Required: {var.is_required}")
    
    # Show template
    template = db.get_active_template(test_element.element_id)
    print(f"\nTemplate: {template[:100]}...")
    
    print("\n=== CREATING TEST PROJECT ===")
    
    # Create project with existing elements
    try:
        project_id = db.create_project("API-DEMO", "API Demo Project", "Demo Location")
        print(f"Created project: API-DEMO (ID: {project_id})")
        
        # Add element to project
        pe_id = db.add_project_element(project_id, test_element.element_code, "ELEM-001", "Test Element")
        print(f"Added element to project: {pe_id}")
        
        # Set variable values
        if variables:
            db.set_project_element_value(pe_id, variables[0].variable_name, "test_value_1")
            if len(variables) > 1:
                db.set_project_element_value(pe_id, variables[1].variable_name, "test_value_2")
        
        # Render description
        rendered = db.render_description(pe_id)
        print(f"\nRendered Description:\n{rendered}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()