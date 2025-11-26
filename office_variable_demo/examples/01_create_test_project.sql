-- ============================================================
-- EXAMPLE 1: Create a Test Project with Existing Elements
-- ============================================================

-- First, let's see what elements we have
SELECT element_code, element_name, price 
FROM elements 
LIMIT 5;

-- Create a test project
INSERT INTO projects (
    project_code, 
    project_name, 
    status, 
    location, 
    created_by
) VALUES (
    'DEMO-001', 
    'Barcelona Office Building Demo', 
    'PLANNING', 
    'Barcelona, Spain',
    'demo_user'
);

-- Get the project_id we just created
SELECT project_id, project_code, project_name FROM projects WHERE project_code = 'DEMO-001';

-- Let's use some of the existing elements in our project
-- We'll pick a concrete wall element
SELECT 
    e.element_id,
    e.element_code, 
    e.element_name,
    dv.version_id,
    dv.description_template
FROM elements e
JOIN description_versions dv ON e.element_id = dv.element_id 
WHERE e.element_code LIKE 'EHM%' 
AND dv.is_active = 1
LIMIT 3;