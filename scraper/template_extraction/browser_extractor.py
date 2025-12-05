"""
Playwright-based variable extraction from CYPE pages.
"""

from typing import List, Tuple
from scraper.models import ElementVariable, VariableType, VariableCombination, CombinationResult
from .text_extractor import TextVariableExtractor


# JavaScript for extracting variables from CYPE fieldsets
JS_EXTRACT_FIELDSETS = '''() => {
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
                const labelEl = formCheck.querySelector('label, .form-check-label');
                if (labelEl) label = labelEl.innerText?.trim();
            }
            if (!label && radio.id) {
                const labelFor = document.querySelector(`label[for="${radio.id}"]`);
                if (labelFor) label = labelFor.innerText?.trim();
            }
            if (!label && radio.labels?.length > 0) {
                label = radio.labels[0].innerText?.trim();
            }
            if (label && label.length > 1 && label.length < 200) {
                options.push(label);
            }
        });

        if (options.length >= 2) {
            results.push({ name: varName, options: options, type: 'RADIO' });
        }
    });
    return results;
}'''

# JavaScript for extracting select elements
JS_EXTRACT_SELECTS = '''() => {
    const result = [];
    document.querySelectorAll('select').forEach(select => {
        let label = select.labels?.[0]?.innerText?.trim();
        if (!label) {
            const legend = select.closest('fieldset')?.querySelector('legend');
            label = legend?.innerText?.trim() || select.name || select.id;
        }
        const options = Array.from(select.options)
            .map(o => o.text?.trim() || o.value)
            .filter(o => o && o.length > 0);
        if (label && options.length >= 2) {
            result.push({ name: label, options: options, type: 'SELECT' });
        }
    });
    return result;
}'''

# JavaScript for extracting description
JS_EXTRACT_DESCRIPTION = '''() => {
    // Try accordion with "Descripción"
    const accordions = document.querySelectorAll('.accordion-item, [class*="accordion"]');
    for (const acc of accordions) {
        const header = acc.querySelector('.accordion-button, button');
        if (header?.innerText?.toLowerCase().includes('descripci')) {
            const body = acc.querySelector('.accordion-body, [class*="collapse"]');
            if (body) return body.innerText?.trim();
        }
    }

    // Try paragraphs with construction patterns
    const patterns = [/aislamiento/i, /sistema/i, /mortero/i, /panel/i, /fachada/i];
    let descText = '';
    for (const p of document.querySelectorAll('p')) {
        const text = p.innerText?.trim();
        if (text?.length > 50 && patterns.some(pat => pat.test(text))) {
            descText += text + '\\n';
        }
    }
    if (descText.length > 100) return descText.trim();

    return '';
}'''


class BrowserExtractor:
    """
    Playwright-based extractor for CYPE pages.

    Extracts variables from:
    1. Fieldset/legend structure (primary)
    2. Select elements
    3. Rendered text content (supplementary)
    """

    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.text_extractor = TextVariableExtractor()
        self._playwright = None
        self.browser = None
        self.context = None

    async def __aenter__(self):
        await self._init_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close_browser()

    async def _init_browser(self):
        """Initialize Playwright browser."""
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
        """Close browser and cleanup."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def extract_variables(self, url: str) -> List[ElementVariable]:
        """Extract all variables from a CYPE URL."""
        page = await self.context.new_page()

        try:
            await page.goto(url, timeout=self.timeout)
            await page.wait_for_load_state('networkidle')

            # Extract from form elements
            variables = await self._extract_form_variables(page)

            # Supplement with text extraction
            rendered_text = await page.inner_text('body')
            text_vars = self.text_extractor.extract_from_text(rendered_text)

            # Merge, avoiding duplicates
            form_names = {v.name.lower() for v in variables}
            for var in text_vars:
                if var.name.lower() not in form_names:
                    variables.append(var)

            return variables
        finally:
            await page.close()

    async def _extract_form_variables(self, page) -> List[ElementVariable]:
        """Extract variables from form elements."""
        variables = []

        # Extract from fieldsets
        fieldset_data = await page.evaluate(JS_EXTRACT_FIELDSETS)
        for data in fieldset_data:
            variables.append(ElementVariable(
                name=data['name'],
                variable_type=VariableType.RADIO,
                options=data['options'],
                source="form"
            ))

        # Extract from selects
        select_data = await page.evaluate(JS_EXTRACT_SELECTS)
        for data in select_data:
            if not any(v.name == data['name'] for v in variables):
                variables.append(ElementVariable(
                    name=data['name'],
                    variable_type=VariableType.SELECT,
                    options=data['options'],
                    source="form"
                ))

        return variables

    async def extract_description(self, page) -> str:
        """Extract description from page."""
        description = await page.evaluate(JS_EXTRACT_DESCRIPTION)
        return description if description and len(description) > 50 else ""

    async def apply_combination(
        self,
        page,
        combination: VariableCombination
    ) -> CombinationResult:
        """Apply a combination and capture the resulting description."""
        try:
            for var_name, value in combination.values.items():
                await self._set_value(page, var_name, value)

            await page.wait_for_timeout(500)
            description = await self.extract_description(page)

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

    async def _set_value(self, page, var_name: str, value: str):
        """Set a variable's value in the form."""
        # Try radio buttons
        radios = await page.query_selector_all(f'input[type="radio"][name="{var_name}"]')
        for radio in radios:
            label = await radio.evaluate('''el =>
                el.labels?.[0]?.innerText || el.nextSibling?.textContent?.trim() || el.value
            ''')
            if label and (value.lower() in label.lower() or label.lower() in value.lower()):
                await radio.click()
                return

        # Try select
        select = await page.query_selector(f'select[name="{var_name}"], select[id="{var_name}"]')
        if select:
            await select.select_option(label=value)
            return

        # Try text input
        input_el = await page.query_selector(f'input[name="{var_name}"], input[id="{var_name}"]')
        if input_el:
            await input_el.fill(value)
