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
-- PART 5: VIEWS
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
-- View for project elements with their templates (rendering happens in application layer)
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
    dv.version_number AS locked_version
FROM project_elements pe
JOIN projects p ON pe.project_id = p.project_id
JOIN elements e ON pe.element_id = e.element_id
JOIN description_versions dv ON pe.description_version_id = dv.version_id;

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
-- END OF SCHEMA
-- ============================================================