# ACAD-GIS Toolkit Testing Safety Guide

**Budget Cap:** $100.00 for OpenAI embeddings  
**Purpose:** Safe testing guardrails to prevent overspending and data corruption during initial testing

---

## 🛡️ Safety Features Overview

### 1. Embedding Cost Controls

✅ **Hard Budget Cap:** $100.00  
✅ **Automatic Warnings:** Alerts at $50, $75, $90  
✅ **Dry Run Mode:** Preview costs before spending  
✅ **Real-time Tracking:** Per-operation and cumulative costs  
✅ **Auto-Stop:** Operations blocked when budget cap reached  

### 2. Import Safety Features

✅ **Idempotent Keys:** Natural keys (name) prevent duplicates  
✅ **Preview Mode:** See what will be loaded without changes  
✅ **Before/After Counts:** Verify entity count changes  
✅ **Error Tracking:** All errors logged and reported  

### 3. Web UI Safety

✅ **Confirmation Prompts:** Warns before embedding operations  
✅ **Cost Display:** Shows estimated and actual costs  
✅ **Operation History:** Tracks all operations in output log  

---

## 🚀 Pre-Flight Checklist

Before running ANY toolkit operations, run the health check:

```bash
# Run from project root
python tools/health_check.py
```

**Expected output:**
```
ACAD-GIS Toolkit Health Check
======================================================================

Database Connectivity:
  ✓ Database connection
  ✓ Core schema tables
  ✓ PostGIS extension
  ✓ pgvector extension
  ✓ Helper functions
  ✓ Materialized views

Toolkit Modules:
  ✓ Ingestion module
  ✓ Embeddings module
  ✓ Relationships module
  ✓ Validation module
  ✓ Maintenance module

Integration Tests:
  ✓ Sample data round-trip

Total: 12 passed, 0 failed

🎉 All checks passed! Toolkit is ready to use.
```

⚠️ **If any checks fail, DO NOT proceed with testing!**

---

## 📋 Safe Testing Workflow

### Step 1: Check Budget Status

```bash
python examples/generate_embeddings_with_budget.py status
```

**Output:**
```
BUDGET STATUS
======================================================================
Model: text-embedding-3-small
Budget cap: $100.00
Cumulative spent: $0.00
Budget remaining: $100.00
Budget used: 0.0%
```

### Step 2: Preview Operations (Dry Run)

**For Embeddings:**
```python
from tools.embeddings.embedding_generator import EmbeddingGenerator

# Dry run mode - no API calls, no cost
generator = EmbeddingGenerator(
    provider='openai',
    model='text-embedding-3-small',
    budget_cap=100.0,
    dry_run=True  # PREVIEW MODE
)

# Preview cost
stats = generator.generate_for_table(
    table_name='layer_standards',
    text_columns=['name', 'description'],
    where_clause='WHERE entity_id IS NOT NULL LIMIT 100'
)

print(f"Estimated cost: ${stats['estimated_cost']:.4f}")
print(f"Budget remaining: ${stats['budget_remaining']:.2f}")
```

**For Data Import:**
```python
from tools.ingestion.standards_loader import StandardsLoader

# Preview mode - no database changes
loader = StandardsLoader(preview_mode=True)

# Load your data
stats = loader.load_layers(your_layer_data)
# Shows what WOULD be inserted/updated without making changes
```

### Step 3: Run Small Tests First

**Start with 10 entities, not 1000:**

```python
# Good: Small test
stats = generator.generate_for_table(
    table_name='layer_standards',
    text_columns=['name', 'description'],
    where_clause='WHERE entity_id IS NOT NULL LIMIT 10'  # Only 10!
)

# Bad: Too many at once
stats = generator.generate_for_table(
    table_name='layer_standards',
    text_columns=['name', 'description'],
    where_clause='WHERE entity_id IS NOT NULL LIMIT 1000'  # Risky!
)
```

### Step 4: Verify Results

**Check counts match expectations:**

```python
from tools.db_utils import get_entity_stats

# Get stats before
stats_before = get_entity_stats()
print(f"Entities before: {stats_before['total_entities']}")

# Run operation
loader = StandardsLoader()
result = loader.load_layers(your_data)

# Get stats after
stats_after = get_entity_stats()
print(f"Entities after: {stats_after['total_entities']}")
print(f"Expected change: {len(your_data)}")
print(f"Actual change: {stats_after['total_entities'] - stats_before['total_entities']}")
```

### Step 5: Monitor Budget

```bash
# Check budget after each operation
python examples/generate_embeddings_with_budget.py status
```

---

## 💰 Budget Management

### Current Budget: $100.00

**Cost Estimates:**
- 10 entities: ~$0.001 (0.001%)
- 100 entities: ~$0.01 (0.01%)
- 1,000 entities: ~$0.10 (0.1%)
- 10,000 entities: ~$1.00 (1%)

**Warning Thresholds:**
- $50: ℹ️ INFO (50% used)
- $75: ⚠️ WARNING (75% used)
- $90: ⚠️ WARNING (90% used - approaching cap!)
- $100: 🛑 STOP (budget cap reached)

### When You Hit the Cap

**Option 1: Increase Budget (if approved)**
```python
generator = EmbeddingGenerator(
    provider='openai',
    model='text-embedding-3-small',
    budget_cap=200.0  # Increase to $200
)
```

**Option 2: Reset Tracking (new budget period)**
```bash
python examples/generate_embeddings_with_budget.py reset
```

⚠️ **WARNING: Only reset when starting a new budget period!**

---

## 🔄 Rollback Procedures

### If You Load Bad Data

**Using Idempotent Keys (Recommended):**
```python
# Simply reload with correct data - idempotent keys prevent duplicates
loader = StandardsLoader()
stats = loader.load_layers(corrected_data)
# Updates existing entities, no duplicates created
```

**Delete Specific Entities:**
```python
from tools.db_utils import execute_query

# Delete by name (natural key)
execute_query(
    "DELETE FROM layer_standards WHERE name = %s",
    ('BAD_LAYER_NAME',),
    fetch=False
)
```

**Delete All from a Session:**
```python
# If you know the timestamp
execute_query(
    "DELETE FROM layer_standards WHERE created_at > %s",
    ('2025-10-30 14:00:00',),
    fetch=False
)
```

### If Embeddings Are Wrong

**Regenerate for Specific Entities:**
```python
generator = EmbeddingGenerator()

# Will overwrite old embeddings
stats = generator.refresh_embeddings(
    entity_ids=['uuid1', 'uuid2', 'uuid3']
)
```

**Reset Embedding Cost Tracking:**
```python
generator = EmbeddingGenerator()
generator.reset_cost_tracking()  # Resets to $0.00
```

---

## ⚠️ Common Pitfalls to Avoid

### ❌ DON'T:

1. **Skip dry run mode** - Always preview costs first
2. **Process everything at once** - Start small (10-100 entities)
3. **Ignore warnings** - Budget warnings mean slow down!
4. **Forget to check** - Verify counts before/after operations
5. **Run without health check** - Always run pre-flight first

### ✅ DO:

1. **Use preview mode** - See what will happen without cost
2. **Start small** - Test with 10 entities, then scale up
3. **Monitor budget** - Check status between operations
4. **Verify results** - Count entities and check data quality
5. **Use idempotent keys** - Safe to re-run imports

---

## 📊 Verification Commands

### Check Database State

```python
from tools.db_utils import get_entity_stats, execute_query

# Overall stats
stats = get_entity_stats()
print(f"Total entities: {stats['total_entities']}")
print(f"Embeddings: {stats['embeddings']['current']}")
print(f"Relationships: {stats['relationships']}")
print(f"Avg quality: {stats['quality']['avg_quality']:.3f}")

# Specific table counts
result = execute_query("SELECT COUNT(*) as count FROM layer_standards")
print(f"Layers: {result[0]['count']}")

result = execute_query("SELECT COUNT(*) as count FROM block_definitions")
print(f"Blocks: {result[0]['count']}")
```

### Run Validation

```python
from tools.validation.data_validator import DataValidator

validator = DataValidator()
results = validator.validate_all_standards()

print(f"Total issues: {results['total_issues']}")
for severity, count in results['issues_by_severity'].items():
    print(f"  {severity}: {count}")
```

---

## 🎯 Recommended Testing Sequence

### Phase 1: Minimal Test (Cost: ~$0.01)

1. Run health check ✓
2. Load 10 sample layers (preview mode)
3. Load 10 sample layers (actual)
4. Generate embeddings for 10 layers (dry run)
5. Generate embeddings for 10 layers (actual)
6. Verify: Check counts and budget

**Expected budget used: $0.01-0.05**

### Phase 2: Small Scale Test (Cost: ~$0.10)

1. Load 100 layers
2. Generate embeddings for 100 layers (dry run first!)
3. Build relationships (semantic)
4. Run validation
5. Verify: Check quality scores

**Expected budget used: $0.10-0.20**

### Phase 3: Production Scale (Cost: ~$1-10)

1. Load all CAD standards (layers, blocks, details)
2. Preview embedding costs (dry run)
3. Generate embeddings in batches of 100
4. Monitor budget between batches
5. Build complete knowledge graph
6. Run full validation
7. Run maintenance

**Expected budget used: $1-10 depending on data volume**

---

## 🚨 Emergency Procedures

### Budget Cap Exceeded

```
🛑 BUDGET CAP REACHED!
   Current: $100.00
   This operation: $0.50
   Projected total: $100.50
   Budget cap: $100.00
   Would exceed budget by: $0.50
```

**Actions:**
1. STOP all operations
2. Review what was spent: `python examples/generate_embeddings_with_budget.py status`
3. Contact budget approver
4. Either increase cap or wait for new budget period
5. Reset tracking when approved: `python examples/generate_embeddings_with_budget.py reset`

### Data Corruption Detected

1. **STOP** all import operations
2. Run validation: `python examples/validate_data_example.py`
3. Check for duplicates:
   ```sql
   SELECT name, COUNT(*) 
   FROM layer_standards 
   GROUP BY name 
   HAVING COUNT(*) > 1;
   ```
4. If duplicates exist, use idempotent import to fix
5. If serious corruption, consider Replit's rollback feature

---

## 📞 Support Resources

**Documentation:**
- `/DATABASE_ARCHITECTURE_GUIDE.md` - Complete technical reference
- `/TOOLKIT_SETUP_COMPLETE.md` - Toolkit usage guide
- `/tools/README.md` - Module reference
- `/examples/README.md` - Example scripts

**Tools:**
- `tools/health_check.py` - Pre-flight system check
- `examples/generate_embeddings_with_budget.py` - Safe embedding generation
- `tools/validation/data_validator.py` - Data quality checks

**Quick Commands:**
```bash
# Health check
python tools/health_check.py

# Budget status
python examples/generate_embeddings_with_budget.py status

# Validate data
python examples/validate_data_example.py

# Database stats
python -c "from tools.db_utils import get_entity_stats; import json; print(json.dumps(get_entity_stats(), indent=2))"
```

---

## ✅ Testing Checklist

Before each testing session:

- [ ] Run `python tools/health_check.py` - all checks pass
- [ ] Check budget status - know current spend
- [ ] Use preview/dry-run mode first
- [ ] Start with small sample (10-100 entities)
- [ ] Verify results match expectations
- [ ] Monitor budget between operations
- [ ] Document any issues or errors

After each testing session:

- [ ] Run validation checks
- [ ] Verify entity counts
- [ ] Check budget remaining
- [ ] Document what was tested
- [ ] Note any issues for investigation

---

**Remember:** The toolkit has safety features, but YOU are the final safety check. When in doubt, preview first, start small, and verify often!

**Budget Status:** Always know where you stand: `python examples/generate_embeddings_with_budget.py status`

**Last Updated:** October 30, 2025  
**Budget Cap:** $100.00  
**Toolkit Version:** 1.0.0
