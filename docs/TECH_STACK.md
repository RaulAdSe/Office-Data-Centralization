# Tech Stack

## Core Technologies

### SQLite (3.40+)
- Zero-configuration, single file
- Perfect for 1-100 concurrent projects
- Migrate to PostgreSQL if >50 concurrent users

### Python (3.10+)
- Rich ecosystem for Excel, Word, DB manipulation
- Cross-platform

## Python Libraries

### Core (POC)
```bash
pandas>=2.0.0      # Data manipulation
openpyxl>=3.1.0   # Excel export
python-docx>=0.8.11  # Word manipulation
```

### Future
- `watchdog` - File monitoring (Phase 2)
- `fastapi` - REST API (Phase 3)
- `streamlit` - Web interface (Phase 3)

## External Integrations

### Microsoft Word
- Native LINK fields: `{ LINK Excel.Sheet "file.xlsx" "Referencias!B3" \a }`
- Update via F9 or auto on open
- No Python code needed once configured

### Presto/Revit
- Presto: CSV/Excel export (Phase 2)
- Revit: Via Presto (existing) or Dynamo (future)

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Resources

- [pandas docs](https://pandas.pydata.org/docs/)
- [openpyxl docs](https://openpyxl.readthedocs.io/)
- [Word LINK fields](https://support.microsoft.com/en-us/office/field-codes-link-field-d71f9a42-92c0-44e5-9bce-dce0d8fc9f09)

---

**Last updated:** December 2024
