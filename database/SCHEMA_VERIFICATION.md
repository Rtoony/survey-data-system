# ACAD-GIS AI-First Database Schema Verification

## Schema Export Date
October 30, 2025

## Schema Statistics

### Tables
- **Total Tables**: 81
- **Core AI Infrastructure**: 5 tables
  - `embedding_models`
  - `standards_entities`
  - `entity_embeddings`
  - `entity_relationships`
  - `entity_aliases`
- **ML Feature Engineering**: 4 tables
  - `spatial_statistics`
  - `network_metrics`
  - `temporal_changes`
  - `classification_confidence`
- **Domain Tables**: 71 tables (projects, CAD standards, survey/civil, etc.)

### Materialized Views
- `mv_survey_points_enriched` - Survey points with spatial context
- `mv_entity_graph_summary` - Relationship statistics
- `mv_spatial_clusters` - K-means spatial clustering

### Indexes
- **Total Indexes**: 700+
- **B-tree Indexes**: For IDs, foreign keys, dates, quality scores
- **GIN Indexes**: For JSONB, text arrays, tsvector
- **GIST Indexes**: For PostGIS geometry columns
- **IVFFlat Vector Indexes**: For embedding similarity search

### Functions
- **Total Functions**: 961
- **Custom Helper Functions**: 4
  - `compute_quality_score()` - Calculate entity quality
  - `find_similar_entities()` - Vector similarity search
  - `find_related_entities()` - GraphRAG multi-hop traversal
  - `hybrid_search()` - Combined full-text + vector + quality search
- **Trigger Functions**: 104 (auto-update search_vector columns)

### Extensions
- **postgis**: 3.3.3 - Spatial data types and operations
- **vector**: 0.8.0 - Vector embeddings and similarity search
- **pg_trgm**: Trigram-based fuzzy text matching
- **uuid-ossp**: UUID generation

## AI Optimization Patterns

### Standard Columns (Present in All Tables)
```sql
entity_id UUID REFERENCES standards_entities(entity_id) ON DELETE SET NULL
quality_score NUMERIC(4, 3)  -- 0.0 to 1.0
tags TEXT[]
attributes JSONB DEFAULT '{}'::jsonb
search_vector tsvector
usage_frequency INTEGER DEFAULT 0
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### Indexing Pattern
Every table includes:
- B-tree index on `entity_id`
- B-tree index on `quality_score DESC NULLS LAST`
- GIN index on `tags`
- GIN index on `attributes`
- GIN index on `search_vector`

### Spatial Tables (17 total)
All spatial tables include:
- PostGIS geometry column (PointZ, LineStringZ, or PolygonZ with SRID 2226)
- GIST spatial index
- AI optimization columns

## Key Table List

### Core AI Infrastructure
1. `embedding_models` - Model registry (OpenAI, Cohere, etc.)
2. `standards_entities` - Unified entity identity
3. `entity_embeddings` - Centralized vector storage
4. `entity_relationships` - Graph edges for GraphRAG
5. `entity_aliases` - Entity resolution and deduplication

### ML Feature Engineering
1. `spatial_statistics` - Point density, elevation stats
2. `network_metrics` - Graph centrality, PageRank
3. `temporal_changes` - Change tracking
4. `classification_confidence` - ML predictions

### Projects
1. `projects` - Project management

### CAD Standards
1. `layer_standards` - Layer definitions
2. `block_definitions` - Block library
3. `color_standards` - Color palette
4. `linetypes` - Linetype library
5. `text_styles` - Text style definitions
6. `hatch_patterns` - Hatch pattern library
7. `plot_styles` - Plot style tables

### CAD Content
1. `detail_standards` - Standard details
2. `abbreviation_standards` - Abbreviations
3. `material_standards` - Material specifications
4. `category_standards` - Categories
5. `code_standards` - Code references
6. `annotation_standards` - Annotation styles
7. `standard_notes` - Standard notes library
8. `drawing_scale_standards` - Scale standards

### DXF Tools
1. `layers` - Project-level CAD layers
2. `block_inserts` - Block placements
3. `cad_entities` - CAD primitives
4. `cad_text` - Text annotations
5. `cad_dimensions` - Dimensions
6. `cad_hatches` - Hatch fills
7. `layout_viewports` - Viewport configurations
8. `export_jobs` - DXF export tracking

### Sheet Management
1. `sheet_sets` - Sheet set organization
2. `sheets` - Individual sheets
3. `sheet_revisions` - Revision tracking
4. `sheet_relationships` - Sheet dependencies
5. `sheet_note_sets` - Note libraries
6. `project_sheet_notes` - Project notes
7. `sheet_note_assignments` - Note-sheet links

### Survey & Civil (29 tables)
**Survey & Control:**
1. `coordinate_systems` - Coordinate system definitions
2. `survey_points` - All survey points
3. `survey_control_network` - Control networks
4. `control_point_membership` - Network memberships

**Site Features:**
5. `site_trees` - Tree inventory
6. `utility_structures` - Manholes, valves, etc.
7. `surface_features` - Curbs, fences, walls

**Alignments & Profiles:**
8. `horizontal_alignments` - Horizontal centerlines
9. `alignment_pis` - Points of intersection
10. `vertical_profiles` - Vertical profiles
11. `profile_pvis` - Vertical PIs

**Cross Sections & Earthwork:**
12. `cross_sections` - Cross section data
13. `cross_section_points` - Cross section points
14. `earthwork_quantities` - Volume calculations
15. `earthwork_balance` - Mass haul data

**Utility Networks:**
16. `utility_lines` - Pipes and conduits
17. `utility_network_connectivity` - Network topology
18. `utility_service_connections` - Service laterals

**Property:**
19. `parcels` - Land parcels
20. `parcel_corners` - Property corners
21. `easements` - Easement boundaries
22. `right_of_way` - ROW boundaries

**Survey Observations:**
23. `survey_observations` - Raw field data
24. `traverse_loops` - Traverse loop definitions
25. `traverse_loop_observations` - Loop measurements

**Civil Design:**
26. `grading_limits` - Grading boundaries
27. `pavement_sections` - Pavement design
28. `surface_models` - TIN/DTM metadata
29. `typical_sections` - Roadway templates

## Verification Queries

### Check Core AI Tables Exist
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN (
    'embedding_models',
    'standards_entities',
    'entity_embeddings',
    'entity_relationships',
    'entity_aliases'
  )
ORDER BY table_name;
```

### Check Materialized Views
```sql
SELECT matviewname 
FROM pg_matviews 
WHERE schemaname = 'public'
ORDER BY matviewname;
```

### Check Helper Functions
```sql
SELECT proname 
FROM pg_proc 
WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
  AND proname IN (
    'compute_quality_score',
    'find_similar_entities',
    'find_related_entities',
    'hybrid_search'
  )
ORDER BY proname;
```

### Check Index Count
```sql
SELECT 
    schemaname,
    COUNT(*) as total_indexes
FROM pg_indexes 
WHERE schemaname = 'public'
GROUP BY schemaname;
```

### Verify Entity Columns Pattern
```sql
SELECT 
    table_name,
    COUNT(*) as ai_columns
FROM information_schema.columns
WHERE table_schema = 'public'
  AND column_name IN ('entity_id', 'quality_score', 'tags', 'attributes', 'search_vector')
GROUP BY table_name
HAVING COUNT(*) >= 4
ORDER BY ai_columns DESC, table_name;
```

## Complete Schema Export

The complete schema DDL is available in: `database/schema/complete_schema.sql` (9,976 lines)

This file contains:
- All table definitions with columns, constraints, and data types
- All indexes (B-tree, GIN, GIST, IVFFlat)
- All functions and triggers
- All materialized view definitions
- Extension configurations
- Comments and documentation

## Next Steps

1. **Data Population**: Start adding data to the tables
2. **Embedding Generation**: Generate embeddings for entities using OpenAI/Cohere
3. **Relationship Building**: Create spatial and engineering relationships
4. **Quality Scoring**: Calculate quality scores for all entities
5. **Materialized View Refresh**: Populate pre-computed views
6. **Testing**: Test hybrid search, GraphRAG, and spatial queries
