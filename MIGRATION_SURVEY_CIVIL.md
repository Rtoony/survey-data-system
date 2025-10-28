# Survey & Civil Engineering - Migration Documentation

## Overview

The Survey & Civil Engineering module extends the ACAD-GIS system with comprehensive support for civil/survey engineering workflows. This module provides complete data management for survey points, control networks, site features, alignments, earthwork, utilities, and property information - transforming the database into the ultimate source of truth for civil engineering projects.

**Key Value:** Survey data management, control network adjustments, site feature inventory, alignment design, earthwork calculations, utility network tracking, property/ROW management, and raw field data storage for quality assurance.

## Use Cases

1. **Survey Point Management**: Store and manage all survey points including control, topo shots, and layout points
2. **Control Networks**: Track control point hierarchies and network adjustments with quality metrics
3. **Site Inventory**: Catalog trees, utility structures, and surface features with detailed attributes
4. **Alignment Design**: Design horizontal and vertical alignments with PI/PVI geometry
5. **Earthwork Analysis**: Calculate cut/fill volumes and track mass haul data
6. **Utility Networks**: Model water, sewer, storm, electric, gas systems with connectivity
7. **Property/Legal**: Manage parcels, easements, and right-of-way with legal descriptions
8. **Field Data QA**: Store raw observations for verification and adjustment analysis

---

## Database Schema

### 1. Survey Points - Core Survey Data

**Table: `survey_points`**

Central repository for all surveyed points on a project.

```sql
CREATE TABLE survey_points (
    point_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    drawing_id UUID REFERENCES drawings(drawing_id) ON DELETE SET NULL,
    
    -- Point Identification
    point_number VARCHAR(50) NOT NULL,
    point_description TEXT,
    point_code VARCHAR(50),
    point_type VARCHAR(50),                            -- 'Control', 'Topo', 'Layout', 'Benchmark'
    
    -- Coordinates (PostGIS 3D Point in State Plane)
    geometry GEOMETRY(PointZ, 2226) NOT NULL,          -- EPSG:2226 = NAD83 CA State Plane Zone 2 (US Feet)
    northing NUMERIC(15, 4),
    easting NUMERIC(15, 4),
    elevation NUMERIC(10, 4),
    coordinate_system VARCHAR(100),
    epsg_code VARCHAR(20),
    
    -- Survey Metadata
    survey_date DATE,
    surveyed_by VARCHAR(255),
    survey_method VARCHAR(100),                        -- 'GPS-RTK', 'Total Station', 'Level'
    instrument_used VARCHAR(100),
    
    -- Quality / Accuracy
    horizontal_accuracy NUMERIC(8, 4),
    vertical_accuracy NUMERIC(8, 4),
    accuracy_units VARCHAR(20) DEFAULT 'Feet',
    quality_code VARCHAR(50),
    
    -- Status
    is_control_point BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    superseded_by UUID REFERENCES survey_points(point_id) ON DELETE SET NULL,
    
    notes TEXT,
    attributes JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Key Features:**
- Multiple coordinate representations (State Plane projected geometry + N/E/E fields)
- Survey method and equipment tracking
- Accuracy/quality metrics
- Control point designation
- Point supersession for revisions

**Relationships:**
- `projects` → ONE project (many-to-one)
- `drawings` → ONE drawing (many-to-one, nullable)
- `site_trees` → MANY trees (one-to-many)
- `utility_structures` → MANY structures (one-to-many)
- `survey_observations` → MANY observations (one-to-many)
- `control_point_membership` → MANY network memberships (one-to-many)

---

### 2. Survey Control Networks

**Table: `survey_control_network`**

Manages control point networks and adjustment metadata.

**Table: `control_point_membership`**

Links control points to networks with adjustment results and residuals.

**Key Features:**
- Network hierarchy (primary/secondary/tertiary)
- Adjustment method tracking (Least Squares, Compass Rule, etc.)
- Standard errors and confidence levels
- Adjusted coordinates and residuals
- Fixed point designation

---

### 3. Site Features

**Table: `site_trees`**

Tree inventory with species, size, condition, and protection status.

**Table: `utility_structures`**

Utility structures (manholes, valves, catch basins, poles, transformers) with elevations and condition.

**Table: `surface_features`**

General surface features (curbs, fences, walls, buildings, pavement) with geometry.

**Key Features:**
- Links to survey points (how features were located)
- Structured attributes (species, diameter, material, dimensions)
- Condition tracking
- Protection/preservation status
- PostGIS geometry (Point, Line, or Polygon)

---

### 4. Alignments & Profiles

**Table: `horizontal_alignments`**

Horizontal centerlines for roads, utilities, property lines.

**Table: `alignment_pis`**

Points of Intersection with curve data (radius, length, delta angle, spirals).

**Table: `vertical_profiles`**

Vertical profiles (existing ground, proposed grade, top of curb).

**Table: `profile_pvis`**

Points of Vertical Intersection with grade data and vertical curves.

**Key Features:**
- Station-based design
- Curve geometry (circular, spiral, compound)
- Grade percentages and K-values
- High/low point identification
- 3D LineStringZ geometry

**Relationships:**
- `horizontal_alignments` → `alignment_pis` (one-to-many)
- `horizontal_alignments` → `vertical_profiles` (one-to-many)
- `vertical_profiles` → `profile_pvis` (one-to-many)
- `horizontal_alignments` → `cross_sections` (one-to-many)

---

### 5. Cross Sections

**Table: `cross_sections`**

Station-based cross sections with cut/fill data.

**Table: `cross_section_points`**

Individual points on each cross section (offset/elevation pairs).

**Key Features:**
- Offset/elevation arrays
- Cut/fill area calculations
- Slope ratios (2:1, 3:1, etc.)
- Typical section references
- 3D LineStringZ geometry

---

### 6. Earthwork Quantities

**Table: `earthwork_quantities`**

Volume calculations by station range with material types and haul data.

**Table: `earthwork_balance`**

Mass haul diagram data with cumulative volumes and balance points.

**Key Features:**
- Cut/fill volumes (cubic yards)
- Material classifications (common, rock, select fill)
- Shrinkage/swell factors
- Haul distances and overhaul
- Unit costs and estimates
- Mass ordinate tracking

---

### 7. Utility Networks

**Table: `utility_lines`**

Utility pipes/conduits (water, sewer, storm, electric, gas) with properties.

**Table: `utility_network_connectivity`**

Network connectivity tracking (line-to-line, line-to-structure).

**Table: `utility_service_connections`**

Service laterals connecting mains to properties.

**Key Features:**
- Multiple utility types in one table
- Material, diameter, pressure ratings
- Invert elevations and slopes
- Flow characteristics (design flow, capacity)
- Upstream/downstream structure connections
- Network topology for analysis
- 3D LineStringZ geometry

**Relationships:**
- `utility_lines` → `utility_structures` (upstream/downstream FKs)
- `utility_lines` → `utility_service_connections` (one-to-many)
- `utility_network_connectivity` tracks graph topology

---

### 8. Parcels & Right-of-Way

**Table: `parcels`**

Property parcels with APNs, legal descriptions, ownership, and boundaries.

**Table: `parcel_corners`**

Surveyed property corners with monument descriptions.

**Table: `easements`**

Easements with grantor/grantee, recording info, and geometry.

**Table: `right_of_way`**

Public right-of-way with ownership, dedication info, and boundaries.

**Key Features:**
- Legal descriptions and recording references
- Area calculations (acres, square feet)
- Zoning and land use
- Monument/corner tracking
- Easement types and purposes
- 3D Polygon/LineString geometry

---

### 9. Survey Observations (Raw Field Data)

**Table: `survey_observations`**

Raw field observations (angles, distances, GPS, leveling).

**Table: `traverse_loops`**

Traverse loop definitions with closure analysis.

**Table: `traverse_loop_observations`**

Links observations to loops for adjustment.

**Key Features:**
- Total station observations (angles, distances, prism heights)
- GPS observations (lat/lon, fix type, DOP values)
- Leveling observations (rod readings, HI)
- Instrument setup tracking
- Backsight/foresight relationships
- Quality metrics (standard deviation, residuals)
- Rejection flags for outliers
- Traverse closure analysis

---

## Data Relationships Summary

### Primary Foreign Key Relationships

**Projects → Survey Data:**
- `survey_points.project_id` → `projects.project_id`
- `horizontal_alignments.project_id` → `projects.project_id`
- `parcels.project_id` → `projects.project_id`
- All survey tables link to projects

**Drawings → Survey Data:**
- `survey_points.drawing_id` → `drawings.drawing_id`
- `site_trees.drawing_id` → `drawings.drawing_id`
- `utility_structures.drawing_id` → `drawings.drawing_id`
- Survey features can optionally link to specific drawings

**Survey Points → Features:**
- `site_trees.survey_point_id` → `survey_points.point_id`
- `utility_structures.survey_point_id` → `survey_points.point_id`
- `parcel_corners.survey_point_id` → `survey_points.point_id`
- Features reference the points used to locate them

**Alignments → Design Elements:**
- `alignment_pis.alignment_id` → `horizontal_alignments.alignment_id`
- `vertical_profiles.alignment_id` → `horizontal_alignments.alignment_id`
- `cross_sections.alignment_id` → `horizontal_alignments.alignment_id`
- `earthwork_quantities.alignment_id` → `horizontal_alignments.alignment_id`

**Utilities → Structures:**
- `utility_lines.upstream_structure_id` → `utility_structures.structure_id`
- `utility_lines.downstream_structure_id` → `utility_structures.structure_id`
- Network topology tracking

**Observations → Control:**
- `survey_observations.instrument_station_point_id` → `survey_points.point_id`
- `survey_observations.backsight_point_id` → `survey_points.point_id`
- `survey_observations.target_point_id` → `survey_points.point_id`
- Full field data traceability

---

## PostGIS Geometry Usage

### CRITICAL: Projected Coordinates Required for Civil Engineering

All spatial tables use PostGIS geometry types with **SRID 2226** (NAD83 California State Plane Zone 2, US Survey Feet) as the default:

**Why Projected Coordinates?**
- Geographic coordinates (lat/lon in degrees) break distance/area calculations
- Civil engineering requires linear units (feet/meters) for:
  - Alignment stationing (10+00, 20+00, etc.)
  - Earthwork volumes (cubic yards)
  - Pipe lengths and slopes
  - Parcel areas (square feet/acres)
- State Plane projections maintain accuracy within survey tolerances (<1:10,000 distortion)

**SRID Selection by Region:**

The schema supports flexible coordinate system management through:
1. **Default SRID**: EPSG:2226 (California State Plane Zone 2) ✓
2. **Project-Level Override**: Each project can specify its own default EPSG code
3. **Reference Table**: `coordinate_systems` table tracks all supported coordinate systems

**California State Plane Zones (All Supported):**
- **Zone 1**: EPSG:2225 (Northern California)
- **Zone 2**: EPSG:2226 (North Central California) ✓ Default
- **Zone 3**: EPSG:2227 (Central California)
- **Zone 4**: EPSG:2228 (South Central California)
- **Zone 5**: EPSG:2229 (Southern California)
- **Zone 6**: EPSG:2230 (Far Southern California)

**Future Expansion:**
Additional coordinate systems (Texas, Nevada, UTM zones, etc.) can be added to the `coordinate_systems` reference table without schema changes.

**Geometry Types:**
- **PointZ**: 3D points (survey points, trees, structures, monuments)
- **LineStringZ**: 3D lines (alignments, utilities, cross sections, easement centerlines)
- **PolygonZ**: 3D polygons (parcels, easements, ROW, earthwork boundaries, surface features)
- **GeometryZ**: Mixed geometry types (surface features can be point/line/polygon)

**Spatial Indexes:**
All geometry columns have GiST indexes for spatial queries:
- Proximity searches (find all points within radius)
- Intersection testing (utilities crossing parcels)
- Buffer analysis (tree protection zones)
- Containment queries (points within parcel)

**Coordinate Transformation:**

For web mapping (Leaflet, Mapbox, Google Maps), transform to WGS84 on-the-fly:
```sql
SELECT ST_Transform(geometry, 4326) as web_geometry FROM survey_points;
```

For cross-zone projects, transform between State Plane zones:
```sql
-- Transform Zone 3 data to Zone 2
SELECT ST_Transform(ST_SetSRID(geometry, 2227), 2226) FROM survey_points;
```

**Project-Level Coordinate System Management:**

The `projects` table includes coordinate system tracking:
```sql
-- Projects table includes:
default_epsg_code VARCHAR(20) DEFAULT 'EPSG:2226'
default_coordinate_system VARCHAR(100) DEFAULT 'NAD83 State Plane California Zone 2'
```

Set project-specific coordinate systems:
```sql
UPDATE projects 
SET default_epsg_code = 'EPSG:2229',
    default_coordinate_system = 'NAD83 State Plane California Zone 5'
WHERE project_id = 'your-project-uuid';
```

---

## Integration with Existing Tables

The survey module integrates seamlessly with existing ACAD-GIS tables:

**Projects:**
- All survey tables reference `projects.project_id`
- Enables project-based filtering and organization

**Drawings:**
- Survey data can link to specific drawing files
- Supports sheet assignment workflows
- Enables "points on this drawing" queries

**Block Inserts:**
- Survey point symbols can reference `block_standards`
- Tree symbols link to `site_trees` data
- Utility symbols link to `utility_structures` data

**Drawing Entities:**
- CAD primitives (lines, polylines) can represent survey data graphically
- Utility lines stored in both `utility_lines` (data) and `drawing_entities` (graphics)

---

## Typical Workflows

### 1. Field Survey Import
1. Import raw observations → `survey_observations`
2. Process coordinates → `survey_points`
3. Link to control network → `control_point_membership`
4. Generate CAD symbols → `block_inserts`

### 2. Site Feature Inventory
1. Surveyors collect topo shots → `survey_points`
2. Classify points by code (TC, MH, TREE, etc.)
3. Create structured features → `site_trees`, `utility_structures`, `surface_features`
4. Link features to survey points → `survey_point_id` FK

### 3. Alignment Design
1. Create horizontal alignment → `horizontal_alignments`
2. Define PIs and curves → `alignment_pis`
3. Create vertical profile → `vertical_profiles`
4. Define PVIs and grades → `profile_pvis`
5. Generate cross sections → `cross_sections`
6. Calculate earthwork → `earthwork_quantities`

### 4. Utility Network Modeling
1. Survey utility structures → `utility_structures`
2. Model utility lines → `utility_lines`
3. Define connectivity → `utility_network_connectivity`
4. Add service laterals → `utility_service_connections`
5. Perform network analysis (flow, capacity, trace)

### 5. Property Survey
1. Set control points → `survey_points` (is_control_point = TRUE)
2. Survey property corners → `parcel_corners`
3. Create parcel boundaries → `parcels`
4. Define easements → `easements`
5. Map ROW → `right_of_way`

---

## API Endpoint Recommendations

### Survey Points
- `GET /api/survey-points` - List all points (filterable by project, type, code)
- `GET /api/survey-points/<point_id>` - Get point details
- `POST /api/survey-points` - Create new point
- `PUT /api/survey-points/<point_id>` - Update point
- `DELETE /api/survey-points/<point_id>` - Delete point
- `GET /api/survey-points/by-project/<project_id>` - Points for project
- `GET /api/survey-points/control` - All control points
- `POST /api/survey-points/import` - Bulk import from CSV/collector

### Site Features
- `GET /api/site-trees` - List trees
- `GET /api/utility-structures` - List structures (filterable by type, system)
- `GET /api/surface-features` - List surface features

### Alignments
- `GET /api/alignments` - List alignments
- `GET /api/alignments/<alignment_id>/pis` - Get PI geometry
- `GET /api/alignments/<alignment_id>/profile` - Get vertical profile
- `GET /api/alignments/<alignment_id>/cross-sections` - Get sections

### Utilities
- `GET /api/utility-lines` - List utility lines (filter by type, owner)
- `GET /api/utility-lines/<line_id>/connectivity` - Get connected elements
- `GET /api/utility-networks/trace` - Network trace analysis

### Earthwork
- `GET /api/earthwork-quantities` - Volume summary by alignment
- `GET /api/earthwork-balance/<alignment_id>` - Mass haul diagram data

### Parcels
- `GET /api/parcels` - List parcels (filter by owner, APN)
- `GET /api/parcels/<parcel_id>/corners` - Get surveyed corners
- `GET /api/easements` - List easements

### Survey Observations
- `GET /api/observations` - List observations (filter by session, date)
- `GET /api/traverse-loops` - List traverse loops with closure stats
- `POST /api/observations/import` - Import raw data collector files

---

## Production Recommendations

### 1. Indexes
- All geometry columns have GiST indexes ✓
- Foreign keys are indexed ✓
- Add composite indexes for common query patterns:
  - `(project_id, point_type)` on survey_points
  - `(project_id, utility_type)` on utility_lines
  - `(alignment_id, station)` on cross_sections

### 2. Data Validation
- Point number uniqueness per project (already enforced via unique index)
- Coordinate system consistency checks
- Elevation range validation (detect outliers)
- Traverse closure tolerance checks
- Network connectivity validation

### 3. Computed Columns / Views
- Create materialized view for point density heatmaps
- Create view for "active control network" (is_active = TRUE)
- Create view for "proposed vs existing utilities"
- Compute earthwork totals by project

### 4. Triggers
- Auto-update `updated_at` timestamp
- Auto-calculate line lengths from geometry
- Auto-update parcel area from geometry
- Cascade point supersession updates

### 5. Permissions
- Survey crew: Read/write survey_points, survey_observations
- Design engineers: Read/write alignments, cross_sections, earthwork
- CAD technicians: Read survey data, write drawings
- Project managers: Read all, approve control networks

### 6. Performance
- Partition large tables by project_id if projects are massive
- Use PostGIS spatial indexes for proximity queries
- Cache frequently accessed control networks
- Batch import survey points (1000+ at a time)

---

## Migration Checklist

- [x] Create survey_points table with PostGIS geometry
- [x] Create survey_control_network and control_point_membership tables
- [x] Create site_features tables (trees, structures, surface features)
- [x] Create alignment tables (horizontal, vertical, PIs, PVIs)
- [x] Create cross_sections and cross_section_points tables
- [x] Create earthwork_quantities and earthwork_balance tables
- [x] Create utility_lines, utility_network_connectivity, utility_service_connections
- [x] Create parcels, parcel_corners, easements, right_of_way tables
- [x] Create survey_observations, traverse_loops, traverse_loop_observations
- [x] Establish foreign key relationships
- [x] Create spatial indexes (GiST)
- [x] Create unique constraints (point numbers, etc.)
- [ ] Implement Pydantic models for request/response validation
- [ ] Create SQLAlchemy ORM models with relationships
- [ ] Implement API routes for all CRUD operations
- [ ] Add business logic (coordinate transformations, earthwork calcs, network analysis)
- [ ] Build frontend components for survey data entry
- [ ] Integrate with CAD import/export workflows
- [ ] Test spatial queries and performance
- [ ] Document API in Swagger/OpenAPI
- [ ] Add data validation and error handling
- [ ] Implement user permissions and access control

---

## Related Documentation

- **MIGRATION_PROJECTS_MANAGER.md**: Parent projects that contain survey data
- **MIGRATION_DRAWINGS_MANAGER.md**: Drawings that reference survey points
- **MIGRATION_DXF_TOOLS.md**: CAD entity storage and block symbols for survey points

---

## Notes

This survey module represents a major expansion of the ACAD-GIS database schema, adding 25+ new tables specifically designed for civil/survey engineering workflows. The schema is designed to be the ultimate source of truth for project survey data while maintaining tight integration with the existing CAD drawing management system.

Key design principles:
1. **Flexibility**: JSONB attributes allow project-specific extensions
2. **Traceability**: Survey observations link to final coordinates
3. **Quality**: Accuracy metrics and adjustment data preserved
4. **Integration**: All data links to projects and drawings
5. **Standards**: PostGIS for spatial data, UUIDs for keys, proper indexing

The schema supports both traditional survey workflows (control networks, traverse loops) and modern workflows (GPS-RTK, real-time data collectors). It enables advanced GIS analysis while preserving the ability to round-trip to CAD formats.
