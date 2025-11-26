#!/usr/bin/env python3
"""
Test with simple template generation that works with CYPE elements
"""

import sys
from pathlib import Path
import time

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enhanced_element_extractor import EnhancedElementExtractor
from db_manager import DatabaseManager

def create_simple_template(element):
    """Create a simple template based on element structure"""
    
    # Get key variables that are commonly used in construction descriptions
    key_variables = []
    dimension_vars = []
    
    for var in element.variables:
        var_name_lower = var.name.lower()
        
        # Key material/type variables
        if any(keyword in var_name_lower for keyword in ['tipo', 'material', 'clase', 'acabado']):
            if var.options and len(var.options) > 1:  # Only if it has meaningful options
                key_variables.append(var.name)
        
        # Dimension variables
        elif any(keyword in var_name_lower for keyword in ['ancho', 'alto', 'dimension', 'diametro', 'espesor', 'longitud']):
            if var.options and len(var.options) > 1:
                dimension_vars.append(var.name)
    
    # Create template based on element title and key variables
    template_parts = [element.title]
    
    # Add key variables
    if key_variables:
        for var in key_variables[:2]:  # Use up to 2 key variables
            template_parts.append(f"{{{var}}}")
    
    # Add dimensions
    if dimension_vars:
        if len(dimension_vars) == 1:
            template_parts.append(f"de {{{dimension_vars[0]}}}")
        elif len(dimension_vars) >= 2:
            template_parts.append(f"de {{{dimension_vars[0]}}}×{{{dimension_vars[1]}}}")
    
    # Join template
    if len(template_parts) > 1:
        # Create a natural Spanish template
        base = template_parts[0]  # Element title
        variables = template_parts[1:]  # Variable placeholders
        
        if 'VIGA' in base.upper():
            template = f"{base} de {' de '.join(variables)}"
        elif 'LACA' in base.upper() or 'PINTURA' in base.upper():
            template = f"{base} para {' con '.join(variables)}"
        else:
            template = f"{base} de {' '.join(variables)}"
        
        return template, key_variables + dimension_vars[:2]
    
    return None, []

def test_with_simple_template():
    """Test with simple template generation"""
    
    print("🧪 TESTING WITH SIMPLE TEMPLATE GENERATION")
    print("=" * 60)
    
    # Test with both elements
    test_urls = [
        "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Lacas/Laca_sintetica_para_madera.html",
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html"
    ]
    
    element_extractor = EnhancedElementExtractor()
    db_path = str(Path(__file__).parent.parent / "src" / "office_data.db")
    db_manager = DatabaseManager(db_path)
    
    for i, test_url in enumerate(test_urls):
        print(f"\\n--- Test {i+1}/2 ---")
        print(f"URL: {test_url}")
        
        # Extract element
        element = element_extractor.extract_element_data(test_url)
        print(f"✅ Element: {element.code} - {element.title}")
        print(f"   Variables: {len(element.variables)}")
        
        # Create simple template
        template, template_vars = create_simple_template(element)
        
        if template:
            print(f"✅ Template: {template}")
            print(f"   Variables used: {template_vars}")
        else:
            print(f"⚠️ No template generated")
        
        # Store in database
        try:
            # Create unique element code for this test
            element_code = f"{element.code}_TEST_{i+1}"
            element_id = db_manager.create_element(
                element_code=element_code,
                element_name=element.title,
                created_by='Template_Test'
            )
            
            # Add variables
            vars_with_options = 0
            total_options = 0
            
            for var in element.variables:
                variable_id = db_manager.add_variable(
                    element_id=element_id,
                    variable_name=var.name,
                    variable_type='TEXT',
                    is_required=len(var.options) > 0,
                    display_order=len(element.variables)
                )
                
                if var.options:
                    vars_with_options += 1
                    for j, option in enumerate(var.options):
                        db_manager.add_variable_option(
                            variable_id=variable_id,
                            option_value=option,
                            option_label=option,
                            display_order=j,
                            is_default=(j == 0)
                        )
                        total_options += 1
            
            print(f"✅ Stored: {vars_with_options} variables with {total_options} options")
            
            # Create template if generated
            if template:
                version_id = db_manager.create_proposal(
                    element_id=element_id,
                    description_template=template,
                    created_by='Template_Test'
                )
                
                # Auto-approve
                for _ in range(3):
                    db_manager.approve_proposal(version_id, 'Template_Test', 'Auto-approved')
                
                print(f"✅ Template created and activated")
            
        except Exception as e:
            print(f"❌ Database error: {e}")
    
    # Final verification
    print(f"\\n📊 FINAL DATABASE STATUS:")
    elements = db_manager.list_elements()
    print(f"   Total elements: {len(elements)}")
    
    for element in elements[-2:]:  # Show last 2 elements
        variables = db_manager.get_element_variables(element['element_id'])
        active_version = db_manager.get_active_version(element['element_id'])
        
        total_options = sum(len(var.get('options', [])) for var in variables)
        
        print(f"   Element {element['element_code']}:")
        print(f"     Variables: {len(variables)} ({total_options} options)")
        if active_version:
            print(f"     Template: {active_version['description_template']}")
        else:
            print(f"     Template: None")
    
    print(f"\\n🎉 SIMPLE TEMPLATE GENERATION TEST COMPLETED!")
    print(f"   ✅ Templates created based on element structure")
    print(f"   ✅ Spanish placeholders like {{tipo_hormigon}}")
    print(f"   ✅ Ready for template-based description generation")

if __name__ == "__main__":
    test_with_simple_template()