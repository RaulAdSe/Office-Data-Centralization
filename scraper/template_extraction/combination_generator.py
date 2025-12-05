#!/usr/bin/env python3
"""
Browser-based combination generator for CYPE template extraction.

This module extracts real variable definitions from CYPE's JavaScript-rendered
content using Playwright browser automation, then generates strategic combinations
for template pattern detection.

Key improvements over static HTML parsing:
- Extracts variables from rendered text content (not empty form elements)
- Interacts with forms to capture dynamic description changes
- Uses strategic 3-5 combination sampling for efficient pattern detection
"""

import asyncio
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class VariableType(Enum):
    """Types of variables found in CYPE elements"""
    RADIO = "RADIO"
    TEXT = "TEXT"
    CHECKBOX = "CHECKBOX"
    SELECT = "SELECT"
    CATEGORICAL = "CATEGORICAL"  # Extracted from text structure


@dataclass
class ExtractedVariable:
    """A variable extracted from CYPE content with all its options"""
    name: str
    variable_type: VariableType
    options: List[str]
    default_value: Optional[str] = None
    is_required: bool = True
    description: Optional[str] = None
    unit: Optional[str] = None
    source: str = "text"  # 'text', 'form', 'inferred'

    def __post_init__(self):
        if self.default_value is None and self.options:
            self.default_value = self.options[0]


@dataclass
class VariableCombination:
    """Represents a specific combination of variable values"""
    values: Dict[str, str]
    combination_id: str = ""
    strategy: str = "default"  # 'default', 'single_change', 'pair_change'

    def __post_init__(self):
        if not self.combination_id:
            sorted_items = sorted(self.values.items())
            self.combination_id = "_".join([f"{k}:{v}" for k, v in sorted_items])


@dataclass
class CombinationResult:
    """Result of generating a combination with browser interaction"""
    combination: VariableCombination
    description: str
    success: bool = True
    error: Optional[str] = None


class TextVariableExtractor:
    """
    Extracts variables from CYPE's rendered text content.

    CYPE displays variable options in structured text like:

        Naturaleza del soporte
        - Mortero de cemento
        - Paramento interior
        - Vertical, de hasta 3 m de altura

        Condiciones del soporte
        - Sin patologías
        - Con patologías

    This class parses such structures to extract real variable definitions.
    """

    # Common Spanish construction variable patterns
    VARIABLE_SECTION_PATTERNS = [
        # Pattern: "Variable name" followed by bullet points
        r'(?P<name>[A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]+)[\s:]*\n(?P<options>(?:[-•·]\s*[^\n]+\n?)+)',
        # Pattern: "Variable:" with options
        r'(?P<name>[A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]+):\s*\n(?P<options>(?:[-•·]\s*[^\n]+\n?)+)',
    ]

    # Known construction variable categories
    KNOWN_CATEGORIES = {
        'naturaleza': 'material',
        'condiciones': 'state',
        'ubicación': 'location',
        'acabado': 'finish',
        'espesor': 'dimension',
        'altura': 'dimension',
        'resistencia': 'property',
        'tipo': 'type',
        'forma': 'shape',
    }

    def extract_from_text(self, text: str) -> List[ExtractedVariable]:
        """
        Extract variables from rendered text content.

        Args:
            text: The full text content from the rendered page

        Returns:
            List of ExtractedVariable objects with all detected options
        """
        variables = []

        # Method 1: Structured bullet point sections
        variables.extend(self._extract_bullet_sections(text))

        # Method 2: Labeled option groups
        variables.extend(self._extract_labeled_groups(text))

        # Method 3: Known construction patterns
        variables.extend(self._extract_construction_patterns(text))

        # Deduplicate by name
        seen_names = set()
        unique_variables = []
        for var in variables:
            if var.name.lower() not in seen_names:
                seen_names.add(var.name.lower())
                unique_variables.append(var)

        return unique_variables

    def _extract_bullet_sections(self, text: str) -> List[ExtractedVariable]:
        """Extract variables from bullet-point structured sections"""
        variables = []

        # Split into potential sections
        sections = re.split(r'\n\s*\n', text)

        for section in sections:
            lines = section.strip().split('\n')
            if len(lines) < 2:
                continue

            # First line might be the variable name
            potential_name = lines[0].strip()

            # Check if following lines are bullet points
            options = []
            for line in lines[1:]:
                line = line.strip()
                if re.match(r'^[-•·]\s*', line):
                    option = re.sub(r'^[-•·]\s*', '', line).strip()
                    if option and len(option) > 1:
                        options.append(option)

            # Valid variable if we have a name and multiple options
            if potential_name and len(options) >= 2:
                # Clean the name
                name = re.sub(r'[:\s]+$', '', potential_name)
                if len(name) > 2 and len(name) < 100:
                    variables.append(ExtractedVariable(
                        name=name,
                        variable_type=VariableType.CATEGORICAL,
                        options=options,
                        source="text"
                    ))

        return variables

    def _extract_labeled_groups(self, text: str) -> List[ExtractedVariable]:
        """Extract variables from labeled option groups"""
        variables = []

        # Pattern: "Label: option1, option2, option3" or "Label: option1/option2/option3"
        patterns = [
            r'([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{2,30}):\s*([^.\n]+(?:[,/][^.\n]+)+)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(1).strip()
                options_str = match.group(2).strip()

                # Split by comma or slash
                if '/' in options_str:
                    options = [o.strip() for o in options_str.split('/')]
                else:
                    options = [o.strip() for o in options_str.split(',')]

                # Filter valid options
                options = [o for o in options if o and len(o) > 1 and len(o) < 100]

                if len(options) >= 2:
                    variables.append(ExtractedVariable(
                        name=name,
                        variable_type=VariableType.CATEGORICAL,
                        options=options,
                        source="text"
                    ))

        return variables

    def _extract_construction_patterns(self, text: str) -> List[ExtractedVariable]:
        """Extract variables using known construction domain patterns"""
        variables = []

        # Common Spanish construction patterns
        construction_patterns = {
            'material': {
                'pattern': r'(?:hormigón|acero|madera|aluminio|PVC|hierro|cobre|zinc)',
                'name': 'Material',
            },
            'ubicacion': {
                'pattern': r'(?:interior|exterior|intemperie|cubierto)',
                'name': 'Ubicación',
            },
            'acabado': {
                'pattern': r'(?:brillante|mate|satinado|pulido|rugoso|liso)',
                'name': 'Acabado',
            },
            'resistencia': {
                'pattern': r'(?:alta|media|baja)\s+resistencia|resistencia\s+(?:alta|media|baja)',
                'name': 'Resistencia',
            },
        }

        for category, config in construction_patterns.items():
            matches = re.findall(config['pattern'], text, re.IGNORECASE)
            if len(matches) >= 2:
                # Deduplicate and normalize
                unique_matches = list(dict.fromkeys([m.lower() for m in matches]))
                if len(unique_matches) >= 2:
                    variables.append(ExtractedVariable(
                        name=config['name'],
                        variable_type=VariableType.CATEGORICAL,
                        options=unique_matches,
                        source="inferred"
                    ))

        return variables


class CombinationGenerator:
    """
    Generates strategic variable combinations for template pattern detection.

    Uses a minimal combination strategy that captures all variable effects:
    1. Default combination (all first options)
    2. Single-variable changes (isolate each variable's effect)
    3. Strategic pairs (detect variable interactions)

    This typically requires only 3-5 combinations instead of exhaustive testing.
    """

    def __init__(self, max_combinations: int = 5):
        """
        Args:
            max_combinations: Maximum combinations to generate (5 is sufficient for pattern detection)
        """
        self.max_combinations = max_combinations
        self.text_extractor = TextVariableExtractor()

    def generate_combinations(
        self,
        variables: List[Any]
    ) -> List[VariableCombination]:
        """
        Generate strategic combinations from variable objects.

        Args:
            variables: List of variable objects with name, variable_type, options, default_value

        Returns:
            List of VariableCombination objects for pattern detection
        """
        # Prepare variable options
        var_options = self._prepare_variable_options(variables)

        if not var_options:
            return []

        # Calculate total possible combinations (for logging)
        total = 1
        for opts in var_options.values():
            total *= len(opts)

        print(f"Variables detected: {len(var_options)}")
        print(f"Total possible combinations: {total}")

        # Generate strategic sample
        combinations = self._generate_strategic_combinations(var_options)

        print(f"Generated {len(combinations)} strategic combinations")
        return combinations

    def generate_from_text(self, rendered_text: str) -> Tuple[List[ExtractedVariable], List[VariableCombination]]:
        """
        Extract variables from rendered text and generate combinations.

        This is the primary method for working with real CYPE content.

        Args:
            rendered_text: Full text content from rendered CYPE page

        Returns:
            Tuple of (extracted variables, generated combinations)
        """
        # Extract variables from text
        variables = self.text_extractor.extract_from_text(rendered_text)

        if not variables:
            print("Warning: No variables extracted from text")
            return [], []

        print(f"Extracted {len(variables)} variables from text:")
        for var in variables:
            print(f"  - {var.name}: {len(var.options)} options")

        # Generate combinations
        combinations = self.generate_combinations(variables)

        return variables, combinations

    def _prepare_variable_options(self, variables: List[Any]) -> Dict[str, List[str]]:
        """Prepare variable options from various input formats"""
        var_options = {}

        for var in variables:
            # Handle both dataclass and dict formats
            name = var.name if hasattr(var, 'name') else var.get('name', '')
            var_type = var.variable_type if hasattr(var, 'variable_type') else var.get('variable_type', '')
            options = var.options if hasattr(var, 'options') else var.get('options', [])
            default = var.default_value if hasattr(var, 'default_value') else var.get('default_value')

            # Normalize variable type
            if hasattr(var_type, 'value'):
                var_type = var_type.value
            var_type = str(var_type).upper()

            if var_type in ('RADIO', 'SELECT', 'CATEGORICAL') and options:
                var_options[name] = list(options)
            elif var_type == 'TEXT':
                if default:
                    var_options[name] = [default]
                else:
                    var_options[name] = self._get_common_text_values(name)
            elif var_type == 'CHECKBOX':
                var_options[name] = ['true', 'false']
            elif options:
                var_options[name] = list(options)
            elif default:
                var_options[name] = [default]

        return var_options

    def _generate_strategic_combinations(
        self,
        var_options: Dict[str, List[str]]
    ) -> List[VariableCombination]:
        """
        Generate minimal strategic combinations for pattern detection.

        Strategy:
        1. Default: All first options (baseline)
        2. Single changes: Change one variable at a time (isolate effects)
        3. Pair changes: Change two variables together (detect interactions)
        """
        combinations = []
        var_names = list(var_options.keys())

        # Strategy 1: Default combination (all first options)
        default_combo = {name: opts[0] for name, opts in var_options.items()}
        combinations.append(VariableCombination(
            values=default_combo.copy(),
            strategy="default"
        ))

        # Strategy 2: Single variable changes
        for var_name, options in var_options.items():
            if len(options) > 1:
                # Test with second option (different from default)
                combo = default_combo.copy()
                combo[var_name] = options[1]
                combinations.append(VariableCombination(
                    values=combo,
                    strategy="single_change"
                ))

                # If we have many options, also test the last one
                if len(options) > 2 and len(combinations) < self.max_combinations:
                    combo = default_combo.copy()
                    combo[var_name] = options[-1]
                    combinations.append(VariableCombination(
                        values=combo,
                        strategy="single_change"
                    ))

        # Strategy 3: Pair changes (if still under limit)
        if len(combinations) < self.max_combinations and len(var_names) >= 2:
            for i in range(len(var_names)):
                for j in range(i + 1, len(var_names)):
                    if len(combinations) >= self.max_combinations:
                        break

                    var1, var2 = var_names[i], var_names[j]
                    opts1, opts2 = var_options[var1], var_options[var2]

                    if len(opts1) > 1 and len(opts2) > 1:
                        combo = default_combo.copy()
                        combo[var1] = opts1[1]
                        combo[var2] = opts2[1]
                        combinations.append(VariableCombination(
                            values=combo,
                            strategy="pair_change"
                        ))

        # Deduplicate
        seen_ids = set()
        unique = []
        for combo in combinations:
            if combo.combination_id not in seen_ids:
                seen_ids.add(combo.combination_id)
                unique.append(combo)

        return unique[:self.max_combinations]

    def _get_common_text_values(self, var_name: str) -> List[str]:
        """Get common test values for text/numeric variables"""
        name_lower = var_name.lower()

        dimension_mappings = {
            ('espesor', 'grosor'): ['20', '30', '40', '50'],
            ('diametro', 'diámetro'): ['12', '16', '20', '25'],
            ('longitud', 'largo', 'long'): ['100', '200', '300'],
            ('ancho', 'anchura'): ['50', '100', '150'],
            ('alto', 'altura'): ['200', '250', '300'],
            ('resistencia',): ['25', '30', '35', '40'],
            ('temperatura',): ['20', '25', '30'],
            ('pendiente',): ['1', '2', '3', '5'],
        }

        for keywords, values in dimension_mappings.items():
            if any(kw in name_lower for kw in keywords):
                return values

        # Generic numeric fallback
        return ['10', '20', '30']


class BrowserCombinationGenerator:
    """
    Playwright-based combination generator for real CYPE interaction.

    This class uses browser automation to:
    1. Load CYPE pages with full JavaScript execution
    2. Extract variables from rendered content
    3. Interact with forms to generate combinations
    4. Capture resulting descriptions for each combination

    Requires: playwright (pip install playwright && playwright install)
    """

    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.context = None
        self.text_extractor = TextVariableExtractor()
        self.combination_generator = CombinationGenerator()

    async def __aenter__(self):
        """Async context manager entry"""
        await self._init_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._close_browser()

    async def _init_browser(self):
        """Initialize Playwright browser"""
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self.browser = await self._playwright.chromium.launch(headless=self.headless)
            self.context = await self.browser.new_context(
                locale='es-ES',
                timezone_id='Europe/Madrid',
            )
        except ImportError:
            raise ImportError(
                "Playwright not installed. Run: pip install playwright && playwright install"
            )

    async def _close_browser(self):
        """Close browser and cleanup"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, '_playwright'):
            await self._playwright.stop()

    async def extract_variables_and_combinations(
        self,
        url: str
    ) -> Tuple[List[ExtractedVariable], List[CombinationResult]]:
        """
        Extract variables and generate combinations from a CYPE URL.

        Uses a multi-strategy approach:
        1. First extracts from form elements (fieldsets/legends) - most reliable for CYPE
        2. Supplements with text-based extraction for variables not in forms
        3. Generates strategic combinations from all found variables

        Args:
            url: CYPE element URL

        Returns:
            Tuple of (extracted variables, combination results with descriptions)
        """
        page = await self.context.new_page()

        try:
            # Load page and wait for JavaScript
            await page.goto(url, timeout=self.timeout)
            await page.wait_for_load_state('networkidle')

            # Strategy 1: Extract from form elements (primary method for CYPE)
            # This gets real variable definitions from fieldsets/legends
            form_variables = await self._extract_from_form_elements(page)

            # Strategy 2: Extract from rendered text (supplementary)
            # This catches variables that might not be in form elements
            rendered_text = await page.inner_text('body')
            text_variables = self.text_extractor.extract_from_text(rendered_text)

            # Combine variables, preferring form-extracted ones (more accurate)
            variables = form_variables.copy()
            form_var_names = {v.name.lower() for v in form_variables}

            for text_var in text_variables:
                # Only add text-extracted variables if not already found in form
                if text_var.name.lower() not in form_var_names:
                    variables.append(text_var)

            # Log what we found
            if form_variables:
                print(f"Extracted {len(form_variables)} variables from form elements:")
                for v in form_variables[:5]:
                    print(f"  - {v.name}: {len(v.options)} options")
                if len(form_variables) > 5:
                    print(f"  ... and {len(form_variables) - 5} more")

            if text_variables:
                new_from_text = len(variables) - len(form_variables)
                if new_from_text > 0:
                    print(f"Added {new_from_text} additional variables from text")

            if not variables:
                print("Warning: No variables extracted from page")
                return [], []

            # Generate strategic combinations
            combinations = self.combination_generator.generate_combinations(variables)

            # Generate results for each combination
            results = []
            for combo in combinations:
                result = await self._apply_combination_and_capture(page, combo)
                results.append(result)

            return variables, results

        finally:
            await page.close()

    async def _extract_from_form_elements(self, page) -> List[ExtractedVariable]:
        """
        Extract variables from CYPE form elements.

        CYPE uses fieldsets with legend elements to group radio buttons.
        The legend contains the variable name, and radio buttons have
        generic names like m_1, m_2 but their labels contain the actual options.
        """
        variables = []

        # Method 1: Extract from fieldsets with legends (CYPE's primary structure)
        # CYPE uses: <fieldset><legend>Variable Name</legend>
        #            <div class="form-check"><input type="radio"><label>Option</label></div>
        fieldset_vars = await page.evaluate('''() => {
            const results = [];

            // Find all fieldsets with legends
            document.querySelectorAll('fieldset').forEach(fieldset => {
                const legend = fieldset.querySelector('legend');
                if (!legend) return;

                const varName = legend.innerText?.trim();
                if (!varName || varName.length < 2) return;

                // Find all radio buttons in this fieldset
                const radios = fieldset.querySelectorAll('input[type="radio"]');
                const options = [];

                radios.forEach(radio => {
                    let label = '';

                    // CYPE pattern: radio + sibling label in same .form-check div
                    const formCheck = radio.closest('.form-check, .form-check-inline');
                    if (formCheck) {
                        const labelEl = formCheck.querySelector('label, .form-check-label');
                        if (labelEl) {
                            // Get text content but exclude nested links/images text artifacts
                            label = labelEl.innerText?.trim();
                        }
                    }

                    // Fallback: Check for label with matching 'for' attribute
                    if (!label && radio.id) {
                        const labelFor = document.querySelector(`label[for="${radio.id}"]`);
                        if (labelFor) {
                            label = labelFor.innerText?.trim();
                        }
                    }

                    // Fallback: Check associated labels
                    if (!label && radio.labels && radio.labels.length > 0) {
                        label = radio.labels[0].innerText?.trim();
                    }

                    // Fallback: Next sibling label element
                    if (!label) {
                        const nextEl = radio.nextElementSibling;
                        if (nextEl && nextEl.tagName === 'LABEL') {
                            label = nextEl.innerText?.trim();
                        }
                    }

                    // Fallback: Next sibling text node
                    if (!label && radio.nextSibling && radio.nextSibling.nodeType === 3) {
                        label = radio.nextSibling.textContent?.trim();
                    }

                    // Clean up label - remove empty strings and very long ones
                    if (label && label.length > 0 && label.length < 200) {
                        // Skip if label is just whitespace or a single character
                        if (label.length > 1) {
                            options.push(label);
                        }
                    }
                });

                // Only add if we have at least 2 valid options
                if (options.length >= 2) {
                    results.push({
                        name: varName,
                        options: options,
                        type: 'RADIO'
                    });
                }
            });

            return results;
        }''')

        for var_data in fieldset_vars:
            variables.append(ExtractedVariable(
                name=var_data['name'],
                variable_type=VariableType.RADIO,
                options=var_data['options'],
                source="form"
            ))

        # Method 2: Extract from accordion sections (CYPE's "Opciones" accordion)
        accordion_vars = await page.evaluate('''() => {
            const results = [];

            // Find accordion items that might contain options
            document.querySelectorAll('.accordion-item, [class*="accordion"]').forEach(accordion => {
                const header = accordion.querySelector('.accordion-button, .accordion-header, button');
                if (!header) return;

                const headerText = header.innerText?.trim()?.toLowerCase();
                if (!headerText?.includes('opciones') && !headerText?.includes('options')) return;

                // Found options accordion, now find fieldsets inside
                const content = accordion.querySelector('.accordion-body, .accordion-collapse, [class*="collapse"]');
                if (!content) return;

                content.querySelectorAll('fieldset').forEach(fieldset => {
                    const legend = fieldset.querySelector('legend');
                    if (!legend) return;

                    const varName = legend.innerText?.trim();
                    if (!varName) return;

                    const radios = fieldset.querySelectorAll('input[type="radio"]');
                    const options = [];

                    radios.forEach(radio => {
                        let label = radio.labels?.[0]?.innerText?.trim() ||
                                   radio.nextSibling?.textContent?.trim() ||
                                   radio.nextElementSibling?.innerText?.trim();
                        if (label && label.length > 0 && label.length < 200) {
                            options.push(label);
                        }
                    });

                    if (options.length >= 2) {
                        results.push({
                            name: varName,
                            options: options,
                            type: 'RADIO'
                        });
                    }
                });
            });

            return results;
        }''')

        for var_data in accordion_vars:
            # Avoid duplicates
            if not any(v.name == var_data['name'] for v in variables):
                variables.append(ExtractedVariable(
                    name=var_data['name'],
                    variable_type=VariableType.RADIO,
                    options=var_data['options'],
                    source="form"
                ))

        # Method 3: Find select elements
        selects = await page.evaluate('''() => {
            const result = [];
            document.querySelectorAll('select').forEach(select => {
                const name = select.name || select.id;

                // Try to find associated label
                let label = '';
                if (select.labels && select.labels.length > 0) {
                    label = select.labels[0].innerText?.trim();
                }
                if (!label) {
                    const legend = select.closest('fieldset')?.querySelector('legend');
                    label = legend?.innerText?.trim();
                }
                if (!label) {
                    label = name;
                }

                const options = Array.from(select.options)
                    .map(o => o.text?.trim() || o.value)
                    .filter(o => o && o.length > 0);

                if (label && options.length >= 2) {
                    result.push({
                        name: label,
                        options: options,
                        type: 'SELECT'
                    });
                }
            });
            return result;
        }''')

        for var_data in selects:
            if not any(v.name == var_data['name'] for v in variables):
                variables.append(ExtractedVariable(
                    name=var_data['name'],
                    variable_type=VariableType.SELECT,
                    options=var_data['options'],
                    source="form"
                ))

        return variables

    async def _apply_combination_and_capture(
        self,
        page,
        combination: VariableCombination
    ) -> CombinationResult:
        """Apply a combination to the form and capture the resulting description"""
        try:
            # Apply each variable value
            for var_name, value in combination.values.items():
                await self._set_variable_value(page, var_name, value)

            # Wait for description to update
            await page.wait_for_timeout(500)  # Allow JS to process

            # Capture the description
            description = await self._extract_description(page)

            return CombinationResult(
                combination=combination,
                description=description,
                success=True
            )

        except Exception as e:
            return CombinationResult(
                combination=combination,
                description="",
                success=False,
                error=str(e)
            )

    async def _set_variable_value(self, page, var_name: str, value: str):
        """Set a variable's value in the form"""
        # Try radio button
        radio_selector = f'input[type="radio"][name="{var_name}"]'
        radios = await page.query_selector_all(radio_selector)

        for radio in radios:
            label = await radio.evaluate('''el => {
                return el.labels?.[0]?.innerText ||
                       el.nextSibling?.textContent?.trim() ||
                       el.value;
            }''')
            if label and (value.lower() in label.lower() or label.lower() in value.lower()):
                await radio.click()
                return

        # Try select element
        select_selector = f'select[name="{var_name}"], select[id="{var_name}"]'
        select = await page.query_selector(select_selector)
        if select:
            await select.select_option(label=value)
            return

        # Try text input
        input_selector = f'input[name="{var_name}"], input[id="{var_name}"]'
        input_el = await page.query_selector(input_selector)
        if input_el:
            await input_el.fill(value)

    async def _extract_description(self, page) -> str:
        """
        Extract the element description from a CYPE page.

        CYPE pages have multiple sections. The description is typically found in:
        - A dedicated description section/accordion
        - Paragraphs containing technical specifications
        - Content after "DESCRIPCIÓN" or "Descripción" headers
        """
        # Try CYPE-specific extraction first
        description = await page.evaluate('''() => {
            // Method 1: Find accordion section with "Descripción"
            const accordions = document.querySelectorAll('.accordion-item, [class*="accordion"]');
            for (const accordion of accordions) {
                const header = accordion.querySelector('.accordion-button, button, .accordion-header');
                if (header) {
                    const headerText = header.innerText?.toLowerCase() || '';
                    if (headerText.includes('descripción') || headerText.includes('descripcion')) {
                        const body = accordion.querySelector('.accordion-body, .accordion-collapse .show, [class*="collapse"]');
                        if (body) {
                            return body.innerText?.trim();
                        }
                    }
                }
            }

            // Method 2: Find paragraphs with construction description patterns
            const paragraphs = document.querySelectorAll('p');
            const descriptionPatterns = [
                /aislamiento/i, /sistema/i, /mortero/i, /panel/i,
                /revestimiento/i, /fachada/i, /malla/i, /perfil/i
            ];

            let descText = '';
            for (const p of paragraphs) {
                const text = p.innerText?.trim();
                if (text && text.length > 50) {
                    const matchesPattern = descriptionPatterns.some(pat => pat.test(text));
                    if (matchesPattern) {
                        descText += text + '\\n';
                    }
                }
            }
            if (descText.length > 100) {
                return descText.trim();
            }

            // Method 3: Find specific CYPE content containers
            const contentSelectors = [
                '.card-body',
                '.ficha-contenido',
                '.descripcion-elemento',
                '[class*="desc"]',
            ];

            for (const selector of contentSelectors) {
                const el = document.querySelector(selector);
                if (el) {
                    const text = el.innerText?.trim();
                    // Filter out navigation/menu content
                    if (text && text.length > 100 && !text.startsWith('OBRA NUEVA')) {
                        return text;
                    }
                }
            }

            // Method 4: Find content near the price unit (m², kg, etc.)
            const priceSection = document.querySelector('[class*="precio"], [class*="price"]');
            if (priceSection) {
                const parent = priceSection.parentElement;
                if (parent) {
                    const siblings = Array.from(parent.children);
                    for (const sibling of siblings) {
                        const text = sibling.innerText?.trim();
                        if (text && text.length > 100 && !text.includes('€')) {
                            return text;
                        }
                    }
                }
            }

            return '';
        }''')

        if description and len(description) > 50:
            return description

        # Fallback: Common generic selectors
        selectors = [
            '.descripcion',
            '.description',
            '#descripcion',
            '#description',
            '[data-description]',
            '.element-description',
            '.contenido-descripcion',
        ]

        for selector in selectors:
            element = await page.query_selector(selector)
            if element:
                text = await element.inner_text()
                if text and len(text) > 50:
                    return text.strip()

        return ""


def test_text_extraction():
    """Test the text variable extractor"""
    sample_text = """
    VIGA DE HORMIGÓN ARMADO

    Naturaleza del soporte
    - Mortero de cemento
    - Paramento interior
    - Vertical, de hasta 3 m de altura

    Condiciones del soporte
    - Sin patologías
    - Con patologías leves
    - Con patologías graves

    Acabado: brillante, mate, satinado

    Material utilizado en la construcción incluyendo hormigón y acero.
    """

    extractor = TextVariableExtractor()
    variables = extractor.extract_from_text(sample_text)

    print(f"\nExtracted {len(variables)} variables:")
    for var in variables:
        print(f"\n  {var.name} ({var.variable_type.value}):")
        print(f"    Options: {var.options}")
        print(f"    Source: {var.source}")


def test_combination_generator():
    """Test the combination generator with mock variables"""
    from dataclasses import dataclass

    @dataclass
    class MockVariable:
        name: str
        variable_type: str
        options: List[str] = None
        default_value: str = None

    variables = [
        MockVariable("Naturaleza del soporte", "CATEGORICAL",
                    ["Mortero de cemento", "Paramento interior", "Vertical"]),
        MockVariable("Condiciones", "CATEGORICAL",
                    ["Sin patologías", "Con patologías"]),
        MockVariable("Acabado", "RADIO",
                    ["Brillante", "Mate", "Satinado"]),
        MockVariable("Espesor", "TEXT", default_value="20"),
    ]

    generator = CombinationGenerator(max_combinations=5)
    combinations = generator.generate_combinations(variables)

    print(f"\nGenerated {len(combinations)} combinations:")
    for i, combo in enumerate(combinations, 1):
        print(f"\n  {i}. Strategy: {combo.strategy}")
        for k, v in combo.values.items():
            print(f"     {k}: {v}")


async def test_browser_generator():
    """Test browser-based extraction (requires Playwright)"""
    try:
        async with BrowserCombinationGenerator(headless=True) as generator:
            # This would work with a real CYPE URL
            print("\nBrowser generator initialized successfully")
            print("Ready to extract from CYPE URLs")
    except ImportError as e:
        print(f"\nPlaywright not available: {e}")
        print("Install with: pip install playwright && playwright install")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Text Variable Extraction")
    print("=" * 60)
    test_text_extraction()

    print("\n" + "=" * 60)
    print("Testing Combination Generator")
    print("=" * 60)
    test_combination_generator()

    print("\n" + "=" * 60)
    print("Testing Browser Generator")
    print("=" * 60)
    asyncio.run(test_browser_generator())
