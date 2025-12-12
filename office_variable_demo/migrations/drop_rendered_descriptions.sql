-- ============================================================
-- Migration: Remove rendered_descriptions table and related objects
-- Reason: Rendering should happen in the application layer, not the database
-- Date: 2025-12-03
-- ============================================================

-- Drop view that depends on rendered_descriptions
DROP VIEW IF EXISTS v_project_elements_rendered;

-- Drop triggers that maintain the is_stale flag
DROP TRIGGER IF EXISTS trg_mark_stale_on_value_change;
DROP TRIGGER IF EXISTS trg_mark_stale_on_value_update;
DROP TRIGGER IF EXISTS trg_mark_stale_on_value_delete;

-- Drop the table itself
DROP TABLE IF EXISTS rendered_descriptions;

-- Recreate the view without rendered_descriptions (optional - shows project elements with template)
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
-- Migration Complete
-- ============================================================

