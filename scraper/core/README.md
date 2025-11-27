# Core Scraper Modules

Production-ready scraper components:

- **page_detector.py** - Detects element vs category pages
- **element_extractor.py** - Extracts element data and variables  
- **url_crawler.py** - Crawls and finds element URLs
- **scraper.py** - Main orchestrator script

## Usage
```python
from core.element_extractor import extract_multiple_elements
elements = extract_multiple_elements(urls)
```
