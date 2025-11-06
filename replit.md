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
- **DXF Tools:** Full DXF import/export functionality with intelligent object creation and change detection using `ezdxf` and PostGIS GeometryZ. Includes bidirectional sync and a comprehensive API for intelligent import, export, and re-import with change detection.
- **Map Viewer & Export:** Interactive Leaflet map with coordinate transformation, bounding box export to DXF/SHP/PNG/KML, measurement tools, address search, and WFS layer support. Features professional styling, area validation, and background processing for exports. Displays user's PostGIS database layers alongside external data.
- **Sheet Note Manager:** Backend for managing construction drawing notes.
- **Sheet Set Manager:** System for organizing construction document deliverables.
- **Survey & Civil Engineering Schema:** Comprehensive database schema for civil/survey data.
- **AI Toolkit:** Python modules and web interface for data ingestion, embedding generation, relationship building, validation, and maintenance. Includes operational safety features like embedding cost control, import safety (idempotent natural keys, preview mode), health checks, and a web UI with confirmation prompts.
- **Interactive AI Visualizations:** Knowledge Graph Visualization using Vis.js and a Quality Dashboard showing real-time metrics.
- **Sidebar Navigation:** Collapsible vertical sidebar for improved navigation, with responsive design and state persistence.

## External Dependencies

**Python Libraries:**
- `Flask`, `Flask-Caching`, `psycopg2-binary`, `python-dotenv`, `flask-cors`, `ezdxf`, `openai`, `pyproj`, `shapely`, `fiona`, `owslib`, `pillow`, `rasterio`, `arcgis2geojson`

**Database:**
- `PostgreSQL 12+`
- `PostGIS Extension`
- `Supabase` (recommended hosting)

**Frontend Resources (CDNs):**
- `Font Awesome 6.4.0`
- `Google Fonts` (Orbitron, Rajdhani)
- `Vis.js`
- `Leaflet.js 1.9.4`, `Leaflet.draw 1.0.4`, `Proj4js 2.9.0`, `Turf.js 6.x`

**Environment Configuration:**
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

**Related Systems:**
- **ACAD-GIS FastAPI application:** Main API server sharing the same PostgreSQL/PostGIS database.

## Recent Changes

**November 6, 2025 - Map Viewer Entity Rendering & Project Area Boxes - COMPLETE:**
- **3D Coordinate Fix:** Added `stripZCoordinates()` function to convert 3D GeoJSON coordinates to 2D before passing to Leaflet, fixing LWPOLYLINE rendering issues
- **Project Area Toggle:** Added "Show Project Areas" checkbox in sidebar to display orange dashed rectangles for all project bounding boxes
- **Visual Preview:** Project area boxes provide quick visual overview of project locations before loading detailed entities
- **Coordinate Transformation:** Project boxes properly transform EPSG:2226 coordinates to WGS84 for display
- **Production Ready:** Architect-reviewed and verified - handles all GeoJSON geometry types, efficient layer management

**November 5, 2025 - Auto-Calculate Project Bounding Boxes - COMPLETE:**
- **Dynamic Bbox Calculation:** Modified `/api/map-viewer/project-structure` to automatically calculate bounding boxes from entity geometry when drawing.bbox is null
- **Edge Case Handling:** Added CASE statements to only calculate ST_Extent when entities exist, preventing null overwrites
- **New Projects Visible:** All projects now appear in dropdown regardless of whether bbox is set in drawings table
- **Newest First Ordering:** Changed ordering to `created_at DESC` so newest projects appear at top of list
- **Production Ready:** Architect-reviewed and verified - handles all edge cases (drawings with/without bbox, with/without entities)

**November 5, 2025 - Project Viewer Bug Fixes - COMPLETE:**
- **SQL Column Fix:** Fixed `/api/map-viewer/project-entities` endpoint to query `e.attributes` instead of non-existent `e.metadata` column, eliminating SQL errors when loading entities
- **Bbox Property Names:** Fixed `zoomToProject()` function to use correct API response format (`bbox.min_x/min_y/max_x/max_y` instead of `bbox.minx/miny/maxx/maxy`)
- **Defensive Error Handling:** Added comprehensive validation in `zoomToProject()` to check for null/invalid bbox coordinates with user-friendly error messages, preventing NaN/proj4 crashes
- **Property Name Fixes:** Corrected `selectedProject.project_name` reference in console logs (was incorrectly using `selectedProject.name`)
- **Production Ready:** All fixes architect-reviewed and verified via curl tests showing successful entity loading with entity type filtering

**November 5, 2025 - Test Data Generator for Spatial Testing - COMPLETE:**
- **Test Data Script:** Created `create_test_project.py` utility that generates projects with valid Sonoma County coordinates
- **3D Geometry Support:** Fixed geometry insertion to use GeometryZ format (LINESTRING Z with Z=0 coordinates)
- **SRID Compatibility:** Uses SRID 0 for geometry insertion to match DXF importer patterns
- **Realistic Test Data:** Generates projects at (6049000, 2001000) feet in EPSG:2226 near downtown Santa Rosa
- **Sample Entities:** Creates buildings, street centerlines, and roundabouts for realistic CAD testing
- **Automated Creation:** Simple `python create_test_project.py` command creates complete project with entities
- **Entity Count Fix:** Drawing Manager now shows actual entity counts via LEFT JOIN with drawing_entities table instead of stale entity_count column

**November 5, 2025 - DXF Project Display on Map Viewer - COMPLETE:**
- **Project Bounding Boxes:** Imported DXF projects now display as dashed orange boxes on the map showing spatial extents
- **Coordinate Transformation:** Fixed `/api/map-viewer/projects` to properly transform EPSG:2226 coordinates to WGS84 using pyproj Transformer
- **Entity Display:** New `/api/map-viewer/project-entities/<drawing_id>` endpoint fetches CAD entities (lines, polylines, arcs, circles) from drawing_entities table
- **Interactive Loading:** Click project boxes to load CAD entities, click again to toggle visibility
- **CAD Styling:** Entities styled with AutoCAD Color Index (ACI) colors (1=red, 2=yellow, 3=green, 4=cyan, 5=blue, 6=magenta, 7=white) and respect lineweight/transparency properties
- **Performance Limits:** 5000 entity limit per drawing to protect performance
- **Database Integration:** Seamlessly integrates with existing DXF import/export workflow - import DXF files through other tools, view them on the map
- **Production Ready:** All features architect-reviewed and verified for coordinate accuracy, SQL injection safety, and UX

**November 5, 2025 - Database Layer Integration & UI Polish - COMPLETE:**
- **Database Layer Display:** Map viewer now shows user's own PostGIS database layers alongside Sonoma County data with dedicated "Database Layers" section in sidebar
- **Database Layer API:** Two new endpoints: `/api/map-viewer/database-layers` (enumerate available tables with feature counts) and `/api/map-viewer/database-layer-data/<layer_id>` (fetch GeoJSON with bbox filtering)
- **Coordinate Transformation:** Backend transforms WGS84 map bounds to EPSG:2226 for PostGIS queries, returns features in WGS84 for display, maintains 1000 feature limit per query
- **CAD Color Schemes:** Professional engineering colors for database layers (yellow survey points, cyan utilities, magenta structures, red parcels, green alignments)
- **Layer Management:** On-demand loading with checkboxes, feature count display, property popups, spinner feedback, and proper cleanup
- **Supported Tables:** survey_points, utility_lines, utility_structures, parcels, horizontal_alignments, surface_features, drawing_entities
- **Zoom Controls:** Finer zoom sensitivity with zoomDelta: 0.25, wheelPxPerZoomLevel: 120, plus shift+drag box zoom enabled
- **UI Polish:** Fixed checkbox alignment with flexbox layout for both Sonoma County and Database Layers sections
- **Production Ready:** All features architect-reviewed and verified for coordinate handling, SQL injection safety, and performance