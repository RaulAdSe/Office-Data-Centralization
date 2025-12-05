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
    // Try accordion with "Pliego de condiciones" (contains full description)
    const accordions = document.querySelectorAll('.accordion-item, [class*="accordion"]');
    for (const acc of accordions) {
        const header = acc.querySelector('.accordion-button, button');
        const headerText = header?.innerText?.toLowerCase() || '';

        // Check "Pliego de condiciones" first (most complete description)
        if (headerText.includes('pliego') || headerText.includes('condiciones')) {
            const body = acc.querySelector('.accordion-body, [class*="collapse"]');
            if (body) {
                // Extract the description paragraph (usually starts with element name)
                const text = body.innerText?.trim();
                // Find the main description (after "UNIDAD DE OBRA" header)
                const match = text.match(/UNIDAD DE OBRA[^:]+:([^]+?)(?:NORMATIVA|CRITERIO|$)/i);
                if (match) {
                    return match[1].trim();
                }
                return text.substring(0, 2000);  // Limit length
            }
        }
    }

    // Fallback: try "Descripción" accordion
    for (const acc of accordions) {
        const header = acc.querySelector('.accordion-button, button');
        if (header?.innerText?.toLowerCase().includes('descripci')) {
            const body = acc.querySelector('.accordion-body, [class*="collapse"]');
            if (body) return body.innerText?.trim();
        }
    }

    // Try paragraphs with construction patterns
    const patterns = [/aislamiento/i, /sistema/i, /mortero/i, /panel/i, /fachada/i, /pilar/i, /hormig/i];
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

    async def _dismiss_cookie_consent(self, page):
        """Dismiss cookie consent popups that block interaction."""
        try:
            # Common cookie consent selectors
            selectors = [
                '.termsfeed-com---nb-interstitial-overlay',
                '.cookie-consent',
                '#cookie-consent',
                '[class*="cookie"]',
                '[class*="consent"]',
            ]

            # Try to click accept/dismiss buttons
            button_selectors = [
                'button:has-text("Aceptar")',
                'button:has-text("Accept")',
                'button:has-text("Acepto")',
                '.termsfeed-com---palette-dark button',
                '[class*="accept"]',
            ]

            for selector in button_selectors:
                try:
                    btn = await page.query_selector(selector)
                    if btn and await btn.is_visible():
                        await btn.click()
                        await page.wait_for_timeout(500)
                        return
                except Exception:
                    continue

            # If no button found, try to hide overlays via JavaScript
            await page.evaluate('''() => {
                const overlays = document.querySelectorAll(
                    '.termsfeed-com---nb-interstitial-overlay, ' +
                    '[class*="cookie"], [class*="consent"], [class*="overlay"]'
                );
                overlays.forEach(el => { el.style.display = 'none'; });
            }''')
        except Exception:
            pass  # Continue even if dismissal fails

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

            # Dismiss cookie consent popup
            await self._dismiss_cookie_consent(page)

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
        # First, try to expand the "Pliego de condiciones" accordion
        try:
            await page.evaluate('''() => {
                const accordions = document.querySelectorAll('.accordion-item');
                for (const acc of accordions) {
                    const header = acc.querySelector('.accordion-button');
                    const headerText = header?.innerText?.toLowerCase() || '';
                    if (headerText.includes('pliego') || headerText.includes('condiciones')) {
                        // Click to expand if collapsed
                        if (header.classList.contains('collapsed')) {
                            header.click();
                        }
                    }
                }
            }''')
            await page.wait_for_timeout(500)  # Wait for accordion animation
        except Exception:
            pass

        description = await page.evaluate(JS_EXTRACT_DESCRIPTION)
        return description if description and len(description) > 50 else ""

    async def apply_combination(
        self,
        page,
        combination: VariableCombination
    ) -> CombinationResult:
        """Apply a combination and capture the resulting description.

        Note: CYPE pages navigate to a new URL when radio buttons are clicked.
        We only change ONE field to avoid cascading navigation issues.
        """
        try:
            # For single_change strategy, identify the ONE field that differs
            # Apply only that change to avoid navigation issues
            changed_count = 0

            for var_name, value in combination.values.items():
                initial_url = page.url
                await self._set_value(page, var_name, value)

                # Wait briefly for potential navigation
                await page.wait_for_timeout(500)

                # Check if navigation occurred
                if page.url != initial_url:
                    changed_count += 1
                    # URL changed - wait for page to fully load
                    await page.wait_for_load_state('networkidle', timeout=8000)
                    # Dismiss cookies on new page
                    await self._dismiss_cookie_consent(page)
                    # Additional wait for DOM to stabilize
                    await page.wait_for_timeout(500)

                    # For single_change strategy, stop after first actual change
                    # to avoid interfering with the new page's state
                    if combination.strategy == 'single_change':
                        break

                # Limit total changes to avoid long processing
                if changed_count >= 2:
                    break

            # Extract description from final page state
            await page.wait_for_timeout(300)
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
        # CYPE uses fieldset/legend structure - find radio by legend text
        # First, try to find the fieldset with matching legend (exact match preferred)
        clicked = await page.evaluate('''(args) => {
            const [varName, targetValue] = args;
            const fieldsets = document.querySelectorAll('fieldset');

            // First pass: exact legend match
            for (const fs of fieldsets) {
                const legend = fs.querySelector('legend');
                const legendText = legend?.innerText?.trim() || '';

                // Exact match (case-insensitive)
                if (legendText.toLowerCase() === varName.toLowerCase()) {
                    const radios = fs.querySelectorAll('input[type="radio"]');
                    for (const radio of radios) {
                        let label = '';
                        const formCheck = radio.closest('.form-check');
                        if (formCheck) {
                            label = formCheck.querySelector('label')?.innerText?.trim() || '';
                        }
                        if (!label && radio.labels?.length > 0) {
                            label = radio.labels[0]?.innerText?.trim() || '';
                        }

                        // Skip if already checked
                        if (radio.checked && label === targetValue) {
                            return { success: false, alreadySet: true };
                        }

                        if (label === targetValue) {
                            radio.click();
                            return { success: true, clicked: label, fieldset: legendText };
                        }
                    }
                }
            }

            // Second pass: partial match (for similar names)
            for (const fs of fieldsets) {
                const legend = fs.querySelector('legend');
                const legendText = legend?.innerText?.trim() || '';

                // Partial match but require significant overlap
                if (legendText.toLowerCase().includes(varName.toLowerCase()) ||
                    (varName.length > 15 && varName.toLowerCase().includes(legendText.toLowerCase()))) {

                    const radios = fs.querySelectorAll('input[type="radio"]');
                    for (const radio of radios) {
                        let label = '';
                        const formCheck = radio.closest('.form-check');
                        if (formCheck) {
                            label = formCheck.querySelector('label')?.innerText?.trim() || '';
                        }
                        if (!label && radio.labels?.length > 0) {
                            label = radio.labels[0]?.innerText?.trim() || '';
                        }

                        if (radio.checked && label === targetValue) {
                            return { success: false, alreadySet: true };
                        }

                        if (label === targetValue) {
                            radio.click();
                            return { success: true, clicked: label, fieldset: legendText };
                        }
                    }
                }
            }
            return { success: false };
        }''', [var_name, value])

        if clicked.get('success'):
            return

        # Fallback: Try select elements
        select = await page.query_selector(f'select[name="{var_name}"], select[id="{var_name}"]')
        if select:
            try:
                await select.select_option(label=value)
                return
            except Exception:
                pass

        # Fallback: Try text input
        input_el = await page.query_selector(f'input[name="{var_name}"], input[id="{var_name}"]')
        if input_el:
            await input_el.fill(value)
