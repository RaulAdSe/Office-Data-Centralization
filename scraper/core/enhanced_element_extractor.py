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
    unit: Optional[str] = None  # Unit for numeric variables (cm, kg/m², etc.)

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
        
        # First, try to extract variables from "Opciones" section intelligently
        opciones_variables = self.extract_variables_from_opciones_section(soup)
        if opciones_variables:
            variables.extend(opciones_variables)
            print(f"  ✓ Extracted {len(opciones_variables)} variables from Opciones section")
        
        # Fallback to traditional extraction if Opciones section not found
        if not opciones_variables:
            # Extract text inputs with context-aware naming
            text_inputs = soup.find_all('input', type='text')
            for i, inp in enumerate(text_inputs):
                value = inp.get('value')
                if value and value.replace('.','').replace(',','').isdigit():
                    # Find context around the input to determine meaningful name
                    var_name, description = self.identify_numeric_variable_context(inp, soup, value)
                    if not var_name:
                        var_name = f"dimension_{i+1}"
                        description = f"Campo numérico {i+1} (dimensiones, cantidades, etc.)"
                    
                    variables.append(ElementVariable(
                        name=var_name,
                        variable_type='NUMERIC',
                        options=[],
                        default_value=value,
                        is_required=True,
                        description=description
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
            },
            # Encofrado/Formwork specific variables
            {
                'name': 'sistema_encofrado',
                'description': 'Sistema de encofrado',
                'keywords': ['sistema de encofrado', 'encofrado recuperable', 'encofrado perdido', 'formwork system'],
                'options': []
            },
            {
                'name': 'tipo_encofrado',
                'description': 'Tipo de material del encofrado',
                'keywords': ['metálico', 'de madera', 'fenólico', 'metal', 'wood', 'phenolic'],
                'options': []
            },
            {
                'name': 'numero_usos',
                'description': 'Número de usos del encofrado',
                'keywords': ['número de usos', 'usos', 'number of uses'],
                'options': []
            },
            {
                'name': 'puntales',
                'description': 'Configuración de puntales',
                'keywords': ['puntales', 'número de puntales', 'props', 'shores'],
                'options': []
            },
            {
                'name': 'desencofrante',
                'description': 'Agente desencofrante',
                'keywords': ['agente desmoldeante', 'desencofrante', 'desmoldeante', 'release agent'],
                'options': []
            },
            {
                'name': 'tablones',
                'description': 'Tablones de madera',
                'keywords': ['tablones de madera', 'wooden planks', 'madera'],
                'options': []
            },
            # Steel/Concrete composite patterns (EHX005, EHX010 type elements)
            {
                'name': 'prelacado',
                'description': 'Tratamiento de prelacado',
                'keywords': ['sin prelacado', 'con prelacado', 'prelacado', 'coating'],
                'options': []
            },
            {
                'name': 'tipo_chapa',
                'description': 'Tipo de chapa colaborante',
                'keywords': ['chapa colaborante', 'chapa metálica', 'steel deck', 'metal sheet'],
                'options': []
            },
            {
                'name': 'acabado_superficie',
                'description': 'Acabado de superficie',
                'keywords': ['galvanizado', 'galvanised', 'zinc', 'coating'],
                'options': []
            },
            {
                'name': 'tipo_hormigon_composite',
                'description': 'Tipo de hormigón para elementos mixtos',
                'keywords': ['haf-25', 'haf-30', 'concrete grade', 'hormigón armado'],
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
    
    def identify_numeric_variable_context(self, input_elem, soup: BeautifulSoup, value: str) -> tuple[str, str]:
        """Identify the context of a numeric input to determine meaningful variable name"""
        # Get surrounding text for context analysis
        label_text = self.find_input_label(input_elem, soup)
        
        # Enhanced context patterns for construction elements
        numeric_patterns = {
            # Encofrado/Formwork patterns
            'numero_usos': {
                'keywords': ['número de usos', 'usos', 'number of uses'],
                'description': 'Número de usos del elemento'
            },
            'numero_puntales': {
                'keywords': ['número de puntales', 'puntales', 'props per'],
                'description': 'Número de puntales por metro cuadrado'
            },
            'rendimiento_desencofrante': {
                'keywords': ['rendimiento', 'l/m', 'litr'],
                'description': 'Rendimiento del desencofrante'
            },
            
            # Steel/Concrete composite patterns (like EHX005)
            'cuantia_acero_negativos': {
                'keywords': ['cuantía de acero para momentos negativos', 'acero negativos', 'momentos negativos'],
                'description': 'Cuantía de acero para momentos negativos'
            },
            'cuantia_acero_positivos': {
                'keywords': ['cuantía de acero para momentos positivos', 'acero positivos', 'momentos positivos'],
                'description': 'Cuantía de acero para momentos positivos'
            },
            'volumen_hormigon': {
                'keywords': ['volumen de hormigón', 'volumen hormigón', 'volume concrete'],
                'description': 'Volumen de hormigón'
            },
            'canto_losa': {
                'keywords': ['canto de la losa', 'canto losa', 'espesor losa', 'slab depth'],
                'description': 'Canto de la losa'
            },
            'altura_perfil': {
                'keywords': ['altura del perfil', 'altura perfil', 'profile height'],
                'description': 'Altura del perfil'
            },
            'intereje': {
                'keywords': ['intereje', 'spacing', 'separación'],
                'description': 'Intereje entre elementos'
            },
            'espesor_chapa': {
                'keywords': ['espesor', 'thickness', 'grosor'],
                'description': 'Espesor de la chapa'
            },
            
            # General dimensions
            'dimension_altura': {
                'keywords': ['altura', 'height', 'alto'],
                'description': 'Dimensión de altura'
            },
            'dimension_ancho': {
                'keywords': ['ancho', 'width', 'largo'],
                'description': 'Dimensión de ancho'
            },
            'dimension_espesor': {
                'keywords': ['espesor', 'thickness', 'grosor'],
                'description': 'Dimensión de espesor'
            }
        }
        
        # Check if the input value or context matches known patterns
        context_text = (label_text + ' ' + str(value)).lower()
        
        for var_name, pattern in numeric_patterns.items():
            for keyword in pattern['keywords']:
                if keyword.lower() in context_text:
                    return var_name, pattern['description']
        
        # Default fallback
        return None, None
    
    def extract_variables_from_opciones_section(self, soup: BeautifulSoup) -> List[ElementVariable]:
        """Intelligently extract ALL types of variables from CYPE's interface"""
        variables = []
        
        # Strategy 1: Extract variables with units (numeric)
        unit_variables = self.extract_variables_by_units(soup)
        variables.extend(unit_variables)
        
        # Strategy 2: Extract choice/selection variables (radio, dropdown)
        choice_variables = self.extract_choice_variables(soup)
        variables.extend(choice_variables)
        
        # Strategy 3: Extract table-based variables
        table_variables = self.extract_table_variables(soup)
        variables.extend(table_variables)
        
        # Strategy 4: Extract form-based variables (fallback)
        opciones_section = self.find_opciones_section(soup)
        if opciones_section:
            form_variables = self.extract_variables_from_form_elements(opciones_section, soup)
            # Only add if not already found by other strategies
            for var in form_variables:
                if not any(v.name == var.name for v in variables):
                    variables.extend([var])
        
        return variables
    
    def extract_variables_by_units(self, soup: BeautifulSoup) -> List[ElementVariable]:
        """Extract variables by finding text with units like (kg/m²), (cm), etc."""
        variables = []
        
        # Common construction units patterns (including encoding variations)
        unit_patterns = [
            # Weight/density (with encoding variations for ²)
            r'\(kg/m²\)', r'\(kg/mÂ²\)', r'\(kg/m\)', r'\(t/m³\)', r'\(kg\)',
            # Volume (with encoding variations)
            r'\(m³/m²\)', r'\(m³/mÂ²\)', r'\(m³/m\)', r'\(l/m²\)', r'\(l/mÂ²\)', r'\(l\)',
            # Length
            r'\(cm\)', r'\(mm\)', r'\(m\)',
            # Pressure/strength (with encoding variations)
            r'\(MPa\)', r'\(N/mm²\)', r'\(N/mmÂ²\)',
            # Temperature/percentage
            r'\(°C\)', r'\(%\)',
            # Construction specific
            r'\(ud/m²\)', r'\(ud/mÂ²\)', r'\(ud\)', r'\(usos\)', r'\(años\)'
        ]
        
        # Find all text that contains units
        for pattern in unit_patterns:
            matches = soup.find_all(string=re.compile(pattern, re.IGNORECASE))
            
            for match in matches:
                # Get the parent element to look for nearby inputs
                parent = match.parent if hasattr(match, 'parent') else None
                if not parent:
                    continue
                
                # Extract unit from the text
                unit_match = re.search(pattern, str(match), re.IGNORECASE)
                if unit_match:
                    unit = unit_match.group().strip('()')
                    
                    # Look for input fields near this text
                    nearby_inputs = self.find_nearby_inputs(parent, soup)
                    
                    for inp in nearby_inputs:
                        value = inp.get('value', '')
                        if value and self.is_numeric_value(value):
                            # Create meaningful variable name from the text containing units
                            full_text = str(match).strip()
                            var_name = self.create_meaningful_variable_name(full_text)
                            
                            if var_name and not any(v.name == var_name for v in variables):
                                variables.append(ElementVariable(
                                    name=var_name,
                                    variable_type='NUMERIC',
                                    options=[],
                                    default_value=value,  # Pure value without units
                                    is_required=True,
                                    description=self.clean_text(full_text),
                                    unit=unit  # Store unit separately
                                ))
                                print(f"  ✓ Found unit-based variable: {var_name} = {value} {unit}")
        
        return variables
    
    def extract_choice_variables(self, soup: BeautifulSoup) -> List[ElementVariable]:
        """Extract choice/selection variables like radio buttons, dropdowns, checkboxes"""
        variables = []
        
        # Extract from radio button groups
        radio_groups = {}
        for radio in soup.find_all('input', type='radio'):
            name = radio.get('name', 'unknown')
            if name not in radio_groups:
                radio_groups[name] = []
            
            label = self.find_comprehensive_label(radio, soup)
            checked = radio.has_attr('checked')
            
            radio_groups[name].append({
                'label': self.clean_text(label),
                'value': radio.get('value', ''),
                'checked': checked
            })
        
        for group_name, options in radio_groups.items():
            if len(options) > 1:  # Only meaningful groups
                option_labels = [opt['label'] for opt in options if opt['label'] != "Unknown"]
                default_value = None
                
                # Find checked option
                for opt in options:
                    if opt['checked']:
                        default_value = opt['label']
                        break
                
                if not default_value and option_labels:
                    default_value = option_labels[0]
                
                if option_labels:
                    var_name = self.create_meaningful_variable_name_from_options(option_labels) or group_name
                    variables.append(ElementVariable(
                        name=var_name,
                        variable_type='RADIO',
                        options=option_labels,
                        default_value=default_value,
                        is_required=True,
                        description=f"Selección entre {len(option_labels)} opciones"
                    ))
                    print(f"  ✓ Found choice variable: {var_name} with {len(option_labels)} options")
        
        # Extract from select dropdowns
        for select in soup.find_all('select'):
            options = []
            default_value = None
            
            for option in select.find_all('option'):
                option_text = self.clean_text(option.get_text())
                if option_text and option_text != "Unknown":
                    options.append(option_text)
                    if option.has_attr('selected'):
                        default_value = option_text
            
            if options:
                label = self.find_comprehensive_label(select, soup)
                
                # Create meaningful variable name from label or options
                var_name = None
                if label and label != "Unknown":
                    var_name = self.create_meaningful_variable_name(label)
                
                # If no meaningful name from label, try to create from options
                if not var_name:
                    var_name = self.create_meaningful_variable_name_from_options(options)
                
                # Last resort: use generic name with counter to avoid conflicts
                if not var_name:
                    dropdown_count = len([v for v in variables if v.name.startswith('select_option')]) + 1
                    var_name = f"select_option_{dropdown_count}"
                
                # Ensure uniqueness within this extraction
                existing_names = [v.name for v in variables]
                if var_name in existing_names:
                    counter = 1
                    base_name = var_name
                    while f"{base_name}_{counter}" in existing_names:
                        counter += 1
                    var_name = f"{base_name}_{counter}"
                
                variables.append(ElementVariable(
                    name=var_name,
                    variable_type='SELECT',
                    options=options,
                    default_value=default_value or options[0],
                    is_required=True,
                    description=self.clean_text(label) if label != "Unknown" else f"Selección desplegable"
                ))
                print(f"  ✓ Found dropdown variable: {var_name} with {len(options)} options")
        
        return variables
    
    def extract_table_variables(self, soup: BeautifulSoup) -> List[ElementVariable]:
        """Extract variables from table structures with options"""
        variables = []
        
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label_cell = cells[0]
                    value_cell = cells[1]
                    
                    label_text = self.clean_text(label_cell.get_text())
                    
                    # Look for radio buttons in value cell
                    radios = value_cell.find_all('input', type='radio')
                    if len(radios) > 1:
                        options = []
                        default_value = None
                        
                        for radio in radios:
                            radio_label = self.find_comprehensive_label(radio, soup)
                            if radio_label != "Unknown":
                                options.append(radio_label)
                                if radio.has_attr('checked'):
                                    default_value = radio_label
                        
                        if options:
                            var_name = self.create_meaningful_variable_name(label_text)
                            if var_name:
                                variables.append(ElementVariable(
                                    name=var_name,
                                    variable_type='RADIO',
                                    options=options,
                                    default_value=default_value or options[0],
                                    is_required=True,
                                    description=label_text
                                ))
                                print(f"  ✓ Found table variable: {var_name} with {len(options)} options")
                    
                    # Look for select dropdown in value cell
                    selects = value_cell.find_all('select')
                    for select in selects:
                        options = []
                        for option in select.find_all('option'):
                            option_text = self.clean_text(option.get_text())
                            if option_text:
                                options.append(option_text)
                        
                        if options:
                            var_name = self.create_meaningful_variable_name(label_text)
                            if var_name:
                                variables.append(ElementVariable(
                                    name=var_name,
                                    variable_type='SELECT',
                                    options=options,
                                    default_value=options[0],
                                    is_required=True,
                                    description=label_text
                                ))
                                print(f"  ✓ Found table dropdown: {var_name} with {len(options)} options")
        
        return variables
    
    def create_meaningful_variable_name_from_options(self, options: List[str]) -> str:
        """Create variable name from the options available"""
        if not options:
            return None
        
        # Analyze options to determine what they represent
        options_text = ' '.join(options).lower()
        
        # Common choice patterns
        choice_patterns = {
            'prelacado': ['sin prelacado', 'con prelacado', 'prelacado'],
            'ubicacion': ['interior', 'exterior'],
            'acabado_superficie': ['galvanizado', 'sin galvanizar', 'zinc', 'aluminio'],
            'tipo_acabado': ['liso', 'rugoso', 'texturizado', 'brillante', 'mate'],
            'sistema_encofrado': ['recuperable', 'perdido', 'encofrado'],
            'tipo_material': ['metalico', 'madera', 'hormigon', 'acero'],
            'tratamiento': ['tratado', 'sin tratar', 'imprimado'],
            'conexion': ['soldado', 'atornillado', 'pegado'],
            'orientacion': ['vertical', 'horizontal', 'inclinado']
        }
        
        for var_name, keywords in choice_patterns.items():
            if any(keyword in options_text for keyword in keywords):
                return var_name
        
        # Create generic meaningful name
        first_option = options[0].lower()
        cleaned = re.sub(r'[^\w\s]', '', first_option)
        cleaned = re.sub(r'\s+', '_', cleaned.strip())
        
        if len(cleaned) > 25:
            cleaned = cleaned[:25]
        
        return f"tipo_{cleaned}" if cleaned else None
    
    def find_nearby_inputs(self, element, soup, max_distance=3):
        """Find input elements near a given element"""
        inputs = []
        
        # Look in the same container
        container = element.find_parent(['div', 'td', 'tr', 'section', 'form']) or element
        inputs.extend(container.find_all('input', type='text'))
        
        # Look in sibling elements
        current = element
        for _ in range(max_distance):
            if hasattr(current, 'next_sibling') and current.next_sibling:
                current = current.next_sibling
                if hasattr(current, 'find_all'):
                    inputs.extend(current.find_all('input', type='text'))
        
        # Look in parent's siblings
        parent = element.parent
        if parent:
            for sibling in parent.find_next_siblings():
                inputs.extend(sibling.find_all('input', type='text'))
                if len(inputs) > 10:  # Prevent too many matches
                    break
        
        return inputs[:5]  # Limit to first 5 matches
    
    def extract_variables_from_form_elements(self, opciones_section, soup) -> List[ElementVariable]:
        """Extract variables from form elements in Opciones section"""
        variables = []
        
        # Look for form elements in the Opciones section
        container = opciones_section.find_parent() if opciones_section.find_parent() else opciones_section
        
        # Find all input elements in the section
        inputs = container.find_all(['input', 'select', 'textarea'])
        
        # Process numeric inputs with labels
        for inp in inputs:
            if inp.get('type') == 'text':
                value = inp.get('value', '')
                if value and self.is_numeric_value(value):
                    # Extract meaningful variable name from label
                    label_text = self.find_comprehensive_label(inp, soup)
                    var_name = self.create_meaningful_variable_name(label_text)
                    
                    # Skip if we already found this variable via units
                    if var_name and not any(v.name == var_name for v in variables):
                        variables.append(ElementVariable(
                            name=var_name,
                            variable_type='NUMERIC',
                            options=[],
                            default_value=value,
                            is_required=True,
                            description=self.clean_text(label_text)
                        ))
        
        # Process radio button groups
        radio_names = set()
        for inp in inputs:
            if inp.get('type') == 'radio':
                name = inp.get('name')
                if name and name not in radio_names:
                    radio_names.add(name)
                    options = []
                    default_value = None
                    
                    # Get all radio buttons with this name
                    radios = container.find_all('input', {'name': name, 'type': 'radio'})
                    for radio in radios:
                        label = self.find_comprehensive_label(radio, soup)
                        if label:
                            options.append(label)
                            if radio.get('checked'):
                                default_value = label
                    
                    if options:
                        var_name = self.create_meaningful_variable_name(name) or name
                        variables.append(ElementVariable(
                            name=var_name,
                            variable_type='RADIO',
                            options=options,
                            default_value=default_value or options[0],
                            is_required=True,
                            description=f"Selección para {name}"
                        ))
        
        return variables
    
    def find_opciones_section(self, soup: BeautifulSoup):
        """Find the 'Opciones' section in the HTML"""
        # Look for headings or text containing "Opciones"
        opciones_indicators = [
            soup.find('h1', string=lambda text: text and 'opciones' in text.lower()),
            soup.find('h2', string=lambda text: text and 'opciones' in text.lower()),
            soup.find('h3', string=lambda text: text and 'opciones' in text.lower()),
            soup.find('h4', string=lambda text: text and 'opciones' in text.lower()),
            soup.find(string=lambda text: text and 'opciones' in text.lower().strip())
        ]
        
        for indicator in opciones_indicators:
            if indicator:
                return indicator
        
        return None
    
    def find_comprehensive_label(self, inp, soup):
        """Find label using multiple strategies"""
        # Strategy 1: Direct label element
        input_id = inp.get('id')
        if input_id:
            label = soup.find('label', {'for': input_id})
            if label:
                return self.clean_text(label.get_text())
        
        # Strategy 2: Parent label
        parent = inp.parent
        if parent and parent.name == 'label':
            return self.clean_text(parent.get_text())
        
        # Strategy 3: Table cell structure  
        td_parent = inp.find_parent('td')
        if td_parent:
            row = td_parent.find_parent('tr')
            if row:
                cells = row.find_all(['td', 'th'])
                for i, cell in enumerate(cells):
                    if inp in cell.find_all(['input', 'select', 'textarea']):
                        # Look for label in previous cells
                        if i > 0:
                            return self.clean_text(cells[i-1].get_text())
        
        # Strategy 4: Preceding text
        prev_sibling = inp.previous_sibling
        while prev_sibling:
            if hasattr(prev_sibling, 'get_text'):
                text = self.clean_text(prev_sibling.get_text())
                if text and len(text) < 200:
                    return text
            elif hasattr(prev_sibling, 'strip'):
                text = prev_sibling.strip()
                if text and len(text) < 200:
                    return text
            prev_sibling = prev_sibling.previous_sibling
        
        return "Unknown"
    
    def create_meaningful_variable_name(self, label_text: str) -> str:
        """Convert label text to meaningful variable name with proper encoding"""
        if not label_text or label_text == "Unknown":
            return None
        
        # First, fix encoding issues
        text = self.fix_encoding_and_clean(label_text)
        text = text.lower()
        
        # Specific mappings for Spanish construction terms
        mappings = {
            # Steel/concrete
            'cuantía de acero para momentos negativos': 'cuantia_acero_negativos',
            'cuantía de acero para momentos positivos': 'cuantia_acero_positivos',
            'acero negativos': 'cuantia_acero_negativos',
            'acero positivos': 'cuantia_acero_positivos',
            'volumen de hormigón': 'volumen_hormigon',
            'canto de la losa': 'canto_losa',
            'altura del perfil': 'altura_perfil',
            'intereje': 'intereje',
            'espesor': 'espesor',
            
            # Rendimiento/Performance with units
            'rendimiento (l/m²)': 'rendimiento_l_m2',
            'rendimiento': 'rendimiento',
            
            # Puntales/Props with units
            'número de puntales (ud/m²)': 'numero_puntales_ud_m2',
            'puntales (ud/m²)': 'numero_puntales_ud_m2',
            'número de puntales': 'numero_puntales',
            'puntales': 'numero_puntales',
            
            # Encofrado
            'sistema de encofrado': 'sistema_encofrado',
            'tipo de encofrado': 'tipo_encofrado',
            'número de usos': 'numero_usos',
            'desencofrante': 'agente_desencofrante',
            
            # General
            'altura': 'altura',
            'ancho': 'ancho',
            'largo': 'largo',
            'dimensión': 'dimension',
            'material': 'material',
            'acabado': 'tipo_acabado',
            'prelacado': 'prelacado'
        }
        
        # Check for direct matches
        for spanish_term, var_name in mappings.items():
            if spanish_term in text:
                return var_name
        
        # Create generic but meaningful name
        # Remove units and parentheses, clean up encoding
        cleaned = re.sub(r'\([^)]*\)', '', text)  # Remove units in parentheses
        cleaned = re.sub(r'[^\w\s]', '', cleaned)  # Remove special chars
        cleaned = re.sub(r'\s+', '_', cleaned.strip())  # Snake case
        
        # Limit length
        if len(cleaned) > 30:
            cleaned = cleaned[:30]
        
        return cleaned if cleaned else None
    
    def fix_encoding_and_clean(self, text: str) -> str:
        """Fix encoding issues and create clean variable names"""
        if not text:
            return ""
        
        # Fix common encoding issues
        encoding_fixes = {
            'Â²': '²',  # Fix squared symbol
            'Â³': '³',  # Fix cubed symbol  
            'â²': '²',
            'â³': '³',
            'mÂ²': 'm²',
            'mÂ³': 'm³',
            'l/mÂ²': 'l/m²',
            'ud/mÂ²': 'ud/m²',
            'kg/mÂ²': 'kg/m²',
            # Spanish character fixes
            'Ã¡': 'á',  # á character
            'Ã©': 'é',  # é character
            'Ã­': 'í',  # í character
            'Ã³': 'ó',  # ó character
            'Ãº': 'ú',  # ú character
            'Ã±': 'ñ',  # ñ character
            'cuantãa': 'cuantía',  # fix cuantía
            'teã³rico': 'teórico',  # fix teórico
            'diãmetro': 'diámetro',  # fix diámetro
        }
        
        for bad, good in encoding_fixes.items():
            text = text.replace(bad, good)
        
        return text
    
    def is_numeric_value(self, value: str) -> bool:
        """Check if a value is numeric"""
        if not value:
            return False
        
        # Handle Spanish decimal format
        value = value.replace(',', '.')
        
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract price from CYPE page tables and elements"""
        try:
            # Method 1: Look for price in table cells (most reliable)
            tables = soup.find_all('table')
            for table in tables:
                cells = table.find_all(['td', 'th'])
                for cell in cells:
                    cell_text = cell.get_text().strip()
                    # Look for price pattern: numbers with decimals and currency
                    price_match = re.search(r'([0-9]+[,\.][0-9]{2})[€âŹâŽ]', cell_text)
                    if price_match:
                        price_str = price_match.group(1)
                        # Convert Spanish decimal format to float
                        price_float = float(price_str.replace(',', '.'))
                        return price_float
            
            # Method 2: Look in meta description as fallback
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                desc_content = meta_desc['content']
                price_match = re.search(r'([0-9]+[,\.][0-9]+)[€âŹâŽ]', desc_content)
                if price_match:
                    price_str = price_match.group(1)
                    price_float = float(price_str.replace(',', '.'))
                    return price_float
            
            return None
            
        except Exception as e:
            print(f"  Warning: Could not extract price: {e}")
            return None
    
    def extract_description(self, soup: BeautifulSoup) -> str:
        """Extract clean description without price from meta description"""
        try:
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                desc_text = meta_desc['content'].strip()
                
                # Clean encoding issues
                desc_text = self.clean_text(desc_text)
                
                # Remove price from beginning using smart detection
                construction_start = re.search(r'\b(Viga|Columna|Pilar|Forjado|Muro|Zapata|Cimiento)', desc_text)
                if construction_start:
                    # Keep everything from the construction element onwards
                    desc_text = desc_text[construction_start.start():]
                else:
                    # Fallback: remove price patterns manually
                    price_patterns = [
                        r'^[0-9]+[,\.][0-9]+[€âŹâŽ]\s*',  # Price at start
                        r'^[0-9\s,\.\€âŹâŽŹŽ]*',  # All price artifacts
                    ]
                    
                    for pattern in price_patterns:
                        desc_text = re.sub(pattern, '', desc_text)
                
                return desc_text.strip()
                
            return "Descripción no disponible"
            
        except Exception as e:
            print(f"  Warning: Could not extract description: {e}")
            return "Error extrayendo descripción"
    
    def extract_unit(self, soup: BeautifulSoup) -> str:
        """Extract unit from CYPE page (m³, m², ud, etc.)"""
        try:
            # Look for units in table headers or cells
            tables = soup.find_all('table')
            for table in tables:
                cells = table.find_all(['td', 'th'])
                for cell in cells:
                    cell_text = cell.get_text().strip()
                    # Common CYPE units
                    unit_match = re.search(r'\b(m³|mÂľ|m²|mÂş|m|ud|kg|t)\b', cell_text)
                    if unit_match:
                        unit = unit_match.group(1)
                        # Clean encoding issues
                        unit = unit.replace('Âľ', '³').replace('Âş', '²')
                        return unit
            
            # Fallback: look in meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                desc_content = meta_desc['content']
                unit_match = re.search(r'de\s+(m³|mÂľ|m²|mÂş|m|ud|kg|t)\s+de', desc_content)
                if unit_match:
                    unit = unit_match.group(1).replace('Âľ', '³').replace('Âş', '²')
                    return unit
            
            return "ud"  # Default unit
            
        except Exception as e:
            print(f"  Warning: Could not extract unit: {e}")
            return "ud"

    def extract_element_data(self, url: str) -> Optional[ElementData]:
        """Extract enhanced element data with properly separated price and description"""
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
            
            # Extract price separately from table cells
            price = self.extract_price(soup)
            if price:
                print(f"  ✓ Price: {price}€")
            else:
                print(f"  ⚠ Price not found")
            
            # Extract unit 
            unit = self.extract_unit(soup)
            print(f"  ✓ Unit: {unit}")
            
            # Extract description without price
            description = self.extract_description(soup)
            print(f"  ✓ Description: {description[:60]}...")
            
            # Extract enhanced variables using new 4-strategy approach
            variables = self.extract_variables_from_opciones_section(soup)
            
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