#!/usr/bin/env python3
"""Debug script to verify timing and description changes."""
import asyncio
from playwright.async_api import async_playwright


async def debug_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        url = "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Pilares/EHS010_Pilar_rectangular_o_cuadrado_de_hor.html"
        await page.goto(url, timeout=30000)
        await page.wait_for_load_state("networkidle")

        # Expand "Pliego de condiciones" accordion first
        await page.evaluate("""() => {
            const accordions = document.querySelectorAll('.accordion-item');
            for (const acc of accordions) {
                const btn = acc.querySelector('.accordion-button');
                const text = btn?.innerText?.toLowerCase() || '';
                if (text.includes('pliego') || text.includes('condiciones') || text.includes('característica')) {
                    if (btn.classList.contains('collapsed')) {
                        btn.click();
                    }
                }
            }
        }""")
        await page.wait_for_timeout(500)

        # Get initial description from the right accordion
        desc1 = await page.evaluate("""() => {
            const accordions = document.querySelectorAll('.accordion-item');
            for (const acc of accordions) {
                const btn = acc.querySelector('.accordion-button');
                const text = btn?.innerText?.toLowerCase() || '';
                if (text.includes('pliego') || text.includes('característica')) {
                    const body = acc.querySelector('.accordion-body, .accordion-collapse');
                    return body ? body.innerText.substring(0, 500) : 'BODY NOT FOUND';
                }
            }
            return 'ACCORDION NOT FOUND';
        }""")
        print(f"INITIAL DESC: {desc1[:200]}...")

        # Find current Sección media value
        current = await page.evaluate("""() => {
            const fieldsets = document.querySelectorAll("fieldset");
            for (const fs of fieldsets) {
                const legend = fs.querySelector("legend");
                if (legend && legend.innerText.includes("Sección media")) {
                    const checked = fs.querySelector("input[type=radio]:checked");
                    if (checked) {
                        const label = checked.closest(".form-check")?.querySelector("label")?.innerText;
                        return label || checked.value;
                    }
                }
            }
            return "NOT FOUND";
        }""")
        print(f"CURRENT Sección media VALUE: {current}")

        # Click 50
        print("\n--- Clicking Sección media = 50 ---")
        initial_url = page.url

        await page.evaluate("""() => {
            const fieldsets = document.querySelectorAll("fieldset");
            for (const fs of fieldsets) {
                const legend = fs.querySelector("legend");
                if (legend && legend.innerText.includes("Sección media")) {
                    const radios = fs.querySelectorAll("input[type=radio]");
                    for (const r of radios) {
                        const label = r.closest(".form-check")?.querySelector("label")?.innerText?.trim();
                        if (label === "50") {
                            r.click();
                            return;
                        }
                    }
                }
            }
        }""")

        await page.wait_for_timeout(1500)
        if page.url != initial_url:
            print("URL CHANGED!")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(1000)
        else:
            print("URL did NOT change")

        # Expand accordion again on new page
        await page.evaluate("""() => {
            const accordions = document.querySelectorAll('.accordion-item');
            for (const acc of accordions) {
                const btn = acc.querySelector('.accordion-button');
                const text = btn?.innerText?.toLowerCase() || '';
                if (text.includes('pliego') || text.includes('condiciones') || text.includes('característica')) {
                    if (btn.classList.contains('collapsed')) {
                        btn.click();
                    }
                }
            }
        }""")
        await page.wait_for_timeout(500)

        # Get new description from the right accordion
        desc2 = await page.evaluate("""() => {
            const accordions = document.querySelectorAll('.accordion-item');
            for (const acc of accordions) {
                const btn = acc.querySelector('.accordion-button');
                const text = btn?.innerText?.toLowerCase() || '';
                if (text.includes('pliego') || text.includes('característica')) {
                    const body = acc.querySelector('.accordion-body, .accordion-collapse');
                    return body ? body.innerText.substring(0, 500) : 'BODY NOT FOUND';
                }
            }
            return 'ACCORDION NOT FOUND';
        }""")
        print(f"NEW DESC: {desc2[:200]}...")

        # Check what is now selected
        current2 = await page.evaluate("""() => {
            const fieldsets = document.querySelectorAll("fieldset");
            for (const fs of fieldsets) {
                const legend = fs.querySelector("legend");
                if (legend && legend.innerText.includes("Sección media")) {
                    const checked = fs.querySelector("input[type=radio]:checked");
                    if (checked) {
                        const label = checked.closest(".form-check")?.querySelector("label")?.innerText;
                        return label || checked.value;
                    }
                }
            }
            return "NOT FOUND";
        }""")
        print(f"NEW Sección media VALUE: {current2}")

        # Compare
        print("\n--- COMPARISON ---")
        if desc1 == desc2:
            print("⚠️  WARNING: Descriptions are IDENTICAL!")
        else:
            print("✅ OK: Descriptions are DIFFERENT")
            # Find what changed
            import difflib
            diff = list(difflib.unified_diff(desc1.split(), desc2.split(), lineterm=''))
            changes = [d for d in diff if d.startswith('+') or d.startswith('-')]
            print(f"Changes: {changes[:10]}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_test())
