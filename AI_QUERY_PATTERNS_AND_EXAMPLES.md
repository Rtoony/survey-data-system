# ACAD-GIS AI Query Patterns & Examples

## Overview

This document provides practical examples of AI-powered queries in the ACAD-GIS system, demonstrating how vector embeddings, GraphRAG, spatial operations, and quality scoring work together to enable intelligent CAD/GIS analysis.

---

## Query Categories

1. **Semantic Search** - Find entities by meaning, not just keywords
2. **Hybrid Search** - Combine text, vector, spatial, and quality filters
3. **GraphRAG Multi-Hop** - Follow relationships to find connected entities
4. **Spatial-Semantic Fusion** - Merge location and meaning
5. **Quality-Weighted Queries** - Prioritize high-quality data
6. **Predictive Analytics** - Use ML features for predictions

---

## Part 1: Semantic Search

### Example 1: Find Water Collection Structures

**User Query:** "Show me all water collection structures"

**Traditional Approach (Keyword Matching):**
```sql
-- PROBLEM: Misses synonyms and related concepts
SELECT * FROM utility_structures
WHERE structure_type ILIKE '%water%'
   OR description ILIKE '%collection%';
```

**Limitations:**
- Misses "catch basin" (doesn't contain "water")
- Misses "storm drain inlet" (doesn't contain "collection")
- Misses "culvert" (conceptually related, but no keyword overlap)

**AI Approach (Semantic Search):**
```sql
-- Generate embedding for search query
-- embedding = get_embedding("water collection structures")

SELECT 
    se.entity_id,
    se.entity_name,
    se.entity_type,
    1 - (ee.embedding <=> query_embedding::vector) AS similarity
FROM entity_embeddings ee
JOIN standards_entities se ON ee.entity_id = se.entity_id
WHERE 1 - (ee.embedding <=> query_embedding::vector) > 0.75
ORDER BY ee.embedding <=> query_embedding::vector
LIMIT 20;
```

**Result:**
```
entity_name                 | entity_type        | similarity
----------------------------|--------------------|-----------
Storm Drain Inlet Type A    | block_definition   | 0.89
Catch Basin CB-1            | utility_structure  | 0.87
Street Inlet                | block_definition   | 0.86
Curb Inlet Type 3           | utility_structure  | 0.84
Culvert 24" RCP             | utility_line       | 0.81
Area Drain AD-2             | utility_structure  | 0.78
```

**Why It Works:** Embeddings capture semantic meaning, so "catch basin" and "inlet" are mathematically similar to "water collection" even though they use different words.

---

### Example 2: Find Maintenance-Related Items

**User Query:** "Find infrastructure that needs maintenance"

**AI Query:**
```sql
WITH maintenance_embedding AS (
    SELECT get_embedding(
        'needs maintenance repair replacement inspection cleaning'
    )::vector AS embedding
)
SELECT 
    se.entity_name,
    se.entity_type,
    us.condition_rating,
    us.install_date,
    1 - (ee.embedding <=> me.embedding) AS relevance
FROM entity_embeddings ee
JOIN standards_entities se ON ee.entity_id = se.entity_id
LEFT JOIN utility_structures us ON se.entity_id = us.entity_id
CROSS JOIN maintenance_embedding me
WHERE 1 - (ee.embedding <=> me.embedding) > 0.70
ORDER BY relevance DESC
LIMIT 50;
```

**Result:** Finds items with descriptions like:
- "Requires annual cleaning"
- "Schedule for replacement"
- "Inspection due"
- "Deteriorated condition"

---

## Part 2: Hybrid Search

### Example 3: Find High-Quality Storm Drainage Near City Hall

**User Query:** "Show me storm drainage infrastructure within 500 feet of City Hall with good data quality"

**Full-Stack Hybrid Query:**
```sql
WITH city_hall AS (
    -- Step 1: Find City Hall using semantic search
    SELECT 
        geometry,
        1 - (ee.embedding <=> get_embedding('city hall building')::vector) AS similarity
    FROM entity_embeddings ee
    JOIN standards_entities se ON ee.entity_id = se.entity_id
    JOIN parcels p ON se.entity_id = p.entity_id
    WHERE 1 - (ee.embedding <=> get_embedding('city hall building')::vector) > 0.85
    ORDER BY similarity DESC
    LIMIT 1
),
storm_drainage AS (
    -- Step 2: Find storm drainage entities (semantic)
    SELECT entity_id
    FROM entity_embeddings ee
    WHERE 1 - (ee.embedding <=> get_embedding('storm drainage stormwater')::vector) > 0.80
),
nearby AS (
    -- Step 3: Spatial filter (within 500 feet)
    SELECT 
        ul.line_id,
        ul.entity_id,
        ST_Distance(ch.geometry, ul.geometry) AS distance_ft
    FROM utility_lines ul
    CROSS JOIN city_hall ch
    WHERE ST_DWithin(ch.geometry, ul.geometry, 500)
)
-- Step 4: Combine semantic + spatial + quality
SELECT 
    se.entity_name,
    ul.line_type,
    ul.diameter,
    ul.material,
    n.distance_ft,
    se.quality_score,
    1 - (ee.embedding <=> get_embedding('storm drainage stormwater')::vector) AS semantic_relevance
FROM nearby n
JOIN utility_lines ul ON n.line_id = ul.line_id
JOIN standards_entities se ON ul.entity_id = se.entity_id
JOIN entity_embeddings ee ON se.entity_id = ee.entity_id
WHERE se.quality_score > 0.7  -- High quality data only
  AND ul.entity_id IN (SELECT entity_id FROM storm_drainage)
ORDER BY n.distance_ft, se.quality_score DESC;
```

**Result:**
```
entity_name          | line_type    | diameter | distance_ft | quality_score | semantic_relevance
---------------------|--------------|----------|-------------|---------------|-------------------
Storm Pipe SP-101    | storm_drain  | 18.0     | 147.3       | 0.92          | 0.91
Storm Main SM-45     | storm_drain  | 24.0     | 203.8       | 0.88          | 0.89
Storm Lateral SL-12  | storm_drain  | 12.0     | 387.5       | 0.85          | 0.87
```

**What Makes This Hybrid:**
1. ✅ **Semantic:** "storm drainage" matches related concepts
2. ✅ **Spatial:** Within 500 feet (PostGIS)
3. ✅ **Quality:** Only high-quality records (quality_score > 0.7)
4. ✅ **Text:** Filtered by entity type (utility_lines)

---

## Part 3: GraphRAG Multi-Hop Queries

### Example 4: Find Everything Connected to a Survey Point

**User Query:** "Show me everything related to survey point SP-101, up to 2 hops away"

**GraphRAG Function:**
```sql
CREATE OR REPLACE FUNCTION find_related_entities(
    start_entity_id UUID,
    max_hops INTEGER DEFAULT 2,
    relationship_types TEXT[] DEFAULT NULL
)
RETURNS TABLE(
    entity_id UUID,
    entity_name VARCHAR,
    entity_type VARCHAR,
    hop_count INTEGER,
    relationship_path TEXT,
    total_strength NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE entity_graph AS (
        -- Base case: Direct relationships
        SELECT 
            er.target_entity_id AS entity_id,
            1 AS hops,
            ARRAY[er.relationship_type] AS path,
            er.relationship_strength AS strength
        FROM entity_relationships er
        WHERE er.source_entity_id = start_entity_id
          AND (relationship_types IS NULL OR er.relationship_type = ANY(relationship_types))
        
        UNION ALL
        
        -- Recursive case: Follow relationships
        SELECT 
            er.target_entity_id,
            eg.hops + 1,
            eg.path || er.relationship_type,
            eg.strength * er.relationship_strength
        FROM entity_relationships er
        JOIN entity_graph eg ON er.source_entity_id = eg.entity_id
        WHERE eg.hops < max_hops
          AND (relationship_types IS NULL OR er.relationship_type = ANY(relationship_types))
          AND NOT (er.target_entity_id = start_entity_id)  -- Prevent cycles
    )
    SELECT 
        eg.entity_id,
        se.entity_name,
        se.entity_type,
        eg.hops,
        array_to_string(eg.path, ' → ') AS relationship_path,
        eg.strength
    FROM entity_graph eg
    JOIN standards_entities se ON eg.entity_id = se.entity_id
    ORDER BY eg.hops, eg.strength DESC;
END;
$$ LANGUAGE plpgsql;
```

**Usage:**
```sql
-- Find entities related to survey point SP-101
SELECT * FROM find_related_entities(
    'survey-point-sp-101-uuid',
    max_hops => 2,
    relationship_types => ARRAY['spatial', 'engineering']
);
```

**Result:**
```
entity_name              | entity_type       | hop_count | relationship_path         | total_strength
-------------------------|-------------------|-----------|---------------------------|---------------
Parcel 123-456-789       | parcel            | 1         | spatial                   | 0.95
Water Main WM-12         | utility_line      | 1         | spatial                   | 0.87
Manhole MH-45            | utility_structure | 2         | spatial → engineering     | 0.74
Fire Hydrant FH-8        | utility_structure | 2         | spatial → engineering     | 0.68
```

---

### Example 5: Infrastructure Dependency Analysis

**User Query:** "If we close water main WM-12 for repairs, what gets affected?"

**Multi-Hop GraphRAG Query:**
```sql
WITH RECURSIVE dependent_infrastructure AS (
    -- Base case: Direct connections to WM-12
    SELECT 
        er.target_entity_id AS entity_id,
        1 AS dependency_level,
        ARRAY[er.target_entity_id] AS dependency_chain
    FROM entity_relationships er
    WHERE er.source_entity_id = 'water-main-wm-12-uuid'
      AND er.relationship_type IN ('engineering', 'spatial')
    
    UNION ALL
    
    -- Recursive case: Find downstream dependencies
    SELECT 
        er.target_entity_id,
        di.dependency_level + 1,
        di.dependency_chain || er.target_entity_id
    FROM entity_relationships er
    JOIN dependent_infrastructure di ON er.source_entity_id = di.entity_id
    WHERE di.dependency_level < 5
      AND NOT (er.target_entity_id = ANY(di.dependency_chain))  -- Prevent loops
)
SELECT 
    se.entity_name,
    se.entity_type,
    di.dependency_level,
    COUNT(*) OVER (PARTITION BY di.dependency_level) AS entities_at_level
FROM dependent_infrastructure di
JOIN standards_entities se ON di.entity_id = se.entity_id
ORDER BY di.dependency_level, se.entity_name;
```

**Result:**
```
entity_name              | entity_type       | dependency_level | entities_at_level
-------------------------|-------------------|------------------|------------------
Fire Hydrant FH-8        | utility_structure | 1                | 3
Service Connection SC-45 | utility_line      | 1                | 3
Valve V-23               | utility_device    | 1                | 3
Building 123 Main St     | parcel            | 2                | 12
Hospital East Wing       | parcel            | 2                | 12
```

**Use Case:** Identify critical infrastructure and plan maintenance schedules to minimize disruption.

---

## Part 4: Spatial-Semantic Fusion

### Example 6: Find Bioretention BMPs in Residential Areas

**User Query:** "Show me bioretention basins located in residential neighborhoods"

**Fusion Query:**
```sql
WITH residential_areas AS (
    -- Semantic search for residential parcels
    SELECT 
        p.parcel_id,
        p.geometry,
        1 - (ee.embedding <=> get_embedding('residential neighborhood housing')::vector) AS relevance
    FROM parcels p
    JOIN entity_embeddings ee ON p.entity_id = ee.entity_id
    WHERE 1 - (ee.embedding <=> get_embedding('residential neighborhood housing')::vector) > 0.75
),
bioretention AS (
    -- Semantic search for bioretention BMPs
    SELECT 
        b.bmp_id,
        b.entity_id,
        b.geometry,
        1 - (ee.embedding <=> get_embedding('bioretention basin rain garden')::vector) AS relevance
    FROM bmps b
    JOIN entity_embeddings ee ON b.entity_id = ee.entity_id
    WHERE 1 - (ee.embedding <=> get_embedding('bioretention basin rain garden')::vector) > 0.80
)
-- Spatial intersection
SELECT 
    se.entity_name,
    br.bmp_id,
    ST_Area(ST_Intersection(br.geometry, ra.geometry)) AS overlap_sqft,
    br.relevance AS bmp_relevance,
    ra.relevance AS area_relevance
FROM bioretention br
JOIN residential_areas ra ON ST_Intersects(br.geometry, ra.geometry)
JOIN standards_entities se ON br.entity_id = se.entity_id
WHERE ST_Area(ST_Intersection(br.geometry, ra.geometry)) > 100
ORDER BY overlap_sqft DESC;
```

**Why It's Powerful:**
- **Semantic:** Finds "rain garden" even though user said "bioretention"
- **Semantic:** Identifies residential areas even if zoning code doesn't say "residential"
- **Spatial:** Ensures BMPs are actually located within those areas

---

## Part 5: Quality-Weighted Queries

### Example 7: Best Data for Client Deliverable

**User Query:** "Get the highest quality survey points for exporting to client"

**Quality-Weighted Query:**
```sql
SELECT 
    sp.point_number,
    sp.point_type,
    ST_X(sp.geometry) AS x,
    ST_Y(sp.geometry) AS y,
    ST_Z(sp.geometry) AS z,
    se.quality_score,
    sp.horizontal_accuracy,
    sp.vertical_accuracy,
    -- Quality breakdown
    CASE 
        WHEN EXISTS(SELECT 1 FROM entity_embeddings WHERE entity_id = se.entity_id) 
        THEN '✅' ELSE '❌' 
    END AS has_embedding,
    CASE 
        WHEN (SELECT COUNT(*) FROM entity_relationships 
              WHERE source_entity_id = se.entity_id OR target_entity_id = se.entity_id) > 0
        THEN '✅' ELSE '❌' 
    END AS has_relationships
FROM survey_points sp
JOIN standards_entities se ON sp.entity_id = se.entity_id
WHERE sp.project_id = 'project-uuid'
  AND se.quality_score >= 0.80  -- High quality threshold
  AND sp.horizontal_accuracy <= 0.05  -- 0.05 feet accuracy
ORDER BY se.quality_score DESC, sp.horizontal_accuracy ASC
LIMIT 500;
```

**Quality Score Factors:**
1. Has vector embedding (+0.3)
2. Has spatial geometry (+0.2)
3. Has relationships (+0.3, scaled by count)
4. Usage frequency (+0.2, scaled)

---

## Part 6: Predictive Analytics

### Example 8: Predict Infrastructure Failure Risk

**Use Case:** ML model trained on historical data predicts which pipes are at risk.

**Feature Extraction Query:**
```sql
SELECT 
    ul.line_id,
    ul.entity_id,
    
    -- Age features
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, ul.install_date)) AS age_years,
    
    -- Physical features
    ul.diameter,
    ul.material,
    ul.slope,
    ST_Length(ul.geometry) AS length_ft,
    
    -- Semantic features (from embeddings)
    1 - (ee.embedding <=> get_embedding('critical high priority')::vector) AS criticality_score,
    
    -- Network features (from relationships)
    (SELECT COUNT(*) 
     FROM entity_relationships er 
     WHERE er.source_entity_id = ul.entity_id) AS outbound_connections,
    (SELECT COUNT(*) 
     FROM entity_relationships er 
     WHERE er.target_entity_id = ul.entity_id) AS inbound_connections,
    
    -- Maintenance history
    (SELECT COUNT(*) 
     FROM maintenance_records mr 
     WHERE mr.entity_id = ul.entity_id) AS past_maintenance_count,
    (SELECT AVG(cost) 
     FROM maintenance_records mr 
     WHERE mr.entity_id = ul.entity_id) AS avg_repair_cost,
    
    -- Spatial density
    (SELECT COUNT(*) 
     FROM utility_lines ul2 
     WHERE ST_DWithin(ul.geometry, ul2.geometry, 100)) AS nearby_pipe_count,
    
    -- Condition rating (target variable for training)
    ul.condition_rating
FROM utility_lines ul
JOIN entity_embeddings ee ON ul.entity_id = ee.entity_id
WHERE ul.project_id = 'project-uuid';
```

**ML Pipeline:**
1. Extract features (query above)
2. Train model (Python scikit-learn, XGBoost)
3. Store predictions in database
4. Use predictions in queries

**Prediction Query:**
```sql
SELECT 
    se.entity_name,
    ul.line_type,
    mp.failure_probability,
    mp.confidence_score,
    mp.top_contributing_factors
FROM ml_predictions mp
JOIN utility_lines ul ON mp.entity_id = ul.entity_id
JOIN standards_entities se ON ul.entity_id = se.entity_id
WHERE mp.model_id = 'pipe-failure-model-v2'
  AND mp.failure_probability > 0.75
ORDER BY mp.failure_probability DESC;
```

---

## Part 7: Natural Language to SQL Translation

### Example 9: LLM-Powered Query Interface

**User Input (Natural Language):** "Find all fire hydrants within 1000 feet of schools that need inspection"

**LLM Translation Process:**
1. Identify entities: fire hydrants, schools
2. Identify spatial relationship: within 1000 feet
3. Identify filter: needs inspection
4. Generate SQL

**Generated Query:**
```sql
WITH schools AS (
    SELECT 
        p.parcel_id,
        p.geometry,
        1 - (ee.embedding <=> get_embedding('school elementary middle high education')::vector) AS relevance
    FROM parcels p
    JOIN entity_embeddings ee ON p.entity_id = ee.entity_id
    WHERE 1 - (ee.embedding <=> get_embedding('school elementary middle high education')::vector) > 0.85
),
fire_hydrants AS (
    SELECT 
        us.structure_id,
        us.entity_id,
        us.geometry,
        1 - (ee.embedding <=> get_embedding('fire hydrant')::vector) AS relevance
    FROM utility_structures us
    JOIN entity_embeddings ee ON us.entity_id = ee.entity_id
    WHERE 1 - (ee.embedding <=> get_embedding('fire hydrant')::vector) > 0.85
),
needs_inspection AS (
    SELECT entity_id
    FROM entity_embeddings ee
    WHERE 1 - (ee.embedding <=> get_embedding('needs inspection maintenance due')::vector) > 0.75
)
SELECT 
    se.entity_name,
    fh.structure_id,
    ST_Distance(fh.geometry, s.geometry) AS distance_to_school_ft,
    s.relevance AS school_relevance
FROM fire_hydrants fh
JOIN schools s ON ST_DWithin(fh.geometry, s.geometry, 1000)
JOIN standards_entities se ON fh.entity_id = se.entity_id
WHERE fh.entity_id IN (SELECT entity_id FROM needs_inspection)
ORDER BY distance_to_school_ft;
```

---

## Summary: The Power of AI Integration

### Traditional CAD/GIS Query Limitations:
- ❌ Keyword-only search (misses synonyms)
- ❌ Manual spatial queries (tedious)
- ❌ No semantic understanding
- ❌ No relationship traversal
- ❌ Quality is not queryable

### ACAD-GIS AI-Powered Queries:
- ✅ Semantic search (meaning-based)
- ✅ Hybrid fusion (text + vector + spatial + quality)
- ✅ GraphRAG (multi-hop relationships)
- ✅ ML features (predictive analytics)
- ✅ Natural language interface
- ✅ Quality-weighted results

**Result:** A database that "understands" civil engineering and can answer complex questions that traditional systems cannot.
