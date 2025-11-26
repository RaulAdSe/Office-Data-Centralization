#!/usr/bin/env python3
"""
Test Dynamic Template Generation with Multiple Element Variations
Focus on creating templates WITH placeholders
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enhanced_template_system import EnhancedTemplateSystem

def test_dynamic_placeholders():
    """Test dynamic template generation with known element variations"""
    
    print("🧪 TESTING DYNAMIC PLACEHOLDER GENERATION")
    print("=" * 60)
    
    # Create test with known element variations (same element code, different descriptions)
    test_variations = {
        'EHV016': [
            "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/EHV016_Viga_descolgada_de_hormigon_arm_1.html",
            "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/EHV016_Viga_descolgada_de_hormigon_arm_2.html"
        ]
    }
    
    # Manually create test data with known differences
    test_elements = [
        {
            'element_code': 'EHV016',
            'title': 'Viga descolgada de hormigón armado',
            'description': 'Viga descolgada, recta, de hormigón armado, de 40x60 cm, realizada con hormigón HA-25/F/20/XC2 fabricado en central, y vertido con cubilote',
            'price': 563.98,
            'variables': [{'name': 'dimension', 'type': 'TEXT', 'options': ['40x60', '30x50']}],
            'url': test_variations['EHV016'][0]
        },
        {
            'element_code': 'EHV016', 
            'title': 'Viga descolgada de hormigón armado',
            'description': 'Viga descolgada, recta, de hormigón armado, de 30x50 cm, realizada con hormigón HA-30/F/20/XC1 fabricado en central, y vertido con bomba',
            'price': 523.45,
            'variables': [{'name': 'dimension', 'type': 'TEXT', 'options': ['40x60', '30x50']}],
            'url': test_variations['EHV016'][1]
        }
    ]
    
    print(f"📊 Testing with {len(test_elements)} element variations")
    for i, elem in enumerate(test_elements, 1):
        print(f"   {i}. {elem['element_code']}: {elem['description'][:60]}...")
    
    # Test enhanced template generation
    system = EnhancedTemplateSystem()
    grouped = system.group_elements_by_code(test_elements)
    
    print(f"\n🔧 GENERATING DYNAMIC TEMPLATES")
    templates = system.generate_enhanced_templates(grouped)
    
    print(f"📊 Results: {len(templates)} templates generated")
    
    for template in templates:
        print(f"\n✅ **{template['element_code']}** ({template['template_type']}):")
        print(f"   Template: {template['template'][:100]}...")
        print(f"   Placeholders: {len(template['placeholders'])} → {template['placeholders']}")
        
        if template['variables']:
            print(f"   Variables:")
            for var in template['variables']:
                print(f"     - {var['name']}: {var['options']}")
    
    # Test with even more obvious differences
    print(f"\n🧪 TESTING WITH MORE OBVIOUS DIFFERENCES")
    
    obvious_test_elements = [
        {
            'element_code': 'TEST001',
            'title': 'Test Element',
            'description': 'Muro de hormigón de 20 cm de espesor, realizado con cemento Portland',
            'price': 100.0,
            'variables': [],
            'url': 'test1.html'
        },
        {
            'element_code': 'TEST001',
            'title': 'Test Element', 
            'description': 'Muro de ladrillo de 15 cm de espesor, realizado con mortero mixto',
            'price': 85.0,
            'variables': [],
            'url': 'test2.html'
        },
        {
            'element_code': 'TEST001',
            'title': 'Test Element',
            'description': 'Muro de piedra de 25 cm de espesor, realizado con cal hidráulica',
            'price': 120.0,
            'variables': [],
            'url': 'test3.html'
        }
    ]
    
    print(f"📊 Testing with {len(obvious_test_elements)} obvious variations")
    for i, elem in enumerate(obvious_test_elements, 1):
        print(f"   {i}. {elem['description']}")
    
    obvious_grouped = system.group_elements_by_code(obvious_test_elements)
    obvious_templates = system.generate_enhanced_templates(obvious_grouped)
    
    print(f"📊 Results: {len(obvious_templates)} templates generated")
    
    for template in obvious_templates:
        print(f"\n✅ **{template['element_code']}** ({template['template_type']}):")
        print(f"   Template: {template['template']}")
        print(f"   Placeholders: {len(template['placeholders'])} → {template['placeholders']}")
        
        if template['variables']:
            print(f"   Variables:")
            for var in template['variables']:
                print(f"     - {var['name']} ({var.get('semantic_type', 'general')}): {var['options']}")
        
        # Test the differences detection specifically
        if len(obvious_test_elements) > 1:
            descriptions = [e['description'] for e in obvious_test_elements]
            differences = system.find_enhanced_differences(descriptions)
            print(f"   🔍 Detected differences: {len(differences)}")
            for diff in differences:
                print(f"     - Position {diff['position']}: {diff['base_word']} → {diff['variations']} ({diff.get('semantic_type', 'unknown')})")

if __name__ == "__main__":
    test_dynamic_placeholders()