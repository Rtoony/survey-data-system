# ACAD-GIS Civil Engineering Domain Model

## Overview

This document explains how the ACAD-GIS system models civil engineering and surveying data, including spatial relationships, network topology, and the connections between survey points, utilities, parcels, alignments, and other infrastructure elements.

---

## Domain Structure

### The Civil Engineering Ecosystem

```
PROJECT
├── SURVEY DATA
│   ├── Survey Points (control, benchmarks, topography)
│   ├── Control Networks (horizontal, vertical)
│   ├── Survey Observations (raw field data)
│   └── Surface Models (TIN/DTM)
│
├── PROPERTY & LEGAL
│   ├── Parcels (property boundaries)
│   ├── Easements
│   └── Right-of-Way
│
├── INFRASTRUCTURE
│   ├── Utility Networks (water, sewer, storm, gas, electric)
│   ├── Roadways & Pavements
│   ├── Structures (buildings, retaining walls)
│   └── Drainage (BMPs, detention ponds)
│
├── DESIGN ELEMENTS
│   ├── Horizontal Alignments (road/utility centerlines)
│   ├── Vertical Profiles
│   ├── Cross-Sections
│   └── Grading Plans
│
└── ANALYSIS & CALCULATIONS
    ├── Earthwork Quantities
    ├── Drainage Calculations
    └── Network Flow Analysis
```

---

## Part 1: Survey Data

### Survey Points

**Purpose:** Store all surveyed points (control, benchmarks, topographic shots, etc.)

```sql
CREATE TABLE survey_points (
    point_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    entity_id UUID REFERENCES standards_entities(entity_id),
    
    -- Point identification
    point_number VARCHAR(50) NOT NULL,
    point_type VARCHAR(50) CHECK (point_type IN (
        'control', 'benchmark', 'monument', 'topo', 'building_corner', 
        'utility', 'tree', 'property_corner', 'temporary'
    )),
    
    -- 3D Coordinates (PostGIS PointZ)
    geometry geometry(PointZ, 2226) NOT NULL,
    
    -- Elevation data
    elevation NUMERIC(10, 3),
    elevation_datum VARCHAR(100),  -- NAVD88, NGVD29, etc.
    
    -- Survey metadata
    description TEXT,
    survey_date DATE,
    surveyor VARCHAR(255),
    instrument_type VARCHAR(100),
    
    -- Accuracy
    horizontal_accuracy NUMERIC(6, 3),  -- feet
    vertical_accuracy NUMERIC(6, 3),    -- feet
    
    -- Point attributes
    attributes JSONB DEFAULT '{}'::jsonb,
    
    -- AI optimization
    quality_score NUMERIC(4, 3),
    search_vector TSVECTOR,
    tags TEXT[],
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_survey_points_geom ON survey_points USING GIST(geometry);
CREATE INDEX idx_survey_points_type ON survey_points(point_type);
CREATE INDEX idx_survey_points_entity ON survey_points(entity_id);
```

### Control Networks

**Purpose:** Organize survey points into control networks for least-squares adjustment.

```sql
CREATE TABLE control_networks (
    network_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    
    network_name VARCHAR(255) NOT NULL,
    network_type VARCHAR(50) CHECK (network_type IN (
        'horizontal', 'vertical', 'combined'
    )),
    
    datum VARCHAR(100),
    coordinate_system_id UUID REFERENCES coordinate_systems(crs_id),
    
    adjustment_date DATE,
    adjustment_method VARCHAR(100),
    adjustment_software VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE control_point_membership (
    membership_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    network_id UUID REFERENCES control_networks(network_id),
    point_id UUID REFERENCES survey_points(point_id),
    
    control_type VARCHAR(50) CHECK (control_type IN (
        'fixed', 'adjusted', 'check'
    )),
    
    weight NUMERIC(5, 2) DEFAULT 1.0,
    is_active BOOLEAN DEFAULT TRUE
);
```

### Survey Observations

**Purpose:** Store raw field measurements (distances, angles, elevations).

```sql
CREATE TABLE survey_observations (
    observation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    
    from_point_id UUID REFERENCES survey_points(point_id),
    to_point_id UUID REFERENCES survey_points(point_id),
    
    observation_type VARCHAR(50) CHECK (observation_type IN (
        'distance', 'angle', 'azimuth', 'elevation_difference', 'GPS_vector'
    )),
    
    measured_value NUMERIC(15, 6),
    units VARCHAR(20),  -- 'feet', 'meters', 'degrees', 'gons'
    
    standard_deviation NUMERIC(10, 6),
    observation_date TIMESTAMP,
    instrument_id VARCHAR(100),
    
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Surface Models

**Purpose:** Manage Digital Terrain Models (DTM) and Triangulated Irregular Networks (TIN).

```sql
CREATE TABLE surface_models (
    surface_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    entity_id UUID REFERENCES standards_entities(entity_id),
    
    surface_name VARCHAR(255) NOT NULL,
    surface_type VARCHAR(50) CHECK (surface_type IN (
        'existing_ground', 'proposed_grade', 'finished_grade', 
        'top_of_curb', 'pavement'
    )),
    
    -- Bounding extent
    extent geometry(PolygonZ, 2226),
    
    -- TIN representation (stored as PostGIS TIN)
    tin_geometry geometry(TINZ, 2226),
    
    -- Statistics
    min_elevation NUMERIC(10, 3),
    max_elevation NUMERIC(10, 3),
    avg_elevation NUMERIC(10, 3),
    triangle_count INTEGER,
    
    -- Source data
    source_point_count INTEGER,
    source_description TEXT,
    created_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Part 2: Property & Legal

### Parcels

**Purpose:** Property boundaries and land ownership.

```sql
CREATE TABLE parcels (
    parcel_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    entity_id UUID REFERENCES standards_entities(entity_id),
    
    -- Parcel identification
    parcel_number VARCHAR(100),
    assessor_parcel_number VARCHAR(100),  -- APN
    
    -- Geometry (closed polygon)
    geometry geometry(PolygonZ, 2226) NOT NULL,
    
    -- Ownership
    owner_name VARCHAR(255),
    owner_address TEXT,
    
    -- Legal description
    legal_description TEXT,
    recorded_document VARCHAR(100),
    recording_date DATE,
    
    -- Area calculations
    area_sqft NUMERIC(15, 3),
    area_acres NUMERIC(10, 4),
    
    -- Zoning
    zoning_code VARCHAR(50),
    land_use VARCHAR(100),
    
    -- AI optimization
    quality_score NUMERIC(4, 3),
    search_vector TSVECTOR,
    tags TEXT[],
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_parcels_geom ON parcels USING GIST(geometry);
CREATE INDEX idx_parcels_apn ON parcels(assessor_parcel_number);
```

### Easements & Rights-of-Way

```sql
CREATE TABLE easements (
    easement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    entity_id UUID REFERENCES standards_entities(entity_id),
    
    easement_type VARCHAR(100) CHECK (easement_type IN (
        'utility', 'access', 'drainage', 'conservation', 'ingress_egress'
    )),
    
    geometry geometry(PolygonZ, 2226) NOT NULL,
    
    grantor VARCHAR(255),
    grantee VARCHAR(255),
    recorded_document VARCHAR(100),
    
    width_feet NUMERIC(10, 2),
    area_sqft NUMERIC(15, 3),
    
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE right_of_way (
    row_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    entity_id UUID REFERENCES standards_entities(entity_id),
    
    row_type VARCHAR(100),  -- 'street', 'highway', 'railroad'
    
    geometry geometry(PolygonZ, 2226) NOT NULL,
    
    controlling_agency VARCHAR(255),
    width_feet NUMERIC(10, 2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Part 3: Utility Networks

### Network Structure (Graph Model)

Utilities are modeled as **directed graphs**:
- **Nodes:** Structures (manholes, vaults, inlets, valves)
- **Edges:** Lines (pipes, cables)

### Utility Lines (Edges)

```sql
CREATE TABLE utility_lines (
    line_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    entity_id UUID REFERENCES standards_entities(entity_id),
    
    -- Line classification
    line_type VARCHAR(100) CHECK (line_type IN (
        'gravity_main', 'pressure_main', 'force_main',
        'storm_drain', 'sanitary_sewer', 'water_distribution',
        'recycled_water', 'gas', 'electric', 'telecom'
    )),
    
    -- 3D Geometry (LineStringZ with invert elevations)
    geometry geometry(LineStringZ, 2226) NOT NULL,
    
    -- Network topology
    upstream_structure_id UUID REFERENCES utility_structures(structure_id),
    downstream_structure_id UUID REFERENCES utility_structures(structure_id),
    
    -- Physical properties
    diameter NUMERIC(10, 2),  -- inches
    material VARCHAR(100),    -- PVC, DI, HDPE, etc.
    pipe_class VARCHAR(50),
    
    -- Hydraulic properties
    slope NUMERIC(6, 4),      -- ft/ft
    length_ft NUMERIC(12, 3),
    
    -- Condition
    install_date DATE,
    condition_rating INTEGER CHECK (condition_rating BETWEEN 1 AND 5),
    
    -- AI optimization
    quality_score NUMERIC(4, 3),
    search_vector TSVECTOR,
    tags TEXT[],
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_utility_lines_geom ON utility_lines USING GIST(geometry);
CREATE INDEX idx_utility_lines_type ON utility_lines(line_type);
CREATE INDEX idx_utility_lines_upstream ON utility_lines(upstream_structure_id);
CREATE INDEX idx_utility_lines_downstream ON utility_lines(downstream_structure_id);
```

### Utility Structures (Nodes)

```sql
CREATE TABLE utility_structures (
    structure_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    entity_id UUID REFERENCES standards_entities(entity_id),
    
    -- Structure classification
    structure_type VARCHAR(100) CHECK (structure_type IN (
        'manhole', 'inlet', 'outlet', 'junction', 
        'catch_basin', 'cleanout', 'valve', 'meter',
        'pump_station', 'tank', 'vault'
    )),
    
    -- 3D Location (PointZ at rim elevation)
    geometry geometry(PointZ, 2226) NOT NULL,
    
    -- Elevations
    rim_elevation NUMERIC(10, 3),
    invert_elevation NUMERIC(10, 3),
    depth_ft NUMERIC(8, 2),
    
    -- Physical properties
    diameter NUMERIC(8, 2),
    material VARCHAR(100),
    
    -- Structure ID
    structure_number VARCHAR(100),
    
    -- Condition
    install_date DATE,
    condition_rating INTEGER CHECK (condition_rating BETWEEN 1 AND 5),
    
    -- AI optimization
    quality_score NUMERIC(4, 3),
    search_vector TSVECTOR,
    tags TEXT[],
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_utility_structures_geom ON utility_structures USING GIST(geometry);
CREATE INDEX idx_utility_structures_type ON utility_structures(structure_type);
```

### Network Analysis Functions

**Find Upstream Network:**
```sql
CREATE OR REPLACE FUNCTION find_upstream_network(start_structure_id UUID)
RETURNS TABLE(
    line_id UUID,
    structure_id UUID,
    distance_from_start NUMERIC,
    hop_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE network AS (
        -- Base case: lines connected to starting structure
        SELECT 
            ul.line_id,
            ul.upstream_structure_id AS structure_id,
            ul.length_ft AS distance,
            1 AS hops
        FROM utility_lines ul
        WHERE ul.downstream_structure_id = start_structure_id
        
        UNION ALL
        
        -- Recursive case: follow upstream
        SELECT 
            ul.line_id,
            ul.upstream_structure_id,
            n.distance + ul.length_ft,
            n.hops + 1
        FROM utility_lines ul
        JOIN network n ON ul.downstream_structure_id = n.structure_id
        WHERE n.hops < 50  -- Prevent infinite loops
    )
    SELECT line_id, structure_id, distance, hops FROM network;
END;
$$ LANGUAGE plpgsql;
```

---

## Part 4: Best Management Practices (BMPs)

### BMPs Table

**Purpose:** Stormwater quality treatment facilities.

```sql
CREATE TABLE bmps (
    bmp_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    entity_id UUID REFERENCES standards_entities(entity_id),
    
    -- BMP classification
    bmp_type VARCHAR(100) CHECK (bmp_type IN (
        'bioretention', 'detention_basin', 'retention_basin',
        'vegetated_swale', 'filter_strip', 'permeable_pavement',
        'constructed_wetland', 'sand_filter', 'oil_water_separator'
    )),
    
    -- Geometry (polygon for area BMPs, point for device BMPs)
    geometry geometry(GeometryZ, 2226) NOT NULL,
    
    -- Sizing
    surface_area_sqft NUMERIC(12, 3),
    volume_cuft NUMERIC(15, 3),
    depth_ft NUMERIC(8, 2),
    
    -- Hydraulic design
    design_storm VARCHAR(50),  -- "2-year, 24-hour", "10-year", etc.
    infiltration_rate NUMERIC(8, 4),  -- inches/hour
    
    -- Treatment capability
    pollutant_removal_rate JSONB,  -- {"TSS": 0.85, "TP": 0.45}
    
    -- Drainage area
    drainage_area_acres NUMERIC(10, 4),
    
    -- Maintenance
    maintenance_frequency VARCHAR(100),
    last_maintenance_date DATE,
    
    -- AI optimization
    quality_score NUMERIC(4, 3),
    search_vector TSVECTOR,
    tags TEXT[],
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Part 5: Alignments & Profiles

### Horizontal Alignments

**Purpose:** Road and utility centerlines defined by stationing.

```sql
CREATE TABLE horizontal_alignments (
    alignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    entity_id UUID REFERENCES standards_entities(entity_id),
    
    alignment_name VARCHAR(255) NOT NULL,
    alignment_type VARCHAR(100) CHECK (alignment_type IN (
        'road_centerline', 'utility_centerline', 'curb_line', 
        'edge_of_pavement', 'right_of_way'
    )),
    
    -- 2D Geometry (horizontal only)
    geometry geometry(LineString, 2226) NOT NULL,
    
    -- Stationing
    start_station NUMERIC(12, 3),  -- e.g., 0+00
    end_station NUMERIC(12, 3),    -- e.g., 25+47.32
    length_ft NUMERIC(12, 3),
    
    -- Design elements (stored as JSON for PI/curve data)
    design_elements JSONB,  -- Points of Intersection, curve data
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Vertical Profiles

**Purpose:** Elevation data along an alignment.

```sql
CREATE TABLE vertical_profiles (
    profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alignment_id UUID REFERENCES horizontal_alignments(alignment_id),
    entity_id UUID REFERENCES standards_entities(entity_id),
    
    profile_name VARCHAR(255),
    profile_type VARCHAR(100) CHECK (profile_type IN (
        'existing_ground', 'proposed_grade', 'top_of_curb', 
        'invert', 'finished_floor'
    )),
    
    -- Profile data (station vs elevation)
    profile_points JSONB,  -- [{"station": 0, "elevation": 125.5}, ...]
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Cross-Sections

**Purpose:** Perpendicular slices along alignments showing cut/fill.

```sql
CREATE TABLE cross_sections (
    section_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alignment_id UUID REFERENCES horizontal_alignments(alignment_id),
    entity_id UUID REFERENCES standards_entities(entity_id),
    
    station NUMERIC(12, 3) NOT NULL,
    
    -- Cross-section geometry (perpendicular to alignment)
    section_geometry geometry(LineStringZ, 2226),
    
    -- Section data (offset vs elevation)
    section_points JSONB,  -- [{"offset": -50, "elevation": 123.2}, ...]
    
    -- Cut/fill calculations
    cut_area_sqft NUMERIC(12, 3),
    fill_area_sqft NUMERIC(12, 3),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cross_sections_alignment ON cross_sections(alignment_id);
CREATE INDEX idx_cross_sections_station ON cross_sections(station);
```

---

## Part 6: Spatial Relationships

### Relationship Examples

#### 1. Survey Point → Parcel (Spatial)

**Query:** Which parcel is this survey point within?

```sql
SELECT 
    p.parcel_number,
    p.owner_name,
    ST_Distance(sp.geometry, p.geometry) AS distance_ft
FROM survey_points sp
JOIN parcels p ON ST_Within(sp.geometry, p.geometry)
WHERE sp.point_id = 'point-uuid';
```

#### 2. Utility Line → Survey Points (Proximity)

**Query:** Find all survey points within 10 feet of a utility line.

```sql
SELECT 
    sp.point_number,
    sp.point_type,
    ST_Distance(ul.geometry, sp.geometry) AS distance_ft
FROM survey_points sp
JOIN utility_lines ul ON ST_DWithin(ul.geometry, sp.geometry, 10)
WHERE ul.line_id = 'line-uuid'
ORDER BY distance_ft;
```

#### 3. BMP → Drainage Area (Tributary)

**Query:** Find all BMPs that serve a specific parcel.

```sql
-- Find BMPs whose drainage area overlaps this parcel
SELECT 
    b.bmp_id,
    b.bmp_type,
    ST_Area(ST_Intersection(b.geometry, p.geometry)) AS overlap_sqft
FROM bmps b
JOIN parcels p ON ST_Intersects(b.geometry, p.geometry)
WHERE p.parcel_id = 'parcel-uuid';
```

#### 4. Alignment → Cross-Sections (Station-Based)

**Query:** Get all cross-sections along an alignment between stations 10+00 and 15+00.

```sql
SELECT 
    cs.section_id,
    cs.station,
    cs.cut_area_sqft,
    cs.fill_area_sqft
FROM cross_sections cs
WHERE cs.alignment_id = 'alignment-uuid'
  AND cs.station BETWEEN 1000.0 AND 1500.0
ORDER BY cs.station;
```

---

## Part 7: Engineering Calculations

### Earthwork Quantities

```sql
CREATE TABLE earthwork_quantities (
    quantity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    
    calculation_type VARCHAR(100) CHECK (calculation_type IN (
        'mass_grading', 'cut_fill', 'trench', 'embankment'
    )),
    
    -- Volumes
    cut_volume_cuyd NUMERIC(15, 3),
    fill_volume_cuyd NUMERIC(15, 3),
    net_volume_cuyd NUMERIC(15, 3),
    
    -- Area
    disturbed_area_acres NUMERIC(10, 4),
    
    -- Associated geometry
    area_geometry geometry(PolygonZ, 2226),
    
    -- Calculation metadata
    calculation_date DATE,
    calculation_method VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Summary: The Complete Civil Engineering Model

```
SURVEY DATA (Foundation)
├── Survey Points (XYZ coordinates)
├── Control Networks (adjustment framework)
├── Surface Models (terrain representation)
└── Observations (raw measurements)
        ↓ (provides base for)
PROPERTY & LEGAL (Context)
├── Parcels (ownership boundaries)
├── Easements (rights)
└── Right-of-Way (public corridors)
        ↓ (constrains)
INFRASTRUCTURE (Physical Assets)
├── Utility Networks (graph topology)
│   ├── Lines (edges)
│   └── Structures (nodes)
├── BMPs (stormwater treatment)
└── Roadways (transportation)
        ↓ (designed using)
DESIGN ELEMENTS (Engineering)
├── Alignments (horizontal paths)
├── Profiles (vertical grades)
├── Cross-Sections (perpendicular slices)
└── Grading Plans (surface manipulation)
        ↓ (results in)
CALCULATIONS (Deliverables)
├── Earthwork Quantities
├── Hydraulic Analysis
└── Cost Estimates
```

**Key Innovation:** All elements are spatially aware (PostGIS), semantically enriched (entity_id + embeddings), and relationship-connected (entity_relationships), enabling both traditional civil engineering analysis AND AI-powered insights.
