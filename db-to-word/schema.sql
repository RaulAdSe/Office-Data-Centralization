-- ============================================================
-- SIMPLIFIED PARAMETRIC ELEMENT DESCRIPTION SYSTEM (SQLite)
-- No ENUM variables, no variable_options table
-- ============================================================

-- ============================================================
-- PART 1: ELEMENT TEMPLATE DEFINITIONS (SIMPLIFIED)
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

-- NO variable_options table!

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

-- SQLite doesn't support partial unique indexes with WHERE clause in older versions
-- We'll enforce the "one active per element" constraint in application logic
-- A trigger could also be used, but application-level check is simpler

CREATE INDEX idx_description_versions_element_state ON description_versions(element_id, state);

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
-- NEW: EXPLICIT PLACEHOLDER-TO-VARIABLE MAPPINGS
-- ============================================================

CREATE TABLE template_variable_mappings (
    mapping_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id      INTEGER NOT NULL REFERENCES description_versions(version_id) ON DELETE CASCADE,
    variable_id     INTEGER NOT NULL REFERENCES element_variables(variable_id) ON DELETE CASCADE,
    placeholder     VARCHAR(100) NOT NULL,  -- The {placeholder} name in template
    position        INTEGER NOT NULL,       -- Order of appearance in template (1, 2, 3...)
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (version_id, placeholder),
    UNIQUE (version_id, position)
);

CREATE INDEX idx_template_mappings_version ON template_variable_mappings(version_id);
CREATE INDEX idx_template_mappings_variable ON template_variable_mappings(variable_id);

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

-- Trigger to mark descriptions as stale when values change
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

CREATE VIEW v_element_variables_simple AS
SELECT 
    e.element_code,
    e.element_name,
    ev.variable_id,
    ev.variable_name,
    ev.variable_type,
    ev.unit,
    ev.default_value,
    ev.is_required,
    ev.display_order
FROM elements e
JOIN element_variables ev ON e.element_id = ev.element_id
ORDER BY e.element_code, ev.display_order;

-- ============================================================
-- NEW: VIEW TO SEE TEMPLATE MAPPINGS
-- ============================================================

CREATE VIEW v_template_variable_mappings AS
SELECT 
    e.element_code,
    dv.version_id,
    dv.version_number,
    dv.description_template,
    dv.state,
    tvm.placeholder,
    tvm.position,
    ev.variable_name,
    ev.variable_type,
    ev.unit
FROM template_variable_mappings tvm
JOIN description_versions dv ON tvm.version_id = dv.version_id
JOIN elements e ON dv.element_id = e.element_id
JOIN element_variables ev ON tvm.variable_id = ev.variable_id
ORDER BY dv.version_id, tvm.position;

-- ============================================================
-- END OF SIMPLIFIED SCHEMA
-- ============================================================
