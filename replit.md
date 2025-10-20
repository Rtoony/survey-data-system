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