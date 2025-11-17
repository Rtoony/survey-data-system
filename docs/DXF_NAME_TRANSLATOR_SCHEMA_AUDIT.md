# DXF Name Translator - Database Schema Audit

**Date:** 2025-11-17 | **Phase:** 2A - Step 4

## Executive Summary

The `import_mapping_patterns` table has a **minimal viable schema** suitable for proof-of-concept but **missing critical columns** needed for production use: versioning, provenance, status lifecycle, performance metrics, and audit trails.

---

## 1. Current Schema (Inferred from Code)

```sql
CREATE TABLE import_mapping_patterns (
    -- Primary Key
    mapping_id SERIAL PRIMARY KEY,

    -- Pattern Definition
    client_name VARCHAR(255),
    source_pattern TEXT,          -- Human-readable pattern description
    regex_pattern TEXT NOT NULL,  -- Python regex with named groups
    extraction_rules JSONB,       -- JSON mapping rules

    -- Target Components (Foreign Keys)
    target_discipline_id INTEGER REFERENCES discipline_codes(discipline_id),
    target_category_id INTEGER REFERENCES category_codes(category_id),
    target_type_id INTEGER REFERENCES object_type_codes(type_id),

    -- Metadata
    confidence_score INTEGER DEFAULT 80,  -- 0-100 scale
    is_active BOOLEAN DEFAULT TRUE

    -- MISSING: timestamps, user tracking, versioning, status, metrics
);
```

### Indexes (Assumed Missing)

```sql
-- Recommended indexes (likely don't exist)
CREATE INDEX idx_import_mapping_is_active ON import_mapping_patterns(is_active);
CREATE INDEX idx_import_mapping_confidence ON import_mapping_patterns(confidence_score DESC);
CREATE INDEX idx_import_mapping_client ON import_mapping_patterns(client_name);
CREATE INDEX idx_import_mapping_discipline ON import_mapping_patterns(target_discipline_id);
```

---

## 2. Missing Columns for Production

### Critical Missing Fields

```sql
ALTER TABLE import_mapping_patterns ADD COLUMN:

-- Provenance Tracking
created_by VARCHAR(255),                    -- User who created pattern
created_at TIMESTAMP DEFAULT NOW(),
modified_by VARCHAR(255),                   -- User who last edited
modified_at TIMESTAMP,

-- Versioning
version INTEGER DEFAULT 1,                  -- Pattern version number
previous_version_id INTEGER REFERENCES import_mapping_patterns(mapping_id),

-- Status Lifecycle
status VARCHAR(20) DEFAULT 'draft',         -- draft/pending/approved/active/deprecated
approved_by VARCHAR(255),                   -- Who approved for production
approved_at TIMESTAMP,
deprecated_at TIMESTAMP,
deprecated_reason TEXT,

-- Usage Metrics
usage_count INTEGER DEFAULT 0,              -- Times pattern matched in imports
last_used_at TIMESTAMP,                     -- Last time pattern matched
success_rate DECIMAL(5,2),                  -- Percentage of matches not overridden
avg_confidence DECIMAL(5,2),                -- Actual match confidence average

-- Validation Results
entity_registry_valid BOOLEAN,              -- Passes entity validation?
vocabulary_compliant BOOLEAN,               -- Passes vocabulary validation?
last_validated_at TIMESTAMP,

-- Conflict Detection
conflicts_with INTEGER[],                   -- Array of pattern IDs that overlap
conflict_resolution_priority INTEGER,       -- Manual priority override

-- Pattern Quality
specificity_score DECIMAL(3,2),             -- How specific vs broad is pattern
test_coverage_count INTEGER DEFAULT 0,      -- Number of test cases for this pattern

-- Notes
description TEXT,                           -- Longer description of pattern purpose
tags TEXT[],                                -- Searchable tags (e.g., ["storm", "sanitary"])
notes TEXT                                  -- Admin notes
```

---

## 3. Proposed Supporting Tables

### 3.1 Pattern Version History

```sql
CREATE TABLE import_mapping_pattern_history (
    history_id SERIAL PRIMARY KEY,
    mapping_id INTEGER REFERENCES import_mapping_patterns(mapping_id),
    version INTEGER NOT NULL,

    -- Snapshot of pattern at this version
    client_name VARCHAR(255),
    source_pattern TEXT,
    regex_pattern TEXT,
    extraction_rules JSONB,
    confidence_score INTEGER,

    -- Change tracking
    changed_by VARCHAR(255),
    changed_at TIMESTAMP DEFAULT NOW(),
    change_reason TEXT,

    UNIQUE(mapping_id, version)
);
```

### 3.2 Pattern Match History

```sql
CREATE TABLE import_mapping_match_history (
    match_id SERIAL PRIMARY KEY,
    mapping_id INTEGER REFERENCES import_mapping_patterns(mapping_id),
    import_session_id UUID,                  -- Link to DXF import session

    -- Input/Output
    dxf_layer_name VARCHAR(255),
    canonical_layer_name VARCHAR(255),
    confidence DECIMAL(3,2),

    -- Validation
    entity_valid BOOLEAN,
    vocabulary_valid BOOLEAN,

    -- User Action
    user_accepted BOOLEAN,                   -- Did user accept translation?
    user_override VARCHAR(255),              -- If rejected, what did user use instead?

    -- Metadata
    matched_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_match_history_mapping ON import_mapping_match_history(mapping_id);
CREATE INDEX idx_match_history_session ON import_mapping_match_history(import_session_id);
```

### 3.3 Pattern Test Cases

```sql
CREATE TABLE import_mapping_test_cases (
    test_case_id SERIAL PRIMARY KEY,
    mapping_id INTEGER REFERENCES import_mapping_patterns(mapping_id),

    -- Test Input
    test_layer_name VARCHAR(255) NOT NULL,

    -- Expected Output
    expected_discipline VARCHAR(50),
    expected_category VARCHAR(50),
    expected_type VARCHAR(50),
    expected_attributes TEXT[],
    expected_phase VARCHAR(50),
    expected_geometry VARCHAR(50),

    -- Test Metadata
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);
```

### 3.4 Pattern Conflicts

```sql
CREATE TABLE import_mapping_conflicts (
    conflict_id SERIAL PRIMARY KEY,
    pattern_1_id INTEGER REFERENCES import_mapping_patterns(mapping_id),
    pattern_2_id INTEGER REFERENCES import_mapping_patterns(mapping_id),

    -- Conflict Details
    conflict_type VARCHAR(50),               -- 'regex_overlap', 'ambiguous_match', etc.
    sample_input VARCHAR(255),               -- Example layer name that matches both
    detected_at TIMESTAMP DEFAULT NOW(),

    -- Resolution
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by VARCHAR(255),
    resolved_at TIMESTAMP,
    resolution_action TEXT,                  -- How was conflict resolved

    CHECK (pattern_1_id < pattern_2_id)      -- Prevent duplicate entries
);
```

### 3.5 Pattern Analytics Summary

```sql
CREATE TABLE import_mapping_analytics (
    analytics_id SERIAL PRIMARY KEY,
    mapping_id INTEGER REFERENCES import_mapping_patterns(mapping_id),
    period_start DATE,
    period_end DATE,

    -- Usage Stats
    total_matches INTEGER DEFAULT 0,
    successful_matches INTEGER DEFAULT 0,
    user_overrides INTEGER DEFAULT 0,
    avg_confidence DECIMAL(5,2),

    -- Performance
    avg_match_time_ms DECIMAL(8,2),

    UNIQUE(mapping_id, period_start, period_end)
);
```

---

## 4. Enhanced Schema Proposal

```sql
-- Complete enhanced table definition
CREATE TABLE import_mapping_patterns_v2 (
    -- Primary Key
    mapping_id SERIAL PRIMARY KEY,

    -- Pattern Definition
    client_name VARCHAR(255),
    source_pattern TEXT NOT NULL,
    regex_pattern TEXT NOT NULL,
    extraction_rules JSONB NOT NULL,
    description TEXT,

    -- Target Components
    target_discipline_id INTEGER REFERENCES discipline_codes(discipline_id),
    target_category_id INTEGER REFERENCES category_codes(category_id),
    target_type_id INTEGER REFERENCES object_type_codes(type_id),

    -- Confidence & Quality
    confidence_score INTEGER DEFAULT 80 CHECK (confidence_score BETWEEN 0 AND 100),
    specificity_score DECIMAL(3,2) CHECK (specificity_score BETWEEN 0 AND 1),

    -- Lifecycle Management
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'pending', 'approved', 'active', 'deprecated')),
    is_active BOOLEAN DEFAULT TRUE,

    -- Provenance
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    modified_by VARCHAR(255),
    modified_at TIMESTAMP,

    -- Approval
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,

    -- Deprecation
    deprecated_at TIMESTAMP,
    deprecated_reason TEXT,
    superseded_by INTEGER REFERENCES import_mapping_patterns_v2(mapping_id),

    -- Versioning
    version INTEGER DEFAULT 1,
    previous_version_id INTEGER REFERENCES import_mapping_patterns_v2(mapping_id),

    -- Validation
    entity_registry_valid BOOLEAN,
    vocabulary_compliant BOOLEAN,
    last_validated_at TIMESTAMP,

    -- Usage Metrics (cached)
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    success_rate DECIMAL(5,2),

    -- Conflict Management
    conflict_resolution_priority INTEGER,

    -- Searchability
    tags TEXT[],
    notes TEXT,

    -- Ensure valid lifecycle transitions
    CHECK (
        (status = 'active' AND is_active = TRUE) OR
        (status != 'active')
    )
);

-- Indexes for Performance
CREATE INDEX idx_mapping_v2_status ON import_mapping_patterns_v2(status);
CREATE INDEX idx_mapping_v2_active ON import_mapping_patterns_v2(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_mapping_v2_client ON import_mapping_patterns_v2(client_name);
CREATE INDEX idx_mapping_v2_confidence ON import_mapping_patterns_v2(confidence_score DESC);
CREATE INDEX idx_mapping_v2_discipline ON import_mapping_patterns_v2(target_discipline_id);
CREATE INDEX idx_mapping_v2_tags ON import_mapping_patterns_v2 USING GIN(tags);
CREATE INDEX idx_mapping_v2_created_at ON import_mapping_patterns_v2(created_at DESC);
CREATE INDEX idx_mapping_v2_last_used ON import_mapping_patterns_v2(last_used_at DESC) WHERE last_used_at IS NOT NULL;
```

---

## 5. Migration Strategy

### Phase 1: Add Critical Columns

```sql
-- Add provenance and timestamps first (non-breaking)
ALTER TABLE import_mapping_patterns
    ADD COLUMN created_by VARCHAR(255),
    ADD COLUMN created_at TIMESTAMP DEFAULT NOW(),
    ADD COLUMN modified_by VARCHAR(255),
    ADD COLUMN modified_at TIMESTAMP;

-- Backfill with system user
UPDATE import_mapping_patterns
SET created_by = 'system', created_at = NOW()
WHERE created_by IS NULL;
```

### Phase 2: Add Status and Lifecycle

```sql
ALTER TABLE import_mapping_patterns
    ADD COLUMN status VARCHAR(20) DEFAULT 'active',
    ADD COLUMN version INTEGER DEFAULT 1,
    ADD COLUMN approved_by VARCHAR(255),
    ADD COLUMN approved_at TIMESTAMP;

-- Mark all existing patterns as approved
UPDATE import_mapping_patterns
SET status = 'approved', approved_at = NOW(), approved_by = 'migration'
WHERE is_active = TRUE;
```

### Phase 3: Create Supporting Tables

```sql
-- Create history, match tracking, test cases, conflicts, analytics tables
-- (See section 3 above)
```

### Phase 4: Add Performance Indexes

```sql
-- Add all recommended indexes
```

---

## 6. Recommendations

### Immediate (Zero Downtime)

1. **Add Timestamps and Provenance**
   - created_by, created_at, modified_by, modified_at
   - Backfill existing records

2. **Add Basic Indexes**
   - is_active, confidence_score, client_name

### Short Term

3. **Add Status and Versioning**
   - status column with draft/approved/active/deprecated
   - version column for tracking changes

4. **Create Match History Table**
   - Track every pattern match during imports
   - Enable analytics and feedback loop

### Medium Term

5. **Create Supporting Tables**
   - Pattern history
   - Test cases
   - Conflicts
   - Analytics

6. **Implement Full Schema Migration**
   - Migrate to import_mapping_patterns_v2
   - Deprecate old table

---

**Next:** Redesign Proposal
