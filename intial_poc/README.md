# Proof of Concept (POC)

This folder contains the initial proof of concept implementation.

## Files

- `schema.sql` - Database schema definition
- `poblar_datos.py` - Script to populate database with test data
- `exportar_excel.py` - Script to export project data to Excel
- `plantilla_memoria.docx` - Word template (for future Word integration)

## Quick Start

```bash
# Initialize database
python poblar_datos.py

# Export project to Excel
python exportar_excel.py --proyecto PROY_001
```

## Status

✅ **Completed:**
- SQLite database schema
- Excel export functionality
- Test data population

⏳ **Next Steps:**
- Word document generation with LINK fields
- Improved export structure

