# GraphRAG API Documentation

## Overview

The GraphRAG (Graph Retrieval-Augmented Generation) system transforms the CAD/GIS database into an intelligent knowledge graph with natural language query capabilities, semantic search, and advanced graph analytics.

**Version:** 1.0
**Date:** 2025-11-18
**Status:** ✅ Complete Implementation

---

## Table of Contents

1. [Architecture](#architecture)
2. [API Endpoints](#api-endpoints)
3. [Services](#services)
4. [Database Schema](#database-schema)
5. [Usage Examples](#usage-examples)
6. [Deployment](#deployment)

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    Flask Application                     │
├─────────────────────────────────────────────────────────┤
│  API Layer                                               │
│  - /api/graphrag/*      (Natural Language Queries)      │
│  - /api/ai/search/*     (Semantic Search)               │
│  - /api/ai/quality/*    (Quality Scoring)               │
├─────────────────────────────────────────────────────────┤
│  Service Layer                                           │
│  - GraphRAGService       (Query engine)                 │
│  - GraphAnalyticsService (NetworkX algorithms)          │
│  - SemanticSearchService (Vector similarity)            │
├─────────────────────────────────────────────────────────┤
│  Database Layer (PostgreSQL + pgvector + PostGIS)       │
│  - entity_embeddings     (1536-dim vectors)             │
│  - entity_relationships  (Graph edges)                  │
│  - ai_query_cache        (Performance optimization)     │
│  - quality_history       (Score tracking)               │
└─────────────────────────────────────────────────────────┘
```

### Key Technologies

- **Flask**: REST API framework
- **PostgreSQL**: Database with pgvector and PostGIS extensions
- **NetworkX**: Graph algorithms (PageRank, community detection, etc.)
- **OpenAI**: Embedding generation (text-embedding-3-small/large)
- **NumPy**: Vector operations
- **scikit-learn**: Clustering algorithms (optional)

---

## API Endpoints

### GraphRAG Natural Language Queries

Base URL: `/api/graphrag`

#### POST /query
Execute a natural language query against the knowledge graph.

**Request:**
```json
{
  "query": "Find all pipes connected to Basin MH-101",
  "use_cache": true,
  "max_results": 100
}
```

**Response:**
```json
{
  "entities": [
    {
      "entity_id": "uuid-1",
      "entity_type": "utility_structure",
      "canonical_name": "Basin MH-101",
      "description": "...",
      "quality_score": 0.95
    },
    {
      "entity_id": "uuid-2",
      "entity_type": "utility_line",
      "canonical_name": "Storm Pipe 12-INCH-001",
      "hop_distance": 1,
      "quality_score": 0.88
    }
  ],
  "relationships": [
    {
      "relationship_id": "uuid-rel-1",
      "subject_entity_id": "uuid-1",
      "object_entity_id": "uuid-2",
      "relationship_type": "connected_to",
      "confidence_score": 0.95
    }
  ],
  "explanation": "Found 5 entities connected to Basin MH-101",
  "metadata": {
    "query_type": "find_connections",
    "execution_time_ms": 45.2,
    "parsed_query": {...},
    "timestamp": "2025-11-18T12:00:00"
  }
}
```

**Supported Query Types:**
- `find_connections`: "Find all entities connected to X"
- `flow_path`: "Show flow path from A to B"
- `similar_entities`: "Find designs similar to X"
- `spatial_query`: "Find entities within 50 feet of X"
- `attribute_filter`: "Show pipes with material = CONCRETE"
- `quality_check`: "Find entities with quality issues"
- `hierarchical`: "Show all entities in Project X"

#### POST /query/parse
Parse a natural language query without executing it.

**Request:**
```json
{
  "query": "Show me pipes within 50 feet of MH-101"
}
```

**Response:**
```json
{
  "query_type": "spatial_query",
  "entity_references": ["MH-101"],
  "entity_types": ["pipe"],
  "parameters": {
    "distance": 50,
    "distance_unit": "feet"
  },
  "confidence": 0.85,
  "original_query": "Show me pipes within 50 feet of MH-101"
}
```

#### GET /query/suggestions
Get query suggestions based on partial input.

**Parameters:**
- `q`: Partial query text
- `limit`: Maximum suggestions (default: 5)

**Example:** `GET /api/graphrag/query/suggestions?q=Find all pipes&limit=5`

**Response:**
```json
{
  "suggestions": [
    "Find all pipes connected to Basin MH-101",
    "Find pipes within 50 feet of Basin A",
    "Find pipes with material = PVC"
  ]
}
```

---

### Graph Analytics

#### GET /analytics/pagerank
Compute PageRank scores for entities.

**Parameters:**
- `project_id`: Optional project scope (UUID)
- `entity_type`: Optional entity type filter
- `use_cache`: Use cached results (default: true)

**Response:**
```json
{
  "pagerank_scores": {
    "uuid-1": 0.023,
    "uuid-2": 0.018,
    "uuid-3": 0.015
  },
  "metadata": {
    "project_id": "project-uuid",
    "num_entities": 1500,
    "timestamp": "2025-11-18T12:00:00"
  }
}
```

#### GET /analytics/communities
Detect communities/clusters in the graph.

**Parameters:**
- `project_id`: Optional project scope
- `algorithm`: `louvain`, `label_propagation`, or `greedy_modularity` (default: louvain)
- `use_cache`: Use cached results (default: true)

**Response:**
```json
{
  "communities": [
    {
      "community_id": 0,
      "entity_ids": ["uuid-1", "uuid-2", "uuid-3"],
      "size": 3
    },
    {
      "community_id": 1,
      "entity_ids": ["uuid-4", "uuid-5"],
      "size": 2
    }
  ],
  "modularity": 0.42,
  "num_communities": 2,
  "algorithm": "louvain"
}
```

#### GET /analytics/centrality
Compute centrality measures.

**Parameters:**
- `project_id`: Optional project scope
- `measures`: Comma-separated list (degree, betweenness, closeness, eigenvector)
- `use_cache`: Use cached results

**Response:**
```json
{
  "degree": {
    "uuid-1": 5,
    "uuid-2": 3
  },
  "betweenness": {
    "uuid-1": 0.12,
    "uuid-2": 0.08
  },
  "closeness": {
    "uuid-1": 0.34,
    "uuid-2": 0.28
  }
}
```

#### GET /analytics/influential-nodes
Find most influential nodes in the graph.

**Parameters:**
- `project_id`: Optional project scope
- `top_k`: Number of top nodes (default: 10)
- `metric`: `pagerank`, `degree`, or `betweenness` (default: pagerank)

**Response:**
```json
[
  {
    "entity_id": "uuid-1",
    "canonical_name": "Main Basin MH-001",
    "entity_type": "utility_structure",
    "pagerank_score": 0.023,
    "description": "Primary collection basin"
  }
]
```

#### GET /analytics/structure
Analyze overall graph structure.

**Response:**
```json
{
  "num_nodes": 1500,
  "num_edges": 3200,
  "density": 0.0014,
  "avg_degree": 4.27,
  "max_degree": 25,
  "min_degree": 0,
  "is_directed": true,
  "num_weakly_connected_components": 3,
  "is_weakly_connected": false
}
```

#### POST /analytics/shortest-path
Find shortest path between two entities.

**Request:**
```json
{
  "source_entity_id": "uuid-1",
  "target_entity_id": "uuid-2",
  "weight_attribute": "distance"
}
```

**Response:**
```json
{
  "path": ["uuid-1", "uuid-3", "uuid-2"],
  "path_entities": [
    {"entity_id": "uuid-1", "canonical_name": "Basin A"},
    {"entity_id": "uuid-3", "canonical_name": "Pipe P-001"},
    {"entity_id": "uuid-2", "canonical_name": "Basin B"}
  ],
  "length": 2,
  "exists": true
}
```

#### GET /analytics/bridges
Identify bridge edges (critical connections whose removal disconnects the graph).

**Response:**
```json
{
  "bridges": [
    ["uuid-1", "uuid-2"],
    ["uuid-5", "uuid-6"]
  ],
  "count": 2
}
```

#### GET /analytics/articulation-points
Identify articulation points (critical nodes whose removal disconnects the graph).

**Response:**
```json
{
  "articulation_points": ["uuid-1", "uuid-5", "uuid-10"],
  "count": 3
}
```

---

### Semantic Search

Base URL: `/api/ai/search`

#### GET /similar/entity/{entity_id}
Find entities similar to a given entity using vector embeddings.

**Parameters:**
- `entity_type`: Optional entity type filter
- `similarity_threshold`: Minimum similarity 0-1 (default: 0.7)
- `max_results`: Maximum results (default: 50)
- `include_cross_type`: Include different entity types (default: true)

**Response:**
```json
[
  {
    "entity_id": "uuid-2",
    "entity_type": "utility_structure",
    "canonical_name": "Basin MH-102",
    "similarity_score": 0.95,
    "description": "...",
    "quality_score": 0.88
  }
]
```

#### POST /similar/text
Find entities similar to a text description.

**Request:**
```json
{
  "search_text": "storm drain manhole with concrete material",
  "entity_type": "utility_structure",
  "similarity_threshold": 0.7,
  "max_results": 50
}
```

**Response:** Same as /similar/entity

#### GET /similar/projects/{project_id}
Find projects similar to a given project.

**Parameters:**
- `similarity_threshold`: Minimum similarity (default: 0.7)
- `max_results`: Maximum results (default: 10)

**Response:**
```json
[
  {
    "project_id": "uuid-proj-2",
    "project_name": "Maple Street Drainage",
    "similarity_score": 0.85,
    "entity_count": 150,
    "description": "..."
  }
]
```

#### POST /cluster
Cluster entities based on embeddings.

**Request:**
```json
{
  "entity_ids": ["uuid-1", "uuid-2", "uuid-3", "uuid-4"],
  "num_clusters": 2,
  "method": "kmeans"
}
```

**Response:**
```json
{
  "clusters": [
    {
      "cluster_id": 0,
      "entity_ids": ["uuid-1", "uuid-2"],
      "size": 2
    },
    {
      "cluster_id": 1,
      "entity_ids": ["uuid-3", "uuid-4"],
      "size": 2
    }
  ],
  "method": "kmeans",
  "num_clusters": 2
}
```

#### GET /duplicates
Find potential duplicate entities based on high similarity.

**Parameters:**
- `entity_type`: Optional entity type filter
- `similarity_threshold`: High threshold (default: 0.95)
- `max_results`: Maximum duplicate pairs (default: 100)

**Response:**
```json
[
  {
    "entity1_id": "uuid-1",
    "entity1_name": "Basin MH-101",
    "entity2_id": "uuid-2",
    "entity2_name": "Manhole MH-101",
    "similarity_score": 0.98
  }
]
```

#### GET /autocomplete
Semantic autocomplete suggestions.

**Parameters:**
- `q`: Partial query text
- `entity_type`: Optional entity type filter
- `max_results`: Maximum suggestions (default: 10)

**Response:**
```json
[
  {
    "entity_id": "uuid-1",
    "canonical_name": "Basin MH-101",
    "entity_type": "utility_structure",
    "quality_score": 0.95
  }
]
```

---

### Quality Scoring

Base URL: `/api/ai/quality`

#### GET /entity/{entity_id}
Get quality details for a specific entity.

**Response:**
```json
{
  "entity_id": "uuid-1",
  "entity_type": "utility_structure",
  "canonical_name": "Basin MH-101",
  "quality_score": 0.85,
  "quality_factors": {
    "has_embedding": true,
    "has_relationships": true,
    "relationship_count": 5,
    "completeness": 0.9
  },
  "last_updated": "2025-11-18T12:00:00"
}
```

#### GET /entity/{entity_id}/history
Get quality score history for an entity.

**Parameters:**
- `days`: Number of days to look back (default: 30)
- `limit`: Maximum history entries (default: 100)

**Response:**
```json
[
  {
    "quality_score": 0.85,
    "previous_score": 0.80,
    "score_delta": 0.05,
    "trigger_event": "embedding_added",
    "calculated_at": "2025-11-18T12:00:00"
  }
]
```

#### GET /project/{project_id}/summary
Get quality summary for a project.

**Response:**
```json
{
  "project_id": "uuid-proj-1",
  "avg_quality_score": 0.82,
  "entity_count": 1500,
  "quality_distribution": {
    "excellent": 450,
    "good": 750,
    "fair": 250,
    "poor": 50
  },
  "entities_with_embeddings": 1200,
  "entities_with_relationships": 1100,
  "timestamp": "2025-11-18T12:00:00"
}
```

#### GET /trends
Get quality score trends over time.

**Parameters:**
- `entity_type`: Optional entity type filter
- `days`: Number of days (default: 30)

**Response:**
```json
[
  {
    "entity_type": "utility_structure",
    "date": "2025-11-18",
    "avg_score": 0.85,
    "score_changes": 15,
    "improvements": 12,
    "degradations": 3
  }
]
```

#### GET /low-quality-entities
Get entities with low quality scores.

**Parameters:**
- `threshold`: Quality score threshold (default: 0.5)
- `entity_type`: Optional entity type filter
- `limit`: Maximum results (default: 100)

**Response:**
```json
[
  {
    "entity_id": "uuid-1",
    "entity_type": "utility_line",
    "canonical_name": "Pipe P-001",
    "quality_score": 0.35,
    "issues": ["no_embedding", "no_relationships", "no_description"]
  }
]
```

---

## Services

### GraphRAGService

**Location:** `services/graphrag_service.py`

**Key Methods:**
- `execute_query(query_text, use_cache, max_results)`: Execute natural language queries
- `parse_query(query_text)`: Parse query intent and extract parameters
- `get_query_suggestions(partial_query, limit)`: Get autocomplete suggestions
- `invalidate_cache(entity_ids, reason)`: Invalidate query cache

**Supported Query Patterns:**
- Find connections: `r'(find|show).*(connect|link|relat)'`
- Flow paths: `r'(flow|path|route).*(from|to|between)'`
- Similarity: `r'(similar|like|comparable)'`
- Spatial: `r'(within|near).*(feet|meters)'`
- Attributes: `r'(where|with).*(material|size|type)'`
- Quality: `r'(quality|score|issue)'`
- Hierarchical: `r'(in|under).*(project|basin)'`

### GraphAnalyticsService

**Location:** `services/graph_analytics_service.py`

**Key Methods:**
- `compute_pagerank(project_id, entity_type, use_cache)`: PageRank centrality
- `detect_communities(project_id, algorithm, use_cache)`: Community detection
- `compute_centrality_measures(project_id, measures, use_cache)`: Various centrality metrics
- `find_shortest_path(source, target, weight)`: Shortest path between nodes
- `find_connected_components(project_id)`: Connected components
- `identify_bridges(project_id)`: Bridge edges
- `identify_articulation_points(project_id)`: Articulation points
- `analyze_graph_structure(project_id)`: Overall graph metrics

### SemanticSearchService

**Location:** `services/semantic_search_service.py`

**Key Methods:**
- `find_similar_entities(entity_id, entity_type, threshold, max_results)`: Vector similarity search
- `find_similar_by_text(search_text, entity_type, threshold)`: Text-based similarity
- `find_similar_projects(project_id, threshold)`: Cross-project similarity
- `cluster_entities(entity_ids, num_clusters, method)`: Semantic clustering
- `find_semantic_duplicates(entity_type, threshold)`: Duplicate detection
- `semantic_autocomplete(partial_query, entity_type)`: Smart autocomplete
- `compute_entity_similarity_matrix(entity_ids)`: Pairwise similarity matrix

---

## Database Schema

### Tables Created in Migration 041

#### `embedding_jobs`
Tracks batch embedding generation jobs.

```sql
CREATE TABLE embedding_jobs (
    job_id UUID PRIMARY KEY,
    entity_type VARCHAR(50),
    entity_count INTEGER,
    status VARCHAR(20),
    model_id UUID,
    tokens_used INTEGER,
    cost_usd DECIMAL(10,4),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

#### `ai_query_cache`
Caches natural language query results.

```sql
CREATE TABLE ai_query_cache (
    cache_id UUID PRIMARY KEY,
    query_hash VARCHAR(64) UNIQUE,
    query_text TEXT,
    query_type VARCHAR(50),
    result_json JSONB,
    hit_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP
);
```

#### `quality_history`
Tracks quality score changes over time.

```sql
CREATE TABLE quality_history (
    history_id UUID PRIMARY KEY,
    entity_id UUID,
    entity_type VARCHAR(50),
    quality_score DECIMAL(5,2),
    previous_score DECIMAL(5,2),
    score_delta DECIMAL(5,2),
    score_factors JSONB,
    trigger_event VARCHAR(50),
    calculated_at TIMESTAMP
);
```

#### `ai_query_history`
Logs all natural language queries for analytics.

```sql
CREATE TABLE ai_query_history (
    query_id UUID PRIMARY KEY,
    query_text TEXT,
    query_type VARCHAR(50),
    was_successful BOOLEAN,
    result_count INTEGER,
    execution_time_ms INTEGER,
    used_cache BOOLEAN
);
```

#### `graph_analytics_cache`
Caches computationally expensive graph analytics.

```sql
CREATE TABLE graph_analytics_cache (
    cache_id UUID PRIMARY KEY,
    analysis_type VARCHAR(50),
    scope_type VARCHAR(50),
    scope_id UUID,
    result_data JSONB,
    node_count INTEGER,
    edge_count INTEGER,
    expires_at TIMESTAMP
);
```

#### `semantic_similarity_cache`
Caches pairwise similarity scores.

```sql
CREATE TABLE semantic_similarity_cache (
    cache_id UUID PRIMARY KEY,
    source_entity_id UUID,
    target_entity_id UUID,
    similarity_score DECIMAL(5,4),
    similarity_method VARCHAR(50)
);
```

---

## Usage Examples

### Example 1: Find Connected Entities

```bash
curl -X POST http://localhost:5000/api/graphrag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find all pipes connected to Basin MH-101",
    "max_results": 50
  }'
```

### Example 2: Compute PageRank

```bash
curl -X GET "http://localhost:5000/api/graphrag/analytics/pagerank?project_id=uuid-proj-1&use_cache=true"
```

### Example 3: Find Similar Entities

```bash
curl -X GET "http://localhost:5000/api/ai/search/similar/entity/uuid-1?similarity_threshold=0.8&max_results=20"
```

### Example 4: Detect Communities

```bash
curl -X GET "http://localhost:5000/api/graphrag/analytics/communities?algorithm=louvain&use_cache=false"
```

### Example 5: Get Quality Summary

```bash
curl -X GET "http://localhost:5000/api/ai/quality/project/uuid-proj-1/summary"
```

---

## Deployment

### Prerequisites

1. PostgreSQL 14+ with extensions:
   - `pgvector` for vector similarity
   - `PostGIS` for spatial operations

2. Python 3.11+ with packages:
   - `networkx>=3.0`
   - `scikit-learn>=1.3.0`
   - `numpy>=1.24.0`
   - `openai>=2.6.1`

### Installation Steps

1. **Run Database Migration:**
   ```bash
   python3 scripts/run_migration_041.py
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   Or with poetry:
   ```bash
   poetry install
   ```

3. **Generate Embeddings** (one-time):
   ```bash
   python3 scripts/phase1_01_generate_embeddings.py
   ```

4. **Build Graph Relationships** (one-time):
   ```bash
   python3 scripts/phase1_02_build_relationships.py
   ```

5. **Start Flask App:**
   ```bash
   python3 app.py
   ```

### Performance Optimization

- **Caching:** Query and analytics results are cached by default (TTL: 1 hour)
- **Indexes:** IVFFlat indexes on embedding columns for fast vector search
- **Connection Pooling:** Use pgbouncer for production deployments
- **Batch Processing:** Generate embeddings in batches of 50-100 entities

### Monitoring

- Check embedding job status: `SELECT * FROM embedding_jobs ORDER BY created_at DESC;`
- Monitor cache hit rates: `SELECT * FROM query_cache_stats;`
- Track quality trends: `SELECT * FROM quality_score_trends LIMIT 30;`

---

## Cost Estimates

### OpenAI API Costs (text-embedding-3-small)

Assuming 10,000 entities at 200 tokens each:
- **Initial embedding generation:** ~$0.04
- **Monthly updates:** ~$0.50/month (for changes/additions)
- **Total annual cost:** ~$6-10

**Very affordable for production use!**

---

## Support & Issues

For questions or issues, please:
1. Check the API documentation above
2. Review service layer code in `services/`
3. Examine database schema in `database/migrations/041_create_graphrag_tables.sql`
4. File issues in the project repository

---

## Future Enhancements

- [ ] LLM-powered query understanding (Claude/GPT-4)
- [ ] Multi-modal embeddings (text + geometry + images)
- [ ] Real-time graph updates via WebSocket
- [ ] Graph export to Neo4j/Cypher format
- [ ] Advanced visualization with D3.js/Cytoscape.js
- [ ] Predictive analytics for utility failures
- [ ] Automated CAD drawing generation from queries

---

**Document Version:** 1.0
**Last Updated:** 2025-11-18
**Author:** AI Agent Toolkit
