# ACAD-GIS: AI-First CAD/GIS System

## Overview

ACAD-GIS is an **AI-first, database-centric CAD/GIS system** optimized for machine learning, embeddings, and GraphRAG (Graph Retrieval-Augmented Generation). The system replaces traditional file-bound CAD workflows with a PostgreSQL/PostGIS database designed specifically for AI understanding and semantic reasoning.

### Core Value Proposition
- **Unified Entity Model**: Every CAD element, survey point, and engineering feature has a canonical identity for AI reasoning
- **Centralized Embeddings**: Vector embeddings with versioning and multi-model support for semantic search
- **Explicit Graph Edges**: Pre-computed spatial and engineering relationships for GraphRAG traversal
- **ML Feature Engineering**: Built-in tables for spatial statistics, network metrics, and predictions
- **Hybrid Search**: Combined full-text search, vector similarity, and quality scoring

### Applications
1.  **Schema Explorer & Data Manager**: Administrative tool for visualizing schemas, managing projects, and CAD standards
2.  **CAD Standards Portal**: User-friendly reference for AI-optimized CAD standards (layers, blocks, colors, etc.)
3.  **Python ML Tools**: Design tools that leverage the AI-optimized database for intelligent CAD operations

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Technologies
-   **Database**: PostgreSQL 12+ with PostGIS 3.3+ and pgvector 0.8+ extensions
-   **AI/ML Stack**: Vector embeddings (1536 dimensions), GraphRAG, full-text search (tsvector)
-   **Web Framework**: Flask (Python) for server-rendered HTML and JSON APIs
-   **Frontend**: Jinja2 templating, Mission Control-themed CSS, vanilla JavaScript
-   **Spatial**: PostGIS with SRID 2226 (California State Plane Zone 2, US Survey Feet)

### AI-First Database Architecture
-   **Unified Entity Registry**: `standards_entities` table provides canonical identity for all CAD/GIS elements
-   **Centralized Embeddings**: `entity_embeddings` table with versioning and multi-model support
-   **Graph Edges**: `entity_relationships` table for explicit spatial, engineering, and semantic relationships
-   **Quality Scoring**: Every table includes `quality_score` column for data quality tracking
-   **Full-Text Search**: All tables have `search_vector` tsvector columns with weighted search
-   **JSONB Attributes**: Flexible metadata storage in `attributes` columns across all tables
-   **Vector Indexing**: IVFFlat indexes on embeddings for fast similarity search
-   **Spatial Indexing**: GIST indexes on PostGIS geometry columns for spatial queries

### Architectural Patterns & Decisions
-   **AI-First Design**: Database schema optimized for machine learning and LLM understanding
-   **Graph Database Patterns**: Explicit relationship tables enable GraphRAG multi-hop queries
-   **Spatial-Semantic Fusion**: Combines PostGIS spatial operations with vector similarity search
-   **Quality-Driven**: All entities have quality scores based on completeness, embeddings, and relationships
-   **Server-Side Rendering**: Flask serves Jinja2 templates, augmented by client-side JavaScript
-   **Database Interaction**: `psycopg2` with connection pooling, raw SQL, and `RealDictCursor`
-   **Materialized Views**: Pre-computed views for fast AI queries (enriched points, graph summaries, spatial clusters)

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

---

## AI-Optimized Database Schema

### Database Migration (October 2025)
The entire ACAD-GIS database was rebuilt from scratch with AI/ML as the primary design goal. All test data was wiped and the schema was optimized for:
- Vector embeddings and semantic search
- GraphRAG (Graph Retrieval-Augmented Generation)
- Machine learning feature engineering
- Spatial-semantic fusion queries

### Core AI Infrastructure Tables

#### 1. `embedding_models` - Model Registry
Tracks which embedding models are used for vector generation (OpenAI ada-002, Cohere, local models, etc.)
- Supports multiple models simultaneously
- Tracks model versions and configurations
- Enables model comparison and experimentation

#### 2. `standards_entities` - Unified Entity Model
**Purpose**: Gives every CAD standard, drawing element, and survey point a canonical identity for AI reasoning.

Key columns:
- `entity_id` (UUID): Global unique identifier
- `entity_type`: 'layer', 'block', 'survey_point', 'utility_line', etc.
- `canonical_name`: Standardized name for the entity
- `source_table` + `source_id`: Links back to the original table
- `quality_score`: Data quality metric (0.0-1.0)
- `tags`: Array of categorization tags
- `attributes`: JSONB for flexible metadata
- `search_vector`: Full-text search index (auto-updated via trigger)

**Why it matters**: AI can now reason about "entities" uniformly across the entire database, enabling entity resolution, cross-table semantic search, and knowledge graph construction.

#### 3. `entity_embeddings` - Centralized Vector Storage
**Purpose**: Single source of truth for all vector embeddings with versioning and multi-model support.

Key features:
- Supports embeddings from multiple models (1536 dimensions by default)
- Version tracking for embedding updates
- `is_current` flag for active embeddings
- Quality metrics per embedding
- IVFFlat index for fast cosine similarity search

**Why it matters**: Easier to manage, version, and optimize embeddings. Enables semantic search across all entity types.

#### 4. `entity_relationships` - Graph Edges for GraphRAG
**Purpose**: Explicit relationships between entities enabling graph traversal and multi-hop reasoning.

Relationship types:
- **Spatial**: `adjacent_to`, `contains`, `within`, `intersects`, `near`
- **Engineering**: `upstream_of`, `downstream_of`, `serves`, `connects_to`
- **Semantic**: `similar_to`, `replaces`, `part_of`, `derived_from`

Key columns:
- `subject_entity_id` → `predicate` → `object_entity_id`
- `confidence_score`: Relationship confidence (0.0-1.0)
- `spatial_relationship`: Boolean flag for spatial edges
- `ai_generated`: Boolean flag for ML-discovered relationships

**Why it matters**: Enables GraphRAG multi-hop queries like "find all utilities within 50 feet of survey point X" or "what layers are typically used with this block?"

#### 5. `entity_aliases` - Deduplication & Resolution
**Purpose**: Prevents duplicate embeddings and improves entity matching.

Tracks alternative names, abbreviations, and common misspellings for entities to enable fuzzy matching and entity resolution.

### AI Features in Every Table

All 77 tables in the ACAD-GIS database include these AI-optimized columns:

```sql
-- Core AI columns (present in all tables)
entity_id UUID REFERENCES standards_entities(entity_id)
quality_score NUMERIC(4, 3)  -- 0.0 to 1.0
tags TEXT[]
attributes JSONB DEFAULT '{}'::jsonb
search_vector tsvector
usage_frequency INTEGER DEFAULT 0  -- where applicable
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### Materialized Views for Fast AI Queries

#### `mv_survey_points_enriched`
Pre-computed enriched survey points with spatial context:
- Nearby point count (within 100 feet)
- Distance to nearest control point
- Linked to standards_entities metadata

#### `mv_entity_graph_summary`
Relationship statistics for each entity:
- Outgoing/incoming relationship counts
- Relationship predicates (types of connections)
- Total connectivity score
- Spatial vs engineering vs AI-generated relationship counts

#### `mv_spatial_clusters`
K-means spatial clustering of survey points:
- Clusters grouped by project and point type
- Enables pattern recognition and outlier detection
- Supports spatial analysis workflows

### ML Feature Engineering Tables

#### `spatial_statistics`
Pre-computed spatial metrics by project region:
- Point density, elevation statistics (min/max/mean/variance)
- Spatial dispersion and clustering coefficients
- Feature type counts (control points, trees, utilities)
- Area calculations

#### `network_metrics`
Graph analysis metrics for each entity:
- Centrality measures (degree, betweenness, closeness, eigenvector, PageRank)
- Clustering coefficient and path length
- Community detection results
- Influence and trust scores

#### `temporal_changes`
Change tracking for ML time-series analysis:
- Before/after state snapshots (JSONB)
- Changed fields tracking
- Change magnitude and significance scores
- Spatial displacement for geometry changes

#### `classification_confidence`
ML prediction results with explainability:
- Model name and version
- Predicted class with confidence score
- Probability distributions and top-K predictions
- Feature importance for explainability
- Ground truth comparison (if available)

### Database Helper Functions

#### `compute_quality_score(required_fields, total_fields, has_embedding, has_relationships)`
Computes entity quality score based on:
- Data completeness (70%)
- Has embeddings (15% bonus)
- Has relationships (15% bonus)

#### `find_similar_entities(entity_id, similarity_threshold, max_results)`
Vector similarity search returning:
- Similar entities above threshold
- Cosine similarity scores
- Filtered by quality and relevance

#### `find_related_entities(entity_id, max_hops, relationship_types)`
GraphRAG multi-hop traversal:
- Recursive graph walking up to N hops
- Optional filtering by relationship type
- Returns relationship paths

#### `hybrid_search(text_query, vector_query, entity_types, min_quality, max_results)`
Combined search using:
- Full-text search (30% weight)
- Vector similarity (50% weight)
- Quality score (20% weight)
- Filtered by entity type and quality threshold

### Indexing Strategy

**518 Total Indexes** across all tables:
- **338 B-tree indexes**: Frequent queries (IDs, foreign keys, status, dates, quality scores)
- **163 GIN indexes**: JSONB attributes, text arrays (tags), tsvector (search_vector)
- **17 GIST indexes**: PostGIS spatial columns (geometry)

**Vector Indexes**: IVFFlat with 100 lists for embeddings (cosine similarity operations)

**Composite Indexes**: Support hybrid queries combining multiple criteria

### Usage Examples

#### Example 1: Semantic Search Across All Entities
```python
# Find all entities related to "stormwater drainage"
results = db.query("""
    SELECT * FROM hybrid_search(
        'stormwater drainage',  -- text query
        NULL,  -- vector query (or pass embedding)
        ARRAY['utility_line', 'utility_structure'],  -- filter by type
        0.5,  -- minimum quality score
        20  -- max results
    )
""")
```

#### Example 2: GraphRAG Multi-Hop Query
```python
# Find all entities within 2 hops of a survey point
results = db.query("""
    SELECT * FROM find_related_entities(
        'uuid-of-survey-point',
        2,  -- max hops
        ARRAY['spatial', 'engineering']  -- relationship types
    )
""")
```

#### Example 3: Spatial-Semantic Fusion
```python
# Find survey points near a location that are semantically similar
results = db.query("""
    SELECT sp.*, ee.embedding <=> query_embedding as similarity
    FROM survey_points sp
    JOIN entity_embeddings ee ON sp.entity_id = ee.entity_id
    WHERE ST_DWithin(sp.geometry, query_point, 100)
        AND ee.is_current = TRUE
        AND 1 - (ee.embedding <=> query_embedding) > 0.8
    ORDER BY similarity DESC
""")
```

#### Example 4: Refresh Materialized Views
```python
# Update pre-computed views after data changes
db.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_survey_points_enriched")
db.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_entity_graph_summary")
db.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_spatial_clusters")
```

### Schema Statistics

- **77 Total Tables**: Complete ACAD-GIS schema
- **5 Core AI Tables**: Infrastructure for embeddings and GraphRAG
- **4 ML Tables**: Feature engineering and predictions
- **3 Materialized Views**: Pre-computed AI queries
- **64 Domain Tables**: Projects, drawings, CAD standards, DXF tools, sheets, survey/civil
- **104 Triggers**: Auto-update search_vector on text changes
- **4 Helper Functions**: Quality scoring, similarity search, GraphRAG, hybrid search

---