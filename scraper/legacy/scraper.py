#!/usr/bin/env python3
"""
Main scraper orchestrator - Integrates crawler, extractor and database
"""

import sys
import os
from pathlib import Path

# Add src directory to path to import db_manager
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from url_crawler import quick_find_elements
from element_extractor import extract_multiple_elements, ElementData
from db_manager import DatabaseManager
import time
from typing import List

class CYPEScraper:
    def __init__(self, db_path: str = "office_data.db", max_elements: int = 5):
        self.db_manager = DatabaseManager(db_path)
        self.max_elements = max_elements
    
    def scrape_and_store(self) -> List[str]:
        """Main method to scrape elements and store in database"""
        print("CYPE Office Data Scraper")
        print("="*80)
        
        # Step 1: Find element URLs
        print("STEP 1: Finding element URLs...")
        element_urls = quick_find_elements(self.max_elements)
        
        if not element_urls:
            print("No element URLs found!")
            return []
        
        print(f"\nFound {len(element_urls)} element URLs")
        
        # Step 2: Extract element data
        print(f"\nSTEP 2: Extracting element data...")
        elements = extract_multiple_elements(element_urls)
        
        if not elements:
            print("No element data extracted!")
            return []
        
        print(f"\nExtracted data from {len(elements)} elements")
        
        # Step 3: Store in database
        print(f"\nSTEP 3: Storing in database...")
        stored_codes = self.store_elements_in_db(elements)
        
        print(f"\nSuccessfully stored {len(stored_codes)} elements in database!")
        
        # Step 4: Show summary
        self.show_summary(stored_codes)
        
        return stored_codes
    
    def store_elements_in_db(self, elements: List[ElementData]) -> List[str]:
        """Store extracted elements in database"""
        stored_codes = []
        
        for element in elements:
            try:
                print(f"Storing {element.code}: {element.title}")
                
                # Create element in database
                element_id = self.db_manager.create_element(
                    element_code=element.code,
                    element_name=element.title,
                    created_by="scraper"
                )
                
                # Add variables for the element (basic set)
                variables = [
                    ("material", "text", "Material type", True),
                    ("dimensions", "text", "Dimensions", False),
                    ("finish", "text", "Finish type", False),
                    ("color", "text", "Color", False),
                ]
                
                for var_name, var_type, var_desc, required in variables:
                    self.db_manager.add_variable(element_id, var_name, var_type, var_desc, required)
                
                # Create initial description version
                template = f"{element.description[:100]}... {{material}}"  # Use part of description as template
                if element.price:
                    template += f" - Price: �{element.price}"
                
                desc_version_id = self.db_manager.create_description_version(
                    element_id=element_id,
                    template=template,
                    variables_data={"material": "standard"},
                    created_by="scraper"
                )
                
                print(f"   Created element {element_id} with description version {desc_version_id}")
                stored_codes.append(element.code)
                
            except Exception as e:
                print(f"   Error storing {element.code}: {e}")
        
        return stored_codes
    
    def show_summary(self, stored_codes: List[str]):
        """Show summary of scraped and stored data"""
        print(f"\n{'='*80}")
        print("SCRAPING SUMMARY")
        print("="*80)
        
        for code in stored_codes:
            # Get element info from database
            element = self.db_manager.get_element_by_code(code)
            if element:
                print(f"Code: {element['code']}")
                print(f"Name: {element['name']}")
                print(f"Category: {element['category']}")
                print(f"Unit: {element['unit']}")
                
                # Get variables
                variables = self.db_manager.get_element_variables(element['id'])
                print(f"Variables: {[v['name'] for v in variables]}")
                
                # Get latest description
                descriptions = self.db_manager.get_element_description_versions(element['id'])
                if descriptions:
                    latest = descriptions[0]  # Newest first
                    print(f"Description: {latest['template'][:100]}...")
                
                print("-" * 40)
        
        print(f"\nTotal elements scraped and stored: {len(stored_codes)}")
        print(f"Database location: {self.db_manager.db_path}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        max_elements = int(sys.argv[1])
    else:
        max_elements = 5
    
    scraper = CYPEScraper(max_elements=max_elements)
    stored_codes = scraper.scrape_and_store()
    
    return stored_codes

if __name__ == "__main__":
    main()