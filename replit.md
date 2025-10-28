# ACAD-GIS Companion Tools

## Overview

The ACAD-GIS Companion Tools project provides two Flask-based web applications that complement the main ACAD-GIS system:

1.  **Schema Explorer & Data Manager**: An administrative tool for visualizing database schemas, managing projects, and maintaining CAD standards data.
2.  **CAD Standards Portal**: A user-friendly reference for machine-optimized CAD standards (layers, blocks, colors, etc.).

Both applications share a common PostgreSQL/Supabase database and a consistent Mission Control-themed UI. They are designed as lightweight interfaces to manage and reference CAD data, featuring DXF round-trip capabilities, interactive schema visualization, a robust sheet note management system, and comprehensive survey/civil engineering data management. The database includes 29 survey/civil tables for complete project lifecycle support from field data to final design.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Technologies
-   **Web Framework**: Flask (Python) for server-rendered HTML and JSON APIs.
-   **Database**: PostgreSQL with PostGIS extension, typically hosted on Supabase.
-   **Frontend**: Jinja2 templating, Mission Control-themed CSS, vanilla JavaScript, Font Awesome, and Google Fonts.

### Architectural Patterns & Decisions
-   **Server-Side Rendering**: Flask serves Jinja2 templates, augmented by client-side JavaScript for dynamism.
-   **Database Interaction**: `psycopg2` with connection pooling, raw SQL, and `RealDictCursor`.
-   **CORS**: Enabled via Flask-CORS.
-   **Caching**: Flask-Caching with SimpleCache for frequently accessed data.
-   **Error Handling**: Centralized database error catching with user-friendly frontend display.
-   **Modularity**: Clear separation of concerns with dedicated API endpoints for distinct features.

### Key Features & Design
-   **Schema Explorer**: Provides database health checks, schema visualization (using Vis.js), and project/drawing management.
-   **CAD Standards Portal**: Presents complex CAD database fields in an accessible, visual, read-only format.
-   **Data Manager**: Offers comprehensive CRUD operations for CAD standards data (Abbreviations, Layers, Blocks, Details) with searching, modal forms, and CSV import/export.
-   **DXF Tools**: Implements full DXF round-trip functionality (import DXF to PostGIS, export PostGIS to DXF) using `ezdxf`, featuring normalized foreign keys, a lookup service, and PostGIS GeometryZ. Includes API and UI for file management.
-   **Sheet Note Manager**: Backend for managing construction drawing notes across projects and sheets, including standard libraries, project-specific sets, custom overrides, and legend generation. The frontend is a React-based three-panel UI.
-   **Sheet Set Manager**: System for organizing construction document deliverables and tracking sheet assignments. Manages project details, sheet categories, sheet sets, individual sheets, revisions, and relationships. Features a React-based two-panel UI for project and sheet set management.
-   **Survey & Civil Engineering Schema**: Comprehensive database schema for civil/survey engineering data, including survey points, control networks, site features, alignments, cross-sections, earthwork, utilities, and parcels, utilizing PostGIS PointZ and projected coordinates (State Plane California Zone 2, with support for all CA zones and future expansion).

## External Dependencies

### Python Libraries
-   `Flask`, `Flask-Caching`, `psycopg2-binary`, `python-dotenv`, `flask-cors`, `ezdxf`.

### Database
-   `PostgreSQL 12+`
-   `PostGIS Extension`
-   `Supabase` (recommended hosting)

### Frontend Resources (CDNs)
-   `Font Awesome 6.4.0`
-   `Google Fonts` (Orbitron, Rajdhani)
-   `Vis.js`

### Environment Configuration
-   `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

### Related Systems
-   **ACAD-GIS FastAPI application**: The main API server sharing the same PostgreSQL/PostGIS database.