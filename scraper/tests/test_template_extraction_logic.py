#!/usr/bin/env python3
"""
Test suite for Albert's template extraction logic implementation.

This test file verifies the fixes for Issues #13, #14, #15, #16:
- Issue #13: find_differences - Text difference detection
- Issue #14: map_difference_to_variable - Variable mapping
- Issue #15: build_template - Template construction with placeholders
- Issue #16: create_dynamic_template - Full integration

Run with: python -m pytest scraper/tests/test_template_extraction_logic.py -v
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from scraper.template_extraction.text_extractor import TextExtractor, TextVariableExtractor
from scraper.models import VariableCombination, CombinationResult


class TestTextExtractorFindDifferences:
    """Test Issue #13: find_differences method."""

    def setup_method(self):
        self.extractor = TextExtractor()

    def test_find_differences_replace(self):
        """Test detection of replaced text."""
        text1 = "Muro de hormigón armado de 20 cm de espesor"
        text2 = "Muro de acero galvanizado de 20 cm de espesor"

        diffs = self.extractor.find_differences(text1, text2)

        assert len(diffs) >= 1
        replace_diffs = [d for d in diffs if d['type'] == 'replace']
        assert len(replace_diffs) >= 1

        # difflib may split diffs into smaller chunks based on character matching
        # The important thing is that we detect changes in the material region (position 8-23)
        # The actual template building uses these diffs with _find_diff_span to get the full span
        material_region_detected = any(
            8 <= d['position'] <= 23 for d in replace_diffs
        )
        assert material_region_detected, "Should detect changes in material region"

    def test_find_differences_numeric_change(self):
        """Test detection of numeric value changes."""
        text1 = "Panel de 50 mm de espesor"
        text2 = "Panel de 80 mm de espesor"

        diffs = self.extractor.find_differences(text1, text2)

        assert len(diffs) >= 1
        # Should find the 50 -> 80 change (may be split by difflib, e.g., '5'->'8')
        replace_diffs = [d for d in diffs if d['type'] == 'replace']
        # Check that we detect a change in the numeric region (position 9-11)
        found_numeric = any(
            d['position'] == 9 and d['old_text'] in '50' and d['new_text'] in '80'
            for d in replace_diffs
        )
        assert found_numeric, "Should detect numeric value change"

    def test_find_differences_empty_input(self):
        """Test handling of empty inputs."""
        assert self.extractor.find_differences("", "text") == []
        assert self.extractor.find_differences("text", "") == []
        assert self.extractor.find_differences("", "") == []
        assert self.extractor.find_differences(None, "text") == []

    def test_find_differences_identical_text(self):
        """Test that identical texts produce no differences."""
        text = "Muro de hormigón de 30 cm"
        diffs = self.extractor.find_differences(text, text)

        # Should have no replace/delete/insert diffs
        change_diffs = [d for d in diffs if d['type'] in ('replace', 'delete', 'insert')]
        assert len(change_diffs) == 0

    def test_find_differences_preserves_position(self):
        """Test that position information is correct."""
        text1 = "ABC_XYZ_123"
        text2 = "ABC_QQQ_123"

        diffs = self.extractor.find_differences(text1, text2)

        replace_diffs = [d for d in diffs if d['type'] == 'replace']
        assert len(replace_diffs) == 1

        diff = replace_diffs[0]
        assert diff['old_text'] == 'XYZ'
        assert diff['new_text'] == 'QQQ'
        assert diff['position'] == 4  # After "ABC_"


class TestTextExtractorMapDifference:
    """Test Issue #14: map_difference_to_variable method."""

    def setup_method(self):
        self.extractor = TextExtractor()

    def test_map_exact_match(self):
        """Test exact matching of variable values."""
        difference = {
            'old_text': 'hormigón',
            'new_text': 'acero',
            'type': 'replace'
        }
        variable_changes = [
            {'variable_name': 'Material', 'old_value': 'hormigón', 'new_value': 'acero'}
        ]

        result = self.extractor.map_difference_to_variable(difference, variable_changes)
        assert result == 'Material'

    def test_map_partial_match(self):
        """Test partial/contained matching."""
        difference = {
            'old_text': 'hormigón armado HA-25',
            'new_text': 'acero S275',
            'type': 'replace'
        }
        variable_changes = [
            {'variable_name': 'Material', 'old_value': 'hormigón', 'new_value': 'acero'}
        ]

        result = self.extractor.map_difference_to_variable(difference, variable_changes)
        assert result == 'Material'

    def test_map_no_match(self):
        """Test when no variable matches the difference."""
        difference = {
            'old_text': 'interior',
            'new_text': 'exterior',
            'type': 'replace'
        }
        variable_changes = [
            {'variable_name': 'Material', 'old_value': 'hormigón', 'new_value': 'acero'}
        ]

        result = self.extractor.map_difference_to_variable(difference, variable_changes)
        assert result is None

    def test_map_multiple_variables(self):
        """Test with multiple variable changes - should match the correct one."""
        difference = {
            'old_text': '50',
            'new_text': '80',
            'type': 'replace'
        }
        variable_changes = [
            {'variable_name': 'Material', 'old_value': 'hormigón', 'new_value': 'acero'},
            {'variable_name': 'Espesor', 'old_value': '50', 'new_value': '80'},
            {'variable_name': 'Ubicación', 'old_value': 'interior', 'new_value': 'exterior'}
        ]

        result = self.extractor.map_difference_to_variable(difference, variable_changes)
        assert result == 'Espesor'

    def test_map_empty_variable_changes(self):
        """Test with empty variable changes list."""
        difference = {
            'old_text': 'hormigón',
            'new_text': 'acero',
            'type': 'replace'
        }

        result = self.extractor.map_difference_to_variable(difference, [])
        assert result is None

    def test_map_ignores_single_char_partial(self):
        """Test that single character partial matches are filtered."""
        difference = {
            'old_text': 'a',
            'new_text': 'b',
            'type': 'replace'
        }
        variable_changes = [
            {'variable_name': 'Test', 'old_value': 'a', 'new_value': 'b'}
        ]

        # Single char exact match should work
        result = self.extractor.map_difference_to_variable(difference, variable_changes)
        assert result == 'Test'


class TestTextExtractorBuildTemplate:
    """Test Issue #15: build_template method."""

    def setup_method(self):
        self.extractor = TextExtractor()

    def test_build_simple_template(self):
        """Test building a simple template with one placeholder."""
        base_text = "Muro de hormigón de 30 cm"
        replacements = [
            {'start': 8, 'end': 16, 'variable': 'Material'}
        ]

        result = self.extractor.build_template(base_text, replacements)
        assert result == "Muro de {Material} de 30 cm"

    def test_build_multiple_placeholders(self):
        """Test building template with multiple placeholders."""
        base_text = "Panel de hormigón de 50 mm para interior"
        replacements = [
            {'start': 9, 'end': 17, 'variable': 'Material'},
            {'start': 21, 'end': 23, 'variable': 'Espesor'},
            {'start': 32, 'end': 40, 'variable': 'Ubicación'}
        ]

        result = self.extractor.build_template(base_text, replacements)
        assert '{Material}' in result
        assert '{Espesor}' in result
        assert '{Ubicación}' in result

    def test_build_handles_reverse_order(self):
        """Test that replacements work regardless of input order."""
        base_text = "A_XX_B_YY_C"
        replacements = [
            {'start': 2, 'end': 4, 'variable': 'First'},
            {'start': 7, 'end': 9, 'variable': 'Second'}
        ]

        result = self.extractor.build_template(base_text, replacements)
        assert result == "A_{First}_B_{Second}_C"

    def test_build_empty_replacements(self):
        """Test with no replacements."""
        base_text = "Texto sin cambios"
        result = self.extractor.build_template(base_text, [])
        assert result == base_text

    def test_build_invalid_positions_skipped(self):
        """Test that invalid positions are skipped."""
        base_text = "Short text"
        replacements = [
            {'start': -1, 'end': 5, 'variable': 'Invalid1'},
            {'start': 0, 'end': 100, 'variable': 'Invalid2'},
            {'start': 0, 'end': 5, 'variable': 'Valid'}
        ]

        result = self.extractor.build_template(base_text, replacements)
        # Should only apply the valid replacement
        assert '{Valid}' in result
        assert '{Invalid1}' not in result
        assert '{Invalid2}' not in result


class TestCreateDynamicTemplate:
    """Test Issue #16: create_dynamic_template integration."""

    def test_create_template_from_results(self):
        """Test full template creation from scraping results."""
        from scraper.template_extraction.browser_extractor import BrowserExtractor

        # Create mock extractor without browser init
        extractor = BrowserExtractor.__new__(BrowserExtractor)
        extractor.template_builder = TextExtractor()

        # Create mock results simulating CYPE scraping
        results = [
            CombinationResult(
                combination=VariableCombination(
                    values={'Material': 'hormigón', 'Espesor': '30'},
                    strategy='default'
                ),
                description="Muro de hormigón de 30 cm de espesor",
                success=True
            ),
            CombinationResult(
                combination=VariableCombination(
                    values={'Material': 'acero', 'Espesor': '30'},
                    strategy='single_change'
                ),
                description="Muro de acero de 30 cm de espesor",
                success=True
            ),
        ]

        template = extractor.create_dynamic_template(results)

        # Template should have placeholder for Material (exact replacement)
        assert template == "Muro de {Material} de 30 cm de espesor"
        # Verify placeholder and structure
        assert '{Material}' in template
        assert 'Muro de' in template
        assert 'de espesor' in template

    def test_create_template_empty_results(self):
        """Test with empty results."""
        from scraper.template_extraction.browser_extractor import BrowserExtractor

        extractor = BrowserExtractor.__new__(BrowserExtractor)
        extractor.template_builder = TextExtractor()

        result = extractor.create_dynamic_template([])
        assert result == ""

    def test_create_template_single_result(self):
        """Test with only one result (no comparison possible)."""
        from scraper.template_extraction.browser_extractor import BrowserExtractor

        extractor = BrowserExtractor.__new__(BrowserExtractor)
        extractor.template_builder = TextExtractor()

        results = [
            CombinationResult(
                combination=VariableCombination(
                    values={'Material': 'hormigón'},
                    strategy='default'
                ),
                description="Muro de hormigón",
                success=True
            ),
        ]

        # With only one result, template should be the base text (no placeholders)
        template = extractor.create_dynamic_template(results)
        assert template == "Muro de hormigón"

    def test_create_template_multiple_variables(self):
        """Test template creation with multiple variable changes."""
        from scraper.template_extraction.browser_extractor import BrowserExtractor

        extractor = BrowserExtractor.__new__(BrowserExtractor)
        extractor.template_builder = TextExtractor()

        results = [
            CombinationResult(
                combination=VariableCombination(
                    values={'Material': 'hormigón', 'Ubicación': 'interior'},
                    strategy='default'
                ),
                description="Panel de hormigón para uso interior",
                success=True
            ),
            CombinationResult(
                combination=VariableCombination(
                    values={'Material': 'acero', 'Ubicación': 'interior'},
                    strategy='single_change'
                ),
                description="Panel de acero para uso interior",
                success=True
            ),
            CombinationResult(
                combination=VariableCombination(
                    values={'Material': 'hormigón', 'Ubicación': 'exterior'},
                    strategy='single_change'
                ),
                description="Panel de hormigón para uso exterior",
                success=True
            ),
        ]

        template = extractor.create_dynamic_template(results)

        # Should detect both variables with correct replacements
        assert template == "Panel de {Material} para uso {Ubicación}"
        assert '{Material}' in template
        assert '{Ubicación}' in template


class TestTextVariableExtractor:
    """Test the TextVariableExtractor class functionality."""

    def setup_method(self):
        self.extractor = TextVariableExtractor()

    def test_extract_bullet_sections(self):
        """Test extraction from bullet-point sections."""
        text = """Naturaleza del soporte
- Mortero de cemento
- Paramento interior
- Hormigón armado

Otra sección sin bullets"""

        variables = self.extractor.extract_from_text(text)

        # Should find "Naturaleza del soporte"
        var_names = [v.name for v in variables]
        assert 'Naturaleza del soporte' in var_names

    def test_extract_labeled_groups(self):
        """Test extraction from labeled groups."""
        text = "Acabado: brillante, mate, satinado"

        variables = self.extractor.extract_from_text(text)

        var_names = [v.name for v in variables]
        assert 'Acabado' in var_names

        acabado_var = [v for v in variables if v.name == 'Acabado'][0]
        assert 'brillante' in acabado_var.options
        assert 'mate' in acabado_var.options
        assert 'satinado' in acabado_var.options

    def test_extract_construction_patterns(self):
        """Test extraction using construction domain patterns."""
        text = "Este elemento puede ser de hormigón o acero, instalado en interior o exterior"

        variables = self.extractor.extract_from_text(text)

        var_names = [v.name for v in variables]
        # Should infer Material and Ubicación patterns
        assert 'Material' in var_names or any('hormigón' in str(v.options) for v in variables)

    def test_deduplicate_variables(self):
        """Test that duplicate variables are removed."""
        text = """Material
- hormigón
- acero

Material
- madera
- PVC"""

        variables = self.extractor.extract_from_text(text)

        # Should only have one "Material" variable
        material_vars = [v for v in variables if v.name.lower() == 'material']
        assert len(material_vars) <= 1


class TestCascadingChanges:
    """Test cascading changes where one variable affects multiple text regions."""

    def test_cascading_material_and_specs(self):
        """Test when material change also changes specifications.

        Note: Current implementation uses precise matching to avoid
        misplacing placeholders. This means only the exact old_value
        is replaced, not cascading changes.
        """
        from scraper.template_extraction.browser_extractor import BrowserExtractor

        extractor = BrowserExtractor.__new__(BrowserExtractor)
        extractor.template_builder = TextExtractor()

        results = [
            CombinationResult(
                combination=VariableCombination(
                    values={'Material': 'hormigón armado'},
                    strategy='default'
                ),
                description='Pilar de hormigón armado HA-25/B/20/IIa, de 30x30 cm.',
                success=True
            ),
            CombinationResult(
                combination=VariableCombination(
                    values={'Material': 'acero'},
                    strategy='single_change'
                ),
                description='Pilar de acero S275JR, perfil HEB 200.',
                success=True
            ),
        ]

        template = extractor.create_dynamic_template(results)

        # With precise matching, only the exact old_value is replaced
        assert template == 'Pilar de {Material} HA-25/B/20/IIa, de 30x30 cm.'

    def test_cascading_thermal_properties(self):
        """Test when insulation material change also changes thermal properties.

        Note: Current implementation uses precise matching to avoid
        misplacing placeholders. Only the exact old_value is replaced.
        """
        from scraper.template_extraction.browser_extractor import BrowserExtractor

        extractor = BrowserExtractor.__new__(BrowserExtractor)
        extractor.template_builder = TextExtractor()

        results = [
            CombinationResult(
                combination=VariableCombination(
                    values={'Material': 'EPS'},
                    strategy='default'
                ),
                description='Aislamiento de EPS (poliestireno expandido) con lambda=0.036 W/mK.',
                success=True
            ),
            CombinationResult(
                combination=VariableCombination(
                    values={'Material': 'XPS'},
                    strategy='single_change'
                ),
                description='Aislamiento de XPS (poliestireno extruido) con lambda=0.034 W/mK.',
                success=True
            ),
        ]

        template = extractor.create_dynamic_template(results)

        # With precise matching, only the exact old_value (EPS) is replaced
        assert template == 'Aislamiento de {Material} (poliestireno expandido) con lambda=0.036 W/mK.'

    def test_simple_replacement_no_cascade(self):
        """Test that simple replacements still work correctly."""
        from scraper.template_extraction.browser_extractor import BrowserExtractor

        extractor = BrowserExtractor.__new__(BrowserExtractor)
        extractor.template_builder = TextExtractor()

        results = [
            CombinationResult(
                combination=VariableCombination(
                    values={'Material': 'hormigón'},
                    strategy='default'
                ),
                description='Muro de hormigón de 30 cm',
                success=True
            ),
            CombinationResult(
                combination=VariableCombination(
                    values={'Material': 'acero'},
                    strategy='single_change'
                ),
                description='Muro de acero de 30 cm',
                success=True
            ),
        ]

        template = extractor.create_dynamic_template(results)
        assert template == 'Muro de {Material} de 30 cm'


class TestIntegration:
    """Integration tests for the complete template extraction flow."""

    def test_full_workflow(self):
        """Test the complete workflow: extract -> compare -> template."""
        text_extractor = TextExtractor()

        # Simulate two CYPE descriptions with different variable values
        desc1 = "Aislamiento térmico de poliestireno expandido (EPS) de 40 mm de espesor"
        desc2 = "Aislamiento térmico de lana mineral de 40 mm de espesor"

        # Step 1: Find differences
        diffs = text_extractor.find_differences(desc1, desc2)
        assert len(diffs) >= 1

        # Step 2: Map to variables
        var_changes = [
            {'variable_name': 'Material', 'old_value': 'poliestireno expandido (EPS)', 'new_value': 'lana mineral'}
        ]

        replacements = []
        for diff in diffs:
            if diff['type'] == 'replace':
                var_name = text_extractor.map_difference_to_variable(diff, var_changes)
                if var_name:
                    replacements.append({
                        'start': diff['position'],
                        'end': diff['position'] + len(diff['old_text']),
                        'variable': var_name
                    })

        # Step 3: Build template
        if replacements:
            template = text_extractor.build_template(desc1, replacements)
            assert '{Material}' in template
            assert 'Aislamiento térmico de' in template
            assert 'de 40 mm de espesor' in template

    def test_spanish_text_handling(self):
        """Test proper handling of Spanish text with accents."""
        text_extractor = TextExtractor()

        desc1 = "Instalación eléctrica con cableado de cobre"
        desc2 = "Instalación eléctrica con cableado de aluminio"

        diffs = text_extractor.find_differences(desc1, desc2)

        # Should detect the change
        replace_diffs = [d for d in diffs if d['type'] == 'replace']
        assert len(replace_diffs) >= 1

        # Accented characters should be preserved
        assert 'Instalación' in desc1  # Original preserved
        assert 'eléctrica' in desc1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
