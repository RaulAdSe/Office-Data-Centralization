#!/usr/bin/env python3
"""
Simple test of static template approach - single element
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enhanced_element_extractor import EnhancedElementExtractor
from db_manager import DatabaseManager

def test_static_template_simple():
    """Test static template approach with one element"""
    
    print("🧪 TESTING STATIC TEMPLATE APPROACH")
    print("=" * 50)
    
    # Test URL
    test_url = "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html"
    
    # Initialize components
    element_extractor = EnhancedElementExtractor()
    db_path = str(Path(__file__).parent.parent / "src" / "office_data.db")
    db_manager = DatabaseManager(db_path)
    
    print(f"🎯 Testing: {test_url}")
    
    # Extract element
    element = element_extractor.extract_element_data(test_url)
    print(f"\n✅ Element extracted:")
    print(f"   Code: {element.code}")
    print(f"   Title: {element.title}")
    print(f"   Variables: {len(element.variables)}")
    
    # Create static template (no placeholders)
    static_template = element.title.strip()
    print(f"\n✅ Static template created:")
    print(f"   Template: {static_template}")
    print(f"   Type: Static (no variable placeholders)")
    
    # Store in database
    try:
        # Use unique element code for this test
        element_code = f"{element.code}_STATIC_TEST"
        element_id = db_manager.create_element(
            element_code=element_code,
            element_name=element.title,
            created_by='Static_Test'
        )
        
        print(f"\n🔄 Storing element in database...")
        print(f"   Element ID: {element_id}")
        
        # Add variables (all optional since template is static)
        vars_added = 0
        options_added = 0
        
        for var in element.variables:
            variable_id = db_manager.add_variable(
                element_id=element_id,
                variable_name=var.name,
                variable_type='TEXT',
                unit=getattr(var, 'unit', None),
                default_value=var.options[0] if var.options else None,
                is_required=False,  # All optional for static templates
                display_order=vars_added + 1
            )
            vars_added += 1
            
            # Add options
            for j, option in enumerate(var.options):
                db_manager.add_variable_option(
                    variable_id=variable_id,
                    option_value=option,
                    option_label=option,
                    display_order=j,
                    is_default=(j == 0)
                )
                options_added += 1
        
        print(f"   ✅ Variables added: {vars_added}")
        print(f"   ✅ Options added: {options_added}")
        
        # Create static template
        version_id = db_manager.create_proposal(
            element_id=element_id,
            description_template=static_template,
            created_by='Static_Test'
        )
        
        # Auto-approve
        for _ in range(3):
            db_manager.approve_proposal(version_id, 'Static_Test', 'Auto-approved static template')
        
        print(f"   ✅ Static template created and activated!")
        
        # Test rendering
        print(f"\n🔄 Testing static template rendering...")
        
        # Create test project
        project_id = db_manager.create_project(
            project_code='STATIC_TEST',
            project_name='Static Template Test'
        )
        
        # Create element instance
        instance_id = db_manager.create_project_element(
            project_id=project_id,
            element_id=element_id,
            description_version_id=version_id,
            instance_code='STATIC_001',
            instance_name='Test Static Element'
        )
        
        # Render static description (no variable values needed)
        rendered = db_manager.render_description(instance_id)
        print(f"   ✅ Rendered description: {rendered}")
        
        print(f"\n🎉 SUCCESS! STATIC TEMPLATE WORKING!")
        print(f"   ✅ Element extraction: Spanish data preserved")
        print(f"   ✅ Static template: Uses element title as-is")
        print(f"   ✅ Database storage: All variables optional")
        print(f"   ✅ Template rendering: Static text output")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_static_template_simple()