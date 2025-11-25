#!/usr/bin/env python3
"""
Enhanced Element Data Extractor with proper variable grouping
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from page_detector import fetch_page, detect_page_type

@dataclass 
class ElementVariable:
    """A variable/option for a CYPE element with all possible options"""
    name: str
    variable_type: str  # 'TEXT', 'RADIO', 'CHECKBOX', 'SELECT'
    options: List[str]  # ALL possible options for this variable
    default_value: Optional[str]
    is_required: bool = True
    description: Optional[str] = None

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

class EnhancedElementExtractor:
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
    
    def extract_variables_enhanced(self, soup: BeautifulSoup, text: str) -> List[ElementVariable]:
        """Extract variables with proper grouping of related options"""
        variables = []
        
        # Extract text inputs first
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
                    is_required=True,
                    description=f"Campo numérico {i+1} (dimensiones, cantidades, etc.)"
                ))
        
        # Extract and group radio buttons
        radio_groups = self.extract_radio_groups(soup)
        logical_groups = self.group_radio_options_logically(radio_groups)
        
        for group_name, group_data in logical_groups.items():
            variables.append(ElementVariable(
                name=group_name,
                variable_type='RADIO',
                options=[opt['label'] for opt in group_data['options']],
                default_value=group_data['default'],
                is_required=True,
                description=group_data['description']
            ))
        
        # Extract checkboxes
        checkboxes = soup.find_all('input', type='checkbox')
        for i, checkbox in enumerate(checkboxes):
            label_text = self.find_input_label(checkbox, soup)
            if label_text:
                var_name = f"opcion_{i+1}"
                variables.append(ElementVariable(
                    name=var_name,
                    variable_type='CHECKBOX',
                    options=[self.clean_text(label_text)],
                    default_value=None,
                    is_required=False,
                    description="Característica opcional"
                ))
        
        return variables
    
    def extract_radio_groups(self, soup: BeautifulSoup) -> Dict:
        """Extract all radio button groups"""
        radio_inputs = soup.find_all('input', type='radio')
        radio_groups = {}
        
        for radio in radio_inputs:
            name = radio.get('name', f'radio_{len(radio_groups)}')
            value = radio.get('value')
            checked = radio.has_attr('checked')
            
            if name not in radio_groups:
                radio_groups[name] = []
            
            label_text = self.find_input_label(radio, soup)
            
            radio_groups[name].append({
                'value': value,
                'label': self.clean_text(label_text) if label_text else '',
                'checked': checked
            })
        
        return radio_groups
    
    def group_radio_options_logically(self, radio_groups: Dict) -> Dict:
        """Group individual radio buttons into logical variable groups"""
        logical_groups = {}
        
        # Get all options with their labels
        all_options = []
        for group_name, options in radio_groups.items():
            for option in options:
                all_options.append({
                    'group': group_name,
                    'label': option['label'],
                    'checked': option['checked'],
                    'option': option
                })
        
        # Define logical grouping patterns (Spanish variable names)
        grouping_patterns = [
            {
                'name': 'ubicacion_aplicacion',
                'description': 'Ubicación de aplicación (interior/exterior)',
                'keywords': ['interior', 'exterior'],
                'options': []
            },
            {
                'name': 'nivel_transito', 
                'description': 'Nivel de tránsito o intensidad de uso',
                'keywords': ['mínimo', 'medio', 'máximo', 'minimum', 'medium', 'maximum'],
                'options': []
            },
            {
                'name': 'tipo_elemento',
                'description': 'Tipo de elemento o superficie',
                'keywords': ['barandilla', 'mobiliario', 'carpintería', 'furniture', 'railing'],
                'options': []
            },
            {
                'name': 'color',
                'description': 'Selección de color',
                'keywords': ['color', 'blanco', 'white', 'elegir'],
                'options': []
            },
            {
                'name': 'tipo_acabado',
                'description': 'Tipo de acabado o textura superficial',
                'keywords': ['brillante', 'satinado', 'mate', 'gloss', 'satin', 'matte'],
                'options': []
            },
            {
                'name': 'aplicacion_imprimacion',
                'description': 'Opciones de imprimación o base',
                'keywords': ['imprimación', 'primer', 'selladora'],
                'options': []
            },
            {
                'name': 'numero_manos',
                'description': 'Número de capas de aplicación',
                'keywords': ['una mano', 'dos manos', 'one coat', 'two coats'],
                'options': []
            },
            {
                'name': 'tipo_material',
                'description': 'Tipo de material o producto',
                'keywords': ['esmalte', 'enamel', 'agua', 'water'],
                'options': []
            },
            {
                'name': 'tipo_hormigon',
                'description': 'Tipo de hormigón',
                'keywords': ['convencional', 'autocompactante', 'conventional', 'self-compacting'],
                'options': []
            },
            {
                'name': 'metodo_vertido',
                'description': 'Método de vertido del hormigón',
                'keywords': ['cubilote', 'bomba', 'bucket', 'pump'],
                'options': []
            },
            {
                'name': 'clase_exposicion',
                'description': 'Clase de exposición ambiental',
                'keywords': ['x0', 'xc1', 'xc2', 'xc3', 'xc4', 'xd1', 'xd2', 'xd3', 'xs1', 'xs2', 'xs3'],
                'options': []
            },
            {
                'name': 'tipo_acero',
                'description': 'Tipo de acero de refuerzo',
                'keywords': ['b 400', 'b 500', 'steel type'],
                'options': []
            },
            {
                'name': 'altura_libre',
                'description': 'Altura libre de planta',
                'keywords': ['altura', 'hasta 3', 'entre 3 y 4', 'entre 4 y 5', 'height'],
                'options': []
            },
            {
                'name': 'posicion_viga',
                'description': 'Posición de la viga',
                'keywords': ['exenta', 'recta', 'inclinada', 'beam position'],
                'options': []
            }
        ]
        
        # Assign options to logical groups
        used_groups = set()
        
        for option in all_options:
            label_lower = option['label'].lower()
            assigned = False
            
            for pattern in grouping_patterns:
                if option['group'] not in used_groups:
                    for keyword in pattern['keywords']:
                        if keyword in label_lower:
                            pattern['options'].append(option)
                            used_groups.add(option['group'])
                            assigned = True
                            break
                if assigned:
                    break
        
        # Build final logical groups
        for pattern in grouping_patterns:
            if pattern['options']:
                # Find default (checked) option
                default = None
                for opt in pattern['options']:
                    if opt['checked']:
                        default = opt['label']
                        break
                
                logical_groups[pattern['name']] = {
                    'options': pattern['options'],
                    'default': default or (pattern['options'][0]['label'] if pattern['options'] else None),
                    'description': pattern['description']
                }
        
        # Handle any ungrouped options as individual variables
        for group_name, options in radio_groups.items():
            if group_name not in used_groups:
                for option in options:
                    var_name = f"opcion_adicional_{group_name}"
                    logical_groups[var_name] = {
                        'options': [{'label': option['label']}],
                        'default': option['label'] if option['checked'] else None,
                        'description': 'Opción adicional'
                    }
        
        return logical_groups
    
    def find_input_label(self, input_elem, soup: BeautifulSoup) -> str:
        """Find the text label associated with an input element"""
        # Method 1: Look for <label> tag
        input_id = input_elem.get('id')
        if input_id:
            label = soup.find('label', {'for': input_id})
            if label:
                return label.get_text(strip=True)
        
        # Method 2: Look for parent label
        parent = input_elem.parent
        if parent and parent.name == 'label':
            return parent.get_text(strip=True)
        
        # Method 3: Look for sibling text
        next_sibling = input_elem.next_sibling
        if next_sibling and hasattr(next_sibling, 'strip'):
            text = next_sibling.strip()
            if text and len(text) < 100:
                return text
        
        # Method 4: Look in parent context (limited length)
        if parent:
            parent_text = parent.get_text(strip=True)
            if parent_text and len(parent_text) < 100:
                return parent_text
        
        return "Unknown Option"
    
    def extract_element_data(self, url: str) -> Optional[ElementData]:
        """Extract enhanced element data with properly grouped variables"""
        try:
            print(f"Extracting enhanced data from: {url}")
            
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
            
            # Extract other data using existing methods (would need to copy from original)
            # For this demo, I'll use simplified versions
            unit = "ud"  # Simplified
            price = None  # Would extract properly
            description = self.clean_text(text[:500])  # Simplified
            
            # Extract enhanced variables
            variables = self.extract_variables_enhanced(soup, text)
            
            element_data = ElementData(
                code=code,
                title=title,
                unit=unit,
                price=price,
                description=description,
                technical_characteristics="",
                measurement_criteria="",
                normativa="",
                variables=variables,
                url=url,
                raw_html=html
            )
            
            print(f"  ✓ Extracted: {len(variables)} grouped variables")
            return element_data
            
        except Exception as e:
            print(f"  ✗ Error extracting enhanced data: {e}")
            return None

# Demo function
def demo_enhanced_extraction():
    """Demo the enhanced variable extraction"""
    
    extractor = EnhancedElementExtractor()
    url = "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Esmaltes/Esmalte_al_agua_para_madera.html"
    
    element = extractor.extract_element_data(url)
    
    if element:
        print(f"\n🎯 ENHANCED EXTRACTION RESULTS:")
        print("="*50)
        print(f"Code: {element.code}")
        print(f"Title: {element.title}")
        print(f"Variables: {len(element.variables)}")
        print()
        
        for i, var in enumerate(element.variables, 1):
            print(f"{i}. {var.name} ({var.variable_type})")
            print(f"   Description: {var.description}")
            print(f"   Options: {var.options}")
            print(f"   Default: {var.default_value}")
            print()

if __name__ == "__main__":
    demo_enhanced_extraction()