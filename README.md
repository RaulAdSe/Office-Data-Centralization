# Office Data Centralization System

> **Status:** Proof of Concept (POC)  
> **Goal:** Single source of truth for construction elements across Presto, Revit, Word, and Excel

## Problem

Data duplicated across 4 systems → Manual updates → Inconsistencies → Time waste

## Solution

SQLite database → Excel → Word (via LINK fields) → Presto → Revit

## Quick Start

```bash
# Setup
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Initialize database
cd poc
python poblar_datos.py

# Export project
python exportar_excel.py --proyecto PROY_001
```

## Repository Structure

```
├── poc/              # Proof of Concept code (current implementation)
├── docs/             # Documentation
├── scripts/          # Production scripts (CLI entry points)
├── src/              # Reusable modules (database, exporters, utils)
├── tests/            # Test files
├── outputs/          # Generated files (Excel, Word)
└── backups/          # Database backups
```

### Using the Scaffolding

**Current (POC):** All code in `poc/` folder

**As you grow:**
- **`src/`** - Extract reusable modules (e.g., `src/database.py`, `src/exporters.py`)
- **`scripts/`** - Create CLI scripts that import from `src/` (e.g., `scripts/export.py`)
- **`tests/`** - Add test files mirroring `src/` structure (e.g., `tests/test_exporters.py`)

**Example migration:**
```python
# Before (poc/exportar_excel.py)
import sqlite3
import pandas as pd
# ... all code here

# After (src/exporters.py)
def export_to_excel(project_code: str, db_path: str) -> str:
    # Reusable function
    
# scripts/export.py
from src.exporters import export_to_excel
if __name__ == "__main__":
    export_to_excel("PROY_001", "elementos.db")
```

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design
- [TECH_STACK.md](docs/TECH_STACK.md) - Technologies used
- [WORKFLOW.md](docs/WORKFLOW.md) - Development workflow
- [CONTRIBUTING.md](.github/CONTRIBUTING.md) - Contribution guidelines

## Development Workflow

1. **Never push to `main`** - Use feature branches
2. **Create PR** for all changes
3. **Code review required** before merging

See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for details.

---

**Last updated:** December 2024
