"""
Text-based variable extraction from rendered CYPE content.
"""

import re
from typing import List
from .models import ExtractedVariable, VariableType


class TextVariableExtractor:
    """
    Extracts variables from CYPE's rendered text content.

    Parses structured text like:
        Naturaleza del soporte
        - Mortero de cemento
        - Paramento interior

    And labeled groups like:
        Acabado: brillante, mate, satinado
    """

    # Construction domain patterns for inference
    CONSTRUCTION_PATTERNS = {
        'material': (r'(?:hormigón|acero|madera|aluminio|PVC|hierro|cobre|zinc)', 'Material'),
        'ubicacion': (r'(?:interior|exterior|intemperie|cubierto)', 'Ubicación'),
        'acabado': (r'(?:brillante|mate|satinado|pulido|rugoso|liso)', 'Acabado'),
    }

    def extract_from_text(self, text: str) -> List[ExtractedVariable]:
        """Extract variables from rendered text content."""
        variables = []

        variables.extend(self._extract_bullet_sections(text))
        variables.extend(self._extract_labeled_groups(text))
        variables.extend(self._extract_construction_patterns(text))

        return self._deduplicate(variables)

    def _extract_bullet_sections(self, text: str) -> List[ExtractedVariable]:
        """Extract variables from bullet-point structured sections."""
        variables = []
        sections = re.split(r'\n\s*\n', text)

        for section in sections:
            lines = section.strip().split('\n')
            if len(lines) < 2:
                continue

            potential_name = lines[0].strip()
            options = []

            for line in lines[1:]:
                line = line.strip()
                if re.match(r'^[-•·]\s*', line):
                    option = re.sub(r'^[-•·]\s*', '', line).strip()
                    if option and len(option) > 1:
                        options.append(option)

            if potential_name and len(options) >= 2:
                name = re.sub(r'[:\s]+$', '', potential_name)
                if 2 < len(name) < 100:
                    variables.append(ExtractedVariable(
                        name=name,
                        variable_type=VariableType.CATEGORICAL,
                        options=options,
                        source="text"
                    ))

        return variables

    def _extract_labeled_groups(self, text: str) -> List[ExtractedVariable]:
        """Extract variables from 'Label: opt1, opt2' patterns."""
        variables = []
        pattern = r'([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{2,30}):\s*([^.\n]+(?:[,/][^.\n]+)+)'

        for match in re.finditer(pattern, text):
            name = match.group(1).strip()
            options_str = match.group(2).strip()

            separator = '/' if '/' in options_str else ','
            options = [o.strip() for o in options_str.split(separator)]
            options = [o for o in options if o and 1 < len(o) < 100]

            if len(options) >= 2:
                variables.append(ExtractedVariable(
                    name=name,
                    variable_type=VariableType.CATEGORICAL,
                    options=options,
                    source="text"
                ))

        return variables

    def _extract_construction_patterns(self, text: str) -> List[ExtractedVariable]:
        """Extract variables using construction domain patterns."""
        variables = []

        for _, (pattern, name) in self.CONSTRUCTION_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if len(matches) >= 2:
                unique = list(dict.fromkeys([m.lower() for m in matches]))
                if len(unique) >= 2:
                    variables.append(ExtractedVariable(
                        name=name,
                        variable_type=VariableType.CATEGORICAL,
                        options=unique,
                        source="inferred"
                    ))

        return variables

    def _deduplicate(self, variables: List[ExtractedVariable]) -> List[ExtractedVariable]:
        """Remove duplicate variables by name."""
        seen = set()
        unique = []
        for var in variables:
            if var.name.lower() not in seen:
                seen.add(var.name.lower())
                unique.append(var)
        return unique
