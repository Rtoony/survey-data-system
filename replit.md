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