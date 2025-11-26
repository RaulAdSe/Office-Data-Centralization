#!/usr/bin/env python3
"""
Element Data Extractor - Extract structured data from CYPE element pages
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from page_detector import fetch_page, detect_page_type

@dataclass 
class ElementVariable:
    """A variable/option for a CYPE element"""
    name: str
    variable_type: str  # 'TEXT', 'RADIO', 'CHECKBOX', 'SELECT'
    options: List[str]  # For radio/select/checkbox
    default_value: Optional[str]
    is_required: bool = True

@dataclass
class ElementData:
    """Structured data for a CYPE element"""
    code: str
    title: str
    unit: str
    price: Optional[float]
    description: str
    technical_characteristics: str
    measurement_criteria: str
    normativa: str
    variables: List[ElementVariable]
    url: str
    raw_html: str

class ElementExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept-Charset': 'utf-8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
    
    def clean_text(self, text: str) -> str:
        """Clean text from encoding issues and extra whitespace"""
        if not text:
            return ""
        
        # Fix UTF-8 encoding issues (common with Spanish text)
        replacements = {
            # Spanish characters (lowercase)
            'Ã±': 'ñ', 'Ã³': 'ó', 'Ã­': 'í', 'Ã¡': 'á', 'Ã©': 'é', 'Ãº': 'ú',
            'Ã¼': 'ü', 'Ã§': 'ç',
            
            # Units and symbols
            'â‚¬': '€', 'mÂ³': 'm³', 'mÂ²': 'm²', 'Â°': '°',
            
            # Common encoding artifacts
            'Â': '', 'â€™': "'", 'â€œ': '"', 
            
            # HTML-like entities that sometimes appear
            '&nbsp;': ' ', '&amp;': '&', '&lt;': '<', '&gt;': '>',
            
            # Fix specific CYPE terms
            'HORMIGÃN': 'HORMIGÓN',
            'CARACTERÃSTICAS': 'CARACTERÍSTICAS', 
            'TÃCNICAS': 'TÉCNICAS',
            'MEDICIÃN': 'MEDICIÓN',
            'APLICACIÃN': 'APLICACIÓN',
            'CONSTRUCCIÃN': 'CONSTRUCCIÓN',
            'MÃ¡ximo': 'Máximo',
            'MÃ­nimo': 'Mínimo',
            'CarpinterÃ­a': 'Carpintería',
            'SINTÃTICO': 'SINTÉTICO',
            'VIGA EXENTA DE HORMIGÃN VISTO': 'VIGA EXENTA DE HORMIGÓN VISTO',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Try to fix any remaining encoding issues by detecting and converting
        try:
            # If text contains byte-like sequences, try to decode properly
            if 'Ã' in text:
                # This is likely UTF-8 text that was incorrectly decoded as latin-1
                # Try to fix it by encoding as latin-1 then decoding as UTF-8
                text_bytes = text.encode('latin-1')
                text = text_bytes.decode('utf-8', errors='ignore')
        except (UnicodeEncodeError, UnicodeDecodeError):
            # If that fails, just continue with what we have
            pass
        
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def extract_price(self, soup: BeautifulSoup, text: str) -> Optional[float]:
        """Extract price information"""
        # Look for price patterns
        price_patterns = [
            r'(\d+[.,]\d+)\s*€',
            r'Precio[^0-9]*(\d+[.,]\d+)',
            r'(\d+[.,]\d+)\s*euros?',
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    price_str = matches[0].replace(',', '.')
                    return float(price_str)
                except ValueError:
                    continue
        
        return None
    
    def extract_unit(self, soup: BeautifulSoup, text: str) -> str:
        """Extract unit of measurement"""
        # Look for unit patterns
        unit_patterns = [
            r'Precio en España de (m³|m²|m|ud|kg|t|l)\s',
            r'(m³|m²|m|ud|kg|t|l)\s+[A-Z]',
        ]
        
        for pattern in unit_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        
        # Default fallback
        if 'mÂ³' in text or 'm³' in text:
            return 'm³'
        elif 'mÂ²' in text or 'm²' in text:
            return 'm²'
        elif 'm ' in text:
            return 'm'
        else:
            return 'ud'
    
    def extract_section(self, text: str, section_name: str) -> str:
        """Extract content from a specific section"""
        # Patterns for different section headers
        patterns = {
            'CARACTERÍSTICAS TÉCNICAS': [
                r'CARACTERÍSTICAS TÉCNICAS([^A-Z]+?)(?:[A-Z]{3,}|$)',
                r'CARACTERÃ[^\\s]*TICAS TÃ[^\\s]*CNICAS([^A-Z]+?)(?:[A-Z]{3,}|$)',
            ],
            'CRITERIO DE MEDICIÓN': [
                r'CRITERIO DE MEDICIÓN([^A-Z]+?)(?:[A-Z]{3,}|$)',
                r'CRITERIO DE MEDICIÃ[^\\s]*N([^A-Z]+?)(?:[A-Z]{3,}|$)',
            ],
            'NORMATIVA DE APLICACIÓN': [
                r'NORMATIVA DE APLICACIÓN([^A-Z]+?)(?:[A-Z]{3,}|$)',
                r'NORMATIVA DE APLICACIÃ[^\\s]*N([^A-Z]+?)(?:[A-Z]{3,}|$)',
            ]
        }
        
        section_patterns = patterns.get(section_name, [section_name + r'([^A-Z]+?)(?:[A-Z]{3,}|$)'])
        
        for pattern in section_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                return self.clean_text(content)
        
        return ""
    
    def extract_description(self, soup: BeautifulSoup, text: str) -> str:
        """Extract the main description"""
        # Try to find description after "UNIDAD DE OBRA"
        unidad_match = re.search(r'UNIDAD DE OBRA [A-Z]{2,4}\d{3}:[^\\n]+(.*?)(?:CARACTERÍSTICAS|CRITERIO|NORMATIVA|$)', 
                                text, re.DOTALL | re.IGNORECASE)
        if unidad_match:
            description = unidad_match.group(1).strip()
            # Clean up extra text
            description = re.sub(r'^[.\\s]+', '', description)
            description = re.sub(r'Incluye:.*$', '', description, flags=re.DOTALL)
            return self.clean_text(description)
        
        return ""
    
    def extract_variables(self, soup: BeautifulSoup, text: str) -> List[ElementVariable]:
        """Extract customizable variables/options from the page"""
        variables = []
        
        # Extract text inputs (dimensions, etc.)
        text_inputs = soup.find_all('input', type='text')
        for i, inp in enumerate(text_inputs):
            value = inp.get('value')
            if value and value.isdigit():  # Likely a dimension
                var_name = f"dimension_{i+1}"
                variables.append(ElementVariable(
                    name=var_name,
                    variable_type='TEXT', 
                    options=[],
                    default_value=value,
                    is_required=True
                ))
        
        # Extract radio button groups
        radio_groups = {}
        radio_inputs = soup.find_all('input', type='radio')
        for radio in radio_inputs:
            name = radio.get('name', f'option_{len(radio_groups)}')
            if name not in radio_groups:
                radio_groups[name] = []
            
            # Try to find the label/text associated with this radio
            label_text = self.find_radio_label(radio, soup)
            if label_text:
                radio_groups[name].append(label_text.strip())
        
        # Convert radio groups to variables
        for group_name, options in radio_groups.items():
            if options:  # Only add if we found options
                # Clean up group name
                clean_name = self.clean_variable_name(group_name, options)
                variables.append(ElementVariable(
                    name=clean_name,
                    variable_type='RADIO',
                    options=options,
                    default_value=options[0] if options else None,
                    is_required=True
                ))
        
        # Extract checkboxes
        checkboxes = soup.find_all('input', type='checkbox')
        for i, checkbox in enumerate(checkboxes):
            label_text = self.find_radio_label(checkbox, soup)
            if label_text:
                var_name = f"option_{i+1}"
                variables.append(ElementVariable(
                    name=var_name,
                    variable_type='CHECKBOX',
                    options=[label_text],
                    default_value=None,
                    is_required=False
                ))
        
        return variables
    
    def find_radio_label(self, input_elem, soup: BeautifulSoup) -> str:
        """Find the text label associated with a radio/checkbox input"""
        # Method 1: Look for parent or sibling text
        parent = input_elem.parent
        if parent:
            text = parent.get_text(strip=True)
            # Clean up the text (remove the input element's text)
            if text:
                return text[:50]  # Limit length
        
        # Method 2: Look in the form structure around this input
        # This is a simplified approach - real implementation might need
        # more sophisticated parsing based on CYPE's specific HTML structure
        
        return ""
    
    def clean_variable_name(self, group_name: str, options: List[str]) -> str:
        """Create a clean variable name from radio group name and options"""
        if not group_name or group_name.startswith('m_'):
            # Infer name from options
            if any('hormigón' in opt.lower() or 'concrete' in opt.lower() for opt in options):
                return "concrete_type"
            elif any('acero' in opt.lower() or 'steel' in opt.lower() for opt in options):
                return "steel_type"
            elif any('vertido' in opt.lower() or 'pour' in opt.lower() for opt in options):
                return "pouring_method"
            elif any('color' in opt.lower() for opt in options):
                return "color"
            elif any('acabado' in opt.lower() or 'finish' in opt.lower() for opt in options):
                return "finish"
            else:
                return f"material_option_{group_name}"
        
        return group_name
    
    def extract_element_data(self, url: str) -> Optional[ElementData]:
        """Extract all data from an element page"""
        try:
            print(f"Extracting data from: {url}")
            
            # Fetch page
            html = fetch_page(url)
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            
            # Detect page type and get basic info
            page_info = detect_page_type(html, url)
            
            if page_info['type'] != 'element':
                print(f"  ✗ Not an element page")
                return None
            
            code = page_info['code']
            title = self.clean_text(page_info['title'])
            
            if not code:
                print(f"  ✗ Could not extract code")
                return None
            
            print(f"  ✓ Element: {code} - {title}")
            
            # Extract other data
            unit = self.extract_unit(soup, text)
            price = self.extract_price(soup, text)
            description = self.extract_description(soup, text)
            technical_characteristics = self.extract_section(text, 'CARACTERÍSTICAS TÉCNICAS')
            measurement_criteria = self.extract_section(text, 'CRITERIO DE MEDICIÓN')
            normativa = self.extract_section(text, 'NORMATIVA DE APLICACIÓN')
            variables = self.extract_variables(soup, text)
            
            element_data = ElementData(
                code=code,
                title=title,
                unit=unit,
                price=price,
                description=description,
                technical_characteristics=technical_characteristics,
                measurement_criteria=measurement_criteria,
                normativa=normativa,
                variables=variables,
                url=url,
                raw_html=html
            )
            
            print(f"  ✓ Extracted: {unit}, €{price}, {len(description)} chars description, {len(variables)} variables")
            return element_data
            
        except Exception as e:
            print(f"  ✗ Error extracting data: {e}")
            return None

def extract_multiple_elements(urls: List[str]) -> List[ElementData]:
    """Extract data from multiple element URLs"""
    extractor = ElementExtractor()
    results = []
    
    print(f"Extracting data from {len(urls)} element pages...")
    print("="*80)
    
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}]", end=" ")
        
        element_data = extractor.extract_element_data(url)
        if element_data:
            results.append(element_data)
        
        # Add delay between requests
        import time
        time.sleep(1)
    
    print("="*80)
    print(f"Successfully extracted {len(results)} / {len(urls)} elements")
    
    return results

if __name__ == "__main__":
    # Test with known element URLs
    test_urls = [
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html",
        "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Esmaltes/Esmalte_al_agua_para_madera.html",
    ]
    
    print("CYPE Element Data Extractor")
    print("="*80)
    
    results = extract_multiple_elements(test_urls)
    
    print("\nEXTRACTED DATA:")
    print("="*80)
    for element in results:
        print(f"Code: {element.code}")
        print(f"Title: {element.title}")
        print(f"Unit: {element.unit}")
        print(f"Price: €{element.price}")
        print(f"Description: {element.description[:100]}...")
        print(f"Technical: {element.technical_characteristics[:100]}...")
        print(f"Variables: {len(element.variables)}")
        for var in element.variables:
            print(f"  - {var.name} ({var.variable_type}): {var.options[:3]}..." if len(var.options) > 3 else f"  - {var.name} ({var.variable_type}): {var.options}")
        print("-" * 40)