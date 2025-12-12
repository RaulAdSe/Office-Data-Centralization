# Template Extraction - How It Works

## The Problem

We want to extract **templates** from CYPE construction element pages. A template looks like:

```
Viga de hormigón armado, realizada con hormigón {Resistencia} N/mm²,
vertido con {Tipo de vertido}, y acero {Tipo de acero}.
```

Where `{Resistencia}`, `{Tipo de vertido}`, etc. are **placeholders** that get filled with actual values.

## The Challenge

The CYPE website doesn't give us templates directly. It gives us:

1. **Variables** (form fields): "Resistencia" with options [25, 30, 35, 40]
2. **Rendered descriptions**: Fully filled text like "...hormigón 25 N/mm²..."

We need to figure out WHERE in the description each variable appears.

## Current Approach (Overcomplicated)

The current code does this:

1. Extract all form variables from the page
2. Generate multiple "combinations" (different variable values)
3. For each combination, capture the resulting description
4. Compare descriptions to find what text changed
5. Map changes back to variables to create placeholders

**Problem**: This is complex, slow, and doesn't work well because:
- Many variables don't directly appear in the text
- Some values are computed (HA-30 doesn't change when "Resistencia: 25" changes)
- The diff-based approach has edge cases

## Simplified Approach (Proposed)

### Option A: Direct Value Search

Instead of comparing multiple descriptions, just:

1. Get ONE description with known variable values
2. Search for each variable's value in the text
3. Replace found values with `{VariableName}`

```python
def create_template(description: str, variables: dict) -> str:
    """
    Simple template creation by finding variable values in text.

    Args:
        description: "Viga con hormigón HA-25/F/20..."
        variables: {"Resistencia": "25", "Tipo de vertido": "cubilote", ...}

    Returns:
        "Viga con hormigón HA-{Resistencia}/F/20..."
    """
    template = description

    for var_name, var_value in variables.items():
        if var_value and len(var_value) >= 2:  # Skip very short values
            # Only replace if it looks like a standalone value
            template = template.replace(var_value, f"{{{var_name}}}")

    return template
```

**Pros**: Simple, fast, one page load
**Cons**: May miss values that appear differently in text

### Option B: No Templates (Just Store Variables)

Maybe we don't need templates at all for the scraper. Instead:

1. Extract variables with their options
2. Store raw description as reference
3. Let the application layer handle templating if needed

This separates concerns:
- **Scraper**: Gets data from CYPE (variables, descriptions, codes)
- **Database**: Stores the raw data
- **Application**: Creates templates when needed

## What We Actually Need

For the MVP, we probably just need:

1. **Element code**: EHV010
2. **Element name**: Viga de hormigón armado
3. **Variables**: List of {name, type, options, unit}
4. **Description**: Raw text from the page
5. **Category**: HORMIGÓN ARMADO

Templates can be created later by a human or more sophisticated logic.

## Files Involved

```
scraper/template_extraction/
├── __init__.py              # Exports CYPEExtractor
├── browser_extractor.py     # Playwright-based extraction (600+ lines, complex)
├── combination_generator.py # Generates test combinations (260 lines)
├── text_extractor.py        # Regex-based variable extraction (200 lines)
└── template_builder.py      # Diff-based template building (150 lines)
```

## Recommendation

Simplify to:

```
scraper/
├── extractor.py        # Single file: load page, get variables, get description
└── models.py           # Data classes: Element, Variable, etc.
```

Template generation (if needed) should be a separate, optional step.
