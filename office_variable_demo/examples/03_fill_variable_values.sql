-- ============================================================
-- EXAMPLE 3: Fill Variable Values for Project Elements
-- ============================================================

-- Fill values for WALL-001 (project_element_id = 1)
-- For EHM010: codigo and variable

INSERT INTO project_element_values (
    project_element_id, 
    variable_id, 
    value,
    updated_by
) VALUES 
    (1, 1, 'IIa', 'demo_user'),           -- codigo = IIa (concrete grade)
    (1, 2, 'liso', 'demo_user');         -- variable = liso (smooth finish)

-- Fill values for FORM-001 (project_element_id = 2)
-- First, let's see what variables it has
SELECT 
    ev.variable_id,
    ev.variable_name,
    ev.variable_type
FROM element_variables ev
WHERE ev.element_id = 3;  -- EHM011 element

-- Insert value for formwork
INSERT INTO project_element_values (
    project_element_id, 
    variable_id, 
    value,
    updated_by
) VALUES 
    (2, 3, 'rugoso', 'demo_user');       -- variable = rugoso (rough finish)

-- Now let's see what we have
SELECT 
    pe.instance_code,
    e.element_name,
    ev.variable_name,
    pev.value
FROM project_element_values pev
JOIN project_elements pe ON pev.project_element_id = pe.project_element_id
JOIN elements e ON pe.element_id = e.element_id
JOIN element_variables ev ON pev.variable_id = ev.variable_id
WHERE pe.project_id = 1
ORDER BY pe.instance_code;