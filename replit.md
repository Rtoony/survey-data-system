# ACAD-GIS Schema Explorer & Data Manager

## Overview

ACAD-GIS Schema Explorer is a Flask-based companion tool for viewing and managing Supabase/PostgreSQL databases used by the main ACAD-GIS system. It provides a web interface for browsing database schemas, managing projects, and viewing drawings. The tool connects directly to a PostgreSQL/PostGIS database and presents data through a Mission Control-themed UI.

The application serves as a lightweight administrative interface, distinct from the main ACAD-GIS FastAPI application, focusing specifically on database exploration and basic CRUD operations for projects and drawings.

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
- **Health Endpoint**: `/api/health` - Database connectivity check with table counts
- **Schema Endpoint**: `/api/schema` - Returns table structures and row counts
- **Projects Endpoint**: `/api/projects` - List projects with drawing counts, delete operations
- **Drawings Endpoint**: `/api/drawings` - List and delete drawings with project filtering

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

## External Dependencies

### Python Libraries
- **Flask 3.x**: Web framework
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