# ACAD-GIS Data Flow & Lifecycle

## Overview

This document traces the complete journey of data through the ACAD-GIS system, from messy client DXF files through intelligent database storage, AI processing, and clean export back to CAD.

---

## The Complete Data Journey

```
┌─────────────────────────────────────────────────────────────────────┐
│  CLIENT DXF FILES (The Starting Point)                              │
│  - Inconsistent layer names                                         │
│  - Non-standard organization                                        │
│  - Buried intelligence in geometry                                  │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│  IMPORT & PATTERN MATCHING                                          │
│  - Parse DXF using ezdxf library                                    │
│  - Apply client-specific regex patterns                             │
│  - Extract semantic information from layer names                    │
│  - Map to canonical database vocabulary                             │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STRUCTURED DATABASE STORAGE                                        │
│  - Create entity records with canonical IDs                         │
│  - Store PostGIS geometry (XYZ-aware)                               │
│  - Generate geometry hashes for change detection                    │
│  - Link to standards library                                        │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│  AI PROCESSING PIPELINE                                             │
│  - Generate vector embeddings (OpenAI/local models)                 │
│  - Build spatial relationships (PostGIS queries)                    │
│  - Compute engineering relationships (network topology)             │
│  - Calculate quality scores                                         │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│  INTELLIGENT QUERYING & ANALYSIS                                    │
│  - Hybrid search (text + vector + spatial + quality)                │
│  - GraphRAG multi-hop queries                                       │
│  - Semantic similarity matching                                     │
│  - Predictive analytics                                             │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│  CLEAN DXF EXPORT                                                   │
│  - Apply standard or client-specific layer names                    │
│  - Generate clean, organized CAD files                              │
│  - Preserve survey-grade XYZ coordinates                            │
│  - Include only necessary entities                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: DXF Import & Pattern Matching

### Step 1: File Upload & Parsing

**Entry Point:** `/tools/dxf-import` or `/tools/batch-cad-import`

```python
# Upload DXF file
file = request.files['dxf_file']
doc = ezdxf.readfile(file)

# Extract metadata
dxf_version = doc.dxfversion
units = doc.header.get('$INSUNITS', 0)
modelspace = doc.modelspace()
```

### Step 2: Import Pattern Matching

**Purpose:** Translate messy client layer names into structured database records.

**Example Client Layer:** `S-UTIL-STORM-12`

**Lookup Import Pattern:**
```sql
SELECT * FROM import_patterns 
WHERE client_id = %s 
  AND is_active = TRUE
ORDER BY priority DESC;
```

**Pattern Record:**
```json
{
  "pattern_id": "uuid-123",
  "client_name": "Acme Engineering",
  "source_pattern": "^([A-Z]+)-([A-Z]+)-([A-Z0-9]+)-([A-Z0-9]+)$",
  "extraction_rules": {
    "discipline_group": 1,
    "category_group": 2,
    "type_group": 3,
    "attribute_group": 4
  }
}
```

**Extraction Process:**
```python
import re

layer_name = "S-UTIL-STORM-12"
pattern = r"^([A-Z]+)-([A-Z]+)-([A-Z0-9]+)-([A-Z0-9]+)$"
match = re.match(pattern, layer_name)

if match:
    discipline_code = match.group(1)  # "S" → lookup "SURV"
    category_code = match.group(2)    # "UTIL"
    type_code = match.group(3)        # "STORM"
    attribute_code = match.group(4)   # "12" → "12IN"
```

**Database Lookup:**
```sql
-- Find matching discipline
SELECT discipline_id FROM discipline_standards 
WHERE discipline_code = 'SURV';

-- Find matching category under that discipline
SELECT category_id FROM category_standards 
WHERE category_code = 'UTIL' AND discipline_id = %s;

-- Find matching object type
SELECT object_type_id FROM object_type_standards 
WHERE type_code = 'STORM' AND category_id = %s;
```

### Step 3: Entity Creation

**For Each DXF Entity:**

```python
def import_dxf_entity(dxf_entity, layer_name, drawing_id):
    # 1. Determine entity type
    entity_type = dxf_entity.dxftype()  # LINE, POLYLINE, INSERT, etc.
    
    # 2. Extract geometry
    if entity_type == 'LINE':
        start = dxf_entity.dxf.start  # (x, y, z)
        end = dxf_entity.dxf.end
        geometry = f'LINESTRING Z ({start[0]} {start[1]} {start[2]}, 
                                     {end[0]} {end[1]} {end[2]})'
    
    elif entity_type == 'LWPOLYLINE':
        points = list(dxf_entity.get_points('xyze'))
        wkt_points = ', '.join([f'{p[0]} {p[1]} {p[2]}' for p in points])
        geometry = f'LINESTRING Z ({wkt_points})'
    
    # 3. Compute geometry hash (for change detection)
    geometry_hash = hashlib.sha256(geometry.encode()).hexdigest()
    
    # 4. Extract attributes
    attributes = {
        'color': dxf_entity.dxf.color,
        'linetype': dxf_entity.dxf.linetype,
        'lineweight': dxf_entity.dxf.lineweight,
        'handle': dxf_entity.dxf.handle
    }
    
    # 5. Create database record
    entity_id = create_or_get_entity(
        entity_type='drawing_entity',
        entity_name=f'{layer_name}_{entity_type}_{dxf_entity.dxf.handle}'
    )
    
    # 6. Store in drawing_entities table
    insert_query = """
        INSERT INTO drawing_entities 
        (entity_id, drawing_id, layer_id, entity_type, geometry, 
         geometry_hash, attributes, dxf_handle)
        VALUES (%s, %s, %s, %s, ST_GeomFromText(%s, 2226), 
                %s, %s, %s)
    """
    
    # 7. Create DXF link record (for sync)
    insert_dxf_link(
        drawing_id=drawing_id,
        dxf_handle=dxf_entity.dxf.handle,
        database_table='drawing_entities',
        database_id=entity_id,
        geometry_hash=geometry_hash
    )
    
    return entity_id
```

### Step 4: Intelligent Object Creation

**For Recognized Objects (e.g., Utility Pipes):**

```python
def create_utility_object(entity, layer_info):
    # Parsed layer: CIV-UTIL-STORM-12IN-NEW-LN
    
    # Extract metadata from layer
    utility_type = layer_info['object_type']  # STORM
    diameter = extract_diameter(layer_info['attributes'])  # 12IN → 12.0
    phase = layer_info['phase']  # NEW
    
    # Create canonical entity
    entity_id = create_or_get_entity(
        entity_type='utility_line',
        entity_name=f'Storm Pipe {entity.dxf.handle}'
    )
    
    # Create utility_lines record
    insert_query = """
        INSERT INTO utility_lines
        (line_id, entity_id, project_id, line_type, diameter, 
         material, phase, geometry, quality_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 2226), 0.75)
    """
    
    execute_query(insert_query, (
        uuid.uuid4(), entity_id, project_id, 'storm_drain',
        diameter, 'PVC', phase, geometry_wkt
    ))
    
    # Tag for AI processing
    tag_entity_for_embedding_generation(entity_id)
    
    return entity_id
```

---

## Phase 2: AI Processing Pipeline

### Step 1: Embedding Generation

**Trigger:** New entity created or updated

```python
def generate_entity_embedding(entity_id):
    # 1. Fetch entity data
    entity = get_entity_details(entity_id)
    
    # 2. Create text description for embedding
    text = f"""
    {entity['entity_type']}: {entity['entity_name']}
    Description: {entity.get('description', '')}
    Tags: {', '.join(entity.get('tags', []))}
    Attributes: {json.dumps(entity.get('attributes', {}))}
    """
    
    # 3. Call OpenAI API (or local model)
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-3-small"
    )
    
    embedding_vector = response['data'][0]['embedding']
    
    # 4. Store in entity_embeddings table
    insert_query = """
        INSERT INTO entity_embeddings 
        (entity_id, embedding, model_id, generated_at, text_used)
        VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s)
        ON CONFLICT (entity_id, model_id) 
        DO UPDATE SET 
            embedding = EXCLUDED.embedding,
            generated_at = CURRENT_TIMESTAMP
    """
    
    execute_query(insert_query, (
        entity_id, 
        embedding_vector,  # pgvector automatically converts list to vector
        model_id,
        text
    ))
    
    # 5. Update quality score (has embedding now!)
    update_quality_score(entity_id)
```

### Step 2: Spatial Relationship Building

**Trigger:** Batch processing or new entity added

```python
def build_spatial_relationships(entity_id):
    # Get entity geometry
    entity = get_entity_with_geometry(entity_id)
    
    # Find nearby entities (within 100 feet)
    nearby_query = """
        SELECT 
            se.entity_id,
            se.entity_type,
            ST_Distance(e1.geometry, e2.geometry) AS distance
        FROM standards_entities se
        JOIN (SELECT geometry FROM get_entity_geometry(%s)) e1 ON true
        JOIN get_entity_geometry(se.entity_id) e2 ON true
        WHERE se.entity_id != %s
          AND ST_DWithin(e1.geometry, e2.geometry, 100)
        ORDER BY distance
        LIMIT 50
    """
    
    nearby = execute_query(nearby_query, (entity_id, entity_id))
    
    # Create relationship records
    for neighbor in nearby:
        # Compute relationship strength (inverse of distance)
        strength = max(0.0, 1.0 - (neighbor['distance'] / 100.0))
        
        insert_relationship(
            source_entity_id=entity_id,
            target_entity_id=neighbor['entity_id'],
            relationship_type='spatial',
            relationship_strength=strength,
            metadata={'distance_ft': neighbor['distance']}
        )
```

### Step 3: Engineering Relationship Building

**For Network Entities (Pipes, Structures):**

```python
def build_utility_network_relationships(project_id):
    # Find all utility structures
    structures = get_utility_structures(project_id)
    
    # For each pipe
    pipes = get_utility_lines(project_id)
    
    for pipe in pipes:
        # Find upstream structure (start point of pipe)
        upstream = find_nearest_structure(
            point=ST_StartPoint(pipe.geometry),
            max_distance=5.0  # 5 feet tolerance
        )
        
        # Find downstream structure (end point of pipe)
        downstream = find_nearest_structure(
            point=ST_EndPoint(pipe.geometry),
            max_distance=5.0
        )
        
        if upstream:
            # Pipe flows FROM upstream structure
            insert_relationship(
                source_entity_id=upstream.entity_id,
                target_entity_id=pipe.entity_id,
                relationship_type='engineering',
                relationship_strength=1.0,
                metadata={'connection_type': 'outflow', 'role': 'source'}
            )
            
            # Update pipe record
            update_query = """
                UPDATE utility_lines 
                SET upstream_structure_id = %s
                WHERE line_id = %s
            """
            execute_query(update_query, (upstream.structure_id, pipe.line_id))
        
        if downstream:
            # Pipe flows TO downstream structure
            insert_relationship(
                source_entity_id=pipe.entity_id,
                target_entity_id=downstream.entity_id,
                relationship_type='engineering',
                relationship_strength=1.0,
                metadata={'connection_type': 'inflow', 'role': 'target'}
            )
            
            update_query = """
                UPDATE utility_lines 
                SET downstream_structure_id = %s
                WHERE line_id = %s
            """
            execute_query(update_query, (downstream.structure_id, pipe.line_id))
```

### Step 4: Semantic Relationship Building

**Based on Embedding Similarity:**

```python
def build_semantic_relationships(entity_id, similarity_threshold=0.80):
    # Get entity's embedding
    embedding = get_entity_embedding(entity_id)
    
    # Find similar entities using vector similarity
    query = """
        SELECT 
            ee.entity_id,
            1 - (ee.embedding <=> %s::vector) AS similarity,
            se.entity_type,
            se.entity_name
        FROM entity_embeddings ee
        JOIN standards_entities se ON ee.entity_id = se.entity_id
        WHERE ee.entity_id != %s
          AND 1 - (ee.embedding <=> %s::vector) > %s
        ORDER BY ee.embedding <=> %s::vector
        LIMIT 20
    """
    
    similar = execute_query(query, (
        embedding, entity_id, embedding, 
        similarity_threshold, embedding
    ))
    
    # Create semantic relationship records
    for match in similar:
        insert_relationship(
            source_entity_id=entity_id,
            target_entity_id=match['entity_id'],
            relationship_type='semantic',
            relationship_strength=match['similarity'],
            metadata={
                'similarity_score': match['similarity'],
                'related_type': match['entity_type']
            }
        )
```

### Step 5: Quality Score Computation

**Automated Function:**

**AUTHORITATIVE IMPLEMENTATION** (from complete_schema.sql):

```sql
CREATE FUNCTION compute_quality_score(
    required_fields_filled INTEGER,
    total_required_fields INTEGER,
    has_embedding BOOLEAN DEFAULT false,
    has_relationships BOOLEAN DEFAULT false
) RETURNS NUMERIC AS $$
DECLARE
    completeness_score NUMERIC(4, 3);
    bonus_score NUMERIC(4, 3);
BEGIN
    -- Base score from completeness (70% weight)
    IF total_required_fields > 0 THEN
        completeness_score := (required_fields_filled::NUMERIC / total_required_fields::NUMERIC) * 0.7;
    ELSE
        completeness_score := 0.7;
    END IF;

    -- Bonus for having embeddings and relationships (15% each)
    bonus_score := 0.0;
    IF has_embedding THEN
        bonus_score := bonus_score + 0.15;  -- Embedding bonus: 15%
    END IF;
    IF has_relationships THEN
        bonus_score := bonus_score + 0.15;  -- Relationships bonus: 15%
    END IF;

    RETURN LEAST(1.0, completeness_score + bonus_score);
END;
$$ LANGUAGE plpgsql IMMUTABLE;
```

---

## Phase 3: Change Detection & Re-Import

### Step 1: Detect Changes on Re-Import

```python
def reimport_dxf_with_change_detection(drawing_id, new_dxf_file):
    # 1. Parse new DXF
    doc = ezdxf.readfile(new_dxf_file)
    
    # 2. Get existing DXF links
    existing_links = get_dxf_links(drawing_id)
    
    # 3. Process each entity
    new_handles = set()
    
    for entity in doc.modelspace():
        handle = entity.dxf.handle
        new_handles.add(handle)
        
        # Compute current geometry hash
        geometry = extract_geometry(entity)
        current_hash = hashlib.sha256(geometry.encode()).hexdigest()
        
        # Check if entity existed before
        existing = existing_links.get(handle)
        
        if existing:
            # Entity exists - check if modified
            if existing['geometry_hash'] != current_hash:
                # Geometry changed - update database
                update_entity_geometry(
                    table=existing['database_table'],
                    id=existing['database_id'],
                    new_geometry=geometry
                )
                
                # Update link record
                update_dxf_link(
                    link_id=existing['link_id'],
                    geometry_hash=current_hash,
                    last_sync_at=datetime.now()
                )
                
                # Re-trigger AI processing
                tag_entity_for_reprocessing(existing['database_id'])
        else:
            # New entity - create it
            entity_id = import_dxf_entity(entity, drawing_id)
            create_dxf_link(drawing_id, handle, entity_id, current_hash)
    
    # 4. Find deleted entities (in DB but not in new DXF)
    deleted_handles = set(existing_links.keys()) - new_handles
    
    for handle in deleted_handles:
        link = existing_links[handle]
        # Mark as deleted or actually delete
        soft_delete_entity(link['database_table'], link['database_id'])
        delete_dxf_link(link['link_id'])
```

---

## Phase 4: Export & Layer Name Generation

### Step 1: Query Database for Export

```python
def export_project_to_dxf(project_id, export_config):
    # 1. Create new DXF document
    doc = ezdxf.new('R2018')
    msp = doc.modelspace()
    
    # 2. Get export configuration
    layer_name_format = export_config.get('layer_name_format', 'standard')
    coordinate_system = export_config.get('coordinate_system', 'STATE_PLANE')
    
    # 3. Query all entities for export
    entities = get_project_entities_for_export(project_id)
    
    # 4. Group by layer
    layers_dict = {}
    
    for entity in entities:
        # Generate layer name based on config
        if layer_name_format == 'standard':
            layer_name = generate_standard_layer_name(entity)
        elif layer_name_format == 'client_specific':
            layer_name = generate_client_layer_name(entity, export_config)
        
        # Create layer if not exists
        if layer_name not in layers_dict:
            doc.layers.add(
                name=layer_name,
                color=entity.get('color', 7),
                linetype=entity.get('linetype', 'Continuous')
            )
            layers_dict[layer_name] = []
        
        layers_dict[layer_name].append(entity)
    
    # 5. Add entities to DXF
    for layer_name, layer_entities in layers_dict.items():
        for entity in layer_entities:
            add_entity_to_dxf(msp, entity, layer_name)
    
    # 6. Save file
    output_path = f'/tmp/export_{project_id}_{datetime.now().timestamp()}.dxf'
    doc.saveas(output_path)
    
    return output_path
```

### Step 2: Standard Layer Name Generation

```python
def generate_standard_layer_name(entity):
    # Entity metadata from database
    discipline = entity.get('discipline_code', 'CIV')
    category = entity.get('category_code', 'UTIL')
    obj_type = entity.get('object_type_code', 'MISC')
    attributes = entity.get('attribute_codes', [])
    phase = entity.get('phase_code', 'EXIST')
    geometry = entity.get('geometry_code', 'LN')
    
    # Build layer name
    parts = [discipline, category, obj_type]
    
    # Add attributes if present
    if attributes:
        parts.extend(attributes)
    
    parts.extend([phase, geometry])
    
    # Join with hyphens
    layer_name = '-'.join(parts)
    
    return layer_name

# Example output: "CIV-UTIL-STORM-12IN-NEW-LN"
```

### Step 3: Client-Specific Layer Name Generation

```python
def generate_client_layer_name(entity, export_config):
    # Get client's export pattern
    client_id = export_config['client_id']
    export_pattern = get_client_export_pattern(client_id)
    
    # Example pattern: "{discipline}.{category}.{type}.{phase}"
    template = export_pattern['layer_template']
    
    # Map database codes to client codes
    mappings = export_pattern['code_mappings']
    
    layer_name = template.format(
        discipline=mappings['discipline'].get(entity['discipline_code'], 'CIVIL'),
        category=mappings['category'].get(entity['category_code'], 'UTILITIES'),
        type=mappings['object_type'].get(entity['object_type_code'], 'MISC'),
        phase=mappings['phase'].get(entity['phase_code'], 'EXISTING')
    )
    
    return layer_name

# Example output: "CIVIL.UTILITIES.STORM.NEW"
```

---

## Data Lifecycle Timeline

```
DAY 1: Initial Import
├── 09:00 - Client uploads messy DXF (500 entities)
├── 09:05 - Pattern matching extracts metadata
├── 09:10 - Database records created (500 entities)
├── 09:15 - DXF link records created (change tracking enabled)
└── 09:20 - Import complete

DAY 1: AI Processing (Background)
├── 10:00 - Embedding generation starts (batch of 100)
├── 10:30 - Spatial relationship building (500 relationships)
├── 11:00 - Quality scores computed
└── 11:30 - AI processing complete

DAY 5: User Makes Changes
├── 14:00 - User modifies standard note (creates modified copy)
├── 14:01 - Modified copy created with deviation tracking
├── 14:02 - Embedding regenerated for modified copy
└── 14:05 - Quality score updated

DAY 10: Re-Import Updated DXF
├── 16:00 - Client uploads updated DXF (520 entities)
├── 16:02 - Change detection: 480 unchanged, 15 modified, 5 new, 20 deleted
├── 16:05 - Update 15 modified entities (geometry hashes updated)
├── 16:06 - Create 5 new entities
├── 16:07 - Soft-delete 20 removed entities
├── 16:10 - Re-trigger AI processing for 20 changed entities
└── 16:30 - Re-import complete

DAY 15: Export Clean DXF
├── 10:00 - User requests export with standard layer names
├── 10:02 - Query database (520 entities)
├── 10:03 - Generate standard layer names
├── 10:05 - Create DXF with clean, organized layers
├── 10:06 - User downloads perfectly organized CAD file
└── 10:07 - Export job logged for audit trail
```

---

## Summary: The Transformation

### Before (File-Bound CAD)
- Data trapped in DXF files
- Manual interpretation required
- No change tracking
- No semantic understanding
- Inconsistent organization

### After (Database-First AI System)
- Data structured and queryable
- Automatic semantic extraction
- Geometry hash-based change detection
- AI embeddings for semantic search
- Clean, standards-compliant export

**Key Innovation:** The database is the source of truth, and DXF files are just import/export formats—not storage.
