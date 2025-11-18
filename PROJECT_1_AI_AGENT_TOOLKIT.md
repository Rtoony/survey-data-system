# Project 1: AI Agent Toolkit & GraphRAG Query System

## Executive Summary
Activate ACAD-GIS's AI-first architecture by implementing the embedding generation pipeline, GraphRAG query engine, and semantic search capabilities. Transform the database from a passive storage system into an intelligent knowledge graph that understands CAD/GIS relationships and enables natural language queries.

## Current State Assessment

### Existing Infrastructure (Ready to Use)
- ✅ `embeddings` table with versioned vector storage (1536 dimensions)
- ✅ `graph_edges` table for explicit relationships
- ✅ `quality_score` columns on all entities
- ✅ `search_vector` tsvector columns for full-text search
- ✅ pgvector extension with IVFFlat indexes
- ✅ PostGIS spatial indexes
- ✅ JSONB attributes for flexible metadata
- ✅ Materialized views for AI queries

### Current Gaps
- ❌ No automated embedding generation
- ❌ Empty embeddings table (0 records)
- ❌ Empty graph_edges table (0 relationships)
- ❌ No AI query interface
- ❌ Quality scores not automatically calculated
- ❌ No semantic search functionality

## Goals & Objectives

### Primary Goals
1. **Populate Embeddings Table**: Generate vector embeddings for all CAD entities using OpenAI
2. **Build Relationship Graph**: Auto-discover and store spatial/engineering/semantic relationships
3. **Natural Language Queries**: Enable GraphRAG queries like "Find all pipes connected to Basin MH-101"
4. **Semantic Search**: Cross-project similarity search ("Show retention pond designs similar to Project X")
5. **Quality Automation**: ML-driven quality scoring based on completeness and relationships

### Success Metrics
- 100% of utility lines, structures, and survey points have embeddings
- Graph edges capture 95%+ of spatial connections
- Natural language queries return accurate results in <2 seconds
- Semantic search finds relevant projects with 85%+ precision
- Quality scores automatically updated on entity changes

## Technical Architecture

### Core Components

#### 1. Embedding Generation Pipeline
**Technology**: OpenAI API (text-embedding-3-small or text-embedding-3-large)
**Input**: Entity descriptions (geometry + attributes + context)
**Output**: 1536-dimension vectors stored in `embeddings` table

```python
# Example entity description for embedding
"Storm drain manhole MH-101 at coordinates (6010234.5, 2102456.8), 
 structure type MH, material CONCRETE, rim elevation 105.3 ft, 
 invert elevation 98.5 ft, connects to 3 pipes, 
 located in Project Maple Street Drainage, serves Basin A"
```

#### 2. Graph Edge Builder
**Auto-Discovery Rules**:
- **Spatial**: Lines connected to structures (tolerance: 0.1 ft)
- **Engineering**: Upstream/downstream pipe flow relationships
- **Hierarchical**: Projects → Entities (direct relationship, drawings table removed)
- **Semantic**: Similar BMP types, related survey points
- **Reference**: Entities → Standards (materials, structure types)

#### 3. GraphRAG Query Engine
**Multi-Hop Query Examples**:
- "What's the flow path from Basin MH-5 to the outlet?"
- "Which projects have similar stormwater treatment designs?"
- "Find all pipes with questionable slope between two structures"
- "Show me survey points within 50 feet of utility conflicts"

#### 4. Quality Scoring Engine
**Scoring Factors**:
- Geometry completeness (30%): Non-null coordinates, valid 3D elevation
- Attribute completeness (25%): Required fields populated
- Embedding quality (20%): Vector exists and is current
- Relationship density (15%): Connected to other entities
- Standard compliance (10%): Valid material/structure type references

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Tasks**:
1. Set up OpenAI integration using Replit connector
2. Create embedding generation service (`services/ai_embeddings.py`)
3. Build entity description builder for each table type
4. Implement batch embedding API with rate limiting
5. Create embedding versioning system (track model changes)

**Deliverables**:
- Working OpenAI integration with API key management
- Python service that generates embeddings for single entities
- Batch processing capability (100 entities at a time)
- Database migration to track embedding versions

### Phase 2: Relationship Discovery (Week 3-4)
**Tasks**:
1. Implement spatial relationship detector using PostGIS
2. Build engineering relationship rules (flow direction, elevation)
3. Create semantic similarity detector using embeddings
4. Populate `graph_edges` table with discovered relationships
5. Add edge type taxonomy (spatial, flow, hierarchical, semantic)

**Deliverables**:
- Automated relationship discovery for all projects
- Graph edges populated with 10,000+ relationships
- Relationship confidence scores (0.0-1.0)
- Edge type classification system

### Phase 3: GraphRAG Query Engine (Week 5-6)
**Tasks**:
1. Build natural language query parser
2. Implement multi-hop graph traversal algorithms
3. Create vector similarity search with pgvector
4. Develop hybrid search (vector + full-text + spatial)
5. Build query result ranking and relevance scoring

**Deliverables**:
- REST API endpoints for natural language queries
- Query response with entities, relationships, and explanations
- Support for 20+ common CAD/GIS query patterns
- Query performance <2 seconds for 95% of queries

### Phase 4: Quality Scoring Automation (Week 7-8)
**Tasks**:
1. Implement quality score calculation algorithms
2. Create automated scoring triggers on INSERT/UPDATE
3. Build quality dashboard with score distributions
4. Develop anomaly detection (low-quality outliers)
5. Create quality improvement recommendations

**Deliverables**:
- Automated quality scores for all entities
- Real-time score updates on data changes
- Quality dashboard showing project/entity health
- AI-generated improvement suggestions

### Phase 5: Web Interface & Visualization (Week 9-10)
**Tasks**:
1. Create AI Query Playground web interface
2. Build knowledge graph visualization (Cytoscape.js)
3. Implement semantic search UI
4. Add query history and saved queries
5. Create quality score heatmaps

**Deliverables**:
- Web UI for natural language CAD queries
- Interactive graph visualization with filtering
- Semantic search interface with visual results
- Quality analytics dashboards

## Database Schema Extensions

### New Tables Needed
```sql
-- Track embedding generation jobs
CREATE TABLE embedding_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50),
    entity_count INTEGER,
    status VARCHAR(20), -- pending, running, completed, failed
    model_version VARCHAR(50),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Cache AI query results
CREATE TABLE ai_query_cache (
    query_hash VARCHAR(64) PRIMARY KEY,
    query_text TEXT,
    result_json JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    hit_count INTEGER DEFAULT 0
);

-- Store quality score history
CREATE TABLE quality_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID,
    entity_type VARCHAR(50),
    quality_score DECIMAL(5,2),
    score_factors JSONB,
    calculated_at TIMESTAMP DEFAULT NOW()
);
```

## API Endpoints

### Embedding Management
- `POST /api/ai/embeddings/generate` - Generate embeddings for entities
- `GET /api/ai/embeddings/status` - Check generation job status
- `DELETE /api/ai/embeddings/refresh` - Regenerate outdated embeddings

### GraphRAG Queries
- `POST /api/ai/query` - Natural language query
- `GET /api/ai/query/history` - User query history
- `POST /api/ai/query/save` - Save favorite query

### Semantic Search
- `POST /api/ai/search/similar` - Find similar entities
- `POST /api/ai/search/projects` - Cross-project similarity

### Quality Scoring
- `GET /api/ai/quality/entity/{id}` - Entity quality details
- `GET /api/ai/quality/project/{id}` - Project quality summary
- `POST /api/ai/quality/recalculate` - Force quality recalculation

## Python Modules Structure

```
services/
├── ai_embeddings.py          # OpenAI embedding generation
├── ai_graph_builder.py       # Relationship discovery
├── ai_query_engine.py        # GraphRAG query processing
├── ai_quality_scorer.py      # Quality score calculation
└── ai_semantic_search.py     # Vector similarity search

utils/
├── entity_describer.py       # Generate entity descriptions
├── graph_traversal.py        # Multi-hop graph algorithms
├── query_parser.py           # Natural language parsing
└── vector_operations.py      # Embedding math operations
```

## Dependencies & Requirements

### Python Packages (Add to requirements)
- `openai>=1.0.0` - OpenAI API client
- `tiktoken>=0.5.0` - Token counting for embeddings
- `numpy>=1.24.0` - Vector operations
- `scikit-learn>=1.3.0` - Similarity calculations
- `networkx>=3.0` - Graph algorithms

### Replit Integrations
- OpenAI connector for API key management

### Database Requirements
- Existing pgvector extension (already installed)
- Existing embeddings, graph_edges tables (already created)

## Cost Estimates

### OpenAI API Costs (text-embedding-3-small)
- Assuming 10,000 entities at 200 tokens each
- Cost: $0.02 per 1M tokens = $0.04 for full system
- Monthly updates: ~$0.50/month
- **Very affordable at scale**

### Performance Targets
- Embedding generation: 1,000 entities/minute
- Graph edge discovery: 10,000 edges/minute
- Query response time: <2 seconds
- Quality score calculation: <100ms per entity

## Risk Assessment

### Technical Risks
- **OpenAI API rate limits**: Mitigate with batch processing and rate limiting
- **Vector index performance**: Monitor query times, optimize IVFFlat parameters
- **Relationship explosion**: Implement confidence thresholds to filter weak edges
- **Query complexity**: Cache frequent queries, limit graph traversal depth

### Data Quality Risks
- **Poor entity descriptions**: Iteratively improve description templates
- **Missing attributes**: Highlight incomplete entities for manual review
- **Spatial tolerance issues**: Make connection tolerance configurable

## Success Criteria

### Must Have
- ✅ All entities have current embeddings
- ✅ Graph edges capture spatial connections
- ✅ Natural language queries work for common patterns
- ✅ Quality scores auto-update on changes

### Should Have
- ✅ Semantic search finds similar projects
- ✅ Query performance <2 seconds
- ✅ Quality dashboard with visualizations
- ✅ AI-generated recommendations

### Nice to Have
- ✅ Query suggestions based on project context
- ✅ Anomaly detection alerts
- ✅ Embedding model version comparison
- ✅ Export knowledge graph to external tools

## Future Enhancements (Post-Project)
- LLM-powered CAD design assistant
- Predictive modeling for utility failures
- Automated CAD drawing generation from specifications
- Integration with Claude for complex reasoning tasks
- Multi-modal embeddings (text + geometry + images)

## Timeline Summary
- **Phase 1**: Weeks 1-2 (Foundation)
- **Phase 2**: Weeks 3-4 (Relationships)
- **Phase 3**: Weeks 5-6 (Query Engine)
- **Phase 4**: Weeks 7-8 (Quality Scoring)
- **Phase 5**: Weeks 9-10 (Web Interface)

**Total Duration**: 10 weeks (aggressive timeline with focused effort)

## ROI & Business Value
- **Time Savings**: Instant answers to CAD queries (vs. manual file searching)
- **Quality Improvement**: Automated detection of design issues
- **Knowledge Leverage**: Learn from past projects automatically
- **Client Value**: Demonstrate AI-powered design intelligence
- **Competitive Edge**: No other CAD system has this capability
