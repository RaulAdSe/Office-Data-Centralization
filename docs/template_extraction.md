# Template Extraction

## Overview

Template extraction creates **description templates** from CYPE element pages by replacing variable values with `{VariableName}` placeholders.

**Example**:
```
Input:  "Viga con hormigón HA-25/F/20/X0, vertido con cubilote"
Output: "Viga con hormigón HA-{Resistencia}/F/20/{Riesgo}, vertido con {Tipo de vertido}"
```

## How It Works

### Simple Search-Replace Approach

The template extraction uses a straightforward algorithm:

1. **Get description** with current variable values from the page
2. **For each variable**, search for its value in the text
3. **Replace** found values with `{VariableName}` placeholders

```python
# Core logic (scraper/template_extraction/simple_template.py)

def create_template(description: str, variables: Dict[str, str]) -> TemplateResult:
    template = description

    # Sort by value length (longer first to avoid partial replacements)
    for var_name, var_value in sorted(variables.items(), key=lambda x: len(x[1]), reverse=True):
        if var_value in template:
            template = template.replace(var_value, f"{{{var_name}}}")

    return TemplateResult(template=template, placeholders=[...], not_found=[...])
```

### Edge Cases Handled

| Case | Example | Solution |
|------|---------|----------|
| Partial match | "Con cubilote" → finds "cubilote" | Try last word of value |
| Case insensitive | "CUBILOTE" in text | Fallback to case-insensitive search |
| Short values | "1", "a" | Skip values < 2 chars (too many false positives) |
| Longer first | "HA-25" before "25" | Sort by length descending |

## Usage

### In the Pipeline

The pipeline automatically creates templates when extracting elements:

```python
from scraper.pipeline import CYPEPipeline, PipelineConfig, ExtractionMode

config = PipelineConfig(
    db_path="elements.db",
    extraction_mode=ExtractionMode.BROWSER,
    headless=True
)
pipeline = CYPEPipeline(config)

element = await pipeline.extract_element(url)
print(element.description)  # Template with {placeholders}
```

### Standalone Usage

```python
from scraper.template_extraction.simple_template import create_template

description = "Viga con hormigón HA-25/F/20/X0, vertido con cubilote"
variables = {
    "Resistencia": "25",
    "Tipo de vertido": "cubilote",
    "Riesgo": "X0",
}

result = create_template(description, variables)
print(result.template)      # Template with placeholders
print(result.placeholders)  # Variables that were found
print(result.not_found)     # Variables not found in text
```

## Files

```
scraper/template_extraction/
├── simple_template.py      # Simple search-replace template creation (~80 lines)
├── browser_extractor.py    # Playwright-based page extraction
├── combination_generator.py # Variable extraction + CYPEExtractor class
├── text_extractor.py       # Text parsing utilities
└── TEMPLATE_EXTRACTION.md  # Detailed technical notes (internal)
```

## Limitations

1. **Computed values**: If the page shows "HA-30" but the variable is "Resistencia: 25", we can't detect it (the value doesn't appear directly)

2. **Multiple occurrences**: If a value appears multiple times, all occurrences get replaced

3. **Context-dependent**: No understanding of where values should/shouldn't be replaced

## Testing

```bash
# Run template extraction tests
python -m pytest scraper/tests/test_live_extraction.py::TestDescriptionExtraction -v

# Quick test of simple_template module
python scraper/template_extraction/simple_template.py
```

## Results

The simple approach typically finds **6-10 placeholders** per element, covering:
- Resistance values (25, 30, etc.)
- Material types (cubilote, bomba, etc.)
- Exposure classes (X0, XC1, etc.)
- Heights, thicknesses, and other dimensions
