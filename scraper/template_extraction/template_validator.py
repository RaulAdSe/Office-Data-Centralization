#!/usr/bin/env python3
"""
Template validator with Spanish construction domain expertise.

This module validates extracted templates against real CYPE descriptions,
using fuzzy matching and construction-specific terminology.
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from .models import ExtractedVariable, VariableCombination, CombinationResult


# =============================================================================
# SPANISH CONSTRUCTION DOMAIN KNOWLEDGE
# =============================================================================

# Construction material synonyms and variations
MATERIAL_SYNONYMS = {
    # Concrete variations
    'hormigón': ['hormigon', 'concreto', 'HA', 'HP', 'HM', 'hormigón armado', 'hormigón pretensado'],
    'hormigón armado': ['HA', 'hormigon armado', 'hormigón reforzado'],
    'hormigón pretensado': ['HP', 'hormigon pretensado'],
    'hormigón en masa': ['HM', 'hormigon en masa'],

    # Steel variations
    'acero': ['acero', 'steel', 'hierro', 'metalico', 'metálico'],
    'acero galvanizado': ['galvanizado', 'acero galv', 'galv.'],
    'acero inoxidable': ['inox', 'inoxidable', 'acero inox'],
    'acero corrugado': ['corrugado', 'barras corrugadas', 'armadura'],

    # Wood variations
    'madera': ['madera', 'wood', 'maderero'],
    'madera laminada': ['laminada', 'GL', 'glulam', 'madera lam'],
    'madera maciza': ['maciza', 'madera sólida'],
    'contrachapado': ['contrachapado', 'plywood', 'tablero'],

    # Masonry variations
    'ladrillo': ['ladrillo', 'cerámico', 'cerámica', 'brick'],
    'bloque': ['bloque', 'block', 'bloque de hormigón'],
    'piedra': ['piedra', 'mampostería', 'stone'],

    # Insulation materials
    'aislamiento': ['aislante', 'aislamiento térmico', 'EPS', 'XPS', 'lana mineral'],
    'EPS': ['poliestireno expandido', 'eps', 'corcho blanco'],
    'XPS': ['poliestireno extruido', 'xps'],
    'lana mineral': ['lana de roca', 'lana de vidrio', 'mineral wool'],

    # Mortars and coatings
    'mortero': ['mortero', 'mortar', 'revoco', 'enfoscado'],
    'mortero de cemento': ['mortero cemento', 'M-5', 'M-10', 'M-15'],
    'yeso': ['yeso', 'escayola', 'plaster'],
    'pintura': ['pintura', 'acabado pintado', 'imprimación'],

    # Aluminum and PVC
    'aluminio': ['aluminio', 'Al', 'aluminum', 'alu'],
    'PVC': ['pvc', 'vinilo', 'plástico'],
}

# Construction location/placement synonyms
LOCATION_SYNONYMS = {
    'interior': ['interior', 'interiores', 'indoor', 'interno'],
    'exterior': ['exterior', 'exteriores', 'outdoor', 'externo', 'intemperie'],
    'fachada': ['fachada', 'facade', 'paramento exterior'],
    'cubierta': ['cubierta', 'tejado', 'roof', 'azotea'],
    'cimentación': ['cimentación', 'foundation', 'zapata', 'losa'],
    'forjado': ['forjado', 'floor slab', 'entrepiso'],
    'muro': ['muro', 'pared', 'wall', 'tabique'],
    'pilar': ['pilar', 'columna', 'column', 'soporte'],
    'viga': ['viga', 'beam', 'dintel', 'cargadero'],
    'solera': ['solera', 'base plate', 'carrera'],
}

# Unit variations
UNIT_SYNONYMS = {
    'mm': ['mm', 'milímetro', 'milímetros', 'milimetro'],
    'cm': ['cm', 'centímetro', 'centímetros', 'centimetro'],
    'm': ['m', 'metro', 'metros', 'ml'],
    'm²': ['m²', 'm2', 'metro cuadrado', 'metros cuadrados'],
    'm³': ['m³', 'm3', 'metro cúbico', 'metros cúbicos'],
    'kg': ['kg', 'kilogramo', 'kilogramos', 'kilo'],
    'N/mm²': ['N/mm²', 'N/mm2', 'MPa', 'megapascal'],
    'kN': ['kN', 'kilonewton', 'kilonewtons'],
}

# Spanish linguistic variations (accent handling)
ACCENT_MAP = {
    'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
    'ü': 'u', 'ñ': 'n',
}

# Common Spanish construction abbreviations
ABBREVIATIONS = {
    'HA': 'hormigón armado',
    'HP': 'hormigón pretensado',
    'HM': 'hormigón en masa',
    'EPS': 'poliestireno expandido',
    'XPS': 'poliestireno extruido',
    'SATE': 'sistema de aislamiento térmico exterior',
    'ETICS': 'sistema de aislamiento térmico exterior',
    'GL': 'madera laminada encolada',
    'fck': 'resistencia característica del hormigón',
    'fyk': 'límite elástico del acero',
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DescriptionData:
    """Description data for validation."""
    combination_id: str
    variable_values: Dict[str, str]
    description: str
    full_html: str = ""
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            'combination_id': self.combination_id,
            'variable_values': self.variable_values,
            'description': self.description,
            'timestamp': self.timestamp
        }


@dataclass
class ValidationResult:
    """Result of template validation."""
    template_accuracy: float
    placeholder_accuracy: Dict[str, float]
    failed_cases: List[str]
    successful_cases: List[str]
    error_analysis: Dict[str, int]
    fuzzy_matches: int = 0
    exact_matches: int = 0

    def to_dict(self) -> dict:
        return {
            'template_accuracy': self.template_accuracy,
            'placeholder_accuracy': self.placeholder_accuracy,
            'failed_cases': self.failed_cases,
            'successful_cases': self.successful_cases,
            'error_analysis': self.error_analysis,
            'fuzzy_matches': self.fuzzy_matches,
            'exact_matches': self.exact_matches,
        }


@dataclass
class ExtractedTemplate:
    """Template extracted from CYPE descriptions."""
    element_code: str
    element_url: str
    description_template: str
    variables: Dict[str, str]  # {var_name: var_type}
    dependencies: List[str] = field(default_factory=list)
    confidence: float = 0.0
    coverage: float = 0.0
    total_combinations_tested: int = 0


# =============================================================================
# FUZZY MATCHING UTILITIES
# =============================================================================

def remove_accents(text: str) -> str:
    """Remove Spanish accents for fuzzy matching."""
    result = text.lower()
    for accented, plain in ACCENT_MAP.items():
        result = result.replace(accented, plain)
    return result


def expand_abbreviations(text: str) -> str:
    """Expand common construction abbreviations."""
    result = text
    for abbr, full in ABBREVIATIONS.items():
        # Case-insensitive replacement
        pattern = re.compile(re.escape(abbr), re.IGNORECASE)
        result = pattern.sub(full, result)
    return result


def get_synonyms(term: str, synonym_dict: dict) -> List[str]:
    """Get all synonyms for a term."""
    term_lower = term.lower()
    term_no_accent = remove_accents(term)

    synonyms = [term_lower, term_no_accent]

    for canonical, variations in synonym_dict.items():
        canonical_lower = canonical.lower()
        canonical_no_accent = remove_accents(canonical)

        # Check if term matches canonical or any variation
        if (term_lower == canonical_lower or
            term_no_accent == canonical_no_accent or
            term_lower in [v.lower() for v in variations] or
            term_no_accent in [remove_accents(v) for v in variations]):
            synonyms.extend([v.lower() for v in variations])
            synonyms.append(canonical_lower)

    return list(set(synonyms))


def fuzzy_match(text1: str, text2: str, threshold: float = 0.7) -> Tuple[bool, float]:
    """
    Check if two texts match using fuzzy matching.

    Returns:
        Tuple of (is_match, similarity_score)
    """
    # Normalize both texts
    norm1 = remove_accents(text1.lower().strip())
    norm2 = remove_accents(text2.lower().strip())

    # Exact match
    if norm1 == norm2:
        return True, 1.0

    # Check if one contains the other
    if norm1 in norm2 or norm2 in norm1:
        return True, 0.9

    # Sequence matching
    ratio = SequenceMatcher(None, norm1, norm2).ratio()

    return ratio >= threshold, ratio


def term_matches_in_text(term: str, text: str, synonym_dict: dict = None) -> bool:
    """Check if a term or its synonyms appear in text."""
    text_normalized = remove_accents(text.lower())

    # Direct match
    term_normalized = remove_accents(term.lower())
    if term_normalized in text_normalized:
        return True

    # Synonym match
    if synonym_dict:
        synonyms = get_synonyms(term, synonym_dict)
        for syn in synonyms:
            if remove_accents(syn) in text_normalized:
                return True

    return False


# =============================================================================
# TEMPLATE VALIDATOR
# =============================================================================

class TemplateValidator:
    """
    Validates extracted templates with Spanish construction domain expertise.

    Features:
    - Fuzzy matching for linguistic variations
    - Construction-specific synonym handling
    - Accent-insensitive comparison
    - Abbreviation expansion
    """

    def __init__(self, accuracy_threshold: float = 0.70):
        """
        Args:
            accuracy_threshold: Minimum similarity for a match (default 70%)
        """
        self.accuracy_threshold = accuracy_threshold

    def validate_template(
        self,
        template: ExtractedTemplate,
        test_descriptions: List[DescriptionData]
    ) -> ValidationResult:
        """
        Validate a template against test descriptions.

        Args:
            template: The extracted template to validate
            test_descriptions: Descriptions with known variable combinations

        Returns:
            ValidationResult with accuracy metrics
        """
        print(f"\nValidating template: {template.description_template[:80]}...")
        print(f"Testing against {len(test_descriptions)} descriptions...")

        successful_cases = []
        failed_cases = []
        placeholder_successes = {var: 0 for var in template.variables.keys()}
        placeholder_totals = {var: 0 for var in template.variables.keys()}
        error_types = {}
        fuzzy_matches = 0
        exact_matches = 0

        for desc in test_descriptions:
            result = self._test_single_description(template, desc)

            if result['success']:
                successful_cases.append(result['case_description'])

                if result.get('exact_match'):
                    exact_matches += 1
                else:
                    fuzzy_matches += 1

                for var, success in result['placeholder_results'].items():
                    if success:
                        placeholder_successes[var] += 1
                    placeholder_totals[var] += 1
            else:
                failed_cases.append(result['case_description'])
                error_type = result['error_type']
                error_types[error_type] = error_types.get(error_type, 0) + 1

                for var in result['placeholder_results']:
                    placeholder_totals[var] += 1

        # Calculate accuracies
        overall_accuracy = len(successful_cases) / len(test_descriptions) if test_descriptions else 0

        placeholder_accuracies = {}
        for var in template.variables.keys():
            if placeholder_totals[var] > 0:
                placeholder_accuracies[var] = placeholder_successes[var] / placeholder_totals[var]
            else:
                placeholder_accuracies[var] = 0.0

        result = ValidationResult(
            template_accuracy=overall_accuracy,
            placeholder_accuracy=placeholder_accuracies,
            failed_cases=failed_cases,
            successful_cases=successful_cases,
            error_analysis=error_types,
            fuzzy_matches=fuzzy_matches,
            exact_matches=exact_matches,
        )

        self._print_validation_results(result)
        return result

    def _test_single_description(
        self,
        template: ExtractedTemplate,
        desc: DescriptionData
    ) -> Dict:
        """Test template against a single description."""
        try:
            generated_desc = self._apply_template(template, desc.variable_values)

            if not generated_desc:
                return {
                    'success': False,
                    'case_description': f"Variables: {desc.variable_values}",
                    'error_type': 'template_application_failed',
                    'placeholder_results': {var: False for var in template.variables.keys()}
                }

            # Calculate similarity with fuzzy matching
            is_match, similarity = self._calculate_similarity_fuzzy(
                generated_desc, desc.description
            )

            # Test individual placeholders
            placeholder_results = self._test_placeholders(template, desc)

            success = similarity >= self.accuracy_threshold
            exact_match = similarity >= 0.95

            return {
                'success': success,
                'exact_match': exact_match,
                'case_description': f"Variables: {desc.variable_values} | Similarity: {similarity:.2f}",
                'error_type': 'low_similarity' if not success else None,
                'placeholder_results': placeholder_results,
                'similarity': similarity,
                'generated': generated_desc,
                'actual': desc.description
            }

        except Exception as e:
            return {
                'success': False,
                'case_description': f"Variables: {desc.variable_values}",
                'error_type': f'exception_{type(e).__name__}',
                'placeholder_results': {var: False for var in template.variables.keys()}
            }

    def _apply_template(
        self,
        template: ExtractedTemplate,
        variables: Dict[str, str]
    ) -> Optional[str]:
        """Apply template with variable values to generate description."""
        result = template.description_template

        for var_name, var_type in template.variables.items():
            placeholder = f"{{{var_name}}}"

            if var_name in variables:
                var_value = variables[var_name]
                transformed_value = self._transform_variable_value(var_value, var_type)
                result = result.replace(placeholder, transformed_value)
            else:
                result = result.replace(placeholder, f"[MISSING_{var_name}]")

        return result

    def _transform_variable_value(self, value: str, var_type: str) -> str:
        """Transform variable value based on its type with domain knowledge."""
        var_type_upper = var_type.upper()

        if var_type_upper == 'NUMERIC':
            try:
                num_value = float(value)
                return str(int(num_value)) if num_value.is_integer() else str(num_value)
            except ValueError:
                return value

        elif var_type_upper == 'MATERIAL':
            # Find canonical form if exists
            value_lower = value.lower()
            for canonical, variations in MATERIAL_SYNONYMS.items():
                if value_lower == canonical.lower() or value_lower in [v.lower() for v in variations]:
                    return canonical
            return value

        elif var_type_upper == 'LOCATION':
            value_lower = value.lower()
            for canonical, variations in LOCATION_SYNONYMS.items():
                if value_lower == canonical.lower() or value_lower in [v.lower() for v in variations]:
                    return canonical
            return value

        elif var_type_upper == 'UNIT':
            value_lower = value.lower()
            for canonical, variations in UNIT_SYNONYMS.items():
                if value_lower == canonical.lower() or value_lower in [v.lower() for v in variations]:
                    return canonical
            return value

        return value

    def _test_placeholders(
        self,
        template: ExtractedTemplate,
        desc: DescriptionData
    ) -> Dict[str, bool]:
        """Test if individual placeholders are correctly placed using fuzzy matching."""
        results = {}

        for var_name, var_type in template.variables.items():
            if var_name in desc.variable_values:
                var_value = desc.variable_values[var_name]

                # Determine which synonym dictionary to use
                synonym_dict = None
                var_type_upper = var_type.upper()
                if var_type_upper == 'MATERIAL':
                    synonym_dict = MATERIAL_SYNONYMS
                elif var_type_upper == 'LOCATION':
                    synonym_dict = LOCATION_SYNONYMS
                elif var_type_upper == 'UNIT':
                    synonym_dict = UNIT_SYNONYMS

                # Check with domain-aware matching
                results[var_name] = self._value_appears_in_description_fuzzy(
                    var_value, desc.description, synonym_dict
                )
            else:
                results[var_name] = False

        return results

    def _value_appears_in_description_fuzzy(
        self,
        var_value: str,
        description: str,
        synonym_dict: Optional[dict] = None
    ) -> bool:
        """Check if variable value appears in description using fuzzy matching."""
        # Normalize
        desc_normalized = remove_accents(description.lower())
        value_normalized = remove_accents(var_value.lower())

        # Direct substring match
        if value_normalized in desc_normalized:
            return True

        # Synonym match
        if synonym_dict:
            if term_matches_in_text(var_value, description, synonym_dict):
                return True

        # Word-level fuzzy matching
        value_words = value_normalized.split()
        desc_words = desc_normalized.split()

        for var_word in value_words:
            if len(var_word) > 3:  # Only check meaningful words
                for desc_word in desc_words:
                    is_match, _ = fuzzy_match(var_word, desc_word, threshold=0.8)
                    if is_match:
                        return True

        return False

    def _calculate_similarity_fuzzy(self, text1: str, text2: str) -> Tuple[bool, float]:
        """Calculate similarity between two texts with domain awareness."""
        # Normalize texts
        norm1 = self._normalize_text_domain(text1)
        norm2 = self._normalize_text_domain(text2)

        if not norm1 and not norm2:
            return True, 1.0

        if not norm1 or not norm2:
            return False, 0.0

        # Tokenize
        words1 = set(norm1.split())
        words2 = set(norm2.split())

        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        jaccard = intersection / union if union > 0 else 0.0

        # Calculate sequence similarity
        sequence = SequenceMatcher(None, norm1, norm2).ratio()

        # Weighted combination (favor Jaccard for technical text)
        similarity = 0.6 * jaccard + 0.4 * sequence

        return similarity >= self.accuracy_threshold, similarity

    def _normalize_text_domain(self, text: str) -> str:
        """Normalize text with domain-specific handling."""
        # Remove accents
        text = remove_accents(text.lower())

        # Expand abbreviations
        text = expand_abbreviations(text)

        # Remove punctuation but keep units
        text = re.sub(r'[^\w\sñ/²³]', ' ', text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _print_validation_results(self, result: ValidationResult):
        """Print validation results."""
        print(f"\n{'='*60}")
        print("VALIDATION RESULTS")
        print('='*60)

        print(f"Overall Template Accuracy: {result.template_accuracy:.2%}")
        print(f"Exact Matches: {result.exact_matches} | Fuzzy Matches: {result.fuzzy_matches}")

        print(f"\nPlaceholder Accuracies:")
        for var, accuracy in result.placeholder_accuracy.items():
            status = "✓" if accuracy > 0.8 else "⚠" if accuracy > 0.5 else "✗"
            print(f"  {status} {var}: {accuracy:.2%}")

        print(f"\nSuccessful Cases: {len(result.successful_cases)}")
        for case in result.successful_cases[:3]:
            print(f"  ✓ {case}")
        if len(result.successful_cases) > 3:
            print(f"  ... and {len(result.successful_cases) - 3} more")

        print(f"\nFailed Cases: {len(result.failed_cases)}")
        for case in result.failed_cases[:3]:
            print(f"  ✗ {case}")
        if len(result.failed_cases) > 3:
            print(f"  ... and {len(result.failed_cases) - 3} more")

        if result.error_analysis:
            print(f"\nError Analysis:")
            for error_type, count in result.error_analysis.items():
                print(f"  {error_type}: {count}")

        # Overall assessment
        if result.template_accuracy >= 0.85:
            print(f"\n🎉 EXCELLENT: Template is highly accurate!")
        elif result.template_accuracy >= 0.70:
            print(f"\n✓ GOOD: Template meets accuracy threshold")
        elif result.template_accuracy >= 0.50:
            print(f"\n⚠️  FAIR: Template may need improvement")
        else:
            print(f"\n✗ POOR: Template needs significant improvement")


# =============================================================================
# QUICK VALIDATION HELPER
# =============================================================================

def validate_extraction_results(
    variables: List[ExtractedVariable],
    results: List[CombinationResult],
    threshold: float = 0.70
) -> ValidationResult:
    """
    Quick validation of extraction results from CYPEExtractor.

    Args:
        variables: Variables from CYPEExtractor.extract()
        results: Results from CYPEExtractor.extract()
        threshold: Accuracy threshold

    Returns:
        ValidationResult
    """
    if not results or len(results) < 2:
        print("Not enough results to validate (need at least 2)")
        return ValidationResult(
            template_accuracy=0.0,
            placeholder_accuracy={},
            failed_cases=["Not enough results"],
            successful_cases=[],
            error_analysis={"insufficient_data": 1}
        )

    # Use first result as template, test against others
    baseline = results[0]
    template_str = baseline.description

    # Simple placeholder detection
    var_dict = {v.name: v.variable_type.value for v in variables}

    template = ExtractedTemplate(
        element_code="TEST",
        element_url="",
        description_template=template_str,
        variables=var_dict,
    )

    test_descriptions = []
    for r in results[1:]:
        test_descriptions.append(DescriptionData(
            combination_id=r.combination.combination_id,
            variable_values=r.combination.values,
            description=r.description,
        ))

    validator = TemplateValidator(accuracy_threshold=threshold)
    return validator.validate_template(template, test_descriptions)


# =============================================================================
# TEST
# =============================================================================

def test_template_validator():
    """Test the template validator with Spanish construction examples."""
    print("Testing Template Validator with Spanish Construction Domain\n")

    # Test fuzzy matching
    print("1. Testing fuzzy matching:")
    test_cases = [
        ("hormigón armado", "hormigon armado", True),
        ("acero galvanizado", "acero galv.", True),
        ("interior", "interiores", True),
        ("EPS", "poliestireno expandido", True),
        ("25 N/mm²", "25 MPa", True),
    ]

    for term1, term2, expected in test_cases:
        is_match, score = fuzzy_match(term1, term2)
        # Check synonym matching too
        syn_match = term_matches_in_text(term1, term2, MATERIAL_SYNONYMS)
        syn_match = syn_match or term_matches_in_text(term1, term2, UNIT_SYNONYMS)
        result = "✓" if (is_match or syn_match) == expected else "✗"
        print(f"  {result} '{term1}' ~ '{term2}': match={is_match or syn_match}, score={score:.2f}")

    # Test template validation
    print("\n2. Testing template validation:")

    template = ExtractedTemplate(
        element_code="TEST001",
        element_url="http://test.com",
        description_template="Viga de {material} para {ubicacion}, resistencia {resistencia} N/mm²",
        variables={
            "material": "MATERIAL",
            "ubicacion": "LOCATION",
            "resistencia": "NUMERIC"
        },
    )

    test_descriptions = [
        DescriptionData(
            combination_id="test1",
            variable_values={"material": "hormigón", "ubicacion": "interior", "resistencia": "25"},
            description="Viga de hormigón armado para interior, resistencia característica 25 N/mm²"
        ),
        DescriptionData(
            combination_id="test2",
            variable_values={"material": "acero", "ubicacion": "exterior", "resistencia": "30"},
            description="Viga de acero galvanizado para exterior, resistencia característica 30 N/mm²"
        ),
        DescriptionData(
            combination_id="test3",
            variable_values={"material": "madera", "ubicacion": "interior", "resistencia": "20"},
            description="Viga de madera laminada para interior, resistencia característica 20 N/mm²"
        )
    ]

    validator = TemplateValidator(accuracy_threshold=0.70)
    result = validator.validate_template(template, test_descriptions)

    print(f"\nValidation completed with accuracy: {result.template_accuracy:.2%}")


if __name__ == "__main__":
    test_template_validator()
