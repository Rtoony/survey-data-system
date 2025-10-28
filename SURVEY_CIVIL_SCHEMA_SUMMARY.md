# Survey & Civil Engineering Database Schema - Summary for Main App

## Overview

The ACAD-GIS database now includes comprehensive survey and civil engineering capabilities with **29 specialized tables** organized into 10 functional categories. All spatial data uses **PostGIS PointZ/LineStringZ/PolygonZ** with **SRID 2226** (California State Plane Zone 2, US Survey Feet) by default, with built-in multi-zone support.

---

## Quick Reference - All Tables

### 1. Survey Points & Control (4 tables)
| Table | Purpose | Geometry Type |
|-------|---------|---------------|
| `coordinate_systems` | Multi-zone coordinate reference system lookup | N/A |
| `survey_points` | Core survey point database (control, topo, layout) | PointZ |
| `survey_control_network` | Network adjustment metadata | N/A |
| `control_point_membership` | Point-to-network relationships with residuals | N/A |

### 2. Site Features (3 tables)
| Table | Purpose | Geometry Type |
|-------|---------|---------------|
| `site_trees` | Tree inventory (species, DBH, condition) | Via survey_point |
| `utility_structures` | Manholes, valves, catch basins, poles | PointZ |
| `surface_features` | Curbs, fences, walls, buildings | GeometryZ |

### 3. Alignments & Profiles (4 tables)
| Table | Purpose | Geometry Type |
|-------|---------|---------------|
| `horizontal_alignments` | Road/utility centerlines | LineStringZ |
| `alignment_pis` | PI geometry with curve data | PointZ |
| `vertical_profiles` | Existing ground, proposed grade profiles | N/A |
| `profile_pvis` | PVI geometry with grade data | N/A |

### 4. Cross Sections & Earthwork (4 tables)
| Table | Purpose | Geometry Type |
|-------|---------|---------------|
| `cross_sections` | Station-based sections | LineStringZ |
| `cross_section_points` | Individual cross_offset/elevation points | N/A |
| `earthwork_quantities` | Cut/fill volumes by station range | N/A |
| `earthwork_balance` | Mass haul diagram data | N/A |

### 5. Utility Networks (3 tables)
| Table | Purpose | Geometry Type |
|-------|---------|---------------|
| `utility_lines` | Water/sewer/storm/electric/gas pipes | LineStringZ |
| `utility_network_connectivity` | Network topology/graph | N/A |
| `utility_service_connections` | Service laterals to properties | PointZ |

### 6. Property & Legal (4 tables)
| Table | Purpose | Geometry Type |
|-------|---------|---------------|
| `parcels` | Property parcels with APN/ownership | PolygonZ |
| `parcel_corners` | Surveyed corners with monuments | Via survey_point |
| `easements` | Utility/access easements | GeometryZ |
| `right_of_way` | Public ROW boundaries | GeometryZ |

### 7. Survey Observations (3 tables)
| Table | Purpose | Geometry Type |
|-------|---------|---------------|
| `survey_observations` | Raw field data (angles, distances, GPS) | N/A |
| `traverse_loops` | Traverse closure analysis | N/A |
| `traverse_loop_observations` | Loop membership with adjustments | N/A |

### 8. Grading & Construction (4 tables)
| Table | Purpose | Geometry Type |
|-------|---------|---------------|
| `grading_limits` | Grading/clearing/disturbance boundaries | PolygonZ |
| `pavement_sections` | Pavement layer design & specs | N/A |
| `surface_models` | TIN/DTM surface metadata | PolygonZ (bbox) |
| `typical_sections` | Reusable cross-section templates | N/A |

---

## Coordinate System Support

### Default Coordinate System
- **EPSG:2226** - NAD83 California State Plane Zone 2, US Survey Feet
- All geometry columns use SRID 2226 by default

### Supported California State Plane Zones
| Zone | EPSG Code | Coverage Area |
|------|-----------|---------------|
| Zone 1 | EPSG:2225 | Northern California |
| **Zone 2** | **EPSG:2226** | **North Central California (Default)** |
| Zone 3 | EPSG:2227 | Central California |
| Zone 4 | EPSG:2228 | South Central California |
| Zone 5 | EPSG:2229 | Southern California |
| Zone 6 | EPSG:2230 | Far Southern California |

### Project-Level Coordinate System Override
The `projects` table includes:
- `default_epsg_code` VARCHAR(20) DEFAULT 'EPSG:2226'
- `default_coordinate_system` VARCHAR(100) DEFAULT 'NAD83 State Plane California Zone 2'

### Transform Between Zones
```sql
-- Transform Zone 3 data to Zone 2 (default)
INSERT INTO survey_points (geometry, ...)
VALUES (ST_Transform(ST_SetSRID(your_point, 2227), 2226), ...);

-- Transform to WGS84 for web mapping
SELECT ST_Transform(geometry, 4326) FROM survey_points;
```

---

## Key Foreign Key Relationships

### All Tables → Projects
Every survey/civil table has `project_id` referencing `projects.project_id` for project-based organization.

### Survey Points as Hub
Many tables reference `survey_points.point_id`:
- `site_trees.survey_point_id` - Trees located by survey points
- `utility_structures.survey_point_id` - Structures located by survey points
- `parcel_corners.survey_point_id` - Property corners
- `survey_observations.instrument_station_point_id` - Instrument setups
- `survey_observations.backsight_point_id` - Backsight references
- `survey_observations.target_point_id` - Target points

### Alignments as Design Spine
`horizontal_alignments.alignment_id` ties together:
- `alignment_pis` - Horizontal curve geometry
- `vertical_profiles` - Vertical profiles
- `cross_sections` - Station-based sections
- `earthwork_quantities` - Volume calculations
- `pavement_sections` - Pavement design

### Utility Network Topology
- `utility_lines.from_structure_id` → `utility_structures.structure_id`
- `utility_lines.to_structure_id` → `utility_structures.structure_id`
- `utility_network_connectivity` - Explicit graph representation

---

## API Endpoint Recommendations

### Survey Points
```
GET    /api/v1/survey-points                    # List all (filter by project/type/code)
GET    /api/v1/survey-points/{point_id}         # Get point details
POST   /api/v1/survey-points                    # Create new point
PUT    /api/v1/survey-points/{point_id}         # Update point
DELETE /api/v1/survey-points/{point_id}         # Delete point
GET    /api/v1/survey-points/by-project/{id}    # Points for specific project
POST   /api/v1/survey-points/import             # Bulk import from CSV/collector
```

### Site Features
```
GET    /api/v1/site-trees                       # List trees
GET    /api/v1/utility-structures               # List structures (filter by type/system)
GET    /api/v1/surface-features                 # List surface features
```

### Alignments & Earthwork
```
GET    /api/v1/alignments                       # List alignments
GET    /api/v1/alignments/{id}/pis              # Get PI geometry
GET    /api/v1/alignments/{id}/profile          # Get vertical profile
GET    /api/v1/alignments/{id}/cross-sections   # Get sections
GET    /api/v1/earthwork-quantities             # Volume summary by alignment
GET    /api/v1/earthwork-balance/{id}           # Mass haul diagram data
```

### Utilities
```
GET    /api/v1/utility-lines                    # List lines (filter by type/owner)
GET    /api/v1/utility-lines/{id}/connectivity  # Get connected elements
POST   /api/v1/utility-networks/trace           # Network trace analysis
```

### Parcels & Legal
```
GET    /api/v1/parcels                          # List parcels (filter by owner/APN)
GET    /api/v1/parcels/{id}/corners             # Get surveyed corners
GET    /api/v1/easements                        # List easements
GET    /api/v1/right-of-way                     # List ROW
```

### Grading & Construction
```
GET    /api/v1/grading-limits                   # List grading limits (filter by type)
GET    /api/v1/pavement-sections                # List pavement sections
GET    /api/v1/surface-models                   # List surface metadata
GET    /api/v1/typical-sections                 # List typical section templates
```

### Survey Observations
```
GET    /api/v1/observations                     # List observations (filter by session/date)
GET    /api/v1/traverse-loops                   # List traverse loops with closure
POST   /api/v1/observations/import              # Import raw data collector files
```

---

## Spatial Queries & PostGIS Usage

### Common Spatial Queries

**Find points within radius:**
```sql
SELECT * FROM survey_points 
WHERE ST_DWithin(geometry, ST_MakePoint(easting, northing, elev), 100);
```

**Find utilities crossing parcel:**
```sql
SELECT u.* FROM utility_lines u, parcels p
WHERE p.parcel_id = 'some-uuid' 
  AND ST_Intersects(u.geometry, p.boundary_geometry);
```

**Tree protection zones (buffer):**
```sql
SELECT ST_Buffer(sp.geometry, 15) as protection_zone
FROM survey_points sp
JOIN site_trees st ON st.survey_point_id = sp.point_id
WHERE st.protection_status = 'Protected';
```

**Points within parcel:**
```sql
SELECT sp.* FROM survey_points sp, parcels p
WHERE p.parcel_id = 'some-uuid'
  AND ST_Contains(p.boundary_geometry, sp.geometry);
```

### All Geometry Columns Have GiST Indexes
Optimized for spatial queries:
- `CREATE INDEX idx_*_geom ON table_name USING GIST(geometry);`

---

## Data Validation & Quality

### Recommended Validations
1. **Survey Points**: Validate coordinate ranges for State Plane zone
2. **Earthwork**: Ensure `start_station < end_station`
3. **Utility Lines**: Validate `from_structure_id != to_structure_id`
4. **Parcels**: Check area calculations match geometry
5. **Grading Limits**: Validate actual area ≤ max_allowed_area

### Triggers & Constraints
Consider adding:
- Auto-calculate area/length on geometry insert/update
- Validate SRID matches project coordinate system
- Auto-populate northing/easting from geometry
- Prevent deletion of control points used in active networks

---

## Integration Points with Existing ACAD-GIS Tables

### Projects Table
- All survey tables reference `projects.project_id`
- Projects table now includes `default_epsg_code` and `default_coordinate_system`

### Drawings Table
- Survey points, trees, structures, parcels, utilities can link to `drawings.drawing_id`
- Enables "features on this sheet" queries

### Block Standards
- Survey symbols (point markers, tree symbols, utility structures) reference `block_standards`
- CAD graphics stored in `block_inserts`, data stored in survey tables

### Drawing Entities
- Utility lines stored in both `utility_lines` (engineering data) and `drawing_entities` (CAD graphics)
- Alignments can be rendered as polylines in `drawing_entities`

---

## Production Deployment Notes

### Database Requirements
- **PostgreSQL 12+** with **PostGIS 3.0+** extension
- Ensure `gen_random_uuid()` function is available (built-in PostgreSQL 13+)
- Recommended: Connection pooling for high-traffic APIs

### Performance Optimization
1. **Spatial Indexes**: All geometry columns have GiST indexes ✓
2. **Foreign Key Indexes**: All FKs are indexed ✓
3. **Composite Indexes**: Consider adding:
   - `(project_id, point_type)` on survey_points
   - `(project_id, utility_system)` on utility_lines
   - `(alignment_id, station)` on cross_sections

### Backup & Recovery
- Survey data is critical - implement regular backups
- Consider point-in-time recovery for field data imports
- Test restore procedures before production deployment

---

## Quick Start Guide

### 1. Deploy Schema
```bash
psql -U your_user -d your_database -f create_survey_civil_schema.sql
```

### 2. Set Project Coordinate System
```sql
UPDATE projects 
SET default_epsg_code = 'EPSG:2229',
    default_coordinate_system = 'NAD83 State Plane California Zone 5'
WHERE project_name = 'Southern California Project';
```

### 3. Import Survey Points
```sql
INSERT INTO survey_points (
    project_id, point_number, point_type, geometry, 
    northing, easting, elevation, survey_date
) VALUES (
    'project-uuid', 
    '101', 
    'Control',
    ST_SetSRID(ST_MakePoint(6000000, 2000000, 100), 2226),
    2000000.0000,
    6000000.0000,
    100.0000,
    '2025-01-15'
);
```

### 4. Query Survey Data
```sql
-- Get all control points for a project
SELECT point_number, northing, easting, elevation
FROM survey_points
WHERE project_id = 'project-uuid' 
  AND point_type = 'Control'
  AND is_active = TRUE
ORDER BY point_number;
```

---

## Documentation Files

- **`create_survey_civil_schema.sql`** - Complete SQL schema with all 29 tables
- **`MIGRATION_SURVEY_CIVIL.md`** - Detailed migration guide with full table definitions
- **`SURVEY_CIVIL_SCHEMA_SUMMARY.md`** - This summary (for main app reference)

---

## Schema Statistics

- **Total Tables**: 29
- **Geometry Columns**: 18 (all with GiST indexes)
- **Foreign Key Relationships**: 40+
- **Supported Coordinate Systems**: 6+ CA State Plane zones (expandable)
- **Default SRID**: EPSG:2226 (NAD83 CA State Plane Zone 2, US Survey Feet)

---

## Next Steps for Main App Integration

1. ✅ **Schema Deployed** - Run `create_survey_civil_schema.sql`
2. 🔄 **API Endpoints** - Implement CRUD endpoints for each table
3. 🔄 **Coordinate Validation** - Add SRID validation in API layer
4. 🔄 **Spatial Queries** - Implement PostGIS queries for proximity/intersection
5. 🔄 **Import/Export** - Build CSV/LandXML/DXF import workflows
6. 🔄 **WebGIS Integration** - Transform coordinates to WGS84 for map display

---

**Questions?** Refer to `MIGRATION_SURVEY_CIVIL.md` for detailed table schemas, workflows, and examples.
