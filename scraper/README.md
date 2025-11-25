# CYPE Scraper

Modular web scraper for CYPE construction elements from generadordeprecios.info.

## 📁 Directory Structure

```
scraper/
├── core/           # Core scraper modules
├── examples/       # Example usage scripts  
├── tests/          # Test and debug scripts
├── data/           # Output data (JSON, DB)
├── utils/          # Utility functions
└── README.md       # This file
```

## 🚀 Quick Start

```python
# Import core modules
from core.element_extractor import extract_multiple_elements

# Scrape elements
urls = ["https://generadordeprecios.info/..."]
elements = extract_multiple_elements(urls)

# Access data
for element in elements:
    print(f"{element.code}: {element.title}")
    print(f"Variables: {len(element.variables)}")
```

## 📊 Features

- ✅ **Page Detection** - Distinguish elements from categories
- ✅ **Data Extraction** - Titles, prices, descriptions, variables
- ✅ **Variable Parsing** - TEXT, RADIO, CHECKBOX options
- ✅ **Spanish Encoding** - Proper UTF-8 handling (ñ, ó, í, etc.)
- ✅ **JSON Export** - Clean, structured output
- ✅ **Database Integration** - Compatible with existing DB schema

## 🎯 Extracted Data

Each element includes:
- **Metadata**: Code, title, unit, price, URL
- **Descriptions**: Main, technical, criteria, normativa  
- **Variables**: User customization options
- **Stats**: Variable counts by type

Generated: Core scraper modules
