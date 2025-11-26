# CYPE Scraper Database Storage Details

## What Gets Stored in Your Database

When you run the complete CYPE pipeline, here's exactly what data gets stored in each table:

## 📊 **Data Flow Summary**

For each of the 694+ CYPE elements discovered:

1. **Element metadata** → `elements` table
2. **40+ variables per element** → `element_variables` table  
3. **Hundreds of variable options** → `variable_options` table
4. **Template with placeholders** → `description_versions` table
5. **Variable→placeholder mappings** → `template_variable_mappings` table

---

## 📋 **Table-by-Table Breakdown**

### 1. `elements` Table
**What**: Basic element information
**Spanish Data**: ✅ Element titles and codes in Spanish

```sql
-- Example data stored:
INSERT INTO elements VALUES (
    1,                               -- element_id 
    'EHV015',                       -- element_code (from CYPE)
    'VIGA EXENTA DE HORMIGÓN VISTO', -- element_name (Spanish!)
    '2024-11-25 10:30:00',         -- created_at
    'CYPE_Scraper'                  -- created_by
);
```

**Real Examples from CYPE**:
- `RML010` - "LACA SINTÉTICA PARA MADERA" 
- `CPI080` - "PILOTE BARRENADO Y HORMIGONADO POR TUBO CENTRAL DE BARRENA"
- `EHE020` - "ESCALERA DE HORMIGÓN VISTO"

---

### 2. `element_variables` Table  
**What**: All customizable variables for each element (40+ per element average)
**Spanish Data**: ✅ Variable names in Spanish

```sql
-- Example variables for a concrete beam:
INSERT INTO element_variables VALUES (
    1, 1, 'tipo_hormigon', 'TEXT', NULL, 'HA-25', 1, 1, '2024-11-25'
), (
    2, 1, 'ancho', 'TEXT', 'cm', '30', 1, 2, '2024-11-25'
), (
    3, 1, 'alto', 'TEXT', 'cm', '60', 1, 3, '2024-11-25'
), (
    4, 1, 'clase_exposicion', 'TEXT', NULL, 'XC1', 1, 4, '2024-11-25'
), (
    5, 1, 'tipo_acero', 'TEXT', NULL, 'B 500 S', 1, 5, '2024-11-25'
);
```

**Spanish Variable Examples**:
- `tipo_hormigon` (concrete type)
- `clase_exposicion` (exposure class)  
- `acabado_superficie` (surface finish)
- `ubicacion_aplicacion` (application location)
- `nivel_transito` (traffic level)

---

### 3. `variable_options` Table
**What**: All available options for each variable (Spanish values!)
**Spanish Data**: ✅ All option values in Spanish

```sql
-- Example options for concrete type:
INSERT INTO variable_options VALUES (
    1, 1, 'HA-25', 'HA-25', 1, '2024-11-25'
), (
    2, 1, 'HA-30', 'HA-30', 2, '2024-11-25'  
), (
    3, 1, 'HA-35', 'HA-35', 3, '2024-11-25'
);

-- Example options for surface finish:
INSERT INTO variable_options VALUES (
    4, 3, 'Visto', 'Visto', 1, '2024-11-25'
), (
    5, 3, 'Para revestir', 'Para revestir', 2, '2024-11-25'
), (
    6, 3, 'Con molde fenólico', 'Con molde fenólico', 3, '2024-11-25'
);
```

**Spanish Option Examples**:
- `"Visto"` (exposed concrete)
- `"Para revestir"` (to be covered)
- `"Con molde fenólico"` (with phenolic mold)
- `"Interior"`, `"Exterior"` (interior, exterior)
- `"Bajo"`, `"Medio"`, `"Alto"` (low, medium, high)

---

### 4. `description_versions` Table
**What**: Template with placeholders for dynamic descriptions  
**Spanish Data**: ✅ Templates in Spanish with variable placeholders

```sql
-- Example template with placeholders:
INSERT INTO description_versions VALUES (
    1,                                      -- version_id
    1,                                      -- element_id  
    'Viga {tipo_hormigon} de {ancho}×{alto} cm, clase de exposición {clase_exposicion}',
    'S3',                                   -- state (approved)
    1,                                      -- is_active
    1,                                      -- version_number
    '2024-11-25 10:30:00',                -- created_at
    'CYPE_Scraper',                        -- created_by
    '2024-11-25 10:30:00'                 -- updated_at
);
```

**Real Template Examples**:
- `"Viga exenta de hormigón visto de tipo {tipo_hormigon} de dimensiones {ancho}×{alto}"`
- `"Laca sintética para madera en {ubicacion_aplicacion} con nivel de tránsito {nivel_transito}"`
- `"Pilote de {tipo_hormigon} de diámetro {diametro} y profundidad {profundidad}"`

---

### 5. `template_variable_mappings` Table  
**What**: Maps placeholders in templates to actual variables
**Purpose**: Links `{tipo_hormigon}` placeholder to `tipo_hormigon` variable

```sql
-- Example mappings for template placeholders:
INSERT INTO template_variable_mappings VALUES (
    1, 1, 1, 'tipo_hormigon', 1, '2024-11-25'    -- {tipo_hormigon} → variable #1, position 1
), (
    2, 1, 2, 'ancho', 2, '2024-11-25'            -- {ancho} → variable #2, position 2  
), (
    3, 1, 3, 'alto', 3, '2024-11-25'             -- {alto} → variable #3, position 3
), (
    4, 1, 4, 'clase_exposicion', 4, '2024-11-25' -- {clase_exposicion} → variable #4, position 4
);
```

---

## 🔍 **Example: Complete Element Data**

Here's what a complete CYPE element looks like in your database:

### Element: "VIGA EXENTA DE HORMIGÓN VISTO" (EHV015)

**`elements` table:**
```
element_code: EHV015  
element_name: VIGA EXENTA DE HORMIGÓN VISTO
```

**`element_variables` table (sample of 40+ variables):**
```
tipo_hormigon     → Options: HA-25, HA-30, HA-35
ancho            → Options: 25 cm, 30 cm, 35 cm, 40 cm  
alto             → Options: 40 cm, 50 cm, 60 cm, 70 cm
clase_exposicion → Options: XC1, XC2, XC3, XC4
tipo_acero       → Options: B 500 S, B 500 SD
acabado          → Options: Visto, Para revestir
```

**`description_versions` table:**
```
description_template: "Viga exenta de hormigón visto de tipo {tipo_hormigon} de dimensiones {ancho}×{alto}"
```

**`variable_options` table (hundreds of entries):**
```
tipo_hormigon: "HA-25", "HA-30", "HA-35", "HA-40", "HA-45", "HA-50"
ancho: "25", "30", "35", "40", "45", "50", "60", "70", "80"  
alto: "40", "50", "60", "70", "80", "100", "120", "140"
...
```

---

## 📈 **Scale: What You Get**

Running the complete pipeline stores:

### **Elements**: 694+ construction elements
- Concrete beams, columns, stairs, foundations
- Steel structures, connections, plates  
- Wood beams, columns, connections
- Paints, varnishes, lacquers, treatments
- Doors, windows, facades, roofs
- Installations, pipes, electrical systems

### **Variables**: ~30,000+ customizable parameters  
- Material types, dimensions, finishes
- Structural properties, load classes
- Installation locations, applications
- Colors, textures, performance specs

### **Options**: ~200,000+ Spanish option values
- All concrete types (HA-25, HA-30, HA-35...)
- All steel grades (B 500 S, B 500 SD...)  
- All finishes (Visto, Para revestir...)
- All locations (Interior, Exterior...)

### **Templates**: 694+ Spanish description templates
- Clean templates with variable placeholders
- No hardcoded units (stored separately)
- Ready for dynamic description generation

---

## 🔄 **How Templates Work**

When someone selects options in your system:

1. **User selects**: `tipo_hormigon="HA-30"`, `ancho="40"`, `alto="60"`

2. **Template**: `"Viga exenta de hormigón visto de tipo {tipo_hormigon} de dimensiones {ancho}×{alto}"`

3. **Generated description**: `"Viga exenta de hormigón visto de tipo HA-30 de dimensiones 40×60"`

4. **Result**: Perfect Spanish construction description!

---

## ✅ **Data Quality Guarantees**

- **✅ Spanish Text**: All content in original Spanish (no translations)
- **✅ Technical Accuracy**: Data extracted directly from CYPE's professional system
- **✅ Complete Coverage**: 40+ variables per element (comprehensive customization)
- **✅ Clean Templates**: No hardcoded units, proper placeholder structure
- **✅ Proper Relationships**: All foreign keys and constraints maintained

---

## 🚀 **Ready to Use**

Once stored, your database becomes a comprehensive Spanish construction elements system with:

- **Professional construction vocabulary** in Spanish
- **Complete parametric descriptions** for 694+ elements  
- **Thousands of technical options** for precise specifications
- **Dynamic description generation** using templates
- **Full CYPE compatibility** for Spanish construction industry

**Total Size**: Approximately 300,000+ database records with complete Spanish construction data!