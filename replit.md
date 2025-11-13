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
- **Project-Centric Organization (Nov 2025):** System restructured from drawing-centric to project-centric organization. Entities now link directly to projects rather than through intermediate drawing files, simplifying data retrieval and aligning with real-world civil engineering workflows where projects are the primary unit of work.
- **Projects Navigation Restructure:** Unified projects functionality under `/projects` route with search, CRUD, and individual project overviews.
- **Specialized Tools Registry:** Database-driven system linking CAD object types to interactive management tools.

**Key Features & Design:**
- **Standards Management:** Dedicated interfaces for Layer Vocabulary and Reference Data Hub for managing entities, clients, vendors, municipalities, coordinate systems, and survey point descriptions with full CRUD.
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