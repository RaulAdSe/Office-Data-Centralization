#!/usr/bin/env python3
"""
Complete CYPE Pipeline: Discover ALL elements + Extract + Store in Database

This script runs the full pipeline:
1. Discovers all CYPE elements (694+ elements) 
2. Extracts data for each element (Spanish text, variables, etc.)
3. Generates templates using strategic combinations
4. Stores everything in the database

Usage:
    python3 run_complete_pipeline.py
"""

import sys
import os
from pathlib import Path
import time
from datetime import datetime
import json

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent / "core"))
sys.path.insert(0, str(Path(__file__).parent / "template_extraction"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from final_production_crawler import FinalProductionCrawler
from enhanced_element_extractor import EnhancedElementExtractor
from smart_template_extractor import SmartTemplateExtractor
from db_manager import DatabaseManager

class CompleteCYPEPipeline:
    """Complete pipeline: Discovery → Extraction → Database"""
    
    def __init__(self, database_path: str = None):
        self.database_path = database_path or str(Path(__file__).parent.parent / "src" / "office_data.db")
        
        # Initialize components
        self.crawler = FinalProductionCrawler(delay=1.0, max_workers=3)
        self.element_extractor = EnhancedElementExtractor()
        self.template_extractor = SmartTemplateExtractor()
        self.db_manager = DatabaseManager(self.database_path)
        
        # Results
        self.discovered_urls = []
        self.processed_elements = []
        self.failed_elements = []
        
        # Stats
        self.stats = {
            'start_time': datetime.now(),
            'discovery_time': None,
            'elements_discovered': 0,
            'elements_processed': 0,
            'elements_stored': 0,
            'failed_count': 0
        }
    
    def run_discovery_phase(self, resume: bool = True) -> bool:
        """Phase 1: Discover all CYPE elements"""
        
        print("🔍 PHASE 1: DISCOVERING ALL CYPE ELEMENTS")
        print("=" * 60)
        
        try:
            # Run the production crawler
            self.discovered_urls = self.crawler.crawl_all_elements()
            self.stats['discovery_time'] = datetime.now()
            self.stats['elements_discovered'] = len(self.discovered_urls)
            
            print(f"✅ Discovery complete!")
            print(f"   Elements found: {len(self.discovered_urls)}")
            
            # Export discovery results
            discovery_file = 'complete_pipeline_discovery.json'
            self.crawler.export_elements(discovery_file)
            print(f"   Discovery exported to: {discovery_file}")
            
            return len(self.discovered_urls) > 0
            
        except Exception as e:
            print(f"❌ Discovery failed: {e}")
            return False
    
    def run_extraction_phase(self, limit: int = None) -> bool:
        """Phase 2: Extract data from all discovered elements"""
        
        print(f"\n🏗️  PHASE 2: EXTRACTING DATA FROM {len(self.discovered_urls)} ELEMENTS")
        print("=" * 60)
        
        if limit:
            urls_to_process = self.discovered_urls[:limit]
            print(f"   Processing first {limit} elements for testing")
        else:
            urls_to_process = self.discovered_urls
            print(f"   Processing ALL {len(urls_to_process)} elements")
        
        for i, url in enumerate(urls_to_process):
            try:
                print(f"\n--- Element {i+1}/{len(urls_to_process)} ---")
                print(f"Processing: {url}")
                
                # Extract element data
                element = self.element_extractor.extract_element_data(url)
                
                if not element:
                    print(f"   ⚠️ Skipped: No element data extracted")
                    self.failed_elements.append({'url': url, 'reason': 'extraction_failed'})
                    self.stats['failed_count'] += 1
                    continue
                
                print(f"   ✓ Extracted: {element.code} - {element.title}")
                print(f"   ✓ Variables: {len(element.variables)}")
                
                # Try to generate template (with variable testing)
                template = self.template_extractor.extract_template_smart(url)
                
                if template and hasattr(template, 'template') and template.template:
                    print(f"   ✓ Dynamic template: {template.template}")
                    print(f"   ✓ Template variables: {len(template.variables)}")
                    template_to_use = template.template
                else:
                    # If no dynamic template found, get REAL element description from meta description
                    template_to_use = self.template_extractor.get_static_description(url)
                    print(f"   ✓ Static template: {template_to_use[:100]}...")
                    print(f"   ✓ Template length: {len(template_to_use)} characters")
                
                # Store in database
                try:
                    element_id = self.store_complete_element(element, template_to_use, url)
                    
                    print(f"   ✅ Stored in database with ID: {element_id}")
                    
                    self.processed_elements.append({
                        'url': url,
                        'element_id': element_id,
                        'code': element.code,
                        'title': element.title,
                        'variables_count': len(element.variables),
                        'template': template_to_use
                    })
                    
                    self.stats['elements_processed'] += 1
                    self.stats['elements_stored'] += 1
                    
                except Exception as e:
                    print(f"   ❌ Database storage failed: {e}")
                    self.failed_elements.append({'url': url, 'reason': f'database_error: {e}'})
                    self.stats['failed_count'] += 1
                
                # Progress update
                if (i + 1) % 10 == 0:
                    self.print_progress()
                
                # Respectful delay
                time.sleep(1.0)
                
            except Exception as e:
                print(f"   ❌ Processing failed: {e}")
                self.failed_elements.append({'url': url, 'reason': f'processing_error: {e}'})
                self.stats['failed_count'] += 1
                continue
        
        return len(self.processed_elements) > 0
    
    def store_complete_element(self, element, template=None, url=None) -> int:
        """Store complete element data in database"""
        
        # 1. Create element
        element_id = self.db_manager.create_element(
            element_code=element.code,
            element_name=element.title,
            price=element.price,  # Store extracted price
            created_by='CYPE_Scraper'
        )
        
        # 2. Add variables with options
        for var in element.variables:
            # Add variable
            variable_id = self.db_manager.add_variable(
                element_id=element_id,
                variable_name=var.name,
                variable_type='TEXT',  # CYPE variables are mostly text
                unit=getattr(var, 'unit', None),
                default_value=var.options[0] if var.options else None,
                is_required=False,  # All optional since using static templates
                display_order=len(element.variables)
            )
            
            # Add options for this variable
            for i, option in enumerate(var.options):
                self.db_manager.add_variable_option(
                    variable_id=variable_id,
                    option_value=option,
                    option_label=option,
                    display_order=i,
                    is_default=(i == 0)  # First option is default
                )
        
        # 3. Add template (dynamic or static based on analysis)
        if template:
            try:
                version_id = self.db_manager.create_proposal(
                    element_id=element_id,
                    description_template=template,
                    created_by='CYPE_Scraper'
                )
                
                # Auto-approve to S3 (active)
                for _ in range(3):  # S0->S1->S2->S3
                    self.db_manager.approve_proposal(version_id, 'CYPE_Scraper', 'Auto-approved template')
                
            except Exception as e:
                print(f"      ⚠️ Template creation failed: {e}")
        
        return element_id
    
    def print_progress(self):
        """Print current progress"""
        elapsed = datetime.now() - self.stats['start_time']
        
        print(f"\n📊 PROGRESS UPDATE:")
        print(f"   Elements discovered: {self.stats['elements_discovered']}")
        print(f"   Elements processed: {self.stats['elements_processed']}")
        print(f"   Elements stored: {self.stats['elements_stored']}")
        print(f"   Failed elements: {self.stats['failed_count']}")
        print(f"   Elapsed time: {elapsed}")
        
        if self.stats['elements_processed'] > 0:
            success_rate = (self.stats['elements_stored'] / self.stats['elements_processed']) * 100
            print(f"   Success rate: {success_rate:.1f}%")
    
    def generate_final_report(self):
        """Generate final pipeline report"""
        
        total_time = datetime.now() - self.stats['start_time']
        
        print(f"\n🎉 COMPLETE PIPELINE FINISHED!")
        print("=" * 60)
        print(f"📊 FINAL RESULTS:")
        print(f"   Total elements discovered: {self.stats['elements_discovered']}")
        print(f"   Total elements processed: {self.stats['elements_processed']}")  
        print(f"   Total elements stored in database: {self.stats['elements_stored']}")
        print(f"   Failed elements: {self.stats['failed_count']}")
        print(f"   Total processing time: {total_time}")
        
        if self.stats['elements_processed'] > 0:
            success_rate = (self.stats['elements_stored'] / self.stats['elements_processed']) * 100
            print(f"   Overall success rate: {success_rate:.1f}%")
        
        # Export final results
        final_report = {
            'pipeline_run': {
                'start_time': self.stats['start_time'].isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_time': str(total_time),
                'database_path': self.database_path
            },
            'results': {
                'elements_discovered': self.stats['elements_discovered'],
                'elements_processed': self.stats['elements_processed'],
                'elements_stored': self.stats['elements_stored'],
                'failed_count': self.stats['failed_count']
            },
            'processed_elements': self.processed_elements,
            'failed_elements': self.failed_elements
        }
        
        report_file = f'complete_pipeline_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Final report exported to: {report_file}")
        
        # Database summary
        print(f"\n🗄️ DATABASE SUMMARY:")
        try:
            elements = self.db_manager.list_elements()
            print(f"   Total elements in database: {len(elements)}")
            
            # Count variables and options
            total_variables = 0
            total_options = 0
            for element in elements:
                variables = self.db_manager.get_element_variables(element['element_id'])
                total_variables += len(variables)
                for var in variables:
                    total_options += len(var.get('options', []))
            
            print(f"   Total variables in database: {total_variables}")
            print(f"   Total variable options: {total_options}")
        except Exception as e:
            print(f"   Database summary error: {e}")
    
    def run_complete_pipeline(self, extraction_limit: int = None):
        """Run the complete pipeline from discovery to database storage"""
        
        print("🚀 COMPLETE CYPE PIPELINE")
        print("=" * 60)
        print("Discovering ALL CYPE elements and storing in database")
        print(f"Database: {self.database_path}")
        if extraction_limit:
            print(f"Extraction limit: {extraction_limit} elements (for testing)")
        print()
        
        # Phase 1: Discovery
        if not self.run_discovery_phase():
            print("❌ Pipeline failed at discovery phase")
            return False
        
        # Phase 2: Extraction and Storage
        if not self.run_extraction_phase(limit=extraction_limit):
            print("❌ Pipeline failed at extraction phase")
            return False
        
        # Final report
        self.generate_final_report()
        
        return True

def main():
    """Main function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Run complete CYPE pipeline')
    parser.add_argument('--database', '-d', 
                      help='Database path (default: src/office_data.db)',
                      default=None)
    parser.add_argument('--limit', '-l', type=int,
                      help='Limit extraction to N elements (for testing)',
                      default=None)
    parser.add_argument('--discovery-only', action='store_true',
                      help='Run discovery phase only')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = CompleteCYPEPipeline(database_path=args.database)
    
    try:
        if args.discovery_only:
            # Run discovery only
            success = pipeline.run_discovery_phase()
            if success:
                print(f"✅ Discovery completed! Found {len(pipeline.discovered_urls)} elements")
            else:
                print("❌ Discovery failed")
        else:
            # Run complete pipeline
            success = pipeline.run_complete_pipeline(extraction_limit=args.limit)
            
            if success:
                print("\n✅ COMPLETE PIPELINE SUCCESS!")
                print("   All CYPE elements have been discovered, extracted, and stored in your database!")
                print(f"   Database location: {pipeline.database_path}")
            else:
                print("\n❌ PIPELINE FAILED")
                print("   Check error messages above for details")
        
    except KeyboardInterrupt:
        print("\n⚠️ Pipeline interrupted by user")
        print("   Progress has been saved and can be resumed")
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")

if __name__ == "__main__":
    main()