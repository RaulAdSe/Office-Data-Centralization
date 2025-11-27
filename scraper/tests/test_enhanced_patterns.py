#!/usr/bin/env python3
"""
Test Enhanced Variable Pattern Recognition
Mock test to verify our pattern improvements are working
"""

import sys
from pathlib import Path

# Add paths  
sys.path.insert(0, str(Path(__file__).parent / "core"))

def test_enhanced_patterns():
    """Test enhanced pattern recognition with mock data"""
    from enhanced_element_extractor import EnhancedElementExtractor
    from bs4 import BeautifulSoup
    
    print("🧪 TESTING ENHANCED VARIABLE PATTERNS")
    print("=" * 50)
    
    extractor = EnhancedElementExtractor()
    
    # Mock HTML for EHX005-like element
    mock_html = """
    <html>
    <body>
        <h1>EHX005 - Losa mixta con chapa colaborante</h1>
        
        <!-- Numeric inputs that should get enhanced names -->
        <label>Cuantía de acero para momentos negativos (kg/m²):</label>
        <input type="text" value="1.0" id="acero_neg">
        
        <label>Cuantía de acero para momentos positivos (kg/m²):</label>
        <input type="text" value="0.0" id="acero_pos">
        
        <label>Volumen de hormigón (m³/m²):</label>
        <input type="text" value="0.062" id="vol_hormigon">
        
        <label>Canto de la losa (cm):</label>
        <input type="text" value="10" id="canto">
        
        <label>Altura del perfil (mm):</label>
        <input type="text" value="44" id="altura">
        
        <label>Intereje (mm):</label>
        <input type="text" value="172" id="intereje">
        
        <label>Espesor (mm):</label>
        <input type="text" value="0.75" id="espesor">
        
        <!-- Radio buttons that should get enhanced names -->
        <input type="radio" name="prelacado" value="sin" checked>Sin prelacado
        <input type="radio" name="prelacado" value="con">Con prelacado
        
        <input type="radio" name="chapa" value="galvanizado" checked>Galvanizado
        <input type="radio" name="chapa" value="otro">Otro acabado
    </body>
    </html>
    """
    
    soup = BeautifulSoup(mock_html, 'html.parser')
    
    # Test numeric variable identification
    print("🔢 TESTING NUMERIC VARIABLE PATTERNS:")
    print("-" * 40)
    
    text_inputs = soup.find_all('input', type='text')
    for inp in text_inputs:
        value = inp.get('value')
        var_name, description = extractor.identify_numeric_variable_context(inp, soup, value)
        
        label_elem = soup.find('label', string=lambda text: text and inp.get('id') in str(text))
        if label_elem:
            label_text = label_elem.get_text()
        else:
            label_text = extractor.find_input_label(inp, soup)
        
        if var_name:
            print(f"✅ Enhanced: '{label_text}' → {var_name}")
            print(f"   Value: {value}")
            print(f"   Description: {description}")
        else:
            print(f"❌ Generic: '{label_text}' → dimension_X")
            print(f"   Value: {value}")
        print()
    
    # Test radio button grouping
    print("📻 TESTING RADIO BUTTON PATTERNS:")
    print("-" * 40)
    
    variables = extractor.extract_variables_enhanced(soup, soup.get_text())
    
    for var in variables:
        print(f"Variable: {var.name} ({var.variable_type})")
        print(f"  Options: {var.options}")
        print(f"  Default: {var.default_value}")
        print(f"  Description: {var.description}")
        print()
    
    # Analysis
    enhanced_vars = [var for var in variables if not var.name.startswith('dimension_') and not var.name.startswith('opcion_')]
    
    print("📊 ENHANCEMENT ANALYSIS:")
    print("-" * 40)
    print(f"Total variables: {len(variables)}")
    print(f"Enhanced variables: {len(enhanced_vars)}")
    print(f"Enhancement rate: {len(enhanced_vars)*100//len(variables) if variables else 0}%")
    
    if enhanced_vars:
        print("\n✅ Enhanced variable names found:")
        for var in enhanced_vars:
            print(f"  • {var.name}")
    else:
        print("\n❌ No enhanced variable names detected")
    
    return len(enhanced_vars) > 0

if __name__ == "__main__":
    success = test_enhanced_patterns()
    print(f"\n🎯 Result: {'SUCCESS' if success else 'NEEDS_IMPROVEMENT'}")