#!/usr/bin/env python3
"""
Create template generation based on URL variations of same element
"""

import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import re
from difflib import SequenceMatcher
from urllib.parse import urljoin

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_url_based_template_generation():
    """Test template generation using URL variations of same element"""
    
    print("🔧 TESTING URL-BASED TEMPLATE GENERATION")
    print("=" * 60)
    
    # Known element variations (same EHV016 code)
    base_urls = [
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html",
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_de_hormigon_armado.html", 
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Sistema_de_encofrado_para_viga.html"
    ]
    
    print(f"🌐 Testing {len(base_urls)} URL variations:")
    
    # Extract data from each URL
    variations = []
    
    for i, url in enumerate(base_urls):
        print(f"\n--- Variation {i+1}/{len(base_urls)} ---")
        print(f"URL: {url.split('/')[-1]}")
        
        data = extract_full_element_data(url)
        
        if data:
            variations.append(data)
            print(f"✅ Success")
            print(f"   Code: {data['code']}")
            print(f"   Technical description: {data['tech_description'][:80]}...")
        else:
            print(f"❌ Failed")
    
    if len(variations) >= 2:
        # Generate template from variations
        template_result = generate_template_from_variations(variations)
        
        if template_result:
            print(f"\n🎉 TEMPLATE GENERATION SUCCESS!")
            print(f"   Element: {template_result['element_code']}")
            print(f"   Template: {template_result['template'][:100]}...")
            print(f"   Placeholders: {template_result['placeholders']}")
            print(f"   Variations: {len(template_result['variations'])}")
            
            # Test template with each variation
            test_template_with_variations(template_result)
        else:
            print(f"\n❌ Template generation failed")
    else:
        print(f"\n❌ Need at least 2 variations for template generation")

def extract_full_element_data(url):
    """Extract comprehensive element data including technical description"""
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract element code
        code_pattern = r'([A-Z]{2,3}\d{3})'
        code_match = re.search(code_pattern, response.text)
        code = code_match.group(1) if code_match else "UNKNOWN"
        
        # Extract title 
        title_elem = soup.find('h1')
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
        
        # Extract technical description (the part that varies)
        tech_description = extract_technical_description(soup)
        
        # Extract price if available
        price = extract_price_from_page(soup)
        
        # Parse URL to understand variable context
        url_context = parse_url_context(url)
        
        return {
            'url': url,
            'code': code,
            'title': title,
            'tech_description': tech_description,
            'price': price,
            'url_context': url_context
        }
        
    except Exception as e:
        print(f"   Error: {e}")
        return None

def extract_technical_description(soup):
    """Extract the technical description that varies between URL variations"""
    
    # Look for main content areas that might contain technical descriptions
    content_selectors = [
        'div.contenido',
        'div.descripcion', 
        'div.main-content',
        'td.descripcion',
        'div#content'
    ]
    
    for selector in content_selectors:
        content = soup.select_one(selector)
        if content:
            text = content.get_text(strip=True)
            # Look for construction-specific content
            if len(text) > 100 and any(term in text.lower() for term in 
                ['hormigón', 'viga', 'encofrado', 'armado', 'aplicación']):
                return clean_technical_text(text)
    
    # Fallback: look for largest text block with construction terms
    all_text = soup.get_text()
    paragraphs = re.split(r'\n\s*\n', all_text)
    
    construction_paragraphs = []
    for para in paragraphs:
        para = para.strip()
        if (len(para) > 100 and 
            any(term in para.lower() for term in ['hormigón', 'viga', 'acero', 'madera']) and
            not any(nav in para.lower() for nav in ['navegación', 'menú', 'copyright'])):
            construction_paragraphs.append((len(para), para))
    
    if construction_paragraphs:
        # Return longest construction paragraph
        construction_paragraphs.sort(reverse=True)
        return clean_technical_text(construction_paragraphs[0][1])
    
    # Last resort: get main page text
    main_text = soup.get_text()[:2000]  # First 2000 chars
    return clean_technical_text(main_text)

def clean_technical_text(text):
    """Clean and normalize technical text"""
    
    # Fix encoding issues
    text = fix_encoding_issues(text)
    
    # Remove navigation and irrelevant content
    lines = text.split('\n')
    clean_lines = []
    
    skip_patterns = [
        'obra nueva', 'rehabilitación', 'espacios urbanos',
        'actuaciones previas', 'demoliciones', 'navegación',
        'menú', 'copyright', 'política', 'cookies'
    ]
    
    for line in lines:
        line = line.strip()
        if (len(line) > 10 and 
            not any(pattern in line.lower() for pattern in skip_patterns)):
            clean_lines.append(line)
    
    cleaned = ' '.join(clean_lines)
    
    # Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned

def fix_encoding_issues(text):
    """Fix common encoding issues"""
    
    fixes = {
        'Ã±': 'ñ', 'Ã³': 'ó', 'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ãº': 'ú',
        'ÃÃ±': 'ñ', 'íłn': 'ión', 'aÃÃ³n': 'ación'
    }
    
    for wrong, correct in fixes.items():
        text = text.replace(wrong, correct)
    
    return text

def extract_price_from_page(soup):
    """Extract price information"""
    
    # Look for price patterns in the page
    text = soup.get_text()
    
    price_patterns = [
        r'(\d+[.,]\d+)\s*€/m',  # Price per m²/m³
        r'(\d+[.,]\d+)\s*€',    # General price
        r'precio.*?(\d+[.,]\d+)',
    ]
    
    for pattern in price_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                price_str = matches[0].replace(',', '.')
                return float(price_str)
            except ValueError:
                continue
    
    return None

def parse_url_context(url):
    """Parse URL to understand variable context"""
    
    filename = url.split('/')[-1].replace('.html', '')
    
    # Extract meaningful context from filename
    context = {
        'filename': filename,
        'type': None,
        'material': None,
        'application': None
    }
    
    # Analyze filename for context clues
    filename_lower = filename.lower()
    
    if 'viga_exenta' in filename_lower:
        context['type'] = 'exenta'
    elif 'viga_de_hormigon' in filename_lower:
        context['type'] = 'armado'
    elif 'encofrado' in filename_lower:
        context['type'] = 'encofrado'
    
    if 'hormigon' in filename_lower:
        context['material'] = 'hormigon'
    elif 'madera' in filename_lower:
        context['material'] = 'madera'
    elif 'acero' in filename_lower:
        context['material'] = 'acero'
    
    return context

def generate_template_from_variations(variations):
    """Generate template by comparing variations"""
    
    print(f"\n🔧 GENERATING TEMPLATE FROM {len(variations)} VARIATIONS:")
    
    # Verify all variations have same element code
    codes = [v['code'] for v in variations]
    if len(set(codes)) != 1:
        print(f"❌ Different element codes: {codes}")
        return None
    
    element_code = codes[0]
    print(f"   Element code: {element_code}")
    
    # Compare technical descriptions
    descriptions = [v['tech_description'] for v in variations]
    
    print(f"   Description lengths: {[len(d) for d in descriptions]}")
    
    # Find common parts and differences
    template_parts = find_template_structure(descriptions, variations)
    
    if not template_parts:
        print(f"❌ Could not identify template structure")
        return None
    
    # Create template string
    template = create_template_string(template_parts)
    
    # Extract placeholders
    placeholders = extract_placeholders_from_template(template)
    
    return {
        'element_code': element_code,
        'template': template,
        'placeholders': placeholders,
        'variations': variations,
        'template_parts': template_parts
    }

def find_template_structure(descriptions, variations):
    """Find template structure by comparing descriptions"""
    
    print(f"   Comparing {len(descriptions)} descriptions...")
    
    # Use the first description as base, compare with others
    base_desc = descriptions[0]
    
    # Find differences between base and each other description
    differences = []
    
    for i, desc in enumerate(descriptions[1:], 1):
        print(f"     Comparing with variation {i+1}")
        
        # Find differing segments
        diff_segments = find_differences(base_desc, desc, variations[0], variations[i])
        differences.append(diff_segments)
    
    # Merge all differences to find consistent patterns
    template_structure = merge_differences(base_desc, differences, variations)
    
    return template_structure

def find_differences(text1, text2, var1, var2):
    """Find specific differences between two descriptions"""
    
    # Simple word-level comparison
    words1 = text1.split()
    words2 = text2.split()
    
    # Find differing word positions
    diff_positions = []
    
    max_len = max(len(words1), len(words2))
    
    for i in range(max_len):
        word1 = words1[i] if i < len(words1) else ""
        word2 = words2[i] if i < len(words2) else ""
        
        if word1 != word2:
            diff_positions.append({
                'position': i,
                'word1': word1,
                'word2': word2,
                'context1': var1['url_context'],
                'context2': var2['url_context']
            })
    
    return diff_positions

def merge_differences(base_desc, all_differences, variations):
    """Merge differences to create template structure"""
    
    # This is a simplified approach - in production would be more sophisticated
    words = base_desc.split()
    template_parts = []
    
    # Find positions that consistently differ across variations
    position_diffs = {}
    
    for differences in all_differences:
        for diff in differences:
            pos = diff['position']
            if pos not in position_diffs:
                position_diffs[pos] = []
            position_diffs[pos].append(diff)
    
    # Create template by replacing variable positions
    for i, word in enumerate(words):
        if i in position_diffs and len(position_diffs[i]) > 1:
            # This position varies - create placeholder
            placeholder_name = determine_placeholder_name(position_diffs[i], variations)
            template_parts.append(f"{{{placeholder_name}}}")
        else:
            # Static word
            template_parts.append(word)
    
    return template_parts

def determine_placeholder_name(differences, variations):
    """Determine appropriate placeholder name from differences"""
    
    # Analyze the different words to determine what variable they represent
    words = [diff['word1'] for diff in differences] + [diff['word2'] for diff in differences]
    words = [w for w in words if w]  # Remove empty
    
    # Simple heuristic based on word content
    if any('hormigón' in w.lower() for w in words):
        return 'tipo_material'
    elif any('viga' in w.lower() for w in words):
        return 'tipo_viga' 
    elif any('encofrado' in w.lower() for w in words):
        return 'tipo_construccion'
    elif any(w.replace('.', '').isdigit() for w in words):
        return 'medida'
    else:
        return 'variable'

def create_template_string(template_parts):
    """Create final template string from parts"""
    
    if not template_parts:
        return ""
    
    template = ' '.join(template_parts)
    
    # Clean up spacing around placeholders
    template = re.sub(r'\s+', ' ', template)
    template = re.sub(r'\s*\{\s*', '{', template)
    template = re.sub(r'\s*\}\s*', '}', template)
    
    return template.strip()

def extract_placeholders_from_template(template):
    """Extract placeholder names from template"""
    
    placeholders = re.findall(r'\{([^}]+)\}', template)
    return list(set(placeholders))  # Remove duplicates

def test_template_with_variations(template_result):
    """Test generated template with original variations"""
    
    print(f"\n🔍 TESTING TEMPLATE WITH VARIATIONS:")
    
    template = template_result['template']
    placeholders = template_result['placeholders']
    variations = template_result['variations']
    
    print(f"   Template: {template}")
    print(f"   Placeholders: {placeholders}")
    
    # Try to fill template with each variation
    for i, variation in enumerate(variations):
        print(f"\n   Testing with variation {i+1}:")
        print(f"     URL: {variation['url'].split('/')[-1]}")
        
        # Simple placeholder filling (would be more sophisticated in production)
        filled_template = template
        for placeholder in placeholders:
            # Try to extract value from URL context or description
            value = extract_placeholder_value(placeholder, variation)
            if value:
                filled_template = filled_template.replace(f'{{{placeholder}}}', value)
        
        print(f"     Filled: {filled_template[:80]}...")

def extract_placeholder_value(placeholder, variation):
    """Extract placeholder value from variation data"""
    
    # Simple extraction based on URL context and content
    context = variation['url_context']
    
    if placeholder == 'tipo_material':
        return context.get('material', 'material')
    elif placeholder == 'tipo_viga':
        return context.get('type', 'viga')
    elif placeholder == 'tipo_construccion':
        if 'encofrado' in variation['url']:
            return 'encofrado'
        else:
            return 'construccion'
    else:
        return placeholder  # Fallback

if __name__ == "__main__":
    test_url_based_template_generation()