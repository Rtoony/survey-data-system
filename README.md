# ACAD-GIS: AI-First CAD/GIS System

A revolutionary database-centric CAD/GIS platform optimized for AI/ML applications in civil engineering and surveying.

## Overview

ACAD-GIS replaces traditional file-based CAD workflows with a PostgreSQL/PostGIS database as the source of truth. The system provides intelligent DXF import/export, semantic layer naming, GraphRAG knowledge graphs, and vector embeddings for hybrid search across CAD/GIS data.

**Key Innovation:** Layer names are semantic labels, not data storage. All intelligence lives in the database.

## Core Features

### 🎯 CAD Standards System
- **Hierarchical Layer Naming:** `DISCIPLINE-CATEGORY-TYPE-ATTRIBUTE-PHASE-GEOMETRY`
- **CAD Layer Vocabulary:** Manage 6 vocabulary types (disciplines, categories, object types, phases, geometries, attributes)
- **Attribute System:** Three-dimensional filtering (Object Type → Attribute → Database Table) for surgical precision in tool workflows. See [ATTRIBUTE_SYSTEM_GUIDE.md](ATTRIBUTE_SYSTEM_GUIDE.md)
- **Reference Data Hub:** Manage 9 types of project-agnostic reference data (Attribute Codes, CAD Standards, Clients, Municipalities, Coordinate Systems, Survey Point Descriptions, Naming Templates, Tool-Object Mappings, Specialized Tools Registry)
- **Import Template Manager:** Configure client-specific layer mapping patterns with live regex testing
- **Standards Portal:** Visual documentation of the layer naming system

### 📐 DXF Tools & Projects Only System
- **Intelligent Import:** Pattern-based classification creates database objects from CAD entities
- **Hybrid Classification:** Automatic classification for high-confidence entities (≥0.7), manual review for low-confidence
- **Generic Objects Workflow:** Unclassified entities saved for review instead of dropped
- **Object Reclassifier Tool:** Interactive UI for reviewing and reclassifying unclassified DXF entities
- **Project-Level Linking:** Entities link directly to projects (no drawing files required)
- **Bidirectional Sync:** Track changes between CAD files and database
- **Export Engine:** Generate clean DXF files with standard or client-specific layer names
- **Change Detection:** Geometry hashing detects modifications for merge operations

### 🗺️ Visualization Tools
**Full documentation:** [VISUALIZATION_TOOLS.md](VISUALIZATION_TOOLS.md)

#### Enhanced Map Viewer
Full-featured spatial workbench for CAD/GIS analysis:
- **Interactive Leaflet Map:** View all spatial data with coordinate transformation (SRID 2226 ↔ SRID 4326 for web display)
- **Layer Controls:** Toggle individual layers, expand groups, view feature counts
- **Basemap Selection:** Streets, Satellite, Topo, Dark basemap options
- **Multi-Format Export:** DXF, Shapefile, PNG, KML with bounding box selection
- **Measurement Tools:** Distance and area measurement capabilities
- **Address Search:** Geocoding integration with auto-zoom
- **Full-Screen Mode:** Press `F` or click button to maximize workspace (optimized for wide-screen monitors)

#### Project Command Center
Streamlined project management dashboard:
- **Collapsible Sidebar:** 250px sidebar with 10 tools and 24 CAD standards
- **Read-Only Context Map:** Auto-fit project overview with layer toggles
- **Basemap Selection:** Switch between Streets/Satellite/Topo/Dark for context
- **Health Metrics:** Real-time project statistics (entities, layers, intelligent objects, drawings)
- **Quick Access:** One-click navigation to all project tools
- **Full-Screen Mode:** Click button or press `ESC` to maximize workspace

### 🔧 Civil Engineering Tools
- **Gravity Pipe Network Editor:** Interactive SVG diagrams with auto-connection and classification
- **Sheet Note Manager:** Construction sheet notes database
- **Sheet Set Manager:** Deliverables tracking
- **Survey & Civil Schema:** Comprehensive database for civil/survey workflows

### 🤖 AI Toolkit
- **Vector Embeddings:** 1536-dimension OpenAI embeddings with pgvector
- **Knowledge Graph:** Explicit relationship tables for GraphRAG multi-hop queries
- **Quality Scoring:** Automated data quality assessment
- **Full-Text Search:** Weighted tsvector search across all entities
- **Materialized Views:** Pre-computed AI-optimized queries
- **Interactive Visualizations:** Vis.js graph viewer and quality dashboard

## Technology Stack

- **Database:** PostgreSQL 12+ with PostGIS 3.3+ and pgvector 0.8+
- **Backend:** Flask (Python) with server-rendered Jinja2 templates
- **Frontend:** Vanilla JavaScript, Leaflet.js, Mission Control theme
- **Spatial:** PostGIS with SRID 2226 (CA State Plane Zone 3) for all geometry storage
- **AI/ML:** OpenAI embeddings, semantic search, GraphRAG

## Quick Start

### 1. Environment Setup
Copy the example environment file and configure your settings:
```bash
cp .env.example .env
```

Edit `.env` with your values:
```bash
# Database connection (required)
DB_HOST=your-database-host
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-password

# Flask security (required for production)
SECRET_KEY=your-secret-key-here

# OpenAI API (optional - for AI/ML features)
OPENAI_API_KEY=your-openai-api-key
```

See `.env.example` for complete configuration options including PostgreSQL standard variables.

### 2. Run the Application
```bash
python app.py
```

Access at `http://localhost:5000`

### 3. Set Up CAD Standards
1. Navigate to **Standards > CAD Layer Vocabulary**
2. Add your disciplines, categories, object types, and phases
3. Create import patterns in **Standards > Import Template Manager** for your client formats

### 4. Import Your First DXF
1. Go to **DXF Tools**
2. Create or select a project
3. Choose an import pattern (optional)
4. Upload your DXF file
5. View classification statistics

## Documentation

### Essential Guides
- **[Attribute System Guide](ATTRIBUTE_SYSTEM_GUIDE.md)** - Complete guide to three-dimensional filtering (Object Type → Attribute → Database Table)
- **[CAD Standards Guide](CAD_STANDARDS_GUIDE.md)** - Comprehensive user guide and cheat sheet for the CAD standards system
- **[Projects Only Migration Guide](archive/completed-migrations/PROJECTS_ONLY_MIGRATION_GUIDE.md)** - Complete guide to the new Projects Only system with hybrid classification
- **[replit.md](replit.md)** - Project overview, architecture, and recent changes
- **[Database Architecture Guide](DATABASE_ARCHITECTURE_GUIDE.md)** - Technical deep dive into AI-first database design
- **[AI Optimization Guide](AI_DATABASE_OPTIMIZATION_GUIDE.md)** - ML/AI features and optimization patterns

### Developer Resources
- **[Database Schema](database/SCHEMA_VERIFICATION.md)** - Complete schema reference (81 tables)
- **[AI Toolkit](tools/README.md)** - Python modules for embeddings, relationships, validation
- **[Example Scripts](examples/README.md)** - Sample workflows for data ingestion and processing

## Architecture Highlights

### AI-First Database Design
- **Unified Entity Registry:** `standards_entities` table as canonical identity
- **Centralized Embeddings:** `entity_embeddings` with versioning
- **Graph Edges:** `entity_relationships` for GraphRAG
- **Quality Metrics:** Completeness, embedding coverage, relationship depth
- **Vector Indexing:** IVFFlat indexes for fast similarity search
- **Spatial Indexing:** GIST indexes on PostGIS geometries

### Intelligent DXF Workflow
```
Legacy DXF → Pattern Matching → Database Objects → Standard Layers → Clean DXF
```

1. **Import:** DXF with any layer format → regex patterns extract intent → create database objects
2. **Process:** Enrich data with ML, relationships, validation
3. **Export:** Database objects → generate layer names → DXF output

## Key Use Cases

### Civil Engineering
- Storm drainage networks with automatic pipe/structure classification
- Grading plans with surface models and contour generation
- Road design with alignments and cross-sections
- ADA compliance tracking

### Surveying
- Control point networks with accuracy metadata
- Topographic surveys with feature classification
- Boundary surveys with parcel relationships
- Construction staking with phase tracking

### Multi-Discipline Coordination
- Filter layers by discipline for consultant deliverables
- Track relationships between civil, site, and utility elements
- Generate discipline-specific exports from unified database
- Maintain consistency across project lifecycle

## System Benefits

✅ **AI-Friendly:** Clear hierarchical structure for LLM understanding  
✅ **Flexible:** Support any client's CAD standards via import patterns  
✅ **Intelligent:** ML-driven classification, validation, and quality scoring  
✅ **Scalable:** Database handles millions of entities efficiently  
✅ **Auditable:** Track all changes with version control  
✅ **Collaborative:** Single source of truth for all disciplines  

## Project Status

**Current Version:** Production-ready core features  
**Last Updated:** November 15, 2025

### Recent Additions (November 2025)
- DXF Test Generator for validating import workflows (PR #31)
- Projects Only System with hybrid intelligent object classification
- Object Reclassifier Tool for reviewing unclassified DXF entities
- CAD Layer Vocabulary and Reference Data Hub with clean separation
- Survey Point Descriptions API and database table
- Standards integration with Map Viewer and DXF Tools
- Pattern-based intelligent object creation with confidence scoring

## Contributing

This is an open-source project focused on revolutionizing CAD/GIS workflows for civil engineering. The database schema and Python tools are designed to be extended for additional domains.

## License

See LICENSE file for details.

---

**Built with the database as the source of truth. 🗄️**
