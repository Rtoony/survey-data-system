# SQLAlchemy Core Migration Guide

**Phase 9: Data Confidence Build**

## Executive Summary

This document outlines the comprehensive migration strategy for converting the legacy raw SQL/psycopg2 data layer to a modern, secure, and maintainable **SQLAlchemy Core** architecture. This migration eliminates SQL injection vulnerabilities, improves code maintainability, and establishes a foundation for future "Specialized Tools" development.

**Status:** Framework Complete - Ready for Implementation
**Priority:** High (Security & Reliability)
**Estimated Effort:** 3-4 weeks (phased rollout)

---

## Table of Contents

1. [Why SQLAlchemy Core?](#why-sqlalchemy-core)
2. [Architecture Overview](#architecture-overview)
3. [Migration Framework](#migration-framework)
4. [Step-by-Step Migration Process](#step-by-step-migration-process)
5. [Pattern Library](#pattern-library)
6. [Security Improvements](#security-improvements)
7. [Testing Strategy](#testing-strategy)
8. [Rollout Plan](#rollout-plan)
9. [Troubleshooting](#troubleshooting)

---

## Why SQLAlchemy Core?

### Problems with Current Raw SQL Approach

1. **SQL Injection Risk**: Direct string concatenation creates vulnerabilities
2. **No Type Safety**: No compile-time or IDE validation of queries
3. **Poor Maintainability**: Schema changes require manual updates across dozens of files
4. **Connection Management**: Manual connection pooling is error-prone
5. **Testing Difficulty**: Hard to mock or test database interactions

### Benefits of SQLAlchemy Core

1. **Automatic SQL Injection Protection**: Parameterized queries by default
2. **Type-Safe Query Building**: Catch errors at development time
3. **Schema Reflection**: Table definitions act as living documentation
4. **Connection Pooling**: Battle-tested, production-ready pooling
5. **Database Portability**: Easy to switch databases (PostgreSQL → MySQL, etc.)
6. **Performance**: Core is lightweight (not ORM overhead)

### Why Core and Not ORM?

- **Performance**: No session overhead, no lazy loading penalties
- **Flexibility**: Full SQL control when needed
- **Simplicity**: No complex object-relational mapping
- **Bulk Operations**: Optimized for large data imports (DXF files)

---

## Architecture Overview

### New Layer Structure

```
┌─────────────────────────────────────────────────────┐
│                  Flask Routes                       │
│                    (app.py)                         │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              Business Logic Layer                   │
│        (Future: app/services/*.py)                  │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│          SQLAlchemy Core Data Layer                 │
│   ┌──────────────────┬──────────────────────┐      │
│   │  app/db_session  │   app/data_models    │      │
│   │  (Connections)   │   (Table Schemas)    │      │
│   └──────────────────┴──────────────────────┘      │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│            PostgreSQL Database                      │
│         (PostGIS, pgvector, extensions)            │
└─────────────────────────────────────────────────────┘
```

### File Responsibilities

| File | Purpose |
|------|---------|
| `app/db_session.py` | Connection pooling, context managers, Flask integration |
| `app/data_models.py` | SQLAlchemy Table definitions (10 sample tables provided) |
| `app/config.py` | Database URI and pool configuration |
| `database.py` | **Legacy** - Will be deprecated after migration |

---

## Migration Framework

### Phase 1: Infrastructure Setup ✅ COMPLETE

- [x] Created `app/db_session.py` with connection pooling
- [x] Created `app/data_models.py` with 10 representative tables
- [x] Updated `app/config.py` with SQLAlchemy settings
- [x] Generated this migration guide

### Phase 2: Expand Table Definitions (Next Step)

**Goal**: Complete the `app/data_models.py` file with ALL 73 tables.

**Process**:
1. Extract table definitions from `database/schema/complete_schema.sql`
2. Convert SQL DDL to SQLAlchemy `Table` objects
3. Map PostgreSQL types to SQLAlchemy types:
   - `uuid` → `UUID`
   - `text` → `Text`
   - `varchar(N)` → `String(N)`
   - `geometry(PointZ, SRID)` → `Geometry('POINTZ', srid=SRID)`
   - `jsonb` → `Text` (with comment indicating JSONB)
   - `tsvector` → `Text` (with comment indicating tsvector)
   - `timestamp` → `DateTime`
   - `numeric(P,S)` → `Numeric(P, S)`
   - `boolean` → `Boolean`
   - `integer` → `Integer`
   - `text[]` → `ARRAY(Text)`

**Example Conversion**:

```sql
-- SQL DDL (from complete_schema.sql)
CREATE TABLE public.layers (
    layer_id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    project_id uuid REFERENCES projects(project_id) ON DELETE CASCADE,
    layer_name varchar(255) NOT NULL,
    layer_color varchar(50),
    is_frozen boolean DEFAULT false,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP
);
```

```python
# SQLAlchemy Core Table (add to app/data_models.py)
layers = Table(
    'layers',
    metadata,
    Column('layer_id', UUID, primary_key=True, server_default=UUID_DEFAULT,
           comment='Unique identifier for the layer'),
    Column('project_id', UUID, ForeignKey('projects.project_id', ondelete='CASCADE'),
           nullable=True, comment='Project this layer belongs to'),
    Column('layer_name', String(255), nullable=False,
           comment='Name of the layer'),
    Column('layer_color', String(50), nullable=True,
           comment='Display color for the layer'),
    Column('is_frozen', Boolean, nullable=False, server_default=text('false'),
           comment='Flag indicating if layer is frozen'),
    Column('created_at', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT,
           comment='Timestamp when record was created'),

    Index('idx_layers_project', 'project_id'),
    Index('idx_layers_name', 'layer_name'),

    comment='CAD layer definitions'
)
```

**Tables Remaining** (63 tables to convert):
- alignment_pis
- annotation_standards
- block_inserts
- block_standards
- category_standards
- classification_confidence
- code_standards
- color_standards
- control_point_membership
- coordinate_systems
- cross_section_points
- cross_sections
- detail_standards
- dimension_styles
- drawing_dimensions
- earthwork_balance
- earthwork_quantities
- ... (see `database/schema/complete_schema.sql` for full list)

### Phase 3: Migrate Routes One-by-One

**Goal**: Convert each route in `app.py` from raw SQL to SQLAlchemy Core.

**Strategy**: Migrate by **functional area** (not alphabetically):

1. **Health/Status Routes** (Low Risk, High Visibility)
   - `/api/db/health` ✅ Already migrated in `db_session.py`
   - `/api/system/status`

2. **Project Management Routes** (Core Functionality)
   - `GET /api/projects` - List all projects
   - `POST /api/projects` - Create new project
   - `GET /api/projects/<id>` - Get project details
   - `PUT /api/projects/<id>` - Update project
   - `DELETE /api/projects/<id>` - Delete project

3. **Survey Points Routes**
   - `GET /api/survey-points`
   - `POST /api/survey-points`
   - `PUT /api/survey-points/<id>`
   - `DELETE /api/survey-points/<id>`

4. **Standards & Vocabularies** (Recently extracted, lower complexity)
   - Standards blueprint routes
   - Vocabulary blueprint routes

5. **Complex/High-Risk Routes** (Last)
   - DXF import/export (already async via Celery)
   - Relationship graph queries
   - AI/NL query system

### Phase 4: Service Layer Extraction (Future)

Once routes are migrated to SQLAlchemy Core, extract business logic into services:

```
app/services/
├── project_service.py
├── survey_point_service.py
├── easement_service.py
└── ... (one service per entity type)
```

---

## Step-by-Step Migration Process

### For Each Route Migration

#### Step 1: Identify the Raw SQL Query

**Example from `app.py:606-617`**:

```python
@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT project_id, project_name, project_number,
                           client_name, description, created_at, updated_at
                    FROM projects
                    ORDER BY created_at DESC
                    """
                )
                projects = cur.fetchall()
        return jsonify([dict(p) for p in projects])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

#### Step 2: Convert to SQLAlchemy Core

```python
from app.db_session import get_db_connection
from app.data_models import projects

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    try:
        with get_db_connection() as conn:
            # Build query using SQLAlchemy Core
            stmt = (
                projects.select()
                .with_only_columns([
                    projects.c.project_id,
                    projects.c.project_name,
                    projects.c.project_number,
                    projects.c.client_name,
                    projects.c.description,
                    projects.c.created_at,
                    projects.c.updated_at,
                ])
                .order_by(projects.c.created_at.desc())
            )

            result = conn.execute(stmt)
            rows = result.fetchall()

        # Convert to list of dicts (SQLAlchemy Row objects are dict-like)
        return jsonify([dict(row._mapping) for row in rows])

    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**Key Changes**:
- ✅ Import `get_db_connection` from `app.db_session`
- ✅ Import `projects` table from `app.data_models`
- ✅ Replace raw SQL string with `.select()` query builder
- ✅ Use `projects.c.column_name` for column references
- ✅ Use `row._mapping` to convert Row to dict

#### Step 3: Test the Migrated Route

```bash
# Manual test
curl http://localhost:5000/api/projects

# Automated test (create tests/test_projects_migration.py)
pytest tests/test_projects_migration.py -v
```

#### Step 4: Update Documentation

Add comment to route:

```python
@app.route('/api/projects', methods=['GET'])
def get_projects():
    """
    Get all projects
    MIGRATION: Converted to SQLAlchemy Core (Phase 9)
    """
```

#### Step 5: Mark Legacy Code for Removal

If the route was the only user of a legacy helper function, mark it:

```python
# DEPRECATED: Remove after all routes migrated to SQLAlchemy Core
@contextmanager
def get_db():
    """Legacy database connection - use app.db_session.get_db_connection() instead"""
    ...
```

---

## Pattern Library

### Pattern 1: Simple SELECT

**Before (Raw SQL)**:
```python
cur.execute("SELECT * FROM projects WHERE project_id = %s", (project_id,))
project = cur.fetchone()
```

**After (SQLAlchemy Core)**:
```python
from app.data_models import projects

stmt = projects.select().where(projects.c.project_id == project_id)
result = conn.execute(stmt)
project = result.fetchone()
```

### Pattern 2: INSERT with RETURNING

**Before (Raw SQL)**:
```python
cur.execute(
    """
    INSERT INTO projects (project_name, project_number, client_name)
    VALUES (%s, %s, %s)
    RETURNING project_id
    """,
    (name, number, client)
)
project_id = cur.fetchone()['project_id']
```

**After (SQLAlchemy Core)**:
```python
from app.data_models import projects

stmt = (
    projects.insert()
    .values(
        project_name=name,
        project_number=number,
        client_name=client
    )
    .returning(projects.c.project_id)
)
result = conn.execute(stmt)
project_id = result.fetchone()[0]
```

### Pattern 3: UPDATE

**Before (Raw SQL)**:
```python
cur.execute(
    """
    UPDATE projects
    SET project_name = %s, updated_at = CURRENT_TIMESTAMP
    WHERE project_id = %s
    """,
    (new_name, project_id)
)
```

**After (SQLAlchemy Core)**:
```python
from sqlalchemy import text
from app.data_models import projects

stmt = (
    projects.update()
    .where(projects.c.project_id == project_id)
    .values(
        project_name=new_name,
        updated_at=text('CURRENT_TIMESTAMP')
    )
)
conn.execute(stmt)
```

### Pattern 4: DELETE

**Before (Raw SQL)**:
```python
cur.execute("DELETE FROM projects WHERE project_id = %s", (project_id,))
```

**After (SQLAlchemy Core)**:
```python
from app.data_models import projects

stmt = projects.delete().where(projects.c.project_id == project_id)
conn.execute(stmt)
```

### Pattern 5: JOIN Queries

**Before (Raw SQL)**:
```python
cur.execute(
    """
    SELECT p.project_name, sp.point_number, sp.elevation
    FROM projects p
    JOIN survey_points sp ON p.project_id = sp.project_id
    WHERE p.project_id = %s
    """,
    (project_id,)
)
```

**After (SQLAlchemy Core)**:
```python
from sqlalchemy import select
from app.data_models import projects, survey_points

stmt = (
    select([
        projects.c.project_name,
        survey_points.c.point_number,
        survey_points.c.elevation
    ])
    .select_from(
        projects.join(
            survey_points,
            projects.c.project_id == survey_points.c.project_id
        )
    )
    .where(projects.c.project_id == project_id)
)
result = conn.execute(stmt)
rows = result.fetchall()
```

### Pattern 6: Complex WHERE Clauses

**Before (Raw SQL)**:
```python
cur.execute(
    """
    SELECT * FROM survey_points
    WHERE project_id = %s
      AND point_type IN %s
      AND elevation > %s
      AND is_active = true
    ORDER BY point_number
    """,
    (project_id, tuple(point_types), min_elevation)
)
```

**After (SQLAlchemy Core)**:
```python
from app.data_models import survey_points

stmt = (
    survey_points.select()
    .where(
        survey_points.c.project_id == project_id,
        survey_points.c.point_type.in_(point_types),
        survey_points.c.elevation > min_elevation,
        survey_points.c.is_active == True
    )
    .order_by(survey_points.c.point_number)
)
result = conn.execute(stmt)
rows = result.fetchall()
```

### Pattern 7: Aggregate Queries

**Before (Raw SQL)**:
```python
cur.execute(
    """
    SELECT project_id, COUNT(*) as point_count, AVG(elevation) as avg_elevation
    FROM survey_points
    WHERE is_active = true
    GROUP BY project_id
    HAVING COUNT(*) > 10
    """
)
```

**After (SQLAlchemy Core)**:
```python
from sqlalchemy import func, select
from app.data_models import survey_points

stmt = (
    select([
        survey_points.c.project_id,
        func.count().label('point_count'),
        func.avg(survey_points.c.elevation).label('avg_elevation')
    ])
    .where(survey_points.c.is_active == True)
    .group_by(survey_points.c.project_id)
    .having(func.count() > 10)
)
result = conn.execute(stmt)
rows = result.fetchall()
```

### Pattern 8: Spatial Queries (PostGIS)

**Before (Raw SQL)**:
```python
cur.execute(
    """
    SELECT point_id, point_number,
           ST_AsGeoJSON(geometry) as geojson
    FROM survey_points
    WHERE ST_DWithin(
        geometry,
        ST_SetSRID(ST_MakePoint(%s, %s, %s), 2226),
        %s
    )
    """,
    (x, y, z, radius)
)
```

**After (SQLAlchemy Core)**:
```python
from sqlalchemy import func
from app.data_models import survey_points

# Build reference point
ref_point = func.ST_SetSRID(
    func.ST_MakePoint(x, y, z),
    2226
)

stmt = (
    survey_points.select()
    .with_only_columns([
        survey_points.c.point_id,
        survey_points.c.point_number,
        func.ST_AsGeoJSON(survey_points.c.geometry).label('geojson')
    ])
    .where(
        func.ST_DWithin(survey_points.c.geometry, ref_point, radius)
    )
)
result = conn.execute(stmt)
rows = result.fetchall()
```

### Pattern 9: Bulk INSERT

**Before (Raw SQL)**:
```python
data = [
    {'point_number': 'P1', 'elevation': 100.5},
    {'point_number': 'P2', 'elevation': 101.2},
    # ... thousands more
]

execute_batch(cur,
    """
    INSERT INTO survey_points (project_id, point_number, elevation)
    VALUES (%s, %s, %s)
    """,
    [(project_id, d['point_number'], d['elevation']) for d in data]
)
```

**After (SQLAlchemy Core)**:
```python
from app.data_models import survey_points

# Prepare data
insert_data = [
    {
        'project_id': project_id,
        'point_number': d['point_number'],
        'elevation': d['elevation']
    }
    for d in data
]

# Bulk insert (much faster than individual inserts)
conn.execute(survey_points.insert(), insert_data)
```

### Pattern 10: Transaction Management

**Before (Raw SQL)**:
```python
with get_db() as conn:
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO projects ...")
            cur.execute("INSERT INTO survey_points ...")
            conn.commit()
    except:
        conn.rollback()
        raise
```

**After (SQLAlchemy Core)**:
```python
# Transactions are automatic with get_db_connection()
with get_db_connection() as conn:
    # All operations are in a transaction
    conn.execute(projects.insert().values(...))
    conn.execute(survey_points.insert().values(...))
    # Auto-commits on successful context exit
    # Auto-rolls back on exception
```

---

## Security Improvements

### SQL Injection Prevention

**VULNERABLE (Raw SQL)**:
```python
# DANGER: Never do this!
query = f"SELECT * FROM projects WHERE project_name = '{user_input}'"
cur.execute(query)
```

**Attack Vector**:
```python
user_input = "'; DROP TABLE projects; --"
# Resulting query:
# SELECT * FROM projects WHERE project_name = ''; DROP TABLE projects; --'
```

**SECURE (Parameterized Raw SQL)**:
```python
# Better, but still manual
cur.execute(
    "SELECT * FROM projects WHERE project_name = %s",
    (user_input,)  # Parameters are escaped
)
```

**SECURE (SQLAlchemy Core - Automatic)**:
```python
# SQL injection impossible - parameters are ALWAYS escaped
stmt = projects.select().where(projects.c.project_name == user_input)
conn.execute(stmt)
```

### Identified Vulnerabilities in Current Code

Review these locations during migration:

1. **app.py:3819** - Raw SQL in category management
2. **app.py:3857** - Raw SQL in category delete
3. **app.py:3898** - Raw SQL in discipline queries
4. **app.py:3957** - Raw SQL in discipline updates

All use parameterized queries (%s placeholders), so no **immediate** risk, but SQLAlchemy Core provides defense-in-depth.

---

## Testing Strategy

### Unit Tests

Create `tests/test_data_layer_migration.py`:

```python
"""
Unit tests for SQLAlchemy Core data layer migration
"""
import pytest
from app.db_session import get_db_connection
from app.data_models import projects, survey_points

def test_select_projects():
    """Test SELECT query on projects table"""
    with get_db_connection() as conn:
        stmt = projects.select().limit(10)
        result = conn.execute(stmt)
        rows = result.fetchall()

        assert len(rows) <= 10
        for row in rows:
            assert 'project_id' in row._mapping
            assert 'project_name' in row._mapping

def test_insert_project():
    """Test INSERT with RETURNING"""
    with get_db_connection() as conn:
        stmt = (
            projects.insert()
            .values(
                project_name='Test Project',
                project_number='TEST-001'
            )
            .returning(projects.c.project_id)
        )
        result = conn.execute(stmt)
        project_id = result.fetchone()[0]

        assert project_id is not None

def test_update_project():
    """Test UPDATE operation"""
    # Create test project first
    # ... (setup code)

    with get_db_connection() as conn:
        stmt = (
            projects.update()
            .where(projects.c.project_id == test_project_id)
            .values(project_name='Updated Name')
        )
        conn.execute(stmt)

        # Verify update
        verify_stmt = (
            projects.select()
            .where(projects.c.project_id == test_project_id)
        )
        result = conn.execute(verify_stmt)
        row = result.fetchone()
        assert row.project_name == 'Updated Name'

def test_delete_project():
    """Test DELETE operation"""
    # Create test project first
    # ... (setup code)

    with get_db_connection() as conn:
        stmt = projects.delete().where(projects.c.project_id == test_project_id)
        conn.execute(stmt)

        # Verify deletion
        verify_stmt = (
            projects.select()
            .where(projects.c.project_id == test_project_id)
        )
        result = conn.execute(verify_stmt)
        row = result.fetchone()
        assert row is None
```

### Integration Tests

Compare old vs new implementations:

```python
def test_get_projects_route_parity():
    """Ensure new SQLAlchemy implementation returns same data as legacy"""

    # Call legacy route (if still exists)
    legacy_response = client.get('/api/projects/legacy')
    legacy_data = legacy_response.get_json()

    # Call new route
    new_response = client.get('/api/projects')
    new_data = new_response.get_json()

    # Compare
    assert len(legacy_data) == len(new_data)
    # ... more assertions
```

### Performance Tests

```python
import time

def test_bulk_insert_performance():
    """Ensure SQLAlchemy Core bulk insert is fast"""

    data = [{'point_number': f'P{i}', 'elevation': i} for i in range(10000)]

    start = time.time()
    with get_db_connection() as conn:
        conn.execute(survey_points.insert(), data)
    duration = time.time() - start

    # Should complete in under 2 seconds
    assert duration < 2.0
```

---

## Rollout Plan

### Week 1: Foundation

- [ ] Add remaining 63 tables to `app/data_models.py`
- [ ] Write unit tests for all table definitions
- [ ] Create migration tracking checklist (spreadsheet or GitHub issues)
- [ ] Set up monitoring for database connection pool

### Week 2: Core Routes

- [ ] Migrate health/status endpoints
- [ ] Migrate project CRUD routes
- [ ] Migrate survey point CRUD routes
- [ ] Create integration tests comparing old vs new

### Week 3: Standards & Vocabularies

- [ ] Migrate standards blueprint
- [ ] Migrate vocabulary blueprint
- [ ] Migrate attribute codes routes

### Week 4: Complex Routes & Cleanup

- [ ] Migrate remaining routes
- [ ] Remove `database.py` legacy code
- [ ] Update all documentation
- [ ] Celebrate! 🎉

### Post-Migration

- [ ] Extract business logic into service layer
- [ ] Implement database caching layer
- [ ] Add query performance monitoring
- [ ] Consider Alembic for schema migrations

---

## Troubleshooting

### Issue: "Table not found in metadata"

**Symptom**:
```python
KeyError: 'some_table_name'
```

**Cause**: Table not yet defined in `app/data_models.py`

**Solution**: Add the table definition following the patterns in this guide.

---

### Issue: "Cannot convert Row to dict"

**Symptom**:
```python
TypeError: 'Row' object is not subscriptable
```

**Cause**: SQLAlchemy 2.0 changed Row behavior

**Solution**: Use `row._mapping` to get dict-like access:
```python
# Old (1.x)
row['column_name']

# New (2.0)
row._mapping['column_name']
# or
dict(row._mapping)
```

---

### Issue: "Connection pool exhausted"

**Symptom**:
```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 20 reached
```

**Cause**: Not properly closing connections (missing context manager)

**Solution**: Always use `with get_db_connection()`:
```python
# WRONG
conn = get_db_connection()
result = conn.execute(...)

# RIGHT
with get_db_connection() as conn:
    result = conn.execute(...)
```

---

### Issue: "Geometry type not recognized"

**Symptom**:
```
sqlalchemy.exc.ArgumentError: Could not locate column in row for column 'geometry'
```

**Cause**: Missing `geoalchemy2` import or incorrect geometry type

**Solution**:
```python
# Ensure geoalchemy2 is installed
pip install geoalchemy2

# Import Geometry type
from geoalchemy2 import Geometry

# Use correct geometry type
Column('geometry', Geometry('POINTZ', srid=2226))
```

---

### Issue: "JSONB type not working"

**Symptom**:
```python
TypeError: Object of type 'dict' is not JSON serializable
```

**Cause**: Using `Text` type instead of proper JSONB handling

**Solution**: For now, manually serialize/deserialize JSON:
```python
import json

# INSERT
conn.execute(
    projects.insert().values(
        attributes=json.dumps({'key': 'value'})
    )
)

# SELECT
result = conn.execute(projects.select())
row = result.fetchone()
attributes = json.loads(row.attributes) if row.attributes else {}
```

**Future**: Add proper JSONB type to data models:
```python
from sqlalchemy.dialects.postgresql import JSONB

Column('attributes', JSONB, nullable=True)
```

---

### Issue: "Performance regression on complex queries"

**Symptom**: Queries slower after migration

**Cause**: Missing indexes or inefficient query construction

**Solution**:
1. Check execution plan:
   ```python
   from sqlalchemy import text

   with get_db_connection() as conn:
       result = conn.execute(text("EXPLAIN ANALYZE " + str(stmt)))
       print(result.fetchall())
   ```

2. Add missing indexes to `app/data_models.py`

3. Consider using `.subquery()` for complex queries

---

## Appendix A: Full Table Conversion Checklist

Use this checklist to track progress when converting all 73 tables:

### Core Entity Tables (10/73) ✅

- [x] projects
- [x] survey_points
- [x] easements
- [x] block_definitions
- [x] attribute_codes
- [x] entity_relationships
- [x] horizontal_alignments
- [x] drawing_hatches
- [x] audit_log
- [x] ai_query_cache

### Remaining Tables (63/73)

- [ ] abbreviation_standards
- [ ] alignment_pis
- [ ] annotation_standards
- [ ] block_inserts
- [ ] block_standards
- [ ] category_standards
- [ ] classification_confidence
- [ ] code_standards
- [ ] color_standards
- [ ] control_point_membership
- [ ] coordinate_systems
- [ ] cross_section_points
- [ ] cross_sections
- [ ] detail_standards
- [ ] dimension_styles
- [ ] drawing_dimensions
- [ ] earthwork_balance
- [ ] earthwork_quantities
- [ ] entity_registry
- [ ] graphrag_chunks
- [ ] graphrag_embeddings
- [ ] graphrag_entities
- [ ] graphrag_relationships
- [ ] hatch_patterns
- [ ] import_queue
- [ ] layers
- [ ] line_styles
- [ ] material_standards
- [ ] municipality_owners
- [ ] parcels
- [ ] pipe_networks
- [ ] pipes
- [ ] profile_views
- [ ] profiles
- [ ] relationship_edges
- [ ] relationship_set_naming_templates
- [ ] relationship_sets
- [ ] section_views
- [ ] service_connections
- [ ] standard_categories
- [ ] standard_category_applications
- [ ] standard_disciplines
- [ ] standard_discipline_applications
- [ ] standard_notes
- [ ] status_standards
- [ ] stormwater_bmps
- [ ] structure_foundations
- [ ] structure_type_standards
- [ ] structures
- [ ] survey_point_description_standards
- [ ] text_styles
- [ ] users
- [ ] utility_lines
- [ ] utility_poles
- [ ] utility_structures
- [ ] utility_system_standards
- [ ] vertical_alignments
- [ ] vertical_curves
- [ ] viewports
- [ ] watersheds
- [ ] workflow_tasks

---

## Appendix B: Environment Variables

Add these to your `.env` file:

```bash
# SQLAlchemy Database Configuration
# Option 1: Direct URI
SQLALCHEMY_DATABASE_URI=postgresql://user:password@host:port/database?sslmode=require

# Option 2: Individual components (fallback)
PGHOST=your-database-host.com
PGPORT=5432
PGDATABASE=postgres
PGUSER=your-username
PGPASSWORD=your-password
DB_SSLMODE=require

# Connection Pool Configuration
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Debug Mode (set to 'true' to log all SQL queries)
SQLALCHEMY_ECHO=false
```

---

## Appendix C: Required Dependencies

Add to `requirements.txt`:

```txt
# SQLAlchemy Core
sqlalchemy>=2.0.0,<3.0.0
geoalchemy2>=0.14.0  # For PostGIS geometry types
psycopg2-binary>=2.9.0  # PostgreSQL driver

# Optional: For Alembic migrations (future)
# alembic>=1.13.0
```

Install:
```bash
pip install -r requirements.txt
```

---

## Appendix D: Quick Reference

### Common Imports

```python
# Connection management
from app.db_session import get_db_connection, get_flask_db_connection

# Table definitions
from app.data_models import (
    projects, survey_points, easements, block_definitions,
    attribute_codes, entity_relationships
)

# Query builders
from sqlalchemy import select, insert, update, delete, func, text

# Types (for type hints)
from sqlalchemy import Connection, Row
```

### Common Query Patterns

```python
# SELECT all
stmt = projects.select()

# SELECT specific columns
stmt = projects.select().with_only_columns([projects.c.project_id, projects.c.project_name])

# SELECT with WHERE
stmt = projects.select().where(projects.c.project_id == project_id)

# SELECT with multiple WHERE
stmt = projects.select().where(
    projects.c.is_active == True,
    projects.c.created_at > start_date
)

# SELECT with ORDER BY
stmt = projects.select().order_by(projects.c.created_at.desc())

# SELECT with LIMIT
stmt = projects.select().limit(100)

# INSERT
stmt = projects.insert().values(project_name='New Project')

# INSERT with RETURNING
stmt = projects.insert().values(project_name='New').returning(projects.c.project_id)

# UPDATE
stmt = projects.update().where(projects.c.project_id == pid).values(project_name='Updated')

# DELETE
stmt = projects.delete().where(projects.c.project_id == pid)

# COUNT
stmt = select([func.count()]).select_from(projects)

# JOIN
stmt = select([projects, survey_points]).select_from(
    projects.join(survey_points, projects.c.project_id == survey_points.c.project_id)
)
```

---

## Conclusion

This migration represents a critical investment in the **long-term reliability, security, and maintainability** of the Survey Data System. By converting from raw SQL to SQLAlchemy Core, we eliminate entire classes of bugs and security vulnerabilities while establishing a solid foundation for future "Specialized Tools" development.

**Next Steps**:
1. Complete table definitions in `app/data_models.py`
2. Begin migrating high-value, low-risk routes
3. Build comprehensive test coverage
4. Roll out incrementally with feature flags

**Questions or Issues?**
- Review the Pattern Library for common conversions
- Check the Troubleshooting section for known issues
- Consult SQLAlchemy Core documentation: https://docs.sqlalchemy.org/en/20/core/

---

**Document Version**: 1.0
**Last Updated**: Phase 9 Kickoff
**Author**: Claude (The Builder)
**Status**: Ready for Implementation
