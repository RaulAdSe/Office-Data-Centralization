#!/usr/bin/env python3
"""
FULL PRODUCTION PIPELINE: Discover ALL CYPE elements and process them
This script will discover 694+ elements and extract/store all of them
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

from final_production_crawler import FinalProductionCrawler
from enhanced_element_extractor import EnhancedElementExtractor
from smart_template_extractor import SmartTemplateExtractor
from db_manager import DatabaseManager

def setup_logging():
    """Setup comprehensive logging for production run"""
    
    # Create logs directory
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Setup log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"full_production_{timestamp}.log"
    
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
        print(f"\n{'='*20} {message} {'='*20}")

def save_progress_json(data, filename="production_progress.json"):
    """Save progress data to JSON for monitoring"""
    progress_file = Path(__file__).parent / "logs" / filename
    progress_file.parent.mkdir(exist_ok=True)
    
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    return str(progress_file)

def run_full_production():
    """Run the complete production pipeline on ALL elements"""
    
    # Setup logging
    log_file = setup_logging()
    
    log_progress("🚀 FULL PRODUCTION PIPELINE STARTED", "section")
    log_progress("Discovering ALL CYPE elements + Extraction + Database Storage")
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
        "performance": {
            "avg_extraction_time": 0,
            "avg_storage_time": 0,
            "total_extraction_time": 0,
            "total_storage_time": 0,
            "elements_per_minute": 0
        }
    }
    
    try:
        # Initialize components
        log_progress("Initializing pipeline components...")
        crawler = FinalProductionCrawler(delay=1.0, max_workers=3)
        element_extractor = EnhancedElementExtractor()
        template_extractor = SmartTemplateExtractor()
        db_path = str(Path(__file__).parent.parent / "src" / "office_data.db")
        db_manager = DatabaseManager(db_path)
        log_progress("Components initialized", "success")
        
        # Save initial progress
        progress_file = save_progress_json(progress_data)
        log_progress(f"Progress file: {progress_file}")
        
        # Phase 1: Discovery
        log_progress("PHASE 1: DISCOVERING ALL CYPE ELEMENTS", "section")
        progress_data["phase"] = "discovery"
        save_progress_json(progress_data)
        
        discovery_start = time.time()
        discovered_urls = crawler.crawl_all_elements()
        discovery_time = time.time() - discovery_start
        
        progress_data["elements_discovered"] = len(discovered_urls)
        progress_data["discovery_time"] = discovery_time
        
        log_progress(f"Discovery complete! Found {len(discovered_urls)} elements", "success")
        log_progress(f"Discovery took {discovery_time:.1f} seconds")
        
        if len(discovered_urls) == 0:
            raise Exception("No elements discovered! Check crawler configuration.")
        
        # Export discovery results
        discovery_file = Path(__file__).parent / "logs" / f"discovered_elements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        crawler.export_elements(str(discovery_file))
        log_progress(f"Discovery results exported to: {discovery_file}")
        
        # Phase 2: Processing ALL elements
        log_progress(f"PHASE 2: PROCESSING {len(discovered_urls)} ELEMENTS", "section")
        progress_data["phase"] = "processing"
        save_progress_json(progress_data)
        
        processing_start = time.time()
        
        for i, url in enumerate(discovered_urls):
            element_name = url.split('/')[-1].replace('_', ' ').replace('.html', '')
            
            log_progress(f"Processing {i+1}/{len(discovered_urls)}: {element_name}")
            progress_data["current_element"] = {
                "index": i+1,
                "total": len(discovered_urls),
                "url": url,
                "name": element_name,
                "start_time": datetime.now().isoformat()
            }
            
            # Update progress every 10 elements
            if i % 10 == 0:
                save_progress_json(progress_data)
                
                # Calculate performance metrics
                elapsed = time.time() - processing_start
                if i > 0:
                    progress_data["performance"]["elements_per_minute"] = (i / elapsed) * 60
                    log_progress(f"Performance: {progress_data['performance']['elements_per_minute']:.1f} elements/minute")
            
            try:
                # Extract element data
                extraction_start = time.time()
                element = element_extractor.extract_element_data(url)
                
                if not element:
                    raise Exception("Failed to extract element data")
                
                extraction_time = time.time() - extraction_start
                progress_data["performance"]["total_extraction_time"] += extraction_time
                
                # Generate template
                template_start = time.time()
                template_text = template_extractor.get_static_description(url)
                template_time = time.time() - template_start
                
                # Store in database
                storage_start = time.time()
                
                # Create unique element code
                timestamp = int(time.time())
                element_code = f"{element.code}_PROD_{timestamp}_{i+1}"
                
                # Store element with price
                element_id = db_manager.create_element(
                    element_code=element_code,
                    element_name=element.title,
                    price=element.price,
                    created_by='Full_Production_Pipeline'
                )
                
                # Store variables (limit to first 15 for performance)
                vars_stored = 0
                options_stored = 0
                
                for var in element.variables[:15]:
                    variable_id = db_manager.add_variable(
                        element_id=element_id,
                        variable_name=var.name,
                        variable_type='TEXT',
                        default_value=var.default_value,
                        is_required=False
                    )
                    
                    vars_stored += 1
                    
                    # Add options
                    for j, option in enumerate(var.options[:10]):  # Limit options too
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
                    created_by='Full_Production_Pipeline'
                )
                
                storage_time = time.time() - storage_start
                progress_data["performance"]["total_storage_time"] += storage_time
                
                progress_data["elements_processed"] += 1
                
                # Log every 50 elements or show key info every 10
                if i % 50 == 0 or i < 10:
                    log_progress(f"✅ {element_code}: {element.price}€, {vars_stored} vars, {len(template_text)} chars", "success")
                
            except Exception as e:
                error_msg = str(e)
                log_progress(f"❌ Element {i+1} failed: {error_msg}", "error")
                
                progress_data["elements_failed"] += 1
                progress_data["errors"].append({
                    "element_index": i+1,
                    "url": url,
                    "error": error_msg,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Continue with next element
                continue
        
        # Final results
        processing_time = time.time() - processing_start
        total_time = time.time() - time.mktime(start_time.timetuple())
        
        log_progress("PRODUCTION PIPELINE COMPLETE", "section")
        progress_data["phase"] = "completed"
        progress_data["end_time"] = datetime.now().isoformat()
        progress_data["total_time"] = total_time
        progress_data["processing_time"] = processing_time
        progress_data["success_rate"] = (progress_data["elements_processed"] / progress_data["elements_discovered"]) * 100
        
        # Calculate final performance metrics
        if progress_data["elements_processed"] > 0:
            progress_data["performance"]["avg_extraction_time"] = progress_data["performance"]["total_extraction_time"] / progress_data["elements_processed"]
            progress_data["performance"]["avg_storage_time"] = progress_data["performance"]["total_storage_time"] / progress_data["elements_processed"]
            progress_data["performance"]["final_elements_per_minute"] = (progress_data["elements_processed"] / processing_time) * 60
        
        # Final summary
        log_progress(f"🎉 FINAL RESULTS:", "section")
        log_progress(f"Elements discovered: {progress_data['elements_discovered']}", "success")
        log_progress(f"Elements processed: {progress_data['elements_processed']}", "success")
        log_progress(f"Elements failed: {progress_data['elements_failed']}")
        log_progress(f"Success rate: {progress_data['success_rate']:.1f}%", "success")
        log_progress(f"Total time: {total_time:.1f} seconds", "success")
        log_progress(f"Processing time: {processing_time:.1f} seconds")
        log_progress(f"Average processing: {progress_data['performance']['final_elements_per_minute']:.1f} elements/minute", "success")
        
        if progress_data["elements_failed"] > 0:
            log_progress(f"⚠️ {progress_data['elements_failed']} elements failed - check errors in progress file")
        
        save_progress_json(progress_data)
        log_progress(f"Complete results saved to: {progress_file}", "success")
        
    except Exception as e:
        log_progress(f"Critical error in production pipeline: {e}", "error")
        progress_data.update({
            "phase": "failed",
            "critical_error": str(e),
            "end_time": datetime.now().isoformat()
        })
        save_progress_json(progress_data)
        raise

def clean_database():
    """Clean the database before production run"""
    
    print("🧹 CLEANING DATABASE FOR PRODUCTION RUN")
    print("=" * 50)
    
    db_path = str(Path(__file__).parent.parent / "src" / "office_data.db")
    
    # Backup current database
    backup_path = f"{db_path}.backup_production_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        import shutil
        if Path(db_path).exists():
            shutil.copy2(db_path, backup_path)
            print(f"✅ Database backed up to: {backup_path}")
            
            # Remove old database
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
    
    print("🚀 FULL PRODUCTION PIPELINE")
    print("This will discover and process ALL CYPE elements (694+)")
    print("Estimated time: 30-60 minutes")
    print("=" * 60)
    
    # Check if clean flag is provided
    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        if clean_database():
            print("\n" + "="*60)
            print("🚀 STARTING FULL PRODUCTION RUN...")
            print("="*60)
            run_full_production()
        else:
            print("❌ Database cleanup failed. Exiting.")
            sys.exit(1)
    elif len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("\nUsage:")
        print("  python3 run_full_production_pipeline.py --clean    # Clean database and run")
        print("  python3 run_full_production_pipeline.py           # Run with existing database")
        print("\nRecommended: Use --clean for production run")
    else:
        # Ask for confirmation
        response = input("⚠️  Are you sure you want to process ALL elements? (y/N): ")
        if response.lower() == 'y':
            run_full_production()
        else:
            print("Operation cancelled.")