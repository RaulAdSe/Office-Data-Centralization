"""
Text-based extraction utilities for CYPE template processing.

This module provides:
- TextVariableExtractor: Extracts variables from rendered text content
- TextExtractor: Compares text versions and builds templates with placeholders
"""

import re
import difflib
from typing import List, Dict, Any, Optional
from scraper.models import ElementVariable, VariableType


class TextVariableExtractor:
    """
    Extracts variables from CYPE's rendered text content.
    """
    CONSTRUCTION_PATTERNS = {
        'material': (r'(?:hormigón|acero|madera|aluminio|PVC|hierro|cobre|zinc)', 'Material'),
        'ubicacion': (r'(?:interior|exterior|intemperie|cubierto)', 'Ubicación'),
        'acabado': (r'(?:brillante|mate|satinado|pulido|rugoso|liso)', 'Acabado'),
    }

    def extract_from_text(self, text: str) -> List[ElementVariable]:
        variables = []
        variables.extend(self._extract_bullet_sections(text))
        variables.extend(self._extract_labeled_groups(text))
        variables.extend(self._extract_construction_patterns(text))
        return self._deduplicate(variables)

    def _extract_bullet_sections(self, text: str) -> List[ElementVariable]:
        variables = []
        sections = re.split(r'\n\s*\n', text)
        for section in sections:
            lines = section.strip().split('\n')
            if len(lines) < 2: continue
            potential_name = lines[0].strip()
            options = []
            for line in lines[1:]:
                line = line.strip()
                if re.match(r'^[-•·]\s*', line):
                    option = re.sub(r'^[-•·]\s*', '', line).strip()
                    if option and len(option) > 1: options.append(option)
            if potential_name and len(options) >= 2:
                name = re.sub(r'[:\s]+$', '', potential_name)
                if 2 < len(name) < 100:
                    variables.append(ElementVariable(name=name, variable_type=VariableType.CATEGORICAL, options=options, source="text"))
        return variables

    def _extract_labeled_groups(self, text: str) -> List[ElementVariable]:
        variables = []
        pattern = r'([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{2,30}):\s*([^.\n]+(?:[,/][^.\n]+)+)'
        for match in re.finditer(pattern, text):
            name = match.group(1).strip()
            options_str = match.group(2).strip()
            separator = '/' if '/' in options_str else ','
            options = [o.strip() for o in options_str.split(separator) if o.strip()]
            if len(options) >= 2:
                variables.append(ElementVariable(name=name, variable_type=VariableType.CATEGORICAL, options=options, source="text"))
        return variables

    def _extract_construction_patterns(self, text: str) -> List[ElementVariable]:
        variables = []
        for _, (pattern, name) in self.CONSTRUCTION_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            unique = list(dict.fromkeys([m.lower() for m in matches]))
            if len(unique) >= 2:
                variables.append(ElementVariable(name=name, variable_type=VariableType.CATEGORICAL, options=unique, source="inferred"))
        return variables

    def _deduplicate(self, variables: List[ElementVariable]) -> List[ElementVariable]:
        seen = set()
        unique = []
        for var in variables:
            if var.name.lower() not in seen:
                seen.add(var.name.lower())
                unique.append(var)
        return unique

class TextExtractor:
    """
    Analyzes texts and detects differences between description versions.
    Used for building templates with variable placeholders.
    """

    def find_differences(self, text1: str, text2: str) -> List[Dict[str, Any]]:
        """Compare two texts and return a list of differences."""
        if not text1 or not text2:
            return []
            
        differences = []
        matcher = difflib.SequenceMatcher(None, text1, text2)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                differences.append({
                    'position': i1,
                    'old_text': text1[i1:i2],
                    'new_text': text2[j1:j2],
                    'type': 'replace'
                })
            elif tag == 'delete':
                differences.append({
                    'position': i1,
                    'old_text': text1[i1:i2],
                    'new_text': '',
                    'type': 'delete'
                })
            elif tag == 'insert':
                differences.append({
                    'position': i1,
                    'old_text': '',
                    'new_text': text2[j1:j2],
                    'type': 'insert'
                })
        return differences

    def map_difference_to_variable(self, difference: Dict[str, Any], variable_changes: List[Dict[str, Any]]) -> Optional[str]:
        """
        Intenta esbrinar quina variable és responsable d'un canvi de text.
        
        Args:
            difference: El diccionari de la diferència trobada (old_text, new_text)
            variable_changes: Llista de canvis de variables [{'variable_name': 'X', 'old_value': 'A', 'new_value': 'B'}]
            
        Returns:
            El nom de la variable responsable, o None si no es troba.
        """
        old_text = difference.get('old_text', '').strip()
        new_text = difference.get('new_text', '').strip()
        
        for var in variable_changes:
            var_name = var.get('variable_name')
            var_old = str(var.get('old_value', '')).strip()
            var_new = str(var.get('new_value', '')).strip()
            
            if not var_old or not var_new:
                continue
            
            # ESTRATÈGIA 1: Coincidència Exacta
            if old_text == var_old and new_text == var_new:
                return var_name
                
            # ESTRATÈGIA 2: Coincidència Parcial (Continguda)
            if (var_old in old_text or old_text in var_old) and \
               (var_new in new_text or new_text in var_new):
                # Filtre de seguretat: ignorem coincidències d'1 sol caràcter si no són exactes
                if len(var_old) > 1 or old_text == var_old:
                    return var_name
                
        return None

    def build_template(self, base_text: str, replacements: List[Dict[str, Any]]) -> str:
        """
        Substitueix les parts del text identificades per placeholders.
        
        Args:
            base_text: El text original complet.
            replacements: Llista de canvis a fer [{'start': 10, 'end': 12, 'variable': 'Gruix'}]
            
        Returns:
            El text final amb el format "Muro de {Gruix} cm..."
        """
        sorted_replacements = sorted(replacements, key=lambda x: x['start'], reverse=True)
        
        template = base_text
        
        for rep in sorted_replacements:
            start = rep['start']
            end = rep['end']
            var_name = rep['variable']
            
            if start < 0 or end > len(base_text):
                continue
                
            template = template[:start] + f"{{{var_name}}}" + template[end:]
            
        return template