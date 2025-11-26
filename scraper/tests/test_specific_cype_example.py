#!/usr/bin/env python3
"""
Test the specific CYPE example provided by user to verify the system works correctly
"""

import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import re

def test_specific_cype_example():
    """Test with the specific example provided by the user"""
    
    print("🔍 TESTING SPECIFIC CYPE EXAMPLE")
    print("=" * 60)
    
    # The exact URLs provided by user
    test_urls = [
        "https://generadordeprecios.info/obra_nueva/Demoliciones/Estructuras/Acero/Demolicion_de_forjado_metalico.html",
        "https://generadordeprecios.info/obra_nueva/Demoliciones/Estructuras/Acero/Demolicion_de_forjado_metalico_0_0_1_0_0.html"
    ]
    
    # Expected descriptions from user
    expected_descriptions = [
        "Demolición de forjado de viguetas metálicas y entrevigado de tablero cerámico machihembrado con capa de compresión, realizado con martillo neumático y equipo de oxicorte, previo levantado del pavimento y su base, y carga manual sobre camión o contenedor.",
        "Demolición de forjado de viguetas metálicas y entrevigado de revoltón cerámico formado por una o dos roscas de ladrillo cerámico y relleno de senos con cascotes y mortero de cal, realizado con martillo neumático y equipo de oxicorte, previo levantado del pavimento y su base, y carga manual sobre camión o contenedor."
    ]
    
    print(f"🌐 Testing {len(test_urls)} specific URLs:")
    
    results = []
    
    for i, url in enumerate(test_urls):
        print(f"\n--- URL {i+1}/{len(test_urls)} ---")
        print(f"URL: {url.split('/')[-1]}")
        
        result = extract_element_details(url)
        
        if result:
            results.append(result)
            print(f"✅ Success")
            print(f"   Code: {result['code']}")
            print(f"   Title: {result['title']}")
            print(f"   Description length: {len(result['description'])}")
            print(f"   Description: {result['description'][:100]}...")
            
            # Compare with expected
            expected = expected_descriptions[i]
            if expected.lower() in result['description'].lower():
                print(f"   ✅ Description matches expected content")
            else:
                print(f"   ⚠️  Description differs from expected")
                print(f"   Expected: {expected[:100]}...")
                print(f"   Found: {result['description'][:100]}...")
        else:
            print(f"   ❌ Failed to extract")
    
    # Analyze if they are the same element
    if len(results) >= 2:
        analyze_element_similarity(results)
        
        # Test template generation
        if are_same_element(results):
            print(f"\n🔧 TESTING TEMPLATE GENERATION:")
            template_result = generate_template_from_descriptions(results)
            
            if template_result:
                print(f"   ✅ Template generated!")
                print(f"   Template: {template_result['template'][:150]}...")
                print(f"   Placeholders: {template_result['placeholders']}")
                print(f"   Variable differences found: {len(template_result['differences'])}")
            else:
                print(f"   ❌ Template generation failed")

def extract_element_details(url):
    """Extract detailed element information"""
    
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
        
        # Extract title from h1 or page title
        title_elem = soup.find('h1')
        if not title_elem:
            title_elem = soup.find('title')
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
        
        # Extract description - look for the technical description
        description = find_technical_description(soup)
        
        return {
            'url': url,
            'code': code,
            'title': title,
            'description': clean_description(description) if description else "No description found"
        }
        
    except Exception as e:
        print(f"   Error extracting: {e}")
        return None

def find_technical_description(soup):
    """Find the main technical description in the page"""
    
    # Try different selectors for CYPE descriptions
    description_selectors = [
        '.descripcion',
        'p.descripcion',  
        'div.descripcion',
        '.contenido p',
        'td.descripcion',
        '.texto_descripcion'
    ]
    
    for selector in description_selectors:
        desc_elem = soup.select_one(selector)
        if desc_elem:
            text = desc_elem.get_text(strip=True)
            if len(text) > 50:  # Meaningful description length
                return text
    
    # Look for paragraphs with construction terminology
    construction_terms = ['demolición', 'forjado', 'viguetas', 'metálicas', 'martillo', 'neumático']
    
    for p in soup.find_all('p'):
        text = p.get_text(strip=True)
        if (len(text) > 100 and 
            any(term in text.lower() for term in construction_terms)):
            return text
    
    # Look in table cells
    for td in soup.find_all('td'):
        text = td.get_text(strip=True)
        if (len(text) > 100 and 
            any(term in text.lower() for term in construction_terms)):
            return text
    
    # Last resort: find longest text with construction terms
    all_text = soup.get_text()
    paragraphs = [p.strip() for p in all_text.split('\n') if len(p.strip()) > 100]
    
    for para in paragraphs:
        if any(term in para.lower() for term in construction_terms):
            return para
    
    return None

def clean_description(text):
    """Clean and normalize description text"""
    
    if not text:
        return ""
    
    # Fix common encoding issues
    fixes = {
        'Ã±': 'ñ', 'Ã³': 'ó', 'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ãº': 'ú',
        'Â': '', 'â': '', 'ï': ''
    }
    
    for wrong, correct in fixes.items():
        text = text.replace(wrong, correct)
    
    # Clean whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    return text

def analyze_element_similarity(results):
    """Analyze if the results represent the same element"""
    
    print(f"\n📊 ELEMENT SIMILARITY ANALYSIS:")
    
    codes = [r['code'] for r in results]
    titles = [r['title'] for r in results]
    descriptions = [r['description'] for r in results]
    
    print(f"   Element codes: {codes}")
    print(f"   Same code: {'✅' if len(set(codes)) == 1 else '❌'}")
    
    print(f"   Titles: {len(set(titles))} unique")
    for i, title in enumerate(titles):
        print(f"     {i+1}. {title}")
    
    print(f"   Descriptions: {len(set(descriptions))} unique")
    if len(set(descriptions)) > 1:
        print(f"   ✅ DESCRIPTIONS ARE DIFFERENT - perfect for template generation!")
    else:
        print(f"   ❌ Descriptions are identical")

def are_same_element(results):
    """Check if results represent the same element"""
    codes = [r['code'] for r in results]
    return len(set(codes)) == 1 and codes[0] != "UNKNOWN"

def generate_template_from_descriptions(results):
    """Generate template by comparing the descriptions"""
    
    descriptions = [r['description'] for r in results]
    
    # Find differences between descriptions
    differences = find_description_differences(descriptions)
    
    if not differences:
        return None
    
    # Create template with placeholders
    base_description = descriptions[0]
    template = base_description
    placeholders = []
    
    # Replace different words with placeholders
    for diff in differences:
        placeholder_name = determine_placeholder_name(diff['words'])
        placeholder = f"{{{placeholder_name}}}"
        
        # Replace the first occurrence of the variable word
        if diff['words'][0] in template:
            template = template.replace(diff['words'][0], placeholder, 1)
            placeholders.append(placeholder_name)
    
    return {
        'template': template,
        'placeholders': list(set(placeholders)),  # Remove duplicates
        'differences': differences
    }

def find_description_differences(descriptions):
    """Find specific differences between descriptions"""
    
    if len(descriptions) < 2:
        return []
    
    # Split into words
    word_sets = [set(desc.split()) for desc in descriptions]
    
    # Find words that appear in some but not all descriptions
    all_words = set()
    for word_set in word_sets:
        all_words.update(word_set)
    
    # Find common words (appear in ALL descriptions)
    common_words = word_sets[0]
    for word_set in word_sets[1:]:
        common_words &= word_set
    
    # Variable words = all words - common words
    variable_words = all_words - common_words
    
    differences = []
    
    # Group variable words by context
    for word in variable_words:
        # Find which descriptions contain this word
        containing_descriptions = []
        for i, desc in enumerate(descriptions):
            if word in desc.split():
                containing_descriptions.append(i)
        
        # Only include meaningful differences (not single character differences)
        if len(word) > 2:
            differences.append({
                'word': word,
                'descriptions': containing_descriptions,
                'words': [word]  # Could be expanded to word groups
            })
    
    return differences

def determine_placeholder_name(words):
    """Determine appropriate placeholder name for variable words"""
    
    # Combine words to analyze
    combined = ' '.join(words).lower()
    
    # Categorize based on content
    if any(term in combined for term in ['tablero', 'revoltón', 'cerámico', 'ladrillo']):
        return 'tipo_entrevigado'
    elif any(term in combined for term in ['compresión', 'cascotes', 'mortero']):
        return 'tipo_relleno'
    elif any(term in combined for term in ['machihembrado', 'formado']):
        return 'metodo_construccion'
    elif any(term in combined for term in ['una', 'dos', 'roscas']):
        return 'numero_roscas'
    else:
        return 'variable'

if __name__ == "__main__":
    test_specific_cype_example()