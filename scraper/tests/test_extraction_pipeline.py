#!/usr/bin/env python3
"""
Test extraction pipeline with already discovered elements
"""

import sys
import json
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "core"))
sys.path.insert(0, str(Path(__file__).parent / "template_extraction"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enhanced_element_extractor import EnhancedElementExtractor
from smart_template_extractor import SmartTemplateExtractor
from template_db_integrator import TemplateDbIntegrator

def test_extraction_with_discovered_elements():
    """Test the extraction pipeline with already discovered elements"""
    
    # Load discovered elements
    try:
        with open('core/final_crawl_progress.json', 'r') as f:
            data = json.load(f)
        discovered_urls = data['element_urls']
        print(f"📂 Loaded {len(discovered_urls)} discovered elements")
    except:
        print("❌ No discovery data found. Run discovery first.")
        return
    
    # Initialize components
    element_extractor = EnhancedElementExtractor()
    template_extractor = SmartTemplateExtractor()
    
    # Database setup
    db_path = str(Path(__file__).parent.parent / "src" / "office_data.db")
    db_integrator = TemplateDbIntegrator(db_path)
    
    print(f"🗄️ Database: {db_path}")
    print()
    
    # Test with first 3 elements
    test_urls = discovered_urls[:3]
    
    for i, url in enumerate(test_urls):
        print(f"--- Test Element {i+1}/3 ---")
        print(f"URL: {url}")
        
        try:
            # Extract element data
            print("  🔄 Extracting element data...")
            element = element_extractor.extract_element_data(url)
            
            if not element:
                print("  ❌ No element data extracted")
                continue
            
            print(f"  ✅ Element: {element.code} - {element.title}")
            print(f"  ✅ Variables: {len(element.variables)}")
            
            # Generate template
            print("  🔄 Generating template...")
            template = template_extractor.extract_template_smart(url)
            
            if template and template.template_text:
                print(f"  ✅ Template: {template.template_text}")
                print(f"  ✅ Template variables: {len(template.variables)}")
            else:
                print("  ⚠️ No template generated")
            
            # Store in database
            print("  🔄 Storing in database...")
            element_id = db_integrator.store_complete_element(
                element=element,
                template=template,
                url=url
            )
            
            print(f"  ✅ Stored with ID: {element_id}")
            print()
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue
    
    # Check database status
    print("📊 DATABASE SUMMARY:")
    try:
        summary = db_integrator.get_database_summary()
        print(f"   Elements: {summary.get('total_elements', 0)}")
        print(f"   Variables: {summary.get('total_variables', 0)}")
        print(f"   Variable Options: {summary.get('total_options', 0)}")
        print(f"   Description Versions: {summary.get('total_descriptions', 0)}")
        print(f"   Template Mappings: {summary.get('total_mappings', 0)}")
    except Exception as e:
        print(f"   Error getting summary: {e}")

if __name__ == "__main__":
    test_extraction_with_discovered_elements()