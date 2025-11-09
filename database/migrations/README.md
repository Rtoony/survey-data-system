# Database Migrations - CAD Standards Mapping Framework

## Migration Execution Order

**CRITICAL:** These migrations MUST be executed in the following order:

1. **create_name_mapping_tables.sql** - Creates 5 name mapping tables with search_vector support
   - block_name_mappings
   - detail_name_mappings
   - hatch_pattern_name_mappings
   - material_name_mappings
   - note_name_mappings

2. **create_project_context_mappings.sql** - Creates 6 project context mapping tables
   - project_keynote_block_mappings
   - project_keynote_detail_mappings
   - project_hatch_material_mappings
   - project_detail_material_mappings
   - project_block_specification_mappings
   - project_element_cross_references

3. **add_search_vectors_to_project_mappings.sql** - Adds AI search support to project context tables
   - Adds search_vector columns
   - Creates GIN indexes
   - Adds automatic update triggers
   - Backfills existing data

## Schema Overview

### Name Mapping Tables (DXF ↔ Database)
These tables support bidirectional translation between DXF file names and canonical database names:

| Table | Purpose | Example |
|-------|---------|---------|
| block_name_mappings | Maps DXF block names to standard block names | "CB-D" → "UTIL-WATER-CATCHBASIN-D-NEW" |
| detail_name_mappings | Maps detail callouts to canonical detail names | "DTL 5/C-3" → "CIVIL-ROAD-PAVEMENT-SECTION-NEW" |
| hatch_pattern_name_mappings | Maps DXF hatch patterns to standard patterns | "AC-2" → "PAVE-ASPHALT-AC2-SOLID-NEW" |
| material_name_mappings | Maps material abbreviations to full material names | "4" AC" → "PAVE-ASPHALT-AC2-4IN-NEW" |
| note_name_mappings | Maps keynote numbers to standard note IDs | "G-5" → "GENERAL-GRADING-SLOPE-WARNING-NEW" |

**Key Features:**
- Multi-client scoping (`client_id`, `project_id`)
- Import/export direction flags
- DXF alias patterns for flexible matching
- Confidence scores for ambiguous mappings
- AI-friendly search vectors

### Project Context Mapping Tables (Element Relationships)

These tables create semantic relationships between different element types within projects:

| Table | Purpose | Example |
|-------|---------|---------|
| project_keynote_block_mappings | Links keynotes to blocks | Keynote "5" references "Type D Catch Basin" block |
| project_keynote_detail_mappings | Links keynotes to details | Keynote "10" → "See Detail C-3.1" |
| project_hatch_material_mappings | Links hatch patterns to materials | "AC-2 Pattern" represents "AC Type II Material" |
| project_detail_material_mappings | Tracks materials shown in details | "Pavement Detail" shows AC, PCC, Base materials |
| project_block_specification_mappings | Links symbols to specifications | "Fire Hydrant" → "AWWA C502 Spec" |
| project_element_cross_references | Master relationship index | All cross-element relationships |

**Key Features:**
- Flexible relationship types (references, defines, specifies, shows)
- Sheet-level context tracking
- Material thickness and quantity support
- Manufacturer/product data for symbols
- Jurisdiction-specific requirements

## AI-Friendly Features

All 11 tables include:

- **Full-text search:** `search_vector` TSVECTOR columns with GIN indexes
- **Weighted search:** High weights for primary identifiers (keynote numbers, names), lower weights for descriptions
- **Automatic updates:** Triggers maintain search vectors on INSERT/UPDATE
- **Flexible metadata:** `tags TEXT[]` and `attributes JSONB` columns
- **Quality tracking:** Confidence scores and validation flags

## Cross-Element Alignment

Elements are semantically aligned using shared naming components:

```
Keynote:  CIVIL-WATER-VALVE-INSTALL → THEME = WATER
Block:    UTIL-WATER-VALVE-6IN     → ATTRIBUTE = WATER
Detail:   UTIL-VALVE-ASSEMBLY-A    → FAMILY = VALVE
Material: WATER-VALVE-6IN-BRASS    → Specification linkage
```

This enables semantic chaining like:
"Keynote references Block" → "Block shown in Detail" → "Detail specifies Material"

## Usage Examples

### Query 1: Find all elements related to "catch basin"
```sql
SELECT 'block' as type, canonical_name, description 
FROM block_name_mappings 
WHERE search_vector @@ to_tsquery('english', 'catch & basin')
UNION ALL
SELECT 'detail', canonical_name, description 
FROM detail_name_mappings 
WHERE search_vector @@ to_tsquery('english', 'catch & basin');
```

### Query 2: Get all keynotes referencing a specific block
```sql
SELECT kn.*, bm.canonical_name as block_name
FROM project_keynote_block_mappings kb
JOIN standard_notes kn ON kb.note_id = kn.note_id
JOIN block_name_mappings bm ON kb.block_id = bm.mapping_id
WHERE kb.project_id = 'PROJECT_UUID'
AND bm.canonical_name LIKE '%CATCHBASIN%';
```

### Query 3: Find materials shown in a detail
```sql
SELECT d.canonical_name as detail_name,
       m.canonical_name as material_name,
       dm.material_thickness,
       dm.material_layer_order
FROM project_detail_material_mappings dm
JOIN detail_name_mappings d ON dm.detail_id = d.mapping_id
JOIN material_name_mappings m ON dm.material_id = m.mapping_id
WHERE dm.project_id = 'PROJECT_UUID'
ORDER BY d.canonical_name, dm.material_layer_order;
```

## Next Steps

These database tables enable:

1. **Standards Visualization Dashboard** - Interactive web UI showing all mapping relationships
2. **CRUD Managers** - Data entry interfaces for all 11 mapping types
3. **Project Context Manager** - UI for assigning keynotes to blocks, hatches to materials, etc.
4. **Export/Documentation Generator** - Create PDFs, Excel files, or web pages for client handoffs and training

## Documentation References

- Naming conventions: `standards/cad_standards_vocabulary.md`
- Project documentation: `replit.md`
