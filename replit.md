# ACAD-GIS Companion Tools

## Overview

The ACAD-GIS Companion Tools project consists of two Flask-based web applications that support the main ACAD-GIS system:

1.  **Schema Explorer & Data Manager**: A database administration tool for visualizing schemas, managing projects, and maintaining CAD standards data.
2.  **CAD Standards Portal**: A user-friendly reference portal that presents machine-optimized CAD standards (layers, blocks, colors, etc.) in an accessible format for employees.

Both tools utilize a shared Supabase/PostgreSQL database and feature a consistent Mission Control-themed user interface. They are intended as lightweight administrative and reference interfaces, complementing the primary ACAD-GIS FastAPI application. The project aims to provide comprehensive tools for managing and referencing CAD data, including full DXF round-trip capabilities, interactive schema visualization, and a robust sheet note management system.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Technologies
-   **Web Framework**: Flask (Python) for server-rendered HTML and JSON APIs.
-   **Database**: PostgreSQL with PostGIS extension for geospatial data, typically hosted on Supabase.
-   **Frontend**: Jinja2 templating, Mission Control-themed CSS, vanilla JavaScript, Font Awesome for icons, and Google Fonts (Orbitron, Rajdhani).

### Architectural Patterns & Decisions
-   **Server-Side Rendering**: Traditional Flask serving Jinja2 templates with client-side JavaScript for dynamic elements.
-   **Database Interaction**: `psycopg2` with connection pooling, raw SQL queries, and `RealDictCursor` for results.
-   **CORS**: Flask-CORS enabled for cross-origin requests.
-   **Caching**: Flask-Caching with SimpleCache for frequently accessed data (e.g., standards, recent activity) to reduce database load.
-   **Error Handling**: Centralized database error catching and user-friendly display on the frontend.
-   **Modularity**: Separation of concerns with dedicated API endpoints for Schema Explorer, CAD Standards, Data Management, and DXF tools.

### Key Features & Design
-   **Schema Explorer**: Provides database health checks, schema visualization, and project/drawing management capabilities. Includes an interactive network graph using Vis.js to visualize table relationships and row counts.
-   **CAD Standards Portal**: Designed to translate complex CAD database fields into an easily digestible format with visual aids (color swatches, SVG previews). It is a read-only reference.
-   **Data Manager**: Comprehensive CRUD interface for managing CAD standards data (Abbreviations, Layers, Blocks, Details) with features like searching, modal forms, CSV import (upsert), and CSV export. Clears cache on data modifications.
-   **DXF Tools**: Implements a full DXF round-trip workflow (import DXF to PostGIS, export PostGIS to DXF) using `ezdxf`. Features a normalized foreign key structure, a lookup service for name-to-UUID mapping, and PostGIS GeometryZ for 3D coordinates. Includes API endpoints and a UI for file upload, export configuration, and job tracking.
-   **Sheet Note Manager**: Backend infrastructure for managing construction drawing notes across projects and sheets. Includes standard note libraries, project-specific note sets, custom overrides, note reordering, assignment to drawing sheets/layouts, and generation of formatted note legends. The frontend is a React-based three-panel UI.

## External Dependencies

### Python Libraries
-   `Flask`
-   `Flask-Caching`
-   `psycopg2-binary`
-   `python-dotenv`
-   `flask-cors`
-   `ezdxf` (for DXF import/export)

### Database
-   `PostgreSQL 12+`
-   `PostGIS Extension`
-   `Supabase` (recommended hosting)

### Frontend Resources (CDNs)
-   `Font Awesome 6.4.0`
-   `Google Fonts` (Orbitron, Rajdhani)
-   `Vis.js` (for schema relationship visualization)

### Environment Configuration
-   `DB_HOST`
-   `DB_PORT`
-   `DB_NAME`
-   `DB_USER`
-   `DB_PASSWORD`

### Related Systems
-   **ACAD-GIS FastAPI application**: The main API server that shares the same PostgreSQL/PostGIS database.