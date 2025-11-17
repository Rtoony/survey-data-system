# Phase 1 Quick Start Guide
**AI Embedding & Graph RAG Implementation - Week 1**

This guide will walk you through completing Phase 1 of your AI implementation in **30-60 minutes**.

---

## 📋 **Prerequisites**

Before you begin, verify you have:

- ✅ PostgreSQL database with pgvector extension installed
- ✅ Database credentials in `.env` file
- ✅ OpenAI API key in `.env` file
- ✅ Python 3.11+ installed
- ✅ Required Python packages installed

### **Verify Prerequisites**

```bash
cd /home/user/survey-data-system

# Check .env file exists
ls -la .env

# Test database connection (from psql)
psql "$DATABASE_URL" -c "SELECT version()"

# Check pgvector extension
psql "$DATABASE_URL" -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'"
```

---

## 🚀 **Step-by-Step Execution**

### **Step 0: Fix Database Schema (REQUIRED)**

⚠️ **Important**: Run this first to add missing columns to the `embedding_models` table.

```bash
python3 scripts/phase1_00_fix_schema.py
```

**What this does:**
- Checks if `embedding_models` table has required columns
- Adds `cost_per_1k_tokens` and `max_input_tokens` columns if missing
- Sets default values for OpenAI model
- Verifies schema is correct

**Expected Output:**
```
✓ All required columns present!
✓ SCHEMA FIX SUCCESSFUL

You can now run Phase 1 scripts:
  python3 scripts/phase1_01_generate_embeddings.py --dry-run
```

**⏱ Duration**: 5-10 seconds
**✅ Success if**: No errors and schema verification passes

---

### **Step 1: Dry Run (Cost Estimation)**

First, let's estimate costs without making any API calls:

```bash
python3 scripts/phase1_01_generate_embeddings.py --dry-run --limit 100
```

**Expected Output:**
```
Cost Estimate:
  Layers: 100
  Estimated tokens: ~6,500
  Estimated cost: $0.0013

✓ DRY RUN MODE - No API calls will be made
```

**✅ Success if**: Estimated cost is under $0.10

---

### **Step 2: Generate Embeddings**

Now generate actual embeddings:

```bash
python3 scripts/phase1_01_generate_embeddings.py --limit 100
```

**What this does:**
- Fetches 100 layer standards without embeddings
- Generates 1536-dimensional vectors using OpenAI
- Saves embeddings to `entity_embeddings` table
- Registers model in `embedding_models` table
- Tracks cost and token usage

**Prompts:**
```
Proceed with embedding generation? (yes/no): yes
```

**Expected Output:**
```
RESULTS:
  ✓ Generated: 100
  ✗ Failed: 0
  Total tokens: 6,543
  Total cost: $0.0013

✓ Phase 1 - Task 1 Complete!
```

**⏱ Duration**: 30-60 seconds
**💰 Cost**: ~$0.0015-0.0020

**✅ Success if**: Generated >= 50 embeddings with $0 failures

---

### **Step 3: Build Relationships**

Create semantic relationships between similar entities:

```bash
python3 scripts/phase1_02_build_relationships.py --threshold 0.75 --limit 5
```

**What this does:**
- Finds pairs of similar entities using vector similarity
- Creates bidirectional `similar_to` relationships
- Stores in `entity_relationships` table with confidence scores
- Builds the knowledge graph for GraphRAG

**Prompts:**
```
Sample similarity pairs:
  C-UTIL-STORM-CB-EXIST-PT     ↔ C-UTIL-STORM-INLET-EXIST-PT   (87.2%)
  ...

Create 245 relationship pairs? (yes/no): yes
```

**Expected Output:**
```
RESULTS:
  ✓ Created: 245 relationship pairs
  ✗ Failed: 0
  Total edges: 490 (bidirectional)

✓ Phase 1 - Task 2 Complete!
```

**⏱ Duration**: 10-30 seconds
**💰 Cost**: $0 (uses existing embeddings)

**✅ Success if**: Created >= 100 relationship pairs

**Troubleshooting:**
- If "No similar pairs found":
  - Lower threshold: `--threshold 0.70`
  - Or generate more embeddings first

---

### **Step 4: Verify Implementation**

Verify everything is working:

```bash
python3 scripts/phase1_03_verify.py
```

**What this checks:**
1. Embedding counts and dimensions
2. Relationship counts and types
3. Similarity search function
4. GraphRAG traversal function
5. Quality score distribution

**Expected Output:**
```
PHASE 1 VERIFICATION

1. Checking Embeddings...
  Total embeddings: 100
  Current embeddings: 100
  Avg dimensions: 1536

2. Checking Relationships...
  Total relationships: 490
  Entities with outbound: 98

3. Testing Similarity Search...
  Test entity: C-UTIL-STORM-CB-EXIST-PT
  Similar entities found: 5
  ✓ Similarity search working!

4. Testing Graph Traversal (GraphRAG)...
  Test entity: C-UTIL-SEWER-MANHOLE-EXIST-PT
  Related entities (2-hops): 12
  ✓ GraphRAG traversal working!

Success Criteria:
  ✓ At least 50 embeddings generated
  ✓ At least 100 relationships created
  ✓ Similarity search functional

🎉 PHASE 1 SUCCESSFUL!
```

**⏱ Duration**: 5-10 seconds

**✅ Success if**: All checkmarks pass

---

## 🎯 **Success Criteria**

Phase 1 is complete when:

- [x] **100+ embeddings** generated and stored
- [x] **100+ relationships** created
- [x] **Similarity search** returns relevant results
- [x] **GraphRAG traversal** follows relationship chains
- [x] **Total cost** under $0.10

---

## 🧪 **Testing the AI Features**

### **Test 1: Similarity Search in Database**

```bash
psql "$DATABASE_URL" << 'SQL'
-- Find layers similar to a specific one
WITH test_layer AS (
    SELECT entity_id, name
    FROM layer_standards
    WHERE name ILIKE '%storm%'
    LIMIT 1
)
SELECT
    tl.name as original_layer,
    se.canonical_name as similar_layer,
    s.similarity_score
FROM test_layer tl
CROSS JOIN LATERAL (
    SELECT * FROM find_similar_entities(tl.entity_id::uuid, 0.70, 5)
) s
JOIN standards_entities se ON s.entity_id = se.entity_id
ORDER BY s.similarity_score DESC;
SQL
```

**Expected**: 5 similar layers with similarity scores

---

### **Test 2: GraphRAG Multi-Hop Query**

```bash
psql "$DATABASE_URL" << 'SQL'
-- Find entities within 2 hops of a layer
WITH test_entity AS (
    SELECT entity_id, canonical_name
    FROM standards_entities
    WHERE entity_type = 'layer'
    LIMIT 1
)
SELECT
    te.canonical_name as start_entity,
    se.canonical_name as related_entity,
    r.hop_distance,
    r.relationship_path
FROM test_entity te
CROSS JOIN LATERAL (
    SELECT * FROM find_related_entities(te.entity_id::uuid, 2, NULL)
) r
JOIN standards_entities se ON r.entity_id = se.entity_id
ORDER BY r.hop_distance, r.relationship_path;
SQL
```

**Expected**: Multiple entities at 1-hop and 2-hop distances

---

## 📊 **What You've Built**

After completing Phase 1, your system has:

### **AI Infrastructure** ✅
- Vector embeddings for semantic search
- Knowledge graph with relationship edges
- Quality scoring system
- Multi-hop graph traversal

### **Database Functions** ✅
- `find_similar_entities()` - Vector similarity search
- `find_related_entities()` - GraphRAG traversal
- `hybrid_search()` - Combined search (ready for Phase 2)
- `compute_quality_score()` - Automated quality tracking

### **Data** ✅
- 100+ entities with 1536-dim embeddings
- 100+ semantic relationships
- Bidirectional graph edges for traversal
- Quality scores updated automatically

---

## 🔧 **Troubleshooting**

### **Issue: "No module named 'openai'"**
```bash
pip install openai psycopg2-binary python-dotenv
```

### **Issue: "OPENAI_API_KEY not found"**
Check `.env` file exists and contains:
```
OPENAI_API_KEY=sk-proj-...
```

### **Issue: "Database connection failed"**
Verify credentials:
```bash
psql "$DATABASE_URL" -c "SELECT 1"
```

### **Issue: "pgvector extension not found"**
Install pgvector:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### **Issue: "No layers without embeddings"**
All layers already have embeddings! Skip to Step 3 or increase limit:
```bash
python3 scripts/phase1_01_generate_embeddings.py --limit 200
```

### **Issue: "No similar pairs found"**
Lower the similarity threshold:
```bash
python3 scripts/phase1_02_build_relationships.py --threshold 0.65
```

### **Issue: Cost concerns**
Use dry-run mode first:
```bash
python3 scripts/phase1_01_generate_embeddings.py --dry-run --limit 50
```

Reduce batch size:
```bash
python3 scripts/phase1_01_generate_embeddings.py --limit 50
```

---

## 💰 **Cost Breakdown**

| Task | Tokens | Cost | Time |
|------|--------|------|------|
| 100 embeddings | ~6,500 | $0.0013 | 30-60s |
| Relationships | 0 | $0 | 10-30s |
| Verification | 0 | $0 | 5-10s |
| **Total** | **~6,500** | **~$0.0015** | **~2min** |

**Budget**: $10 cap (more than enough for 500,000+ embeddings)

---

## 📈 **Next Steps**

### **Immediate (This Week)**
1. ✅ **Generate more embeddings** for other entity types:
   ```bash
   # Blocks
   python3 scripts/phase1_01_generate_embeddings.py --entity-type block --limit 100

   # Details
   python3 scripts/phase1_01_generate_embeddings.py --entity-type detail --limit 100
   ```

2. ✅ **Add "Find Similar" UI** (see `AI_IMPLEMENTATION_GAME_PLAN.md` Phase 1 Task 1.4)

3. ✅ **Demo to stakeholders** - Show semantic search in action

### **Phase 2 (Next Week)**
See `AI_IMPLEMENTATION_GAME_PLAN.md` for:
- Auto-generate embeddings on DXF import
- Hybrid search in Advanced Search UI
- Background worker for async processing
- Quality score automation

---

## 📚 **Documentation**

- **Full Audit**: `AI_EMBEDDING_GRAPH_RAG_AUDIT.md`
- **Implementation Plan**: `AI_IMPLEMENTATION_GAME_PLAN.md`
- **Query Examples**: `AI_QUERY_PATTERNS_AND_EXAMPLES.md`
- **Database Architecture**: `DATABASE_ARCHITECTURE_GUIDE.md`

---

## ✅ **Phase 1 Checklist**

- [ ] Dry run completed successfully
- [ ] 100+ embeddings generated
- [ ] 100+ relationships created
- [ ] Verification script passes all checks
- [ ] Similarity search tested manually
- [ ] GraphRAG traversal tested manually
- [ ] Total cost under $0.10
- [ ] Ready to demo to users

---

## 🎉 **Congratulations!**

You've successfully activated the AI features in your survey-data-system!

Your system now has:
- ✅ **Semantic search** - Find entities by meaning, not just keywords
- ✅ **Knowledge graph** - Explore relationships between entities
- ✅ **GraphRAG** - Multi-hop reasoning for complex queries
- ✅ **Quality tracking** - Automatically score data completeness

**Next**: Add UI features so users can actually see and use these capabilities!

---

**Questions?** See the troubleshooting section above or check the full documentation in `AI_IMPLEMENTATION_GAME_PLAN.md`.

**Ready for Phase 2?** Continue with the game plan to integrate AI into your core workflows.
