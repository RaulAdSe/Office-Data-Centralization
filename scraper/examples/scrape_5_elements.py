#!/usr/bin/env python3
"""
Scrape 5 CYPE elements with complete variables and save as JSON
"""

from element_extractor import extract_multiple_elements
import json
from datetime import datetime
import time

def scrape_and_save_elements():
    """Scrape 5 elements and save complete data as JSON"""
    
    # Known working element URLs 
    element_urls = [
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html",
        "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Esmaltes/Esmalte_al_agua_para_madera.html",
        # Add 3 more diverse elements
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Pilares/Pilar_de_hormigon_armado.html",
        "https://generadordeprecios.info/obra_nueva/Fachadas_y_particiones/Fachadas/Ladrillo_cara_vista.html",
        "https://generadordeprecios.info/obra_nueva/Instalaciones/Fontaneria/Tuberia_de_polietileno_reticulado.html"
    ]
    
    print("🚀 SCRAPING 5 CYPE ELEMENTS WITH COMPLETE VARIABLES")
    print("="*80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URLs to scrape: {len(element_urls)}")
    print()
    
    # Extract elements
    elements = extract_multiple_elements(element_urls)
    
    if not elements:
        print("❌ No elements extracted!")
        return
    
    print(f"✅ Successfully extracted {len(elements)} elements")
    print()
    
    # Convert to JSON format
    elements_json = []
    
    for element in elements:
        element_data = {
            "metadata": {
                "code": element.code,
                "title": element.title,
                "unit": element.unit,
                "price": element.price,
                "url": element.url,
                "scraped_at": datetime.now().isoformat()
            },
            "description": {
                "main": element.description,
                "technical_characteristics": element.technical_characteristics,
                "measurement_criteria": element.measurement_criteria,
                "normativa": element.normativa
            },
            "variables": [
                {
                    "name": var.name,
                    "type": var.variable_type,
                    "options": var.options,
                    "default_value": var.default_value,
                    "required": var.is_required
                }
                for var in element.variables
            ],
            "stats": {
                "total_variables": len(element.variables),
                "text_variables": len([v for v in element.variables if v.variable_type == 'TEXT']),
                "radio_variables": len([v for v in element.variables if v.variable_type == 'RADIO']),
                "checkbox_variables": len([v for v in element.variables if v.variable_type == 'CHECKBOX'])
            }
        }
        
        elements_json.append(element_data)
    
    # Save individual JSON files
    for i, element_data in enumerate(elements_json):
        code = element_data["metadata"]["code"]
        filename = f"element_{code.lower()}.json"
        filepath = f"/Users/rauladell/Work/Office-Data-Centralization/scraper/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(element_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved: {filename}")
        
        # Show summary
        meta = element_data["metadata"]
        stats = element_data["stats"]
        print(f"   Code: {meta['code']}")
        print(f"   Title: {meta['title'][:50]}...")
        print(f"   Price: €{meta['price']}")
        print(f"   Variables: {stats['total_variables']} ({stats['text_variables']} TEXT, {stats['radio_variables']} RADIO, {stats['checkbox_variables']} CHECKBOX)")
        print()
    
    # Save combined JSON file
    combined_data = {
        "scrape_info": {
            "timestamp": datetime.now().isoformat(),
            "total_elements": len(elements_json),
            "scraper_version": "1.0.0"
        },
        "elements": elements_json
    }
    
    combined_filepath = f"/Users/rauladell/Work/Office-Data-Centralization/scraper/scraped_elements_5.json"
    with open(combined_filepath, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved combined file: scraped_elements_5.json")
    print()
    
    # Summary stats
    total_vars = sum(stats["total_variables"] for stats in [e["stats"] for e in elements_json])
    total_text = sum(stats["text_variables"] for stats in [e["stats"] for e in elements_json])
    total_radio = sum(stats["radio_variables"] for stats in [e["stats"] for e in elements_json])
    total_checkbox = sum(stats["checkbox_variables"] for stats in [e["stats"] for e in elements_json])
    
    print("📊 SCRAPING SUMMARY:")
    print("="*50)
    print(f"✅ Elements extracted: {len(elements_json)}")
    print(f"🔧 Total variables: {total_vars}")
    print(f"   📝 Text inputs: {total_text}")
    print(f"   🔘 Radio options: {total_radio}")  
    print(f"   ☑️  Checkboxes: {total_checkbox}")
    print(f"💾 Files saved in: /Users/rauladell/Work/Office-Data-Centralization/scraper/")
    print()
    
    return elements_json

if __name__ == "__main__":
    scrape_and_save_elements()