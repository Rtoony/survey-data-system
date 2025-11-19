-- ============================================================================
-- PERFORMANCE INDEXES FOR SURVEY DATA SYSTEM
-- ============================================================================
-- Generated: 2025-11-18
-- Purpose: Create 15 essential performance indexes for high-impact queries
--
-- INDEX STRATEGY:
-- - Foreign Keys: B-Tree indexes on project_id, entity_id, and relationship keys
-- - Spatial Columns: GiST indexes on PostGIS geometry columns
-- - Using CONCURRENTLY for production safety (no table locking)
--
-- DEPLOYMENT NOTES:
-- - Run during low-traffic periods if possible
-- - CONCURRENTLY requires autocommit mode (cannot run in transaction block)
-- - Each index creation can be monitored with:
--   SELECT * FROM pg_stat_progress_create_index;
-- ============================================================================

-- ============================================================================
-- SECTION 1: FOREIGN KEY INDEXES (B-Tree)
-- ============================================================================

-- Index 1: entity_relationships.subject_entity_id
-- High Impact: GraphRAG traversal, relationship queries, entity graph navigation
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_entity_relationships_subject_entity_id
ON entity_relationships (subject_entity_id);

-- Index 2: entity_relationships.object_entity_id
-- High Impact: Reverse relationship lookups, bi-directional graph traversal
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_entity_relationships_object_entity_id
ON entity_relationships (object_entity_id);

-- Index 3: entity_embeddings.entity_id
-- High Impact: Semantic search, vector similarity queries, AI features
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_entity_embeddings_entity_id
ON entity_embeddings (entity_id);

-- Index 4: entity_aliases.entity_id
-- High Impact: Entity resolution, duplicate detection, alias lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_entity_aliases_entity_id
ON entity_aliases (entity_id);

-- Index 5: easements.project_id
-- High Impact: Project-scoped easement queries, project filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_easements_project_id
ON easements (project_id);

-- Index 6: easements.entity_id
-- High Impact: Entity-based easement lookups, cross-referencing
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_easements_entity_id
ON easements (entity_id);

-- Index 7: grading_limits.project_id
-- High Impact: Project-scoped grading limit queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_grading_limits_project_id
ON grading_limits (project_id);

-- Index 8: drawing_hatches.project_id
-- High Impact: Project-based hatch filtering, drawing queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_drawing_hatches_project_id
ON drawing_hatches (project_id);

-- Index 9: horizontal_alignments.project_id
-- High Impact: Project alignment queries, roadway design lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_horizontal_alignments_project_id
ON horizontal_alignments (project_id);

-- Index 10: survey_points.project_id
-- High Impact: Project survey data queries, point cloud filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_survey_points_project_id
ON survey_points (project_id);

-- ============================================================================
-- SECTION 2: SPATIAL INDEXES (GiST for PostGIS)
-- ============================================================================

-- Index 11: easements.boundary_geometry
-- High Impact: Spatial queries, boundary intersections, proximity analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_easements_boundary_geometry
ON easements USING GIST (boundary_geometry);

-- Index 12: grading_limits.boundary_geometry
-- High Impact: Grading area calculations, spatial overlaps, site planning
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_grading_limits_boundary_geometry
ON grading_limits USING GIST (boundary_geometry);

-- Index 13: drawing_hatches.boundary_geometry
-- High Impact: Hatch pattern spatial queries, CAD rendering optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_drawing_hatches_boundary_geometry
ON drawing_hatches USING GIST (boundary_geometry);

-- Index 14: horizontal_alignments.alignment_geometry
-- High Impact: Alignment spatial queries, route analysis, geometric operations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_horizontal_alignments_alignment_geometry
ON horizontal_alignments USING GIST (alignment_geometry);

-- Index 15: survey_points.geometry
-- High Impact: Survey point spatial queries, proximity searches, point cloud operations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_survey_points_geometry
ON survey_points USING GIST (geometry);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- After creation, verify indexes with:
--
-- -- List all newly created indexes:
-- SELECT
--     schemaname,
--     tablename,
--     indexname,
--     pg_size_pretty(pg_relation_size(indexrelid)) as index_size
-- FROM pg_indexes
-- JOIN pg_class ON pg_class.relname = indexname
-- WHERE indexname LIKE 'idx_%'
-- ORDER BY tablename, indexname;
--
-- -- Check index usage statistics:
-- SELECT
--     schemaname,
--     tablename,
--     indexname,
--     idx_scan as number_of_scans,
--     idx_tup_read as tuples_read,
--     idx_tup_fetch as tuples_fetched
-- FROM pg_stat_user_indexes
-- WHERE indexname LIKE 'idx_%'
-- ORDER BY idx_scan DESC;
-- ============================================================================
