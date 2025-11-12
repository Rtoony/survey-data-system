# ACAD-GIS: AI-First CAD/GIS System

## Overview

ACAD-GIS is an AI-first, database-centric CAD/GIS system designed for machine learning, embeddings, and GraphRAG. It replaces traditional file-based CAD workflows with a PostgreSQL/PostGIS database, optimizing for AI understanding and semantic reasoning. The system provides a unified entity model, centralized embeddings, explicit graph edges for GraphRAG, and built-in ML feature engineering, enabling hybrid search across CAD/GIS data. Key capabilities include a Schema Explorer, CAD Standards Portal, and Python ML Tools for intelligent CAD operations, with a focus on civil engineering and surveying workflows. This project aims to revolutionize CAD/GIS data management by integrating AI directly into the core architecture, offering enhanced data consistency, semantic understanding, and automated compliance tracking for civil engineering and surveying firms.

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
- **Unified Entity Registry:** Canonical identity for all CAD/GIS elements (`standards_entities`, `entity_registry`).
- **Centralized Embeddings:** Stores versioned vector embeddings (`entity_embeddings`).
- **Graph Edges:** Defines explicit spatial, engineering, and semantic relationships for GraphRAG (`entity_relationships`).
- **Quality Scoring:** `quality_score` column for data quality assessment.
- **Full-Text Search:** `search_vector` tsvector columns.
- **JSONB Attributes:** Flexible metadata storage.
- **Vector Indexing:** IVFFlat indexes for fast similarity search.
- **Spatial Indexing:** GIST indexes on PostGIS geometry columns.

**Architectural Patterns & Decisions:**
- **AI-First Design:** Database schema optimized for ML and LLM understanding, enabling GraphRAG for multi-hop queries and hybrid search.
- **Quality-Driven:** Entities have quality scores based on completeness, embeddings, and relationships.
- **Server-Side Rendering:** Flask serves Jinja2 templates, augmented by client-side JavaScript.
- **Materialized Views:** Pre-computed views for fast AI queries.
- **Modular Standards Management:** Separation of "Standards Library" from "Project Operations" with clear navigation and compliance tracking.
- **Database-Driven Vocabulary:** Comprehensive, database-backed controlled vocabulary system for CAD elements with full CRUD.
- **CAD Layer Naming Standards:** Database-driven classifier (`[DISCIPLINE]-[CATEGORY]-[OBJECT_TYPE]-[PHASE]-[GEOMETRY]`) for CAD layer names.
- **Mission Control Design System:** Centralized design system with reusable classes, variables, and a cyan/neon color palette. All templates extend `base.html` for consistency.
- **Horizontal Navigation Architecture:** Sticky horizontal navbar in `base.html` with 10 dropdown menus and 41 navigation items, implementing hybrid hover/click dropdowns, ARIA accessibility, and a responsive mobile hamburger menu.
- **Projects Navigation Restructure:** Unified projects functionality under `/projects` route with search, CRUD, and individual project overviews.
- **Specialized Tools Registry:** Database-driven system linking CAD object types to interactive management tools via `layer_object_tools` table. Layer Generator UI dynamically displays tool badges for objects with specialized capabilities (e.g., Gravity Pipe Manager for GRAV objects). New tools are added via simple database inserts without code changes. Uses DOM APIs for XSS prevention and includes cascade-aware badge clearing.

**Key Features & Design:**
- **Standards Management:** Dedicated interfaces for Layer Vocabulary (`/standards/layer-vocabulary`) and Reference Data Hub (`/standards/reference-data`) for managing entities, clients, vendors, municipalities, coordinate systems, and survey point descriptions with full CRUD.
- **Schema Explorer & Data Manager:** CRUD operations for CAD standards and vocabulary inline editing.
- **Schema Visualization Suite:** Multiple database schema visualization tools including a classic table browser (`/schema`), relationship diagram (`/schema/relationships`), and an optimized knowledge graph (`/schema/graph`) using Cytoscape.js for interactive exploration of 146+ tables and 244+ relationships with search, filtering, and multiple layout algorithms.
- **CAD Standards Portal:** Visual, read-only display of AI-optimized CAD standards.
- **Standards Mapping Framework:** 11-table database schema with 5 name mapping managers (blocks, details, hatches, materials, notes) supporting bidirectional DXF↔Database translation.
- **Project Context Mapping Manager:** Manages 6 relationship types (Keynote↔Block, Keynote↔Detail, Hatch↔Material, Detail↔Material, Block↔Specification, Cross-References).
- **Standards Documentation Export:** Generates client handoffs and training materials (Excel, CSV, HTML, PDF).
- **DXF Tools:** Full DXF import/export with intelligent object creation, change detection, and bidirectional sync. Includes survey-grade 3D elevation (Z-value) preservation using dimension-based detection and POLYLINE3D export.
- **Z-Value Stress Test Harness (`scripts/z_stress_harness.py`):** Production-ready CLI tool for proving Z-value preservation over 20+ import/export cycles. Generates auditable JSON reports with SHA256 hashes, per-cycle error metrics (max/avg/z-delta), and canonical test fixtures (Z=0 flat pads, sloped pipes, large coordinates, sub-millimeter precision). Exits with status code 0 on PASS, 1 on FAIL. Supports both SRID 0 (local CAD) and EPSG:2226 (CA State Plane).
- **Map Viewer & Export:** Interactive Leaflet map with coordinate transformation, bounding box export, and measurement tools.
- **Entity Viewer (`/entity-viewer`):** Lightweight 2D viewer for project entities with SVG rendering, supporting 8 entity types, multi-select filters, and dynamic legend.
- **Network Managers Suite:** Unified framework of specialized manager tools (Gravity Pipe, Pressure Pipe, BMP Manager) following the Entity Viewer pattern, with shared core module for zoom, pan, grid, scale, and north arrow functionalities.
- **Unified Batch CAD Import Tool (`/tools/batch-cad-import`):** Productivity tool for batch importing Blocks, Details, Hatches, and Linetypes from DXF files. Features drag-and-drop upload, automatic extraction, SVG preview, conflict resolution, and batch selection.
- **Drawing Usage Tracking Dashboard:** Analytics on drawing/layer/block/note usage patterns.
- **Civil Project Manager (`/projects/<id>`):** Comprehensive project overview dashboard with 5 tabs (Overview, Drawings, Reference Data, Compliance, Standards). Features Leaflet map, editable project information, and a metadata-driven CRUD architecture for managing project-specific attachments across 6 entity types.
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
- `Cytoscape.js 3.28.1` with COSE-Bilkent layout extension
- `Leaflet.js 1.9.4`, `Leaflet.draw 1.0.4`, `Proj4js 2.9.0`, `Turf.js 6.x`.

**Related Systems:**
- ACAD-GIS FastAPI application (main API server).