-- ============================================================
-- SIMPLIFIED PARAMETRIC ELEMENT DESCRIPTION SYSTEM
-- No ENUM variables, no variable_options table
-- ============================================================

-- ============================================================
-- PART 1: ELEMENT TEMPLATE DEFINITIONS (SIMPLIFIED)
-- ============================================================

CREATE TABLE elements (
    element_id      SERIAL PRIMARY KEY,
    element_code    VARCHAR(50) NOT NULL UNIQUE,
    element_name    VARCHAR(255) NOT NULL,
    description     TEXT,
    created_at      TIMESTAMP DEFAULT NOW(),
    created_by      VARCHAR(100)
);

-- ============================================================

CREATE TABLE element_variables (
    variable_id     SERIAL PRIMARY KEY,
    element_id      INT NOT NULL REFERENCES elements(element_id) ON DELETE CASCADE,
    variable_name   VARCHAR(100) NOT NULL,
    variable_type   VARCHAR(20) NOT NULL CHECK (variable_type IN ('TEXT', 'NUMERIC', 'DATE')),
    unit            VARCHAR(20),
    default_value   TEXT,
    is_required     BOOLEAN DEFAULT TRUE,
    display_order   INT DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW(),
    
    UNIQUE (element_id, variable_name)
);

COMMENT ON TABLE element_variables IS 'Variables that characterize each element type - all free-form input';
COMMENT ON COLUMN element_variables.variable_type IS 'TEXT=string, NUMERIC=number, DATE=date - all free-form, no dropdowns';

CREATE INDEX idx_element_variables_element ON element_variables(element_id);

-- NO variable_options table!

-- ============================================================
-- PART 2: DESCRIPTION VERSIONING (UNCHANGED)
-- ============================================================

CREATE TABLE description_versions (
    version_id          SERIAL PRIMARY KEY,
    element_id          INT NOT NULL REFERENCES elements(element_id) ON DELETE CASCADE,
    description_template TEXT NOT NULL,
    state               VARCHAR(2) NOT NULL DEFAULT 'S0' CHECK (state IN ('S0', 'S1', 'S2', 'S3', 'D')),
    is_active           BOOLEAN DEFAULT FALSE,
    version_number      INT NOT NULL,
    created_at          TIMESTAMP DEFAULT NOW(),
    created_by          VARCHAR(100),
    updated_at          TIMESTAMP DEFAULT NOW(),
    
    UNIQUE (element_id, version_number)
);

CREATE UNIQUE INDEX idx_one_active_per_element 
ON description_versions (element_id) 
WHERE is_active = TRUE;

ALTER TABLE description_versions 
ADD CONSTRAINT chk_active_must_be_s3 
CHECK (is_active = FALSE OR state = 'S3');

CREATE INDEX idx_description_versions_element_state ON description_versions(element_id, state);

-- ============================================================

CREATE TABLE approvals (
    approval_id     SERIAL PRIMARY KEY,
    version_id      INT NOT NULL REFERENCES description_versions(version_id) ON DELETE CASCADE,
    from_state      VARCHAR(2) NOT NULL,
    to_state        VARCHAR(2) NOT NULL,
    approved_by     VARCHAR(100) NOT NULL,
    approved_at     TIMESTAMP DEFAULT NOW(),
    comments        TEXT
);

CREATE INDEX idx_approvals_version ON approvals(version_id);

-- ============================================================
-- PART 3: PROJECTS (UNCHANGED)
-- ============================================================

CREATE TABLE projects (
    project_id      SERIAL PRIMARY KEY,
    project_code    VARCHAR(50) NOT NULL UNIQUE,
    project_name    VARCHAR(255) NOT NULL,
    status          VARCHAR(20) DEFAULT 'PLANNING' CHECK (status IN ('PLANNING', 'ACTIVE', 'COMPLETED', 'CANCELLED')),
    start_date      DATE,
    end_date        DATE,
    location        TEXT,
    created_at      TIMESTAMP DEFAULT NOW(),
    created_by      VARCHAR(100)
);

-- ============================================================
-- PART 4: PROJECT ELEMENT INSTANCES (UNCHANGED)
-- ============================================================

CREATE TABLE project_elements (
    project_element_id      SERIAL PRIMARY KEY,
    project_id              INT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    element_id              INT NOT NULL REFERENCES elements(element_id) ON DELETE RESTRICT,
    description_version_id  INT NOT NULL REFERENCES description_versions(version_id) ON DELETE RESTRICT,
    instance_code           VARCHAR(100) NOT NULL,
    instance_name           VARCHAR(255),
    location                VARCHAR(255),
    created_at              TIMESTAMP DEFAULT NOW(),
    created_by              VARCHAR(100),
    
    UNIQUE (project_id, instance_code)
);

CREATE INDEX idx_project_elements_project ON project_elements(project_id);
CREATE INDEX idx_project_elements_element ON project_elements(element_id);

-- ============================================================

CREATE TABLE project_element_values (
    value_id            SERIAL PRIMARY KEY,
    project_element_id  INT NOT NULL REFERENCES project_elements(project_element_id) ON DELETE CASCADE,
    variable_id         INT NOT NULL REFERENCES element_variables(variable_id) ON DELETE RESTRICT,
    value               TEXT NOT NULL,
    updated_at          TIMESTAMP DEFAULT NOW(),
    updated_by          VARCHAR(100),
    
    UNIQUE (project_element_id, variable_id)
);

COMMENT ON TABLE project_element_values IS 'Actual values - all stored as text, no validation against options';

CREATE INDEX idx_project_element_values_element ON project_element_values(project_element_id);

-- ============================================================

CREATE TABLE rendered_descriptions (
    render_id           SERIAL PRIMARY KEY,
    project_element_id  INT NOT NULL UNIQUE REFERENCES project_elements(project_element_id) ON DELETE CASCADE,
    rendered_text       TEXT NOT NULL,
    is_stale            BOOLEAN DEFAULT FALSE,
    rendered_at         TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- PART 5: HELPER FUNCTIONS (SLIGHTLY SIMPLIFIED)
-- ============================================================

CREATE OR REPLACE FUNCTION get_next_version_number(p_element_id INT)
RETURNS INT AS $$
BEGIN
    RETURN COALESCE(
        (SELECT MAX(version_number) + 1 
         FROM description_versions 
         WHERE element_id = p_element_id),
        1
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================

CREATE OR REPLACE FUNCTION extract_placeholders(p_template TEXT)
RETURNS TEXT[] AS $$
DECLARE
    v_placeholders TEXT[];
BEGIN
    SELECT ARRAY_AGG(DISTINCT matches[1])
    INTO v_placeholders
    FROM regexp_matches(p_template, '\{([a-zA-Z_][a-zA-Z0-9_]*)\}', 'g') AS matches;
    
    RETURN COALESCE(v_placeholders, ARRAY[]::TEXT[]);
END;
$$ LANGUAGE plpgsql;

-- ============================================================

CREATE OR REPLACE FUNCTION validate_template_placeholders(
    p_element_id INT,
    p_template TEXT
)
RETURNS TABLE (
    is_valid BOOLEAN,
    message TEXT,
    missing_variables TEXT[],
    undefined_placeholders TEXT[]
) AS $$
DECLARE
    v_placeholders TEXT[];
    v_element_variables TEXT[];
    v_missing TEXT[];
    v_undefined TEXT[];
BEGIN
    v_placeholders := extract_placeholders(p_template);
    
    SELECT ARRAY_AGG(variable_name) INTO v_element_variables
    FROM element_variables
    WHERE element_id = p_element_id;
    
    v_element_variables := COALESCE(v_element_variables, ARRAY[]::TEXT[]);
    
    -- Find undefined placeholders
    SELECT ARRAY_AGG(p)
    INTO v_undefined
    FROM unnest(v_placeholders) AS p
    WHERE p != ALL(v_element_variables);
    
    -- Find missing required variables
    SELECT ARRAY_AGG(variable_name)
    INTO v_missing
    FROM element_variables
    WHERE element_id = p_element_id
      AND is_required = TRUE
      AND variable_name != ALL(v_placeholders);
    
    v_missing := COALESCE(v_missing, ARRAY[]::TEXT[]);
    v_undefined := COALESCE(v_undefined, ARRAY[]::TEXT[]);
    
    IF array_length(v_undefined, 1) > 0 THEN
        RETURN QUERY SELECT FALSE, 'Template contains undefined placeholders'::TEXT, v_missing, v_undefined;
    ELSIF array_length(v_missing, 1) > 0 THEN
        RETURN QUERY SELECT FALSE, 'Template missing required variables'::TEXT, v_missing, v_undefined;
    ELSE
        RETURN QUERY SELECT TRUE, 'Valid'::TEXT, v_missing, v_undefined;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- PART 6: VERSIONING WORKFLOW FUNCTIONS (UNCHANGED)
-- ============================================================

CREATE OR REPLACE FUNCTION create_proposal(
    p_element_id            INT,
    p_description_template  TEXT,
    p_created_by            VARCHAR(100)
)
RETURNS INT AS $$
DECLARE
    v_version_id INT;
    v_version_number INT;
    v_validation RECORD;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM elements WHERE element_id = p_element_id) THEN
        RAISE EXCEPTION 'Element % does not exist', p_element_id;
    END IF;
    
    SELECT * INTO v_validation
    FROM validate_template_placeholders(p_element_id, p_description_template);
    
    IF NOT v_validation.is_valid THEN
        RAISE EXCEPTION 'Invalid template: %. Missing: %, Undefined: %', 
            v_validation.message,
            array_to_string(v_validation.missing_variables, ', '),
            array_to_string(v_validation.undefined_placeholders, ', ');
    END IF;
    
    v_version_number := get_next_version_number(p_element_id);
    
    INSERT INTO description_versions (
        element_id, description_template, state, is_active, version_number, created_by
    ) VALUES (
        p_element_id, p_description_template, 'S0', FALSE, v_version_number, p_created_by
    ) RETURNING version_id INTO v_version_id;
    
    RETURN v_version_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================

CREATE OR REPLACE FUNCTION approve_proposal(
    p_version_id    INT,
    p_approved_by   VARCHAR(100),
    p_comments      TEXT DEFAULT NULL
)
RETURNS TABLE (
    success         BOOLEAN,
    message         TEXT,
    new_state       VARCHAR(2)
) AS $$
DECLARE
    v_current_state VARCHAR(2);
    v_next_state    VARCHAR(2);
    v_element_id    INT;
    v_old_active_id INT;
BEGIN
    SELECT state, element_id INTO v_current_state, v_element_id
    FROM description_versions
    WHERE version_id = p_version_id;
    
    IF v_current_state IS NULL THEN
        RETURN QUERY SELECT FALSE, 'Version not found'::TEXT, NULL::VARCHAR(2);
        RETURN;
    END IF;
    
    v_next_state := CASE v_current_state
        WHEN 'S0' THEN 'S1'
        WHEN 'S1' THEN 'S2'
        WHEN 'S2' THEN 'S3'
        ELSE NULL
    END;
    
    IF v_next_state IS NULL THEN
        RETURN QUERY SELECT FALSE, 
            ('Cannot approve from state ' || v_current_state)::TEXT, 
            NULL::VARCHAR(2);
        RETURN;
    END IF;
    
    IF v_next_state = 'S3' THEN
        SELECT version_id INTO v_old_active_id
        FROM description_versions
        WHERE element_id = v_element_id AND is_active = TRUE;
        
        IF v_old_active_id IS NOT NULL THEN
            UPDATE description_versions
            SET is_active = FALSE, updated_at = NOW()
            WHERE version_id = v_old_active_id;
        END IF;
        
        UPDATE description_versions
        SET state = 'S3', is_active = TRUE, updated_at = NOW()
        WHERE version_id = p_version_id;
    ELSE
        UPDATE description_versions
        SET state = v_next_state, updated_at = NOW()
        WHERE version_id = p_version_id;
    END IF;
    
    INSERT INTO approvals (version_id, from_state, to_state, approved_by, comments)
    VALUES (p_version_id, v_current_state, v_next_state, p_approved_by, p_comments);
    
    RETURN QUERY SELECT TRUE, 'Approved'::TEXT, v_next_state;
END;
$$ LANGUAGE plpgsql;

-- ============================================================

CREATE OR REPLACE FUNCTION reject_proposal(
    p_version_id    INT,
    p_rejected_by   VARCHAR(100),
    p_reason        TEXT
)
RETURNS BOOLEAN AS $$
DECLARE
    v_current_state VARCHAR(2);
BEGIN
    SELECT state INTO v_current_state
    FROM description_versions
    WHERE version_id = p_version_id;
    
    IF v_current_state IS NULL THEN
        RAISE EXCEPTION 'Version % not found', p_version_id;
    END IF;
    
    IF v_current_state IN ('S3', 'D') THEN
        RAISE EXCEPTION 'Cannot reject version in state %', v_current_state;
    END IF;
    
    UPDATE description_versions
    SET state = 'D', updated_at = NOW()
    WHERE version_id = p_version_id;
    
    INSERT INTO approvals (version_id, from_state, to_state, approved_by, comments)
    VALUES (p_version_id, v_current_state, 'D', p_rejected_by, p_reason);
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- PART 7: RENDERING FUNCTIONS (UNCHANGED)
-- ============================================================

CREATE OR REPLACE FUNCTION render_description(p_project_element_id INT)
RETURNS TEXT AS $$
DECLARE
    v_template TEXT;
    v_rendered TEXT;
    v_value RECORD;
BEGIN
    SELECT dv.description_template INTO v_template
    FROM project_elements pe
    JOIN description_versions dv ON pe.description_version_id = dv.version_id
    WHERE pe.project_element_id = p_project_element_id;
    
    IF v_template IS NULL THEN
        RAISE EXCEPTION 'Project element % not found', p_project_element_id;
    END IF;
    
    v_rendered := v_template;
    
    FOR v_value IN
        SELECT ev.variable_name, pev.value
        FROM project_element_values pev
        JOIN element_variables ev ON pev.variable_id = ev.variable_id
        WHERE pev.project_element_id = p_project_element_id
    LOOP
        v_rendered := regexp_replace(
            v_rendered, 
            '\{' || v_value.variable_name || '\}', 
            v_value.value, 
            'g'
        );
    END LOOP;
    
    RETURN v_rendered;
END;
$$ LANGUAGE plpgsql;

-- ============================================================

CREATE OR REPLACE FUNCTION upsert_rendered_description(p_project_element_id INT)
RETURNS VOID AS $$
DECLARE
    v_rendered TEXT;
BEGIN
    v_rendered := render_description(p_project_element_id);
    
    INSERT INTO rendered_descriptions (project_element_id, rendered_text, is_stale, rendered_at)
    VALUES (p_project_element_id, v_rendered, FALSE, NOW())
    ON CONFLICT (project_element_id) 
    DO UPDATE SET 
        rendered_text = EXCLUDED.rendered_text,
        is_stale = FALSE,
        rendered_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- PART 8: TRIGGERS (UNCHANGED)
-- ============================================================

CREATE OR REPLACE FUNCTION mark_description_stale()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE rendered_descriptions
    SET is_stale = TRUE
    WHERE project_element_id = COALESCE(NEW.project_element_id, OLD.project_element_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_mark_stale_on_value_change
AFTER INSERT OR UPDATE OR DELETE ON project_element_values
FOR EACH ROW
EXECUTE FUNCTION mark_description_stale();

-- ============================================================
-- PART 9: VIEWS (SIMPLIFIED)
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
    ON e.element_id = dv.element_id AND dv.is_active = TRUE;

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

-- Simplified view - no options array
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
-- END OF SIMPLIFIED SCHEMA
-- ============================================================
