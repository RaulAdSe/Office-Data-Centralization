#!/usr/bin/env python3
"""
End-to-end test with comprehensive logging: Discovery → Extraction → Database Storage
"""

import sys
import logging
import json
from pathlib import Path
from datetime import datetime
import time

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "core"))
sys.path.insert(0, str(Path(__file__).parent / "template_extraction"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enhanced_element_extractor import EnhancedElementExtractor
from smart_template_extractor import SmartTemplateExtractor
from db_manager import DatabaseManager

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
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    return str(progress_file)

def test_end_to_end_logged():
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
        # Step 1: Discovery
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
        
        # Process each element
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
            
            element_result = {
                "index": i+1,
                "url": url,
                "name": element_name,
                "start_time": datetime.now().isoformat(),
                "status": "processing"
            }
            
            try:
                # Step 2a: Extract element data
                log_progress("Extracting element data...")
                extraction_start = time.time()
                element = element_extractor.extract_element_data(url)
                
                if not element:
                    raise Exception("Failed to extract element data")
                
                extraction_time = time.time() - extraction_start
                log_progress(f"Extracted: {element.code} - {element.title}", "success")
                log_progress(f"Price: {element.price}€, Variables: {len(element.variables)}, Time: {extraction_time:.2f}s")
                
                element_result.update({
                    "extraction_time": extraction_time,
                    "element_code": element.code,
                    "element_title": element.title,
                    "price": element.price,
                    "variables_count": len(element.variables)
                })
                
                # Step 2b: Generate template
                log_progress("Generating template...")
                template_start = time.time()
                template_text = template_extractor.get_static_description(url)
                template_time = time.time() - template_start
                log_progress(f"Template generated: {len(template_text)} characters, Time: {template_time:.2f}s", "success")
                
                element_result.update({
                    "template_time": template_time,
                    "template_length": len(template_text)
                })
                
                # Step 2c: Store in database
                log_progress("Storing in database...")
                storage_start = time.time()
                
                # Create unique element code
                timestamp = int(time.time())
                element_code = f"{element.code}_E2E_{timestamp}_{i+1}"
                
                # Store element with price
                element_id = db_manager.create_element(
                    element_code=element_code,
                    element_name=element.title,
                    price=element.price,
                    created_by='End_To_End_Test_Logged'
                )
                
                log_progress(f"Element stored with ID: {element_id}", "success")
                
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
                
                # Store template
                description_version_id = db_manager.create_proposal(
                    element_id=element_id,
                    description_template=template_text,
                    created_by='End_To_End_Test_Logged'
                )
                
                storage_time = time.time() - storage_start
                log_progress(f"Storage complete: {vars_stored} vars, {options_stored} options, template ID {description_version_id}", "success")
                log_progress(f"Storage time: {storage_time:.2f}s")
                
                # Update result
                element_result.update({
                    "storage_time": storage_time,
                    "element_id": element_id,
                    "element_code": element_code,
                    "variables_stored": vars_stored,
                    "options_stored": options_stored,
                    "template_id": description_version_id,
                    "status": "completed",
                    "end_time": datetime.now().isoformat(),
                    "total_time": time.time() - time.mktime(datetime.fromisoformat(element_result["start_time"]).timetuple())
                })
                
                progress_data["elements_processed"] += 1
                log_progress(f"Element {i+1} completed successfully! Total time: {element_result['total_time']:.2f}s", "success")
                
            except Exception as e:
                error_msg = str(e)
                log_progress(f"Error processing element {i+1}: {error_msg}", "error")
                
                element_result.update({
                    "status": "failed",
                    "error": error_msg,
                    "end_time": datetime.now().isoformat()
                })
                
                progress_data["elements_failed"] += 1
                progress_data["errors"].append({
                    "element_index": i+1,
                    "url": url,
                    "error": error_msg,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Add to results
            progress_data["results"].append(element_result)
            
            # Save progress after each element
            save_progress_json(progress_data)
        
        # Final verification
        log_progress("FINAL VERIFICATION", "section")
        progress_data["phase"] = "verification"
        
        if progress_data["elements_processed"] > 0:
            log_progress(f"Successfully processed {progress_data['elements_processed']} elements", "success")
            
            # Show summary
            total_extraction_time = sum(r.get("extraction_time", 0) for r in progress_data["results"])
            total_storage_time = sum(r.get("storage_time", 0) for r in progress_data["results"])
            
            log_progress(f"Total extraction time: {total_extraction_time:.2f}s")
            log_progress(f"Total storage time: {total_storage_time:.2f}s")
            
            for result in progress_data["results"]:
                if result["status"] == "completed":
                    log_progress(f"✅ {result['element_code']}: {result['price']}€, {result['variables_stored']} vars")
                else:
                    log_progress(f"❌ {result['name']}: {result.get('error', 'Unknown error')}")
        
        # Final summary
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        progress_data.update({
            "phase": "completed",
            "end_time": end_time.isoformat(),
            "total_time": total_time,
            "success_rate": progress_data["elements_processed"] / progress_data["elements_discovered"] * 100
        })
        
        save_progress_json(progress_data)
        
        log_progress("END-TO-END TEST COMPLETE", "section")
        log_progress(f"Total time: {total_time:.2f}s", "success")
        log_progress(f"Success rate: {progress_data['success_rate']:.1f}%", "success")
        log_progress("Pipeline ready for full deployment!", "success")
        
    except Exception as e:
        log_progress(f"Critical error in pipeline: {e}", "error")
        progress_data.update({
            "phase": "failed",
            "critical_error": str(e),
            "end_time": datetime.now().isoformat()
        })
        save_progress_json(progress_data)
        raise

def clean_database():
    """Clean the database before running the test"""
    
    print("🧹 CLEANING DATABASE")
    print("=" * 40)
    
    db_path = str(Path(__file__).parent.parent / "src" / "office_data.db")
    
    # Backup current database
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        
        # Recreate fresh database
        if Path(db_path).exists():
            Path(db_path).unlink()
            print(f"✅ Removed old database: {db_path}")
        
        # Initialize fresh database
        db_manager = DatabaseManager(db_path)
        print(f"✅ Created fresh database: {db_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning database: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    # Check if clean flag is provided
    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        if clean_database():
            print("\n" + "="*60)
            test_end_to_end_logged()
        else:
            print("❌ Database cleanup failed. Exiting.")
            sys.exit(1)
    else:
        test_end_to_end_logged()