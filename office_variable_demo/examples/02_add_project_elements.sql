-- ============================================================
-- EXAMPLE 2: Add Project Elements and Fill Variables
-- ============================================================

-- Let's see what variables exist for our concrete wall element
SELECT 
    e.element_code,
    ev.variable_name, 
    ev.variable_type, 
    ev.unit,
    ev.is_required,
    ev.variable_id
FROM elements e
JOIN element_variables ev ON e.element_id = ev.element_id
WHERE e.element_code = 'EHM010_PROD_1764161964'
ORDER BY ev.display_order;

-- Add a concrete wall instance to our project
INSERT INTO project_elements (
    project_id, 
    element_id, 
    description_version_id,
    instance_code, 
    instance_name,
    location,
    created_by
) VALUES (
    1,  -- DEMO-001 project
    2,  -- EHM010 (concrete wall)
    2,  -- version_id for this element
    'WALL-001',
    'Exterior Wall - North Face',
    'Ground Floor',
    'demo_user'
);

-- Add another element - the formwork system
INSERT INTO project_elements (
    project_id, 
    element_id, 
    description_version_id,
    instance_code, 
    instance_name,
    location,
    created_by
) VALUES (
    1,  -- DEMO-001 project  
    3,  -- EHM011 (formwork system)
    3,  -- version_id for this element
    'FORM-001',
    'Formwork for Exterior Wall',
    'Ground Floor',
    'demo_user'
);

-- Check what we created
SELECT 
    pe.project_element_id,
    pe.instance_code,
    pe.instance_name,
    e.element_code,
    e.element_name
FROM project_elements pe
JOIN elements e ON pe.element_id = e.element_id
WHERE pe.project_id = 1;