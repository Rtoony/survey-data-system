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
- **Sheet Note Manager:** Backend for managing construction drawing notes with standard libraries and custom overrides.
- **Sheet Set Manager:** System for organizing construction document deliverables and tracking sheet assignments.
- **Survey & Civil Engineering Schema:** Comprehensive database schema for civil/survey data (points, networks, alignments, parcels) utilizing PostGIS PointZ.
- **AI Toolkit:** Python modules and web interface for data ingestion, embedding generation, relationship building, validation, and maintenance.

## External Dependencies

**Python Libraries:**
- `Flask`, `Flask-Caching`, `psycopg2-binary`, `python-dotenv`, `flask-cors`, `ezdxf`, `openai`.

**Database:**
- `PostgreSQL 12+`
- `PostGIS Extension`
- `Supabase` (recommended hosting)

**Frontend Resources (CDNs):**
- `Font Awesome 6.4.0`
- `Google Fonts` (Orbitron, Rajdhani)
- `Vis.js`

**Environment Configuration:**
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

**Related Systems:**
- **ACAD-GIS FastAPI application:** Main API server sharing the same PostgreSQL/PostGIS database.

## Recent Changes

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
- `TOOLKIT_SETUP_COMPLETE.md` - Toolkit usage guide and quick reference
- `DOCUMENTATION_INDEX.md` - Navigation hub for all 9 documentation files
- `tools/README.md` - Module reference
- `examples/README.md` - Example scripts