# ACAD-GIS Toolkit Examples

Example scripts demonstrating how to use the AI-optimized database tools.

## Prerequisites

1. **OpenAI API Key**: Required for embedding generation
   ```bash
   export OPENAI_API_KEY='your-key-here'
   ```

2. **Database Connection**: DATABASE_URL environment variable must be set

## Examples

### 1. Load CAD Standards
Load layer standards, blocks, and details from JSON/CSV files.

```bash
python examples/load_standards_example.py
```

**What it does:**
- Creates entities in `standards_entities`
- Populates CAD standards tables
- Extracts tags and attributes
- Calculates initial quality scores

### 2. Generate Embeddings
Create vector embeddings for semantic search.

```bash
# Generate for sample data (10 items per table)
python examples/generate_embeddings_example.py

# Generate for ALL standards (uses API credits)
python examples/generate_embeddings_example.py --all
```

**What it does:**
- Generates 1536-dimension embeddings using OpenAI
- Stores in `entity_embeddings` with version tracking
- Updates quality scores (entities with embeddings score higher)
- Tracks API usage and costs

**Cost Estimate:**
- text-embedding-3-small: ~$0.02 per 1000 tokens
- Average standard: ~50 tokens
- 1000 standards ≈ $1.00

### 3. Build Relationships
Create spatial, engineering, and semantic relationships for GraphRAG.

```bash
# Build sample relationships
python examples/build_relationships_example.py

# Build complete graph (all relationships)
python examples/build_relationships_example.py --complete
```

**What it does:**
- **Spatial relationships**: Uses PostGIS to find adjacent/contains/within
- **Engineering relationships**: Domain logic (upstream_of, serves, connects_to)
- **Semantic relationships**: Embedding similarity (similar_to)
- Populates `entity_relationships` for GraphRAG queries

### 4. Validate Data
Check data quality and find issues.

```bash
python examples/validate_data_example.py
```

**What it does:**
- Checks for missing required fields
- Validates PostGIS geometries
- Finds duplicate records
- Identifies low-quality entities
- Reports missing embeddings

### 5. Database Maintenance
Regular maintenance tasks.

```bash
# Full maintenance (recommended weekly)
python examples/maintenance_example.py

# Quick refresh (after data changes)
python examples/maintenance_example.py --quick
```

**What it does:**
- Refreshes materialized views
- Recomputes quality scores
- Runs VACUUM and ANALYZE
- Checks index health
- Monitors database size

## Typical Workflow

### Initial Setup (One Time)
```bash
# 1. Load your CAD standards
python examples/load_standards_example.py

# 2. Generate embeddings for all standards
python examples/generate_embeddings_example.py --all

# 3. Build complete relationship graph
python examples/build_relationships_example.py --complete

# 4. Validate everything
python examples/validate_data_example.py

# 5. Run maintenance
python examples/maintenance_example.py
```

### Regular Updates (After Adding Data)
```bash
# 1. Generate embeddings for new entities
python examples/generate_embeddings_example.py

# 2. Build new relationships
python examples/build_relationships_example.py

# 3. Quick refresh
python examples/maintenance_example.py --quick
```

### Weekly Maintenance
```bash
# Full maintenance routine
python examples/maintenance_example.py
```

## Testing AI Features

After running the examples, test your AI-optimized database:

### 1. Semantic Search (Full-Text + Vector + Quality)
```sql
-- Find all entities related to "water main"
SELECT * FROM hybrid_search(
    'water main',
    NULL::vector,
    NULL,  -- all entity types
    0.5,   -- min quality
    10     -- max results
);
```

### 2. Vector Similarity Search
```sql
-- Find similar entities to a specific entity
SELECT * FROM find_similar_entities(
    'entity-uuid-here',
    0.80,  -- similarity threshold
    20     -- max results
);
```

### 3. GraphRAG Multi-Hop Traversal
```sql
-- Find all related entities within 2 hops
SELECT * FROM find_related_entities(
    'entity-uuid-here',
    2,     -- max hops
    ARRAY['spatial', 'engineering']  -- relationship types
);
```

### 4. Spatial-Semantic Fusion
```sql
-- Find survey points near a location that are semantically similar
SELECT sp.*, ee.embedding <=> query_embedding AS similarity
FROM survey_points sp
JOIN entity_embeddings ee ON sp.entity_id = ee.entity_id
WHERE ST_DWithin(sp.geometry, ST_SetSRID(ST_MakePoint(x, y), 2226), 100)
  AND ee.is_current = true
  AND 1 - (ee.embedding <=> query_embedding) > 0.8
ORDER BY similarity
LIMIT 10;
```

## Customization

### Custom Standards Loader
```python
from tools.ingestion.standards_loader import StandardsLoader

loader = StandardsLoader()

# Load from your own JSON format
with open('my_standards.json') as f:
    data = json.load(f)
    stats = loader.load_layers(data)
```

### Custom Relationships
```python
from tools.relationships.graph_builder import GraphBuilder

builder = GraphBuilder()

# Define your own engineering relationships
rules = [{
    'source_table': 'my_source_table',
    'target_table': 'my_target_table',
    'predicate': 'custom_relationship',
    'join_condition': 'source.foreign_key = target.primary_key'
}]

builder.create_engineering_relationships(rules)
```

### Custom Validation Rules
```python
from tools.validation.data_validator import DataValidator

validator = DataValidator()

# Validate your custom table
results = validator.validate_table(
    'my_table',
    required_fields=['field1', 'field2'],
    unique_fields=['field1', 'field2'],
    has_geometry=True
)
```

## Troubleshooting

### "OPENAI_API_KEY not set"
```bash
export OPENAI_API_KEY='sk-...'
```

### "DATABASE_URL not set"
Check your .env file or environment variables.

### "Table does not exist"
Make sure you've run the schema creation scripts first.

### Slow embedding generation
- Use `text-embedding-3-small` (faster, cheaper)
- Process in batches (automatic in toolkit)
- Consider rate limiting (1 request/second automatic)

## Next Steps

1. Integrate tools into your Flask application
2. Create API endpoints for tool operations
3. Add progress tracking and monitoring
4. Schedule maintenance tasks with cron
5. Build custom tools for your specific workflow

## Support

See main documentation in:
- `/database/SCHEMA_VERIFICATION.md`
- `/database/AI_OPTIMIZATION_SUMMARY.md`
- `/replit.md`
