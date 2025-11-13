# ACAD-GIS: AI-First CAD/GIS System

A revolutionary database-centric CAD/GIS platform optimized for AI/ML applications in civil engineering and surveying.

## Overview

ACAD-GIS replaces traditional file-based CAD workflows with a PostgreSQL/PostGIS database as the source of truth. The system provides intelligent DXF import/export, semantic layer naming, GraphRAG knowledge graphs, and vector embeddings for hybrid search across CAD/GIS data.

**Key Innovation:** Layer names are semantic labels, not data storage. All intelligence lives in the database.

## Core Features

### 🎯 CAD Standards System
- **Hierarchical Layer Naming:** `DISCIPLINE-CATEGORY-TYPE-ATTRIBUTE-PHASE-GEOMETRY`
- **Bulk Standards Editor:** Manage 6 vocabulary types (disciplines, categories, object types, phases, geometries, attributes)
- **Import Template Manager:** Configure client-specific layer mapping patterns with live regex testing
- **Standards Portal:** Visual documentation of the layer naming system

### 📐 DXF Tools
- **Intelligent Import:** Pattern-based classification creates database objects from CAD entities
- **Bidirectional Sync:** Track changes between CAD files and database
- **Export Engine:** Generate clean DXF files with standard or client-specific layer names
- **Change Detection:** Geometry hashing detects modifications for merge operations

### 🗺️ Map Viewer
- **Interactive Leaflet Map:** View all spatial data with coordinate transformation (SRID 0 ↔ SRID 2226)
- **Standards Filtering:** Filter layers by discipline, category, and phase
- **Multi-Format Export:** DXF, Shapefile, PNG, KML with bounding box selection
- **WFS Integration:** Load external GIS layers
- **Address Search & Measurement Tools**

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
- **Spatial:** SRID 2226 (CA State Plane) for GIS, SRID 0 for CAD
- **AI/ML:** OpenAI embeddings, semantic search, GraphRAG

## Quick Start

### 1. Database Setup
Configure your PostgreSQL/PostGIS database connection in `.env`:
```bash
DB_HOST=your-database-host
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-password
```

### 2. Run the Application
```bash
python app.py
```

Access at `http://localhost:5000`

### 3. Set Up CAD Standards
1. Navigate to **Standards > Bulk Standards Editor**
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
- **[CAD Standards Guide](CAD_STANDARDS_GUIDE.md)** - Comprehensive user guide and cheat sheet for the CAD standards system
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
**Last Updated:** November 9, 2025

### Recent Additions
- Standards integration with Map Viewer and DXF Tools
- Bulk Standards Editor and Import Template Manager
- Pattern-based intelligent object creation
- Gravity pipe network editor with SVG visualization

## Contributing

This is an open-source project focused on revolutionizing CAD/GIS workflows for civil engineering. The database schema and Python tools are designed to be extended for additional domains.

## License

See LICENSE file for details.

---

**Built with the database as the source of truth. 🗄️**
