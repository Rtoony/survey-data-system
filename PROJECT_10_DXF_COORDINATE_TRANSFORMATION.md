# Project 10: DXF Import Coordinate System Integration

## Executive Summary
Fix critical coordinate system bug in DXF import pipeline where imported geometries are stored with incorrect SRID (always 0/LOCAL) instead of using the project's configured coordinate reference system. This creates data integrity issues where coordinates from different CRS get mixed incorrectly, potentially causing positional errors of miles/kilometers.

**Dependency**: Must complete **Project 3, Phase 2** first (coordinate_systems FK constraints)

## Problem Statement

### Current Broken Behavior
1. **DXF Import API Ignores Coordinate System**: The `/api/dxf/import` endpoint does not fetch or pass the project's coordinate system to the importer
2. **Importer Always Defaults to SRID 0**: `DXFImporter.import_dxf()` defaults to `coordinate_system='LOCAL'` (SRID 0) when parameter is not provided
3. **Project CRS Configuration Unused**: Projects have `default_coordinate_system_id` field that is configured by users but completely ignored during import
4. **Data Integrity Failure**: Geometries from different coordinate systems get mixed in the same project with wrong SRID tags

### Real-World Impact
- **Survey Data**: Importing State Plane survey data into WGS84 project → coordinates off by thousands of feet
- **GIS Integration**: External GIS data imports with wrong projection → cannot overlay with other data sources
- **Export Round-Trip**: Export → Import cycle loses coordinate system information
- **Liability Risk**: Survey-grade applications require sub-inch accuracy; wrong CRS creates legal liability

### Evidence of the Bug

**File: `app.py` line 12173**
```python
stats = importer.import_dxf(
    temp_path,
    project_id,
    import_modelspace=import_modelspace
)
# BUG: coordinate_system parameter not passed!
```

**File: `dxf_importer.py` line 40**
```python
def import_dxf(self, file_path: str, project_id: str,
               coordinate_system: str = 'LOCAL',  # Always defaults to LOCAL
               import_modelspace: bool = True,
               external_conn=None) -> Dict:
```

**Database Query Showing Impact**
```sql
-- All imported entities have SRID 0, regardless of project CRS
SELECT 
    p.project_name,
    cs.system_name as project_crs,
    cs.epsg_code as project_epsg,
    COUNT(*) as entity_count,
    ST_SRID(de.geometry) as actual_srid
FROM drawing_entities de
JOIN projects p ON de.project_id = p.project_id
LEFT JOIN coordinate_systems cs ON p.default_coordinate_system_id = cs.system_id
GROUP BY p.project_name, cs.system_name, cs.epsg_code, ST_SRID(de.geometry);

-- Expected: actual_srid matches project_epsg (2226, 4326, etc)
-- Actual: actual_srid is always 0 (LOCAL)
```

## Goals & Objectives

### Primary Goals
1. **Connect Coordinate System Infrastructure**: Wire up existing `coordinate_systems` table and service to DXF import
2. **Correct SRID Tagging**: Ensure imported geometries are tagged with project's EPSG code
3. **Minimal Invasive Fix**: Use existing infrastructure, no new tables or major refactoring
4. **Preserve Existing Functionality**: Zero breaking changes to current import workflow

### Success Metrics
- DXF imports use project's `default_coordinate_system_id` from database
- Imported entities stored with correct SRID (2226, 4326, etc. - not 0)
- Round-trip coordinate validation passes
- No breaking changes to existing import API
- Performance impact < 10ms per import (single DB lookup)

### Explicit Non-Goals (Future Enhancements)
- ❌ Coordinate transformation (converting coordinates between CRS)
- ❌ Auto-detecting DXF source coordinate system
- ❌ Supporting multiple coordinate systems per project
- ❌ Batch re-projecting existing entities

## Implementation Plan

### Phase 1: API Endpoint Fix (Week 1, Day 1-2)

**File: `app.py`**

#### Current Code (Lines 12136-12216)
```python
@app.route('/api/dxf/import', methods=['POST'])
def import_dxf():
    """Import DXF file into database - with optional pattern-based classification"""
    try:
        # ... file validation ...
        
        project_id = request.form.get('project_id')
        if not project_id:
            return jsonify({'error': 'project_id is required'}), 400

        import_modelspace = request.form.get('import_modelspace', 'true') == 'true'
        pattern_id = request.form.get('pattern_id')

        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join('/tmp', f'{uuid.uuid4()}_{filename}')
        file.save(temp_path)

        try:
            # BUG: No coordinate system lookup here!
            importer = DXFImporter(DB_CONFIG, create_intelligent_objects=use_intelligent)
            stats = importer.import_dxf(
                temp_path,
                project_id,
                import_modelspace=import_modelspace  # Missing coordinate_system!
            )
```

#### Fixed Code
```python
@app.route('/api/dxf/import', methods=['POST'])
def import_dxf():
    """Import DXF file into database - with optional pattern-based classification"""
    try:
        # ... file validation ...
        
        project_id = request.form.get('project_id')
        if not project_id:
            return jsonify({'error': 'project_id is required'}), 400

        import_modelspace = request.form.get('import_modelspace', 'true') == 'true'
        pattern_id = request.form.get('pattern_id')

        # PHASE 1 FIX: Fetch project's coordinate system
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT cs.epsg_code, cs.system_name
                    FROM projects p
                    LEFT JOIN coordinate_systems cs 
                        ON p.default_coordinate_system_id = cs.system_id
                    WHERE p.project_id = %s
                """, (project_id,))
                result = cur.fetchone()
                
                # Map EPSG code to DXFImporter coordinate_system parameter
                coordinate_system = 'LOCAL'  # default fallback
                if result and result[0]:
                    epsg_code = result[0]
                    # Map common California State Plane zones
                    epsg_to_system = {
                        'EPSG:2226': 'STATE_PLANE',  # CA Zone 2 (NAD83, US Survey Feet)
                        'EPSG:2227': 'STATE_PLANE',  # CA Zone 3
                        'EPSG:2228': 'STATE_PLANE',  # CA Zone 4
                        'EPSG:2229': 'STATE_PLANE',  # CA Zone 5
                        'EPSG:2230': 'STATE_PLANE',  # CA Zone 6
                        'EPSG:4326': 'WGS84',        # WGS84 Geographic
                        'EPSG:3857': 'WEB_MERCATOR'  # Web Mercator (future)
                    }
                    coordinate_system = epsg_to_system.get(epsg_code, 'LOCAL')

        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join('/tmp', f'{uuid.uuid4()}_{filename}')
        file.save(temp_path)

        try:
            importer = DXFImporter(DB_CONFIG, create_intelligent_objects=use_intelligent)
            stats = importer.import_dxf(
                temp_path,
                project_id,
                coordinate_system=coordinate_system,  # FIXED: Pass coordinate system
                import_modelspace=import_modelspace
            )
```

**Changes Summary:**
- Add database query to fetch project's coordinate system (1 query, indexed lookup)
- Create EPSG → coordinate_system mapping dictionary
- Pass `coordinate_system` parameter to `import_dxf()`
- Graceful fallback to 'LOCAL' if project has no CRS configured

### Phase 2: Update DXFImporter SRID Mapping (Week 1, Day 2)

**File: `dxf_importer.py`**

#### Current SRID Mapping (Lines 57-62)
```python
# Map coordinate system to SRID
srid_map = {
    'LOCAL': 0,  # Local CAD coordinates (no projection)
    'STATE_PLANE': 2226,  # CA State Plane Zone 2, US Survey Feet (NAD83)
    'WGS84': 4326  # WGS84 geographic coordinates
}
self.srid = srid_map.get(coordinate_system.upper(), 0)
```

#### Enhanced SRID Mapping
```python
# Map coordinate system to SRID
# NOTE: STATE_PLANE defaults to Zone 2 (2226) for backward compatibility
# For specific zones, pass EPSG code directly in future enhancement
srid_map = {
    'LOCAL': 0,           # Local CAD coordinates (no projection)
    'STATE_PLANE': 2226,  # CA State Plane Zone 2, US Survey Feet (NAD83) - DEFAULT
    'WGS84': 4326,        # WGS84 geographic coordinates
    'WEB_MERCATOR': 3857  # Web Mercator (Google Maps projection)
}
self.srid = srid_map.get(coordinate_system.upper(), 0)
```

**No Breaking Changes**: The mapping structure remains the same, just added documentation and Web Mercator support for future use.

### Phase 3: Verification & Testing (Week 1, Day 3-5)

#### Test 1: Project CRS Lookup
```python
# tests/integration/test_dxf_coordinate_import.py

def test_import_uses_project_coordinate_system():
    """Verify DXF import fetches and uses project's CRS"""
    
    # Setup: Create project with State Plane CRS
    project_id = create_test_project(
        name="Test State Plane Project",
        coordinate_system_epsg='EPSG:2226'
    )
    
    # Import DXF file
    response = client.post('/api/dxf/import', data={
        'project_id': project_id,
        'file': open('tests/fixtures/sample.dxf', 'rb')
    })
    
    assert response.status_code == 200
    
    # Verify entities have correct SRID
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ST_SRID(geometry) as srid
        FROM drawing_entities
        WHERE project_id = %s
    """, (project_id,))
    
    srids = [row[0] for row in cur.fetchall()]
    assert srids == [2226], f"Expected SRID 2226, got {srids}"
```

#### Test 2: Fallback to LOCAL
```python
def test_import_defaults_to_local_when_no_crs():
    """Verify graceful fallback to LOCAL when project has no CRS configured"""
    
    # Setup: Create project WITHOUT coordinate system
    project_id = create_test_project(
        name="Test Local Project",
        coordinate_system_epsg=None
    )
    
    # Import DXF file
    response = client.post('/api/dxf/import', data={
        'project_id': project_id,
        'file': open('tests/fixtures/sample.dxf', 'rb')
    })
    
    assert response.status_code == 200
    
    # Verify entities default to SRID 0 (LOCAL)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ST_SRID(geometry) as srid
        FROM drawing_entities
        WHERE project_id = %s
    """, (project_id,))
    
    srids = [row[0] for row in cur.fetchall()]
    assert srids == [0], f"Expected SRID 0 (LOCAL), got {srids}"
```

#### Test 3: Multiple CRS Types
```python
def test_import_with_different_crs_types():
    """Test import with various coordinate systems"""
    
    test_cases = [
        ('EPSG:2226', 2226, 'STATE_PLANE'),  # CA Zone 2
        ('EPSG:4326', 4326, 'WGS84'),         # Geographic
        (None, 0, 'LOCAL')                    # No CRS
    ]
    
    for epsg, expected_srid, crs_name in test_cases:
        project_id = create_test_project(
            name=f"Test {crs_name} Project",
            coordinate_system_epsg=epsg
        )
        
        response = client.post('/api/dxf/import', data={
            'project_id': project_id,
            'file': open('tests/fixtures/sample.dxf', 'rb')
        })
        
        assert response.status_code == 200
        
        # Verify SRID
        srid = get_entity_srid(project_id)
        assert srid == expected_srid, \
            f"{crs_name}: Expected SRID {expected_srid}, got {srid}"
```

#### Manual Validation Script
```python
# scripts/validate_coordinate_import.py

"""
Manual validation script to verify coordinate system integration.
Run after implementing Phase 1-2 changes.
"""

import psycopg2
from dxf_importer import DXFImporter
import os

DB_CONFIG = {
    'host': os.getenv('PGHOST'),
    'database': os.getenv('PGDATABASE'),
    'user': os.getenv('PGUSER'),
    'password': os.getenv('PGPASSWORD')
}

def validate_import():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Find a project with coordinate system configured
    cur.execute("""
        SELECT p.project_id, p.project_name, cs.epsg_code, cs.system_name
        FROM projects p
        JOIN coordinate_systems cs ON p.default_coordinate_system_id = cs.system_id
        LIMIT 1
    """)
    
    result = cur.fetchone()
    if not result:
        print("ERROR: No projects with coordinate systems found!")
        print("Run Project 3 Phase 2 first to create coordinate_systems FK constraints")
        return False
    
    project_id, project_name, epsg_code, system_name = result
    print(f"\n✓ Found test project: {project_name}")
    print(f"  Project ID: {project_id}")
    print(f"  Coordinate System: {system_name} ({epsg_code})")
    
    # Count entities BEFORE import
    cur.execute("SELECT COUNT(*) FROM drawing_entities WHERE project_id = %s", (project_id,))
    before_count = cur.fetchone()[0]
    
    # Import test DXF
    test_dxf = 'tests/fixtures/sample.dxf'
    if not os.path.exists(test_dxf):
        print(f"\nWARNING: Test DXF not found at {test_dxf}")
        print("Upload any DXF file to test manually")
        return True
    
    importer = DXFImporter(DB_CONFIG, create_intelligent_objects=False)
    
    # Map EPSG to coordinate_system parameter
    epsg_map = {
        'EPSG:2226': 'STATE_PLANE',
        'EPSG:4326': 'WGS84'
    }
    coordinate_system = epsg_map.get(epsg_code, 'LOCAL')
    
    print(f"\n✓ Importing DXF with coordinate_system='{coordinate_system}'...")
    stats = importer.import_dxf(test_dxf, project_id, coordinate_system=coordinate_system)
    
    print(f"  Imported {stats['entities']} entities")
    
    # Verify SRID of imported entities
    cur.execute("""
        SELECT DISTINCT ST_SRID(geometry) as srid, COUNT(*) as count
        FROM drawing_entities
        WHERE project_id = %s
        GROUP BY ST_SRID(geometry)
    """, (project_id,))
    
    results = cur.fetchall()
    print(f"\n✓ Geometry SRID distribution:")
    for srid, count in results:
        print(f"  SRID {srid}: {count} entities")
        
        # Validate against expected SRID
        expected_srid = int(epsg_code.replace('EPSG:', '')) if epsg_code != 'LOCAL' else 0
        if srid != expected_srid:
            print(f"\n✗ FAIL: Expected SRID {expected_srid}, found {srid}")
            print("  The coordinate system integration is NOT working correctly")
            return False
    
    print(f"\n✓ SUCCESS: All entities have correct SRID!")
    print(f"  Project CRS ({epsg_code}) matches entity SRID")
    conn.close()
    return True

if __name__ == '__main__':
    success = validate_import()
    exit(0 if success else 1)
```

### Phase 4: Documentation Updates (Week 1, Day 5)

#### Update API Documentation
```markdown
# docs/API_ENDPOINTS.md

## POST /api/dxf/import

Import a DXF file into a project.

**Request:**
- `file`: DXF file (multipart/form-data)
- `project_id`: UUID of target project (required)
- `import_modelspace`: Boolean, default true
- `pattern_id`: Optional import mapping pattern ID

**Coordinate System Handling:**
The import automatically uses the project's configured coordinate system 
(`default_coordinate_system_id`). Imported geometries are stored with the 
correct SRID matching the project's EPSG code.

**Supported Coordinate Systems:**
- EPSG:2226-2230 (CA State Plane Zones 2-6) → SRID 2226-2230
- EPSG:4326 (WGS84) → SRID 4326
- No CRS configured → SRID 0 (LOCAL)

**Example:**
```bash
curl -X POST http://localhost:5000/api/dxf/import \
  -F "file=@survey_plan.dxf" \
  -F "project_id=123e4567-e89b-12d3-a456-426614174000"
```

**Response:**
```json
{
  "success": true,
  "stats": {
    "entities": 1523,
    "coordinate_system": "STATE_PLANE",
    "srid": 2226,
    ...
  }
}
```
```

#### Update User Guide
```markdown
# docs/USER_GUIDE.md

## Importing DXF Files

### Coordinate System Configuration

**IMPORTANT:** Before importing DXF files, ensure your project has a coordinate 
system configured:

1. Navigate to Project Settings
2. Select "Coordinate System" from dropdown
3. Choose the appropriate system (typically CA State Plane Zone 2 for Northern California)
4. Save project settings

**Automatic CRS Handling:**
When you import a DXF file, the system automatically:
- Reads your project's coordinate system
- Tags all imported geometries with the correct SRID
- Ensures spatial consistency across all project data

**Best Practices:**
- Use State Plane coordinates for survey-grade work (sub-foot accuracy)
- Use WGS84 for GPS data or web mapping integration
- Use LOCAL only for preliminary design with arbitrary coordinates

**Troubleshooting:**
If imported coordinates appear in wrong location:
1. Verify project coordinate system matches DXF source CRS
2. Check entity SRID in database: `SELECT ST_SRID(geometry) FROM drawing_entities`
3. Contact support if SRID is 0 (indicates import bug)
```

## Migration Strategy

### No Database Migration Required
This fix uses existing schema:
- ✅ `projects.default_coordinate_system_id` already exists (Project 3 Phase 2)
- ✅ `coordinate_systems` table already exists
- ✅ `drawing_entities.geometry` already supports SRID tagging
- ✅ No new columns or tables needed

### Code Deployment Process
1. **Deploy Phase 1**: Update `app.py` with coordinate system lookup
2. **Verify**: Run validation script to confirm correct SRID tagging
3. **Monitor**: Check import logs for any CRS lookup errors
4. **Document**: Update API docs and user guide

### Rollback Plan
If issues arise:
```python
# Revert app.py to previous version
git diff HEAD~1 app.py
git checkout HEAD~1 -- app.py

# System gracefully falls back to SRID 0 (LOCAL)
# No data corruption - just incorrect SRID tags
```

## Risk Assessment

### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Database query adds latency | Low | Low | Single indexed FK lookup (<5ms) |
| EPSG mapping incomplete | Medium | Low | Fallback to LOCAL, document supported EPSG codes |
| Project has NULL CRS | Low | Low | Graceful fallback to LOCAL with log warning |

### Data Quality Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Existing entities have wrong SRID | High | Medium | Document as known issue; future migration script |
| Mixed SRID in single project | Low | High | Prevented by FK constraint (Project 3 Phase 2) |

## Success Criteria

### Must Have (Phase 1-2)
- ✅ DXF import reads project's `default_coordinate_system_id`
- ✅ Entities stored with correct SRID (not always 0)
- ✅ Fallback to LOCAL when project has no CRS
- ✅ Zero breaking changes to existing API
- ✅ Performance impact < 10ms

### Should Have (Phase 3-4)
- ✅ Integration tests validate CRS handling
- ✅ Manual validation script passes
- ✅ API documentation updated
- ✅ User guide includes CRS best practices

### Nice to Have (Future Enhancements)
- ⏸️ Coordinate transformation (actual reprojection between CRS)
- ⏸️ Auto-detect DXF source CRS from metadata
- ⏸️ UI warning when DXF CRS ≠ Project CRS
- ⏸️ Batch re-project existing entities to correct CRS

## Timeline

**Total Duration: 1 Week**

- **Day 1-2**: Implement Phase 1 (app.py changes)
- **Day 2**: Review Phase 2 (dxf_importer.py validation)
- **Day 3-4**: Phase 3 testing (integration tests, validation script)
- **Day 5**: Phase 4 documentation and deployment

## Dependencies

### Prerequisite Projects
- ✅ **Project 3, Phase 2**: Must complete first
  - Adds `projects.default_coordinate_system_id` FK constraint
  - Ensures all projects can have coordinate system configured
  - Creates `coordinate_systems` reference table

### Required Infrastructure
- ✅ PostgreSQL with PostGIS extension
- ✅ `coordinate_systems` table populated (Project 3 setup)
- ✅ Projects have `default_coordinate_system_id` configured

## ROI & Business Value

### Data Integrity Benefits
- **Spatial Accuracy**: Coordinates stored in correct reference system
- **Multi-Source Integration**: Can confidently overlay data from different sources
- **Survey Compliance**: Meets survey-grade accuracy requirements
- **Liability Reduction**: Eliminates CRS confusion that causes positioning errors

### User Experience Benefits
- **Zero Configuration**: Automatic CRS handling based on project settings
- **Consistent Behavior**: Import respects project-level standards
- **Error Prevention**: Cannot accidentally mix coordinate systems

### Technical Benefits
- **Minimal Code Changes**: ~30 lines of code, leverages existing infrastructure
- **No Schema Changes**: Uses existing Project 3 Phase 2 constraints
- **Performance**: Single indexed lookup, negligible overhead
- **Maintainability**: Centralizes CRS logic in one place

## Appendix: Complete EPSG Mapping Reference

### California State Plane Zones (NAD83, US Survey Feet)
```python
CALIFORNIA_STATE_PLANE_EPSG = {
    'EPSG:2226': {'zone': 2, 'region': 'Northern CA', 'srid': 2226},
    'EPSG:2227': {'zone': 3, 'region': 'Central CA', 'srid': 2227},
    'EPSG:2228': {'zone': 4, 'region': 'Southern CA', 'srid': 2228},
    'EPSG:2229': {'zone': 5, 'region': 'Southern CA', 'srid': 2229},
    'EPSG:2230': {'zone': 6, 'region': 'San Diego', 'srid': 2230},
}
```

### Common Geographic Systems
```python
GEOGRAPHIC_EPSG = {
    'EPSG:4326': {'name': 'WGS84', 'units': 'degrees', 'srid': 4326},
    'EPSG:3857': {'name': 'Web Mercator', 'units': 'meters', 'srid': 3857},
}
```

### Usage in DXFImporter
```python
def map_epsg_to_coordinate_system(epsg_code: str) -> str:
    """Map EPSG code to DXFImporter coordinate_system parameter"""
    
    if epsg_code in CALIFORNIA_STATE_PLANE_EPSG:
        return 'STATE_PLANE'
    elif epsg_code == 'EPSG:4326':
        return 'WGS84'
    elif epsg_code == 'EPSG:3857':
        return 'WEB_MERCATOR'
    else:
        return 'LOCAL'  # Fallback
```
