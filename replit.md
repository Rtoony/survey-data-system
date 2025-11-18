# ACAD-GIS: AI-First CAD/GIS System

## Overview
ACAD-GIS is an AI-first, database-centric CAD/GIS system designed to replace traditional file-based CAD workflows with a PostgreSQL/PostGIS database. It optimizes for AI understanding, semantic reasoning, and machine learning, offering a unified entity model, centralized embeddings, explicit graph edges, and built-in ML feature engineering. The system enables hybrid search across CAD/GIS data, focusing on civil engineering and surveying. Key capabilities include a Schema Explorer, CAD Standards Portal, and Python ML Tools for intelligent CAD operations, aiming to enhance data consistency, semantic understanding, and automated compliance tracking.

## User Preferences
Preferred communication style: Simple, everyday language.

## Recent Changes

### 2025-11-18: Authentication System - Database Deployment (Project 2 Completion)
Executed database migration to deploy authentication infrastructure:

**Database Migration Executed:**
- ✅ Created `users` table with 1 initial admin user
- ✅ Created `project_permissions` table for project-level access control
- ✅ Created `audit_log` table for comprehensive audit trail
- ✅ Created `user_sessions` table for session management
- ✅ Created 3 analytical views: `active_user_sessions`, `user_activity_summary`, `recent_audit_events`
- ✅ Created 3 helper functions: `update_updated_at_column()`, `cleanup_expired_sessions()`, `user_has_project_access()`

**Code Quality:**
- ✅ Fixed 2 LSP errors in `services/rbac_service.py` (type safety improvements)

**Authentication System Status:**
- ✅ **Code Implemented** (Previous commit d015f92): All auth services, routes, decorators, and UI templates
- ✅ **Database Deployed** (This commit): All tables, views, and functions created
- ⏭️ **Configuration Required**: Set Replit Auth credentials to activate OAuth login

**What Exists (Already Merged):**
- Auth services: `services/auth_service.py`, `services/rbac_service.py`
- Auth routes: `auth/routes.py` with login, logout, user management, permissions
- Auth decorators: `auth/decorators.py` with 5 route protection decorators
- UI templates: User management, profile, audit log viewer
- Navbar integration: User menu with login/logout links

**Configuration Required to Activate:**
- ⏭️ Set `REPLIT_CLIENT_ID` and `REPLIT_CLIENT_SECRET` in Secrets
- ⏭️ Set `INITIAL_ADMIN_EMAIL` for first admin user
- ⏭️ Apply decorators to protect sensitive routes (currently optional auth)

See `AUTH_SETUP_GUIDE.md` for complete configuration instructions.

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
- **Entity Registry System:** Core architectural component that maps CAD object type codes (STORM, MH, SURVEY, etc.) to database tables (`utility_lines`, `utility_structures`, `survey_points`, etc.). Acts as the central switchboard connecting CAD Layer Vocabulary → DXF Import Classification → Database Storage → Specialized Tools. Enables flexible, UI-driven expansion of object types without code changes, supporting client-specific CAD standard customization.
- **Mission Control Design System:** Centralized design system with reusable classes, variables, and a cyan/neon color palette.
- **Horizontal Navigation Architecture:** Sticky horizontal navbar with dropdown menus.
- **Projects Only System:** Migration to a "Projects Only" architecture where DXF imports create entities directly at the project level, featuring a hybrid intelligent object creation system for classification and review.
- **Specialized Tools Registry:** Database-driven system linking CAD object types to interactive management tools with three-dimensional filtering: Object Type → Attribute → Database Table. Enables surgical precision (e.g., BASIN+STORAGE for volume calculations vs BASIN+TREATMENT for water quality analysis).
- **Truth-Driven Filterable Columns Registry:** Reference Data Hub table (`filterable_entity_columns`) serving as authoritative source for filterable metadata columns in Project Relationship Sets, preventing manual typos and enabling dynamic vocabulary updates without code changes.

**Key Features & Design:**
- **Standards Management:** Dedicated interfaces for CAD Layer Vocabulary (managing naming standards) and Reference Data Hub (managing 9 types of project-agnostic reference data: Attribute Codes, CAD Standards, Clients, Municipalities, Coordinate Systems, Survey Point Descriptions, Naming Templates, Tool-Object Mappings, and Specialized Tools Registry).
- **Schema Explorer & Data Manager:** CRUD operations for CAD standards and vocabulary.
- **Schema Visualization Suite:** Tools for visualizing database schema, including a classic table browser, relationship diagram, and an optimized knowledge graph using Cytoscape.js.
- **CAD Standards Portal:** Visual, read-only display of AI-optimized CAD standards.
- **Enhanced CAD Layer Generator:** Dynamic layer name generation tool with integrated architecture explanations. Connects three core components: CAD Layer Vocabulary (naming standards), Entity Registry (database table mapping), and Specialized Tools (management interfaces). Features include: system overview dashboard with live statistics, DXF layer validation with import readiness scoring, tool-to-layer mapping APIs, educational content explaining component relationships, and automatic vocabulary refresh. Enables users to validate DXF imports, understand database routing, and discover specialized tools for each object type. All layer generation is truth-driven from the database, updating automatically as vocabulary evolves.
- **Standards Mapping Framework:** 11-table database schema with 5 name mapping managers for bidirectional DXF↔Database translation.
- **DXF Tools:** Full DXF import/export with intelligent object creation, change detection, and bidirectional sync, including survey-grade 3D elevation preservation. Includes a Z-Value Stress Test for coordinate precision.
- **Enhanced Map Viewer:** Full-featured spatial workbench with Leaflet-based interactive mapping, layer toggle controls, basemap selection (Streets/Satellite/Topo/Dark), multi-format export (DXF/KML/SHP/PNG), measurement tools (distance/area), address search with geocoding, bounding box selection for exports, and full-screen mode optimized for wide-screen monitors (20"/27"/ultrawide). See [VISUALIZATION_TOOLS.md](VISUALIZATION_TOOLS.md) for complete documentation.
- **Project Command Center:** Streamlined project management dashboard with collapsible 250px sidebar containing 10 specialized tools and 24 CAD standards, read-only context map with layer toggles and basemap selection, health metrics ribbon (entities/layers/intelligent objects/drawings), quick access navigation, and full-screen mode. Provides central hub for all project operations with visual project overview.
- **Entity Viewer:** Lightweight 2D viewer for project entities with SVG rendering, multi-select filters, and dynamic legend.
- **Network Managers Suite:** Unified framework of specialized manager tools (Gravity Pipe, Pressure Pipe, BMP Manager) following the Entity Viewer pattern.
- **Unified Batch CAD Import Tool:** Productivity tool for batch importing Blocks, Details, Hatches, and Linetypes from DXF files.
- **Batch Point Import Tool:** Survey point import tool for PNEZD text files with coordinate system selection, automatic transformation, and conflict detection.
- **Survey Code Library Manager:** AI-first survey point code system for structured, machine-parsable codes driving automatic CAD generation.
- **Survey Code Testing Interface:** Comprehensive testing and validation system for survey codes.
- **Survey Point Manager:** Comprehensive point management interface for imported survey data.
- **Project Usage Tracking Dashboard:** Analytics on project/layer/block/note usage patterns.
- **Civil Project Manager:** Comprehensive project overview dashboard with metadata-driven CRUD for project-specific attachments.
- **Sheet Note Manager:** Project-centric note management system with standard and custom notes, deviation tracking, and project-level organization.
- **Object Reclassifier Tool:** Interactive UI for reviewing and reclassifying unclassified or low-confidence DXF entities.
- **Project Relationship Sets:** Comprehensive dependency tracking and automated compliance auditing system that groups interconnected project elements (CAD geometry, specs, details, notes, hatches, materials) to detect out-of-sync conditions. Features include:
  - **Member Management:** Add specific entities or filtered groups using truth-driven metadata columns from filterable_entity_columns Reference Data Hub table
  - **Rule Builder:** Visual interface for creating compliance rules with 8 operator types (required, equals, contains, in_list, min, max, regex, not_equals)
  - **Violations Dashboard:** Tabbed interface displaying detected violations with resolve/acknowledge actions and status tracking
  - **Sync Checker:** Three intelligent checking algorithms (Existence, Link Integrity, Metadata Consistency)
  - **Template System:** Save and reuse relationship set configurations across projects
  - **Naming Templates:** ⚠️ PLANNED (not yet implemented) - Will use `relationship_set_naming_templates` table for database-backed naming standards; replaces free-text Set Name/Short Code inputs with template-based selection + token replacement for consistency
  - **Truth-Driven Architecture:** Dynamic field dropdowns from filterable_entity_columns (33 columns across 11 entity types) preventing manual errors
- **Relationship Set Naming Templates Manager:** CRUD interface in Reference Data Hub for managing standardized naming conventions with format strings, token definitions, examples, and usage instructions
- **About ACAD-GIS Page:** Comprehensive system documentation page explaining philosophy, architecture, workflows, and capabilities. Covers the companion tool concept (database-centric vs. file-based CAD), 5 core architectural components (CAD Layer Vocabulary, Entity Registry, Specialized Tools Registry, Reference Data Hub, Standards Mapping Framework), complete DXF↔Database workflow, 30+ tools organized into 8 categories, and 6 key differentiators (GraphRAG, automated compliance, multi-project intelligence, version control, truth-driven architecture, quality workflows). Features collapsible sections, visual diagrams, quick navigation menu, and Mission Control styling. Serves as the definitive onboarding and reference resource for understanding ACAD-GIS architecture.
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