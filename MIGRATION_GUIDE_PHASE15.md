# Phase 15: Database Layer Migration Guide

## Overview
This guide documents the migration from legacy `database.py` to the new SQLAlchemy Core framework in `app/db_session.py`.

## Migration Pattern

### Pattern 1: Import Replacements

**OLD:**
```python
from database import execute_query, get_db, DB_CONFIG
```

**NEW:**
```python
from sqlalchemy import text
from app.db_session import get_db_connection
```

### Pattern 2: Simple SELECT Queries

**OLD:**
```python
result = execute_query("SELECT * FROM projects WHERE project_id = %s", (project_id,))
if result:
    project = dict(result[0])
```

**NEW:**
```python
with get_db_connection() as conn:
    result = conn.execute(text("SELECT * FROM projects WHERE project_id = :id"), {"id": project_id})
    row = result.fetchone()
    project = dict(row._mapping) if row else None
```

### Pattern 3: SELECT with Multiple Rows

**OLD:**
```python
results = execute_query("SELECT * FROM projects ORDER BY project_name")
projects = [dict(row) for row in results] if results else []
```

**NEW:**
```python
with get_db_connection() as conn:
    result = conn.execute(text("SELECT * FROM projects ORDER BY project_name"))
    projects = [dict(row._mapping) for row in result]
```

### Pattern 4: INSERT/UPDATE/DELETE with RETURNING

**OLD:**
```python
result = execute_query("""
    INSERT INTO projects (project_name) VALUES (%s)
    RETURNING project_id, project_name
""", (name,))
return dict(result[0]) if result else None
```

**NEW:**
```python
with get_db_connection() as conn:
    result = conn.execute(text("""
        INSERT INTO projects (project_name) VALUES (:name)
        RETURNING project_id, project_name
    """), {"name": name})
    row = result.fetchone()
    return dict(row._mapping) if row else None
```

### Pattern 5: get_db() Context Manager

**OLD:**
```python
with get_db() as conn:
    with conn.cursor() as cur:
        cur.execute("UPDATE projects SET project_name = %s WHERE project_id = %s", (name, id))
```

**NEW:**
```python
with get_db_connection() as conn:
    conn.execute(text("UPDATE projects SET project_name = :name WHERE project_id = :id"),
                {"name": name, "id": id})
```

### Pattern 6: DB_CONFIG Usage

**OLD:**
```python
from database import DB_CONFIG
service = SomeService(DB_CONFIG)
```

**NEW:**
```python
# Option 1: Remove DB_CONFIG dependency entirely and use get_db_connection() within the service
# Option 2: For services that need connection info, pass the SQLAlchemy engine or connection
from app.db_session import get_engine
engine = get_engine()
```

## Key Differences

1. **Parameter Placeholders**: Change from `%s` to `:named_param`
2. **Parameters**: Change from tuple `(param1, param2)` to dict `{"key1": param1, "key2": param2}`
3. **Wrap SQL**: Wrap SQL strings with `text()` function
4. **Row Access**: Use `row._mapping` instead of direct dict conversion
5. **Context Manager**: Use `get_db_connection()` instead of `get_db()`
6. **No Cursor**: SQLAlchemy Core doesn't use cursors - execute directly on connection

## Files to Refactor

### Completed:
- ✅ `services/auth_service.py`
- ✅ `app/__init__.py`

### In Progress:
- 🔄 `services/rbac_service.py`

### Pending:
- services/relationship_validation_service.py
- services/relationship_graph_service.py
- services/semantic_search_service.py
- services/validation_helper.py
- services/graph_analytics_service.py
- services/graphrag_service.py
- services/project_mapping_service.py
- app.py (LARGE - ~5000 lines with ~100+ database calls)
- app/blueprints/classification.py
- app/blueprints/survey_codes.py
- app/blueprints/specialized_tools.py
- app/blueprints/pipe_networks.py
- app/blueprints/details_management.py
- app/blueprints/blocks_management.py
- app/blueprints/projects.py
- app/blueprints/gis_engine.py
- app/blueprints/standards.py
- app/tasks.py
- api/quality_routes.py
- db.py
- scripts/run_migration_041.py
- scripts/z_stress_harness.py
- tools/backfill_entity_layers.py

## Semi-Automated Refactoring Script

See `refactor_database_layer_complete.py` for a Python script that can assist with the bulk refactoring.

## Testing After Migration

1. **Run the application:**
   ```bash
   python run.py
   ```

2. **Test basic operations:**
   - List projects
   - Create a project
   - View project details
   - Run database queries

3. **Check for errors:**
   - Watch console for any `AttributeError` or `NameError` related to `database`
   - Check for SQL execution errors

## Common Pitfalls

1. **Forgetting to wrap SQL with text()**
   - Error: `AttributeError: 'str' object has no attribute 'compile'`
   - Fix: Wrap SQL string with `text(...)`

2. **Using tuple instead of dict for parameters**
   - Error: `Invalid parameter type`
   - Fix: Convert `(param1, param2)` to `{"param1": value1, "param2": value2}`

3. **Accessing row directly as dict**
   - Error: `TypeError: 'Row' object does not support item assignment`
   - Fix: Use `dict(row._mapping)` or `row._mapping['column']`

4. **Missing import for text**
   - Error: `NameError: name 'text' is not defined`
   - Fix: Add `from sqlalchemy import text`

5. **Not using named parameters**
   - Error: `This text() construct doesn't define a bound parameter named 'param0'`
   - Fix: Replace `%s` with `:param_name` and provide dict with matching keys

## Final Steps

After all files are refactored:

1. **Delete database.py:**
   ```bash
   rm database.py
   ```

2. **Remove from version control:**
   ```bash
   git rm database.py
   ```

3. **Verify no references remain:**
   ```bash
   grep -r "from database import" --include="*.py" .
   grep -r "import database" --include="*.py" .
   ```

4. **Run full test suite:**
   ```bash
   pytest
   ```

5. **Update documentation:**
   - Update README.md
   - Update DEVELOPER_GUIDE.md
   - Update any tutorials or examples
