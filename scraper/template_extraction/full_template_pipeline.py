#!/usr/bin/env python3
"""
Complete end-to-end template extraction and database integration pipeline
"""

import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from enhanced_element_extractor import EnhancedElementExtractor
from template_extractor import TemplateExtractor
from template_db_integrator import TemplateDbIntegrator
from db_manager import DatabaseManager

def run_full_template_pipeline(element_url: str, output_db_path: str):
    """
    Complete pipeline: Extract element -> Extract template -> Store in database
    
    Args:
        element_url: URL of CYPE element to process
        output_db_path: Path to output database
    """
    
    print("🏗️  COMPLETE TEMPLATE EXTRACTION PIPELINE")
    print("=" * 80)
    print(f"Element URL: {element_url}")
    print(f"Output DB: {output_db_path}")
    print()
    
    # =========================================================================
    # STEP 1: Extract Element Data (variables, etc.)
    # =========================================================================
    print("📊 STEP 1: Extracting element data...")
    
    extractor = EnhancedElementExtractor()
    element = extractor.extract_element_data(element_url)
    
    if not element:
        print("❌ Failed to extract element data")
        return False
    
    print(f"✅ Element extracted:")
    print(f"   Code: {element.code}")
    print(f"   Title: {element.title}")
    print(f"   Variables: {len(element.variables)}")
    
    for i, var in enumerate(element.variables[:5]):  # Show first 5
        print(f"   {i+1}. {var.name} ({var.variable_type}): {var.options[:3] if var.options else 'No options'}")
    
    if not element.variables:
        print("❌ No variables found - cannot extract template")
        return False
    
    # =========================================================================
    # STEP 2: Extract Description Template
    # =========================================================================
    print(f"\\n🔍 STEP 2: Extracting template with 5 combinations...")
    
    template_extractor = TemplateExtractor(max_combinations=5, delay_seconds=1.0)
    template = template_extractor.extract_template(
        element_url=element_url,
        variables=element.variables,
        element_code=element.code
    )
    
    if not template:
        print("❌ Failed to extract template")
        return False
    
    print(f"✅ Template extracted:")
    print(f"   Template: {template.description_template}")
    print(f"   Variables: {list(template.variables.keys())}")
    print(f"   Confidence: {template.confidence:.2f}")
    print(f"   Coverage: {template.coverage:.2f}")
    
    # =========================================================================
    # STEP 3: Prepare Database
    # =========================================================================
    print(f"\\n💾 STEP 3: Setting up database...")
    
    db_manager = DatabaseManager(output_db_path)
    
    # Create element in database
    element_id = db_manager.create_element(
        element_code=element.code,
        element_name=element.title,
        created_by="template_pipeline"
    )
    
    print(f"✅ Element created with ID: {element_id}")
    
    # Add variables to database
    print(f"📝 Adding {len(element.variables)} variables...")
    
    for i, var in enumerate(element.variables):
        var_id = db_manager.add_variable(
            element_id=element_id,
            variable_name=var.name,
            variable_type=var.variable_type,
            unit=None,
            default_value=var.default_value,
            is_required=True,
            display_order=i + 1
        )
        
        # Add options if it's a RADIO variable
        if var.variable_type == 'RADIO' and var.options:
            for j, option in enumerate(var.options):
                db_manager.add_variable_option(
                    variable_id=var_id,
                    option_value=option,
                    option_label=option,
                    display_order=j + 1,
                    is_default=(option == var.default_value)
                )
        
        print(f"   ✅ {var.name} (ID: {var_id}) - {len(var.options) if var.options else 0} options")
    
    # =========================================================================
    # STEP 4: Integrate Template into Database Schema
    # =========================================================================
    print(f"\\n🔗 STEP 4: Integrating template into database schema...")
    
    integrator = TemplateDbIntegrator(output_db_path)
    result = integrator.integrate_template(template, element_id)
    
    if not result:
        print("❌ Failed to integrate template")
        return False
    
    print(f"✅ Template integrated:")
    print(f"   Version ID: {result.version_id}")
    print(f"   Mappings created: {len(result.mappings_created)}")
    print(f"   Variables matched: {result.variables_matched}")
    
    if result.variables_not_matched:
        print(f"   ⚠️  Variables not matched: {result.variables_not_matched}")
    
    # =========================================================================
    # STEP 5: Verify Final Result
    # =========================================================================
    print(f"\\n✅ STEP 5: Verification - Showing final database structure...")
    
    # Show the complete template information as it exists in the database
    template_info = integrator.get_template_info(result.version_id)
    
    print(f"\\n" + "=" * 80)
    print("FINAL RESULT IN DATABASE")
    print("=" * 80)
    print(f"Element: {template_info['element_code']} - {template_info['element_name']}")
    print(f"Template: {template_info['description_template']}")
    print(f"State: {template_info['state']}")
    print(f"Version: {template_info['version_number']}")
    
    print(f"\\nTemplate Variable Mappings:")
    print(f"{'Pos':<3} {'Placeholder':<15} {'Variable Name':<15} {'Type':<8} {'Required':<8}")
    print("-" * 60)
    
    for mapping in template_info['mappings']:
        print(f"{mapping['position']:<3} {mapping['placeholder']:<15} {mapping['variable_name']:<15} "
              f"{mapping['variable_type']:<8} {'Yes' if mapping['is_required'] else 'No':<8}")
    
    # Show SQL query to reconstruct this info
    print(f"\\n" + "=" * 80)
    print("SQL QUERY TO VIEW THIS TEMPLATE:")
    print("=" * 80)
    print(f"""
SELECT 
    dv.version_id,
    dv.description_template,
    tvm.position,
    tvm.placeholder,
    ev.variable_name,
    ev.variable_type,
    ev.unit,
    ev.is_required
FROM description_versions dv
JOIN template_variable_mappings tvm ON dv.version_id = tvm.version_id
JOIN element_variables ev ON tvm.variable_id = ev.variable_id
WHERE dv.version_id = {result.version_id}
ORDER BY tvm.position;
""")
    
    print(f"\\n🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"   Database: {output_db_path}")
    print(f"   Element ID: {element_id}")
    print(f"   Template Version ID: {result.version_id}")
    
    return True

def test_pipeline():
    """Test the pipeline with a real CYPE element"""
    
    # Test with a known CYPE element
    test_url = "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html"
    output_db = "template_pipeline_test.db"
    
    success = run_full_template_pipeline(test_url, output_db)
    
    if success:
        print(f"\\n✅ Test completed successfully!")
        print(f"Check the database: {output_db}")
    else:
        print(f"\\n❌ Test failed")

if __name__ == "__main__":
    test_pipeline()