#!/usr/bin/env python3
"""
Database Integration for CYPE Scraped Elements
Maps scraped Spanish variables to the enhanced database structure
"""

import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from enhanced_element_extractor import EnhancedElementExtractor, ElementData
from db_manager import DatabaseManager
from typing import List, Dict, Any
import json

class CYPEDatabaseIntegrator:
    """Integrates scraped CYPE elements with the database"""
    
    def __init__(self, db_path: str = "cype_elements.db"):
        self.db_manager = DatabaseManager(db_path)
        self.extractor = EnhancedElementExtractor()
        
    def integrate_scraped_elements(self, urls: List[str], created_by: str = "cype_scraper") -> Dict[str, Any]:
        """
        Scrape elements and integrate them into the database
        
        Args:
            urls: List of CYPE element URLs to scrape
            created_by: User identifier for database records
            
        Returns:
            Dictionary with integration results
        """
        results = {
            "scraped_count": 0,
            "integrated_count": 0,
            "errors": [],
            "element_codes": []
        }
        
        print(f"🔄 INTEGRATING CYPE ELEMENTS TO DATABASE")
        print("="*60)
        print(f"URLs to scrape: {len(urls)}")
        print(f"Database: {self.db_manager.db_path}")
        print()
        
        # Scrape elements
        scraped_elements = []
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] Scraping: {url}")
            
            element = self.extractor.extract_element_data(url)
            if element:
                scraped_elements.append(element)
                results["scraped_count"] += 1
                print(f"  ✅ Scraped: {element.code} - {element.title}")
            else:
                error_msg = f"Failed to scrape: {url}"
                results["errors"].append(error_msg)
                print(f"  ❌ {error_msg}")
            print()
        
        # Integrate into database
        print(f"📊 INTEGRATING {len(scraped_elements)} ELEMENTS INTO DATABASE")
        print("-" * 60)
        
        for element in scraped_elements:
            try:
                self.integrate_single_element(element, created_by)
                results["integrated_count"] += 1
                results["element_codes"].append(element.code)
                print(f"  ✅ Integrated: {element.code}")
                
            except Exception as e:
                error_msg = f"Failed to integrate {element.code}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"  ❌ {error_msg}")
        
        print()
        print(f"📈 INTEGRATION SUMMARY:")
        print(f"  Scraped: {results['scraped_count']} elements")
        print(f"  Integrated: {results['integrated_count']} elements")
        print(f"  Errors: {len(results['errors'])}")
        
        return results
    
    def integrate_single_element(self, element: ElementData, created_by: str) -> int:
        """
        Integrate a single scraped element into the database
        
        Args:
            element: Scraped element data
            created_by: User identifier
            
        Returns:
            element_id of the created database element
        """
        # Create the element record
        element_id = self.db_manager.create_element(
            element_code=element.code,
            element_name=element.title,
            created_by=created_by
        )
        
        # Add variables with their options
        for var in element.variables:
            variable_id = self.create_variable_with_options(element_id, var)
            
        return element_id
    
    def create_variable_with_options(self, element_id: int, var) -> int:
        """
        Create a variable with its options in the database
        
        Args:
            element_id: Database element ID
            var: ElementVariable from scraper
            
        Returns:
            variable_id of the created variable
        """
        # Map scraper types to database types
        type_mapping = {
            'TEXT': 'TEXT',
            'RADIO': 'TEXT',  # Radio options stored as TEXT with options
            'CHECKBOX': 'TEXT'  # Checkbox stored as TEXT with options
        }
        
        db_type = type_mapping.get(var.variable_type, 'TEXT')
        
        # Prepare options for database - KEEP VALUES IN SPANISH
        options = []
        if var.options:
            for i in range(len(var.options)):
                option_text = var.options[i]
                is_default = (option_text == var.default_value)
                options.append({
                    'option_value': option_text,  # Store Spanish text as value
                    'option_label': option_text,  # Same for label
                    'display_order': i + 1,
                    'is_default': is_default
                })
        
        # Create variable with options
        variable_id = self.db_manager.add_variable(
            element_id=element_id,
            variable_name=var.name,
            variable_type=db_type,
            unit=None,  # Could extract from description if needed
            default_value=var.default_value,
            is_required=var.is_required,
            display_order=0,  # Could implement ordering logic
            options=options if options else None
        )
        
        return variable_id
    
    def create_option_value(self, option_text: str) -> str:
        """
        Create a clean option value from option text
        Converts display text to a database-friendly value
        
        Args:
            option_text: Display text for the option
            
        Returns:
            Clean value for database storage
        """
        # Remove accents and special characters for value
        value = option_text.lower()
        
        # Spanish to English mappings for common terms
        mappings = {
            'interior': 'interior',
            'exterior': 'exterior',
            'mínimo': 'minimum',
            'medio': 'medium', 
            'máximo': 'maximum',
            'color blanco': 'white',
            'color a elegir': 'custom_color',
            'brillante': 'gloss',
            'satinado': 'satin',
            'mate': 'matte',
            'convencional': 'conventional',
            'autocompactante': 'self_compacting',
            'con cubilote': 'bucket_pour',
            'con bomba': 'pump_pour',
            'barandillas o pasamanos': 'railings',
            'mobiliario': 'furniture',
            'carpintería': 'carpentry',
        }
        
        # Use mapping if available, otherwise create clean value
        for spanish, english in mappings.items():
            if spanish in value:
                return english
        
        # Fallback: create clean value from original text
        clean_value = value.replace(' ', '_').replace('ó', 'o').replace('í', 'i').replace('á', 'a').replace('é', 'e').replace('ú', 'u').replace('ñ', 'n')
        clean_value = ''.join(c for c in clean_value if c.isalnum() or c == '_')
        return clean_value[:50]  # Limit length
    
    def create_description_version(self, element_id: int, element: ElementData, created_by: str) -> int:
        """
        Create a description version using element variables
        
        Args:
            element_id: Database element ID
            element: Scraped element data
            created_by: User identifier
            
        Returns:
            version_id of the created description version
        """
        # Create template using available variables
        variables = self.db_manager.get_element_variables(element_id)
        
        # Build template with placeholders for key variables
        template_parts = [element.title]
        
        # Add key variable placeholders
        for var in variables[:3]:  # Use first 3 variables
            template_parts.append(f"{{{var['variable_name']}}}")
        
        template = " - ".join(template_parts)
        
        # Create variables data with defaults
        variables_data = {}
        for var in variables:
            options = self.db_manager.get_variable_options(var['variable_id'])
            if options:
                # Use default option if available
                default_option = next((opt for opt in options if opt['is_default']), options[0])
                variables_data[var['variable_name']] = default_option['option_value']
            else:
                variables_data[var['variable_name']] = var.get('default_value', '')
        
        # Create description version
        version_id = self.db_manager.create_description_version(
            element_id=element_id,
            template=template,
            variables_data=variables_data,
            created_by=created_by
        )
        
        return version_id
    
    def export_integration_summary(self, results: Dict[str, Any], output_file: str = None):
        """Export integration results to JSON"""
        
        summary = {
            "integration_summary": results,
            "database_elements": []
        }
        
        # Get detailed info for each integrated element
        for code in results["element_codes"]:
            element = self.db_manager.get_element_by_code(code)
            if element:
                variables = self.db_manager.get_element_variables(element['element_id'], include_options=True)
                summary["database_elements"].append({
                    "code": code,
                    "element_info": element,
                    "variables": variables
                })
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            print(f"📄 Integration summary exported to: {output_file}")
        
        return summary

def demo_integration():
    """Demonstrate the database integration"""
    
    # Sample URLs for testing
    demo_urls = [
        "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Esmaltes/Esmalte_al_agua_para_madera.html",
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html"
    ]
    
    integrator = CYPEDatabaseIntegrator("demo_cype.db")
    
    # Run integration
    results = integrator.integrate_scraped_elements(demo_urls, created_by="demo_user")
    
    # Export summary
    summary_file = "integration_summary.json"
    integrator.export_integration_summary(results, summary_file)
    
    return results

if __name__ == "__main__":
    demo_integration()