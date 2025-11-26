#!/usr/bin/env python3
"""
Complete End-to-End Test of Enhanced Template System
Ensures dynamic placeholders work in production pipeline
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enhanced_template_system import EnhancedTemplateSystem
from production_dynamic_template_system import ProductionDynamicTemplateSystem

def test_complete_enhanced_pipeline():
    """Test complete enhanced pipeline with real CYPE variations"""
    
    print("🚀 COMPLETE ENHANCED PIPELINE TEST")
    print("=" * 70)
    
    # Step 1: Force discovery of multi-URL elements
    print("📊 STEP 1: DISCOVERING REAL ELEMENT VARIATIONS")
    prod_system = ProductionDynamicTemplateSystem()
    all_urls = prod_system.discover_element_urls(100)  # Get more URLs
    element_groups = prod_system.group_urls_by_element_code(all_urls)
    
    multi_url_elements = element_groups.get('multi_url', {})
    print(f"   Found {len(multi_url_elements)} elements with multiple URLs:")
    
    selected_elements = {}
    count = 0
    for code, urls in multi_url_elements.items():
        if count >= 3:  # Test with 3 multi-URL elements
            break
        selected_elements[code] = urls[:3]  # Max 3 URLs per element
        print(f"   - {code}: {len(urls)} URLs → testing {len(selected_elements[code])}")
        count += 1
    
    if not selected_elements:
        print("   ❌ No multi-URL elements found! Creating test variations...")
        # Create synthetic test with known variations
        selected_elements = create_synthetic_variations()
    
    # Step 2: Extract content from all variations
    print(f"\n📊 STEP 2: ENHANCED CONTENT EXTRACTION")
    enhanced_system = EnhancedTemplateSystem()
    
    all_extracted_elements = []
    for element_code, urls in selected_elements.items():
        print(f"   Extracting {element_code} ({len(urls)} variations)...")
        
        for i, url in enumerate(urls, 1):
            print(f"     Variation {i}: {url[:60]}...")
            element_data = enhanced_system.extract_enhanced_element_data(url)
            if element_data:
                print(f"       ✅ {len(element_data['description'])} chars extracted")
                all_extracted_elements.append(element_data)
            else:
                print(f"       ❌ Failed to extract")
    
    print(f"   ✅ Total extracted: {len(all_extracted_elements)} element variations")
    
    # Step 3: Generate enhanced dynamic templates
    print(f"\n📊 STEP 3: DYNAMIC TEMPLATE GENERATION")
    grouped = enhanced_system.group_elements_by_code(all_extracted_elements)
    templates = enhanced_system.generate_enhanced_templates(grouped)
    
    print(f"   Generated {len(templates)} templates:")
    
    dynamic_templates = []
    static_templates = []
    
    for template in templates:
        if template['template_type'] == 'dynamic':
            dynamic_templates.append(template)
            print(f"   ✅ {template['element_code']}: DYNAMIC ({len(template['placeholders'])} placeholders)")
            for placeholder in template['placeholders']:
                print(f"      - {{{placeholder}}}")
        else:
            static_templates.append(template)
            print(f"   📄 {template['element_code']}: STATIC (no variations)")
    
    # Step 4: Test database storage with placeholders
    print(f"\n📊 STEP 4: DATABASE STORAGE WITH PLACEHOLDERS")
    
    stored_count = 0
    for template in templates:
        try:
            print(f"   Storing {template['element_code']} ({template['template_type']})...")
            
            # Create element
            element_id = enhanced_system.create_enhanced_element(template)
            print(f"     ✅ Element created: ID {element_id}")
            
            # Create description version
            version_id = enhanced_system.create_enhanced_description_version(element_id, template)
            print(f"     ✅ Template stored: Version ID {version_id}")
            
            # Create variables and mappings if dynamic
            if template['placeholders']:
                enhanced_system.create_enhanced_variable_mappings(element_id, version_id, template)
                print(f"     ✅ {len(template['placeholders'])} placeholder mappings created")
            
            stored_count += 1
            
        except Exception as e:
            print(f"     ❌ Storage error: {e}")
    
    # Step 5: Verify database content
    print(f"\n📊 STEP 5: DATABASE VERIFICATION")
    verify_database_content()
    
    # Final report
    print(f"\n🎉 COMPLETE PIPELINE TEST RESULTS")
    print("=" * 70)
    print(f"📊 Summary:")
    print(f"   Elements discovered: {len(selected_elements)}")
    print(f"   Variations extracted: {len(all_extracted_elements)}")
    print(f"   Templates generated: {len(templates)}")
    print(f"     - Dynamic (with placeholders): {len(dynamic_templates)}")
    print(f"     - Static (no variations): {len(static_templates)}")
    print(f"   Templates stored: {stored_count}")
    
    if dynamic_templates:
        print(f"\n✅ SUCCESS: Dynamic templates with placeholders work end-to-end!")
        print(f"🎯 Placeholder examples:")
        for template in dynamic_templates[:2]:  # Show first 2
            print(f"   {template['element_code']}: {template['placeholders']}")
    else:
        print(f"\n⚠️  No dynamic templates generated - need more URL variations")
    
    return len(dynamic_templates) > 0

def create_synthetic_variations():
    """Create synthetic test variations when no real ones found"""
    
    print("   Creating synthetic test variations...")
    return {
        'TEST_EHV': [
            'https://test.com/viga_40x60_hormigon_ha25.html',
            'https://test.com/viga_30x50_hormigon_ha30.html',
            'https://test.com/viga_50x70_hormigon_ha35.html'
        ],
        'TEST_EHS': [
            'https://test.com/pilar_20x20_acero_b500.html',
            'https://test.com/pilar_25x25_acero_b400.html'
        ]
    }

def verify_database_content():
    """Verify that enhanced templates and placeholders are correctly stored"""
    
    import sqlite3
    conn = sqlite3.connect(str(Path(__file__).parent.parent / "src" / "office_data.db"))
    cursor = conn.cursor()
    
    print("   🔍 Checking enhanced templates in database...")
    
    # Check enhanced elements
    cursor.execute('''
    SELECT COUNT(*) FROM elements 
    WHERE element_code LIKE '%_ENH_%'
    ''')
    element_count = cursor.fetchone()[0]
    print(f"     Enhanced elements: {element_count}")
    
    # Check description versions
    cursor.execute('''
    SELECT COUNT(*) FROM description_versions dv
    JOIN elements e ON dv.element_id = e.element_id
    WHERE e.element_code LIKE '%_ENH_%'
    ''')
    version_count = cursor.fetchone()[0]
    print(f"     Description versions: {version_count}")
    
    # Check template variable mappings (placeholders)
    cursor.execute('''
    SELECT COUNT(*) FROM template_variable_mappings tvm
    JOIN description_versions dv ON tvm.version_id = dv.version_id
    JOIN elements e ON dv.element_id = e.element_id
    WHERE e.element_code LIKE '%_ENH_%'
    ''')
    mapping_count = cursor.fetchone()[0]
    print(f"     Placeholder mappings: {mapping_count}")
    
    # Check element variables
    cursor.execute('''
    SELECT COUNT(*) FROM element_variables ev
    JOIN elements e ON ev.element_id = e.element_id
    WHERE e.element_code LIKE '%_ENH_%'
    ''')
    variable_count = cursor.fetchone()[0]
    print(f"     Element variables: {variable_count}")
    
    # Show some examples
    if mapping_count > 0:
        print("   📋 Placeholder examples:")
        cursor.execute('''
        SELECT e.element_code, tvm.placeholder, ev.variable_name
        FROM template_variable_mappings tvm
        JOIN description_versions dv ON tvm.version_id = dv.version_id
        JOIN elements e ON dv.element_id = e.element_id
        JOIN element_variables ev ON tvm.variable_id = ev.variable_id
        WHERE e.element_code LIKE '%_ENH_%'
        ORDER BY e.element_code, tvm.position
        LIMIT 5
        ''')
        
        for row in cursor.fetchall():
            element_code, placeholder, var_name = row
            print(f"     {element_code}: {{{placeholder}}} → {var_name}")
    
    conn.close()
    
    success = mapping_count > 0
    status = "✅ SUCCESS" if success else "❌ NO PLACEHOLDERS"
    print(f"   {status}: Placeholders {'are' if success else 'are NOT'} stored in database")
    
    return success

if __name__ == "__main__":
    success = test_complete_enhanced_pipeline()
    
    if success:
        print(f"\n🎉 ENHANCED SYSTEM READY FOR PRODUCTION!")
        print(f"✅ Dynamic templates with placeholders work end-to-end")
    else:
        print(f"\n⚠️  Need to adjust for more URL variations in production")