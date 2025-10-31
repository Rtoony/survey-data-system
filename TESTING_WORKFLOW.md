# ACAD-GIS Testing Workflow Guide

**Version:** 1.0  
**Last Updated:** October 31, 2025  
**Purpose:** Comprehensive step-by-step guide for testing all AI toolkit features

---

## Table of Contents

1. [Pre-Flight Checklist](#pre-flight-checklist)
2. [Phase 1: Health Checks (Free)](#phase-1-health-checks)
3. [Phase 2: Manual Data Entry (Free)](#phase-2-manual-data-entry)
4. [Phase 3: Embeddings Generation ($0.01-0.02)](#phase-3-embeddings-generation)
5. [Phase 4: Relationship Building (Free)](#phase-4-relationship-building)
6. [Phase 5: Visualizations (Free)](#phase-5-visualizations)
7. [Phase 6: API Testing (Free)](#phase-6-api-testing)
8. [Phase 7: Search & Quality (Free)](#phase-7-search--quality)
9. [Verification Checklist](#verification-checklist)
10. [Troubleshooting Guide](#troubleshooting-guide)
11. [Quick Reference](#quick-reference)

---

## Pre-Flight Checklist

Before starting any tests, verify these prerequisites:

### ✅ Database Connection
```bash
# Check database connection
psql $DATABASE_URL -c "SELECT version();"

# Verify PostGIS and pgvector extensions
psql $DATABASE_URL -c "SELECT PostGIS_Version();"
psql $DATABASE_URL -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

**Expected Results:**
- PostgreSQL version displays (should be 12+)
- PostGIS version displays (should be 3.3+)
- pgvector extension shows installed

### ✅ Environment Variables
```bash
# Check required environment variables
env | grep DB_
env | grep OPENAI_API_KEY
```

**Required Variables:**
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `OPENAI_API_KEY` (for embeddings generation)

**⚠️ If OPENAI_API_KEY is missing:**
- Visit `/toolkit` → "Generate Embeddings" will show API key request
- Or set it via Replit Secrets panel

### ✅ Flask Application
```bash
# Verify Flask app is running
curl http://localhost:5000/
```

**Expected Result:** HTML response with "ACAD-GIS Schema Explorer" title

### ✅ Budget Planning
**Embedding Costs (OpenAI text-embedding-3-small):**
- 10 entities: ~$0.01
- 100 entities: ~$0.10
- 1,000 entities: ~$1.00

**Safety Limits Built-In:**
- Hard cap: $100
- Warnings at: $50, $75, $90
- Dry-run mode available for cost preview

---

## Phase 1: Health Checks

**Estimated Time:** 2 minutes  
**Cost:** Free  
**Purpose:** Verify all systems are operational

### Step 1.1: Run Automated Health Check

1. Open browser to `http://localhost:5000/toolkit`
2. Click **"Run Health Check"** button (top right)
3. Wait 5-10 seconds for results

**Expected Results (12 tests should pass):**

✅ **Database Tests (4/4):**
- PostgreSQL connection successful
- PostGIS extension available
- pgvector extension available
- Required tables exist

✅ **Module Tests (5/5):**
- Ingestion module imports
- Embeddings module imports
- Relationships module imports
- Validation module imports
- Maintenance module imports

✅ **Data Tests (3/3):**
- Sample entity round-trip successful
- Embedding generation test successful
- Relationship creation test successful

### Step 1.2: Verify Database Schema

1. Navigate to `http://localhost:5000/schema`
2. Click **"Database Health"** tab
3. Review table counts

**Expected Results:**
```
standards_entities: 0 rows
standards_abbreviations: 0 rows
standards_layers: 0 rows
standards_blocks: 0 rows
standards_details: 0 rows
entity_embeddings: 0 rows
entity_relationships: 0 rows
```

### Step 1.3: Check Console Logs

1. Open browser DevTools (F12)
2. Check Console tab for errors
3. Verify no red error messages

**⚠️ Stop if:**
- Any health check fails
- Database connection errors appear
- Missing extensions detected

**→ See [Troubleshooting Guide](#troubleshooting-guide) for fixes**

---

## Phase 2: Manual Data Entry

**Estimated Time:** 5 minutes  
**Cost:** Free  
**Purpose:** Create test data for AI tools

### Step 2.1: Add Test Abbreviations

1. Navigate to `http://localhost:5000/data-manager`
2. Click **"Abbreviations"** tab
3. Click **"+ Add New"** button
4. Enter test data:

```
Code: CL
Full Name: Centerline
Description: Center line of roadway or feature
Category: Survey
Notes: Used for alignment reference
```

5. Click **"Save"**
6. Repeat for additional abbreviations:

```
Code: BM
Full Name: Benchmark
Description: Survey control point with known elevation
Category: Survey

Code: ROW
Full Name: Right of Way
Description: Public property boundary
Category: Legal

Code: EX
Full Name: Existing
Description: Existing conditions or features
Category: General

Code: PROP
Full Name: Proposed
Description: Proposed design features
Category: General
```

**Expected Result:** 5 abbreviations created, displayed in table

### Step 2.2: Add Test Layer Standards

1. Click **"Layers"** tab
2. Click **"+ Add New"**
3. Enter test layers:

```
Layer Name: C-TOPO
Description: Topographic survey data
Category: Civil
Color: Cyan
Linetype: Continuous
```

```
Layer Name: C-PROP-ROAD
Description: Proposed roadway centerlines
Category: Civil
Color: Red
Linetype: Continuous
```

```
Layer Name: A-WALL
Description: Architectural walls
Category: Architectural
Color: White
Linetype: Continuous
```

**Expected Result:** 3 layer standards created

### Step 2.3: Verify Entity Creation

1. Open `http://localhost:5000/schema`
2. Click **"Database Health"** tab
3. Check row counts

**Expected Results:**
```
standards_abbreviations: 5 rows
standards_layers: 3 rows
standards_entities: 8 rows (auto-created for each abbreviation + layer)
```

### Step 2.4: Database Verification Query

```sql
-- Check entities were created
SELECT entity_type, COUNT(*) 
FROM standards_entities 
GROUP BY entity_type;

-- View sample entities
SELECT entity_id, entity_type, name, description 
FROM standards_entities 
LIMIT 5;
```

**Expected Output:**
```
entity_type        | count
abbreviation       | 5
layer              | 3

entity_id | entity_type  | name | description
...       | abbreviation | CL   | Centerline
...       | layer        | C-TOPO | Topographic survey data
```

---

## Phase 3: Embeddings Generation

**Estimated Time:** 10 minutes  
**Cost:** ~$0.01-0.02  
**Purpose:** Test AI embedding generation pipeline

### Step 3.1: Preview Embedding Costs (Dry-Run)

1. Navigate to `http://localhost:5000/toolkit`
2. Click **"Generate Embeddings"** section
3. Select **"Dry Run (Preview Only)"** checkbox
4. Click **"Generate Embeddings"**

**Expected Result:**
```
Dry Run Results:
- Entities to process: 8
- Estimated API calls: 8
- Estimated cost: $0.008
- Time estimate: ~10 seconds
```

### Step 3.2: Generate Actual Embeddings

1. Uncheck **"Dry Run"** checkbox
2. Click **"Generate Embeddings"**
3. Watch progress bar (should complete in 10-15 seconds)

**Expected Result:**
```
✅ Embedding Generation Complete
- Entities processed: 8
- Embeddings created: 8
- Actual cost: $0.008
- Duration: 12.3 seconds
```

### Step 3.3: Verify Embeddings in Database

```sql
-- Check embedding counts
SELECT COUNT(*) FROM entity_embeddings;

-- View embedding details
SELECT 
    ee.entity_id,
    se.name,
    ee.model_name,
    ee.embedding_version,
    array_length(ee.embedding, 1) as dimensions,
    ee.created_at
FROM entity_embeddings ee
JOIN standards_entities se ON ee.entity_id = se.entity_id
LIMIT 5;
```

**Expected Output:**
```
count: 8

entity_id | name   | model_name              | dimensions | created_at
...       | CL     | text-embedding-3-small  | 1536       | 2025-10-31...
...       | C-TOPO | text-embedding-3-small  | 1536       | 2025-10-31...
```

### Step 3.4: Test Embedding Search API

```bash
# Search for similar entities
curl -X POST http://localhost:5000/api/toolkit/embeddings/search \
  -H "Content-Type: application/json" \
  -d '{"query": "road centerline", "limit": 3}'
```

**Expected Response:**
```json
{
  "results": [
    {
      "entity_id": "...",
      "name": "CL",
      "description": "Centerline",
      "similarity": 0.89
    },
    {
      "entity_id": "...",
      "name": "C-PROP-ROAD",
      "similarity": 0.85
    }
  ]
}
```

**⚠️ Cost Tracking:**
- Check actual cost in response
- Should be < $0.01 for 8 entities
- Budget remaining displayed in UI

---

## Phase 4: Relationship Building

**Estimated Time:** 5 minutes  
**Cost:** Free (database operations only)  
**Purpose:** Test GraphRAG relationship detection

### Step 4.1: Build Semantic Relationships

1. Navigate to `http://localhost:5000/toolkit`
2. Click **"Build Relationships"** section
3. Select **"Semantic Similarity"** checkbox
4. Set **Similarity Threshold: 0.75**
5. Click **"Build Relationships"**

**Expected Result:**
```
✅ Relationship Building Complete
- Relationships created: 12
- Semantic: 12
- Spatial: 0 (no geometry data yet)
- Engineering: 0
- Duration: 2.1 seconds
```

### Step 4.2: Verify Relationships in Database

```sql
-- Check relationship counts
SELECT relationship_type, COUNT(*) 
FROM entity_relationships 
GROUP BY relationship_type;

-- View sample relationships
SELECT 
    se1.name as subject,
    er.relationship_type,
    se2.name as object,
    er.confidence_score,
    er.attributes->>'reason' as reason
FROM entity_relationships er
JOIN standards_entities se1 ON er.subject_entity_id = se1.entity_id
JOIN standards_entities se2 ON er.object_entity_id = se2.entity_id
LIMIT 5;
```

**Expected Output:**
```
relationship_type | count
semantic          | 12

subject | relationship_type | object    | confidence_score | reason
CL      | semantic         | C-PROP-ROAD| 0.85            | Both relate to road centerlines
BM      | semantic         | C-TOPO     | 0.78            | Survey control and topography
```

### Step 4.3: Test Relationship API

```bash
# Get relationships for an entity
curl http://localhost:5000/api/toolkit/relationships/entity/<entity_id>
```

**Expected Response:**
```json
{
  "entity_id": "...",
  "name": "CL",
  "relationships": [
    {
      "related_entity_id": "...",
      "related_name": "C-PROP-ROAD",
      "type": "semantic",
      "confidence": 0.85,
      "direction": "outgoing"
    }
  ]
}
```

---

## Phase 5: Visualizations

**Estimated Time:** 5 minutes  
**Cost:** Free  
**Purpose:** Test interactive graph and dashboard

### Step 5.1: Knowledge Graph Visualization

1. Navigate to `http://localhost:5000/graph`
2. Verify graph loads with nodes and edges

**Expected Visualization:**
- **8 nodes** (circles) representing entities
- **12 edges** (lines) connecting related entities
- **Color coding:**
  - Blue edges = Spatial relationships
  - Green edges = Semantic relationships
  - Orange edges = Engineering relationships
- Zoom/pan controls work
- Click node to see details panel

### Step 5.2: Test Graph Interactions

1. **Zoom in/out** - Mouse wheel or pinch
2. **Pan** - Click and drag background
3. **Click a node** - Details panel appears on right
4. **Filter relationships** - Uncheck "Semantic" to hide green edges

**Expected Behavior:**
- Graph smoothly zooms and pans
- Node details show entity name, type, description
- Filters update graph in real-time

### Step 5.3: Quality Dashboard

1. Navigate to `http://localhost:5000/quality-dashboard`
2. Review metrics

**Expected Metrics:**
- **Embedding Coverage:** 100% (8/8 entities)
- **Relationship Density:** 1.5 (12 relationships / 8 entities)
- **Orphaned Entities:** 0
- **Quality Score Distribution:** Chart showing distribution
- **Relationship Breakdown:**
  - Semantic: 12 (100%)
  - Spatial: 0
  - Engineering: 0
- **Missing Embeddings:** None

### Step 5.4: Verify Dashboard Charts

**Charts to check:**
- **Quality Score Distribution** - Bar chart with scores 0-100
- **Relationship Type Breakdown** - Pie chart showing semantic (100%)
- **Missing Embeddings by Type** - Empty (all have embeddings)

---

## Phase 6: API Testing

**Estimated Time:** 10 minutes  
**Cost:** Free  
**Purpose:** Validate all REST API endpoints

### Step 6.1: Stats & Health Endpoints

```bash
# Database stats
curl http://localhost:5000/api/toolkit/stats

# Health check
curl http://localhost:5000/api/toolkit/health
```

**Expected Responses:**

**Stats:**
```json
{
  "total_entities": 8,
  "total_embeddings": 8,
  "total_relationships": 12,
  "embedding_coverage": 100.0,
  "by_entity_type": {
    "abbreviation": 5,
    "layer": 3
  }
}
```

**Health:**
```json
{
  "status": "healthy",
  "tests_passed": 12,
  "tests_failed": 0,
  "details": { ... }
}
```

### Step 6.2: Search Endpoints

```bash
# Full-text search
curl "http://localhost:5000/api/toolkit/search?q=centerline&limit=5"

# Hybrid search (text + semantic)
curl -X POST http://localhost:5000/api/toolkit/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{"query": "road features", "limit": 5, "weights": {"text": 0.5, "semantic": 0.5}}'
```

**Expected Responses:**
- Results ranked by relevance
- Mix of text match and semantic similarity
- Quality scores included

### Step 6.3: Graph Data Endpoint

```bash
# Get graph visualization data
curl http://localhost:5000/api/toolkit/graph/data
```

**Expected Response:**
```json
{
  "nodes": [
    {"id": "...", "label": "CL", "type": "abbreviation"},
    {"id": "...", "label": "C-TOPO", "type": "layer"}
  ],
  "edges": [
    {
      "from": "...",
      "to": "...",
      "type": "semantic",
      "confidence": 0.85
    }
  ]
}
```

### Step 6.4: Quality Metrics Endpoint

```bash
# Get quality dashboard metrics
curl http://localhost:5000/api/toolkit/quality/metrics
```

**Expected Response:**
```json
{
  "embedding_coverage": 100.0,
  "relationship_density": 1.5,
  "orphaned_entities": 0,
  "quality_distribution": {...},
  "relationship_breakdown": {
    "semantic": 12,
    "spatial": 0,
    "engineering": 0
  }
}
```

### Step 6.5: Validation Endpoint

```bash
# Run data validation
curl -X POST http://localhost:5000/api/toolkit/validate
```

**Expected Response:**
```json
{
  "status": "success",
  "issues_found": 0,
  "checks_performed": 8,
  "details": {
    "missing_embeddings": 0,
    "orphaned_entities": 0,
    "invalid_relationships": 0
  }
}
```

---

## Phase 7: Search & Quality

**Estimated Time:** 5 minutes  
**Cost:** Free  
**Purpose:** Test search functionality and quality scoring

### Step 7.1: Test Data Manager Search

1. Navigate to `http://localhost:5000/data-manager`
2. Click **"Abbreviations"** tab
3. Use search box: type **"road"**

**Expected Result:**
- Filters to show abbreviations containing "road" in name/description
- Should show "CL" (Centerline mentions roadway)

### Step 7.2: Test Semantic Search

1. Navigate to `http://localhost:5000/toolkit`
2. Scroll to **"Search"** section
3. Enter query: **"survey control points"**
4. Click **"Search"**

**Expected Results:**
- Shows "BM" (Benchmark) as top result
- Shows "C-TOPO" as related result
- Quality scores displayed
- Sorted by relevance

### Step 7.3: Verify Quality Scores

```sql
-- Check quality scores were calculated
SELECT 
    name,
    entity_type,
    quality_score,
    (attributes->>'has_embedding')::boolean as has_embedding,
    (attributes->>'relationship_count')::int as relationship_count
FROM standards_entities
ORDER BY quality_score DESC;
```

**Expected Output:**
```
name    | entity_type  | quality_score | has_embedding | relationship_count
CL      | abbreviation | 95.0         | true          | 3
C-TOPO  | layer        | 92.0         | true          | 2
...
```

**Quality Score Formula:**
- Base: 50 points
- Has embedding: +25 points
- Has description: +10 points
- Per relationship: +5 points (max 15)

### Step 7.4: Test Quality Dashboard Filters

1. Go to `http://localhost:5000/quality-dashboard`
2. Use filters to find:
   - Entities with quality score > 90
   - Entities with 2+ relationships
   - Entities missing embeddings (should be none)

---

## Verification Checklist

After completing all phases, verify:

### ✅ Data Layer
- [ ] 8 entities exist in `standards_entities`
- [ ] 5 abbreviations in `standards_abbreviations`
- [ ] 3 layers in `standards_layers`
- [ ] All entities have quality scores

### ✅ AI Features
- [ ] 8 embeddings exist in `entity_embeddings`
- [ ] All embeddings are 1536 dimensions
- [ ] 12 semantic relationships exist
- [ ] No orphaned entities

### ✅ Web Interface
- [ ] All pages load without errors
- [ ] Search works in Data Manager
- [ ] Knowledge Graph displays correctly
- [ ] Quality Dashboard shows metrics
- [ ] Toolkit operations complete successfully

### ✅ API Endpoints
- [ ] `/api/toolkit/stats` returns correct counts
- [ ] `/api/toolkit/health` shows all tests passing
- [ ] `/api/toolkit/search` returns relevant results
- [ ] `/api/toolkit/graph/data` returns nodes and edges
- [ ] `/api/toolkit/quality/metrics` shows 100% coverage

### ✅ Cost Tracking
- [ ] Total cost < $0.02
- [ ] Cost warnings appeared appropriately
- [ ] Budget tracking displayed in UI

---

## Troubleshooting Guide

### Issue: Health Check Fails

**Symptom:** Red X on database connection test

**Solution:**
```bash
# Check database environment variables
env | grep DB_

# Test connection manually
psql $DATABASE_URL -c "SELECT 1;"

# Restart Flask app
# (Workflows restart automatically)
```

### Issue: No Embeddings Generated

**Symptom:** "API key not found" error

**Solution:**
1. Check `OPENAI_API_KEY` exists: `env | grep OPENAI`
2. If missing, add via Replit Secrets panel
3. Restart Flask app after adding secret

### Issue: Relationships Not Created

**Symptom:** 0 relationships after building

**Solution:**
```sql
-- Verify embeddings exist
SELECT COUNT(*) FROM entity_embeddings;

-- Check if entities have embeddings
SELECT se.name, ee.entity_id IS NOT NULL as has_embedding
FROM standards_entities se
LEFT JOIN entity_embeddings ee ON se.entity_id = ee.entity_id;
```

**Fix:** Generate embeddings first, then build relationships

### Issue: Knowledge Graph Empty

**Symptom:** Blank graph visualization

**Solution:**
1. Open browser DevTools (F12) → Console tab
2. Check for JavaScript errors
3. Verify API returns data:
   ```bash
   curl http://localhost:5000/api/toolkit/graph/data
   ```
4. If API returns empty: Add data via Data Manager
5. If API has data but graph empty: Check browser console for Vis.js errors

### Issue: Quality Dashboard Shows 0%

**Symptom:** All metrics show zero

**Solution:**
```sql
-- Check if quality scores were calculated
SELECT COUNT(*) FROM standards_entities WHERE quality_score > 0;

-- Recalculate quality scores
UPDATE standards_entities
SET quality_score = 50
  + CASE WHEN EXISTS (
      SELECT 1 FROM entity_embeddings 
      WHERE entity_id = standards_entities.entity_id
    ) THEN 25 ELSE 0 END
  + CASE WHEN description IS NOT NULL THEN 10 ELSE 0 END;
```

### Issue: Search Returns No Results

**Symptom:** Empty search results

**Solution:**
```sql
-- Verify search_vector is populated
SELECT name, search_vector IS NOT NULL as has_search_vector
FROM standards_entities;

-- Update search vectors if needed
UPDATE standards_abbreviations
SET search_vector = 
  setweight(to_tsvector('english', COALESCE(code, '')), 'A') ||
  setweight(to_tsvector('english', COALESCE(full_name, '')), 'A') ||
  setweight(to_tsvector('english', COALESCE(description, '')), 'B');
```

### Emergency: Reset All Test Data

**Use this to start over:**

```sql
-- WARNING: Deletes all data!
TRUNCATE TABLE entity_relationships CASCADE;
TRUNCATE TABLE entity_embeddings CASCADE;
TRUNCATE TABLE standards_details CASCADE;
TRUNCATE TABLE standards_blocks CASCADE;
TRUNCATE TABLE standards_layers CASCADE;
TRUNCATE TABLE standards_abbreviations CASCADE;
TRUNCATE TABLE standards_entities CASCADE;
```

---

## Quick Reference

### All URLs

| Page | URL | Purpose |
|------|-----|---------|
| Home | `/` | Schema Explorer home |
| AI Toolkit | `/toolkit` | AI tool operations |
| Data Manager | `/data-manager` | CRUD operations |
| Schema Viewer | `/schema` | Database schema |
| Knowledge Graph | `/graph` | Graph visualization |
| Quality Dashboard | `/quality-dashboard` | Metrics & analytics |

### All API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/toolkit/stats` | GET | Database statistics |
| `/api/toolkit/health` | GET | Health check |
| `/api/toolkit/search` | GET | Full-text search |
| `/api/toolkit/search/hybrid` | POST | Hybrid search |
| `/api/toolkit/embeddings/generate` | POST | Generate embeddings |
| `/api/toolkit/embeddings/search` | POST | Semantic search |
| `/api/toolkit/relationships/build` | POST | Build relationships |
| `/api/toolkit/relationships/entity/<id>` | GET | Get entity relationships |
| `/api/toolkit/graph/data` | GET | Graph visualization data |
| `/api/toolkit/quality/metrics` | GET | Quality metrics |
| `/api/toolkit/validate` | POST | Validate data |
| `/api/toolkit/maintenance/cleanup` | POST | Cleanup orphans |
| `/api/toolkit/maintenance/rebuild` | POST | Rebuild indexes |

### Cost Estimates

| Operation | Entities | Cost | Time |
|-----------|----------|------|------|
| Embeddings (small test) | 10 | $0.01 | 10s |
| Embeddings (medium test) | 100 | $0.10 | 90s |
| Embeddings (full CAD standards) | 1,000 | $1.00 | 15m |
| Relationships | Any | Free | <5s |
| Search | Any | Free | <1s |

### Database Quick Queries

```sql
-- Entity counts by type
SELECT entity_type, COUNT(*) FROM standards_entities GROUP BY entity_type;

-- Embedding coverage
SELECT 
  (SELECT COUNT(*) FROM entity_embeddings)::float / 
  NULLIF((SELECT COUNT(*) FROM standards_entities), 0) * 100 
  AS coverage_percent;

-- Relationship summary
SELECT relationship_type, COUNT(*) 
FROM entity_relationships 
GROUP BY relationship_type;

-- Top quality entities
SELECT name, entity_type, quality_score 
FROM standards_entities 
ORDER BY quality_score DESC 
LIMIT 10;

-- Find orphaned entities
SELECT name, entity_type 
FROM standards_entities se
WHERE NOT EXISTS (
  SELECT 1 FROM entity_relationships 
  WHERE subject_entity_id = se.entity_id 
     OR object_entity_id = se.entity_id
);
```

---

## Next Steps

After completing this testing workflow:

1. **Scale Up**: Add more CAD standards data
2. **Real DXF Files**: Import actual CAD drawings
3. **Advanced GraphRAG**: Test multi-hop queries
4. **Performance**: Test with 1,000+ entities
5. **Production**: Deploy to Supabase for team access

**Questions or Issues?**
- Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- Review [DATABASE_ARCHITECTURE_GUIDE.md](./DATABASE_ARCHITECTURE_GUIDE.md)
- See [TESTING_SAFETY_GUIDE.md](./TESTING_SAFETY_GUIDE.md) for safety procedures

---

**Happy Testing! 🚀**
