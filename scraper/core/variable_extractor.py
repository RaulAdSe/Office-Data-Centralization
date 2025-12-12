"""
Variable extraction strategies for CYPE HTML content.

Extracts form variables (radio buttons, selects, text inputs) from
static HTML. For JavaScript-rendered content, use
scraper.template_extraction.BrowserExtractor instead.
"""

import re
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

from scraper.models import ElementVariable, VariableType
from .text_utils import clean_text, is_numeric_value


# Patterns for creating meaningful variable names from Spanish construction terms
VARIABLE_NAME_MAPPINGS: Dict[str, str] = {
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

    # Rendimiento/Performance
    'rendimiento (l/m²)': 'rendimiento_l_m2',
    'rendimiento': 'rendimiento',

    # Puntales/Props
    'número de puntales (ud/m²)': 'numero_puntales_ud_m2',
    'puntales (ud/m²)': 'numero_puntales_ud_m2',
    'número de puntales': 'numero_puntales',
    'puntales': 'numero_puntales',

    # Encofrado
    'sistema de encofrado': 'sistema_encofrado',
    'tipo de encofrado': 'tipo_encofrado',
    'número de usos': 'numero_usos',
    'desencofrante': 'agente_desencofrante',

    # General dimensions
    'altura': 'altura',
    'ancho': 'ancho',
    'largo': 'largo',
    'dimensión': 'dimension',
    'material': 'material',
    'acabado': 'tipo_acabado',
    'prelacado': 'prelacado',
}

# Unit patterns for numeric variable detection
UNIT_PATTERNS = [
    r'\(kg/m²\)', r'\(kg/mÂ²\)', r'\(kg/m\)', r'\(t/m³\)', r'\(kg\)',
    r'\(m³/m²\)', r'\(m³/mÂ²\)', r'\(m³/m\)', r'\(l/m²\)', r'\(l/mÂ²\)', r'\(l\)',
    r'\(cm\)', r'\(mm\)', r'\(m\)',
    r'\(MPa\)', r'\(N/mm²\)', r'\(N/mmÂ²\)',
    r'\(°C\)', r'\(%\)',
    r'\(ud/m²\)', r'\(ud/mÂ²\)', r'\(ud\)', r'\(usos\)', r'\(años\)',
]

# Choice patterns for inferring variable names from options
CHOICE_PATTERNS: Dict[str, List[str]] = {
    'prelacado': ['sin prelacado', 'con prelacado', 'prelacado'],
    'ubicacion': ['interior', 'exterior'],
    'acabado_superficie': ['galvanizado', 'sin galvanizar', 'zinc', 'aluminio'],
    'tipo_acabado': ['liso', 'rugoso', 'texturizado', 'brillante', 'mate'],
    'sistema_encofrado': ['recuperable', 'perdido', 'encofrado'],
    'tipo_material': ['metalico', 'madera', 'hormigon', 'acero'],
    'tratamiento': ['tratado', 'sin tratar', 'imprimado'],
    'conexion': ['soldado', 'atornillado', 'pegado'],
    'orientacion': ['vertical', 'horizontal', 'inclinado'],
}


class VariableExtractor:
    """
    Extracts variables from CYPE HTML content using multiple strategies.

    Strategies:
    1. Unit-based detection (numeric variables with units like kg/m²)
    2. Choice variables (radio buttons, dropdowns)
    3. Table-based variables
    4. Form element fallback
    """

    def extract_all(self, soup: BeautifulSoup) -> List[ElementVariable]:
        """
        Extract all variables using all available strategies.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            List of extracted ElementVariable objects
        """
        variables = []

        # Strategy 1: Unit-based numeric variables
        variables.extend(self.extract_by_units(soup))

        # Strategy 2: Choice/selection variables
        variables.extend(self.extract_choice_variables(soup))

        # Strategy 3: Table-based variables
        variables.extend(self.extract_table_variables(soup))

        # Strategy 4: Form element fallback
        opciones_section = self._find_opciones_section(soup)
        if opciones_section:
            form_vars = self.extract_from_form_elements(opciones_section, soup)
            for var in form_vars:
                if not any(v.name == var.name for v in variables):
                    variables.append(var)

        return variables

    def extract_by_units(self, soup: BeautifulSoup) -> List[ElementVariable]:
        """Extract numeric variables by finding text with units."""
        variables = []

        for pattern in UNIT_PATTERNS:
            matches = soup.find_all(string=re.compile(pattern, re.IGNORECASE))

            for match in matches:
                parent = match.parent if hasattr(match, 'parent') else None
                if not parent:
                    continue

                unit_match = re.search(pattern, str(match), re.IGNORECASE)
                if unit_match:
                    unit = unit_match.group().strip('()')

                    nearby_inputs = self._find_nearby_inputs(parent, soup)
                    for inp in nearby_inputs:
                        value = inp.get('value', '')
                        if value and is_numeric_value(value):
                            full_text = str(match).strip()
                            var_name = self._create_variable_name(full_text)

                            if var_name and not any(v.name == var_name for v in variables):
                                variables.append(ElementVariable(
                                    name=var_name,
                                    variable_type=VariableType.NUMERIC,
                                    options=[],
                                    default_value=value,
                                    is_required=True,
                                    description=clean_text(full_text),
                                    unit=unit,
                                    source="form",
                                ))

        return variables

    def extract_choice_variables(self, soup: BeautifulSoup) -> List[ElementVariable]:
        """Extract choice variables from radio buttons and dropdowns."""
        variables = []

        # Radio button groups
        radio_groups: Dict[str, List[Dict]] = {}
        for radio in soup.find_all('input', type='radio'):
            name = radio.get('name', 'unknown')
            if name not in radio_groups:
                radio_groups[name] = []

            label = self._find_comprehensive_label(radio, soup)
            radio_groups[name].append({
                'label': clean_text(label),
                'value': radio.get('value', ''),
                'checked': radio.has_attr('checked'),
            })

        for group_name, options in radio_groups.items():
            if len(options) > 1:
                option_labels = [opt['label'] for opt in options if opt['label'] != "Unknown"]
                default_value = next(
                    (opt['label'] for opt in options if opt['checked']),
                    option_labels[0] if option_labels else None
                )

                if option_labels:
                    var_name = self._create_variable_name_from_options(option_labels) or group_name
                    variables.append(ElementVariable(
                        name=var_name,
                        variable_type=VariableType.RADIO,
                        options=option_labels,
                        default_value=default_value,
                        is_required=True,
                        description=f"Selección entre {len(option_labels)} opciones",
                        source="form",
                    ))

        # Select dropdowns
        for select in soup.find_all('select'):
            options = []
            default_value = None

            for option in select.find_all('option'):
                option_text = clean_text(option.get_text())
                if option_text and option_text != "Unknown":
                    options.append(option_text)
                    if option.has_attr('selected'):
                        default_value = option_text

            if options:
                label = self._find_comprehensive_label(select, soup)
                var_name = self._create_variable_name(label)

                if not var_name:
                    var_name = self._create_variable_name_from_options(options)
                if not var_name:
                    var_name = f"select_{len([v for v in variables if 'select' in v.name]) + 1}"

                # Ensure uniqueness
                existing_names = [v.name for v in variables]
                if var_name in existing_names:
                    counter = 1
                    while f"{var_name}_{counter}" in existing_names:
                        counter += 1
                    var_name = f"{var_name}_{counter}"

                variables.append(ElementVariable(
                    name=var_name,
                    variable_type=VariableType.SELECT,
                    options=options,
                    default_value=default_value or options[0],
                    is_required=True,
                    description=clean_text(label) if label != "Unknown" else "Selección desplegable",
                    source="form",
                ))

        return variables

    def extract_table_variables(self, soup: BeautifulSoup) -> List[ElementVariable]:
        """Extract variables from table structures."""
        variables = []

        for table in soup.find_all('table'):
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label_cell = cells[0]
                    value_cell = cells[1]
                    label_text = clean_text(label_cell.get_text())

                    # Radio buttons in table
                    radios = value_cell.find_all('input', type='radio')
                    if len(radios) > 1:
                        options = []
                        default_value = None

                        for radio in radios:
                            radio_label = self._find_comprehensive_label(radio, soup)
                            if radio_label != "Unknown":
                                options.append(radio_label)
                                if radio.has_attr('checked'):
                                    default_value = radio_label

                        if options:
                            var_name = self._create_variable_name(label_text)
                            if var_name:
                                variables.append(ElementVariable(
                                    name=var_name,
                                    variable_type=VariableType.RADIO,
                                    options=options,
                                    default_value=default_value or options[0],
                                    is_required=True,
                                    description=label_text,
                                    source="form",
                                ))

                    # Selects in table
                    for select in value_cell.find_all('select'):
                        options = [
                            clean_text(opt.get_text())
                            for opt in select.find_all('option')
                            if clean_text(opt.get_text())
                        ]

                        if options:
                            var_name = self._create_variable_name(label_text)
                            if var_name:
                                variables.append(ElementVariable(
                                    name=var_name,
                                    variable_type=VariableType.SELECT,
                                    options=options,
                                    default_value=options[0],
                                    is_required=True,
                                    description=label_text,
                                    source="form",
                                ))

        return variables

    def extract_from_form_elements(
        self, section, soup: BeautifulSoup
    ) -> List[ElementVariable]:
        """Extract variables from form elements in a section."""
        variables = []
        container = section.find_parent() if section.find_parent() else section
        inputs = container.find_all(['input', 'select', 'textarea'])

        # Numeric inputs
        for inp in inputs:
            if inp.get('type') == 'text':
                value = inp.get('value', '')
                if value and is_numeric_value(value):
                    label_text = self._find_comprehensive_label(inp, soup)
                    var_name = self._create_variable_name(label_text)

                    if var_name and not any(v.name == var_name for v in variables):
                        variables.append(ElementVariable(
                            name=var_name,
                            variable_type=VariableType.NUMERIC,
                            options=[],
                            default_value=value,
                            is_required=True,
                            description=clean_text(label_text),
                            source="form",
                        ))

        return variables

    def _find_opciones_section(self, soup: BeautifulSoup):
        """Find the 'Opciones' section in the HTML."""
        indicators = [
            soup.find('h1', string=lambda t: t and 'opciones' in t.lower()),
            soup.find('h2', string=lambda t: t and 'opciones' in t.lower()),
            soup.find('h3', string=lambda t: t and 'opciones' in t.lower()),
            soup.find('h4', string=lambda t: t and 'opciones' in t.lower()),
            soup.find(string=lambda t: t and 'opciones' in t.lower().strip()),
        ]
        return next((i for i in indicators if i), None)

    def _find_nearby_inputs(self, element, soup: BeautifulSoup, max_distance: int = 3):
        """Find input elements near a given element."""
        inputs = []

        container = element.find_parent(['div', 'td', 'tr', 'section', 'form']) or element
        inputs.extend(container.find_all('input', type='text'))

        current = element
        for _ in range(max_distance):
            if hasattr(current, 'next_sibling') and current.next_sibling:
                current = current.next_sibling
                if hasattr(current, 'find_all'):
                    inputs.extend(current.find_all('input', type='text'))

        return inputs[:5]

    def _find_comprehensive_label(self, inp, soup: BeautifulSoup) -> str:
        """Find label using multiple strategies."""
        # Strategy 1: Direct label element
        input_id = inp.get('id')
        if input_id:
            label = soup.find('label', {'for': input_id})
            if label:
                return clean_text(label.get_text())

        # Strategy 2: Parent label
        parent = inp.parent
        if parent and parent.name == 'label':
            return clean_text(parent.get_text())

        # Strategy 3: Table cell structure
        td_parent = inp.find_parent('td')
        if td_parent:
            row = td_parent.find_parent('tr')
            if row:
                cells = row.find_all(['td', 'th'])
                for i, cell in enumerate(cells):
                    if inp in cell.find_all(['input', 'select', 'textarea']):
                        if i > 0:
                            return clean_text(cells[i - 1].get_text())

        # Strategy 4: Preceding text
        prev_sibling = inp.previous_sibling
        while prev_sibling:
            if hasattr(prev_sibling, 'get_text'):
                text = clean_text(prev_sibling.get_text())
                if text and len(text) < 200:
                    return text
            elif hasattr(prev_sibling, 'strip'):
                text = prev_sibling.strip()
                if text and len(text) < 200:
                    return text
            prev_sibling = prev_sibling.previous_sibling

        return "Unknown"

    def _create_variable_name(self, label_text: str) -> Optional[str]:
        """Convert label text to meaningful variable name."""
        if not label_text or label_text == "Unknown":
            return None

        text = clean_text(label_text).lower()

        # Check for direct matches in mappings
        for spanish_term, var_name in VARIABLE_NAME_MAPPINGS.items():
            if spanish_term in text:
                return var_name

        # Create generic name
        cleaned = re.sub(r'\([^)]*\)', '', text)  # Remove units
        cleaned = re.sub(r'[^\w\s]', '', cleaned)  # Remove special chars
        cleaned = re.sub(r'\s+', '_', cleaned.strip())  # Snake case

        if len(cleaned) > 30:
            cleaned = cleaned[:30]

        return cleaned if cleaned else None

    def _create_variable_name_from_options(self, options: List[str]) -> Optional[str]:
        """Create variable name from the options available."""
        if not options:
            return None

        options_text = ' '.join(options).lower()

        for var_name, keywords in CHOICE_PATTERNS.items():
            if any(keyword in options_text for keyword in keywords):
                return var_name

        # Create generic name from first option
        first_option = options[0].lower()
        cleaned = re.sub(r'[^\w\s]', '', first_option)
        cleaned = re.sub(r'\s+', '_', cleaned.strip())

        if len(cleaned) > 25:
            cleaned = cleaned[:25]

        return f"tipo_{cleaned}" if cleaned else None
