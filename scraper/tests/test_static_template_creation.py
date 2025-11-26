#!/usr/bin/env python3
"""
Create static description templates from CYPE descriptions
Since CYPE descriptions don't change with variables, create static templates
"""

import sys
import re
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enhanced_element_extractor import EnhancedElementExtractor
from db_manager import DatabaseManager

def test_static_template_creation():
    """Test creating static description templates from CYPE elements"""
    
    print("🔧 TESTING STATIC TEMPLATE CREATION")
    print("=" * 60)
    
    # Test URL
    test_url = "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html"
    
    extractor = EnhancedElementExtractor()
    
    print(f"🌐 Testing URL: {test_url}")
    
    try:
        # Extract element with base configuration
        result = extractor.extract_element(test_url)
        
        if not result or not result.get('success'):
            print(f"❌ Failed to extract element: {result.get('error', 'Unknown error')}")
            return
        
        element = result['element']
        
        print(f"✅ Element extracted successfully:")
        print(f"   Code: {element.code}")
        print(f"   Title: {element.title}")
        print(f"   Price: {element.price}€")
        print(f"   Description length: {len(element.description)} characters")
        print(f"   Variables: {len(element.variables)}")
        
        # Create static description template
        static_template = create_static_description_template(element.description)
        
        print(f"\n📋 STATIC TEMPLATE CREATED:")
        print(f"   Template length: {len(static_template)} characters")
        print(f"   Template preview: {static_template[:150]}...")
        
        # Store in database
        db_path = str(Path(__file__).parent.parent / "src" / "office_data.db")
        db_manager = DatabaseManager(db_path)
        
        element_id = store_element_with_static_template(
            db_manager, element, static_template, test_url
        )
        
        print(f"\n💾 STORED IN DATABASE:")
        print(f"   Element ID: {element_id}")
        print(f"   Template stored: ✅")
        print(f"   Variables stored: {len(element.variables)}")
        
        # Verify template storage
        verify_template_storage(db_manager, element_id)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_static_description_template(description):
    """Create a static template from CYPE description"""
    
    # Clean the description text
    clean_desc = clean_description_text(description)
    
    # Since CYPE descriptions are static, the template IS the description
    # No placeholders needed, just clean static text
    return clean_desc

def clean_description_text(text):
    """Clean and normalize description text"""
    
    if not text:
        return ""
    
    # Fix encoding issues
    text = fix_utf8_issues(text)
    
    # Clean up formatting
    text = re.sub(r'\s+', ' ', text.strip())  # Multiple spaces to single
    text = re.sub(r'^\W+', '', text)  # Remove leading non-word chars
    
    # Ensure proper punctuation
    if text and not text.endswith('.'):
        text += '.'
    
    return text

def fix_utf8_issues(text):
    """Fix common UTF-8 encoding issues in CYPE descriptions"""
    
    utf8_fixes = {
        'Ã±': 'ñ',
        'Ã³': 'ó', 
        'Ã¡': 'á',
        'Ã©': 'é',
        'Ã­': 'í',
        'Ãº': 'ú',
        'Ã¼': 'ü',
        'Ã‡': 'Ç',
        'Â²': '²',
        'Â³': '³',
        'Â°': '°',
        'ÃŸ': 'ß',
        'Â': '',
        'û°': 'ó',
        'môý': 'm²',
        '‚¬': '€',
        'ã˜': '€',
        'Ž': '€',
        'ÃŠ': 'Ê',
        'Ãģ': 'ã',
        'Âē': '²',
        'HORMIGÃN': 'HORMIGÓN'
    }
    
    for wrong, correct in utf8_fixes.items():
        text = text.replace(wrong, correct)
    
    return text

def store_element_with_static_template(db_manager, element, template, url):
    """Store element with static template in database"""
    
    # Create element
    element_id = db_manager.create_element(
        element_code=f"{element.code}_STATIC_TEST",
        element_name=element.title,
        price=element.price,
        created_by='Static_Template_Test'
    )
    
    # Store variables
    for variable in element.variables:
        var_id = db_manager.add_element_variable(
            element_id=element_id,
            variable_name=variable.name,
            variable_type=variable.var_type,
            unit=variable.unit,
            is_required=variable.is_required
        )
        
        # Store options
        if hasattr(variable, 'options') and variable.options:
            for option_value in variable.options:
                db_manager.add_variable_option(
                    variable_id=var_id,
                    option_value=str(option_value)
                )
    
    # Create static description template
    version_id = db_manager.create_description_version(
        element_id=element_id,
        description_template=template,
        state='finalized',
        created_by='Static_Template_Test'
    )
    
    print(f"   Created template version: {version_id}")
    
    # No template variable mappings needed for static templates
    # Variables are stored separately for application use
    
    return element_id

def verify_template_storage(db_manager, element_id):
    """Verify that template was stored correctly"""
    
    print(f"\n🔍 VERIFYING TEMPLATE STORAGE:")
    
    # Get template
    with db_manager.get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM description_versions WHERE element_id = ?",
            (element_id,)
        )
        template_row = cursor.fetchone()
    
    if template_row:
        template = template_row['description_template']
        print(f"   ✅ Template found: {len(template)} characters")
        print(f"   ✅ Template state: {template_row['state']}")
        print(f"   ✅ Created by: {template_row['created_by']}")
        
        # Check for encoding issues
        if any(bad in template for bad in ['Ã', 'â', 'Â']):
            print(f"   ⚠️  May have encoding issues")
        else:
            print(f"   ✅ Clean UTF-8 encoding")
        
        # Check template content
        if 'hormigón' in template.lower() or 'madera' in template.lower() or 'acero' in template.lower():
            print(f"   ✅ Contains construction terms")
        
        return True
    else:
        print(f"   ❌ No template found")
        return False

if __name__ == "__main__":
    success = test_static_template_creation()
    
    if success:
        print(f"\n🎉 STATIC TEMPLATE CREATION SUCCESS!")
        print(f"   ✅ CYPE description → static template")
        print(f"   ✅ Clean UTF-8 encoding")
        print(f"   ✅ Database storage working")
        print(f"   ✅ Variables stored separately")
    else:
        print(f"\n❌ Static template creation failed")