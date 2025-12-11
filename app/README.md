# Office Data Management Web Application

Flask-based web interface for managing CYPE office elements, projects, and variable descriptions.

## Features

- 📊 **Element Browser**: Browse 75+ CYPE construction elements
- 🏗️ **Project Management**: Create and manage construction projects
- 🔧 **Variable Editor**: Set element variables and generate descriptions
- 📝 **Template Rendering**: Real-time description generation from templates

## Quick Start

```bash
# From repository root
cd app/
python app.py
```

Access at: http://localhost:5001

## Architecture

```
app/
├── app.py              # Main Flask application
├── templates/          # HTML templates
│   ├── index.html      # Element browser
│   ├── projects.html   # Project listing
│   ├── element_detail.html
│   ├── project_detail.html
│   ├── edit_values.html
│   └── ...
└── README.md          # This file
```

## Database

Uses: `../office_variable_demo/office_data.db`
- **75 elements** from CYPE construction data
- **7,274+ variables** with options and constraints
- **Project system** for element instances

## Dependencies

- Flask (web framework)
- office_variable_demo.api.OfficeDBManager (database interface)

## URL Routes

- `/` - Element browser homepage
- `/element/<code>` - Element details and variables
- `/projects` - Project listing
- `/project/<id>` - Project details and elements
- `/create_project` - New project form
- `/edit_values/<id>` - Variable value editor
- `/api/render/<id>` - Description rendering API

## Development

The app runs on port 5001 to avoid conflicts with other services on the default Flask port 5000.

Database integration is handled through the OfficeDBManager which provides:
- Element and variable management
- Project and instance tracking
- Template rendering with variable substitution