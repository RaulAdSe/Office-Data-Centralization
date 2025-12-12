# System Architecture

## Overview

Single source of truth (SQLite) → Excel → Word → Presto → Revit

## Centralized Database Layer

All database operations are centralized in a single module:

```
src/db_manager.py          ← Single source of truth for all DB logic
       │
       ├── app/app_gestio.py      (Streamlit UI)
       ├── scraper/pipeline.py    (CYPE data import)
       ├── db-to-word/            (Excel export for Mail Merge)
       └── tests/                 (All test suites)
```

### Benefits of Centralization

- **Single source of truth** - All database operations in one place
- **Consistency** - Same validation rules everywhere (e.g., 33 construction categories)
- **Easier maintenance** - Fix bugs once, propagate everywhere
- **Better testability** - Test `db_manager.py` once, trust it everywhere
- **Clear separation** - `db_manager.py` = data, apps = presentation

## Data Flow

```
SQLite Database (data/office_data.db)
    ↓ [db_manager.py]
    ├── app/app_gestio.py (Streamlit web interface)
    ├── scraper/pipeline.py (CYPE element import)
    └── db-to-word/ (Excel export)
         ↓
    Excel (Mail Merge optimized)
         ↓ [LINK fields]
    Word (Technical Report)
         ↓ [Export]
    Presto → Revit
```

## Core Components

### 1. Data Layer (`src/db_manager.py`)

Central database manager handling:
- Element and variable CRUD operations
- Description versioning (S0 → S1 → S2 → S3 workflow)
- 3-vote approval system
- Project and element instance management
- Description rendering with placeholder substitution
- User authentication support
- Category validation (33 official construction categories)

### 2. Web Interface (`app/app_gestio.py`)

Streamlit application providing:
- User authentication with role-based access
- Element catalog management (browse, create, edit)
- Variable management with dropdown options
- Draft creation and approval voting
- Project management with bulk element creation
- Variable value editing per instance

### 3. Data Import (`scraper/`)

CYPE scraper for importing construction elements:
- Automated element extraction from CYPE
- Variable and option parsing
- Database integration via `db_manager.py`

### 4. Export Layer (`db-to-word/`)

Excel export for Word Mail Merge:
- Category-based sheet organization
- All variables as named columns
- Rendered descriptions with placeholder substitution
- Direct Mail Merge field compatibility

### 5. Integration Layer (Excel)

- **ALL_ELEMENTS** - Complete project elements
- **Category sheets** - FOUNDATIONS, STEEL_STRUCTURE, etc.
- **PROJECT_OVERVIEW** - Summary statistics

### 6. Presentation Layer (Word)

- Native LINK fields to Excel
- Mail Merge with direct field access (`{{ MERGEFIELD UBICACION }}`)
- Auto-update via F9

## Database Schema

See `docs/DATABASE.md` for complete schema documentation.

Key tables:
- `elements` - Construction element types with 33-category validation
- `element_variables` - Variables with type, unit, options
- `variable_options` - Dropdown options for LIST variables
- `description_versions` - Versioned templates with approval workflow
- `projects` - Project definitions
- `project_elements` - Element instances within projects
- `project_element_values` - Variable values per instance
- `rendered_descriptions` - Cached rendered descriptions
- `users` - User authentication with roles

## Development Phases

- ✅ **Phase 1: POC** - SQLite + Excel export
- ✅ **Phase 2: Core** - Streamlit app, version control, approval workflow
- ✅ **Phase 3: Integration** - CYPE scraper, centralized db_manager
- 🔄 **Phase 4: Advanced** - REST API, chatbot, web interface
- ⏳ **Phase 5: Deployment** - Office rollout

## Key Decisions

- **Centralized database module** - All DB operations via `db_manager.py`
- **Excel as intermediary** - Single transformation pipeline for Mail Merge
- **Native Word LINK fields** - No additional code needed
- **SQLite for simplicity** - Zero config, portable, easy backup
- **33 construction categories** - Standardized CYPE-compatible classification
- **3-vote approval** - Collaborative description validation

---

**Last updated:** December 2024
