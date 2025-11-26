#!/usr/bin/env python3
"""
End-to-End Production System for Dynamic Template Generation
Integrates URL discovery, variation detection, and template creation
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
sys.path.insert(0, str(Path(__file__).parent / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db_manager import DatabaseManager

class ProductionDynamicTemplateSystem:
    """End-to-end system for dynamic template generation from CYPE"""
    
    def __init__(self, db_path=None):
        """Initialize the production system"""
        self.db_path = db_path or str(Path(__file__).parent.parent / "src" / "office_data.db")
        self.db_manager = DatabaseManager(self.db_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.1',  # Prefer Spanish
            'Accept-Charset': 'utf-8;q=1.0,iso-8859-1;q=0.5',  # Prefer UTF-8
            'Accept-Encoding': 'gzip, deflate'
        })
        self.progress = {
            'discovered_urls': 0,
            'elements_found': 0,
            'templates_created': 0,
            'elements_stored': 0,
            'errors': []
        }
    
    def run_production_pipeline(self, max_elements=50):
        """Run the complete production pipeline"""
        
        print("🚀 PRODUCTION DYNAMIC TEMPLATE SYSTEM")
        print("=" * 60)
        print(f"Target: {max_elements} elements maximum")
        print(f"Database: {self.db_path}")
        
        try:
            # Stage 1: Discover element URLs
            print(f"\n📊 STAGE 1: ELEMENT DISCOVERY")
            element_urls = self.discover_element_urls(15)  # Limited discovery for testing
            
            # Stage 2: Group URLs by element code
            print(f"\n📊 STAGE 2: URL GROUPING BY ELEMENT CODE")
            element_groups = self.group_urls_by_element_code(element_urls)
            
            # Stage 3: Generate dynamic templates
            print(f"\n📊 STAGE 3: DYNAMIC TEMPLATE GENERATION")
            template_results = self.generate_dynamic_templates(element_groups, max_elements)
            
            # Stage 4: Store in database
            print(f"\n📊 STAGE 4: DATABASE STORAGE")
            storage_results = self.store_templates_in_database(template_results)
            
            # Final report
            self.print_final_report()
            
            return {
                'success': True,
                'elements_processed': len(template_results),
                'templates_created': self.progress['templates_created'],
                'elements_stored': self.progress['elements_stored']
            }
            
        except Exception as e:
            print(f"\n❌ PIPELINE ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def discover_element_urls(self, max_urls=150):
        """Discover element URLs from CYPE categories"""
        
        print(f"   🔍 Discovering up to {max_urls} element URLs...")
        
        # Start with productive categories known to have elements
        target_categories = [
            "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas.html",
            "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Pilares.html",
            "https://generadordeprecios.info/obra_nueva/Demoliciones/Estructuras/Acero.html",
            "https://generadordeprecios.info/obra_nueva/Estructuras/Madera/Vigas.html",
            "https://generadordeprecios.info/obra_nueva/Estructuras/Acero/Vigas.html"
        ]
        
        discovered_urls = []
        
        for category_url in target_categories:
            if len(discovered_urls) >= max_urls:
                break
                
            print(f"     Scanning: {category_url.split('/')[-1]}")
            
            try:
                category_urls = self.extract_urls_from_category(category_url)
                discovered_urls.extend(category_urls)
                print(f"       Found {len(category_urls)} URLs")
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"       Error: {e}")
                self.progress['errors'].append(f"Category {category_url}: {e}")
        
        # Limit to max_urls
        discovered_urls = discovered_urls[:max_urls]
        self.progress['discovered_urls'] = len(discovered_urls)
        
        print(f"   ✅ Total URLs discovered: {len(discovered_urls)}")
        return discovered_urls
    
    def extract_urls_from_category(self, category_url):
        """Extract element URLs from a category page"""
        
        response = self.session.get(category_url, timeout=30)
        response.raise_for_status()
        
        # Force UTF-8 encoding for Spanish content
        if response.encoding != 'utf-8':
            response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        element_urls = []
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            
            # Convert to absolute URL
            if href.startswith('/'):
                full_url = 'https://generadordeprecios.info' + href
            elif href.startswith('http'):
                full_url = href
            else:
                full_url = urljoin(category_url, href)
            
            # Filter for element URLs
            if self.is_element_url(full_url):
                element_urls.append(full_url)
        
        return element_urls
    
    def is_element_url(self, url):
        """Check if URL is an element page (not category)"""
        
        # Element URL criteria
        if not url.endswith('.html'):
            return False
        
        if '/obra_nueva/' not in url:
            return False
        
        # Skip non-Spain domains
        if 'generadordeprecios.info' not in url:
            return False
        
        # Element URLs typically have underscores or are descriptive
        filename = url.split('/')[-1].replace('.html', '')
        
        # Skip obvious category pages
        if len(filename) < 8:  # Very short names are usually categories
            return False
        
        return True
    
    def group_urls_by_element_code(self, urls):
        """Group URLs by element code to find variations"""
        
        print(f"   📊 Grouping {len(urls)} URLs by element code...")
        
        element_groups = defaultdict(list)
        processed_count = 0
        
        for url in urls:
            try:
                # Quick extraction of element code
                element_code = self.extract_element_code_quick(url)
                
                if element_code and element_code != "UNKNOWN":
                    element_groups[element_code].append(url)
                    processed_count += 1
                
                # Rate limiting and progress
                if processed_count % 10 == 0:
                    print(f"     Processed {processed_count}/{len(urls)} URLs...")
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                self.progress['errors'].append(f"URL {url}: {e}")
                continue
        
        # Filter for elements with multiple URLs (potential variations)
        multi_url_elements = {code: urls for code, urls in element_groups.items() if len(urls) > 1}
        single_url_elements = {code: urls for code, urls in element_groups.items() if len(urls) == 1}
        
        print(f"   ✅ Element analysis:")
        print(f"     Total unique elements: {len(element_groups)}")
        print(f"     Elements with multiple URLs: {len(multi_url_elements)}")
        print(f"     Elements with single URL: {len(single_url_elements)}")
        
        self.progress['elements_found'] = len(element_groups)
        
        # Return both multi-URL (for dynamic templates) and single-URL (for static templates)
        return {
            'multi_url': multi_url_elements,
            'single_url': single_url_elements
        }
    
    def extract_element_code_quick(self, url):
        """Quick extraction of element code from URL"""
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Force UTF-8 encoding for Spanish content
            if response.encoding != 'utf-8':
                response.encoding = 'utf-8'
            
            # Look for element code pattern in response
            code_pattern = r'([A-Z]{2,3}\d{3})'
            code_match = re.search(code_pattern, response.text)
            
            return code_match.group(1) if code_match else None
            
        except Exception:
            return None
    
    def generate_dynamic_templates(self, element_groups, max_elements):
        """Generate dynamic templates from element groups"""
        
        multi_url_elements = element_groups['multi_url']
        single_url_elements = element_groups['single_url']
        
        print(f"   🔧 Generating templates for up to {max_elements} elements...")
        print(f"     Multi-URL elements (dynamic): {len(multi_url_elements)}")
        print(f"     Single-URL elements (static): {len(single_url_elements)}")
        
        template_results = []
        processed_count = 0
        
        # Process multi-URL elements first (they get dynamic templates)
        for element_code, urls in list(multi_url_elements.items()):
            if processed_count >= max_elements:
                break
            
            print(f"\n     Element {processed_count + 1}: {element_code} ({len(urls)} variations)")
            
            try:
                template_result = self.create_dynamic_template(element_code, urls)
                
                if template_result:
                    template_results.append(template_result)
                    self.progress['templates_created'] += 1
                    print(f"       ✅ Dynamic template created")
                else:
                    print(f"       ❌ Template creation failed")
                
                processed_count += 1
                
            except Exception as e:
                print(f"       ❌ Error: {e}")
                self.progress['errors'].append(f"Element {element_code}: {e}")
        
        # Fill remaining slots with single-URL elements (static templates)
        remaining_slots = max_elements - processed_count
        
        if remaining_slots > 0:
            print(f"\n     Processing {remaining_slots} single-URL elements with static templates...")
            
            for element_code, urls in list(single_url_elements.items())[:remaining_slots]:
                try:
                    template_result = self.create_static_template(element_code, urls[0])
                    
                    if template_result:
                        template_results.append(template_result)
                        self.progress['templates_created'] += 1
                    
                    processed_count += 1
                    
                    if processed_count % 5 == 0:
                        print(f"       Processed {processed_count}/{max_elements} total elements...")
                    
                except Exception as e:
                    self.progress['errors'].append(f"Element {element_code}: {e}")
        
        print(f"   ✅ Template generation complete: {len(template_results)} templates created")
        return template_results
    
    def create_dynamic_template(self, element_code, urls):
        """Create dynamic template from multiple URL variations"""
        
        # Extract descriptions from each URL
        descriptions_data = []
        
        for url in urls[:5]:  # Limit to 5 variations max
            desc_data = self.extract_full_element_data(url)
            if desc_data:
                descriptions_data.append(desc_data)
            
            time.sleep(0.8)  # Rate limiting
        
        if len(descriptions_data) < 2:
            # Fall back to static template
            return self.create_static_template(element_code, urls[0])
        
        # Generate template from description variations
        template_result = self.analyze_descriptions_for_template(element_code, descriptions_data)
        
        if template_result:
            template_result['template_type'] = 'dynamic'
            template_result['variations_count'] = len(descriptions_data)
        
        return template_result
    
    def create_static_template(self, element_code, url):
        """Create static template from single URL"""
        
        element_data = self.extract_full_element_data(url)
        
        if not element_data:
            return None
        
        # For static templates, the description IS the template
        return {
            'element_code': element_code,
            'element_name': element_data.get('title', f'Element {element_code}'),
            'template': element_data['description'],
            'placeholders': [],  # No placeholders for static templates
            'variables': [],     # No variables for static templates  
            'template_type': 'static',
            'price': element_data.get('price'),
            'source_urls': [url]
        }
    
    def extract_full_element_data(self, url):
        """Extract complete element data from URL"""
        
        try:
            response = self.session.get(url, timeout=25)
            response.raise_for_status()
            
            # Force UTF-8 encoding for Spanish content
            if response.encoding != 'utf-8':
                response.encoding = 'utf-8'
            
            # Use response.text (decoded) instead of response.content (bytes) 
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract code
            code_pattern = r'([A-Z]{2,3}\d{3})'
            code_match = re.search(code_pattern, response.text)
            code = code_match.group(1) if code_match else "UNKNOWN"
            
            # Extract title
            title_elem = soup.find('h1')
            if not title_elem:
                title_elem = soup.find('title')
            title = title_elem.get_text(strip=True) if title_elem else f"Element {code}"
            
            # Extract technical description
            description = self.find_technical_description(soup)
            
            # Extract price
            price = self.extract_price_from_page(soup)
            
            return {
                'url': url,
                'code': code,
                'title': title,
                'description': self.clean_description(description) if description else "No description available",
                'price': price
            }
            
        except Exception as e:
            return None
    
    def find_technical_description(self, soup):
        """Find technical description in CYPE page using improved extraction"""
        
        # Method 1: Look for tables with technical content (most reliable)
        technical_desc = self.extract_from_tables(soup)
        if technical_desc:
            return technical_desc
        
        # Method 2: Look for paragraphs with construction terms
        technical_desc = self.extract_from_paragraphs(soup)
        if technical_desc:
            return technical_desc
        
        # Method 3: Text analysis method
        technical_desc = self.extract_from_text_analysis(soup)
        if technical_desc:
            return technical_desc
        
        return None
    
    def extract_from_tables(self, soup):
        """Extract technical description from tables"""
        
        tables = soup.find_all('table')
        
        for table in tables:
            for cell in table.find_all(['td', 'th']):
                text = cell.get_text(strip=True)
                
                if (len(text) > 100 and 
                    self.is_technical_content(text) and
                    not self.is_navigation_content(text)):
                    return text
        
        return None
    
    def extract_from_paragraphs(self, soup):
        """Extract from paragraphs with construction terms"""
        
        construction_terms = [
            'demolición', 'forjado', 'viguetas', 'metálicas', 'hormigón', 
            'acero', 'viga', 'pilar', 'martillo', 'neumático', 'aplicación',
            'realizado', 'formado', 'tablero', 'cerámico', 'compresión'
        ]
        
        # Look in paragraphs first
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            
            if (len(text) > 100 and 
                any(term in text.lower() for term in construction_terms) and
                not self.is_navigation_content(text)):
                return text
        
        # Look in divs as fallback
        for div in soup.find_all('div'):
            text = div.get_text(strip=True)
            
            if (len(text) > 100 and len(text) < 1000 and  # Not too long
                any(term in text.lower() for term in construction_terms) and
                not self.is_navigation_content(text)):
                return text
        
        return None
    
    def extract_from_text_analysis(self, soup):
        """Extract by analyzing all text blocks"""
        
        full_text = soup.get_text()
        chunks = [chunk.strip() for chunk in full_text.split('\n\n') if len(chunk.strip()) > 100]
        
        best_chunk = None
        best_score = 0
        
        for chunk in chunks:
            if self.is_navigation_content(chunk):
                continue
            
            score = self.score_technical_content(chunk)
            
            if score > best_score and score > 3:
                best_score = score
                best_chunk = chunk
        
        return best_chunk
    
    def is_technical_content(self, text):
        """Check if text contains technical construction content"""
        
        if not text:
            return False
        
        text_lower = text.lower()
        
        technical_terms = [
            'demolición', 'forjado', 'viguetas', 'metálicas', 'hormigón', 
            'acero', 'viga', 'pilar', 'martillo', 'neumático', 'cerámico',
            'tablero', 'revoltón', 'compresión', 'armado', 'encofrado',
            'aplicación', 'realizado', 'formado', 'machihembrado'
        ]
        
        technical_count = sum(1 for term in technical_terms if term in text_lower)
        
        return technical_count >= 2
    
    def is_navigation_content(self, text):
        """Check if text is navigation/menu content"""
        
        if not text:
            return False
        
        text_lower = text.lower()
        
        nav_indicators = [
            'obra nueva', 'rehabilitación', 'espacios urbanos',
            'actuaciones previas', 'demoliciones', 'acondicionamiento',
            'menú', 'navegación', 'inicio', 'buscar', 'generador de precios',
            'españa', 'argentina', 'mexico', 'chile'
        ]
        
        nav_count = sum(1 for indicator in nav_indicators if indicator in text_lower)
        word_count = len(text_lower.split())
        nav_ratio = nav_count / max(word_count, 1)
        
        return nav_ratio > 0.1 or nav_count >= 3
    
    def score_technical_content(self, text):
        """Score text for technical content quality"""
        
        if not text:
            return 0
        
        score = 0
        text_lower = text.lower()
        
        high_value_terms = ['demolición', 'forjado', 'hormigón', 'acero', 'viga']
        medium_value_terms = ['metálicas', 'cerámico', 'martillo', 'neumático', 'aplicación']
        
        for term in high_value_terms:
            if term in text_lower:
                score += 3
        
        for term in medium_value_terms:
            if term in text_lower:
                score += 2
        
        if self.is_navigation_content(text):
            score -= 5
        
        if 100 < len(text) < 500:
            score += 2
        
        return score
    
    def extract_price_from_page(self, soup):
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
    
    def clean_description(self, text):
        """Clean description text - text should already be in proper UTF-8 Spanish"""
        
        if not text:
            return ""
        
        # Since we're now using proper UTF-8, minimal cleaning needed
        # Just clean whitespace and remove any navigation prefixes
        
        # Remove navigation prefixes that might still appear
        nav_prefixes = [
            'Obra nueva', 'Rehabilitación', 'Espacios urbanos',
            'Generador de Precios', 'Buscar unidades'
        ]
        
        # Remove any leading navigation text
        for prefix in nav_prefixes:
            if text.startswith(prefix):
                # Find where technical content starts (usually after navigation)
                words = text.split()
                for i, word in enumerate(words):
                    if any(tech in word.lower() for tech in ['viga', 'pilar', 'hormigón', 'demolición', 'forjado']):
                        text = ' '.join(words[i:])
                        break
                break
        
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Ensure proper sentence start
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        return text
    
    def analyze_descriptions_for_template(self, element_code, descriptions_data):
        """Analyze descriptions to create dynamic template"""
        
        descriptions = [d['description'] for d in descriptions_data]
        
        # Find differences between descriptions
        differences = self.find_semantic_differences(descriptions)
        
        if not differences:
            # No meaningful differences found, create static template
            return {
                'element_code': element_code,
                'element_name': descriptions_data[0].get('title', f'Element {element_code}'),
                'template': descriptions[0],
                'placeholders': [],
                'variables': [],
                'template_type': 'static_from_multi',
                'price': descriptions_data[0].get('price'),
                'source_urls': [d['url'] for d in descriptions_data]
            }
        
        # Create template with placeholders
        template = descriptions[0]
        placeholders = []
        variables = []
        
        for diff in differences:
            placeholder_name = self.determine_semantic_placeholder(diff)
            placeholder = f"{{{placeholder_name}}}"
            
            # Replace first occurrence
            if diff['base_word'] in template:
                template = template.replace(diff['base_word'], placeholder, 1)
                placeholders.append(placeholder_name)
                
                # Create variable definition
                variables.append({
                    'name': placeholder_name,
                    'type': 'TEXT',
                    'options': diff['variations'],
                    'is_required': True
                })
        
        return {
            'element_code': element_code,
            'element_name': descriptions_data[0].get('title', f'Element {element_code}'),
            'template': template,
            'placeholders': list(set(placeholders)),  # Remove duplicates
            'variables': variables,
            'template_type': 'dynamic',
            'price': descriptions_data[0].get('price'),
            'source_urls': [d['url'] for d in descriptions_data]
        }
    
    def find_semantic_differences(self, descriptions):
        """Find semantic differences between descriptions"""
        
        if len(descriptions) < 2:
            return []
        
        # Split into word sets
        word_sets = [set(desc.split()) for desc in descriptions]
        
        # Find common words
        common_words = word_sets[0]
        for word_set in word_sets[1:]:
            common_words &= word_set
        
        # Find variable words
        all_words = set()
        for word_set in word_sets:
            all_words.update(word_set)
        
        variable_words = all_words - common_words
        
        # Group semantically related variable words
        differences = []
        processed_words = set()
        
        for word in variable_words:
            if word in processed_words or len(word) < 3:
                continue
            
            # Find all variations of this semantic concept
            related_words = self.find_related_words(word, variable_words)
            
            if len(related_words) > 1:
                differences.append({
                    'base_word': word,
                    'variations': list(related_words),
                    'semantic_type': self.classify_semantic_type(related_words)
                })
                
                processed_words.update(related_words)
        
        return differences
    
    def find_related_words(self, base_word, word_set):
        """Find semantically related words"""
        
        related = {base_word}
        base_lower = base_word.lower()
        
        # Find words that are likely variations of the same concept
        for word in word_set:
            word_lower = word.lower()
            
            # Same semantic field indicators
            if (self.are_construction_materials(base_lower, word_lower) or
                self.are_construction_methods(base_lower, word_lower) or
                self.are_dimensions(base_lower, word_lower)):
                related.add(word)
        
        return related
    
    def are_construction_materials(self, word1, word2):
        """Check if words are construction materials"""
        materials = [
            ['tablero', 'revoltón', 'ladrillo', 'cerámico'],
            ['hormigón', 'acero', 'madera'],
            ['metálicas', 'armado', 'visto']
        ]
        
        for group in materials:
            if word1 in group and word2 in group:
                return True
        return False
    
    def are_construction_methods(self, word1, word2):
        """Check if words are construction methods"""
        methods = [
            ['machihembrado', 'formado', 'realizado'],
            ['compresión', 'relleno', 'cascotes'],
            ['montaje', 'desmontaje', 'demolición']
        ]
        
        for group in methods:
            if word1 in group and word2 in group:
                return True
        return False
    
    def are_dimensions(self, word1, word2):
        """Check if words are dimensions"""
        return (re.match(r'\d+x\d+', word1) and re.match(r'\d+x\d+', word2))
    
    def classify_semantic_type(self, words):
        """Classify the semantic type of word group"""
        
        words_str = ' '.join(words).lower()
        
        if any(mat in words_str for mat in ['tablero', 'revoltón', 'cerámico', 'ladrillo']):
            return 'material_type'
        elif any(met in words_str for met in ['machihembrado', 'formado', 'compresión', 'relleno']):
            return 'construction_method'
        elif any(dim in words_str for dim in ['cm', 'mm', 'x']) or re.search(r'\d+x\d+', words_str):
            return 'dimension'
        else:
            return 'general_property'
    
    def determine_semantic_placeholder(self, difference):
        """Determine appropriate placeholder name"""
        
        semantic_type = difference['semantic_type']
        
        type_mapping = {
            'material_type': 'tipo_material',
            'construction_method': 'metodo_construccion', 
            'dimension': 'dimension',
            'general_property': 'propiedad'
        }
        
        return type_mapping.get(semantic_type, 'variable')
    
    def store_templates_in_database(self, template_results):
        """Store generated templates in database"""
        
        print(f"   💾 Storing {len(template_results)} templates in database...")
        
        stored_count = 0
        
        for i, template_result in enumerate(template_results):
            try:
                element_id = self.store_single_template(template_result)
                
                if element_id:
                    stored_count += 1
                    self.progress['elements_stored'] += 1
                
                if (i + 1) % 10 == 0:
                    print(f"     Stored {i + 1}/{len(template_results)} templates...")
                
            except Exception as e:
                print(f"     ❌ Error storing {template_result['element_code']}: {e}")
                self.progress['errors'].append(f"Storage {template_result['element_code']}: {e}")
        
        print(f"   ✅ Storage complete: {stored_count}/{len(template_results)} templates stored")
        return stored_count
    
    def store_single_template(self, template_result):
        """Store a single template in database"""
        
        # Create unique element code with timestamp to avoid conflicts
        timestamp = int(time.time())
        unique_code = f"{template_result['element_code']}_V1_{timestamp}"
        
        # Create element
        element_id = self.db_manager.create_element(
            element_code=unique_code,
            element_name=template_result['element_name'],
            price=template_result.get('price'),
            created_by='Production_Dynamic_Template_System'
        )
        
        # Create variables if dynamic template
        variable_map = {}
        if template_result.get('variables'):
            for var in template_result['variables']:
                var_id = self.db_manager.add_variable(
                    element_id=element_id,
                    variable_name=var['name'],
                    variable_type=var['type'],
                    is_required=var.get('is_required', True)
                )
                variable_map[var['name']] = var_id
        
        # Create template proposal
        version_id = self.db_manager.create_proposal(
            element_id=element_id,
            description_template=template_result['template'],
            created_by='Production_Dynamic_Template_System'
        )
        
        # Create template variable mappings for placeholders
        if template_result.get('placeholders'):
            with self.db_manager.get_connection() as conn:
                for i, placeholder in enumerate(template_result['placeholders']):
                    if placeholder in variable_map:
                        conn.execute(
                            "INSERT INTO template_variable_mappings (version_id, variable_id, placeholder, position) VALUES (?, ?, ?, ?)",
                            (version_id, variable_map[placeholder], placeholder, i)
                        )
        
        return element_id
    
    def print_final_report(self):
        """Print final pipeline report"""
        
        print(f"\n🎉 PRODUCTION PIPELINE COMPLETE!")
        print("=" * 60)
        print(f"📊 FINAL RESULTS:")
        print(f"   URLs discovered: {self.progress['discovered_urls']}")
        print(f"   Elements found: {self.progress['elements_found']}")
        print(f"   Templates created: {self.progress['templates_created']}")
        print(f"   Elements stored: {self.progress['elements_stored']}")
        print(f"   Errors encountered: {len(self.progress['errors'])}")
        
        if self.progress['errors']:
            print(f"\n⚠️  First 5 errors:")
            for error in self.progress['errors'][:5]:
                print(f"     • {error}")
        
        success_rate = (self.progress['elements_stored'] / max(self.progress['elements_found'], 1)) * 100
        print(f"\n✅ Overall success rate: {success_rate:.1f}%")

def main():
    """Run the production system"""
    
    print("🚀 Starting Production Dynamic Template System...")
    
    # Initialize system
    system = ProductionDynamicTemplateSystem()
    
    # Run pipeline with limited testing
    result = system.run_production_pipeline(max_elements=5)
    
    if result['success']:
        print(f"\n🎉 SUCCESS: Created {result['templates_created']} templates for {result['elements_processed']} elements")
    else:
        print(f"\n❌ FAILURE: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()