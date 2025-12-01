# Test Suite

## End-to-End Test

**`test_end_to_end.py`** - Validates Excel export from real database

### Usage:
```bash
python3 test_end_to_end.py
```

### What it tests:
- Excel file generation
- Required sheets present (ALL_ELEMENTS, PROJECT_OVERVIEW)  
- Required columns present
- Description rendering completeness