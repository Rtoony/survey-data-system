# ACAD-GIS: AI-First CAD/GIS System

## Overview

ACAD-GIS is an AI-first, database-centric CAD/GIS system designed for machine learning, embeddings, and GraphRAG. It aims to replace traditional file-based CAD workflows with a PostgreSQL/PostGIS database, optimizing for AI understanding and semantic reasoning. The system provides a unified entity model, centralized embeddings, explicit graph edges for GraphRAG, and built-in ML feature engineering, enabling hybrid search across CAD/GIS data. Key capabilities include a Schema Explorer, CAD Standards Portal, and Python ML Tools for intelligent CAD operations, with a focus on civil engineering and surveying workflows. This project aims to revolutionize CAD/GIS data management by integrating AI directly into the core architecture, offering enhanced data consistency, semantic understanding, and automated compliance tracking for civil engineering and surveying firms.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

**Core Technologies:**
- **Database:** PostgreSQL 12+ with PostGIS 3.3+ and pgvector 0.8+.
- **AI/ML Stack:** Vector embeddings (1536 dimensions), GraphRAG, full-text search.
- **Web Framework:** Flask (Python) for server-rendered HTML and JSON APIs.
- **Frontend:** Jinja2 templating, Mission Control-themed CSS, vanilla JavaScript, Leaflet.js.
- **Spatial:** PostGIS with SRID 2226 (California State Plane Zone 2, US Survey Feet) for GIS and SRID 0 for CAD data.

**AI-First Database Architecture:**
- **Unified Entity Registry (`standards_entities`):** Canonical identity for all CAD/GIS elements.
- **Entity Registry (`entity_registry`):** Validated registry of database tables that can store CAD objects, enforcing referential integrity between layer vocabulary and database schema. Each entry validates table existence in `information_schema.tables` before registration.
- **Centralized Embeddings (`entity_embeddings`):** Stores versioned vector embeddings.
- **Graph Edges (`entity_relationships`):** Defines explicit spatial, engineering, and semantic relationships for GraphRAG.
- **Quality Scoring:** `quality_score` column for data quality assessment.
- **Full-Text Search:** `search_vector` tsvector columns with weighted search.
- **JSONB Attributes:** Flexible metadata storage in `attributes` columns.
- **Vector Indexing:** IVFFlat indexes for fast similarity search.
- **Spatial Indexing:** GIST indexes on PostGIS geometry columns.

**Architectural Patterns & Decisions:**
- **AI-First Design:** Database schema optimized for ML and LLM understanding, enabling GraphRAG for multi-hop queries and hybrid search.
- **Quality-Driven:** Entities have quality scores based on completeness, embeddings, and relationships.
- **Server-Side Rendering:** Flask serves Jinja2 templates, augmented by client-side JavaScript.
- **Materialized Views:** Pre-computed views for fast AI queries.
- **Modular Standards Management:** Separation of "Standards Library" from "Project Operations" with clear navigation, project assignment, and compliance tracking.
- **Database-Driven Vocabulary:** Implemented a comprehensive, database-backed controlled vocabulary system for CAD elements (disciplines, categories, object types, phases, geometries) with full CRUD and automatic propagation across the application.
- **CAD Layer Naming Standards:** Defined and implemented a database-driven classifier (`[DISCIPLINE]-[CATEGORY]-[OBJECT_TYPE]-[PHASE]-[GEOMETRY]`) for CAD layer names, supporting extraction of attributes like diameter and network mode.
- **Split Vocabulary Architecture:** Separated layer-specific vocabulary (/standards/layer-vocabulary) from general reference data management (/standards/reference-data) for better organization and focused workflows.
- **Mission Control Design System:** Centralized design system in static/css/styles.css with reusable mc-* classes and --mc-* CSS variables. Cyan/neon color palette (#00ffff primary, #ff00ff secondary, #00ff88 accent) with Orbitron headings and Rajdhani body text. All 27+ templates use shared styles for visual consistency.
- **Horizontal Navigation Architecture:** Replaced vertical sidebar with sticky horizontal navbar in base.html featuring 10 dropdown menus (Home, Standards, Data Manager, Mapping, Projects, Tools, Analytics, AI, Database, About) organizing 41 navigation items. Implements hybrid hover/click dropdowns with ARIA accessibility, responsive mobile hamburger menu, and automatic active state highlighting. All templates must extend base.html to inherit the shared navbar and Mission Control theme.

**Key Features & Design:**
- **Layer Vocabulary Page (/standards/layer-vocabulary):** Dedicated interface for database-driven layer naming classification with 7 tabs (Overview, Disciplines, Categories, Object Types, Phases, Geometries, Full Hierarchy). Object Type codes link to validated database tables via Entity Registry dropdown with server-side validation.
- **Reference Data Hub (/standards/reference-data):** Centralized management of system configuration and reference tables. Entity Registry tab provides full CRUD interface for managing valid database entity tables with real-time table existence validation, category grouping, and modal editing. Future tabs: Clients, Vendors, Municipalities, Coordinate Systems, Survey Point Descriptions.
- **Schema Explorer & Data Manager:** CRUD operations for CAD standards, including a complete vocabulary inline editing interface.
- **CAD Standards Portal:** Visual, read-only display of AI-optimized CAD standards, including a curated layer examples catalog.
- **Standards Mapping Framework:** 11-table database schema with 5 name mapping managers (blocks, details, hatches, materials, notes) supporting bidirectional DXF↔Database translation, a visualization dashboard, and full-text search.
- **Project Context Mapping Manager:** Manages 6 relationship types (Keynote↔Block, Keynote↔Detail, Hatch↔Material, Detail↔Material, Block↔Specification, Cross-References) with project-scoped views, modal editing, and hybrid typeahead search UI.
- **Standards Documentation Export:** Generates client handoffs and training materials in Excel, CSV, HTML, and PDF formats.
- **DXF Tools:** Full DXF import/export with intelligent object creation, change detection, and bidirectional sync.
- **Map Viewer & Export:** Interactive Leaflet map with coordinate transformation, bounding box export, and measurement tools.
- **Entity Viewer (/entity-viewer):** Lightweight 2D viewer for project entities with SVG rendering on black background, supporting 8 entity types (parcels, utility lines, structures, survey points, alignments, easements, ROW, drawing entities). Features project/drawing/layer multi-select filters, auto-fit viewport, hover/click entity info, and dynamic legend with entity type and layer counts. Handles both project_id and drawing_id scoped tables with proper coordinate transformation to EPSG:4326.
- **Network Managers Suite:** Unified framework of specialized manager tools for different infrastructure types, all following the Entity Viewer pattern with shared viewer core module (static/js/entity_viewer_core.js - 27KB reusable class):
  - **Shared Entity Viewer Core Features:** Mouse wheel zoom (0.5x-10x), click-drag panning, zoom controls (+/-/reset/zoom%), auto-scaled coordinate grid, north arrow, dynamic scale bar (ft/mi), SVG viewBox manipulation for smooth performance. All features enabled by default across all managers.
  - **Gravity Pipe Network Manager (/gravity-network-manager):** Manages gravity-flow networks (Storm/Sanitary) with color-coded visualization (Storm=orange, Sanitary=blue), bidirectional selection sync, auto-fit viewport, zoom/pan/grid navigation, and pressure-specific editing for inverts/slopes. Includes Auto-Connect and Save Changes functionality.
  - **Pressure Pipe Network Manager (/pressure-network-manager):** Manages pressurized networks (Potable/Reclaimed/Fire) with color-coded visualization (Potable=blue, Reclaimed=purple, Fire=red), zoom/pan/grid navigation, pressure-specific database tables (utility_line_pressure_data, utility_structure_pressure_data, pressure_zones), and editing for pressure ratings, valve types/status, and flow directions.
  - **BMP Manager (/bmp-manager):** Manages stormwater Best Management Practices with polygon rendering, color-coded by BMP type (bioswale, detention basin, retention basin, etc.), zoom/pan/grid navigation, dedicated database schema (storm_bmps, bmp_inflow_outflow, bmp_drainage_areas, bmp_maintenance_log), and editing for treatment volumes, infiltration rates, and drainage areas.
- **Unified Batch CAD Import Tool (/tools/batch-cad-import):** Productivity tool for batch importing 4 types of CAD elements from DXF files: **Blocks** (symbols), **Details** (construction details), **Hatches** (fill patterns), and **Linetypes** (line patterns). Built with strategy pattern architecture using `BatchCADExtractor` factory and discrete extractor modules (`BlockExtractor`, `DetailExtractor`, `HatchExtractor`, `LinetypeExtractor`). Features drag-and-drop multi-file upload, automatic element extraction with CAD Layer Vocabulary integration for smart category/discipline suggestions, SVG preview generation (matplotlib Agg backend), existing element detection, conflict resolution (import/update/skip actions), search/filter capabilities, and batch selection controls. Unified API endpoints (`/api/batch-cad-import/extract`, `/api/batch-cad-import/save`) dispatch to type-specific handlers with backward-compatible legacy routes. Supports importing entire CAD libraries in minutes vs hours of manual entry. Legacy route `/tools/batch-block-import` redirects to unified tool.
- **Drawing Usage Tracking Dashboard:** Provides analytics on drawing/layer/block/note usage patterns.
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
- `Leaflet.js 1.9.4`, `Leaflet.draw 1.0.4`, `Proj4js 2.9.0`, `Turf.js 6.x`.

**Related Systems:**
- ACAD-GIS FastAPI application (main API server).