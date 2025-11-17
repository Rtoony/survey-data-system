# Phase 1 Implementation Scripts

This directory contains production-ready scripts for implementing AI embeddings and Graph RAG features (Phase 1).

## 📁 **Files**

| Script | Purpose | Duration | Cost |
|--------|---------|----------|------|
| `phase1_01_generate_embeddings.py` | Generate vector embeddings using OpenAI | 30-60s | ~$0.0015 |
| `phase1_02_build_relationships.py` | Build semantic relationships from embeddings | 10-30s | $0 |
| `phase1_03_verify.py` | Verify Phase 1 implementation | 5-10s | $0 |
| `PHASE1_QUICKSTART.md` | Complete step-by-step guide | - | - |

## 🚀 **Quick Start**

```bash
# 1. Estimate cost (no API calls)
python3 scripts/phase1_01_generate_embeddings.py --dry-run

# 2. Generate embeddings
python3 scripts/phase1_01_generate_embeddings.py --limit 100

# 3. Build relationships
python3 scripts/phase1_02_build_relationships.py

# 4. Verify everything works
python3 scripts/phase1_03_verify.py
```

**Total time**: ~2 minutes
**Total cost**: ~$0.0015

## 📖 **Detailed Guide**

See `PHASE1_QUICKSTART.md` for:
- Prerequisites checklist
- Step-by-step execution
- Troubleshooting guide
- Testing procedures
- Success criteria

## 🎯 **What You'll Build**

After running these scripts, you'll have:

- ✅ 100+ vector embeddings (1536 dimensions)
- ✅ 100+ semantic relationships
- ✅ Working similarity search
- ✅ GraphRAG multi-hop traversal
- ✅ Quality scoring system

## 💡 **Script Options**

### **phase1_01_generate_embeddings.py**

```bash
# Generate embeddings for first 100 layers
python3 scripts/phase1_01_generate_embeddings.py --limit 100

# Dry run (estimate cost only)
python3 scripts/phase1_01_generate_embeddings.py --dry-run --limit 100

# Custom budget cap
python3 scripts/phase1_01_generate_embeddings.py --budget-cap 5.0

# Help
python3 scripts/phase1_01_generate_embeddings.py --help
```

### **phase1_02_build_relationships.py**

```bash
# Default (75% similarity, 5 per entity)
python3 scripts/phase1_02_build_relationships.py

# Lower threshold for more relationships
python3 scripts/phase1_02_build_relationships.py --threshold 0.70

# More relationships per entity
python3 scripts/phase1_02_build_relationships.py --limit 10

# Help
python3 scripts/phase1_02_build_relationships.py --help
```

### **phase1_03_verify.py**

```bash
# Run all verification checks
python3 scripts/phase1_03_verify.py
```

## 🔧 **Requirements**

### **Python Packages**
```bash
pip install openai psycopg2-binary python-dotenv
```

### **Environment Variables**
Create `.env` file with:
```
OPENAI_API_KEY=sk-proj-...
DATABASE_URL=postgresql://...
```

### **Database Extensions**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS postgis;
```

## 📊 **Expected Results**

### **After phase1_01_generate_embeddings.py**
```
RESULTS:
  ✓ Generated: 100
  ✗ Failed: 0
  Total tokens: 6,543
  Total cost: $0.0013
```

### **After phase1_02_build_relationships.py**
```
RESULTS:
  ✓ Created: 245 relationship pairs
  ✗ Failed: 0
  Total edges: 490 (bidirectional)
```

### **After phase1_03_verify.py**
```
Success Criteria:
  ✓ At least 50 embeddings generated
  ✓ At least 100 relationships created
  ✓ Similarity search functional

🎉 PHASE 1 SUCCESSFUL!
```

## 🐛 **Troubleshooting**

### **"No module named 'openai'"**
```bash
pip install openai psycopg2-binary python-dotenv
```

### **"OPENAI_API_KEY not found"**
Create `.env` file with your API key

### **"Database connection failed"**
Verify credentials in `.env` file

### **"No layers without embeddings"**
All layers already have embeddings! Either:
- Skip to relationship building
- Increase limit: `--limit 200`
- Process different entity type

### **"No similar pairs found"**
Lower threshold: `--threshold 0.65`

## 📈 **Next Steps**

1. **Review results**: Check `phase1_03_verify.py` output
2. **Test manually**: Run similarity searches in database
3. **Add UI features**: See `AI_IMPLEMENTATION_GAME_PLAN.md` Phase 1 Task 1.4
4. **Proceed to Phase 2**: Auto-integration and hybrid search

## 📚 **Documentation**

- `PHASE1_QUICKSTART.md` - Step-by-step guide (this directory)
- `AI_IMPLEMENTATION_GAME_PLAN.md` - Full roadmap (project root)
- `AI_EMBEDDING_GRAPH_RAG_AUDIT.md` - Complete audit (project root)
- `AI_QUERY_PATTERNS_AND_EXAMPLES.md` - Query examples (project root)

## 💰 **Cost Estimates**

| Operation | Tokens | Cost |
|-----------|--------|------|
| 100 embeddings | ~6,500 | $0.0013 |
| 500 embeddings | ~32,500 | $0.0065 |
| 1,000 embeddings | ~65,000 | $0.0130 |
| 10,000 embeddings | ~650,000 | $0.1300 |

**OpenAI pricing**: $0.00002 per 1K tokens (text-embedding-3-small)

## ✅ **Success Checklist**

- [ ] Scripts executed without errors
- [ ] 100+ embeddings in database
- [ ] 100+ relationships created
- [ ] Similarity search returns results
- [ ] GraphRAG traversal works
- [ ] Total cost under $0.10
- [ ] Ready for Phase 2

---

**Created**: November 17, 2025
**Author**: Claude (Anthropic AI)
**Phase**: 1 of 4 (Week 1 - Quick Wins)
