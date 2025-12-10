-- ============================================================
-- SISTEMA AVANZADO DE GESTIÓN PARAMÉTRICA (SQLite)
-- ============================================================

CREATE TABLE elements (
    element_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    element_code    VARCHAR(50) NOT NULL UNIQUE,
    element_name    VARCHAR(255) NOT NULL,
    category        VARCHAR(50) NOT NULL DEFAULT 'GENERAL', -- Columna per separar Excel per pestanyes
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by      VARCHAR(100)
);

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

CREATE TABLE description_versions (
    version_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    element_id          INTEGER NOT NULL REFERENCES elements(element_id) ON DELETE CASCADE,
    description_template TEXT NOT NULL,
    state                VARCHAR(2) NOT NULL DEFAULT 'S0' CHECK (state IN ('S0', 'S1', 'S2', 'S3', 'D')),
    is_active            BOOLEAN DEFAULT 0,
    version_number       INTEGER NOT NULL,
    created_at           DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by           VARCHAR(100),
    updated_at           DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (element_id, version_number),
    CHECK (is_active = 0 OR state = 'S3')
);

CREATE TABLE approvals (
    approval_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id      INTEGER NOT NULL REFERENCES description_versions(version_id) ON DELETE CASCADE,
    from_state      VARCHAR(2) NOT NULL,
    to_state        VARCHAR(2) NOT NULL,
    approved_by     VARCHAR(100) NOT NULL,
    approver_role   VARCHAR(20) NOT NULL,  -- Rol de l'usuari que vota: 'admin', 'editor'
    approved_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    comments        TEXT
);

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

CREATE TABLE variable_options (
    option_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_id     INTEGER NOT NULL REFERENCES element_variables(variable_id) ON DELETE CASCADE,
    option_value    TEXT NOT NULL,
    display_order   INTEGER DEFAULT 0,
    UNIQUE (variable_id, option_value)
);

CREATE TABLE projects (
    project_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    project_code    VARCHAR(50) NOT NULL UNIQUE,
    project_name    VARCHAR(255) NOT NULL,
    status          VARCHAR(20) DEFAULT 'PLANNING',
    start_date      DATE,
    end_date        DATE,
    location        TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by      VARCHAR(100)
);

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

CREATE TABLE project_element_values (
    value_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    project_element_id  INTEGER NOT NULL REFERENCES project_elements(project_element_id) ON DELETE CASCADE,
    variable_id         INTEGER NOT NULL REFERENCES element_variables(variable_id) ON DELETE RESTRICT,
    value               TEXT NOT NULL,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by          VARCHAR(100),
    UNIQUE (project_element_id, variable_id)
);

CREATE TABLE rendered_descriptions (
    render_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    project_element_id  INTEGER NOT NULL UNIQUE REFERENCES project_elements(project_element_id) ON DELETE CASCADE,
    rendered_text       TEXT NOT NULL,
    is_stale            BOOLEAN DEFAULT 0,
    rendered_at         DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- TAULA D'USUARIS I SEGURETAT
CREATE TABLE users (
    user_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username        VARCHAR(50) NOT NULL UNIQUE, -- El nom per fer login (ex: 'admin')
    password_hash   TEXT NOT NULL,               -- La contrasenya encriptada
    full_name       VARCHAR(100),                -- Nom real per mostrar (ex: 'Enginyer En Cap')
    role            VARCHAR(20) DEFAULT 'editor' CHECK (role IN ('admin', 'editor', 'viewer')),
    is_active       BOOLEAN DEFAULT 1,           -- Per desactivar usuaris sense esborrar-los
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login      DATETIME                     -- Últim accés al sistema
);

-- TRIGGERS
CREATE TRIGGER trg_mark_stale_on_value_change AFTER INSERT ON project_element_values
BEGIN
    UPDATE rendered_descriptions SET is_stale = 1 WHERE project_element_id = NEW.project_element_id;
END;

CREATE TRIGGER trg_mark_stale_on_value_update AFTER UPDATE ON project_element_values
BEGIN
    UPDATE rendered_descriptions SET is_stale = 1 WHERE project_element_id = NEW.project_element_id;
END;

-- VISTA PRINCIPAL
CREATE VIEW v_project_elements_rendered AS
SELECT 
    p.project_code,
    p.project_name,
    e.element_code,
    pe.instance_code,
    pe.instance_name,
    pe.location,
    dv.description_template,
    rd.rendered_text,
    rd.is_stale
FROM project_elements pe
JOIN projects p ON pe.project_id = p.project_id
JOIN elements e ON pe.element_id = e.element_id
JOIN description_versions dv ON pe.description_version_id = dv.version_id
LEFT JOIN rendered_descriptions rd ON pe.project_element_id = rd.project_element_id;