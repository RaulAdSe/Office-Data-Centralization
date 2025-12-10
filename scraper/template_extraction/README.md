# Template Extraction System

Extract description templates from CYPE construction elements using browser automation.

## Architecture

```
template_extraction/
├── __init__.py              # Public API exports
├── models.py                # Data classes (ExtractedVariable, VariableCombination, etc.)
├── text_extractor.py        # Text-based variable extraction
├── browser_extractor.py     # Playwright browser automation
├── combination_generator.py # Strategic combination generation + CYPEExtractor
├── template_validator.py    # Validation + Spanish construction domain knowledge
├── template_db_integrator.py # Database integration
└── README.md
```

## Quick Start

```python
from scraper.template_extraction import CYPEExtractor

async with CYPEExtractor(headless=True, timeout=60000) as extractor:
    variables, results = await extractor.extract(url)

    for var in variables:
        print(f"{var.name}: {len(var.options)} options")

    for result in results:
        print(f"{result.combination.strategy}: {result.description[:100]}...")
```

## Modules

### models.py
Core data classes:
- `VariableType` - Enum: RADIO, TEXT, CHECKBOX, SELECT, CATEGORICAL
- `ExtractedVariable` - Variable with name, type, options
- `VariableCombination` - Set of variable values to test
- `CombinationResult` - Result of applying a combination

### text_extractor.py
Extract variables from rendered text content:
- Bullet point sections
- Labeled groups (key: value)
- Construction patterns (materials, locations)

### browser_extractor.py
Playwright-based extraction:
- Navigate CYPE pages with JavaScript execution
- Extract from `<fieldset><legend>` structure
- Apply combinations and capture descriptions

### combination_generator.py
Strategic combination generation:
- `CombinationGenerator` - Generate 3-5 strategic tests instead of millions
- `CYPEExtractor` - High-level API combining browser + text extraction

### template_validator.py
Validation with Spanish construction domain expertise:
- `TemplateValidator` - Validate templates against descriptions
- `ExtractedTemplate` - Template with placeholders
- `DescriptionData` - Test data for validation
- Fuzzy matching, synonym handling, accent-insensitive comparison
- 60+ material synonyms, 30+ location synonyms, unit variations

### template_db_integrator.py
Database integration:
- `TemplateDbIntegrator` - Store templates in database
- `TemplateMappingResult` - Integration result
- Variable mapping and placeholder extraction

## Domain Knowledge

Spanish construction terminology is built-in:

```python
from scraper.template_extraction import (
    MATERIAL_SYNONYMS,   # hormigón, acero, madera, EPS, XPS...
    LOCATION_SYNONYMS,   # interior, exterior, fachada, cubierta...
    UNIT_SYNONYMS,       # mm, cm, m², N/mm², MPa...
    ABBREVIATIONS,       # HA, HP, EPS, SATE, ETICS, GL...
    fuzzy_match,
    remove_accents,
)
```

## Dependencies

```bash
pip install playwright
playwright install chromium
```

## Example: Full Extraction Pipeline

```python
import asyncio
from scraper.template_extraction import (
    CYPEExtractor,
    validate_extraction_results,
    TemplateValidator,
)

async def extract_and_validate(url: str):
    async with CYPEExtractor(headless=True, timeout=60000) as extractor:
        variables, results = await extractor.extract(url)

        print(f"Extracted {len(variables)} variables")
        for var in variables:
            print(f"  - {var.name}: {len(var.options)} options")

        # Validate extraction quality
        if len(results) >= 2:
            validation = validate_extraction_results(variables, results)
            print(f"Validation accuracy: {validation.template_accuracy:.2%}")

        return variables, results

# Run
asyncio.run(extract_and_validate("https://generadordeprecios.info/..."))
```
