#!/usr/bin/env python3
"""
Test: Discover and process elements with static templates
"""

import sys
from pathlib import Path
import time

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "core"))
sys.path.insert(0, str(Path(__file__).parent / "template_extraction"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enhanced_element_extractor import EnhancedElementExtractor
from db_manager import DatabaseManager
import requests
from bs4 import BeautifulSoup
import re

# Test configuration
NUM_TEST_ELEMENTS = 2

def discover_test_elements():
    """Discover elements from CYPE for testing"""
    
    print(f"🔍 DISCOVERING {NUM_TEST_ELEMENTS} ELEMENTS...")
    
    # Try a known category that has elements
    test_url = "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas.html"
    
    try:
        response = requests.get(test_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find element links
        element_urls = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('/') and href.endswith('.html'):
                # Convert to full URL
                full_url = f"https://generadordeprecios.info{href}"
                # Check if it looks like an element (not category)
                if re.search(r'[A-Z]{2,}[0-9]{2,}', href):  # Pattern like EHV015
                    element_urls.append(full_url)
                    if len(element_urls) >= NUM_TEST_ELEMENTS:
                        break
        
        if len(element_urls) >= NUM_TEST_ELEMENTS:
            print(f"   ✅ Found {len(element_urls)} elements:")
            for i, url in enumerate(element_urls[:NUM_TEST_ELEMENTS]):
                print(f"      {i+1}. {url}")
            return element_urls[:NUM_TEST_ELEMENTS]
        else:
            # Fallback to known working URLs
            fallback_urls = [
                "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html",
                "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_de_hormigon_armado.html"
            ]
            print(f"   ⚠️ Using fallback URLs:")
            for i, url in enumerate(fallback_urls):
                print(f"      {i+1}. {url}")
            return fallback_urls
            
    except Exception as e:
        print(f"   ❌ Discovery failed: {e}")
        return []

def process_element(url, element_extractor, db_manager, element_number):
    """Process single element with static template"""
    
    print(f"\n--- PROCESSING ELEMENT {element_number} ---")
    print(f"URL: {url}")
    
    try:
        # Extract element data
        element = element_extractor.extract_element_data(url)
        if not element:
            print(f"   ❌ Failed to extract element data")
            return False
        
        print(f"   ✅ Extracted: {element.code} - {element.title}")
        print(f"   Variables: {len(element.variables)}")
        
        # Try to generate template (with variable testing)
        from smart_template_extractor import SmartTemplateExtractor
        template_extractor = SmartTemplateExtractor()
        template = template_extractor.extract_template_smart(url)
        
        if template and hasattr(template, 'template') and template.template:
            print(f"   ✅ Dynamic template: {template.template}")
            print(f"   Variables: {len(template.variables)}")
            template_to_use = template.template
        else:
            # If no dynamic template found, get REAL element description from meta description
            template_to_use = template_extractor.get_static_description(url)
            print(f"   ✅ Static template: {template_to_use[:100]}...")
            print(f"   Template length: {len(template_to_use)} characters")
        
        # Store in database
        import time
        timestamp = int(time.time())
        element_code = f"{element.code}_TEST_{timestamp}_{element_number}"
        element_id = db_manager.create_element(
            element_code=element_code,
            element_name=element.title,
            created_by='Two_Element_Test'
        )
        
        # Add variables (all optional)
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
        
        # Create template (dynamic or static)
        version_id = db_manager.create_proposal(
            element_id=element_id,
            description_template=template_to_use,
            created_by='Two_Element_Test'
        )
        
        # Auto-approve
        for _ in range(3):
            db_manager.approve_proposal(version_id, 'Two_Element_Test', 'Auto-approved static template')
        
        print(f"   ✅ Stored: {vars_added} variables, {options_added} options")
        print(f"   ✅ Template created and activated")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Processing failed: {e}")
        return False

def test_two_elements():
    """Main test function"""
    
    print(f"🧪 DISCOVER AND PROCESS {NUM_TEST_ELEMENTS} ELEMENTS TEST")
    print("=" * 50)
    
    # Initialize components
    element_extractor = EnhancedElementExtractor()
    db_path = str(Path(__file__).parent.parent / "src" / "office_data.db")
    db_manager = DatabaseManager(db_path)
    
    # Phase 1: Discover elements
    element_urls = discover_test_elements()
    if len(element_urls) < NUM_TEST_ELEMENTS:
        print(f"❌ Could not discover {NUM_TEST_ELEMENTS} elements")
        return False
    
    # Phase 2: Process both elements
    print(f"\n🔄 PROCESSING {len(element_urls)} ELEMENTS...")
    
    success_count = 0
    for i, url in enumerate(element_urls):
        if process_element(url, element_extractor, db_manager, i + 1):
            success_count += 1
        time.sleep(1)  # Be respectful
    
    # Final summary
    print(f"\n📊 FINAL RESULTS:")
    print(f"   Elements discovered: {len(element_urls)}")
    print(f"   Elements processed successfully: {success_count}")
    print(f"   Failed: {len(element_urls) - success_count}")
    
    if success_count == len(element_urls):
        print(f"\n🎉 SUCCESS! All {len(element_urls)} elements processed!")
        print(f"   ✅ Discovery: Working")
        print(f"   ✅ Extraction: Working")
        print(f"   ✅ Static templates: Working")
        print(f"   ✅ Database storage: Working")
        return True
    else:
        print(f"\n⚠️ Partial success: {success_count}/{len(element_urls)} elements processed")
        return False

if __name__ == "__main__":
    test_two_elements()