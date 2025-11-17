# Phase 2 Quick Start Guide
**Auto-Integration - Make AI Automatic**

This guide walks you through Phase 2: integrating AI features into your core workflows so embeddings generate automatically.

---

## 📋 **Prerequisites**

- ✅ Phase 1 completed successfully
- ✅ 100+ embeddings already in database
- ✅ Relationships created and verified
- ✅ Database access from local/Replit environment

---

## 🚀 **Step-by-Step Execution**

### **Step 1: Apply Database Migration** (30 seconds)

Create the embedding queue infrastructure:

```bash
psql "$DATABASE_URL" < database/migrations/phase2_01_embedding_queue.sql
```

**What this creates:**
- `embedding_generation_queue` table
- Triggers on `layer_standards`, `block_definitions`, `detail_standards`
- Quality score auto-update triggers
- Queue statistics functions

**Expected Output:**
```
NOTICE:  Phase 2 Migration Complete!
NOTICE:
NOTICE:  Created:
NOTICE:    - embedding_generation_queue table
NOTICE:    - trigger_queue_embedding() function
NOTICE:    - Triggers on layer_standards, block_definitions, detail_standards
...
```

**Verify:**
```sql
-- Check table exists
SELECT COUNT(*) FROM embedding_generation_queue;

-- Check triggers exist
SELECT * FROM get_queue_stats();
```

---

### **Step 2: Start Background Worker** (in separate terminal)

The worker processes the queue continuously:

```bash
# Terminal 1: Start worker
python workers/embedding_worker.py --batch-size 50 --poll-interval 10
```

**What it does:**
- Polls `embedding_generation_queue` every 10 seconds
- Processes up to 50 items per batch
- Generates embeddings via OpenAI API
- Updates quality scores automatically
- Tracks cost and stays within budget cap

**Expected Output:**
```
======================================================================
EMBEDDING WORKER STARTED
======================================================================
  Model: text-embedding-3-small
  Batch size: 50
  Poll interval: 10s
  Budget cap: $100.00/day

Press Ctrl+C to stop
======================================================================

  Processing 0 items...
  (waiting for queue items...)
```

**Leave this running!** It will process items as they're added.

---

### **Step 3: Test Auto-Generation** (Terminal 2)

While worker is running, create a new layer to trigger auto-embedding:

```bash
# Terminal 2: Test insertion
psql "$DATABASE_URL" << 'SQL'
INSERT INTO layer_standards (name, description, category)
VALUES ('TEST-AUTO-EMBED', 'Test automatic embedding generation', 'test')
RETURNING layer_id, entity_id;
SQL
```

**Watch Terminal 1** (worker) - you should see:
```
  Processing 1 items...
  ✓ Completed: 1, Failed: 0
```

**Verify in database:**
```sql
-- Check queue
SELECT * FROM embedding_generation_queue
WHERE text_to_embed ILIKE '%TEST-AUTO-EMBED%';

-- Check embedding was created
SELECT ee.embedding_id, ee.tokens_used, ee.created_at
FROM entity_embeddings ee
JOIN layer_standards ls ON ee.entity_id = ls.entity_id
WHERE ls.name = 'TEST-AUTO-EMBED';
```

**Expected**: Embedding created within 10 seconds! ✅

---

### **Step 4: Test Quality Score Auto-Update**

Quality scores should update automatically when embeddings are added:

```sql
-- Check quality score was updated
SELECT
    ls.name,
    se.quality_score,
    EXISTS(SELECT 1 FROM entity_embeddings WHERE entity_id = se.entity_id) as has_embedding
FROM layer_standards ls
JOIN standards_entities se ON ls.entity_id = se.entity_id
WHERE ls.name = 'TEST-AUTO-EMBED';
```

**Expected**: `quality_score` > 0.7 because it now has an embedding

---

### **Step 5: Run as System Service** (Production)

For production, run the worker as a systemd service:

**File**: `/etc/systemd/system/embedding-worker.service`

```ini
[Unit]
Description=AI Embedding Worker
After=postgresql.service network.target
Wants=postgresql.service

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/survey-data-system
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 workers/embedding_worker.py --batch-size 50
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable embedding-worker
sudo systemctl start embedding-worker
sudo systemctl status embedding-worker
```

**View logs:**
```bash
sudo journalctl -u embedding-worker -f
```

---

## ✅ **Success Criteria**

Phase 2 is successful when:

- [x] Migration applied without errors
- [x] Worker starts and polls queue
- [x] New entities trigger embedding generation automatically
- [x] Embeddings appear in database within 10 seconds
- [x] Quality scores update automatically
- [x] Worker runs continuously without crashes

---

## 🧪 **Testing the Integration**

### **Test 1: Bulk Insert**

Insert multiple layers and watch worker process them:

```sql
INSERT INTO layer_standards (name, description, category)
SELECT
    'TEST-BULK-' || i,
    'Bulk test layer ' || i,
    'test'
FROM generate_series(1, 10) AS i;
```

**Watch worker**: Should process 10 items in next batch

---

### **Test 2: DXF Import Integration** (If available)

Import a DXF file and verify embeddings are generated automatically for intelligent objects.

**Check queue after import:**
```sql
SELECT COUNT(*) FROM embedding_generation_queue WHERE status = 'pending';
```

**Expected**: Queue populated with newly imported entities

---

### **Test 3: Queue Statistics**

Monitor queue health:

```sql
SELECT * FROM get_queue_stats();
```

**Expected Output:**
```
status     | priority | count | oldest_timestamp
-----------|----------|-------|------------------
pending    | normal   | 5     | 2025-11-17 10:30:00
processing | high     | 2     | 2025-11-17 10:31:00
completed  | normal   | 123   | 2025-11-17 09:00:00
```

---

## 🐛 **Troubleshooting**

### **Issue: Worker not starting**

**Check 1**: OpenAI API key set?
```bash
echo $OPENAI_API_KEY
```

**Check 2**: Database connection?
```bash
psql "$DATABASE_URL" -c "SELECT 1"
```

**Check 3**: Python dependencies?
```bash
pip install openai psycopg2-binary python-dotenv
```

---

### **Issue: Queue items not processing**

**Check 1**: Worker running?
```bash
ps aux | grep embedding_worker
```

**Check 2**: Items in queue?
```sql
SELECT COUNT(*) FROM embedding_generation_queue WHERE status = 'pending';
```

**Check 3**: Budget cap reached?
```sql
SELECT SUM(ee.tokens_used * em.cost_per_1k_tokens / 1000.0) as today_cost
FROM entity_embeddings ee
JOIN embedding_models em ON ee.model_id = em.model_id
WHERE ee.created_at >= CURRENT_DATE;
```

---

### **Issue: Triggers not firing**

**Verify triggers exist:**
```sql
SELECT
    trigger_name,
    event_object_table,
    action_statement
FROM information_schema.triggers
WHERE trigger_name LIKE '%embedding_queue%';
```

**Manual test:**
```sql
-- This should add item to queue
INSERT INTO layer_standards (name, description)
VALUES ('TRIGGER-TEST', 'Testing trigger');

-- Check queue
SELECT * FROM embedding_generation_queue WHERE text_to_embed LIKE '%TRIGGER-TEST%';
```

---

### **Issue: High costs**

**Check daily spending:**
```sql
SELECT
    DATE(ee.created_at) as date,
    COUNT(*) as embeddings,
    SUM(ee.tokens_used) as tokens,
    SUM(ee.tokens_used * em.cost_per_1k_tokens / 1000.0) as cost
FROM entity_embeddings ee
JOIN embedding_models em ON ee.model_id = em.model_id
WHERE ee.created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(ee.created_at)
ORDER BY date DESC;
```

**Reduce budget cap:**
```bash
# Restart worker with lower cap
python workers/embedding_worker.py --budget-cap 10.0
```

---

## 📊 **Monitoring**

### **Queue Health Dashboard**

```sql
WITH stats AS (
    SELECT
        status,
        priority,
        COUNT(*) as count,
        AVG(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_at))) as avg_age_seconds
    FROM embedding_generation_queue
    GROUP BY status, priority
)
SELECT
    status,
    priority,
    count,
    ROUND(avg_age_seconds / 60, 1) as avg_age_minutes
FROM stats
ORDER BY status, priority;
```

---

### **Worker Performance**

```sql
-- Embeddings generated per hour (last 24 hours)
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as embeddings_generated,
    SUM(tokens_used) as tokens
FROM entity_embeddings
WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;
```

---

## 💰 **Cost Projection**

| Scenario | Items/Day | Tokens/Day | Cost/Day | Cost/Month |
|----------|-----------|------------|----------|------------|
| Light usage | 100 | ~6,500 | $0.0013 | $0.04 |
| Medium usage | 1,000 | ~65,000 | $0.0130 | $0.40 |
| Heavy usage | 10,000 | ~650,000 | $0.1300 | $4.00 |

**Budget recommendations:**
- Development: $10/day cap
- Production: $50-100/day cap

---

## 📈 **Next Steps**

### **Completed Phase 2? ✅**

You now have:
- ✅ Automatic embedding generation
- ✅ Background worker processing queue
- ✅ Quality scores auto-updating
- ✅ Production-ready infrastructure

### **Move to Phase 3:**

Add user-facing AI features:
- Natural language query interface
- Smart autocomplete for layer names
- Graph visualization with real data
- AI context panel in map viewer

See `AI_IMPLEMENTATION_GAME_PLAN.md` Phase 3 for details.

---

## 🎉 **You're Done!**

Your AI system now runs **automatically** in the background. Every new entity gets:
- ✅ Vector embedding generated within 10 seconds
- ✅ Quality score updated automatically
- ✅ Ready for similarity search immediately

**No manual intervention required!** 🚀

---

**Created**: November 17, 2025
**Phase**: 2 of 4 (Auto-Integration)
**Duration**: 30 minutes setup, then runs automatically
**Cost**: ~$0.01-5.00/day depending on usage
