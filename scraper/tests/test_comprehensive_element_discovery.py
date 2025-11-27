#!/usr/bin/env python3
"""
Comprehensive test: Discover all URL variations for elements and generate dynamic templates
"""

import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import re
from collections import defaultdict
import time
from urllib.parse import urljoin

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from db_manager import DatabaseManager

def test_comprehensive_discovery():
    """Test comprehensive element discovery with URL variations"""
    
    print("🚀 COMPREHENSIVE ELEMENT DISCOVERY & TEMPLATE GENERATION")
    print("=" * 70)
    
    # Test with known element variations (limit to 5 max)
    known_variations = [
        {
            'url': 'https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html',
            'code': 'EHV016',
            'title': 'Viga exenta de hormigón visto'
        },
        {
            'url': 'https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_de_hormigon_armado.html',
            'code': 'EHV016', 
            'title': 'Viga de hormigón armado'
        },
        {
            'url': 'https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Sistema_de_encofrado_para_viga.html',
            'code': 'EHV016',
            'title': 'Sistema de encofrado para viga'
        }
    ]
    
    print(f"\n🔍 Testing with {len(known_variations)} known element variations")
    
    all_elements = {}  # Group by element code
    
    # Group the known variations by element code
    for element_data in known_variations:
        code = element_data['code']
        if code not in all_elements:
            all_elements[code] = []
        all_elements[code].append(element_data)
    
    # Analyze elements with multiple URL variations
    print(f"\n📊 ELEMENT ANALYSIS:")
    print(f"   Total unique elements: {len(all_elements)}")
    
    multi_url_elements = {code: variations for code, variations in all_elements.items() if len(variations) > 1}
    
    print(f"   Elements with multiple URLs: {len(multi_url_elements)}")
    
    if multi_url_elements:
        print(f"\n🎯 Testing template generation for multi-URL elements:")
        
        # Test template generation for first element only (limit to 1)
        success_count = 0
        
        for i, (element_code, variations) in enumerate(list(multi_url_elements.items())[:1]):
            print(f"\n--- Element {i+1}: {element_code} ---")
            print(f"   URL variations: {len(variations)}")
            
            # Generate template for this element
            template_result = generate_dynamic_template(element_code, variations)
            
            if template_result:
                success_count += 1
                print(f"   ✅ Template generated successfully!")
                print(f"   Template: {template_result['template'][:100]}...")
                print(f"   Placeholders: {template_result['placeholders']}")
                
                # Store in database
                store_element_with_dynamic_template(template_result)
                
            else:
                print(f"   ❌ Template generation failed")
        
        print(f"\n🎉 RESULTS:")
        print(f"   Elements tested: {min(1, len(multi_url_elements))}")
        print(f"   Templates created: {success_count}")
        print(f"   Success rate: {(success_count/min(1, len(multi_url_elements)))*100:.1f}%")
        
    else:
        print(f"❌ No elements with multiple URLs found - need to expand discovery")

def discover_category_elements(category_url):
    """Discover all element URLs in a category"""
    
    elements = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(category_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all links that look like element URLs
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '')
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                full_url = 'https://generadordeprecios.info' + href
            elif href.startswith('http'):
                full_url = href
            else:
                full_url = urljoin(category_url, href)
            
            # Check if this looks like an element URL (not category)
            if is_element_url(full_url):
                # Extract element data
                element_data = extract_quick_element_data(full_url, link.get_text(strip=True))
                if element_data:
                    elements.append(element_data)
                
                # Rate limiting
                time.sleep(0.5)
        
    except Exception as e:
        print(f"   Error discovering category: {e}")
    
    return elements

def is_element_url(url):
    """Check if URL looks like an element page (not category)"""
    
    # Element URLs typically:
    # 1. End with .html
    # 2. Have underscores in filename (element naming pattern)
    # 3. Are in obra_nueva section
    # 4. Don't end with just category name
    
    if not url.endswith('.html'):
        return False
    
    if '/obra_nueva/' not in url:
        return False
    
    filename = url.split('/')[-1].replace('.html', '')
    
    # Element files typically have underscores or are descriptive
    if '_' in filename or len(filename) > 10:
        return True
    
    return False

def extract_quick_element_data(url, link_text):
    """Quick extraction of element data for discovery"""
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        # Quick element code extraction
        code_pattern = r'([A-Z]{2,3}\d{3})'
        code_match = re.search(code_pattern, response.text)
        
        if not code_match:
            return None
        
        code = code_match.group(1)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Quick title extraction
        title_elem = soup.find('h1')
        title = title_elem.get_text(strip=True) if title_elem else link_text
        
        return {
            'url': url,
            'code': code,
            'title': title,
            'link_text': link_text
        }
        
    except Exception as e:
        print(f"     Error extracting {url.split('/')[-1]}: {e}")
        return None

def generate_dynamic_template(element_code, variations):
    """Generate dynamic template from URL variations"""
    
    print(f"   🔧 Generating template for {element_code}...")
    
    # Extract full descriptions from each variation
    descriptions_data = []
    
    for i, variation in enumerate(variations):
        print(f"     Extracting description {i+1}/{len(variations)}...")
        
        desc_data = extract_full_description(variation['url'])
        if desc_data:
            desc_data['variation'] = variation
            descriptions_data.append(desc_data)
        
        time.sleep(1)  # Rate limiting
    
    if len(descriptions_data) < 2:
        print(f"     ❌ Need at least 2 descriptions, got {len(descriptions_data)}")
        return None
    
    # Compare descriptions to find patterns
    template_result = create_template_from_descriptions(element_code, descriptions_data)
    
    return template_result

def extract_full_description(url):
    """Extract full technical description from element page"""
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for technical description sections
        description = find_technical_description(soup)
        price = extract_price(soup)
        
        if description and len(description) > 50:
            return {
                'url': url,
                'description': clean_description_text(description),
                'price': price
            }
    
    except Exception as e:
        print(f"       Error: {e}")
    
    return None

def find_technical_description(soup):
    """Find the main technical description in CYPE page"""
    
    # Look for text that contains technical construction terms
    construction_terms = ['hormigón', 'acero', 'madera', 'encofrado', 'armado', 'aplicación']
    
    # Search in paragraphs and divs
    for elem in soup.find_all(['p', 'div', 'td']):
        text = elem.get_text(strip=True)
        
        if (len(text) > 100 and 
            any(term in text.lower() for term in construction_terms) and
            not any(nav in text.lower() for nav in ['navegación', 'menú', 'obra nueva'])):
            return text
    
    # Fallback: get largest meaningful text block
    all_text = soup.get_text()
    paragraphs = [p.strip() for p in all_text.split('\n') if len(p.strip()) > 100]
    
    for para in paragraphs:
        if any(term in para.lower() for term in construction_terms):
            return para
    
    return None

def clean_description_text(text):
    """Clean description text for template processing"""
    
    # Fix encoding
    fixes = {
        'Ã±': 'ñ', 'Ã³': 'ó', 'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ãº': 'ú',
        'Â': '', 'â': '', 'ï': '', '°': '°'
    }
    
    for wrong, correct in fixes.items():
        text = text.replace(wrong, correct)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    return text

def extract_price(soup):
    """Extract price from page"""
    
    text = soup.get_text()
    price_patterns = [r'(\d+[.,]\d+)\s*€']
    
    for pattern in price_patterns:
        matches = re.findall(pattern, text)
        if matches:
            try:
                return float(matches[0].replace(',', '.'))
            except ValueError:
                continue
    
    return None

def create_template_from_descriptions(element_code, descriptions_data):
    """Create template by analyzing description differences"""
    
    print(f"     📝 Creating template from {len(descriptions_data)} descriptions...")
    
    descriptions = [d['description'] for d in descriptions_data]
    
    # Find common base and variable parts
    template_result = analyze_description_patterns(descriptions, descriptions_data)
    
    if not template_result:
        return None
    
    return {
        'element_code': element_code,
        'template': template_result['template'],
        'placeholders': template_result['placeholders'],
        'variations': descriptions_data,
        'base_description': descriptions[0]
    }

def analyze_description_patterns(descriptions, descriptions_data):
    """Analyze patterns in descriptions to create template"""
    
    # Simple approach: find words that differ between descriptions
    word_sets = [set(desc.split()) for desc in descriptions]
    
    # Find common words
    common_words = word_sets[0]
    for word_set in word_sets[1:]:
        common_words &= word_set
    
    # Find variable words (appear in some but not all descriptions)
    all_words = set()
    for word_set in word_sets:
        all_words |= word_set
    
    variable_words = all_words - common_words
    
    if not variable_words:
        print(f"       ❌ No variable words found")
        return None
    
    print(f"       Found {len(variable_words)} variable words")
    
    # Create template by replacing variable words with placeholders
    base_description = descriptions[0]
    template = base_description
    
    placeholders = []
    
    # Group similar variable words
    variable_groups = group_variable_words(variable_words, descriptions_data)
    
    for group_name, words in variable_groups.items():
        placeholder = f"{{{group_name}}}"
        placeholders.append(group_name)
        
        # Replace all words in this group with the placeholder
        for word in words:
            template = re.sub(r'\b' + re.escape(word) + r'\b', placeholder, template, count=1)
    
    if placeholders:
        return {
            'template': template,
            'placeholders': placeholders
        }
    
    return None

def group_variable_words(variable_words, descriptions_data):
    """Group variable words by type (material, dimension, etc.)"""
    
    groups = {
        'tipo_material': [],
        'dimension': [],
        'tipo_construccion': [],
        'acabado': []
    }
    
    for word in variable_words:
        word_lower = word.lower()
        
        if any(mat in word_lower for mat in ['hormigón', 'acero', 'madera']):
            groups['tipo_material'].append(word)
        elif any(dim in word_lower for dim in ['cm', 'm', 'mm', 'x']) or word.replace('.', '').isdigit():
            groups['dimension'].append(word)
        elif any(const in word_lower for const in ['encofrado', 'armado', 'visto']):
            groups['tipo_construccion'].append(word)
        elif any(acab in word_lower for acab in ['liso', 'rugoso', 'brillante']):
            groups['acabado'].append(word)
        else:
            # Default to construction type
            groups['tipo_construccion'].append(word)
    
    # Remove empty groups
    return {k: v for k, v in groups.items() if v}

def store_element_with_dynamic_template(template_result):
    """Store element with dynamic template in database"""
    
    print(f"     💾 Storing in database...")
    
    try:
        db_path = str(Path(__file__).parent.parent / "src" / "office_data.db")
        db_manager = DatabaseManager(db_path)
        
        element_code = template_result['element_code']
        
        # Create element with timestamp to avoid conflicts
        import time
        timestamp = int(time.time())
        
        element_id = db_manager.create_element(
            element_code=f"{element_code}_DYN_{timestamp}",
            element_name=f"Dynamic template test for {element_code}",
            created_by='Dynamic_Template_Test'
        )
        
        # Create dummy variables for the placeholders
        placeholder_to_variable = {}
        for placeholder in template_result['placeholders']:
            var_id = db_manager.add_variable(
                element_id=element_id,
                variable_name=placeholder,
                variable_type='TEXT',  # Use valid type
                is_required=True
            )
            placeholder_to_variable[placeholder] = var_id
        
        # Create template version using proposal method
        version_id = db_manager.create_proposal(
            element_id=element_id,
            description_template=template_result['template'],
            created_by='Dynamic_Template_Test'
        )
        
        # Create placeholder mappings manually since no public method exists
        with db_manager.get_connection() as conn:
            # Get unique placeholders to avoid duplicates
            unique_placeholders = list(set(template_result['placeholders']))
            for i, placeholder in enumerate(unique_placeholders):
                variable_id = placeholder_to_variable[placeholder]
                conn.execute(
                    "INSERT INTO template_variable_mappings (version_id, variable_id, placeholder, position) VALUES (?, ?, ?, ?)",
                    (version_id, variable_id, placeholder, i)
                )
        
        print(f"       ✅ Stored: Element {element_id}, Template {version_id}")
        return element_id
        
    except Exception as e:
        print(f"       ❌ Storage error: {e}")
        return None

if __name__ == "__main__":
    test_comprehensive_discovery()