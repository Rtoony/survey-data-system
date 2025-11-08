# ACAD-GIS: AI-First CAD/GIS System

## Overview

ACAD-GIS is an AI-first, database-centric CAD/GIS system for machine learning, embeddings, and GraphRAG. It replaces traditional file-based CAD workflows with a PostgreSQL/PostGIS database, optimizing for AI understanding and semantic reasoning. Its core value lies in providing a unified entity model, centralized embeddings, explicit graph edges for GraphRAG, and built-in ML feature engineering, enabling hybrid search across CAD/GIS data. Key applications include a Schema Explorer, CAD Standards Portal, and Python ML Tools for intelligent CAD operations, with a focus on civil engineering and surveying workflows.

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
- **Specific Tables:** `dxf_entity_links`, `pipe_networks`, `utility_network_memberships` for civil infrastructure.

**Architectural Patterns & Decisions:**
- **AI-First Design:** Database schema optimized for ML and LLM understanding.
- **Graph Database Patterns:** Explicit relationship tables for GraphRAG multi-hop queries.
- **Spatial-Semantic Fusion:** Combines PostGIS spatial operations with vector similarity search.
- **Quality-Driven:** Entities have quality scores based on completeness, embeddings, and relationships.
- **Server-Side Rendering:** Flask serves Jinja2 templates, augmented by client-side JavaScript.
- **Materialized Views:** Pre-computed views for fast AI queries (e.g., `mv_survey_points_enriched`).

**Key Features & Design:**
- **Schema Explorer & Data Manager:** CRUD operations for CAD standards.
- **CAD Standards Portal:** Visual, read-only display of AI-optimized CAD standards.
- **DXF Tools:** Full DXF import/export with intelligent object creation, change detection, and bidirectional sync using `ezdxf` and PostGIS GeometryZ, supporting SRID 0.
- **Map Viewer & Export:** Interactive Leaflet map with coordinate transformation, bounding box export (DXF/SHP/PNG/KML), measurement tools, address search, and WFS layer support. Handles both SRID 0 and SRID 2226 data, with appropriate transformations.
- **Sheet Note Manager & Sheet Set Manager:** Backend for managing construction drawing notes and deliverables.
- **Survey & Civil Engineering Schema:** Comprehensive database schema for civil/survey data.
- **AI Toolkit:** Python modules and web interface for data ingestion, embedding generation, relationship building, validation, and maintenance.
- **Interactive AI Visualizations:** Knowledge Graph Visualization (Vis.js) and a Quality Dashboard.
- **Gravity Pipe Network Editor:** Backend and frontend for managing gravity pipe networks, including automatic classification, intelligent object creation, network auto-connection based on spatial proximity, and interactive SVG diagram visualization with editable tables for pipes and structures.

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

### 2025-11-08: Revolutionary CAD Standards System
Implemented a database-optimized CAD naming system that makes the database the source of truth, with layer names serving as semantic labels rather than data storage.

**New Standards Architecture:**
- **8 new vocabulary tables:** `discipline_codes`, `category_codes`, `object_type_codes`, `attribute_codes`, `phase_codes`, `geometry_codes`, `standard_layer_patterns`, `import_mapping_patterns`
- **Hierarchical layer format:** `DISCIPLINE-CATEGORY-TYPE-[ATTRIBUTES]-PHASE-GEOMETRY`
  - Example: `CIV-UTIL-STORM-12IN-NEW-LN` = Civil utility storm pipe, 12", new construction, line
- **47 object types** across 8 disciplines (CIV, SITE, SURV, LAND, ARCH, UTIL, ANNO, XREF)
- **Comprehensive coverage:** Utilities, roads, grading, stormwater, ADA, ponds, tanks, erosion control

**New Tools:**
- `LayerNameBuilder`: Generates and validates standard layer names programmatically
- `LayerClassifierV2`: Parses both standard and legacy layer formats, auto-converts to standard naming
- `load_standards_data.py`: Populates vocabulary tables from structured definitions
- Migration: `migrations/create_standards_schema.sql` for reproducible schema setup

**Workflow:**
1. **Import:** DXF files with any client layer format → regex patterns extract intent → database objects created
2. **Process:** Data enriched in database using Python scripts and ML tools
3. **Export:** Database objects → generate layer names (standard or client-specific) → DXF output

**Benefits:**
- AI-friendly: Clear hierarchy makes LLM processing straightforward
- Human-readable: Engineers understand `CIV-UTIL-STORM-12IN-NEW-LN` at a glance
- Flexible: Handles variations in client CAD standards via mapping patterns
- Extensible: New codes added without breaking existing patterns
- Quality-driven: Database validates and scores confidence on import

**Integration:** `IntelligentObjectCreator` now uses `LayerClassifierV2` for standards-driven object creation during DXF import.