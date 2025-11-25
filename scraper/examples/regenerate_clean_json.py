#!/usr/bin/env python3
"""
Regenerate the 5 element JSON files with proper Spanish encoding
"""

from element_extractor import extract_multiple_elements
import json
from datetime import datetime

def regenerate_clean_json():
    """Regenerate JSON files with fixed Spanish encoding"""
    
    # Use the same 5 working URLs
    element_urls = [
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html",
        "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Esmaltes/Esmalte_al_agua_para_madera.html",
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_de_hormigon_armado.html",
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Sistema_de_encofrado_para_viga.html",
        "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Esmaltes/Esmalte_sintetico_para_madera.html",
    ]
    
    print("🧹 REGENERATING JSON WITH CLEAN SPANISH ENCODING")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URLs to re-scrape: {len(element_urls)}")
    print()
    
    # Extract elements with fixed encoding
    elements = extract_multiple_elements(element_urls)
    
    if not elements:
        print("❌ No elements extracted!")
        return
    
    print(f"✅ Successfully extracted {len(elements)} elements with clean encoding")
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
    
    # Save clean individual JSON files
    for i, element_data in enumerate(elements_json):
        code = element_data["metadata"]["code"]
        filename = f"clean_element_{code.lower()}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(element_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved: {filename}")
        
        # Show clean title 
        meta = element_data["metadata"]
        stats = element_data["stats"]
        print(f"   📝 Title: {meta['title']}")
        print(f"   💰 Price: €{meta['price']}")
        print(f"   🔧 Variables: {stats['total_variables']}")
        print()
    
    # Save combined clean JSON file
    combined_data = {
        "scrape_info": {
            "timestamp": datetime.now().isoformat(),
            "total_elements": len(elements_json),
            "scraper_version": "1.1.0",
            "encoding_fixed": True,
            "description": "CYPE elements with proper Spanish character encoding"
        },
        "elements": elements_json
    }
    
    clean_combined_file = "clean_scraped_elements_5.json"
    with open(clean_combined_file, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved clean combined file: {clean_combined_file}")
    print()
    
    # Summary
    print("📊 CLEAN SCRAPING SUMMARY:")
    print("="*40)
    for i, element in enumerate(elements_json, 1):
        meta = element["metadata"]
        print(f"{i}. {meta['code']} - {meta['title']}")
    
    total_vars = sum(e["stats"]["total_variables"] for e in elements_json)
    print(f"\n✅ Total: {len(elements_json)} elements, {total_vars} variables")
    print(f"🎯 All Spanish characters properly encoded (ñ, ó, í, á, etc.)")
    
    return elements_json

if __name__ == "__main__":
    regenerate_clean_json()