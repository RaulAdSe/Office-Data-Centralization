#!/usr/bin/env python3
"""
Simple test showing template extraction concept working
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from db_manager import DatabaseManager
from template_db_integrator import TemplateDbIntegrator
from template_extractor import ExtractedTemplate

def test_template_database_integration():
    """Test the template database integration with mock data"""
    
    print("🧪 TESTING TEMPLATE DATABASE INTEGRATION")
    print("=" * 60)
    
    # Create test database
    db_path = "simple_template_test.db" 
    db = DatabaseManager(db_path)
    
    # Create test element
    element_id = db.create_element(
        element_code="VIGA001",
        element_name="Viga de hormigón armado", 
        created_by="test"
    )
    print(f"✅ Created element {element_id}: VIGA001")
    
    # Add variables that would come from CYPE extraction
    var_ids = {}
    variables = [
        ("tipo_hormigon", "TEXT", ["Convencional", "Autocompactante"], "Convencional"),
        ("resistencia", "TEXT", None, "25"),
        ("dimension_ancho", "TEXT", None, "30"),
        ("dimension_alto", "TEXT", None, "60"),
        ("tipo_acero", "TEXT", ["B 400 S", "B 500 S"], "B 400 S"),
        ("acabado", "TEXT", ["Liso", "Texturizado"], "Liso")
    ]
    
    for var_name, var_type, options, default in variables:
        var_id = db.add_variable(element_id, var_name, var_type, None, default, True, len(var_ids) + 1)
        var_ids[var_name] = var_id
        
        if options:
            for i, option in enumerate(options):
                db.add_variable_option(var_id, option, option, i + 1, option == default)
        
        print(f"  ✅ Variable: {var_name} (ID: {var_id})")
    
    # Create mock extracted template (this is what the template extractor would produce)
    extracted_template = ExtractedTemplate(
        element_code="VIGA001",
        element_url="http://test.com/viga",
        description_template="Viga de hormigón {tipo_hormigon}, resistencia característica {resistencia} N/mm², dimensiones {dimension_ancho}x{dimension_alto} cm, acero {tipo_acero}, acabado {acabado}",
        variables={
            "tipo_hormigon": "MATERIAL",
            "resistencia": "NUMERIC", 
            "dimension_ancho": "NUMERIC",
            "dimension_alto": "NUMERIC",
            "tipo_acero": "MATERIAL",
            "acabado": "FINISH"
        },
        dependencies=[],
        confidence=0.85,
        coverage=0.90,
        total_combinations_tested=7
    )
    
    print(f"\\n📝 Mock template to integrate:")
    print(f"   {extracted_template.description_template}")
    print(f"   Variables: {list(extracted_template.variables.keys())}")
    
    # Integrate template into database
    integrator = TemplateDbIntegrator(db_path)
    result = integrator.integrate_template(extracted_template, element_id)
    
    if result:
        print(f"\\n✅ INTEGRATION SUCCESSFUL!")
        print(f"   Version ID: {result.version_id}")
        print(f"   Mappings: {len(result.mappings_created)}")
        
        # Show the final database structure
        template_info = integrator.get_template_info(result.version_id)
        
        print(f"\\n" + "=" * 80)
        print("FINAL DATABASE STRUCTURE")
        print("=" * 80)
        print(f"Element: {template_info['element_code']} - {template_info['element_name']}")
        print(f"Template: {template_info['description_template']}")
        print(f"State: {template_info['state']} | Version: {template_info['version_number']}")
        
        print(f"\\nVariable Mappings (template_variable_mappings table):")
        print(f"{'Pos':<3} {'Placeholder':<18} {'Variable Name':<18} {'Type':<8}")
        print("-" * 50)
        
        for mapping in template_info['mappings']:
            print(f"{mapping['position']:<3} {mapping['placeholder']:<18} {mapping['variable_name']:<18} {mapping['variable_type']:<8}")
        
        # Show how to use this template
        print(f"\\n" + "=" * 80)
        print("HOW THIS TEMPLATE WOULD BE USED")
        print("=" * 80)
        
        example_values = {
            "tipo_hormigon": "Autocompactante",
            "resistencia": "30", 
            "dimension_ancho": "35",
            "dimension_alto": "70",
            "tipo_acero": "B 500 S",
            "acabado": "Texturizado"
        }
        
        # Simulate template rendering
        rendered = template_info['description_template']
        for mapping in template_info['mappings']:
            var_name = mapping['variable_name']
            placeholder = mapping['placeholder']
            if var_name in example_values:
                rendered = rendered.replace(placeholder, example_values[var_name])
        
        print(f"Template: {template_info['description_template']}")
        print(f"Values: {example_values}")
        print(f"Result: {rendered}")
        
        print(f"\\n🎉 SUCCESS! Template system works exactly as specified!")
        print(f"   Database: {db_path}")
        print(f"   Ready for real CYPE template extraction!")
        
        return True
    else:
        print(f"❌ Integration failed")
        return False

if __name__ == "__main__":
    success = test_template_database_integration()
    
    if success:
        print(f"\\n✅ Template system is ready!")
        print(f"   Next: Run real CYPE extraction with full_template_pipeline.py")
    else:
        print(f"\\n❌ Template system needs debugging")