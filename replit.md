# ACAD-GIS: AI-First CAD/GIS System

## Overview

ACAD-GIS is an AI-first, database-centric CAD/GIS system designed for machine learning, embeddings, and GraphRAG. It replaces traditional file-based CAD workflows with a PostgreSQL/PostGIS database optimized for AI understanding and semantic reasoning. Its core value lies in providing a unified entity model, centralized embeddings, explicit graph edges for GraphRAG, and built-in ML feature engineering capabilities, enabling hybrid search across CAD/GIS data. Key applications include a Schema Explorer, CAD Standards Portal, and Python ML Tools for intelligent CAD operations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

**Core Technologies:**
- **Database:** PostgreSQL 12+ with PostGIS 3.3+ and pgvector 0.8+.
- **AI/ML Stack:** Vector embeddings (1536 dimensions), GraphRAG, full-text search.
- **Web Framework:** Flask (Python) for server-rendered HTML and JSON APIs.
- **Frontend:** Jinja2 templating, Mission Control-themed CSS, vanilla JavaScript.
- **Spatial:** PostGIS with SRID 2226 (California State Plane Zone 2, US Survey Feet) for GIS data and SRID 0 for CAD data.

**AI-First Database Architecture:**
- **Unified Entity Registry (`standards_entities`):** Canonical identity for all CAD/GIS elements.
- **Centralized Embeddings (`entity_embeddings`):** Stores versioned vector embeddings.
- **Graph Edges (`entity_relationships`):** Defines explicit spatial, engineering, and semantic relationships for GraphRAG.
- **Quality Scoring:** `quality_score` column for data quality assessment.
- **Full-Text Search:** `search_vector` tsvector columns with weighted search.
- **JSONB Attributes:** Flexible metadata storage in `attributes` columns.
- **Vector Indexing:** IVFFlat indexes for fast similarity search.
- **Spatial Indexing:** GIST indexes on PostGIS geometry columns.

**Architectural Patterns & Decisions:**
- **AI-First Design:** Database schema optimized for ML and LLM understanding.
- **Graph Database Patterns:** Explicit relationship tables for GraphRAG multi-hop queries.
- **Spatial-Semantic Fusion:** Combines PostGIS spatial operations with vector similarity search.
- **Quality-Driven:** Entities have quality scores based on completeness, embeddings, and relationships.
- **Server-Side Rendering:** Flask serves Jinja2 templates, augmented by client-side JavaScript.
- **Materialized Views:** Pre-computed views for fast AI queries (e.g., `mv_survey_points_enriched`, `mv_entity_graph_summary`, `mv_spatial_clusters`).

**Key Features & Design:**
- **Schema Explorer & Data Manager:** Tools for schema visualization, data management, and CRUD operations for CAD standards.
- **CAD Standards Portal:** Visual, read-only display of AI-optimized CAD standards.
- **DXF Tools:** Full DXF import/export with intelligent object creation, change detection, and bidirectional sync using `ezdxf` and PostGIS GeometryZ. Supports local coordinate systems (SRID 0).
- **Map Viewer & Export:** Interactive Leaflet map with coordinate transformation, bounding box export (DXF/SHP/PNG/KML), measurement tools, address search, and WFS layer support. Displays user PostGIS layers and external data with professional styling and background processing for exports.
- **Sheet Note Manager & Sheet Set Manager:** Backend systems for managing construction drawing notes and organizing deliverables.
- **Survey & Civil Engineering Schema:** Comprehensive database schema for civil/survey data.
- **AI Toolkit:** Python modules and web interface for data ingestion, embedding generation, relationship building, validation, and maintenance, including cost control and import safety.
- **Interactive AI Visualizations:** Knowledge Graph Visualization (Vis.js) and a Quality Dashboard.
- **Sidebar Navigation:** Collapsible vertical sidebar for improved navigation and responsive design.

## External Dependencies

**Python Libraries:**
- `Flask`, `Flask-Caching`, `psycopg2-binary`, `python-dotenv`, `flask-cors`, `ezdxf`, `openai`, `pyproj`, `shapely`, `fiona`, `owslib`, `pillow`, `rasterio`, `arcgis2geojson`.

**Database:**
- `PostgreSQL 12+`
- `PostGIS Extension`
- `Supabase` (recommended hosting).

**Frontend Resources (CDNs):**
- `Font Awesome 6.4.0`
- `Google Fonts` (Orbitron, Rajdhani)
- `Vis.js`
- `Leaflet.js 1.9.4`, `Leaflet.draw 1.0.4`, `Proj4js 2.9.0`, `Turf.js 6.x`.

**Environment Configuration:**
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

**Related Systems:**
- **ACAD-GIS FastAPI application:** Main API server sharing the same PostgreSQL/PostGIS database.

## Recent Changes

**November 6, 2025 - Map Viewer "Linework" Unification & DXF Export Enhancement:**
- **Unified Linework Display:** Map viewer now groups LINE/ARC/LWPOLYLINE into single "Linework" entity type
  - Simplified UX with single checkbox instead of 3 separate entity types
  - Backend returns unified type using SQL CASE statement (no geometry changes)
  - Frontend automatically renders whatever backend provides (generic implementation)
- **DXF Layer Export Fixed:** Bounding box exports now automatically include DXF-imported layers
  - Replaced placeholder data with real database queries via `MapExportService.fetch_drawing_entities_by_layer()`
  - Queries `drawing_entities` table with ST_Intersects spatial filter
  - Groups features by layer_name for organized SHP/KML/DXF outputs
  - Tested: 243 features across 8 DXF layers successfully exported
- **3D Geometry Transformation Fixed:** Export now handles LineStringZ (3D coordinates) correctly
  - Fixed "too many values to unpack" error in coordinate transformation
  - Properly extracts (x, y) from 3D coordinates, ignoring Z during EPSG transforms
  - Preserves survey-grade accuracy: EPSG:2226 ↔ EPSG:4326 transformations validated
  - Architect review confirmed: 0.000000ft coordinate preservation maintained
- **Status:** All 7 tasks complete. Export pipeline delivers survey-grade accuracy for staking and final CAD deliverables.

**November 6, 2025 - Complete DXF Import & Map Viewer Fix for Local CAD Coordinates:**
- **Critical SRID Fix for DXF Import:** Changed ALL geometry insertions from SRID 2226 to SRID 0
  - Fixed: drawing_entities, drawing_text, drawing_hatches, block_inserts (all geometry tables)
  - **Impact:** AutoCAD DXF files with local coordinates (0-100 scale) now import correctly
  - Verified: Zero SRID 2226 references remaining in dxf_importer.py
- **Complete Linetype Table Fix:** Fixed ALL references from non-existent `linetype_standards` to `linetypes`
  - app.py: API endpoint query ✅
  - dxf_lookup_service.py: Linetype lookup during import ✅
  - Added `is_active = true` filter for data consistency
- **Map Viewer SRID 0 Support:** Backend and frontend now handle local CAD coordinates properly
  - **Backend (app.py):** CASE statement in `get_project_entities` checks SRID before transformation
  - Only transforms geographic coordinates (SRID 2226) to WGS84
  - Returns SRID 0 geometries without transformation, includes `srid` property in response
  - `get_drawing_extent` returns `bounds: null` for SRID 0, preventing transform errors
  - **Frontend (map_viewer_simple.html):** Detects SRID 0 features and shows explanatory alert
  - Explains local coordinates can't display on geographic map
  - Suggests export to DXF or use CAD viewer
  - **Impact:** No more ST_Transform errors, clear user communication
- **Enhanced Error Logging:** Comprehensive error handling for geometry operations
  - Try/catch blocks around all geometry insertions
  - Detailed error messages in import stats['errors'] array
  - Console logging with ERROR/WARNING prefixes for debugging
- **Status:** DXF import working, entities imported correctly, Map Viewer properly handles both local (SRID 0) and geographic (SRID 2226) data

**November 6, 2025 - Gravity Pipe Network Editor Foundation (In Progress):**
- **Database Infrastructure:** New pipe network tracking system created
  - `dxf_entity_links`: Bidirectional DXF↔DB mapping with geometry hashes for change detection
  - `pipe_networks`: Groups pipes/structures into logical networks by project+utility+mode
  - `utility_network_memberships`: Links utility_lines and utility_structures to networks
  - `utility_mode` enum: Added to utility_lines and utility_structures ('gravity', 'pressure', 'bmp')
  - `utility_line_quality`: Validation results storage for network integrity checks
- **Layer Classification Enhancement:** LayerClassifier now detects network mode
  - Gravity mode: STORM/SEWER/SD/SS patterns (e.g., "12IN-STORM", "SD-MH-48")
  - Pressure mode: WATER/GAS/ELECTRIC/FIRE/W/G/E/F patterns (e.g., "W-VALVE-6")
  - BMP mode: BIORETENTION/SWALE/BASIN patterns
  - Block name classification for structure prefixes (SD-MH, SS-MH, W-VALVE, etc.)
- **Intelligent Object Creator:** Auto-creates and assigns networks
  - Sets utility_mode on utility_lines and utility_structures from classification
  - Creates dxf_entity_links with geometry hash SHA-256 for change tracking
  - Auto-creates pipe_networks per (project_id, utility_system, network_mode)
  - Auto-assigns pipes/structures to networks via utility_network_memberships
- **Backend API:** 6 Flask endpoints for network editing
  - GET /api/pipe-networks: List all networks with filters for project_id and mode
  - GET /api/pipe-networks/<id>: Get network details
  - GET /api/pipe-networks/<id>/pipes: Get all pipes with from/to structure info
  - GET /api/pipe-networks/<id>/structures: Get all structures
  - PUT /api/pipe-networks/<id>/pipes/<pipe_id>: Update pipe attributes (preserves geometry)
  - PUT /api/pipe-networks/<id>/structures/<structure_id>: Update structure attributes
- **Frontend UI:** Gravity Network Editor web interface
  - Network selector dropdown filtered to gravity mode
  - Editable tables for structures (rim/invert elevations, sizes, condition)
  - Editable tables for pipes (diameters, materials, inverts, slopes)
  - Static SVG diagram placeholder (bounded to network extents)
  - Save button to persist changes via API
  - Mission Control theme styling with status messages
- **Navigation:** Added "Gravity Network Editor" link to sidebar under CAD Tools
- **Status:** Core UI and API working. **CRITICAL GAP:** DXF re-import bidirectional sync (task 4) not yet implemented - user-edited attributes will be lost on re-import until importer checks dxf_entity_links, compares geometry hashes, and preserves data. Next: Complete task 4 to enable true persistence workflow.

**November 6, 2025 - Bug Fixes: DXF Import and Layer Classification:**
- **Case-Sensitivity Fix in IntelligentObjectCreator:** Fixed geometry type matching bug
  - Problem: DXF importer passed "LineString" (PostGIS format) but code checked for "LINESTRING"
  - Result: No intelligent objects created from imported DXF entities
  - Fix: Added `.upper()` normalization in _create_utility_line, _create_utility_structure, _create_bmp
  - Impact: DXF imports now correctly create utility lines and structures
- **Layer Naming Convention Support:** Added SD/SS/W/G/E/F prefix patterns
  - User's convention: "SD-12IN-PIPE", "SS-MH-48", "W-6IN-WATER"
  - Added pattern: `(SD|SS|W|G|E|F)[-_](\d+)(?:IN|INCH)?[-_]?(PIPE|LINE)`
  - Prefix mapping: SD→Storm, SS→Sanitary, W→Water, G→Gas, E→Electric, F→Fire
  - Updated _classify_utility_line to parse prefix patterns and extract diameter
- **Retroactive Processing:** Created utility to convert existing imports
  - Script: retroactive_network_creation.py
  - Processes drawing_entities that weren't converted due to bugs
  - Successfully created 16 utility_lines from "SD-12IN-PIPE" layer
  - Auto-created "Storm Gravity Network" with all pipes assigned
- **Result:** Gravity Network Editor now functional with user's first DXF import
- **Future Work:** Extend patterns (N-, RW-, P-), add geometry normalization to other object types, create unit tests