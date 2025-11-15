# ACAD-GIS: AI-First CAD/GIS System

## Overview
ACAD-GIS is an AI-first, database-centric CAD/GIS system that replaces traditional file-based CAD workflows with a PostgreSQL/PostGIS database. It is designed for machine learning, embeddings, and GraphRAG, optimizing for AI understanding and semantic reasoning. The system provides a unified entity model, centralized embeddings, explicit graph edges, and built-in ML feature engineering, enabling hybrid search across CAD/GIS data. Key capabilities include a Schema Explorer, CAD Standards Portal, and Python ML Tools for intelligent CAD operations, with a focus on civil engineering and surveying workflows. The project aims to revolutionize CAD/GIS data management by integrating AI into the core architecture, offering enhanced data consistency, semantic understanding, and automated compliance tracking.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

**Core Technologies:**
- **Database:** PostgreSQL 12+ with PostGIS 3.3+ and pgvector 0.8+.
- **AI/ML Stack:** Vector embeddings (1536 dimensions), GraphRAG, full-text search.
- **Web Framework:** Flask (Python) for server-rendered HTML and JSON APIs.
- **Frontend:** Jinja2 templating, Mission Control-themed CSS, vanilla JavaScript, Leaflet.js.
- **Spatial:** PostGIS with SRID 2226 for GIS and SRID 0 for CAD data.

**AI-First Database Architecture:**
- **Unified Entity Registry:** Canonical identity for all CAD/GIS elements.
- **Centralized Embeddings:** Stores versioned vector embeddings.
- **Graph Edges:** Defines explicit spatial, engineering, and semantic relationships for GraphRAG.
- **Quality Scoring:** `quality_score` column for data quality assessment.
- **Full-Text Search:** `search_vector` tsvector columns.
- **JSONB Attributes:** Flexible metadata storage.
- **Vector and Spatial Indexing:** IVFFlat and GIST indexes for fast similarity and spatial search.

**Architectural Patterns & Decisions:**
- **AI-First Design:** Database schema optimized for ML and LLM understanding, enabling GraphRAG for multi-hop queries and hybrid search.
- **Quality-Driven:** Entities have quality scores based on completeness, embeddings, and relationships.
- **Server-Side Rendering:** Flask serves Jinja2 templates, augmented by client-side JavaScript.
- **Materialized Views:** Pre-computed views for fast AI queries.
- **Modular Standards Management:** Separation of "Standards Library" from "Project Operations" with clear navigation and compliance tracking.
- **Database-Driven Vocabulary:** Comprehensive, database-backed controlled vocabulary system for CAD elements with full CRUD.
- **CAD Layer Naming Standards:** Database-driven classifier for CAD layer names.
- **Mission Control Design System:** Centralized design system with reusable classes, variables, and a cyan/neon color palette.
- **Horizontal Navigation Architecture:** Sticky horizontal navbar with 10 dropdown menus and 41 navigation items.
- **Projects Only System (Nov 2025):** Complete migration from "Projects + Drawings" architecture to "Projects Only" system. DXF imports now create entities directly at project level without requiring drawing files. Hybrid intelligent object creation system automatically classifies high-confidence entities (≥0.7 confidence) into specific types (utility_lines, bmps, structures) while flagging low-confidence entities as generic_objects for manual review and reclassification. All entity links support project-level imports (drawing_id can be NULL) with proper unique constraints and database triggers.
- **Projects Navigation Restructure:** Unified projects functionality under `/projects` route with search, CRUD, and individual project overviews.
- **Specialized Tools Registry:** Database-driven system linking CAD object types to interactive management tools.

**Key Features & Design:**
- **Standards Management:** Two dedicated interfaces with clean separation:
  - **CAD Layer Vocabulary** (`/standards/layer-vocabulary`): Manages CAD naming standards vocabulary (Disciplines, Categories, Objects, Phases, Geometries) with full CRUD operations.
  - **Reference Data Hub** (`/standards/reference-data`): Manages 8 types of project-agnostic reference data with full CRUD: (1) CAD Standards (Blocks, Hatches, Linetypes, Text Styles, Dimension Styles, Materials, Details, Standard Notes, Abbreviations) via iframe-embedded secondary navigation, (2) Entity Registry for tracking all database entities, (3) Clients, (4) Vendors, (5) Municipalities, (6) Coordinate Systems, (7) Survey Point Descriptions, (8) GIS Data Layers. All data is database-backed with many-to-many relationships via junction tables (project_clients, project_vendors, project_municipalities).
- **Schema Explorer & Data Manager:** CRUD operations for CAD standards and vocabulary inline editing.
- **Schema Visualization Suite:** Multiple database schema visualization tools including a classic table browser, relationship diagram, and an optimized knowledge graph using Cytoscape.js.
- **CAD Standards Portal:** Visual, read-only display of AI-optimized CAD standards.
- **Standards Mapping Framework:** 11-table database schema with 5 name mapping managers supporting bidirectional DXF↔Database translation.
- **Project Context Mapping Manager:** Manages 6 relationship types.
- **Standards Documentation Export:** Generates client handoffs and training materials.
- **DXF Tools:** Full DXF import/export with intelligent object creation, change detection, and bidirectional sync, including survey-grade 3D elevation preservation.
- **Z-Value Stress Test:** Interactive web interface and CLI tool for proving XYZ coordinate preservation over multiple import/export cycles across various SRIDs, ensuring perfect precision.
- **Map Viewer & Export:** Interactive Leaflet map with coordinate transformation, bounding box export, and measurement tools.
- **Entity Viewer:** Lightweight 2D viewer for project entities with SVG rendering, supporting 8 entity types, multi-select filters, and dynamic legend.
- **Network Managers Suite:** Unified framework of specialized manager tools (Gravity Pipe, Pressure Pipe, BMP Manager) following the Entity Viewer pattern.
- **Unified Batch CAD Import Tool:** Productivity tool for batch importing Blocks, Details, Hatches, and Linetypes from DXF files.
- **Batch Point Import Tool:** Survey point import tool for PNEZD text files with coordinate system selection, automatic transformation, and conflict detection.
- **Survey Code Library Manager:** AI-first survey point code system replacing arbitrary text descriptions with structured, machine-parsable codes that drive automatic CAD generation.
- **Survey Code Testing Interface:** Comprehensive 4-tab testing and validation system for survey codes, including single code parsing, field shot simulation, batch validation, and connectivity rules documentation.
- **Survey Point Manager:** Comprehensive point management interface for imported survey data with filtering, multi-select, and soft-delete capabilities.
- **Project Usage Tracking Dashboard:** Analytics on project/layer/block/note usage patterns.
- **Civil Project Manager:** Comprehensive project overview dashboard with 5 tabs and a metadata-driven CRUD architecture for managing project-specific attachments.
- **Sheet Note Manager:** Project-centric note management system with two-panel layout (Standard Notes Library and Project Notes). Supports inline editing with automatic modified copy creation for standard notes, custom note creation with required justification, and full deviation tracking. Features source_type-based badges (Standard/Modified/Custom) and project-level note set organization without drawing dependencies.
- **Object Reclassifier Tool:** Interactive UI for reviewing and reclassifying unclassified or low-confidence DXF entities. Features project-based filtering, confidence threshold controls, real-time statistics, and one-click reclassification to specific object types (utility_line, utility_structure, bmp, alignment, surface_model, survey_point, site_tree). Supports bulk approval, ignore, and custom reclassification with notes tracking.
- **AI Toolkit:** Python modules and web interface for data ingestion, embedding generation, relationship building, validation, and maintenance.
- **Interactive AI Visualizations:** Knowledge Graph Visualization and a Quality Dashboard.

## External Dependencies

**Python Libraries:**
- `Flask`, `Flask-Caching`, `psycopg2-binary`, `python-dotenv`, `flask-cors`, `ezdxf`, `openai`, `pyproj`, `shapely`, `fiona`, `owslib`, `pillow`, `rasterio`, `arcgis2geojson`, `openpyxl`, `weasyprint`.

**Database:**
- `PostgreSQL 12+`
- `PostGIS Extension`

**Frontend Resources (CDNs):**
- `Font Awesome 6.4.0`
- `Google Fonts`
- `Vis.js`
- `Cytoscape.js 3.28.1`
- `Leaflet.js 1.9.4`, `Leaflet.draw 1.0.4`, `Proj4js 2.9.0`, `Turf.js 6.x`.

**Related Systems:**
- ACAD-GIS FastAPI application (main API server).

## Recent Major Changes (November 2025)

### Projects Only System Migration (COMPLETED)

The system has been completely migrated from a "Projects + Drawings" architecture to a streamlined "Projects Only" system. All drawing-centric UI elements and APIs have been replaced with project-centric equivalents:

**Core Changes:**
1. **Direct Project-Level Entities:** DXF imports now create entities directly at the project level without requiring intermediate drawing files.
2. **Hybrid Classification System:** Intelligent object creation with automatic classification for high-confidence entities (≥0.7) and manual review workflow for low-confidence entities.
3. **Generic Objects Table:** New `generic_objects` table stores unclassified/low-confidence DXF entities with review workflow (pending/approved/reclassified/ignored statuses).
4. **Flexible Entity Links:** `dxf_entity_links` table updated to support both legacy drawing-level and new project-level imports with drawing_id as nullable.
5. **Reclassification API:** Complete REST API for listing, reclassifying, approving, and ignoring generic objects with proper status transitions and validation.

**Database Schema Updates:**
- `generic_objects` table with PostGIS geometry, review workflow, confidence tracking, and full-text search
- Partial unique index on `dxf_entity_links` for project-level imports: `(project_id, dxf_handle) WHERE drawing_id IS NULL`
- Updated `IntelligentObjectCreator` to handle low-confidence classifications with ST_GeomFromText(wkt, 2226)
- All intelligent object tables include proper geometry handling and entity link creation

**New Tools:**
- **Object Reclassifier UI** (`/tools/object-reclassifier`): Interactive tool for reviewing and categorizing generic objects
- **Intelligent Objects Map API** (`/api/projects/<id>/intelligent-objects-map`): Separate endpoint for displaying classified objects vs raw DXF geometry
- **Enhanced Project Statistics** (`/api/projects/<id>/statistics`): Now includes intelligent object counts by type

**Migration Path:**
- Existing drawing-based projects continue to work (backward compatible)
- New imports automatically use project-level linking
- No data loss - unclassified entities saved for manual review instead of being dropped

**UI/API Migration (November 2025):**
- **Usage Dashboard:** All drawing-centric metrics replaced with project-centric equivalents
  - "Total Drawings" → "Total Projects"
  - "Avg Entities/Drawing" → "Avg Entities/Project"
  - "Most Accessed Drawings" → "Most Active Projects"
  - "Recent Drawing Activity" → "Recent Project Activity"
- **API Endpoints Updated:**
  - `/api/usage/summary`: Now returns `total_projects`, `avg_entities_per_project`
  - `/api/usage/top-projects`: New endpoint replacing top-drawings
  - `/api/usage/recent-activity`: Enhanced with entity counts per project

### Documentation Refresh (November 15, 2025)

Complete documentation update replacing deprecated "Bulk Standards Editor" terminology with "CAD Layer Vocabulary":

**Files Updated:**
- README.md: Updated tool references, added Reference Data Hub description, refreshed date
- CAD_STANDARDS_GUIDE.md: Replaced 6 instances of "Bulk Standards Editor" with "CAD Layer Vocabulary"
- STANDARDS_CONFORMANCE_PATTERN.md: Updated date to November 15, 2025
- AI_DATABASE_OPTIMIZATION_GUIDE.md: Updated date to November 15, 2025
- docs/CAD_LAYER_NAMING_STANDARDS.md: Verified current (no changes needed)

**Verification:**
- Zero instances of deprecated terminology remain in markdown files
- All documentation dates current to November 15, 2025
- Terminology consistent across all project documentation
  - `/api/projects/<id>/statistics`: Removed `drawing_count`, consolidated intelligent object counts using efficient UNION ALL query
  - `/api/usage/top-layers`: Verified to return project-centric metrics
- **Database Queries:** All APIs now query `projects`, `drawing_entities`, and intelligent object tables directly, avoiding deprecated `drawings` table
- **Project Overview:** Map placeholder text updated to reference DXF imports instead of drawings

### CAD Standards Consolidation (November 15, 2025)

Migrated Data Manager tools into Reference Data Hub as a new "CAD Standards" tab to consolidate all standards management in one location:

**UI Changes:**
1. **New CAD Standards Tab:** Added to Reference Data Hub (`/standards/reference-data`) with secondary vertical navigation for 9 tools:
   - Blocks Manager (preloaded)
   - Hatches Manager (lazy-loaded)
   - Linetypes Manager (lazy-loaded)
   - Text Styles Manager (lazy-loaded)
   - Dimension Styles Manager (lazy-loaded)
   - Materials Manager (lazy-loaded)
   - Details Manager (lazy-loaded)
   - Standard Notes Manager (lazy-loaded)
   - Abbreviations Manager (lazy-loaded)

2. **Iframe Embedding:** Each tool embedded in isolated iframe to prevent script conflicts and modal ID collisions. Lazy-loading implemented using data-src promotion on first click.

3. **Navigation Cleanup:** Removed "Data Manager" dropdown from horizontal navbar (templates/base.html)

**Backend Changes:**
1. **Route Cleanup:** Removed obsolete routes from app.py:
   - `/data-manager` (home page)
   - `/data-manager/layers` (page route)
   - All layers API endpoints (GET, POST, PUT, DELETE, import-csv, export-csv)

2. **Preserved Routes:** Kept all other `/data-manager/{tool}` routes for iframe embedding:
   - `/data-manager/abbreviations`
   - `/data-manager/blocks`
   - `/data-manager/details`
   - `/data-manager/hatches`
   - `/data-manager/linetypes`
   - `/data-manager/text-styles`
   - `/data-manager/dimension-styles`
   - `/data-manager/materials`
   - `/data-manager/standard-notes`

**Design Decisions:**
- **Projects-Only Compatible:** All migrated tools verified to be project-agnostic with no drawing dependencies
- **Iframe Isolation:** Prevents JavaScript initialization conflicts and CSS ID collisions
- **Two-Tier Navigation:** Avoids overwhelming 16-tab horizontal navbar by using secondary navigation within CAD Standards tab
- **Lazy Loading:** Improves initial page load by only loading iframes when clicked
- **Removed Layers Tool:** Obsolete - replaced by CAD Layer Vocabulary system

**Migration Status:**
- ✅ All 9 CAD Standards tools accessible via Reference Data Hub
- ✅ Data Manager dropdown removed from navbar
- ✅ Obsolete layers routes removed
- ✅ Backward compatibility maintained (existing routes preserved for iframe embedding)