# Development Workflow

## Quick Start

```bash
# Setup
git clone [repo]
cd Office-Data-Centralization
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test
cd poc
python poblar_datos.py
python exportar_excel.py --proyecto PROY_001
```

## Git Workflow

### Branch Strategy
- `main` - Production (protected)
- `feature/<name>` - New features
- `fix/<name>` - Bug fixes

### Process
```bash
# 1. Create feature branch
git checkout main
git pull origin main
git checkout -b feature/my-feature

# 2. Make changes and commit
git add .
git commit -m "feat: description"

# 3. Push and create PR
git push origin feature/my-feature
# Create PR on GitHub → Wait for review → Merge
```

### Commit Convention
```
type(scope): description

Types: feat, fix, docs, refactor, test, chore
Example: feat(export): add Presto export
```

## Code Organization

### Current Structure (POC)
- All code in `poc/` folder
- Scripts are standalone

### Moving to Production Structure

**When to migrate:**
- Code is reused in multiple scripts
- Need to add tests
- Multiple developers working

**How to migrate:**

1. **Extract to `src/`:**
   ```python
   # src/database.py
   def get_project_elements(project_code: str):
       # Reusable database functions
   
   # src/exporters.py
   def export_excel(project_code: str):
       # Reusable export functions
   ```

2. **Create CLI in `scripts/`:**
   ```python
   # scripts/export.py
   from src.exporters import export_excel
   import sys
   
   if __name__ == "__main__":
       export_excel(sys.argv[1])
   ```

3. **Add tests in `tests/`:**
   ```python
   # tests/test_exporters.py
   from src.exporters import export_excel
   
   def test_export_excel():
       assert export_excel("PROY_001") == True
   ```

## Code Conventions

### Python
- Follow PEP 8
- Use descriptive names
- Add docstrings to public functions

### SQL
- Keywords UPPERCASE
- Table names lowercase
- Clear indentation

## Common Issues

### Excel not generated
- Verify `elementos.db` exists
- Check write permissions
- Confirm project exists in DB

### Word doesn't update
- Press `Ctrl+A` then `F9` to update fields
- Verify LINK fields (not static text)
- Check Excel path in LINK field

### Database locked
- Close DB Browser for SQLite
- Use context managers: `with sqlite3.connect(...)`

---

**Last updated:** December 2024
