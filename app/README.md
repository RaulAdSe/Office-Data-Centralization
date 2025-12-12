# Gestor de Partides - Streamlit Application

Streamlit-based web interface for managing CYPE construction elements, projects, and variable descriptions with user authentication.

## Features

- **User Authentication**: Login with "Remember Me" cookie support (7 days)
- **Role-based Access**: viewer, editor, admin roles stored in database
- **Element Catalog Management**: Browse, create, and edit construction elements
- **Variable Management**: Define variables with types (TEXT, NUMERIC, LIST with options)
- **Version Control**: Draft versions with 3-vote approval workflow
- **Project Management**: Create projects and add element instances
- **Bulk Creation**: Add multiple element instances at once

## Quick Start

```bash
cd app/
pip install -r requirements.txt
streamlit run app_gestio.py
```

Access at: http://localhost:8501

## Architecture

```
app/
├── app_gestio.py       # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Database

Uses: `../data/office_data.db`
- **Elements** with variables and description templates
- **Projects** with element instances
- **Users** with hashed passwords and roles
- **Approvals** for version voting system

## Dependencies

- streamlit
- streamlit-authenticator
- pandas
- sqlite3 (built-in)
- bcrypt

## Main Sections

### Catalog Management
- **Edit Existing**: Browse elements, manage variables, create drafts
- **Create Element**: Wizard to define new elements with variables

### Project Management
- **Create Projects**: Define new construction projects
- **Add Elements**: Assign element instances to projects
- **Edit Values**: Set variable values for each instance

## Authentication

Users are stored in the `users` table with bcrypt-hashed passwords. The `streamlit-authenticator` library handles:
- Login form
- Cookie-based session persistence
- Logout functionality
