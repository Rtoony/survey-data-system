# ACAD-GIS Companion Tools

## Overview

This project contains two Flask-based companion tools for the main ACAD-GIS system:

1. **Schema Explorer & Data Manager** - Database administration tool for viewing schemas, managing projects, and cleaning up test data
2. **CAD Standards Portal** - Human-friendly reference portal presenting machine-optimized CAD standards (layers, blocks, colors, etc.) in a readable format for employees

Both tools connect to the same Supabase/PostgreSQL database and present data through a Mission Control-themed UI. They serve as lightweight administrative and reference interfaces, distinct from the main ACAD-GIS FastAPI application.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Web Framework
- **Flask**: Lightweight Python web framework serving HTML templates and JSON API endpoints
- **Pattern**: Traditional server-rendered templates (Jinja2) with client-side JavaScript for dynamic updates
- **CORS Enabled**: Flask-CORS middleware to allow cross-origin requests

### Database Layer
- **PostgreSQL + PostGIS**: Primary data store (typically Supabase-hosted)
- **Connection**: psycopg2 with connection pooling via context managers
- **Query Pattern**: Raw SQL queries with RealDictCursor for dict-like results
- **Configuration**: Environment-based credentials loaded from .env file or Replit Secrets

### Frontend Architecture
- **Template Engine**: Jinja2 templates with base template inheritance
- **Styling**: Mission Control theme with CSS variables for consistent dark blue/cyan aesthetic
- **Fonts**: Orbitron (headings) and Rajdhani (body) from Google Fonts
- **Client-side**: Vanilla JavaScript with async/await for API calls
- **Icons**: Font Awesome 6.4.0

### API Structure

**Schema Explorer Endpoints:**
- **Health Endpoint**: `/api/health` - Database connectivity check with table counts
- **Schema Endpoint**: `/api/schema` - Returns table structures and row counts
- **Projects Endpoint**: `/api/projects` - List projects with drawing counts, delete operations
- **Drawings Endpoint**: `/api/drawings` - List and delete drawings with project filtering
- **Recent Activity**: `/api/recent-activity` - Dashboard data showing 5 most recent projects, 5 most recent drawings, and database stats (cached 60s)

**CAD Standards Portal Endpoints:**
- **Overview**: `/api/standards/overview` - Statistics for all standards tables (17 total)
- **Layers**: `/api/standards/layers` - Layer standards with colors, linetypes, discipline
- **Blocks**: `/api/standards/blocks` - Block/symbol definitions with SVG previews
- **Colors**: `/api/standards/colors` - Color standards with RGB, HEX, ACI values
- **Linetypes**: `/api/standards/linetypes` - Linetype patterns and usage
- **Text Styles**: `/api/standards/text` - Text style specifications
- **Hatches**: `/api/standards/hatches` - Hatch patterns for materials
- **Details**: `/api/standards/details` - Standard construction details
- **Abbreviations**: `/api/standards/abbreviations` - Standard CAD abbreviations with full text
- **Materials**: `/api/standards/materials` - Construction material specifications
- **Sheet Templates**: `/api/standards/sheets` - Standard sheet sizes and templates
- **Plot Styles**: `/api/standards/plotstyles` - Plot style standards for printing
- **Viewports**: `/api/standards/viewports` - Viewport scale standards
- **Annotations**: `/api/standards/annotations` - Annotation style standards
- **Symbol Categories**: `/api/standards/categories` - Hierarchical symbol organization
- **Code References**: `/api/standards/codes` - Building codes and regulatory references
- **Standard Notes**: `/api/standards/notes` - Pre-approved drawing notes library
- **Drawing Scales**: `/api/standards/scales` - Standard drawing scales by type

### Key Design Decisions

**Why Flask over FastAPI for this tool?**
- Simpler server-rendered approach for administrative UI
- Separate from main ACAD-GIS FastAPI application
- Minimal dependencies and quick setup for database exploration

**Database Connection Pattern**
- Context managers (`@contextmanager`) ensure proper connection cleanup
- Separate `get_db()` and `execute_query()` helpers for DRY code
- SSL mode configurable (defaulting to 'require' for Supabase)

**Template Inheritance**
- Base template (`base.html`) provides consistent header, navigation, and layout
- Child templates extend base and override content blocks
- Shared status checking and health monitoring across all pages

**Error Handling Strategy**
- Database errors caught and returned as JSON with error keys
- Frontend displays user-friendly error messages with icons
- Connection validation on startup with debug output to console

**CAD Standards Portal Design**
- Translates machine-optimized database fields into human-readable format
- Visual presentation: color swatches, SVG symbol previews, organized tables
- Grouped by discipline/category for easy browsing
- Read-only reference portal (no editing capabilities)
- Eventually intended to become standalone company reference website

**Caching Strategy**
- Flask-Caching configured with SimpleCache (in-memory)
- Standards endpoints cached for 10 minutes (600s) - standards data rarely changes
- Recent activity endpoint cached for 1 minute (60s) - provides fast dashboard loads while staying reasonably fresh
- Cache reduces database load and improves response times significantly

**Recent Activity Dashboard**
- Home page displays real-time overview of database activity
- Shows 4 stat cards: total projects, drawings, layer standards, and block standards
- Lists 5 most recently created projects with client info and drawing counts
- Lists 5 most recently created drawings with project context
- Relative timestamps (e.g., "2h ago", "3d ago") for user-friendly time display

**Schema Relationships Visualization (Added October 2025)**
- Interactive network graph showing database table relationships using Vis.js library
- Backend API `/api/schema/relationships` queries PostgreSQL foreign keys via information_schema
- Visualizes 53 tables and 40 foreign key relationships with physics-based layout
- Features:
  - Color-coded nodes by table type (projects, drawings, standards, etc.)
  - Node size reflects row count (logarithmic scale)
  - Interactive zoom, pan, drag, and click functionality
  - Detailed table information panel shows columns, relationships, and stats
  - Pause/Resume animation and Reset View controls
  - Relationship arrows indicate foreign key direction with column names on hover
- Performance optimized using pg_stat_user_tables for fast row count estimates
- Accessible via Relationships navigation menu item

**Data Manager (Added October 2025)**
- Complete CRUD interface for managing CAD standards data directly in the database
- Four data management sections: Abbreviations, Layers, Blocks, and Details
- Features per manager:
  - Searchable tables with real-time filtering
  - Add/Edit/Delete individual records via modal forms
  - CSV Import: Upsert mode (adds new records or updates existing based on unique identifiers)
  - CSV Export: Download current data for backup or editing
  - SVG preview capability for block symbols
  - Color swatch display for layer standards
- All managers follow consistent UI/UX patterns with Mission Control theme
- Cache clearing on data modifications to ensure fresh reads
- Proper field mapping between CSV columns and database fields

**DXF/GIS Export Schema (Added October 2025)**
- Enhanced database schema to support complete DXF/DWG export capability
- 8 new tables added for storing actual drawing content and export tracking:
  1. **drawing_entities** - Generic CAD primitives (lines, polylines, arcs, circles, ellipses, splines) with PostGIS geometry
  2. **drawing_text** - Text annotations with insertion points, styles, rotation, and justification
  3. **drawing_dimensions** - Dimension annotations (linear, aligned, angular, radial, diametric, ordinate)
  4. **drawing_hatches** - Hatch pattern instances with boundary geometry
  5. **layout_viewports** - Paperspace viewport configurations with scale, view center, and frozen layers
  6. **export_jobs** - DXF/DWG export operation tracking with status, metrics, and output files
  7. **drawing_layer_usage** - Tracks which layers are actively used in each drawing
  8. **drawing_linetype_usage** - Tracks which linetypes are actively used in each drawing
- All entity tables support:
  - PostGIS GeometryZ for 3D coordinates
  - DXF handle preservation for round-trip consistency
  - Model/Paper space designation
  - Visual properties (color ACI, lineweight, transparency)
  - JSONB metadata for flexibility
- Existing tables (drawings, block_inserts, layers) already provide:
  - Drawing-level georeferencing and coordinate systems
  - Block instance tracking with transformations
  - Layer-to-standard relationships
- Export workflow supports:
  - Multiple DXF versions (AC1027/AutoCAD 2013 and newer)
  - Coordinate system transformation
  - Layer and entity type filtering
  - Layout/paperspace inclusion
  - Job status tracking and error handling

## External Dependencies

### Python Libraries
- **Flask 3.x**: Web framework
- **Flask-Caching**: Response caching for improved performance
- **psycopg2-binary**: PostgreSQL adapter
- **python-dotenv**: Environment variable management
- **flask-cors**: Cross-Origin Resource Sharing support

### Database
- **PostgreSQL 12+**: Required database
- **PostGIS Extension**: Geospatial capabilities (inherited from ACAD-GIS main system)
- **Supabase**: Recommended hosting platform (or local PostgreSQL)

### Frontend CDN Resources
- **Font Awesome 6.4.0**: Icon library
- **Google Fonts**: Orbitron and Rajdhani typefaces

### Environment Configuration
Required environment variables:
- `DB_HOST`: Database host (e.g., `project.supabase.co`)
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name (default: postgres)
- `DB_USER`: Database user (default: postgres)
- `DB_PASSWORD`: Database password (required)

### Related Systems
This tool is designed to work alongside the main **ACAD-GIS FastAPI** application documented in attached assets:
- Main API server runs on port 8000
- This Schema Explorer typically runs on port 5000
- Both connect to the same PostgreSQL/PostGIS database
- Separate codebases with different purposes (production API vs. admin tool)