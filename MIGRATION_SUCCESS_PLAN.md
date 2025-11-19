# Phase 16 Migration Success Plan

## Migration 0003: JSONB & TSVECTOR Type Upgrades

**Target:** Production Supabase Database
**Migration File:** `migrations/versions/0003_upgrade_json_types.py`
**Estimated Duration:** 2-5 minutes (depends on table sizes)
**Risk Level:** 🟡 MEDIUM (Type conversions with data preservation)

---

## 📋 Pre-Migration Checklist

Before applying this migration to production, complete ALL items below:

- [ ] **Code Review**: Migration file reviewed and approved
- [ ] **Staging Test**: Migration successfully applied to staging/dev environment
- [ ] **Database Backup**: Full backup created and verified
- [ ] **Data Validation**: Confirmed all `attributes` columns contain NULL or valid JSON
- [ ] **Connection String**: Production DATABASE_URL ready and tested
- [ ] **Rollback Plan**: Downgrade procedure documented and understood
- [ ] **Maintenance Window**: Scheduled downtime or low-traffic period identified
- [ ] **Team Notification**: Stakeholders informed of migration window

---

## 🔍 Step 1: Pre-Migration Validation

### 1.1 Verify Database Connection

```bash
# Test connection to Supabase
psql "$DATABASE_URL" -c "SELECT version();"
```

**Expected Output:**
```
PostgreSQL 15.x on x86_64-pc-linux-gnu...
```

### 1.2 Check Current Migration State

```bash
# Verify current migration head
alembic current
```

**Expected Output:**
```
0002 (head), add_project_archiving
```

⚠️ **If output is different:**
- If shows `0001`: You must apply migration 0002 first
- If shows `0003`: Migration already applied, no action needed
- If shows nothing: Database is not stamped, see "Emergency Procedures" section

### 1.3 Validate Data Integrity

Run these queries to check for non-JSON data in `attributes` columns:

```sql
-- Check for invalid JSON in projects.attributes
SELECT project_id, attributes
FROM projects
WHERE attributes IS NOT NULL
  AND attributes !~ '^[\{\[].*[\}\]]$'
LIMIT 5;

-- Check for invalid JSON in survey_points.attributes
SELECT point_id, attributes
FROM survey_points
WHERE attributes IS NOT NULL
  AND attributes !~ '^[\{\[].*[\}\]]$'
LIMIT 5;

-- If ANY rows are returned, you have invalid JSON data!
-- You must clean the data before proceeding.
```

**Expected Output:** 0 rows (no invalid JSON)

---

## 🚀 Step 2: Apply Migration

### 2.1 Create Database Backup

**CRITICAL:** Always backup before schema changes!

```bash
# Option A: Supabase Dashboard Backup
# 1. Go to Supabase Dashboard → Database → Backups
# 2. Click "Create Backup" → Name: "pre-phase16-migration"
# 3. Wait for completion and verify success

# Option B: Manual pg_dump Backup
pg_dump "$DATABASE_URL" > backup_pre_phase16_$(date +%Y%m%d_%H%M%S).sql
```

### 2.2 Set Environment Variables

```bash
# Export production DATABASE_URL
export DATABASE_URL="postgresql://postgres.xxx:password@aws-1-ca-central-1.pooler.supabase.com:6543/postgres"

# Verify it's set correctly
echo $DATABASE_URL | grep -o "pooler.supabase.com"
```

### 2.3 Run the Migration

```bash
# Apply migration 0003
alembic upgrade head

# Monitor output for errors
# Expected: Progress messages showing each table conversion
# Duration: 2-5 minutes for typical datasets
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 0002 -> 0003, Implement JSONB and TSVECTOR for performance
================================================================================
Phase 16: Upgrading Text columns to JSONB and TSVECTOR
================================================================================

PART 1: Converting 'attributes' columns to JSONB...
--------------------------------------------------------------------------------
  → projects.attributes: Text → JSONB
  → survey_points.attributes: Text → JSONB
  → easements.attributes: Text → JSONB
  → block_definitions.attributes: Text → JSONB
  → attribute_codes.attributes: Text → JSONB
  → entity_relationships.attributes: Text → JSONB
  → horizontal_alignments.attributes: Text → JSONB
  → drawing_hatches.attributes: Text → JSONB
  ✓ All 'attributes' columns converted to JSONB

PART 2: Converting audit_log columns to JSONB...
--------------------------------------------------------------------------------
  → audit_log.old_values: Text → JSONB
  → audit_log.new_values: Text → JSONB
  ✓ Audit log columns converted to JSONB

PART 3: Converting ai_query_cache.result_data to JSONB...
--------------------------------------------------------------------------------
  → ai_query_cache.result_data: Text → JSONB
  ✓ AI query cache column converted to JSONB

PART 4: Converting 'search_vector' columns to TSVECTOR...
--------------------------------------------------------------------------------
  → projects.search_vector: Text → TSVECTOR
  → survey_points.search_vector: Text → TSVECTOR
  → easements.search_vector: Text → TSVECTOR
  → block_definitions.search_vector: Text → TSVECTOR
  → horizontal_alignments.search_vector: Text → TSVECTOR
  → drawing_hatches.search_vector: Text → TSVECTOR
  ✓ All 'search_vector' columns converted to TSVECTOR

================================================================================
✓ Phase 16 Migration Completed Successfully!
================================================================================

SUMMARY:
  • 8 tables: attributes → JSONB
  • 6 tables: search_vector → TSVECTOR
  • 2 audit_log columns → JSONB
  • 1 ai_query_cache column → JSONB
  • TOTAL: 17 columns upgraded
```

---

## ✅ Step 3: Post-Migration Verification

### 3.1 Verify Migration Applied

```bash
# Check current migration state
alembic current
```

**Expected Output:**
```
0003 (head), Implement JSONB and TSVECTOR for performance
```

### 3.2 Verify Column Types

Run these queries to confirm type changes:

```sql
-- Verify JSONB columns
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name IN ('projects', 'survey_points', 'easements',
                     'block_definitions', 'attribute_codes',
                     'entity_relationships', 'horizontal_alignments',
                     'drawing_hatches', 'audit_log', 'ai_query_cache')
  AND column_name IN ('attributes', 'old_values', 'new_values', 'result_data')
ORDER BY table_name, column_name;
```

**Expected Output:** All should show `data_type = 'jsonb'`

```sql
-- Verify TSVECTOR columns
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name IN ('projects', 'survey_points', 'easements',
                     'block_definitions', 'horizontal_alignments',
                     'drawing_hatches')
  AND column_name = 'search_vector'
ORDER BY table_name;
```

**Expected Output:** All should show `data_type = 'tsvector'`

### 3.3 Test JSONB Functionality

```sql
-- Test JSONB querying on projects table
SELECT
    project_id,
    project_name,
    attributes,
    attributes->>'custom_field' as custom_field_value
FROM projects
WHERE attributes IS NOT NULL
LIMIT 5;

-- Test JSONB operators work
SELECT COUNT(*)
FROM projects
WHERE attributes ? 'some_key';  -- Check if key exists
```

### 3.4 Test TSVECTOR Functionality

```sql
-- Test TSVECTOR on projects table
SELECT
    project_id,
    project_name,
    search_vector
FROM projects
WHERE search_vector IS NOT NULL
LIMIT 5;

-- Test full-text search works (if search vectors populated)
SELECT project_id, project_name
FROM projects
WHERE search_vector @@ to_tsquery('english', 'project');
```

### 3.5 Verify Data Integrity

```sql
-- Count records before/after (should be identical)
SELECT
    'projects' as table_name,
    COUNT(*) as row_count
FROM projects
UNION ALL
SELECT 'survey_points', COUNT(*) FROM survey_points
UNION ALL
SELECT 'easements', COUNT(*) FROM easements;

-- Compare with pre-migration counts
```

---

## 🔄 Step 4: Rollback Procedure (If Needed)

If migration fails or issues are discovered:

### 4.1 Immediate Rollback

```bash
# Downgrade to previous migration
alembic downgrade 0002

# Monitor output for errors
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Running downgrade 0003 -> 0002, Implement JSONB and TSVECTOR for performance
================================================================================
ROLLING BACK: Converting JSONB/TSVECTOR to Text
================================================================================
⚠ WARNING: This will convert specialized types back to plain Text
⚠ WARNING: You will lose JSONB querying and native FTS capabilities
...
✓ Migration Rolled Back Successfully
```

### 4.2 Verify Rollback

```bash
# Check migration state
alembic current
```

**Expected:** `0002 (head), add_project_archiving`

### 4.3 Restore from Backup (If Rollback Fails)

```bash
# Option A: Supabase Dashboard Restore
# 1. Go to Supabase Dashboard → Database → Backups
# 2. Find "pre-phase16-migration" backup
# 3. Click "Restore" and confirm

# Option B: Manual Restore
psql "$DATABASE_URL" < backup_pre_phase16_YYYYMMDD_HHMMSS.sql
```

---

## 🚨 Emergency Procedures

### Database Not Stamped

If `alembic current` returns nothing:

```bash
# Stamp database to current state (DO NOT upgrade yet)
alembic stamp 0002

# Verify
alembic current
# Should now show: 0002 (head)

# Then proceed with Step 2
```

### Migration Fails with "invalid input syntax for type json"

This means you have non-JSON text in an `attributes` column.

**Solution:**
1. Identify the problematic rows (see Step 1.3)
2. Clean the data:
   ```sql
   -- Option A: Convert to NULL
   UPDATE projects SET attributes = NULL WHERE attributes = '';

   -- Option B: Convert to empty JSON object
   UPDATE projects SET attributes = '{}' WHERE attributes = '';
   ```
3. Re-run migration

### Connection Lost During Migration

PostgreSQL uses transactional DDL, so:
- If connection lost → Migration **automatically rolled back**
- Check `alembic current` to verify state
- Review database for any partial changes
- If needed, use rollback procedure

---

## 📊 Migration Impact Summary

| Metric | Value |
|--------|-------|
| **Tables Modified** | 10 tables |
| **Columns Upgraded** | 17 columns |
| **Downtime Required** | Minimal (schema-only changes) |
| **Data Loss Risk** | None (if data validated) |
| **Reversible** | Yes (full downgrade support) |
| **Production Ready** | ✅ Yes |

---

## 🎯 Post-Migration Optimization (Optional)

After migration succeeds, consider these optimizations:

### Add GIN Indexes for JSONB Performance

```sql
-- Index for JSONB queries on projects
CREATE INDEX idx_projects_attributes_gin ON projects USING gin(attributes);

-- Index for JSONB queries on survey_points
CREATE INDEX idx_survey_points_attributes_gin ON survey_points USING gin(attributes);

-- Repeat for other tables as needed
```

### Populate Search Vectors

If `search_vector` columns are NULL, populate them:

```sql
-- Example: Generate search vectors for projects
UPDATE projects SET search_vector =
    to_tsvector('english',
        coalesce(project_name, '') || ' ' ||
        coalesce(project_number, '') || ' ' ||
        coalesce(description, '')
    )
WHERE search_vector IS NULL;
```

---

## 📞 Support Contacts

| Issue Type | Contact | Action |
|------------|---------|--------|
| **Migration Fails** | Review error logs | Check Step 4 (Rollback) |
| **Data Issues** | Run validation queries | See Step 3.5 |
| **Connection Problems** | Check DATABASE_URL | See Step 1.1 |
| **Emergency Rollback** | Run downgrade | See Step 4 |

---

## ✅ Completion Checklist

After successful migration:

- [ ] Migration applied successfully (`alembic current` shows `0003`)
- [ ] All column types verified (Step 3.2)
- [ ] JSONB querying tested (Step 3.3)
- [ ] TSVECTOR functionality tested (Step 3.4)
- [ ] Data integrity verified (Step 3.5)
- [ ] Application tested against new schema
- [ ] Backup retained for 30 days
- [ ] Team notified of completion
- [ ] Documentation updated
- [ ] Monitoring enabled for performance metrics

---

## 📝 Notes

**Created:** 2025-11-18
**Migration ID:** 0003
**Phase:** 16
**Status:** ✅ READY FOR PRODUCTION

**Last Updated:** 2025-11-18 22:30:00 UTC
