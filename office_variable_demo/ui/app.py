#!/usr/bin/env python3
"""
Simple Flask Web UI for Office Variable System
Uses the real office_data.db with 75 existing elements
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.office_db_manager import OfficeDBManager

app = Flask(__name__)
db_manager = OfficeDBManager()

@app.route('/')
def index():
    """Home page showing available elements"""
    elements = db_manager.get_all_elements()
    return render_template('index.html', elements=elements)

@app.route('/element/<element_code>')
def element_detail(element_code):
    """Show element details and variables"""
    element = db_manager.get_element_by_code(element_code)
    if not element:
        return "Element not found", 404
    
    variables = db_manager.get_element_variables(element.element_id)
    template = db_manager.get_active_template(element.element_id)
    
    return render_template('element_detail.html', 
                         element=element, 
                         variables=variables, 
                         template=template)

@app.route('/projects')
def projects():
    """Show all projects"""
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
        projects = cursor.fetchall()
    return render_template('projects.html', projects=projects)

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    """Show project elements and their rendered descriptions"""
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,))
        project = cursor.fetchone()
    
    if not project:
        return "Project not found", 404
    
    project_elements = db_manager.get_project_elements(project_id)
    
    return render_template('project_detail.html', 
                         project=project, 
                         project_elements=project_elements)

@app.route('/create_project', methods=['GET', 'POST'])
def create_project():
    """Create a new project"""
    if request.method == 'POST':
        project_code = request.form['project_code']
        project_name = request.form['project_name']
        location = request.form.get('location', '')
        
        project_id = db_manager.create_project(project_code, project_name, location)
        return redirect(url_for('project_detail', project_id=project_id))
    
    return render_template('create_project.html')

@app.route('/add_element_to_project/<int:project_id>', methods=['GET', 'POST'])
def add_element_to_project(project_id):
    """Add element to project"""
    if request.method == 'POST':
        element_code = request.form['element_code']
        instance_code = request.form['instance_code']
        instance_name = request.form.get('instance_name', '')
        
        pe_id = db_manager.add_project_element(project_id, element_code, instance_code, instance_name)
        return redirect(url_for('edit_element_values', project_element_id=pe_id))
    
    elements = db_manager.get_all_elements()
    return render_template('add_element.html', project_id=project_id, elements=elements)

@app.route('/edit_values/<int:project_element_id>', methods=['GET', 'POST'])
def edit_element_values(project_element_id):
    """Edit variable values for project element"""
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        # Get project element info
        cursor.execute("""
            SELECT pe.*, e.element_code, e.element_name, p.project_id
            FROM project_elements pe
            JOIN elements e ON pe.element_id = e.element_id
            JOIN projects p ON pe.project_id = p.project_id
            WHERE pe.project_element_id = ?
        """, (project_element_id,))
        pe_info = cursor.fetchone()
    
    if not pe_info:
        return "Project element not found", 404
    
    # Get variables and current values
    variables = db_manager.get_element_variables(pe_info[2])  # element_id
    
    # Get current values
    current_values = {}
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ev.variable_name, pev.value
            FROM project_element_values pev
            JOIN element_variables ev ON pev.variable_id = ev.variable_id
            WHERE pev.project_element_id = ?
        """, (project_element_id,))
        current_values = dict(cursor.fetchall())
    
    if request.method == 'POST':
        # Update values
        for var in variables:
            value = request.form.get(f'var_{var.variable_name}', '')
            if value:
                db_manager.set_project_element_value(project_element_id, var.variable_name, value)
        
        return redirect(url_for('project_detail', project_id=pe_info[-1]))
    
    # Get rendered description
    rendered = db_manager.render_description(project_element_id)
    
    return render_template('edit_values.html', 
                         pe_info=pe_info, 
                         variables=variables,
                         current_values=current_values,
                         rendered=rendered)

@app.route('/api/render/<int:project_element_id>')
def api_render(project_element_id):
    """API endpoint to render description"""
    try:
        rendered = db_manager.render_description(project_element_id)
        return jsonify({'success': True, 'rendered': rendered})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Use a non-default port (5001) to avoid conflicts with other services on 5000
    app.run(debug=True, host='0.0.0.0', port=5001)