# ACAD-GIS: AI-First CAD/GIS System

## Overview

ACAD-GIS is an AI-first, database-centric CAD/GIS system designed for machine learning, embeddings, and GraphRAG. It aims to replace traditional file-based CAD workflows with a PostgreSQL/PostGIS database, optimizing for AI understanding and semantic reasoning. The system provides a unified entity model, centralized embeddings, explicit graph edges for GraphRAG, and built-in ML feature engineering, enabling hybrid search across CAD/GIS data. Key capabilities include a Schema Explorer, CAD Standards Portal, and Python ML Tools for intelligent CAD operations, with a focus on civil engineering and surveying workflows.

## Recent Changes

- **November 9, 2025**: STANDARDS MAPPING NAVIGATION & CROSS-REFERENCES - Added dedicated "Standards Mapping" section to sidebar navigation (between Standards Library and Project Operations) with links to Mapping Dashboard, Project Context Manager, 5 name mapping CRUD managers, and Export Documentation. Enhanced Project Context Manager with 6th relationship type: Cross-References (`project_element_cross_references`) supporting flexible any-to-any element relationships (keynote/block/detail/hatch/material) with hybrid UI (type dropdown + typeahead search), server-side validation ensuring element IDs match their declared types, relationship type/strength metadata, tags, and sheet references. Total of 25 relationship API endpoints with production-ready validation.
- **November 9, 2025**: PROJECT CONTEXT MAPPING MANAGER & EXPORT TOOLS - Built comprehensive Project Context Mapping Manager (`/project-context-manager`) with 5 tabbed interfaces for managing semantic relationships: Keynote→Block, Keynote→Detail, Hatch→Material, Detail→Material, and Block→Specification. Implemented full CRUD operations (20 API endpoints) with modal-based editing, project-scoped views, and relationship tracking. Created Standards Documentation Export Tool (`/standards-export`) supporting 4 export formats: Excel (.xlsx with multi-sheet workbooks), CSV (.zip archives), standalone HTML (Mission Control styling), and PDF (WeasyPrint generation). Both tools provide client handoff capabilities, training documentation, and quality control workflows. Added `openpyxl` and `weasyprint` packages.
- **November 9, 2025**: NAME MAPPING MANAGERS - Built 5 complete CRUD managers for all name mapping types: Block Mappings (`/data-manager/block-mappings`), Detail Mappings (`/data-manager/detail-mappings`), Hatch Mappings (`/data-manager/hatch-mappings`), Material Mappings (`/data-manager/material-mappings`), and Note Mappings (`/data-manager/note-mappings`). Each manager supports bidirectional DXF↔Database translation, multi-client scoping, confidence scoring, modal editing, and search/filter capabilities with import/export direction badges.
- **November 9, 2025**: STANDARDS MAPPING VISUALIZATION DASHBOARD - Created Standards Mapping Dashboard (`/standards-mapping-dashboard`) with tabbed interface showing Overview (statistics and counts), Name Mappings (all 5 types with direction badges), Relationships (6 project context mapping types), and full-text Search capabilities across all mappings. Provides read-only visualization with "Manage" links to CRUD interfaces.
- **November 9, 2025**: CAD STANDARDS MAPPING FRAMEWORK - Created comprehensive database schema for CAD element name mappings and project-level context relationships. Built 11 new tables: 5 name mapping tables (block_name_mappings, detail_name_mappings, hatch_pattern_name_mappings, material_name_mappings, note_name_mappings) supporting bidirectional DXF↔Database translation with multi-client scoping, and 6 project context mapping tables (project_keynote_block_mappings, project_keynote_detail_mappings, project_hatch_material_mappings, project_detail_material_mappings, project_block_specification_mappings, project_element_cross_references) enabling semantic relationships between keynotes, blocks, details, hatches, and materials. All tables include AI-friendly search_vector columns with GIN indexes and automatic triggers for full-text search capability.
- **November 9, 2025**: MAJOR ARCHITECTURAL RESTRUCTURING - Separated "Standards Library" from "Project Operations" with clear navigation hubs, new database tables (`project_standard_assignments`, `project_standard_overrides`), Project Standards Assignment UI (`/project-standards-assignment`) for assigning standard bundles to projects, and Project Compliance Dashboard (`/project-compliance`) for tracking compliance and deviations. This enables the core workflow: manage global standards → assign to projects → track compliance.
- **November 9, 2025**: Completed 4 CAD Standards Managers - Hatch Patterns (`/data-manager/hatches`), Linetypes (`/data-manager/linetypes`), Text Styles (`/data-manager/text-styles`), and Dimension Styles (`/data-manager/dimension-styles`) providing full CRUD for all CAD drawing standards. Created `drawing_materials` junction table and built Drawing-Materials Relationship Manager (`/data-manager/drawing-materials`) for linking materials to specific drawings with quantity tracking.
- **November 9, 2025**: Completed 4 new Data Managers - Materials (`/data-manager/materials`), Projects (`/data-manager/projects`), Drawings (`/data-manager/drawings`), and Sheet Sets (`/data-manager/sheet-sets`) providing full CRUD interfaces with search/filter capabilities, modal-based editing, and FK relationship handling via project dropdowns.
- **November 9, 2025**: Completed Drawing Usage Tracking Dashboard - comprehensive analytics dashboard at `/usage-dashboard` showing drawing/layer/block/note usage patterns, most accessed drawings, layer aggregation statistics, and recent activity timeline.
- **November 9, 2025**: Completed Standard Notes Library CRUD manager - full create/read/update/delete interface at `/data-manager/standard-notes` for managing construction notes, following established data manager patterns with search, filtering, and modal-based editing.

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
- **Materialized Views:** Pre-computed views for fast AI queries.

**Key Features & Design:**
- **Schema Explorer & Data Manager:** CRUD operations for CAD standards.
- **CAD Standards Portal:** Visual, read-only display of AI-optimized CAD standards.
- **Standards Mapping Framework:** 11-table database schema with 5 name mapping managers (blocks, details, hatches, materials, notes) supporting bidirectional DXF↔Database translation, visualization dashboard, and full-text search.
- **Project Context Mapping Manager:** Manage 6 relationship types (Keynote→Block, Keynote→Detail, Hatch→Material, Detail→Material, Block→Specification, Cross-References) with project-scoped views, modal editing, hybrid typeahead search UI for flexible element linking, server-side validation, and 25 CRUD API endpoints.
- **Standards Documentation Export:** Generate client handoffs and training materials in 4 formats (Excel multi-sheet workbooks, CSV ZIP archives, standalone HTML, PDF documents) with content selection and custom titles/descriptions.
- **Standards Management UI:** Tools for configuring client-specific layer mapping patterns and bulk editing vocabulary types.
- **DXF Tools:** Full DXF import/export with intelligent object creation, change detection, and bidirectional sync.
- **Map Viewer & Export:** Interactive Leaflet map with coordinate transformation, bounding box export, measurement tools, address search, and WFS layer support.
- **Sheet Note Manager & Sheet Set Manager:** Backend for managing construction drawing notes and deliverables.
- **Survey & Civil Engineering Schema:** Comprehensive database schema for civil/survey data.
- **AI Toolkit:** Python modules and web interface for data ingestion, embedding generation, relationship building, validation, and maintenance.
- **Interactive AI Visualizations:** Knowledge Graph Visualization and a Quality Dashboard.
- **Gravity Pipe Network Editor:** Backend and frontend for managing gravity pipe networks.

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