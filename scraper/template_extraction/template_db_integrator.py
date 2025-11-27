#!/usr/bin/env python3
"""
Integrate extracted templates into the database using proper schema
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from db_manager import DatabaseManager
from template_extractor import ExtractedTemplate

@dataclass
class TemplateMappingResult:
    """Result of template integration into database"""
    version_id: int
    element_id: int
    template: str
    mappings_created: List[Dict]
    variables_matched: List[str]
    variables_not_matched: List[str]

class TemplateDbIntegrator:
    """Integrates extracted templates into the database schema"""
    
    def __init__(self, db_path: str):
        """
        Args:
            db_path: Path to the SQLite database
        """
        self.db = DatabaseManager(db_path)
    
    def integrate_template(self, template: ExtractedTemplate, 
                          element_id: int = None) -> TemplateMappingResult:
        """
        Integrate extracted template into database
        
        Args:
            template: Extracted template from template extraction system
            element_id: Optional existing element ID, will lookup by code if not provided
            
        Returns:
            TemplateMappingResult with integration details
        """
        print(f"\\nIntegrating template for element: {template.element_code}")
        print(f"Template: {template.description_template}")
        
        # Step 1: Get or verify element
        if element_id is None:
            element = self.db.get_element_by_code(template.element_code)
            if not element:
                print(f"❌ Element {template.element_code} not found in database")
                return None
            element_id = element['element_id']
        
        print(f"Using element_id: {element_id}")
        
        # Step 2: Get existing variables for this element
        existing_vars = self.db.get_element_variables(element_id)
        var_lookup = {var['variable_name']: var['variable_id'] for var in existing_vars}
        
        print(f"Found {len(existing_vars)} existing variables: {list(var_lookup.keys())}")
        
        # Step 3: Parse template to find placeholders and their positions
        placeholders = self._extract_placeholders_with_positions(template.description_template)
        print(f"Found {len(placeholders)} placeholders: {[p['name'] for p in placeholders]}")
        
        # Step 4: Match template variables to existing database variables
        matched_mappings = []
        not_matched = []
        
        for placeholder in placeholders:
            var_name = placeholder['name']
            
            # Try exact match first
            if var_name in var_lookup:
                matched_mappings.append({
                    'variable_id': var_lookup[var_name],
                    'variable_name': var_name,
                    'placeholder': placeholder['placeholder'],
                    'position': placeholder['position']
                })
            else:
                # Try fuzzy matching
                matched_var = self._find_matching_variable(var_name, var_lookup)
                if matched_var:
                    print(f"  Fuzzy match: {var_name} -> {matched_var}")
                    matched_mappings.append({
                        'variable_id': var_lookup[matched_var],
                        'variable_name': matched_var,
                        'placeholder': placeholder['placeholder'],
                        'position': placeholder['position']
                    })
                else:
                    not_matched.append(var_name)
                    print(f"  ❌ No match for variable: {var_name}")
        
        if not matched_mappings:
            print("❌ No variables could be matched to existing database variables")
            return None
        
        # Step 5: Create description version
        version_id = self._create_description_version(element_id, template)
        
        # Step 6: Create template variable mappings
        self._create_variable_mappings(version_id, matched_mappings)
        
        result = TemplateMappingResult(
            version_id=version_id,
            element_id=element_id,
            template=template.description_template,
            mappings_created=matched_mappings,
            variables_matched=[m['variable_name'] for m in matched_mappings],
            variables_not_matched=not_matched
        )
        
        print(f"✅ Template integrated successfully!")
        print(f"   Version ID: {version_id}")
        print(f"   Mappings created: {len(matched_mappings)}")
        print(f"   Variables matched: {result.variables_matched}")
        if result.variables_not_matched:
            print(f"   Variables not matched: {result.variables_not_matched}")
        
        return result
    
    def _extract_placeholders_with_positions(self, template: str) -> List[Dict]:
        """
        Extract placeholders from template with their positions
        
        Args:
            template: Template string like "Muro de {material} de {width}×{height}"
            
        Returns:
            List of dicts with placeholder info
        """
        placeholders = []
        position = 1
        
        # Find all {variable} patterns
        pattern = r'\{([^}]+)\}'
        
        for match in re.finditer(pattern, template):
            placeholder_text = match.group(0)  # e.g., "{material}"
            variable_name = match.group(1)     # e.g., "material"
            
            placeholders.append({
                'name': variable_name,
                'placeholder': placeholder_text,
                'position': position,
                'start_index': match.start(),
                'end_index': match.end()
            })
            
            position += 1
        
        return placeholders
    
    def _find_matching_variable(self, template_var: str, var_lookup: Dict[str, int]) -> Optional[str]:
        """
        Find matching variable using fuzzy matching
        
        Args:
            template_var: Variable name from template
            var_lookup: Dict of existing variable names -> variable_ids
            
        Returns:
            Matching variable name or None
        """
        template_var_lower = template_var.lower()
        
        # Common Spanish-English mappings for CYPE variables
        translation_mappings = {
            'material': ['material', 'tipo_material', 'material_type'],
            'ubicacion': ['location', 'ubicacion', 'placement'],
            'resistencia': ['resistance', 'resistencia', 'strength'],
            'espesor': ['thickness', 'espesor', 'width'],
            'diametro': ['diameter', 'diametro', 'size'],
            'acabado': ['finish', 'acabado', 'surface'],
            'longitud': ['length', 'longitud', 'largo'],
            'ancho': ['width', 'ancho', 'anchura'],
            'alto': ['height', 'alto', 'altura'],
            'peso': ['weight', 'peso'],
            'color': ['color', 'colour'],
        }
        
        # Check direct translations
        for spanish_term, english_variants in translation_mappings.items():
            if template_var_lower in english_variants or template_var_lower == spanish_term:
                for db_var in var_lookup.keys():
                    db_var_lower = db_var.lower()
                    if db_var_lower in english_variants or db_var_lower == spanish_term:
                        return db_var
        
        # Check substring matches
        for db_var in var_lookup.keys():
            db_var_lower = db_var.lower()
            
            # Check if template variable is contained in db variable name
            if template_var_lower in db_var_lower or db_var_lower in template_var_lower:
                # Only match if significant overlap (avoid matching "a" with "acabado")
                min_length = min(len(template_var_lower), len(db_var_lower))
                if min_length >= 3:
                    return db_var
        
        return None
    
    def _create_description_version(self, element_id: int, template: ExtractedTemplate) -> int:
        """Create description version in database"""
        
        # Determine state based on confidence
        if template.confidence >= 0.9:
            state = 'S3'  # Approved
        elif template.confidence >= 0.7:
            state = 'S2'  # Under Review
        else:
            state = 'S1'  # Draft
        
        # Get next version number
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT COALESCE(MAX(version_number), 0) + 1
                FROM description_versions 
                WHERE element_id = ?
            """, (element_id,))
            
            version_number = cursor.fetchone()[0]
            
            # Create description version (without notes column)
            cursor = conn.execute("""
                INSERT INTO description_versions (
                    element_id, description_template, state, is_active, 
                    version_number, created_by
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                element_id,
                template.description_template,
                state,
                0,  # Not active by default
                version_number,
                'template_extractor'
            ))
            
            version_id = cursor.lastrowid
            conn.commit()
        
        return version_id
    
    def _create_variable_mappings(self, version_id: int, mappings: List[Dict]):
        """Create template variable mappings"""
        
        with self.db.get_connection() as conn:
            for mapping in mappings:
                conn.execute("""
                    INSERT INTO template_variable_mappings (
                        version_id, variable_id, placeholder, position
                    ) VALUES (?, ?, ?, ?)
                """, (
                    version_id,
                    mapping['variable_id'],
                    mapping['placeholder'],
                    mapping['position']
                ))
            
            conn.commit()
            print(f"Created {len(mappings)} variable mappings")
    
    def get_template_info(self, version_id: int) -> Dict:
        """Get complete template information"""
        
        with self.db.get_connection() as conn:
            # Get template with mappings
            cursor = conn.execute("""
                SELECT 
                    dv.version_id,
                    dv.element_id,
                    dv.description_template,
                    dv.state,
                    dv.version_number,
                    e.element_code,
                    e.element_name
                FROM description_versions dv
                JOIN elements e ON dv.element_id = e.element_id
                WHERE dv.version_id = ?
            """, (version_id,))
            
            template_info = cursor.fetchone()
            if not template_info:
                return None
            
            # Get mappings
            cursor = conn.execute("""
                SELECT 
                    tvm.mapping_id,
                    tvm.placeholder,
                    tvm.position,
                    tvm.variable_id,
                    ev.variable_name,
                    ev.variable_type,
                    ev.unit,
                    ev.is_required
                FROM template_variable_mappings tvm
                JOIN element_variables ev ON tvm.variable_id = ev.variable_id
                WHERE tvm.version_id = ?
                ORDER BY tvm.position
            """, (version_id,))
            
            mappings = cursor.fetchall()
        
        return {
            'version_id': template_info[0],
            'element_id': template_info[1], 
            'description_template': template_info[2],
            'state': template_info[3],
            'version_number': template_info[4],
            'element_code': template_info[5],
            'element_name': template_info[6],
            'mappings': [dict(mapping) for mapping in mappings]
        }

def test_template_integration():
    """Test template integration with mock data"""
    
    # First, create a simple test database with an element and variables
    db = DatabaseManager("test_template_integration.db")
    
    # Create test element
    element_id = db.create_element(
        element_code="WALL001",
        element_name="Muro de hormigón",
        created_by="test"
    )
    
    # Add variables
    material_var_id = db.add_variable(element_id, "material", "TEXT", None, "hormigón", True, 1)
    width_var_id = db.add_variable(element_id, "ancho", "NUMERIC", "mm", "300", True, 2)
    height_var_id = db.add_variable(element_id, "alto", "NUMERIC", "mm", "2800", True, 3)
    finish_var_id = db.add_variable(element_id, "acabado", "TEXT", None, "liso", False, 4)
    
    print(f"Created element {element_id} with variables:")
    print(f"  material: {material_var_id}")
    print(f"  ancho: {width_var_id}")
    print(f"  alto: {height_var_id}")
    print(f"  acabado: {finish_var_id}")
    
    # Create mock extracted template
    from template_extractor import ExtractedTemplate
    
    template = ExtractedTemplate(
        element_code="WALL001",
        element_url="http://test.com",
        description_template="Muro de {material} de {ancho}×{alto} con acabado {acabado}",
        variables={
            "material": "MATERIAL",
            "ancho": "NUMERIC",
            "alto": "NUMERIC", 
            "acabado": "FINISH"
        },
        dependencies=[],
        confidence=0.85,
        coverage=0.90,
        total_combinations_tested=5
    )
    
    # Test integration
    integrator = TemplateDbIntegrator("test_template_integration.db")
    result = integrator.integrate_template(template, element_id)
    
    if result:
        print(f"\\n" + "="*60)
        print("INTEGRATION RESULT:")
        print("="*60)
        print(f"Version ID: {result.version_id}")
        print(f"Template: {result.template}")
        print(f"Mappings: {len(result.mappings_created)}")
        
        # Show detailed template info
        template_info = integrator.get_template_info(result.version_id)
        print(f"\\nDETAILED TEMPLATE INFO:")
        print(f"Element: {template_info['element_code']} - {template_info['element_name']}")
        print(f"Template: {template_info['description_template']}")
        print(f"State: {template_info['state']}")
        
        print(f"\\nMAPPINGS:")
        for mapping in template_info['mappings']:
            print(f"  {mapping['position']}: {mapping['placeholder']} -> {mapping['variable_name']} ({mapping['variable_type']})")

if __name__ == "__main__":
    test_template_integration()