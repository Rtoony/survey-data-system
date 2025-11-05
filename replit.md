# ACAD-GIS: AI-First CAD/GIS System

## Overview

ACAD-GIS is an AI-first, database-centric CAD/GIS system designed for machine learning, embeddings, and GraphRAG. It replaces traditional file-based CAD workflows with a PostgreSQL/PostGIS database optimized for AI understanding and semantic reasoning.

**Core Value Proposition:**
- **Unified Entity Model:** Canonical identity for every CAD element.
- **Centralized Embeddings:** Versioned vector embeddings for semantic search.
- **Explicit Graph Edges:** Pre-computed spatial and engineering relationships for GraphRAG.
- **ML Feature Engineering:** Built-in tables for spatial statistics, network metrics, and predictions.
- **Hybrid Search:** Combines full-text, vector similarity, and quality scoring.

**Key Applications:**
- **Schema Explorer & Data Manager:** Administrative tool for schema visualization and data management.
- **CAD Standards Portal:** User-friendly reference for AI-optimized CAD standards.
- **Python ML Tools:** Intelligent CAD operations leveraging the AI-optimized database.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

**Core Technologies:**
- **Database:** PostgreSQL 12+ with PostGIS 3.3+ and pgvector 0.8+.
- **AI/ML Stack:** Vector embeddings (1536 dimensions), GraphRAG, full-text search.
- **Web Framework:** Flask (Python) for server-rendered HTML and JSON APIs.
- **Frontend:** Jinja2 templating, Mission Control-themed CSS, vanilla JavaScript.
- **Spatial:** PostGIS with SRID 2226 (California State Plane Zone 2, US Survey Feet).

**AI-First Database Architecture:**
- **Unified Entity Registry (`standards_entities`):** Provides canonical identity for all CAD/GIS elements.
- **Centralized Embeddings (`entity_embeddings`):** Stores versioned vector embeddings from multiple models.
- **Graph Edges (`entity_relationships`):** Defines explicit spatial, engineering, and semantic relationships for GraphRAG.
- **Quality Scoring:** `quality_score` column in every table for data quality.
- **Full-Text Search:** `search_vector` tsvector columns with weighted search in all tables.
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
- **Schema Explorer:** Database health checks, schema visualization, project/drawing management.
- **CAD Standards Portal:** Visual, read-only display of CAD standards.
- **Data Manager:** CRUD operations for CAD standards data (Abbreviations, Layers, Blocks, Details) with searching and import/export.
- **DXF Tools:** Full DXF import/export functionality using `ezdxf` with PostGIS GeometryZ.
- **Map Viewer & Export:** Interactive Leaflet map with coordinate transformation, bounding box export to DXF/SHP/PNG, measurement tools, and WFS layer support.
- **Sheet Note Manager:** Backend for managing construction drawing notes with standard libraries and custom overrides.
- **Sheet Set Manager:** System for organizing construction document deliverables and tracking sheet assignments.
- **Survey & Civil Engineering Schema:** Comprehensive database schema for civil/survey data (points, networks, alignments, parcels) utilizing PostGIS PointZ.
- **AI Toolkit:** Python modules and web interface for data ingestion, embedding generation, relationship building, validation, and maintenance.

## External Dependencies

**Python Libraries:**
- `Flask`, `Flask-Caching`, `psycopg2-binary`, `python-dotenv`, `flask-cors`, `ezdxf`, `openai`
- **Geospatial:** `pyproj`, `shapely`, `fiona`, `owslib`, `pillow`, `rasterio`

**Database:**
- `PostgreSQL 12+`
- `PostGIS Extension`
- `Supabase` (recommended hosting)

**Frontend Resources (CDNs):**
- `Font Awesome 6.4.0`
- `Google Fonts` (Orbitron, Rajdhani)
- `Vis.js`
- **Mapping:** `Leaflet.js 1.9.4`, `Leaflet.draw 1.0.4`, `Proj4js 2.9.0`, `Turf.js 6.x`

**Environment Configuration:**
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

**Related Systems:**
- **ACAD-GIS FastAPI application:** Main API server sharing the same PostgreSQL/PostGIS database.

## Recent Changes

**November 5, 2025 - Multi-Format Export System - COMPLETE:**
- **Format Selection Modal:** User-friendly modal dialog allows simultaneous export to multiple formats (PNG, DXF, Shapefile, KML) with single-click checkbox selection
- **PNG Export Options:** Checkboxes for north arrow and scale bar overlays within modal, pre-checked for convenience
- **KML Support:** New KML export format using fiona library with proper EPSG:2226 → WGS84 coordinate transformations for Google Earth/Maps compatibility
- **Unified Export API:** New `/api/map-export/create` endpoint handles multi-format exports with correct coordinate system transformations:
  - Fetches features in WGS84 from FeatureServers
  - Transforms ALL features to EPSG:2226 (Point, Polygon, LineString and Multi* variants)
  - DXF/Shapefile receive EPSG:2226 data for CAD accuracy
  - KML receives EPSG:2226 data, then service transforms to WGS84 for standard compliance
  - PNG uses EPSG:2226 bbox for accurate scale bar calculations
- **Production Ready:** Complete coordinate transformation pipeline architect-reviewed and verified for all formats

**November 5, 2025 - Map Viewer Export Polish - COMPLETE:**
- **Professional Layer Styling:** Industry-standard color schemes for all 11 Sonoma County layers (parcels=red, buildings=gray, roads=yellow, drainage=blue, parks=green, administrative=purple with dashed lines)
- **Export Area Validation:** Real-time area calculation using EPSG:2226 for survey-grade accuracy with three-tier warning system (normal/warning/error states), prevents exports over 2M sq ft (46 acres) to protect server performance
- **Professional PNG Overlays:** Enhanced map exports with compass rose north arrow (4 cardinal points, circular border) and accurate scale bar (checkered pattern, automatic unit selection feet/miles, proportional to actual export size)
- **Production Ready:** All features architect-reviewed and verified for accuracy, proper coordinate handling, and CAD/GIS industry standards compliance

**November 5, 2025 - Map Viewer & Export Tool - COMPLETE:**
- **Interactive Web Map:** Fully functional Leaflet.js map viewer at `/map-viewer` with 5 basemap options (OSM, USGS Topo, ESRI Imagery, CartoDB Light/Dark)
- **Coordinate Systems:** Complete EPSG:2226 (CA State Plane Zone 2) support with live coordinate display showing both WGS84 and State Plane coordinates as you move the mouse
- **Drawing Tools:** Leaflet.draw integration for creating bounding boxes to define export areas with automatic area calculation (acres and square feet)
- **Measurement Tools (COMPLETE):** 
  - Distance measurement: Click points to draw lines, shows total length in feet/miles with live updates
  - Area measurement: Click to draw polygons, shows area in square feet/acres with centroid labels
  - Uses Turf.js for accurate geodesic calculations
  - Visual feedback with cyan measurement lines and labels
  - Clear button to remove measurements
- **Address Search (COMPLETE):** Nominatim geocoding with Sonoma County bias, Enter key support, result markers with popups, auto-pan to location
- **Interactive GIS Layer Loading (COMPLETE):**
  - On-demand layer loading: Users check/uncheck boxes to show/hide GIS layers on map
  - Live data from Sonoma County FeatureServers (12 layers: parcels, buildings, roads, etc.)
  - Backend API endpoint (`/api/map-viewer/layer-data/<layer_id>`) handles ESRI JSON to GeoJSON conversion
  - Visual feedback: spinner while loading, feature count display, error handling
  - Feature popups: Click any map feature to see its properties
  - Performance optimized: 1000 feature limit per layer, bbox-based queries
  - Uses `arcgis2geojson` library for robust MultiPolygon and null geometry handling
- **Export Formats:** Complete multi-format export pipeline:
  - **Shapefile:** Proper .shp, .shx, .dbf, .prj files with EPSG:2226 projection
  - **DXF:** AutoCAD-compatible files with organized layers
  - **PNG:** Map images with optional north arrow and scale bar
  - Fixed critical bug: Sonoma County FeatureServers only support `f=json` (ESRI JSON), not `f=geojson`
- **Background Processing:** Asynchronous export jobs with threading, status polling every 2 seconds, download links with 1-hour expiration
- **Database Tables:** `gis_layers` (WFS layer configurations), `export_jobs` (job tracking and status)
- **Database Integration:** Automatic project display when DXF files are imported with bounding boxes
- **Export Service (`map_export_service.py`):** Complete geospatial processing using pyproj (coordinate transforms), shapely (geometry ops), fiona (Shapefile I/O), ezdxf (DXF generation), PIL (map images), arcgis2geojson (ESRI JSON conversion)
- **Initialization Script:** `init_map_viewer_db.py` for easy database setup with sample Sonoma County layer configs

**November 4, 2025 - Complete Intelligent DXF Workflow:**
- **Bidirectional CAD ↔ Database Sync:** Fully functional workflow where database is source of truth and DXF is interchange format (like Git)
- **Intelligent Import:** DXF importer (`dxf_importer.py`) now automatically creates civil engineering objects from CAD layer patterns (e.g., "12IN-STORM" → storm utility line with 12" diameter)
- **Intelligent Export:** DXF exporter (`dxf_exporter.py`) generates CAD files from database objects with proper layer naming (reverse of classification)
- **Change Detection:** Re-import workflow (`dxf_change_detector.py`) detects geometry changes, layer changes, new entities, and deletions using SHA256 geometry hashing
- **Complete API:** Four REST endpoints for intelligent workflow:
  - `POST /api/dxf/import-intelligent` - Import with object creation
  - `POST /api/dxf/export-intelligent` - Export project to DXF
  - `POST /api/dxf/reimport` - Re-import with change detection
  - `GET /api/dxf/sync-status/<drawing_id>` - Check sync status
- **Round-trip Support:** app → CAD → app with automatic merging of changes, property updates, and new entity creation
- **Architect Reviewed:** All components verified for correctness, transaction safety, and complete bidirectional sync

**October 31, 2025 - Sidebar Navigation Implementation:**
- Replaced horizontal navigation bar with collapsible vertical sidebar to address navigation scaling issues
- Organized navigation into logical groups: Database, AI Tools, CAD Tools, Projects, Information
- Implemented responsive design with auto-collapse on mobile (<768px) and overlay expansion
- Added dynamic header height tracking using CSS variables and JavaScript for proper positioning at all viewport sizes
- Toggle state persists via localStorage across sessions
- Mobile-first approach: sidebar starts collapsed on narrow screens, expands to overlay on toggle
- Desktop behavior: sidebar toggles between 250px (expanded) and 70px (icons-only)

**October 30, 2025**

**Complete AI Toolkit Built with Safety Guardrails:**
- Created 5 Python modules: ingestion, embeddings, relationships, validation, maintenance
- Added 15 REST API endpoints at `/api/toolkit`
- Built web interface at `/toolkit` for visual management
- Created 5 example scripts with full documentation
- Created comprehensive health check system testing all modules
- All tools ready for data population when CAD standards are finalized

**Interactive AI Visualizations Added:**
- **Knowledge Graph Visualization (`/graph`):** Interactive Vis.js graph showing entity relationships with color-coded edges (spatial=blue, semantic=green, engineering=orange), node details panel, zoom/pan controls, and relationship filtering
- **Quality Dashboard (`/quality-dashboard`):** Real-time metrics showing embedding coverage percentage, relationship density, orphaned entities, quality score distribution, relationship breakdown by type, and missing embeddings by entity type
- **API Endpoints:** Added `/api/toolkit/graph/data` for graph nodes/edges and `/api/toolkit/quality/metrics` for dashboard metrics
- **Navigation Integration:** Added graph and dashboard links to main navigation menu for easy access

**Operational Safety Features Added:**
- **Embedding Cost Control:** $100 hard cap, warnings at $50/$75/$90, dry-run preview mode
- **Import Safety:** Idempotent natural keys, preview mode, before/after counts, PostGIS geometry validation
- **Health Checks:** 12 automated tests covering database, modules, and data round-trips
- **Web UI Safety:** Confirmation prompts for costly operations, real-time cost tracking
- **Testing Documentation:** Complete safety guide with pre-flight checklist, rollback procedures, emergency protocols

**Key Documentation:**
- `DATABASE_ARCHITECTURE_GUIDE.md` - Complete 12,000-word technical reference of AI-first architecture
- `TESTING_SAFETY_GUIDE.md` - Safe testing workflows with budget management and rollback procedures
- `TESTING_WORKFLOW.md` - Comprehensive step-by-step guide for testing all toolkit features (7 phases)
- `TOOLKIT_SETUP_COMPLETE.md` - Toolkit usage guide and quick reference
- `DOCUMENTATION_INDEX.md` - Navigation hub for all 9 documentation files
- `tools/README.md` - Module reference
- `examples/README.md` - Example scripts