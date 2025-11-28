-- ============================================================
-- COMPLETE SCHEMA WITH VARIABLE OPTIONS
-- Handles both free-form input AND fixed dropdown options
-- ============================================================

-- ============================================================
-- PART 1: ELEMENT TEMPLATE DEFINITIONS
-- ============================================================

CREATE TABLE elements (
    element_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    element_code    VARCHAR(50) NOT NULL UNIQUE,
    element_name    VARCHAR(255) NOT NULL,
    category        VARCHAR(50) NOT NULL CHECK (category IN (
        'ASCENSOR', 'CARPINTERIA', 'CARPINTERIA INDUSTRIAL', 'CARTELERIA',
        'CIMENTACION', 'CUBIERTAS Y FACHADAS', 'ENCEPADOS', 'EQUIPAMIENTOS',
        'ESTRUCTURA DE MADERA', 'ESTRUCTURA METALICA', 'ESTRUCTURA PREFABRICADA',
        'FONTANERIA', 'GEOTECNICO', 'GRUPO ELECTROGENO', 'INAUFUGACION',
        'INSTALACION BT', 'INSTALACION DE CLIMA Y VENTILACION', 'INSTALACION DE FRIO',
        'INSTALACION DE PARARRAYOS', 'INSTALACION PCI', 'MOVIMIENTO DE TIERRAS',
        'MURO CORTINA', 'OBRA CIVIL', 'PILOTATGE', 'SANEAMIENTO PLUVIALES CUBIERTA',
        'SANEAMIENTO RESIDUALES', 'SANEAMIENTO URBANIZACION', 'SLOTDRAIN', 'SOLERAS',
        'SUMINISTRO DE CT Y CS', 'SUMINISTRO SEPARADORES DE HIDROCARBURO',
        'SUMINISTROS DE ILUMINACION', 'URBANIZACION EXTERIOR'
    )),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by      VARCHAR(100)
);

-- ============================================================

CREATE TABLE element_variables (
    variable_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    element_id      INTEGER NOT NULL REFERENCES elements(element_id) ON DELETE CASCADE,
    variable_name   VARCHAR(100) NOT NULL,
    variable_type   VARCHAR(20) NOT NULL CHECK (variable_type IN ('TEXT', 'NUMERIC', 'DATE')),
    unit            VARCHAR(20),
    default_value   TEXT,
    is_required     BOOLEAN DEFAULT 1,
    display_order   INTEGER DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (element_id, variable_name)
);

CREATE INDEX idx_element_variables_element ON element_variables(element_id);

-- ============================================================
-- VARIABLE OPTIONS (For dropdown/select inputs)
-- ============================================================

CREATE TABLE variable_options (
    option_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_id     INTEGER NOT NULL REFERENCES element_variables(variable_id) ON DELETE CASCADE,
    option_value    VARCHAR(255) NOT NULL,
    option_label    VARCHAR(255),           -- Optional display label (e.g., "Hormigón" for value "concrete")
    display_order   INTEGER DEFAULT 0,
    is_default      BOOLEAN DEFAULT 0,      -- Mark default option
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (variable_id, option_value)
);

CREATE INDEX idx_variable_options_variable ON variable_options(variable_id);

COMMENT ON TABLE variable_options IS 'Fixed options for dropdown/select inputs. If variable has options here, show dropdown. If not, show free input.';

-- ============================================================
-- PART 2: DESCRIPTION VERSIONING
-- ============================================================

CREATE TABLE description_versions (
    version_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    element_id          INTEGER NOT NULL REFERENCES elements(element_id) ON DELETE CASCADE,
    description_template TEXT NOT NULL,
    state               VARCHAR(2) NOT NULL DEFAULT 'S0' CHECK (state IN ('S0', 'S1', 'S2', 'S3', 'D')),
    is_active           BOOLEAN DEFAULT 0,
    version_number      INTEGER NOT NULL,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by          VARCHAR(100),
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (element_id, version_number),
    CHECK (is_active = 0 OR state = 'S3')
);

CREATE INDEX idx_description_versions_element_state ON description_versions(element_id, state);

-- ============================================================

CREATE TABLE template_variable_mappings (
    mapping_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id      INTEGER NOT NULL REFERENCES description_versions(version_id) ON DELETE CASCADE,
    variable_id     INTEGER NOT NULL REFERENCES element_variables(variable_id) ON DELETE CASCADE,
    placeholder     VARCHAR(100) NOT NULL,
    position        INTEGER NOT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (version_id, placeholder),
    UNIQUE (version_id, position)
);

CREATE INDEX idx_template_mappings_version ON template_variable_mappings(version_id);
CREATE INDEX idx_template_mappings_variable ON template_variable_mappings(variable_id);

-- ============================================================

CREATE TABLE approvals (
    approval_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id      INTEGER NOT NULL REFERENCES description_versions(version_id) ON DELETE CASCADE,
    from_state      VARCHAR(2) NOT NULL,
    to_state        VARCHAR(2) NOT NULL,
    approved_by     VARCHAR(100) NOT NULL,
    approved_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    comments        TEXT
);

CREATE INDEX idx_approvals_version ON approvals(version_id);

-- ============================================================
-- PART 3: PROJECTS
-- ============================================================

CREATE TABLE projects (
    project_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    project_code    VARCHAR(50) NOT NULL UNIQUE,
    project_name    VARCHAR(255) NOT NULL,
    status          VARCHAR(20) DEFAULT 'PLANNING' CHECK (status IN ('PLANNING', 'ACTIVE', 'COMPLETED', 'CANCELLED')),
    start_date      DATE,
    end_date        DATE,
    location        TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by      VARCHAR(100)
);

-- ============================================================
-- PART 4: PROJECT ELEMENT INSTANCES
-- ============================================================

CREATE TABLE project_elements (
    project_element_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id              INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    element_id              INTEGER NOT NULL REFERENCES elements(element_id) ON DELETE RESTRICT,
    description_version_id  INTEGER NOT NULL REFERENCES description_versions(version_id) ON DELETE RESTRICT,
    instance_code           VARCHAR(100) NOT NULL,
    instance_name           VARCHAR(255),
    location                VARCHAR(255),
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by              VARCHAR(100),
    
    UNIQUE (project_id, instance_code)
);

CREATE INDEX idx_project_elements_project ON project_elements(project_id);
CREATE INDEX idx_project_elements_element ON project_elements(element_id);

-- ============================================================

CREATE TABLE project_element_values (
    value_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    project_element_id  INTEGER NOT NULL REFERENCES project_elements(project_element_id) ON DELETE CASCADE,
    variable_id         INTEGER NOT NULL REFERENCES element_variables(variable_id) ON DELETE RESTRICT,
    value               TEXT NOT NULL,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by          VARCHAR(100),
    
    UNIQUE (project_element_id, variable_id)
);

CREATE INDEX idx_project_element_values_element ON project_element_values(project_element_id);

-- ============================================================

CREATE TABLE rendered_descriptions (
    render_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    project_element_id  INTEGER NOT NULL UNIQUE REFERENCES project_elements(project_element_id) ON DELETE CASCADE,
    rendered_text       TEXT NOT NULL,
    is_stale            BOOLEAN DEFAULT 0,
    rendered_at         DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- PART 5: TRIGGERS
-- ============================================================

CREATE TRIGGER trg_mark_stale_on_value_change
AFTER INSERT ON project_element_values
BEGIN
    UPDATE rendered_descriptions
    SET is_stale = 1
    WHERE project_element_id = NEW.project_element_id;
END;

CREATE TRIGGER trg_mark_stale_on_value_update
AFTER UPDATE ON project_element_values
BEGIN
    UPDATE rendered_descriptions
    SET is_stale = 1
    WHERE project_element_id = NEW.project_element_id;
END;

CREATE TRIGGER trg_mark_stale_on_value_delete
AFTER DELETE ON project_element_values
BEGIN
    UPDATE rendered_descriptions
    SET is_stale = 1
    WHERE project_element_id = OLD.project_element_id;
END;

-- ============================================================
-- PART 6: VIEWS
-- ============================================================

CREATE VIEW v_active_descriptions AS
SELECT 
    e.element_id,
    e.element_code,
    e.element_name,
    dv.version_id,
    dv.description_template,
    dv.version_number,
    dv.updated_at AS active_since
FROM elements e
LEFT JOIN description_versions dv 
    ON e.element_id = dv.element_id AND dv.is_active = 1;

-- ============================================================

CREATE VIEW v_pending_proposals AS
SELECT 
    e.element_code,
    e.element_name,
    dv.version_id,
    dv.description_template,
    dv.state,
    dv.version_number,
    dv.created_by,
    dv.created_at
FROM description_versions dv
JOIN elements e ON dv.element_id = e.element_id
WHERE dv.state IN ('S0', 'S1', 'S2')
ORDER BY dv.element_id, dv.state DESC, dv.created_at;

-- ============================================================

CREATE VIEW v_project_elements_rendered AS
SELECT 
    p.project_code,
    p.project_name,
    e.element_code,
    pe.instance_code,
    pe.instance_name,
    pe.location,
    dv.description_template,
    dv.version_number AS locked_version,
    rd.rendered_text,
    rd.is_stale,
    rd.rendered_at
FROM project_elements pe
JOIN projects p ON pe.project_id = p.project_id
JOIN elements e ON pe.element_id = e.element_id
JOIN description_versions dv ON pe.description_version_id = dv.version_id
LEFT JOIN rendered_descriptions rd ON pe.project_element_id = rd.project_element_id;

-- ============================================================
-- NEW: VIEW TO SEE VARIABLES WITH THEIR OPTIONS (FOR UI FORMS)
-- ============================================================

CREATE VIEW v_element_variables_with_options AS
SELECT 
    e.element_code,
    e.element_name,
    ev.variable_id,
    ev.variable_name,
    ev.variable_type,
    ev.unit,
    ev.default_value,
    ev.is_required,
    ev.display_order,
    CASE 
        WHEN EXISTS (SELECT 1 FROM variable_options WHERE variable_id = ev.variable_id)
        THEN 'DROPDOWN'
        ELSE 'FREE_INPUT'
    END AS input_type,
    (SELECT COUNT(*) FROM variable_options WHERE variable_id = ev.variable_id) AS option_count
FROM elements e
JOIN element_variables ev ON e.element_id = ev.element_id
ORDER BY e.element_code, ev.display_order;

-- ============================================================
-- CONSTRUCTION CATEGORIES REFERENCE - 33 Official Categories
-- ============================================================

CREATE TABLE construction_categories (
    category_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name   VARCHAR(50) NOT NULL UNIQUE,
    display_order   INTEGER NOT NULL,
    logical_group   VARCHAR(50),
    description     TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert all 33 official categories
INSERT INTO construction_categories (category_name, display_order, logical_group, description) VALUES
('ASCENSOR', 1, 'EQUIPAMIENTO_ACABADOS', 'Sistemas de transporte vertical'),
('CARPINTERIA', 2, 'ENVOLVENTE', 'Elementos de carpintería general'),
('CARPINTERIA INDUSTRIAL', 3, 'ENVOLVENTE', 'Carpintería industrial específica'),
('CARTELERIA', 4, 'EQUIPAMIENTO_ACABADOS', 'Elementos de señalización y cartelería'),
('CIMENTACION', 5, 'CIVIL_CIMENTACION', 'Elementos de cimentación general'),
('CUBIERTAS Y FACHADAS', 6, 'ENVOLVENTE', 'Sistemas de cubierta y fachada'),
('ENCEPADOS', 7, 'CIVIL_CIMENTACION', 'Elementos de encepado'),
('EQUIPAMIENTOS', 8, 'EQUIPAMIENTO_ACABADOS', 'Equipamiento general del edificio'),
('ESTRUCTURA DE MADERA', 9, 'ESTRUCTURAS', 'Elementos estructurales de madera'),
('ESTRUCTURA METALICA', 10, 'ESTRUCTURAS', 'Elementos estructurales metálicos'),
('ESTRUCTURA PREFABRICADA', 11, 'ESTRUCTURAS', 'Elementos estructurales prefabricados'),
('FONTANERIA', 12, 'FONTANERIA_PCI', 'Instalaciones de fontanería y agua'),
('GEOTECNICO', 13, 'CIVIL_CIMENTACION', 'Trabajos geotécnicos'),
('GRUPO ELECTROGENO', 14, 'ELECTRICIDAD', 'Sistemas de generación eléctrica'),
('INAUFUGACION', 15, 'ENVOLVENTE', 'Sistemas de inauguración'),
('INSTALACION BT', 16, 'ELECTRICIDAD', 'Instalaciones de baja tensión'),
('INSTALACION DE CLIMA Y VENTILACION', 17, 'CLIMATIZACION', 'Sistemas de climatización y ventilación'),
('INSTALACION DE FRIO', 18, 'CLIMATIZACION', 'Sistemas de refrigeración'),
('INSTALACION DE PARARRAYOS', 19, 'ELECTRICIDAD', 'Sistemas de protección contra rayos'),
('INSTALACION PCI', 20, 'FONTANERIA_PCI', 'Protección contra incendios'),
('MOVIMIENTO DE TIERRAS', 21, 'CIVIL_CIMENTACION', 'Trabajos de movimiento de tierras'),
('MURO CORTINA', 22, 'ENVOLVENTE', 'Sistemas de muro cortina'),
('OBRA CIVIL', 23, 'CIVIL_CIMENTACION', 'Obras civiles generales'),
('PILOTATGE', 24, 'CIVIL_CIMENTACION', 'Sistemas de pilotaje'),
('SANEAMIENTO PLUVIALES CUBIERTA', 25, 'SANEAMIENTO', 'Saneamiento de aguas pluviales en cubierta'),
('SANEAMIENTO RESIDUALES', 26, 'SANEAMIENTO', 'Saneamiento de aguas residuales'),
('SANEAMIENTO URBANIZACION', 27, 'SANEAMIENTO', 'Saneamiento de urbanización'),
('SLOTDRAIN', 28, 'SANEAMIENTO', 'Sistemas de drenaje tipo slot'),
('SOLERAS', 29, 'ESTRUCTURAS', 'Elementos de solera'),
('SUMINISTRO DE CT Y CS', 30, 'ELECTRICIDAD', 'Suministros de centro de transformación y cuadros secundarios'),
('SUMINISTRO SEPARADORES DE HIDROCARBURO', 31, 'SANEAMIENTO', 'Separadores de hidrocarburos'),
('SUMINISTROS DE ILUMINACION', 32, 'ELECTRICIDAD', 'Sistemas de iluminación'),
('URBANIZACION EXTERIOR', 33, 'URBANIZACION', 'Elementos de urbanización exterior');

-- Create index on category name for lookups
CREATE INDEX idx_construction_categories_name ON construction_categories(category_name);

-- ============================================================
-- END OF SCHEMA
-- ============================================================