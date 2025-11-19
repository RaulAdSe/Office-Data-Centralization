# System Architecture

## Overview

Single source of truth (SQLite) → Excel → Word → Presto → Revit

## Data Flow

```
SQLite Database
    ↓ [exportar_excel.py]
Excel (3 sheets: Resumen, Elementos, Referencias)
    ↓ [LINK fields]
Word (Technical Report)
    ↓ [Export]
Presto → Revit
```

## Core Components

### 1. Data Layer (SQLite)
- `elementos` - Construction elements catalog
- `proyectos` - Active projects
- `proyecto_elementos` - Many-to-many relationships

### 2. Export Layer (Python)
- **POC:** `poc/exportar_excel.py` - Standalone script
- **Production:** `src/exporters.py` - Reusable modules, `scripts/export.py` - CLI
- Future: Word generation, Presto export

### 3. Integration Layer (Excel)
- **Resumen** - Project overview
- **Elementos** - Detailed table
- **Referencias** - Key-value pairs for Word

### 4. Presentation Layer (Word)
- Native LINK fields to Excel
- Auto-update via F9

## Development Phases

- ✅ **Phase 1: POC** - SQLite + Excel export
- 🔄 **Phase 2: Core** - Word integration, version control
- ⏳ **Phase 3: Advanced** - REST API, chatbot, web interface
- ⏳ **Phase 4: Deployment** - Office rollout

## Key Decisions

- **Excel as intermediary** - Single transformation pipeline
- **Native Word LINK fields** - No additional code needed
- **SQLite for POC** - Zero config, easy migration later

---

**Last updated:** December 2024
