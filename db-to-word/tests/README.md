# Tests for DB-to-Word System

This folder contains comprehensive tests for the 33-category Excel export system.

## 🧪 End-to-End Test

**`test_end_to_end.py`** - Complete workflow test from element creation to Excel export

### What it tests:

1. **Database Schema Creation** with 33-category validation
2. **Element Creation** across multiple construction categories
3. **Variable Definition** with different types (TEXT, NUMERIC)
4. **Template Creation** with parametric placeholders
5. **Project Management** with element instances
6. **Value Assignment** for project-specific elements
7. **Description Rendering** with placeholder substitution
8. **Excel Export Generation** with category-specific sheets
9. **Content Validation** of generated Excel structure

### Test Coverage:

- **3 Construction Categories**: MURO CORTINA, FONTANERIA, ESTRUCTURA METALICA  
- **6 Element Types**: 2 different element types per category
- **9 Element Instances**: Multiple instances per category testing variety
  - **MURO CORTINA**: 3 instances (2 element types: Principal + Secundario)
  - **FONTANERIA**: 3 instances (2 element types: Tubería + Válvula)  
  - **ESTRUCTURA METALICA**: 3 instances (2 element types: Viga + Pilar)
- **Multiple Variables**: Materials, dimensions, specifications, colors
- **Template Rendering**: Automatic placeholder substitution with diverse values
- **Excel Structure**: INDEX_GLOBAL, CATEGORIES_REFERENCE, MM_[CATEGORY] sheets

### Run the Test:

```bash
cd db-to-word
python3 tests/test_end_to_end.py
```

### Expected Output:

```
🎉 END-TO-END TEST COMPLETED SUCCESSFULLY!
📋 TEST SUMMARY:
   Database: tests/test_e2e.db
   Excel Output: excel_exports/TEST-2025_TEST_EXPORT.xlsx
   Elements: 6 (2 per category)
   Instances: 9 (multiple per category)
   Category Sheets: 3
```

### Test Validation:

✅ **Database Level**
- Schema creation with 33 categories
- Category validation enforcement
- Element and project creation
- Variable and value management

✅ **Template Processing**
- Placeholder extraction and mapping
- Description rendering with real values
- Template validation

✅ **Excel Export**
- Correct sheet structure (INDEX_GLOBAL + CATEGORIES_REFERENCE + MM_[CATEGORY])
- Category-specific data separation
- Word Mail Merge compatible field naming
- Content validation of rendered descriptions

✅ **Data Quality**
- All descriptions properly rendered (no [SIN VALOR])
- Category sheets contain only relevant elements
- Field naming follows convention: `{ELEMENT}_{INSTANCE}_{ATTRIBUTE}`

## 🎯 Test Results

The test validates the complete workflow:

**Database → Elements → Variables → Templates → Project → Instances → Values → Rendering → Excel**

This ensures the entire 33-category system works end-to-end for production use with Word Mail Merge integration.