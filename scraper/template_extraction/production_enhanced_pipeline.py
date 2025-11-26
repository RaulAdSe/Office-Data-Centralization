#!/usr/bin/env python3
"""
Production Enhanced Pipeline - Integrates Enhanced Template System 
with Working Production URLs to ensure end-to-end placeholders
"""

import sys
from pathlib import Path
import time

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enhanced_template_system import EnhancedTemplateSystem
from production_base_system import ProductionDynamicTemplateSystem

class ProductionEnhancedPipeline:
    """Production pipeline with enhanced template generation"""
    
    def __init__(self, db_path=None):
        db_path = db_path or str(Path(__file__).parent.parent.parent / "src" / "office_data.db")
        self.enhanced_system = EnhancedTemplateSystem(db_path)
        self.prod_system = ProductionDynamicTemplateSystem(db_path)
        
    def run_production_enhanced(self, max_elements=5):
        """Run production pipeline with enhanced template generation"""
        
        print("🚀 PRODUCTION ENHANCED PIPELINE")
        print("=" * 70)
        print(f"Target: {max_elements} elements with enhanced templates")
        
        # Step 1: Use working production discovery 
        print(f"\n📊 STEP 1: PRODUCTION ELEMENT DISCOVERY")
        all_urls = self.prod_system.discover_element_urls(50)
        element_groups = self.prod_system.group_urls_by_element_code(all_urls)
        
        # Step 2: Extract content using production methods (that work!)
        print(f"\n📊 STEP 2: PRODUCTION CONTENT EXTRACTION")
        production_elements = []
        
        # Get multi-URL elements first (for dynamic templates)
        multi_url_elements = element_groups.get('multi_url', {})
        single_url_elements = element_groups.get('single_url', {})
        
        processed_count = 0
        
        # Process multi-URL elements (these will create dynamic templates)
        for element_code, urls in list(multi_url_elements.items()):
            if processed_count >= max_elements:
                break
                
            print(f"   Processing {element_code} ({len(urls)} variations)...")
            
            # Extract descriptions using production system (proven to work)
            element_variations = []
            for i, url in enumerate(urls[:3], 1):  # Max 3 variations
                try:
                    element_data = self.prod_system.extract_full_element_data(url)
                    if element_data:
                        # Convert to enhanced format
                        enhanced_data = {
                            'element_code': element_code,
                            'title': element_data.get('title', f'Element {element_code}'),
                            'description': element_data.get('description', ''),
                            'price': element_data.get('price'),
                            'variables': [],  # Will be populated if needed
                            'url': url
                        }
                        
                        # Only add if we got a valid description
                        if enhanced_data['description'] and len(enhanced_data['description']) > 100:
                            # Check if it's technical content
                            if self.enhanced_system.is_valid_technical_description(enhanced_data['description']):
                                element_variations.append(enhanced_data)
                                print(f"     ✅ Variation {i}: {len(enhanced_data['description'])} chars")
                            else:
                                print(f"     ❌ Variation {i}: Navigation content detected")
                        else:
                            print(f"     ❌ Variation {i}: No valid description")
                            
                except Exception as e:
                    print(f"     ❌ Variation {i}: Error - {e}")
            
            # Add all valid variations
            if element_variations:
                production_elements.extend(element_variations)
                print(f"   ✅ Added {len(element_variations)} variations for {element_code}")
            else:
                print(f"   ❌ No valid variations for {element_code}")
            
            processed_count += 1
        
        # Add some single-URL elements if we need more
        for element_code, urls in list(single_url_elements.items()):
            if processed_count >= max_elements or len(production_elements) >= max_elements * 2:
                break
                
            url = urls[0]
            try:
                element_data = self.prod_system.extract_full_element_data(url)
                if element_data and element_data.get('description'):
                    enhanced_data = {
                        'element_code': element_code,
                        'title': element_data.get('title', f'Element {element_code}'),
                        'description': element_data['description'],
                        'price': element_data.get('price'),
                        'variables': [],
                        'url': url
                    }
                    
                    if (len(enhanced_data['description']) > 100 and 
                        self.enhanced_system.is_valid_technical_description(enhanced_data['description'])):
                        production_elements.append(enhanced_data)
                        print(f"   ✅ Single element {element_code}: {len(enhanced_data['description'])} chars")
            except Exception as e:
                print(f"   ❌ Single element {element_code}: Error - {e}")
            
            processed_count += 1
        
        print(f"   ✅ Total extracted: {len(production_elements)} element variations")
        
        # Step 3: Enhanced template generation
        print(f"\n📊 STEP 3: ENHANCED TEMPLATE GENERATION")
        grouped = self.enhanced_system.group_elements_by_code(production_elements)
        templates = self.enhanced_system.generate_enhanced_templates(grouped)
        
        print(f"   Generated {len(templates)} templates:")
        
        dynamic_count = 0
        static_count = 0
        
        for template in templates:
            if template['template_type'] == 'dynamic':
                dynamic_count += 1
                print(f"   🔧 {template['element_code']}: DYNAMIC ({len(template['placeholders'])} placeholders)")
                for ph in template['placeholders']:
                    print(f"      - {{{ph}}}")
            else:
                static_count += 1
                print(f"   📄 {template['element_code']}: STATIC")
        
        # Step 4: Database storage with enhanced system
        print(f"\n📊 STEP 4: ENHANCED DATABASE STORAGE")
        
        stored_templates = 0
        stored_placeholders = 0
        
        for template in templates:
            try:
                # Use enhanced storage methods
                element_id = self.enhanced_system.create_enhanced_element(template)
                version_id = self.enhanced_system.create_enhanced_description_version(element_id, template)
                
                if template['placeholders']:
                    self.enhanced_system.create_enhanced_variable_mappings(element_id, version_id, template)
                    stored_placeholders += len(template['placeholders'])
                    print(f"   ✅ {template['element_code']}: {len(template['placeholders'])} placeholders stored")
                else:
                    print(f"   📄 {template['element_code']}: static template stored")
                
                stored_templates += 1
                
            except Exception as e:
                print(f"   ❌ {template['element_code']}: Storage error - {e}")
        
        # Step 5: Verification
        print(f"\n📊 STEP 5: VERIFICATION")
        self.verify_enhanced_results()
        
        # Final report
        print(f"\n🎉 PRODUCTION ENHANCED PIPELINE COMPLETE")
        print("=" * 70)
        print(f"📊 Final Results:")
        print(f"   Elements processed: {len(grouped)}")
        print(f"   Variations extracted: {len(production_elements)}")
        print(f"   Templates generated: {len(templates)}")
        print(f"     - Dynamic (with placeholders): {dynamic_count}")
        print(f"     - Static (no variations): {static_count}")
        print(f"   Templates stored: {stored_templates}")
        print(f"   Total placeholders: {stored_placeholders}")
        
        success = dynamic_count > 0 and stored_placeholders > 0
        if success:
            print(f"\n✅ SUCCESS: Enhanced system works end-to-end in production!")
            print(f"🎯 Dynamic templates with placeholders are fully operational")
        else:
            print(f"\n⚠️  Need more element variations for dynamic templates")
        
        return {
            'success': success,
            'dynamic_templates': dynamic_count,
            'total_placeholders': stored_placeholders,
            'templates_stored': stored_templates
        }
    
    def verify_enhanced_results(self):
        """Verify that enhanced templates are working correctly"""
        
        import sqlite3
        conn = sqlite3.connect(str(Path(__file__).parent.parent / "src" / "office_data.db"))
        cursor = conn.cursor()
        
        # Check latest enhanced results
        cursor.execute('''
        SELECT e.element_code, dv.description_template,
               (SELECT COUNT(*) FROM template_variable_mappings tvm WHERE tvm.version_id = dv.version_id) as placeholder_count
        FROM description_versions dv
        JOIN elements e ON dv.element_id = e.element_id
        WHERE e.element_code LIKE '%_ENH_%'
        ORDER BY dv.created_at DESC LIMIT 5
        ''')
        
        results = cursor.fetchall()
        
        print("   🔍 Latest enhanced templates:")
        dynamic_found = False
        
        for code, template, placeholder_count in results:
            template_preview = template[:80] + "..." if len(template) > 80 else template
            
            if placeholder_count > 0:
                dynamic_found = True
                print(f"   🔧 {code}: {placeholder_count} placeholders")
                print(f"      Template: {template_preview}")
                
                # Show the placeholders
                cursor.execute('''
                SELECT tvm.placeholder, ev.variable_name
                FROM template_variable_mappings tvm
                JOIN description_versions dv ON tvm.version_id = dv.version_id
                JOIN elements e ON dv.element_id = e.element_id
                JOIN element_variables ev ON tvm.variable_id = ev.variable_id
                WHERE e.element_code = ?
                ORDER BY tvm.position
                ''', (code,))
                
                placeholders = cursor.fetchall()
                for placeholder, var_name in placeholders:
                    print(f"      - {{{placeholder}}} → {var_name}")
            else:
                print(f"   📄 {code}: static template")
                print(f"      Template: {template_preview}")
        
        conn.close()
        
        status = "✅ DYNAMIC TEMPLATES WORKING" if dynamic_found else "⚠️  Only static templates found"
        print(f"   {status}")
        
        return dynamic_found

def main():
    """Run production enhanced pipeline"""
    
    pipeline = ProductionEnhancedPipeline()
    results = pipeline.run_production_enhanced(max_elements=5)
    
    if results['success']:
        print(f"\n🚀 READY FOR PRODUCTION!")
        print(f"✅ Enhanced template system with placeholders is fully operational")
        print(f"📊 Generated {results['dynamic_templates']} dynamic templates")
        print(f"🎯 Created {results['total_placeholders']} placeholders total")
    else:
        print(f"\n🔧 System needs adjustment for more dynamic content")

if __name__ == "__main__":
    main()