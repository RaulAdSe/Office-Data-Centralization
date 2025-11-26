# Office Variable System Demo

Complete demonstration of the Office Variable System using your real `office_data.db` with 75 construction elements.

## What This Demonstrates

This demo shows the complete **Element → Variables → Projects → Rendered Descriptions** flow using your actual database with Spanish construction elements.

### System Overview

```
ELEMENTS (75 total)           →  VARIABLES (85 total)           →  PROJECT USAGE
├─ CSL010: Foundation        →   ├─ codigo (TEXT)               →   ├─ Set values
├─ EHM010: Concrete Wall     →   ├─ variable (TEXT)             →   ├─ Fill "codigo = IIa"
├─ RMB025: Wood Varnish      →   └─ dimension (TEXT)            →   └─ Fill "variable = liso"
└─ ... 72 more              →                                   →
                              →                                   →
TEMPLATES                     →  PLACEHOLDER REPLACEMENT        →   RENDERED DESCRIPTIONS
"Muro de hormigón HA-25/     →   {codigo} → IIa                →   "Muro de hormigón HA-25/
F/20/{codigo} con acabado    →   {variable} → liso             →   F/20/IIa con acabado liso..."
{variable}..."               →                                   →
```

## What's Included

### 🗄️ Database (`office_data.db`)
- **75 construction elements** - Real Spanish construction catalog
- **85 variables** - Properties like `codigo`, `variable`, `dimension`
- **75 active templates** - Spanish description templates with `{placeholders}`
- **Complete schema** - Projects, elements, variables, values, approvals

### 🐍 Python API (`api/office_db_manager.py`)
- **OfficeDBManager** class with all database operations
- **Template rendering** engine (replaces `{variable}` with actual values)
- **Project management** - Create projects, add elements, set values
- **Element browsing** - View all 75 elements and their variables

### 🌐 Web UI (`ui/`)
- **Flask web interface** - Browse elements, create projects, edit values
- **Real-time rendering** - See descriptions update as you change variables
- **Element catalog** - Search and browse your 75 construction elements
- **Project management** - Create projects and add elements from the catalog

### 📝 Examples & Tests
- **Complete demo script** - Creates sample project with multiple elements
- **SQL examples** - Step-by-step database operations
- **Template rendering tests** - Shows variable substitution in action

## Quick Start

### 1. Run the Complete Demo
```bash
python3 run_complete_demo.py
```

**This will:**
- Show overview of your 75 elements
- Create a demo project with foundation, wall, and finish elements
- Fill in variable values (`codigo = "IIa"`, `variable = "liso"`)
- Render Spanish descriptions with substituted values

### 2. Start the Web Interface
```bash
python3 ui/app.py
```

Then browse to: **http://localhost:5000**

**You can:**
- 📋 Browse all 75 construction elements
- 🔍 View element details, variables, and templates
- 🏗️ Create new projects
- ➕ Add elements to projects
- ✏️ Fill variable values and see live rendering
- 📄 View complete project descriptions

## Example Flow

### 1. Pick an Element
```
EHM010_PROD_1764161964: MURO DE HORMIGÓN
Variables: codigo (TEXT), variable (TEXT)
Template: "Muro de hormigón HA-25/F/20/{codigo} con acabado {variable}..."
```

### 2. Add to Project
```
Project: "Barcelona Office Building"
Element Instance: "WALL-001" (Exterior Wall - North Face)
```

### 3. Fill Variables
```
codigo = "IIa"      (concrete grade)
variable = "liso"   (smooth finish)
```

### 4. Get Rendered Description
```
"Muro de hormigón armado 2C, de hasta 3 m de altura, espesor 30 cm, 
superficie plana, realizado con hormigón HA-25/F/20/IIa fabricado en 
central, y vertido con cubilote, y acero UNE-EN 10080 B 500 S, con una 
cuantía aproximada de 50 kg/m³, ejecutado en condiciones complejas; 
montaje y desmontaje de sistema de encofrado con acabado liso..."
```

## Real Data Examples

Your database includes:

**Foundation Elements:**
- CSL010: Losa de cimentación (Foundation slab)
- CSV010: Zapata corrida (Strip footing)
- CSZ010: Zapata de cimentación (Isolated footing)

**Structural Elements:**
- EHM010: Muro de hormigón (Concrete wall)
- EAE010: Acero en estructura (Steel structure)
- EMF040: Muro de fábrica (Masonry wall)

**Finish Elements:**
- RMB025: Barniz al agua para madera (Water-based wood varnish)
- RMB015: Barniz sintético (Synthetic varnish)
- And 65+ more...

Each element has:
- ✅ **Real Spanish names** and descriptions
- ✅ **Defined variables** (codigo, variable, dimension, etc.)
- ✅ **Active templates** with placeholder substitution
- ✅ **Pricing information** (where available)

## Technical Details

### Variable Types Supported
- **TEXT** - Free text input (codes, descriptions)
- **NUMERIC** - Numbers with units (dimensions, quantities)
- **DATE** - Date values (installation dates, inspections)

### Template System
- **Placeholders**: `{variable_name}` in templates
- **Substitution**: Replaces with actual values from project
- **Fallback**: Keeps placeholder if no value provided
- **Spanish Content**: All templates in Spanish construction terminology

### Database Schema
- **Elements** - Abstract construction element definitions
- **Variables** - Properties that elements can have
- **Projects** - Construction projects 
- **Project Elements** - Specific instances in projects
- **Values** - Actual variable values for instances
- **Rendered Descriptions** - Final text with substitutions

## What Makes This Special

1. **Real Data** - 75 actual Spanish construction elements, not toy examples
2. **Production Ready** - Complete approval workflow (S0→S1→S2→S3)
3. **Template Engine** - Dynamic description generation
4. **Full Stack** - Database → API → Web UI
5. **Multilingual** - Spanish construction terminology
6. **Industry Standard** - Construction element catalog structure

## Next Steps

1. **Explore the Web UI** - Browse your 75 elements and create projects
2. **Add More Elements** - Expand the catalog with new construction items
3. **Create Variable Options** - Add dropdown choices for common variables
4. **Build Reports** - Generate project BOQs and specifications
5. **API Integration** - Connect to external construction software

Your database is ready for production use! 🚀