#!/usr/bin/env python3
"""
Enhanced Template System for Better Description Templates and Placeholders
Addresses issues with navigation content and limited placeholder detection
"""

import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import re
import time
import json
from collections import defaultdict
from urllib.parse import urljoin, urlparse
from datetime import datetime

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db_manager import DatabaseManager

class EnhancedTemplateSystem:
    """Enhanced system for better template generation with improved content detection"""
    
    def __init__(self, db_path=None):
        """Initialize the enhanced system"""
        self.db_path = db_path or str(Path(__file__).parent.parent / "src" / "office_data.db")
        self.db_manager = DatabaseManager(self.db_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.1',
            'Accept-Charset': 'utf-8;q=1.0,iso-8859-1;q=0.5',
            'Accept-Encoding': 'gzip, deflate'
        })
        
    def run_enhanced_pipeline(self, max_elements=5):
        """Run enhanced template generation pipeline"""
        
        print("🚀 ENHANCED TEMPLATE SYSTEM")
        print("=" * 60)
        print(f"Target: {max_elements} elements maximum")
        
        try:
            # Get real element URLs and variations
            print("   🔍 Discovering element URLs with variations...")
            element_variations = self.discover_element_variations(max_elements)
            
            test_urls = []
            for element_code, urls in element_variations.items():
                test_urls.extend(urls)
            
            print(f"   Testing with {len(test_urls)} URLs ({len(element_variations)} elements)")
            for code, urls in element_variations.items():
                print(f"     {code}: {len(urls)} variations")
            
            print(f"\n📊 STAGE 1: ENHANCED CONTENT EXTRACTION")
            enhanced_elements = []
            
            for i, url in enumerate(test_urls):
                print(f"   Processing element {i+1}: {url[:80]}...")
                element_data = self.extract_enhanced_element_data(url)
                if element_data:
                    enhanced_elements.append(element_data)
                else:
                    print(f"     ❌ Failed to extract data")
                    
            print(f"   ✅ Extracted {len(enhanced_elements)} elements with enhanced content")
            
            # Group by element code and analyze variations
            print(f"\n📊 STAGE 2: ENHANCED TEMPLATE GENERATION")
            grouped_elements = self.group_elements_by_code(enhanced_elements)
            enhanced_templates = self.generate_enhanced_templates(grouped_elements)
            
            # Store enhanced templates
            print(f"\n📊 STAGE 3: ENHANCED DATABASE STORAGE")
            self.store_enhanced_templates(enhanced_templates)
            
            print(f"\n🎉 ENHANCED PIPELINE COMPLETE!")
            print(f"📊 Results:")
            print(f"   Elements processed: {len(enhanced_elements)}")
            print(f"   Templates created: {len(enhanced_templates)}")
            
            return enhanced_templates
            
        except Exception as e:
            print(f"❌ Pipeline error: {e}")
            return []
    
    def extract_enhanced_element_data(self, url):
        """Extract element data with enhanced content detection"""
        
        try:
            response = self.session.get(url, timeout=25)
            response.raise_for_status()
            
            # Force UTF-8 encoding
            if response.encoding != 'utf-8':
                response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract element code
            element_code = self.extract_element_code_enhanced(soup, url)
            if not element_code:
                return None
            
            # Extract title
            title = self.extract_title_enhanced(soup)
            
            # Extract description with enhanced filtering
            description = self.extract_enhanced_description(soup)
            if not description:
                print(f"     ❌ No valid description found for {element_code}")
                print(f"     🔍 Page has {len(soup.get_text())} total characters")
                return None
            
            # Extract price
            price = self.extract_price_enhanced(soup)
            
            # Extract variables for placeholder detection
            variables = self.extract_variables_enhanced(soup)
            
            print(f"     ✅ {element_code}: {len(description)} chars, {len(variables)} variables")
            
            return {
                'element_code': element_code,
                'title': title,
                'description': description,
                'price': price,
                'variables': variables,
                'url': url,
                'raw_html_size': len(response.text)
            }
            
        except Exception as e:
            print(f"     ❌ Error extracting from {url}: {e}")
            return None
    
    def extract_enhanced_description(self, soup):
        """Enhanced description extraction with better filtering"""
        
        # Method 1: Find description in structured content areas
        description = self.find_structured_description(soup)
        if description:
            return description
        
        # Method 2: Find in main content containers  
        description = self.find_content_container_description(soup)
        if description:
            return description
        
        # Method 3: Find longest technical paragraph
        description = self.find_technical_paragraph(soup)
        if description:
            return description
        
        return None
    
    def find_structured_description(self, soup):
        """Find description in structured content areas"""
        
        # Look for divs with content-related classes
        content_selectors = [
            'div.descripcion', 'div.contenido', 'div.detalle',
            'div.ficha', 'div.elemento', 'td.descripcion',
            'div[class*="content"]', 'div[class*="desc"]'
        ]
        
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if self.is_valid_technical_description(text):
                    return text
        
        return None
    
    def find_content_container_description(self, soup):
        """Find description in main content containers"""
        
        # Find all text blocks longer than 100 characters
        all_elements = soup.find_all(['p', 'div', 'td', 'span'])
        
        candidates = []
        for element in all_elements:
            text = element.get_text(strip=True)
            if len(text) > 100:
                score = self.score_description_candidate(text)
                if score > 0:
                    candidates.append((score, text))
        
        # Return highest scoring candidate
        if candidates:
            candidates.sort(reverse=True)
            return candidates[0][1]
        
        return None
    
    def find_technical_paragraph(self, soup):
        """Find longest technical paragraph as fallback"""
        
        paragraphs = soup.find_all(['p', 'div'])
        
        best_paragraph = None
        best_score = 0
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 50:
                score = self.score_description_candidate(text)
                if score > best_score:
                    best_score = score
                    best_paragraph = text
        
        return best_paragraph if best_score > 0 else None
    
    def is_valid_technical_description(self, text):
        """Enhanced validation for technical descriptions"""
        
        if not text or len(text) < 50:
            return False
        
        # Enhanced navigation detection
        if self.is_enhanced_navigation_content(text):
            return False
        
        # Check for technical construction terms
        technical_terms = [
            'hormigón', 'acero', 'viga', 'muro', 'pilar', 'cimentación',
            'armado', 'prefabricado', 'resistencia', 'módulo', 'espesor',
            'dimensión', 'fabricado', 'mortero', 'cemento', 'árido'
        ]
        
        text_lower = text.lower()
        technical_count = sum(1 for term in technical_terms if term in text_lower)
        
        return technical_count >= 2
    
    def is_enhanced_navigation_content(self, text):
        """Enhanced navigation content detection"""
        
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Enhanced navigation indicators
        nav_patterns = [
            # Direct navigation content
            r'ea acero\w*\s*ec\s*cantería',  # Navigation menu pattern
            r'eh\s*hormigón\s*armado\w*\s*em\s*madera',  # Menu structure
            r'ep\s*hormigón\s*prefabricado\w*\s*ex\s*mixtas',
            
            # Country/location lists
            r'españa\s*argentina\s*mexico',
            r'generador\s*de\s*precios\s*españa',
            
            # Menu-like sequences
            r'^\s*[A-Z]{2,3}\s+[A-Z][a-zá-ú]+([A-Z]{2,3}\s+[A-Z][a-zá-ú]+){2,}',
        ]
        
        for pattern in nav_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # Word frequency analysis
        words = text_lower.split()
        if len(words) < 10:  # Very short text might be navigation
            return True
        
        # Check for repetitive menu-like patterns
        word_freq = {}
        for word in words:
            if len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # If too many repeated short words, likely navigation
        repeated_count = sum(1 for freq in word_freq.values() if freq > 1)
        if repeated_count / len(word_freq) > 0.3:
            return True
        
        # Traditional navigation indicators
        nav_indicators = [
            'obra nueva', 'rehabilitación', 'espacios urbanos',
            'actuaciones previas', 'demoliciones', 'acondicionamiento',
            'menú', 'navegación', 'inicio', 'buscar', 
            'generador de precios', 'estructura', 'cimentaciones'
        ]
        
        nav_count = sum(1 for indicator in nav_indicators if indicator in text_lower)
        nav_ratio = nav_count / max(len(words), 1)
        
        return nav_ratio > 0.15 or nav_count >= 4
    
    def score_description_candidate(self, text):
        """Score a text candidate for being a good description"""
        
        if self.is_enhanced_navigation_content(text):
            return 0
        
        score = 0
        text_lower = text.lower()
        
        # Length bonus
        if 100 <= len(text) <= 1000:
            score += 10
        elif len(text) > 1000:
            score += 5
        
        # Technical terms bonus
        technical_terms = [
            'hormigón', 'acero', 'viga', 'muro', 'pilar', 'cimentación',
            'armado', 'prefabricado', 'resistencia', 'módulo', 'espesor',
            'dimensión', 'fabricado', 'mortero', 'cemento', 'árido',
            'realizada', 'formado', 'incluso', 'amortizable'
        ]
        
        technical_count = sum(1 for term in technical_terms if term in text_lower)
        score += technical_count * 2
        
        # Construction process terms
        process_terms = [
            'montaje', 'desmontaje', 'vertido', 'encofrado', 'curado',
            'fabricación', 'instalación', 'colocación', 'ejecución'
        ]
        
        process_count = sum(1 for term in process_terms if term in text_lower)
        score += process_count * 3
        
        # Penalize navigation-like content
        if any(nav in text_lower for nav in ['ea acero', 'ec cantería', 'eh hormigón']):
            score -= 20
        
        return score
    
    def extract_element_code_enhanced(self, soup, url):
        """Enhanced element code extraction"""
        
        # Try URL-based extraction first
        url_match = re.search(r'/([A-Z]{2,4}\d{3,4})', url)
        if url_match:
            return url_match.group(1)
        
        # Try page title
        title = soup.find('title')
        if title:
            title_match = re.search(r'([A-Z]{2,4}\d{3,4})', title.get_text())
            if title_match:
                return title_match.group(1)
        
        # Try meta tags or page headers
        for tag in soup.find_all(['h1', 'h2', 'h3']):
            header_match = re.search(r'([A-Z]{2,4}\d{3,4})', tag.get_text())
            if header_match:
                return header_match.group(1)
        
        return None
    
    def extract_title_enhanced(self, soup):
        """Enhanced title extraction"""
        
        # Try page title
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
            # Clean up title
            title = re.sub(r'Generador de Precios\.\s*España\s*[-|]*', '', title, flags=re.IGNORECASE)
            title = title.strip(' -|')
            if title:
                return title
        
        # Try main heading
        for tag in soup.find_all(['h1', 'h2']):
            text = tag.get_text(strip=True)
            if len(text) > 10 and not self.is_enhanced_navigation_content(text):
                return text
        
        return "Unknown Element"
    
    def extract_price_enhanced(self, soup):
        """Enhanced price extraction"""
        
        # Look for price patterns
        price_patterns = [
            r'(\d{1,4}[.,]\d{2})\s*€',
            r'€\s*(\d{1,4}[.,]\d{2})',
            r'(\d{1,4}[.,]\d{2})\s*EUR'
        ]
        
        text = soup.get_text()
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                price_str = match.group(1).replace(',', '.')
                try:
                    return float(price_str)
                except ValueError:
                    continue
        
        return None
    
    def extract_variables_enhanced(self, soup):
        """Enhanced variable extraction for better placeholder detection"""
        
        variables = []
        
        # Find radio button groups
        radio_inputs = soup.find_all('input', type='radio')
        radio_groups = defaultdict(list)
        
        for radio in radio_inputs:
            name = radio.get('name', 'unknown')
            value = radio.get('value', '')
            if value:
                radio_groups[name].append(value)
        
        # Convert to variables
        for group_name, values in radio_groups.items():
            variables.append({
                'name': group_name,
                'type': 'RADIO',
                'options': list(set(values)),  # Remove duplicates
                'is_required': True
            })
        
        return variables
    
    def group_elements_by_code(self, elements):
        """Group elements by their codes for variation detection"""
        
        grouped = defaultdict(list)
        for element in elements:
            base_code = element['element_code'].split('_')[0]  # Remove version suffixes
            grouped[base_code].append(element)
        
        return dict(grouped)
    
    def generate_enhanced_templates(self, grouped_elements):
        """Generate enhanced templates with better placeholder detection"""
        
        templates = []
        
        for element_code, variations in grouped_elements.items():
            print(f"   Generating template for {element_code} ({len(variations)} variations)...")
            
            if len(variations) == 1:
                # Single element - create dynamic template from variables
                element = variations[0]
                dynamic_template = self.create_dynamic_from_single_element(element)
                if dynamic_template:
                    templates.append(dynamic_template)
                else:
                    # Fallback to static if no variables found
                    templates.append({
                        'element_code': element_code,
                        'title': element['title'],
                        'template': element['description'],
                        'template_type': 'static',
                        'placeholders': [],
                        'variables': element.get('variables', []),
                        'price': element['price'],
                        'source_urls': [element['url']]
                    })
            else:
                # Multiple variations - dynamic template
                template = self.create_enhanced_dynamic_template(element_code, variations)
                if template:
                    templates.append(template)
        
        return templates
    
    def create_dynamic_from_single_element(self, element):
        """Create dynamic template from single element using extracted variables"""
        
        print(f"     🔍 Analyzing single element for dynamic patterns...")
        
        description = element['description']
        
        # Extract dynamic patterns from description text
        dynamic_patterns = self.extract_dynamic_patterns(description)
        
        if not dynamic_patterns:
            print(f"     ❌ No dynamic patterns found")
            return None
        
        # Create template with placeholders
        template = description
        placeholders = []
        variables = []
        
        for pattern in dynamic_patterns:
            placeholder = f"{{{pattern['name']}}}"
            
            # Replace first occurrence in template
            template = template.replace(pattern['value'], placeholder, 1)
            placeholders.append(pattern['name'])
            
            # Create variable
            variables.append({
                'name': pattern['name'],
                'variable_type': 'TEXT',
                'options': [pattern['value']],  # Original value as default
                'default_value': pattern['value'],
                'is_required': True
            })
        
        if placeholders:
            print(f"     🎯 Created dynamic template with {len(placeholders)} placeholders: {placeholders}")
            return {
                'element_code': element['element_code'],
                'title': element['title'],
                'template': template,
                'template_type': 'dynamic',
                'placeholders': placeholders,
                'variables': variables,
                'price': element['price'],
                'source_urls': [element['url']]
            }
        
        return None
    
    def extract_dynamic_patterns(self, description):
        """Extract patterns that can become placeholders from description"""
        
        patterns = []
        
        # Pattern 1: Dimensions (15 cm, 20 mm, etc.)
        dim_matches = re.findall(r'(\d+(?:\,\d+)?)\s*(cm|mm|m)', description)
        for i, (value, unit) in enumerate(dim_matches):
            patterns.append({
                'name': f'dimension_{i+1}' if i > 0 else 'dimension',
                'value': f'{value} {unit}',
                'type': 'dimension'
            })
        
        # Pattern 2: Material codes (HA-25, B-500, etc.)
        code_matches = re.findall(r'([A-Z]{1,3}-?\d+)', description)
        for i, code in enumerate(set(code_matches)):  # Remove duplicates
            patterns.append({
                'name': f'codigo_{i+1}' if i > 0 else 'codigo',
                'value': code,
                'type': 'material_code'
            })
        
        # Pattern 3: Materials/finishes (hormigón, acero, madera, etc.)
        materials = ['hormigón', 'acero', 'madera', 'pino', 'roble', 'barniz', 'pintura']
        for material in materials:
            if material in description.lower():
                patterns.append({
                    'name': 'material',
                    'value': material,
                    'type': 'material'
                })
                break  # Only first material found
        
        # Pattern 4: Numeric values with context (2 manos, 3 capas, etc.)
        numeric_matches = re.findall(r'(\d+)\s+(manos?|capas?)', description)
        for i, (value, unit) in enumerate(numeric_matches):
            patterns.append({
                'name': f'aplicaciones',
                'value': f'{value} {unit}',
                'type': 'application'
            })
            break  # Only first one
        
        return patterns
    
    def create_enhanced_dynamic_template(self, element_code, variations):
        """Create enhanced dynamic template with better placeholder detection"""
        
        descriptions = [v['description'] for v in variations]
        
        # Enhanced difference detection
        differences = self.find_enhanced_differences(descriptions)
        
        if not differences:
            # No meaningful differences - create static template
            return {
                'element_code': element_code,
                'title': variations[0]['title'],
                'template': descriptions[0],
                'template_type': 'static_from_multi',
                'placeholders': [],
                'variables': [],
                'price': variations[0]['price'],
                'source_urls': [v['url'] for v in variations]
            }
        
        # Create template with enhanced placeholders
        base_template = descriptions[0]
        placeholders = []
        variables = []
        placeholder_counter = {}  # Track placeholder usage
        
        for diff in differences:
            placeholder_name = self.determine_enhanced_placeholder(diff)
            
            # Handle multiple instances of same semantic type
            if placeholder_name in placeholder_counter:
                placeholder_counter[placeholder_name] += 1
                unique_placeholder = f"{placeholder_name}_{placeholder_counter[placeholder_name]}"
            else:
                placeholder_counter[placeholder_name] = 1
                unique_placeholder = placeholder_name
            
            placeholder = f"{{{unique_placeholder}}}"
            
            # Replace in template - find first occurrence of the word
            if diff['base_word'] in base_template:
                base_template = base_template.replace(diff['base_word'], placeholder, 1)
                placeholders.append(unique_placeholder)
                
                # Create enhanced variable with unique name
                variables.append({
                    'name': unique_placeholder,
                    'type': 'TEXT',
                    'options': diff['variations'],
                    'is_required': True,
                    'semantic_type': diff.get('semantic_type', 'general')
                })
        
        return {
            'element_code': element_code,
            'title': variations[0]['title'],
            'template': base_template,
            'template_type': 'dynamic',
            'placeholders': list(set(placeholders)),
            'variables': variables,
            'price': variations[0]['price'],
            'source_urls': [v['url'] for v in variations]
        }
    
    def find_enhanced_differences(self, descriptions):
        """Enhanced difference detection for ALL meaningful placeholders"""
        
        if len(descriptions) < 2:
            return []
        
        print(f"     🔍 Analyzing {len(descriptions)} variations for ALL differences...")
        
        # Look for ALL meaningful semantic differences
        meaningful_differences = []
        
        # Method 1: Find ALL dimension differences
        dimension_diffs = self.find_dimension_differences(descriptions)
        meaningful_differences.extend(dimension_diffs)
        print(f"       📐 Found {len(dimension_diffs)} dimension differences")
        
        # Method 2: Find material code differences  
        material_diffs = self.find_material_differences(descriptions)
        meaningful_differences.extend(material_diffs)
        print(f"       🔧 Found {len(material_diffs)} material differences")
        
        # Method 3: Find numeric/measurement differences
        numeric_diffs = self.find_numeric_differences(descriptions)
        meaningful_differences.extend(numeric_diffs)
        print(f"       📊 Found {len(numeric_diffs)} numeric differences")
        
        # Method 4: Find height/depth differences
        height_diffs = self.find_height_differences(descriptions)
        meaningful_differences.extend(height_diffs)
        print(f"       📏 Found {len(height_diffs)} height differences")
        
        # Method 5: Find finish/acabado differences
        finish_diffs = self.find_finish_differences(descriptions)
        meaningful_differences.extend(finish_diffs)
        print(f"       ✨ Found {len(finish_diffs)} finish differences")
        
        # Method 6: Find thickness/espesor differences
        thickness_diffs = self.find_thickness_differences(descriptions)
        meaningful_differences.extend(thickness_diffs)
        print(f"       📏 Found {len(thickness_diffs)} thickness differences")
        
        # Remove duplicates and limit to maximum 8 meaningful differences
        unique_diffs = []
        seen_words = set()
        for diff in meaningful_differences:
            if diff['base_word'] not in seen_words:
                unique_diffs.append(diff)
                seen_words.add(diff['base_word'])
        
        print(f"       ✅ Total unique differences: {len(unique_diffs)}")
        return unique_diffs[:8]  # Increased limit for richer templates
    
    def find_dimension_differences(self, descriptions):
        """Find ALL dimension-related differences like 40x60, 30x50"""
        
        differences = []
        
        # Look for dimension patterns like "40x60", "30x50", "15 cm", etc.
        patterns = [
            (r'\d+[x×]\d+', 'dimension'),  # 40x60, 30x50
            (r'\d+\s*cm', 'dimension_cm'),  # 15 cm, 20cm
            (r'\d+\s*mm', 'dimension_mm'),  # 10 mm, 5mm
        ]
        
        for pattern, semantic_type in patterns:
            # Collect all dimensions for this pattern
            all_dimensions = []
            for desc in descriptions:
                dims = re.findall(pattern, desc)
                all_dimensions.extend(dims)
            
            # Get unique dimensions
            unique_dims = list(set(all_dimensions))
            
            if len(unique_dims) > 1:
                # Find each unique dimension and create difference
                for dim in unique_dims:
                    # Check if this dimension appears in multiple descriptions
                    appears_in = []
                    for desc in descriptions:
                        if dim in desc:
                            appears_in.append(desc)
                    
                    if appears_in:
                        differences.append({
                            'base_word': dim,
                            'variations': unique_dims,
                            'semantic_type': semantic_type
                        })
                        break  # Only add this pattern once
        
        return differences  # Return ALL dimension differences
    
    def find_material_differences(self, descriptions):
        """Find material-related differences"""
        
        differences = []
        
        # Common construction materials
        materials = ['hormigón', 'acero', 'madera', 'ladrillo', 'piedra', 'hierro', 'aluminio']
        
        found_materials = []
        for desc in descriptions:
            desc_lower = desc.lower()
            for material in materials:
                if material in desc_lower:
                    found_materials.append(material)
                    break
        
        # If we found different materials, create a difference
        unique_materials = list(set(found_materials))
        if len(unique_materials) > 1:
            differences.append({
                'base_word': found_materials[0],
                'variations': unique_materials,
                'semantic_type': 'material'
            })
        
        return differences  # Return ALL material differences
    
    def find_numeric_differences(self, descriptions):
        """Find numeric differences (like HA-25, HA-30)"""
        
        differences = []
        
        # Look for patterns like HA-25, HA-30, B500, B400
        code_pattern = r'[A-Z]{1,3}-?\d+'
        
        code_sets = []
        for desc in descriptions:
            codes = re.findall(code_pattern, desc)
            code_sets.append(codes)
        
        # Find varying codes
        all_codes = []
        for codes in code_sets:
            all_codes.extend(codes)
        
        unique_codes = list(set(all_codes))
        if len(unique_codes) > 1:
            differences.append({
                'base_word': unique_codes[0],
                'variations': unique_codes,
                'semantic_type': 'codigo'
            })
        
        return differences  # Return ALL code differences
    
    def classify_word_type(self, word):
        """Enhanced word classification for semantic placeholders"""
        
        if not word:
            return 'general'
        
        word_lower = word.lower()
        
        # Material types
        if word_lower in ['hormigón', 'acero', 'madera', 'hierro', 'aluminio', 'pvc']:
            return 'material'
        
        # Dimensions
        if re.match(r'\d+[x×]\d+', word_lower) or word_lower in ['mm', 'cm', 'm']:
            return 'dimension'
        
        # Construction methods
        if word_lower in ['montaje', 'desmontaje', 'vertido', 'fabricado', 'realizada']:
            return 'proceso'
        
        # Properties/qualities
        if word_lower in ['resistente', 'flexible', 'impermeable', 'aislante']:
            return 'propiedad'
        
        # Standards/codes
        if re.match(r'[A-Z]{2,4}-\d+', word_lower) or 'une' in word_lower:
            return 'normativa'
        
        return 'general'
    
    def determine_enhanced_placeholder(self, difference):
        """Determine enhanced placeholder names based on semantic type"""
        
        semantic_type = difference.get('semantic_type', 'general')
        
        enhanced_mapping = {
            'material': 'material',
            'dimension': 'dimension', 
            'proceso': 'proceso',
            'propiedad': 'propiedad',
            'normativa': 'normativa',
            'codigo': 'codigo',
            'general': 'caracteristica'
        }
        
        return enhanced_mapping.get(semantic_type, 'variable')
    
    def discover_element_variations(self, max_elements):
        """Discover element URLs with their variations for dynamic templates"""
        
        # Use the production system to get element groups
        from production_base_system import ProductionDynamicTemplateSystem
        prod_system = ProductionDynamicTemplateSystem()
        
        # Get URLs and group them
        all_urls = prod_system.discover_element_urls(50)
        element_groups = prod_system.group_urls_by_element_code(all_urls)
        
        # Get variations (prioritize multi-URL elements)
        variations = {}
        count = 0
        
        # First add multi-URL elements (these create dynamic templates)
        for element_code, urls in element_groups.get('multi_url', {}).items():
            if count >= max_elements:
                break
            variations[element_code] = urls
            count += 1
        
        # Then add single-URL elements if needed
        for element_code, urls in element_groups.get('single_url', {}).items():
            if count >= max_elements:
                break
            variations[element_code] = urls
            count += 1
        
        return variations
    
    def discover_actual_element_urls(self, max_elements):
        """Discover actual element URLs by deep crawling"""
        
        print("   🔍 Deep crawling for actual element URLs...")
        
        # Start from a known subcategory
        start_url = "https://generadordeprecios.info/obra_nueva/Estructuras/EH_Hormigon_armado/EHV_Vigas.html"
        
        try:
            response = self.session.get(start_url, timeout=15)
            response.raise_for_status()
            
            if response.encoding != 'utf-8':
                response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            element_urls = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '.html' in href:
                    full_url = urljoin(start_url, href)
                    
                    # Check if this looks like an element URL
                    if self.is_element_url(full_url):
                        element_urls.append(full_url)
                        if len(element_urls) >= max_elements:
                            break
            
            return element_urls
            
        except Exception as e:
            print(f"   ❌ Discovery error: {e}")
            # Return some known working URLs as final fallback
            return [
                "https://generadordeprecios.info/obra_nueva/Estructuras/EH_Hormigon_armado/EHV_Vigas/EHV016_Viga_descolgada_de_hormigon_arm_1.html",
                "https://generadordeprecios.info/obra_nueva/Estructuras/EH_Hormigon_armado/EHE_Escaleras/EHE015_Escalera_de_hormigon_armado_1.html"
            ]
    
    def is_element_url(self, url):
        """Check if URL looks like an element URL"""
        
        # Element URLs typically have codes like EHV016, EHE015, etc.
        element_pattern = r'/[A-Z]{2,4}\d{3,4}_'
        return bool(re.search(element_pattern, url))
    
    def store_enhanced_templates(self, templates):
        """Store enhanced templates in database"""
        
        print(f"   💾 Storing {len(templates)} enhanced templates...")
        
        for template in templates:
            try:
                # Create element
                element_id = self.create_enhanced_element(template)
                
                # Create description version
                version_id = self.create_enhanced_description_version(element_id, template)
                
                # Create variables and mappings
                if template['placeholders']:
                    self.create_enhanced_variable_mappings(element_id, version_id, template)
                
                print(f"     ✅ Stored {template['element_code']} ({template['template_type']})")
                
            except Exception as e:
                print(f"     ❌ Error storing {template['element_code']}: {e}")
    
    def create_enhanced_element(self, template):
        """Create enhanced element entry"""
        
        # Use timestamp for unique codes during testing
        unique_code = f"{template['element_code']}_ENH_{int(time.time())}"
        
        return self.db_manager.create_element(
            element_code=unique_code,
            element_name=template['title'],
            price=template['price']
        )
    
    def create_enhanced_description_version(self, element_id, template):
        """Create enhanced description version"""
        
        return self.db_manager.create_proposal(
            element_id=element_id,
            description_template=template['template'],
            created_by='enhanced_system'
        )
    
    def create_enhanced_variable_mappings(self, element_id, version_id, template):
        """Create enhanced variable mappings"""
        
        print(f"     🔧 Creating variables for {len(template['variables'])} placeholders...")
        
        # Create variables first
        variable_map = {}
        for var in template['variables']:
            try:
                var_id = self.db_manager.create_element_variable(
                    element_id=element_id,
                    variable_name=var['name'],
                    variable_type=var['type'],
                    is_required=var.get('is_required', True),
                    default_value=var['options'][0] if var['options'] else None
                )
                variable_map[var['name']] = var_id
                print(f"       ✅ Variable {var['name']}: ID {var_id}")
                
                # Create variable options
                for option in var['options']:
                    self.db_manager.create_variable_option(var_id, option)
                    
            except Exception as e:
                print(f"       ❌ Variable {var['name']}: {e}")
        
        # Create template mappings
        print(f"     🔧 Creating {len(template['placeholders'])} placeholder mappings...")
        
        with self.db_manager.get_connection() as conn:
            for i, placeholder in enumerate(template['placeholders']):
                if placeholder in variable_map:
                    try:
                        conn.execute(
                            "INSERT INTO template_variable_mappings (version_id, variable_id, placeholder, position) VALUES (?, ?, ?, ?)",
                            (version_id, variable_map[placeholder], placeholder, i + 1)
                        )
                        print(f"       ✅ Mapping {placeholder} → variable {variable_map[placeholder]}")
                    except Exception as e:
                        print(f"       ❌ Mapping {placeholder}: {e}")
                else:
                    print(f"       ❌ No variable found for placeholder {placeholder}")
        
        print(f"     📊 Variable mapping complete: {len(variable_map)} variables, {len(template['placeholders'])} placeholders")
    
    def find_height_differences(self, descriptions):
        """Find height/depth differences"""
        
        differences = []
        
        # Look for height patterns
        height_patterns = [
            (r'hasta\s+(\d+)\s+m\s+de\s+altura', 'altura'),  # "hasta 3 m de altura"
            (r'(\d+)\s+m\s+de\s+altura', 'altura_simple'),  # "3 m de altura"
            (r'profundidad\s+de\s+(\d+)\s*cm', 'profundidad'),  # "profundidad de 15 cm"
        ]
        
        for pattern, semantic_type in height_patterns:
            all_heights = []
            for desc in descriptions:
                heights = re.findall(pattern, desc)
                all_heights.extend(heights)
            
            unique_heights = list(set(all_heights))
            if len(unique_heights) > 1:
                # Create the full match for replacement
                for desc in descriptions:
                    match = re.search(pattern, desc)
                    if match:
                        differences.append({
                            'base_word': match.group(0),  # Full matched text
                            'variations': unique_heights,
                            'semantic_type': semantic_type
                        })
                        break
        
        return differences
    
    def find_finish_differences(self, descriptions):
        """Find finish/acabado differences"""
        
        differences = []
        
        # Look for finish patterns
        finish_patterns = [
            'tipo industrial para revestir',
            'visto con textura lisa', 
            'acabado visto',
            'para revestir',
            'hormigón visto',
            'textura rugosa'
        ]
        
        found_finishes = []
        for desc in descriptions:
            for finish in finish_patterns:
                if finish in desc.lower():
                    found_finishes.append(finish)
        
        unique_finishes = list(set(found_finishes))
        if len(unique_finishes) > 1:
            differences.append({
                'base_word': unique_finishes[0],
                'variations': unique_finishes,
                'semantic_type': 'acabado'
            })
        
        return differences
    
    def find_thickness_differences(self, descriptions):
        """Find thickness/espesor differences"""
        
        differences = []
        
        # Look for thickness patterns
        thickness_patterns = [
            (r'(\d+)\s+cm\s+de\s+espesor', 'espesor'),  # "15 cm de espesor"
            (r'espesor\s+de\s+(\d+)\s*cm', 'espesor_alt'),  # "espesor de 15 cm"
            (r'cuantía\s+aproximada\s+de\s+(\d+)\s*kg/m', 'cuantia'),  # "cuantía aproximada de 120 kg/m³"
        ]
        
        for pattern, semantic_type in thickness_patterns:
            all_values = []
            for desc in descriptions:
                values = re.findall(pattern, desc)
                all_values.extend(values)
            
            unique_values = list(set(all_values))
            if len(unique_values) > 1:
                # Find the full context for replacement
                for desc in descriptions:
                    match = re.search(pattern, desc)
                    if match:
                        differences.append({
                            'base_word': match.group(0),  # Full matched text
                            'variations': unique_values,
                            'semantic_type': semantic_type
                        })
                        break
        
        return differences

def main():
    """Run enhanced template system"""
    
    print("🚀 Starting Enhanced Template System...")
    
    system = EnhancedTemplateSystem()
    results = system.run_enhanced_pipeline(max_elements=5)
    
    print(f"\n✅ Enhanced system complete!")
    print(f"📊 Generated {len(results)} enhanced templates")
    
    for result in results:
        print(f"   - {result['element_code']}: {result['template_type']} ({len(result['placeholders'])} placeholders)")

if __name__ == "__main__":
    main()