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