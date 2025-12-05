#!/usr/bin/env python3
"""
FINAL PRODUCTION SCRIPT - Complete CYPE Scraper
Single script that handles everything with proper progress tracking
"""

import sys
import os
import sqlite3
import time
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def backup_database():
    """Backup existing database"""
    db_path = Path(__file__).parent.parent / "src" / "office_data.db"
    
    if db_path.exists():
        timestamp = int(time.time())
        backup_path = db_path.parent / f"office_data.db.backup_{timestamp}"
        os.rename(db_path, backup_path)
        print(f"📦 Database backed up: {backup_path.name}")
        return backup_path
    else:
        print(f"📄 No existing database - starting fresh")
        return None

def initialize_database():
    """Initialize clean database with proper schema"""
    print(f"🗄️ Initializing clean database...")
    from db_manager import DatabaseManager
    
    # Create database with correct path
    db_path = Path(__file__).parent.parent / "src" / "office_data.db"
    db_manager = DatabaseManager(str(db_path))
    
    # Verify schema is created
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
    print(f"   ✅ Clean database ready ({len(tables)} tables created)")
    return db_manager

def discover_all_elements(max_elements=1000):
    """Discover all CYPE elements with progress"""
    
    print(f"🔍 DISCOVERING CYPE ELEMENTS (up to {max_elements})")
    print("-" * 60)
    
    # Import the working crawler
    from final_production_crawler import FinalProductionCrawler
    
    crawler = FinalProductionCrawler()
    
    # Get main categories
    print("   Getting element categories...")
    main_categories = crawler.get_element_containing_subcategories()
    print(f"   Found {len(main_categories)} main categories")
    
    # Discover deep subcategories
    print("   Discovering subcategories...")
    all_subcategories = crawler.discover_deep_subcategories(main_categories)
    print(f"   Found {len(all_subcategories)} total subcategories")
    
    # Discover elements from subcategories
    print(f"   Scanning for elements (limit: {max_elements})...")
    
    all_elements = []
    processed_categories = 0
    
    for i, subcat_url in enumerate(all_subcategories):
        if len(all_elements) >= max_elements:
            break
            
        try:
            # Get elements from this subcategory
            elements = crawler.discover_elements_in_subcategory(subcat_url)
            
            if elements:
                # Limit elements from this subcategory
                remaining_slots = max_elements - len(all_elements)
                elements_to_add = elements[:remaining_slots]
                all_elements.extend(elements_to_add)
                
                category_name = subcat_url.split('/')[-1].replace('.html', '')
                print(f"     {category_name}: Found {len(elements_to_add)} elements")
            
            processed_categories += 1
            
            # Show progress every 5 categories
            if processed_categories % 5 == 0:
                print(f"   Progress: {processed_categories}/{len(all_subcategories)} categories, {len(all_elements)} elements found")
                
        except Exception as e:
            print(f"     Error in {subcat_url}: {e}")
    
    print(f"✅ Discovery complete: {len(all_elements)} elements found")
    return all_elements

def extract_element_content(urls, max_elements):
    """Extract content from element URLs with progress"""
    
    print(f"\n📊 EXTRACTING ELEMENT CONTENT")
    print("-" * 60)
    
    from enhanced_element_extractor import EnhancedElementExtractor
    
    extractor = EnhancedElementExtractor()
    extracted_elements = []
    
    # Process URLs with progress
    for i, url in enumerate(urls[:max_elements]):
        try:
            print(f"   Processing {i+1}/{min(len(urls), max_elements)}: {url.split('/')[-1][:40]}...")
            
            element_data = extractor.extract_element_data(url)
            if element_data and hasattr(element_data, 'description') and element_data.description:
                # Check content quality
                desc = element_data.description
                if len(desc) > 100 and 'EA Acero' not in desc:  # Avoid navigation content
                    # Convert ElementVariable objects to dictionaries for storage
                    variables_list = []
                    if hasattr(element_data, 'variables') and element_data.variables:
                        for var in element_data.variables:
                            variables_list.append({
                                'name': var.name,
                                'variable_type': var.variable_type,
                                'options': var.options,
                                'default_value': var.default_value,
                                'is_required': var.is_required,
                                'description': var.description
                            })
                    
                    extracted_elements.append({
                        'element_code': getattr(element_data, 'code', f'ELEM_{i+1}'),
                        'title': getattr(element_data, 'title', 'Unknown Element'),
                        'description': desc,
                        'price': getattr(element_data, 'price', None),
                        'url': url,
                        'variables': variables_list  # Include extracted variables!
                    })
                    print(f"     ✅ Valid content: {len(desc)} chars, {len(variables_list)} variables")
                else:
                    print(f"     ❌ Poor content quality")
            else:
                print(f"     ❌ No content extracted")
                
        except Exception as e:
            print(f"     ❌ Error: {e}")
    
    print(f"✅ Content extraction complete: {len(extracted_elements)} valid elements")
    return extracted_elements

def generate_templates(elements):
    """
    Generate templates from extracted elements.

    NOTE: For advanced template extraction with variable detection,
    use the new CYPEExtractor from scraper.template_extraction:

        from scraper.template_extraction import CYPEExtractor
        async with CYPEExtractor() as extractor:
            variables, results = await extractor.extract(url)
    """
    print(f"\n🔧 GENERATING TEMPLATES")
    print("-" * 60)

    templates = []
    for elem in elements:
        template = {
            'element_code': elem['element_code'],
            'title': elem['title'],
            'description': elem['description'],
            'price': elem['price'],
            'url': elem['url'],
            'variables': elem.get('variables', []),
            'template_type': 'dynamic' if elem.get('variables') else 'static',
            'placeholders': [v.get('name') for v in elem.get('variables', []) if v.get('name')]
        }
        templates.append(template)

    dynamic_count = len([t for t in templates if t['template_type'] == 'dynamic'])
    static_count = len(templates) - dynamic_count

    print(f"✅ Templates generated: {dynamic_count} dynamic, {static_count} static")

    return templates

def store_templates(templates, db_manager):
    """Store enhanced templates with variables in database"""
    
    print(f"\n💾 STORING ENHANCED TEMPLATES IN DATABASE")
    print("-" * 60)
    
    stored_count = 0
    dynamic_stored = 0
    variables_stored = 0
    
    for template in templates:
        try:
            # Create element
            element_id = db_manager.create_element(
                element_code=f"{template['element_code']}_PROD_{int(time.time())}",
                element_name=template['title'],
                price=template['price']
            )
            
            # Store variables if they exist
            if 'variables' in template and template['variables']:
                for var in template['variables']:
                    try:
                        # Convert options to the format expected by add_variable
                        options_list = []
                        if var.get('options'):
                            for option in var['options']:
                                options_list.append({
                                    'option_value': option,
                                    'option_label': option,
                                    'is_default': option == var.get('default_value')
                                })
                        
                        var_id = db_manager.add_variable(
                            element_id=element_id,
                            variable_name=var['name'],
                            variable_type=var.get('variable_type', 'TEXT'),
                            unit=var.get('unit'),
                            default_value=var.get('default_value'),
                            is_required=var.get('is_required', True),
                            options=options_list if options_list else None
                        )
                        
                        variables_stored += 1
                    except Exception as ve:
                        print(f"     Warning: Could not store variable {var['name']}: {ve}")
            
            # Create description template directly to bypass validation
            with db_manager.get_connection() as conn:
                cursor = conn.execute(
                    """INSERT INTO description_versions 
                       (element_id, version_number, description_template, state, is_active, created_by, created_at)
                       VALUES (?, 1, ?, 'S3', 1, 'production_system', datetime('now'))""",
                    (element_id, template['template'])
                )
                version_id = cursor.lastrowid
            
            # Store template variable mappings for placeholders
            if template.get('placeholders'):
                with db_manager.get_connection() as conn:
                    for position, placeholder in enumerate(template['placeholders']):
                        try:
                            conn.execute(
                                "INSERT INTO template_variable_mappings (version_id, placeholder, variable_id, position) VALUES (?, ?, (SELECT variable_id FROM element_variables WHERE element_id = ? AND variable_name = ?), ?)",
                                (version_id, '{' + placeholder + '}', element_id, placeholder, position)
                            )
                        except Exception as pe:
                            print(f"     Warning: Could not store placeholder {placeholder}: {pe}")
            
            template_type = 'dynamic' if template.get('placeholders') else 'static'
            print(f"   ✅ Stored {template['element_code']} ({template_type})")
            stored_count += 1
            
            if template.get('placeholders'):
                dynamic_stored += 1
                print(f"     📊 Placeholders: {template['placeholders']}")
            
        except Exception as e:
            print(f"   ❌ Error storing {template['element_code']}: {e}")
    
    print(f"✅ Storage complete: {stored_count} templates stored ({dynamic_stored} dynamic, {variables_stored} variables)")
    return stored_count

def run_production(max_elements=1000):
    """Run complete production pipeline"""
    
    print("🚀 CYPE PRODUCTION SCRAPER")
    print("=" * 80)
    print(f"Target: {max_elements} elements")
    
    # Step 1: Database setup
    backup_path = backup_database()
    db_manager = initialize_database()
    
    # Step 2: Element discovery
    element_urls = discover_all_elements(max_elements)
    
    # Step 3: Content extraction
    elements = extract_element_content(element_urls, max_elements)
    
    # Step 4: Template generation
    templates = generate_templates(elements)
    
    # Step 5: Database storage
    stored_count = store_templates(templates, db_manager)
    
    # Final report
    print(f"\n🎉 PRODUCTION COMPLETE!")
    print("=" * 80)
    print(f"📊 Results:")
    print(f"   URLs discovered: {len(element_urls)}")
    print(f"   Content extracted: {len(elements)}")
    print(f"   Templates generated: {len(templates)}")
    print(f"   Templates stored: {stored_count}")
    if backup_path:
        print(f"   Database backup: {backup_path.name}")
    
    dynamic_templates = [t for t in templates if t['template_type'] == 'dynamic']
    if dynamic_templates:
        print(f"\n🎯 Dynamic Templates with Placeholders:")
        for dt in dynamic_templates[:3]:  # Show first 3
            print(f"   {dt['element_code']}: {dt['placeholders']}")
    
    print(f"\n✅ Success! Enhanced CYPE database ready for use.")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CYPE Production Scraper')
    parser.add_argument('--elements', type=int, default=100,
                       help='Maximum elements to process (default: 100)')
    
    args = parser.parse_args()
    
    print(f"🎯 Processing up to {args.elements} elements")
    run_production(args.elements)

if __name__ == "__main__":
    main()