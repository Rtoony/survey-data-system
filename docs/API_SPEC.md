# Survey Data System - API Specification

**Version**: 2.0
**Last Updated**: 2025-11-18
**Base URL**: `http://localhost:5000` (development)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Authentication](#2-authentication)
3. [Response Format](#3-response-format)
4. [Error Handling](#4-error-handling)
5. [API Endpoints](#5-api-endpoints)
   - [Authentication Routes](#authentication-routes)
   - [Project Routes](#project-routes)
   - [Entity Routes](#entity-routes)
   - [Classification Routes](#classification-routes)
   - [Relationship Routes](#relationship-routes)
   - [GraphRAG Routes](#graphrag-routes)
   - [AI Search Routes](#ai-search-routes)
   - [Quality Routes](#quality-routes)
   - [Specification Routes](#specification-routes)
   - [Standards Routes](#standards-routes)

---

## 1. Overview

The Survey Data System API provides RESTful endpoints for managing CAD/GIS data, entity classification, relationship graphs, specifications, and AI-powered search.

**Architecture**: Hybrid (Legacy + Modern Blueprints)
- **Modern Routes**: `/api/*` (blueprints)
- **Legacy Routes**: Mixed in `app.py`

**Authentication**: Session-based OAuth (Replit Auth)

---

## 2. Authentication

### Session-Based Authentication

All API endpoints (except `/auth/*`) require authentication.

**Authentication Flow**:
1. User navigates to `/auth/login`
2. OAuth redirect to Replit Auth
3. Callback to `/auth/callback` with code
4. Session cookie set
5. Subsequent requests include session cookie

**Session Cookie**:
- Name: `session`
- Duration: 8 hours (configurable)
- SameSite: `Lax`
- HttpOnly: `true`
- Secure: `true` (production)

**Checking Auth Status**:
```http
GET /auth/check
```

**Response**:
```json
{
  "authenticated": true,
  "user": {
    "user_id": "uuid",
    "username": "john_doe",
    "email": "john@example.com",
    "role": "ENGINEER"
  }
}
```

---

## 3. Response Format

### Success Response

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Paginated Response

```json
{
  "success": true,
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 150,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## 4. Error Handling

### Error Response Format

```json
{
  "error": "Error message",
  "details": "Detailed error information",
  "code": "ERROR_CODE"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (not authenticated) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 409 | Conflict (duplicate resource) |
| 500 | Internal Server Error |

---

## 5. API Endpoints

## Authentication Routes

**Blueprint**: `auth_bp`
**Prefix**: `/auth`

### Login

Initiate OAuth login flow.

```http
GET /auth/login
```

**Parameters**: None

**Response**: Redirect to OAuth provider

---

### OAuth Callback

Handle OAuth callback after authentication.

```http
GET /auth/callback?code={code}&state={state}
```

**Parameters**:
- `code` (query, required): OAuth authorization code
- `state` (query, required): CSRF state token

**Response**: Redirect to dashboard with session cookie set

---

### Logout

Invalidate user session.

```http
GET /auth/logout
```

**Response**: Redirect to login page

---

### User Profile

Get current user profile with statistics.

```http
GET /auth/profile
```

**Authentication**: Required

**Response**:
```json
{
  "user_id": "uuid",
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "ENGINEER",
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z",
  "last_login": "2024-11-18T08:30:00Z",
  "statistics": {
    "projects_owned": 5,
    "entities_created": 1250,
    "classifications_reviewed": 342,
    "last_activity": "2024-11-18T12:45:00Z"
  }
}
```

---

### List Users (Admin)

Get all users in the system.

```http
GET /auth/users
```

**Authentication**: Required (Admin only)

**Query Parameters**:
- `role` (optional): Filter by role (`ADMIN`, `ENGINEER`, `VIEWER`)
- `is_active` (optional): Filter by active status (boolean)

**Response**:
```json
{
  "users": [
    {
      "user_id": "uuid",
      "username": "john_doe",
      "email": "john@example.com",
      "full_name": "John Doe",
      "role": "ENGINEER",
      "is_active": true,
      "created_at": "2024-01-15T10:00:00Z",
      "last_login": "2024-11-18T08:30:00Z"
    }
  ]
}
```

---

### Update User Role (Admin)

Change a user's role.

```http
POST /auth/users/{user_id}/role
```

**Authentication**: Required (Admin only)

**Request Body**:
```json
{
  "role": "ENGINEER"
}
```

**Response**:
```json
{
  "success": true,
  "message": "User role updated successfully"
}
```

---

## Project Routes

### List Projects

Get all projects accessible to the user.

```http
GET /api/projects
```

**Authentication**: Required

**Response**:
```json
{
  "projects": [
    {
      "project_id": "uuid",
      "project_name": "Downtown Water Main Replacement",
      "description": "Replace aging water infrastructure",
      "coordinate_system": "NAD83 California State Plane Zone 2",
      "epsg_code": "2226",
      "project_status": "active",
      "entity_count": 1500,
      "created_at": "2024-06-01T10:00:00Z",
      "updated_at": "2024-11-18T12:00:00Z",
      "owner": {
        "user_id": "uuid",
        "username": "john_doe"
      }
    }
  ]
}
```

---

### Create Project

Create a new project.

```http
POST /api/projects
```

**Authentication**: Required

**Request Body**:
```json
{
  "project_name": "Downtown Water Main Replacement",
  "description": "Replace aging water infrastructure",
  "coordinate_system": "NAD83 California State Plane Zone 2",
  "epsg_code": "2226"
}
```

**Response**:
```json
{
  "success": true,
  "project_id": "uuid",
  "message": "Project created successfully"
}
```

---

### Get Project Details

Get detailed project information.

```http
GET /api/projects/{project_id}
```

**Authentication**: Required

**Response**:
```json
{
  "project_id": "uuid",
  "project_name": "Downtown Water Main Replacement",
  "description": "Replace aging water infrastructure",
  "coordinate_system": "NAD83 California State Plane Zone 2",
  "epsg_code": "2226",
  "project_status": "active",
  "created_at": "2024-06-01T10:00:00Z",
  "updated_at": "2024-11-18T12:00:00Z",
  "statistics": {
    "total_entities": 1500,
    "auto_classified": 1200,
    "needs_review": 300,
    "entity_types": {
      "utility_line": 450,
      "utility_structure": 250,
      "survey_point": 800
    },
    "relationships": 1200,
    "spec_links": 350
  }
}
```

---

### Update Project

Update project details.

```http
PUT /api/projects/{project_id}
```

**Authentication**: Required (Write access)

**Request Body**:
```json
{
  "project_name": "Downtown Water Main Replacement - Phase 2",
  "description": "Updated description",
  "project_status": "active"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Project updated successfully"
}
```

---

### Delete Project

Delete a project and all associated entities.

```http
DELETE /api/projects/{project_id}
```

**Authentication**: Required (Admin or Owner)

**Response**:
```json
{
  "success": true,
  "message": "Project deleted successfully",
  "deleted_entities": 1500
}
```

---

### Get Project Statistics

Get comprehensive project statistics.

```http
GET /api/projects/{project_id}/statistics
```

**Authentication**: Required

**Response**:
```json
{
  "total_entities": 1500,
  "classification_summary": {
    "auto_classified": 1200,
    "user_classified": 250,
    "needs_review": 50
  },
  "entity_types": {
    "utility_line": 450,
    "utility_structure": 250,
    "survey_point": 800
  },
  "relationships": {
    "total_edges": 1200,
    "edge_types": {
      "CONNECTS_TO": 800,
      "REFERENCES": 300,
      "CONTAINS": 100
    }
  },
  "quality_summary": {
    "average_quality_score": 0.87,
    "entities_above_threshold": 1350,
    "entities_below_threshold": 150
  },
  "spatial_extent": {
    "min_x": 6008000.0,
    "min_y": 2108000.0,
    "max_x": 6012000.0,
    "max_y": 2112000.0,
    "srid": 2226
  }
}
```

---

### Get Project Map Summary

Get map data for project visualization.

```http
GET /api/projects/{project_id}/map-summary
```

**Authentication**: Required

**Query Parameters**:
- `entity_types` (optional): Comma-separated entity types to include
- `bbox` (optional): Bounding box filter (format: `minX,minY,maxX,maxY`)

**Response**:
```json
{
  "entities": [
    {
      "entity_id": "uuid",
      "entity_type": "utility_structure",
      "canonical_name": "MH-101",
      "geometry": {
        "type": "Point",
        "coordinates": [6010000.0, 2110000.0, 100.5]
      },
      "properties": {
        "structure_type": "Manhole",
        "utility_system": "Storm",
        "rim_elevation": 100.5
      }
    }
  ],
  "layers": [
    {
      "layer_name": "SS-MH",
      "entity_count": 45,
      "color": "#FF0000",
      "linetype": "Continuous"
    }
  ]
}
```

---

## Entity Routes

### Browse Project Entities

Get all entities in a project with filtering.

```http
GET /api/projects/{project_id}/entities
```

**Authentication**: Required

**Query Parameters**:
- `entity_type` (optional): Filter by entity type
- `classification_state` (optional): Filter by classification state
- `layer_name` (optional): Filter by layer name
- `page` (optional, default: 1): Page number
- `per_page` (optional, default: 50): Results per page

**Response**:
```json
{
  "entities": [
    {
      "entity_id": "uuid",
      "entity_type": "utility_structure",
      "canonical_name": "MH-101",
      "description": "Storm manhole at Main St & 1st Ave",
      "classification_state": "auto_classified",
      "classification_confidence": 0.92,
      "quality_score": 0.85,
      "created_at": "2024-11-01T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 1500,
    "total_pages": 30
  }
}
```

---

### Get Entity Details

Get detailed information for a specific entity.

```http
GET /api/entities/{entity_id}
```

**Authentication**: Required

**Response**:
```json
{
  "entity_id": "uuid",
  "project_id": "uuid",
  "entity_type": "utility_structure",
  "target_table": "utility_structures",
  "target_id": "uuid",
  "canonical_name": "MH-101",
  "description": "Storm manhole at Main St & 1st Ave",
  "classification_state": "auto_classified",
  "classification_confidence": 0.92,
  "quality_score": 0.85,
  "attributes": {
    "structure_type": "Manhole",
    "utility_system": "Storm",
    "rim_elevation": 100.5,
    "invert_elevation": 95.2,
    "manhole_depth_ft": 5.3,
    "size_mm": 1200,
    "material": "Precast Concrete",
    "condition": "Good",
    "owner": "City of Sacramento"
  },
  "geometry": {
    "type": "Point",
    "coordinates": [6010000.0, 2110000.0, 100.5]
  },
  "relationships": {
    "connected_pipes": 4,
    "related_entities": 8
  },
  "spec_links": {
    "total": 2,
    "compliant": 2,
    "violations": 0
  },
  "created_at": "2024-11-01T10:00:00Z",
  "updated_at": "2024-11-15T14:30:00Z"
}
```

---

## Classification Routes

### Get Classification Review Queue

Get entities that need classification review.

```http
GET /api/classification/review-queue
```

**Authentication**: Required

**Query Parameters**:
- `project_id` (optional): Filter by project
- `confidence_threshold` (optional, default: 0.7): Max confidence for review
- `limit` (optional, default: 50): Number of entities to return

**Response**:
```json
{
  "entities": [
    {
      "entity_id": "uuid",
      "project_id": "uuid",
      "entity_type": "generic_object",
      "layer_name": "UNKNOWN-LAYER",
      "classification_confidence": 0.45,
      "geometry_preview_url": "/api/classification/geometry-preview/uuid",
      "ai_suggestions": [
        {
          "entity_type": "utility_structure",
          "confidence": 0.75,
          "reasoning": "Point geometry on utility layer"
        },
        {
          "entity_type": "survey_point",
          "confidence": 0.65,
          "reasoning": "Has elevation attribute"
        }
      ],
      "spatial_context": {
        "nearby_entities": [
          {
            "entity_id": "uuid",
            "entity_type": "utility_line",
            "canonical_name": "SS-PIPE-001",
            "distance_ft": 15.2
          }
        ]
      }
    }
  ],
  "total_needs_review": 300
}
```

---

### Reclassify Entity

Change an entity's classification.

```http
POST /api/classification/reclassify
```

**Authentication**: Required

**Request Body**:
```json
{
  "entity_id": "uuid",
  "new_type": "utility_structure",
  "user_notes": "This is a storm manhole",
  "attributes": {
    "structure_type": "Manhole",
    "utility_system": "Storm"
  }
}
```

**Response**:
```json
{
  "success": true,
  "entity_id": "uuid",
  "new_entity_type": "utility_structure",
  "target_table": "utility_structures",
  "target_id": "uuid",
  "message": "Entity reclassified successfully"
}
```

---

### Bulk Reclassify

Reclassify multiple entities at once.

```http
POST /api/classification/bulk-reclassify
```

**Authentication**: Required

**Request Body**:
```json
{
  "entities": [
    {
      "entity_id": "uuid1",
      "new_type": "utility_structure"
    },
    {
      "entity_id": "uuid2",
      "new_type": "survey_point"
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "reclassified": 2,
  "failed": 0,
  "results": [
    {
      "entity_id": "uuid1",
      "success": true
    },
    {
      "entity_id": "uuid2",
      "success": true
    }
  ]
}
```

---

### Get AI Classification Suggestions

Get AI-powered classification suggestions for an entity.

```http
GET /api/classification/ai-suggestions/{entity_id}
```

**Authentication**: Required

**Query Parameters**:
- `top_n` (optional, default: 3): Number of suggestions to return

**Response**:
```json
{
  "entity_id": "uuid",
  "suggestions": [
    {
      "entity_type": "utility_structure",
      "confidence": 0.85,
      "reasoning": "Point geometry on SS-MH layer with elevation attribute",
      "similar_entities": [
        {
          "entity_id": "uuid",
          "canonical_name": "MH-102",
          "similarity": 0.92
        }
      ]
    },
    {
      "entity_type": "survey_point",
      "confidence": 0.65,
      "reasoning": "Has point geometry and elevation"
    }
  ]
}
```

---

### Get Spatial Context

Get nearby entities to help with classification.

```http
GET /api/classification/spatial-context/{entity_id}
```

**Authentication**: Required

**Query Parameters**:
- `radius_ft` (optional, default: 50): Search radius in feet

**Response**:
```json
{
  "entity_id": "uuid",
  "nearby_entities": [
    {
      "entity_id": "uuid",
      "entity_type": "utility_line",
      "canonical_name": "SS-PIPE-001",
      "distance_ft": 15.2,
      "direction": "northeast"
    },
    {
      "entity_id": "uuid",
      "entity_type": "utility_structure",
      "canonical_name": "MH-102",
      "distance_ft": 120.5,
      "direction": "south"
    }
  ],
  "summary": {
    "total_nearby": 5,
    "most_common_type": "utility_line",
    "dominant_system": "Storm"
  }
}
```

---

### Get Geometry Preview

Get SVG preview of entity geometry.

```http
GET /api/classification/geometry-preview/{entity_id}
```

**Authentication**: Required

**Response**: SVG image
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">
  <circle cx="200" cy="200" r="50" fill="blue" />
</svg>
```

---

## Relationship Routes

**Blueprint**: `relationship_bp`
**Prefix**: `/api/relationships`

### Create Relationship Edge

Create a relationship between two entities.

```http
POST /api/relationships/edges
```

**Authentication**: Required

**Request Body**:
```json
{
  "project_id": "uuid",
  "source_entity_type": "utility_line",
  "source_entity_id": "uuid",
  "target_entity_type": "utility_structure",
  "target_entity_id": "uuid",
  "relationship_type": "CONNECTS_TO",
  "relationship_strength": 1.0,
  "is_bidirectional": false,
  "confidence_score": 0.95,
  "source": "auto",
  "relationship_metadata": {
    "connection_type": "upstream"
  }
}
```

**Response**:
```json
{
  "success": true,
  "relationship_id": "uuid",
  "message": "Relationship created successfully"
}
```

---

### Get Relationship Edge

Get details of a specific relationship.

```http
GET /api/relationships/edges/{edge_id}
```

**Authentication**: Required

**Response**:
```json
{
  "relationship_id": "uuid",
  "project_id": "uuid",
  "source_entity": {
    "entity_type": "utility_line",
    "entity_id": "uuid",
    "canonical_name": "SS-PIPE-001"
  },
  "target_entity": {
    "entity_type": "utility_structure",
    "entity_id": "uuid",
    "canonical_name": "MH-101"
  },
  "relationship_type": "CONNECTS_TO",
  "relationship_strength": 1.0,
  "is_bidirectional": false,
  "confidence_score": 0.95,
  "source": "auto",
  "relationship_metadata": {
    "connection_type": "upstream"
  },
  "is_active": true,
  "created_at": "2024-11-15T10:00:00Z"
}
```

---

### Query Related Entities

Get entities related to a specific entity.

```http
GET /api/relationships/query/related
```

**Authentication**: Required

**Query Parameters**:
- `entity_id` (required): Source entity ID
- `entity_type` (required): Source entity type
- `relationship_type` (optional): Filter by relationship type
- `direction` (optional): `outgoing`, `incoming`, `both` (default: `both`)
- `depth` (optional, default: 1): Traversal depth

**Response**:
```json
{
  "entity_id": "uuid",
  "related_entities": [
    {
      "entity_id": "uuid",
      "entity_type": "utility_line",
      "canonical_name": "SS-PIPE-001",
      "relationship_type": "CONNECTS_TO",
      "relationship_id": "uuid",
      "distance": 1
    }
  ],
  "total": 4
}
```

---

### Get Entity Subgraph

Get subgraph centered on an entity (BFS traversal).

```http
GET /api/relationships/query/subgraph
```

**Authentication**: Required

**Query Parameters**:
- `entity_id` (required): Center entity ID
- `entity_type` (required): Center entity type
- `depth` (optional, default: 2): Maximum traversal depth
- `max_nodes` (optional, default: 100): Maximum nodes to return

**Response**:
```json
{
  "center_entity": {
    "entity_id": "uuid",
    "entity_type": "utility_structure",
    "canonical_name": "MH-101"
  },
  "nodes": [
    {
      "entity_id": "uuid",
      "entity_type": "utility_line",
      "canonical_name": "SS-PIPE-001",
      "depth": 1
    }
  ],
  "edges": [
    {
      "relationship_id": "uuid",
      "source_entity_id": "uuid",
      "target_entity_id": "uuid",
      "relationship_type": "CONNECTS_TO"
    }
  ],
  "statistics": {
    "total_nodes": 15,
    "total_edges": 18,
    "max_depth_reached": 2
  }
}
```

---

### Find Shortest Path

Find shortest path between two entities.

```http
GET /api/relationships/query/path
```

**Authentication**: Required

**Query Parameters**:
- `source_entity_id` (required): Source entity ID
- `source_entity_type` (required): Source entity type
- `target_entity_id` (required): Target entity ID
- `target_entity_type` (required): Target entity type
- `max_depth` (optional, default: 10): Maximum path length

**Response**:
```json
{
  "path_found": true,
  "path_length": 3,
  "path": [
    {
      "entity_id": "uuid1",
      "entity_type": "utility_structure",
      "canonical_name": "MH-101"
    },
    {
      "entity_id": "uuid2",
      "entity_type": "utility_line",
      "canonical_name": "SS-PIPE-001"
    },
    {
      "entity_id": "uuid3",
      "entity_type": "utility_structure",
      "canonical_name": "MH-102"
    }
  ],
  "edges": [
    {
      "relationship_id": "uuid",
      "relationship_type": "CONNECTS_TO"
    }
  ]
}
```

---

### Validate Project Relationships

Run validation rules on project relationships.

```http
POST /api/relationships/validate/{project_id}
```

**Authentication**: Required

**Response**:
```json
{
  "validation_complete": true,
  "total_relationships": 1200,
  "violations": {
    "orphan_entities": 5,
    "cardinality_violations": 2,
    "type_incompatibility": 1,
    "circular_dependencies": 0
  },
  "health_score": 0.95
}
```

---

### Get Relationship Analytics

Get comprehensive relationship analytics for a project.

```http
GET /api/relationships/analytics/{project_id}/summary
```

**Authentication**: Required

**Response**:
```json
{
  "project_id": "uuid",
  "total_relationships": 1200,
  "relationship_types": {
    "CONNECTS_TO": 800,
    "REFERENCES": 300,
    "CONTAINS": 100
  },
  "graph_density": 0.45,
  "average_degree": 3.2,
  "most_connected_entities": [
    {
      "entity_id": "uuid",
      "canonical_name": "MH-101",
      "degree": 12
    }
  ],
  "health_score": 0.95
}
```

---

## GraphRAG Routes

**Blueprint**: `graphrag_bp`
**Prefix**: `/api/graphrag`

### Execute Natural Language Query

Execute a natural language query against the knowledge graph.

```http
POST /api/graphrag/query
```

**Authentication**: Required

**Request Body**:
```json
{
  "query": "Find all storm manholes within 100 feet of Basin A",
  "project_id": "uuid"
}
```

**Response**:
```json
{
  "query": "Find all storm manholes within 100 feet of Basin A",
  "parsed_query": {
    "intent": "spatial_query",
    "entity_types": ["utility_structure"],
    "filters": {
      "utility_system": "Storm",
      "structure_type": "Manhole"
    },
    "spatial": {
      "reference_entity": "Basin A",
      "reference_entity_id": "uuid",
      "distance_ft": 100
    }
  },
  "results": [
    {
      "entity_id": "uuid",
      "entity_type": "utility_structure",
      "canonical_name": "MH-101",
      "distance_ft": 45.2,
      "relevance_score": 0.95
    }
  ],
  "result_count": 5,
  "execution_time_ms": 120
}
```

---

### Parse Query

Parse natural language query without executing.

```http
POST /api/graphrag/query/parse
```

**Authentication**: Required

**Request Body**:
```json
{
  "query": "Find all storm manholes within 100 feet of Basin A"
}
```

**Response**:
```json
{
  "query": "Find all storm manholes within 100 feet of Basin A",
  "parsed": {
    "intent": "spatial_query",
    "entity_types": ["utility_structure"],
    "filters": {
      "utility_system": "Storm",
      "structure_type": "Manhole"
    },
    "spatial": {
      "reference_entity": "Basin A",
      "distance_ft": 100
    }
  },
  "confidence": 0.92
}
```

---

### Get Query Suggestions

Get autocomplete suggestions for natural language queries.

```http
GET /api/graphrag/query/suggestions?q={partial_query}
```

**Authentication**: Required

**Query Parameters**:
- `q` (required): Partial query text
- `limit` (optional, default: 5): Max suggestions

**Response**:
```json
{
  "suggestions": [
    "Find all storm manholes within 100 feet of Basin A",
    "Find all storm pipes with diameter greater than 12 inches",
    "Find survey points with elevation above 100 feet"
  ]
}
```

---

### Compute PageRank

Compute PageRank scores for project entities.

```http
GET /api/graphrag/analytics/pagerank?project_id={project_id}
```

**Authentication**: Required

**Response**:
```json
{
  "project_id": "uuid",
  "pagerank": [
    {
      "entity_id": "uuid",
      "canonical_name": "MH-101",
      "pagerank_score": 0.045,
      "rank": 1
    }
  ],
  "statistics": {
    "max_score": 0.045,
    "min_score": 0.001,
    "mean_score": 0.012
  }
}
```

---

### Detect Communities

Detect communities in the relationship graph.

```http
GET /api/graphrag/analytics/communities?project_id={project_id}
```

**Authentication**: Required

**Query Parameters**:
- `algorithm` (optional, default: `louvain`): Algorithm (`louvain`, `label_propagation`)

**Response**:
```json
{
  "project_id": "uuid",
  "algorithm": "louvain",
  "communities": [
    {
      "community_id": 0,
      "size": 150,
      "entities": ["uuid1", "uuid2", "..."]
    }
  ],
  "total_communities": 5,
  "modularity": 0.45
}
```

---

## AI Search Routes

**Blueprint**: `ai_search_bp`
**Prefix**: `/api/ai/search`

### Find Similar Entities

Find entities with similar vector embeddings.

```http
GET /api/ai/search/similar/entity/{entity_id}
```

**Authentication**: Required

**Query Parameters**:
- `limit` (optional, default: 10): Max results
- `threshold` (optional, default: 0.7): Min similarity score

**Response**:
```json
{
  "entity_id": "uuid",
  "similar_entities": [
    {
      "entity_id": "uuid",
      "entity_type": "utility_structure",
      "canonical_name": "MH-102",
      "similarity_score": 0.95,
      "attributes": {
        "structure_type": "Manhole",
        "utility_system": "Storm"
      }
    }
  ]
}
```

---

### Search by Text

Find entities matching text description.

```http
POST /api/ai/search/similar/text
```

**Authentication**: Required

**Request Body**:
```json
{
  "text": "storm manhole with 48 inch diameter",
  "project_id": "uuid",
  "entity_types": ["utility_structure"],
  "limit": 10
}
```

**Response**:
```json
{
  "query": "storm manhole with 48 inch diameter",
  "results": [
    {
      "entity_id": "uuid",
      "entity_type": "utility_structure",
      "canonical_name": "MH-101",
      "similarity_score": 0.88,
      "attributes": {
        "structure_type": "Manhole",
        "utility_system": "Storm",
        "size_mm": 1200
      }
    }
  ]
}
```

---

### Cluster Entities

Cluster entities using K-means or other algorithms.

```http
POST /api/ai/search/cluster
```

**Authentication**: Required

**Request Body**:
```json
{
  "project_id": "uuid",
  "entity_types": ["utility_structure"],
  "n_clusters": 5,
  "algorithm": "kmeans"
}
```

**Response**:
```json
{
  "algorithm": "kmeans",
  "n_clusters": 5,
  "clusters": [
    {
      "cluster_id": 0,
      "size": 45,
      "centroid_entity_id": "uuid",
      "entities": ["uuid1", "uuid2", "..."]
    }
  ],
  "silhouette_score": 0.72
}
```

---

### Find Duplicates

Detect potential duplicate entities using semantic similarity.

```http
GET /api/ai/search/duplicates?project_id={project_id}
```

**Authentication**: Required

**Query Parameters**:
- `threshold` (optional, default: 0.95): Similarity threshold

**Response**:
```json
{
  "duplicate_pairs": [
    {
      "entity1": {
        "entity_id": "uuid1",
        "canonical_name": "MH-101"
      },
      "entity2": {
        "entity_id": "uuid2",
        "canonical_name": "MH-101A"
      },
      "similarity_score": 0.97,
      "reason": "Similar attributes and geometry"
    }
  ],
  "total_pairs": 3
}
```

---

## Quality Routes

**Blueprint**: `quality_bp`
**Prefix**: `/api/ai/quality`

### Get Entity Quality Details

Get quality score breakdown for an entity.

```http
GET /api/ai/quality/entity/{entity_id}
```

**Authentication**: Required

**Response**:
```json
{
  "entity_id": "uuid",
  "quality_score": 0.87,
  "factors": {
    "completeness": 0.95,
    "accuracy": 0.85,
    "consistency": 0.90,
    "relationships": 0.80
  },
  "issues": [
    {
      "severity": "warning",
      "message": "Missing optional attribute: owner"
    }
  ],
  "recommendations": [
    "Add more relationships to improve connectivity score"
  ]
}
```

---

### Get Project Quality Summary

Get quality summary for entire project.

```http
GET /api/ai/quality/project/{project_id}/summary
```

**Authentication**: Required

**Response**:
```json
{
  "project_id": "uuid",
  "overall_quality_score": 0.85,
  "entity_quality": {
    "average_score": 0.85,
    "median_score": 0.88,
    "above_threshold": 1350,
    "below_threshold": 150
  },
  "by_entity_type": {
    "utility_structure": 0.90,
    "utility_line": 0.85,
    "survey_point": 0.82
  },
  "trends": {
    "improving": true,
    "recent_change": 0.05
  }
}
```

---

## Specification Routes

### List Spec Standards

Get all specification standards.

```http
GET /api/spec-standards
```

**Authentication**: Required

**Response**:
```json
{
  "spec_standards": [
    {
      "spec_standard_id": "uuid",
      "standard_name": "American Public Works Association (APWA)",
      "abbreviation": "APWA",
      "organization": "APWA",
      "publication_year": 2021,
      "version": "2021",
      "is_active": true
    }
  ]
}
```

---

### Get Spec Library

Get specification library items.

```http
GET /api/spec-library
```

**Authentication**: Required

**Query Parameters**:
- `csi_code` (optional): Filter by CSI MasterFormat code
- `search` (optional): Search spec titles

**Response**:
```json
{
  "specs": [
    {
      "spec_library_id": "uuid",
      "spec_number": "33 30 00",
      "spec_title": "Sanitary Sewerage",
      "csi_code": "33 30 00",
      "spec_standard_id": "uuid",
      "is_active": true
    }
  ]
}
```

---

### Create Spec-Geometry Link

Link a specification to an entity.

```http
POST /api/spec-geometry-links
```

**Authentication**: Required

**Request Body**:
```json
{
  "spec_library_id": "uuid",
  "entity_id": "uuid",
  "entity_type": "utility_line",
  "project_id": "uuid",
  "link_type": "governs",
  "relationship_notes": "PVC pipe specification"
}
```

**Response**:
```json
{
  "success": true,
  "link_id": "uuid",
  "compliance_status": "pending",
  "message": "Spec linked successfully"
}
```

---

### Get Entity Specs

Get all specifications linked to an entity.

```http
GET /api/entities/{entity_id}/specs
```

**Authentication**: Required

**Response**:
```json
{
  "entity_id": "uuid",
  "spec_links": [
    {
      "link_id": "uuid",
      "spec_library_id": "uuid",
      "spec_number": "33 30 00",
      "spec_title": "Sanitary Sewerage",
      "link_type": "governs",
      "compliance_status": "compliant",
      "linked_at": "2024-11-01T10:00:00Z"
    }
  ]
}
```

---

## Standards Routes

### Get Layer Standards

Get all layer standards.

```http
GET /api/standards/layers
```

**Authentication**: Required

**Query Parameters**:
- `discipline` (optional): Filter by discipline code
- `search` (optional): Search layer names

**Response**:
```json
{
  "layer_standards": [
    {
      "layer_id": "uuid",
      "layer_name": "SS-MH",
      "discipline_code": "C",
      "category_code": "UTIL",
      "type_code": "MH",
      "description": "Sanitary sewer manholes",
      "color": "Red",
      "linetype": "Continuous",
      "is_active": true
    }
  ]
}
```

---

### Get CSI MasterFormat

Get CSI MasterFormat codes.

```http
GET /api/csi-masterformat
```

**Authentication**: Required

**Query Parameters**:
- `parent_code` (optional): Get children of specific code
- `level` (optional): Filter by hierarchy level (1=division, 2=section, etc.)

**Response**:
```json
{
  "csi_codes": [
    {
      "csi_code": "33 30 00",
      "csi_title": "Sanitary Sewerage",
      "parent_code": "33 00 00",
      "level": 2,
      "division_number": 33,
      "is_division": false
    }
  ]
}
```

---

## Utility Endpoints

### Health Check

Check system health.

```http
GET /api/health
```

**Authentication**: Not required

**Response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "2.0",
  "uptime_seconds": 86400
}
```

---

### Get Active Project

Get current active project from session.

```http
GET /api/active-project
```

**Authentication**: Required

**Response**:
```json
{
  "active_project_id": "uuid",
  "project_name": "Downtown Water Main Replacement"
}
```

---

### Set Active Project

Set active project in session.

```http
POST /api/active-project
```

**Authentication**: Required

**Request Body**:
```json
{
  "project_id": "uuid"
}
```

**Response**:
```json
{
  "success": true,
  "active_project_id": "uuid"
}
```

---

## Appendix: Common Query Patterns

### Pagination

Most list endpoints support pagination:

```http
GET /api/projects/{project_id}/entities?page=2&per_page=50
```

### Filtering

Most endpoints support filtering via query parameters:

```http
GET /api/projects/{project_id}/entities?entity_type=utility_structure&classification_state=needs_review
```

### Sorting

Some endpoints support sorting:

```http
GET /api/projects?sort=created_at&order=desc
```

### Field Selection

Some endpoints support field selection to reduce response size:

```http
GET /api/projects/{project_id}/entities?fields=entity_id,canonical_name,entity_type
```

---

## Conclusion

This API specification covers all major endpoints in the Survey Data System. For implementation details, see [ARCHITECTURE.md](ARCHITECTURE.md). For development setup, see [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md).

**API Versioning**: Currently unversioned. Future versions will use `/api/v1/*` prefix.

**Rate Limiting**: Not yet implemented. Future versions will enforce rate limits.

**API Documentation**: OpenAPI/Swagger documentation generation planned for Phase 3.
