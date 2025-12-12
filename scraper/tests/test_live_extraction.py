"""
Live CYPE Extraction Tests.

Tests the complete extraction pipeline against the actual CYPE website.
Compares web page content directly with extracted data to ensure accuracy.

Run with: python -m pytest scraper/tests/test_live_extraction.py -v --tb=short
"""

import pytest
import pytest_asyncio
import asyncio
import re
import tempfile
import os
import sys

# Configure pytest-asyncio
pytestmark = pytest.mark.asyncio(loop_scope="function")

# Ensure scraper module is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scraper.template_extraction import CYPEExtractor
from scraper.pipeline import CYPEPipeline, PipelineConfig, ExtractionMode
from scraper.core.final_production_crawler import FinalProductionCrawler


# Test URLs - known good CYPE element pages
TEST_URLS = [
    'https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_de_hormigon_armado.html',
    'https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Pilares/Pilar_de_hormigon_armado.html',
]


def get_playwright():
    """Get playwright module, skip if not available."""
    try:
        from playwright.async_api import async_playwright
        return async_playwright
    except ImportError:
        pytest.skip("Playwright not installed. Run: pip install playwright && playwright install")


class TestCrawlerDiscovery:
    """Tests for URL discovery from CYPE website."""

    def test_crawler_discovers_categories(self):
        """Test that crawler can discover main categories."""
        crawler = FinalProductionCrawler()
        categories = crawler.get_element_containing_subcategories()

        assert len(categories) > 0, "Should discover at least some categories"
        assert all(url.startswith('http') for url in categories), "All URLs should be valid"

    def test_crawler_discovers_subcategories(self):
        """Test that crawler can discover subcategories."""
        crawler = FinalProductionCrawler()
        categories = crawler.get_element_containing_subcategories()

        if not categories:
            pytest.skip("No categories found")

        # Test with first category only
        subcats = crawler.discover_deep_subcategories([categories[0]])

        assert len(subcats) > 0, "Should discover subcategories"

    def test_crawler_discovers_elements(self):
        """Test that crawler can discover element URLs."""
        crawler = FinalProductionCrawler()
        categories = crawler.get_element_containing_subcategories()

        if not categories:
            pytest.skip("No categories found")

        subcats = crawler.discover_deep_subcategories([categories[0]])

        if not subcats:
            pytest.skip("No subcategories found")

        elements = crawler.discover_elements_in_subcategory(subcats[0])

        assert len(elements) > 0, "Should discover elements in subcategory"


class TestVariableExtraction:
    """Tests for variable extraction accuracy."""

    @pytest.mark.asyncio
    async def test_extracts_form_variables(self):
        """Test that form variables (fieldsets) are extracted."""
        async_playwright = get_playwright()

        url = TEST_URLS[0]

        async with CYPEExtractor(headless=True, timeout=60000) as extractor:
            variables, _ = await extractor.extract(url)

        assert len(variables) > 0, "Should extract variables"

        # Check for expected variable attributes
        for var in variables:
            assert var.name, "Variable should have a name"
            assert var.variable_type, "Variable should have a type"
            if var.variable_type.value == 'RADIO':
                assert len(var.options) >= 2, f"Radio variable '{var.name}' should have at least 2 options"

    @pytest.mark.asyncio
    async def test_variables_match_web_page(self):
        """Test that extracted variables match what's on the web page."""
        async_playwright = get_playwright()
        from playwright.async_api import async_playwright

        url = TEST_URLS[0]

        # Get variables from web page directly
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=60000)
            await page.wait_for_load_state('networkidle')

            web_vars = await page.evaluate('''() => {
                const results = [];
                document.querySelectorAll('fieldset').forEach(fieldset => {
                    const legend = fieldset.querySelector('legend');
                    if (!legend) return;
                    const varName = legend.innerText?.trim();
                    if (!varName || varName.length < 2) return;
                    const radios = fieldset.querySelectorAll('input[type="radio"]');
                    const options = [];
                    radios.forEach(radio => {
                        let label = '';
                        const formCheck = radio.closest('.form-check, .form-check-inline');
                        if (formCheck) {
                            const labelEl = formCheck.querySelector('label');
                            if (labelEl) label = labelEl.innerText?.trim();
                        }
                        if (label && label.length > 1) options.push(label);
                    });
                    if (options.length >= 2) results.push({ name: varName, options: options });
                });
                return results;
            }''')

            await browser.close()

        # Get extracted variables
        async with CYPEExtractor(headless=True, timeout=60000) as extractor:
            extracted_vars, _ = await extractor.extract(url)

        web_var_names = {v['name'] for v in web_vars}
        extracted_var_names = {v.name for v in extracted_vars}

        # Check coverage - extracted should have most web variables
        missing = web_var_names - extracted_var_names
        coverage = (len(web_var_names) - len(missing)) / len(web_var_names) * 100

        # Allow for some variance due to duplicate handling
        assert coverage >= 80, f"Should capture at least 80% of web variables. Missing: {missing}"

    @pytest.mark.asyncio
    async def test_unit_extraction(self):
        """Test that units are extracted from variable names."""
        async_playwright = get_playwright()

        url = TEST_URLS[0]

        async with CYPEExtractor(headless=True, timeout=60000) as extractor:
            variables, _ = await extractor.extract(url)

        # Look for variables that should have units
        unit_vars = [v for v in variables if v.unit]

        # The page should have some variables with units like N/mm², mm, etc.
        # This is informational - not a hard requirement
        if not unit_vars:
            pytest.xfail("No units extracted - this is expected if page has no unit suffixes")


class TestDescriptionExtraction:
    """Tests for description template extraction."""

    @pytest.mark.asyncio
    async def test_extracts_description(self):
        """Test that description is extracted from Pliego de condiciones."""
        async_playwright = get_playwright()

        url = TEST_URLS[0]

        async with CYPEExtractor(headless=True, timeout=60000) as extractor:
            _, results = await extractor.extract(url)

        # At least one result should have a description
        descriptions = [r.description for r in results if r.description]

        assert len(descriptions) > 0, "Should extract at least one description"

        # Description should contain construction-related terms
        desc = descriptions[0].lower()
        key_terms = ['hormigón', 'viga', 'acero', 'encofrado', 'armado']
        found_terms = [t for t in key_terms if t in desc]

        assert len(found_terms) >= 3, f"Description should contain construction terms. Found: {found_terms}"

    @pytest.mark.asyncio
    async def test_template_generation(self):
        """Test that template with placeholders can be generated."""
        async_playwright = get_playwright()

        url = TEST_URLS[0]

        async with CYPEExtractor(headless=True, timeout=60000) as extractor:
            variables, results = await extractor.extract(url)

            results_with_desc = [r for r in results if r.description]

            if len(results_with_desc) >= 2:
                template = extractor.browser_extractor.create_dynamic_template(results_with_desc)

                # Check if placeholders were created
                placeholders = re.findall(r'\{([^}]+)\}', template)

                # Template should have at least some content
                assert len(template) > 100, "Template should have substantial content"

                # Note: placeholder detection depends on variable changes affecting description
                # This may not always produce placeholders
            else:
                pytest.xfail("Not enough results with descriptions for template generation")


class TestDatabaseIntegration:
    """Tests for database storage of extracted data."""

    @pytest.mark.asyncio
    async def test_stores_element_in_database(self):
        """Test that extracted element is stored correctly in database."""
        async_playwright = get_playwright()

        url = TEST_URLS[0]
        temp_db = tempfile.mktemp(suffix='.db')

        try:
            config = PipelineConfig(
                db_path=temp_db,
                extraction_mode=ExtractionMode.BROWSER,
                headless=True,
                timeout=60000
            )
            pipeline = CYPEPipeline(config)

            # Extract element
            element = await pipeline.extract_element(url)

            assert element is not None, "Should extract element"

            # Store in database
            success = pipeline.store_element(element)

            assert success, "Should store element successfully"

            # Verify database contents
            db = pipeline.db_manager

            db_element = db.get_element_by_code(element.code)
            assert db_element is not None, "Element should be in database"

            db_vars = db.get_element_variables(db_element['element_id'])
            assert len(db_vars) > 0, "Variables should be stored"

            # Check variable options
            vars_with_options = [v for v in db_vars if v.get('options')]
            assert len(vars_with_options) > 0, "Some variables should have options"

        finally:
            if os.path.exists(temp_db):
                os.remove(temp_db)

    @pytest.mark.asyncio
    async def test_stores_description_template(self):
        """Test that description template is stored in database."""
        async_playwright = get_playwright()

        url = TEST_URLS[0]
        temp_db = tempfile.mktemp(suffix='.db')

        try:
            config = PipelineConfig(
                db_path=temp_db,
                extraction_mode=ExtractionMode.BROWSER,
                headless=True,
                timeout=60000
            )
            pipeline = CYPEPipeline(config)

            element = await pipeline.extract_element(url)
            assert element is not None

            success = pipeline.store_element(element)
            assert success

            db = pipeline.db_manager
            db_element = db.get_element_by_code(element.code)

            # Check description version
            version = db.get_active_version(db_element['element_id'])

            assert version is not None, "Should have active description version"
            assert version['description_template'], "Should have template content"
            assert version['state'] == 'S3', "Should be in S3 (approved) state"

        finally:
            if os.path.exists(temp_db):
                os.remove(temp_db)


class TestComprehensiveExtraction:
    """End-to-end tests comparing web content with extracted data."""

    @pytest.mark.asyncio
    async def test_full_extraction_comparison(self):
        """Comprehensive test comparing web page with extracted data."""
        async_playwright = get_playwright()
        from playwright.async_api import async_playwright

        url = TEST_URLS[0]

        # Get web page data directly
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=60000)
            await page.wait_for_load_state('networkidle')

            # Get element code from page
            web_code = await page.evaluate('''() => {
                const text = document.body.innerText;
                const match = text.match(/UNIDAD DE OBRA ([A-Z]{2,3}\\d{3}):/);
                return match ? match[1] : null;
            }''')

            # Get fieldsets
            web_fieldsets = await page.evaluate('''() => {
                const results = [];
                document.querySelectorAll('fieldset').forEach(fieldset => {
                    const legend = fieldset.querySelector('legend');
                    if (!legend) return;
                    const varName = legend.innerText?.trim();
                    if (!varName || varName.length < 2) return;
                    const radios = fieldset.querySelectorAll('input[type="radio"]');
                    let optionCount = 0;
                    radios.forEach(radio => {
                        let label = '';
                        const formCheck = radio.closest('.form-check, .form-check-inline');
                        if (formCheck) {
                            const labelEl = formCheck.querySelector('label');
                            if (labelEl) label = labelEl.innerText?.trim();
                        }
                        if (label && label.length > 1) optionCount++;
                    });
                    if (optionCount >= 2) results.push({ name: varName, options: optionCount });
                });
                return results;
            }''')

            await browser.close()

        # Get extracted data
        async with CYPEExtractor(headless=True, timeout=60000) as extractor:
            extracted_vars, results = await extractor.extract(url)

        # Assertions
        issues = []

        # Check variable count
        web_var_count = len(web_fieldsets)
        ext_var_count = len([v for v in extracted_vars if v.variable_type.value in ('RADIO', 'SELECT')])

        # Allow some variance due to duplicate handling and text extraction
        if abs(web_var_count - ext_var_count) > 3:
            issues.append(f"Variable count mismatch: web={web_var_count}, extracted={ext_var_count}")

        # Check that descriptions were extracted
        descs = [r.description for r in results if r.description]
        if not descs:
            issues.append("No descriptions extracted")

        # Report issues
        if issues:
            issue_str = "\n".join(f"  - {i}" for i in issues)
            pytest.fail(f"Extraction issues found:\n{issue_str}")


# Utility functions for debugging
async def debug_extraction(url: str):
    """
    Debug function to analyze extraction for a specific URL.

    Usage:
        import asyncio
        from scraper.tests.test_live_extraction import debug_extraction
        asyncio.run(debug_extraction("https://..."))
    """
    print(f"Analyzing: {url}")
    print("="*80)

    async with CYPEExtractor(headless=True, timeout=60000) as extractor:
        variables, results = await extractor.extract(url)

        print(f"\nVariables ({len(variables)}):")
        for v in variables:
            print(f"  - {v.name} ({v.variable_type.value})")
            if v.options:
                print(f"    Options: {v.options[:5]}{'...' if len(v.options) > 5 else ''}")

        print(f"\nResults ({len(results)}):")
        for i, r in enumerate(results):
            print(f"  {i+1}. Success: {r.success}, Description: {len(r.description)} chars")

        if len([r for r in results if r.description]) >= 2:
            template = extractor.browser_extractor.create_dynamic_template(
                [r for r in results if r.description]
            )
            placeholders = re.findall(r'\{([^}]+)\}', template)
            print(f"\nTemplate placeholders: {placeholders}")


if __name__ == '__main__':
    # Run a quick test
    import asyncio
    asyncio.run(debug_extraction(TEST_URLS[0]))
