#!/usr/bin/env python3
"""
Combination generator for CYPE template extraction.

This module provides strategic combination generation for template pattern detection,
using only 3-5 combinations instead of exhaustive testing.

Usage:
    # With pre-extracted variables
    generator = CombinationGenerator(max_combinations=5)
    combinations = generator.generate(variables)

    # With Playwright browser automation
    async with CYPEExtractor() as extractor:
        variables, results = await extractor.extract(url)
"""

from typing import Dict, List, Any, Tuple

from scraper.models import (
    ElementVariable,
    VariableCombination,
    CombinationResult,
    VariableType,
)
from .text_extractor import TextVariableExtractor
from .browser_extractor import BrowserExtractor


# Dimension value mappings for TEXT variables
DIMENSION_VALUES = {
    ('espesor', 'grosor'): ['20', '30', '40', '50'],
    ('diametro', 'diámetro'): ['12', '16', '20', '25'],
    ('longitud', 'largo'): ['100', '200', '300'],
    ('ancho', 'anchura'): ['50', '100', '150'],
    ('alto', 'altura'): ['200', '250', '300'],
    ('resistencia',): ['25', '30', '35', '40'],
    ('temperatura',): ['20', '25', '30'],
    ('pendiente',): ['1', '2', '3', '5'],
}


class CombinationGenerator:
    """
    Generates strategic variable combinations for template pattern detection.

    Strategy:
    1. Default combination (all first options) - baseline
    2. Single-variable changes - isolate each variable's effect
    3. Pair changes - detect variable interactions

    This reduces millions of combinations to just 3-5 tests.
    """

    def __init__(self, max_combinations: int = 5):
        self.max_combinations = max_combinations

    def generate(self, variables: List[Any]) -> List[VariableCombination]:
        """Generate strategic combinations from variables."""
        var_options = self._prepare_options(variables)
        if not var_options:
            return []

        total = 1
        for opts in var_options.values():
            total *= len(opts)

        print(f"Variables: {len(var_options)}, Total combinations: {total}")

        combinations = self._generate_strategic(var_options)
        print(f"Generated {len(combinations)} strategic combinations")

        return combinations

    def _prepare_options(self, variables: List[Any]) -> Dict[str, List[str]]:
        """Prepare variable options from various input formats."""
        var_options = {}

        for var in variables:
            name = getattr(var, 'name', None) or var.get('name', '')
            var_type = getattr(var, 'variable_type', None) or var.get('variable_type', '')
            options = getattr(var, 'options', None) or var.get('options', [])
            default = getattr(var, 'default_value', None) or var.get('default_value')

            # Normalize type
            if hasattr(var_type, 'value'):
                var_type = var_type.value
            var_type = str(var_type).upper()

            if var_type in ('RADIO', 'SELECT', 'CATEGORICAL') and options:
                var_options[name] = list(options)
            elif var_type == 'TEXT':
                var_options[name] = [default] if default else self._get_text_values(name)
            elif var_type == 'CHECKBOX':
                var_options[name] = ['true', 'false']
            elif options:
                var_options[name] = list(options)
            elif default:
                var_options[name] = [default]

        return var_options

    def _generate_strategic(self, var_options: Dict[str, List[str]]) -> List[VariableCombination]:
        """Generate minimal strategic combinations."""
        combinations = []
        var_names = list(var_options.keys())

        # Strategy 1: Default (all first options)
        default = {name: opts[0] for name, opts in var_options.items()}
        combinations.append(VariableCombination(values=default.copy(), strategy="default"))

        # Strategy 2: Single changes
        for var_name, options in var_options.items():
            if len(options) > 1 and len(combinations) < self.max_combinations:
                combo = default.copy()
                combo[var_name] = options[1]
                combinations.append(VariableCombination(values=combo, strategy="single_change"))

        # Strategy 3: Pair changes
        if len(combinations) < self.max_combinations and len(var_names) >= 2:
            for i in range(len(var_names)):
                for j in range(i + 1, len(var_names)):
                    if len(combinations) >= self.max_combinations:
                        break
                    var1, var2 = var_names[i], var_names[j]
                    if len(var_options[var1]) > 1 and len(var_options[var2]) > 1:
                        combo = default.copy()
                        combo[var1] = var_options[var1][1]
                        combo[var2] = var_options[var2][1]
                        combinations.append(VariableCombination(values=combo, strategy="pair_change"))

        # Deduplicate
        seen = set()
        unique = []
        for combo in combinations:
            if combo.combination_id not in seen:
                seen.add(combo.combination_id)
                unique.append(combo)

        return unique[:self.max_combinations]

    def _get_text_values(self, var_name: str) -> List[str]:
        """Get common test values for text variables."""
        name_lower = var_name.lower()
        for keywords, values in DIMENSION_VALUES.items():
            if any(kw in name_lower for kw in keywords):
                return values
        return ['10', '20', '30']


class CYPEExtractor:
    """
    High-level CYPE extraction interface combining browser and text extraction.

    Usage:
        async with CYPEExtractor() as extractor:
            variables, results = await extractor.extract(url)
    """

    def __init__(self, headless: bool = True, timeout: int = 30000, max_combinations: int = 5):
        self.browser_extractor = BrowserExtractor(headless=headless, timeout=timeout)
        self.combination_generator = CombinationGenerator(max_combinations=max_combinations)

    async def __aenter__(self):
        await self.browser_extractor.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.browser_extractor.__aexit__(exc_type, exc_val, exc_tb)

    async def extract(self, url: str) -> Tuple[List[ElementVariable], List[CombinationResult]]:
        """
        Extract variables and generate combination results from a CYPE URL.

        Returns:
            Tuple of (extracted variables, combination results with descriptions)
        """
        page = await self.browser_extractor.context.new_page()

        try:
            await page.goto(url, timeout=self.browser_extractor.timeout)
            await page.wait_for_load_state('networkidle')

            # Extract variables
            variables = await self.browser_extractor._extract_form_variables(page)

            # Supplement with text extraction
            text = await page.inner_text('body')
            text_vars = self.browser_extractor.text_extractor.extract_from_text(text)
            form_names = {v.name.lower() for v in variables}
            for var in text_vars:
                if var.name.lower() not in form_names:
                    variables.append(var)

            if variables:
                print(f"Extracted {len(variables)} variables from form elements")

            if not variables:
                print("Warning: No variables extracted")
                return [], []

            # Generate combinations
            combinations = self.combination_generator.generate(variables)

            # Apply combinations and capture descriptions
            results = []
            for combo in combinations:
                result = await self.browser_extractor.apply_combination(page, combo)
                results.append(result)

            return variables, results

        finally:
            await page.close()


# Backwards compatibility aliases
BrowserCombinationGenerator = CYPEExtractor


def test():
    """Quick test of the combination generator."""
    import asyncio

    async def run_test():
        print("=" * 60)
        print("Testing CombinationGenerator")
        print("=" * 60)

        # Test with mock variables
        variables = [
            {"name": "Sistema", "variable_type": "RADIO", "options": ["EPS", "Mineral", "Flexible"]},
            {"name": "Espesor", "variable_type": "RADIO", "options": ["40", "60", "80"]},
            {"name": "Color", "variable_type": "RADIO", "options": ["Blanco", "Gris"]},
        ]

        generator = CombinationGenerator(max_combinations=5)
        combinations = generator.generate(variables)

        for i, combo in enumerate(combinations, 1):
            print(f"\n{i}. {combo.strategy}: {combo.values}")

        print("\n" + "=" * 60)
        print("Testing Browser Extractor")
        print("=" * 60)

        try:
            async with CYPEExtractor(headless=True) as extractor:
                print("Browser initialized successfully")
        except ImportError as e:
            print(f"Playwright not available: {e}")

    asyncio.run(run_test())


if __name__ == "__main__":
    test()
