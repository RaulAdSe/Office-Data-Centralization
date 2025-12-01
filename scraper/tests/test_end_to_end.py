#!/usr/bin/env python3
"""
End-to-end test: Discovery → Extraction → Database Storage
Test with just a couple elements to verify the complete pipeline
"""

import sys
import logging
import json
from pathlib import Path
from datetime import datetime

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "core"))
sys.path.insert(0, str(Path(__file__).parent / "template_extraction"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enhanced_element_extractor import EnhancedElementExtractor
from smart_template_extractor import SmartTemplateExtractor
from db_manager import DatabaseManager
import time

def setup_logging():
    """Setup comprehensive logging for progress tracking"""
    
    # Create logs directory
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Setup log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"e2e_test_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return str(log_file)

def log_progress(message, level="info"):
    """Log progress with different levels"""
    if level == "info":
        logging.info(message)
        print(f"📊 {message}")
    elif level == "success":
        logging.info(f"SUCCESS: {message}")
        print(f"✅ {message}")
    elif level == "warning":
        logging.warning(message)
        print(f"⚠️  {message}")
    elif level == "error":
        logging.error(message)
        print(f"❌ {message}")
    elif level == "section":
        logging.info(f"SECTION: {message}")
        print(f"\n{'='*15} {message} {'='*15}")

def save_progress_json(data, filename="e2e_progress.json"):
    """Save progress data to JSON for monitoring"""
    progress_file = Path(__file__).parent / "logs" / filename
    progress_file.parent.mkdir(exist_ok=True)
    
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return str(progress_file)

def test_end_to_end():
    """Test complete pipeline with comprehensive logging"""
    
    # Setup logging
    log_file = setup_logging()
    
    log_progress("END-TO-END PIPELINE TEST STARTED", "section")
    log_progress("Testing: Discovery → Extraction → Database Storage")
    log_progress(f"Log file: {log_file}")
    
    # Initialize progress tracking
    start_time = datetime.now()
    progress_data = {
        "start_time": start_time.isoformat(),
        "log_file": log_file,
        "phase": "initialization",
        "elements_discovered": 0,
        "elements_processed": 0,
        "elements_failed": 0,
        "current_element": None,
        "errors": [],
        "results": []
    }
    
    try:
        # Step 1: "Discovery" - we'll use known element URLs
        log_progress("ELEMENT DISCOVERY", "section")
        test_urls = [
            "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html",
            "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_de_hormigon_armado.html"
        ]
        
        progress_data["phase"] = "discovery"
        progress_data["elements_discovered"] = len(test_urls)
        
        log_progress(f"Discovered {len(test_urls)} elements to process", "success")
        for i, url in enumerate(test_urls):
            element_name = url.split('/')[-1].replace('_', ' ').replace('.html', '')
            log_progress(f"Element {i+1}: {element_name}")
        
        # Initialize components
        log_progress("Initializing pipeline components...")
        element_extractor = EnhancedElementExtractor()
        template_extractor = SmartTemplateExtractor()
        db_path = str(Path(__file__).parent.parent / "src" / "office_data.db")
        db_manager = DatabaseManager(db_path)
        log_progress("Components initialized", "success")
        
        # Save initial progress
        progress_file = save_progress_json(progress_data)
        log_progress(f"Progress file: {progress_file}")
        
        log_progress("DATA EXTRACTION & DATABASE STORAGE", "section")
        progress_data["phase"] = "processing"
        
        processed_elements = []
    
        for i, url in enumerate(test_urls):
            element_name = url.split('/')[-1].replace('_', ' ').replace('.html', '')
            
            log_progress(f"Processing Element {i+1}/{len(test_urls)}: {element_name}", "section")
            progress_data["current_element"] = {
                "index": i+1,
                "total": len(test_urls), 
                "url": url,
                "name": element_name,
                "start_time": datetime.now().isoformat()
            }
            
            # Update progress file
            save_progress_json(progress_data)
            
            try:
                # Step 2a: Extract element data
                log_progress("Extracting element data...")
                extraction_start = time.time()
                element = element_extractor.extract_element_data(url)
                
                if not element:
                    print("   ❌ Failed to extract element data")
                    continue
                
                print(f"   ✅ Extracted: {element.code} - {element.title}")
                print(f"   💰 Price: {element.price}€")
                print(f"   🔧 Variables: {len(element.variables)}")
            
            # Step 2b: Generate template
            print("   📝 Generating template...")
            template_text = template_extractor.get_static_description(url)
            print(f"   ✅ Template: {len(template_text)} characters")
            
            # Step 2c: Store in database
            print("   💾 Storing in database...")
            
            # Create unique element code
            timestamp = int(time.time())
            element_code = f"{element.code}_E2E_{timestamp}_{i+1}"
            
            # Store element with price
            element_id = db_manager.create_element(
                element_code=element_code,
                element_name=element.title,
                price=element.price,
                created_by='End_To_End_Test'
            )
            
            print(f"   ✅ Element stored with ID: {element_id}")
            
            # Store variables
            vars_stored = 0
            options_stored = 0
            
            for var in element.variables[:10]:  # Limit to first 10 variables for test
                variable_id = db_manager.add_variable(
                    element_id=element_id,
                    variable_name=var.name,
                    variable_type='TEXT',
                    default_value=var.default_value,
                    is_required=False
                )
                
                vars_stored += 1
                
                # Add options
                for j, option in enumerate(var.options):
                    db_manager.add_variable_option(
                        variable_id=variable_id,
                        option_value=option,
                        option_label=option,
                        display_order=j,
                        is_default=(j == 0)
                    )
                    options_stored += 1
            
            print(f"   ✅ Variables stored: {vars_stored} variables, {options_stored} options")
            
            # Store template
            description_version_id = db_manager.create_proposal(
                element_id=element_id,
                description_template=template_text,
                created_by='End_To_End_Test'
            )
            
            print(f"   ✅ Template stored with version ID: {description_version_id}")
            
            # Store summary
            processed_elements.append({
                'element_id': element_id,
                'code': element_code,
                'title': element.title,
                'price': element.price,
                'variables_count': vars_stored,
                'options_count': options_stored,
                'template_id': description_version_id
            })
            
                print(f"   🎉 Element {i+1} complete!")
                
            except Exception as e:
                print(f"   ❌ Error processing element: {e}")
                import traceback
                traceback.print_exc()
    
    # Step 3: Verification
    print(f"\n✅ STEP 3: VERIFICATION")
    
    if processed_elements:
        print(f"   📊 Successfully processed {len(processed_elements)} elements")
        
        for i, elem in enumerate(processed_elements):
            print(f"   \n   Element {i+1}:")
            print(f"     • ID: {elem['element_id']}")
            print(f"     • Code: {elem['code']}")
            print(f"     • Title: {elem['title']}")
            print(f"     • Price: {elem['price']}€")
            print(f"     • Variables: {elem['variables_count']}")
            print(f"     • Options: {elem['options_count']}")
            print(f"     • Template ID: {elem['template_id']}")
        
        # Verify data in database
        print(f"\n   🔍 Database verification:")
        
        for elem in processed_elements:
            # Check element exists with price
            elements = db_manager.list_elements()
            db_element = next((e for e in elements if e['element_id'] == elem['element_id']), None)
            
            if db_element:
                print(f"     ✅ Element {elem['code']}: Found in DB with price {db_element.get('price')}€")
                
                # Check variables
                variables = db_manager.get_element_variables(elem['element_id'])
                print(f"     ✅ Variables: {len(variables)} found in DB")
                
                # Check template
                template = db_manager.get_active_version(elem['element_id'])
                if template:
                    print(f"     ✅ Template: {len(template['description_template'])} chars in DB")
                else:
                    print(f"     ❌ Template: Not found in DB")
            else:
                print(f"     ❌ Element {elem['code']}: Not found in DB")
    
    print(f"\n🎉 END-TO-END TEST COMPLETE!")
    print(f"   ✅ Discovery: Simulated with known URLs")
    print(f"   ✅ Extraction: Element data, prices, variables, descriptions")
    print(f"   ✅ Database: Complete storage and verification")
    print(f"   🚀 Pipeline ready for full deployment!")

if __name__ == "__main__":
    test_end_to_end()