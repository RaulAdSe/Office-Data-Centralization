#!/usr/bin/env python3
"""
Test Spanish variable names with concrete and paint elements
"""

import sys
sys.path.insert(0, 'core')

from enhanced_element_extractor import EnhancedElementExtractor

def test_spanish_variables():
    """Test Spanish variable extraction on different element types"""
    
    urls = [
        # Paint element
        ("RME030 - Esmalte", "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Esmaltes/Esmalte_al_agua_para_madera.html"),
        
        # Concrete beam element  
        ("EHV015 - Viga Hormigón", "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html"),
    ]
    
    extractor = EnhancedElementExtractor()
    
    print("🇪🇸 VARIABLES EN ESPAÑOL - PRUEBA COMPLETA")
    print("="*60)
    
    for element_name, url in urls:
        print(f"\n🏗️ ELEMENTO: {element_name}")
        print("-" * 40)
        
        element = extractor.extract_element_data(url)
        
        if element:
            print(f"Código: {element.code}")
            print(f"Título: {element.title}")
            print(f"Variables: {len(element.variables)}")
            print()
            
            # Group by type for better display
            text_vars = [v for v in element.variables if v.variable_type == 'TEXT']
            radio_vars = [v for v in element.variables if v.variable_type == 'RADIO'] 
            checkbox_vars = [v for v in element.variables if v.variable_type == 'CHECKBOX']
            
            if text_vars:
                print("📏 CAMPOS NUMÉRICOS:")
                for var in text_vars:
                    print(f"   • {var.name}: {var.default_value} ({var.description})")
                print()
            
            if radio_vars:
                print("🔘 OPCIONES DE SELECCIÓN:")
                for var in radio_vars:
                    options_str = f"{var.options}" if len(var.options) <= 3 else f"{var.options[:3]}... ({len(var.options)} opciones)"
                    print(f"   • {var.name}: {options_str}")
                    print(f"     Descripción: {var.description}")
                    print(f"     Por defecto: {var.default_value}")
                print()
            
            if checkbox_vars:
                print("☑️ CARACTERÍSTICAS OPCIONALES:")
                for var in checkbox_vars:
                    print(f"   • {var.name}: {var.options[0][:50]}...")
                print()
        else:
            print(f"   ❌ Error extrayendo {element_name}")
        
        print("="*40)
    
    print("\n✅ PRUEBA COMPLETADA")
    print("Variables con nombres en español y descripciones apropiadas")

if __name__ == "__main__":
    test_spanish_variables()