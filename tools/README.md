# ACAD-GIS AI-First Database Toolkit

Complete Python toolkit for managing your AI-optimized ACAD-GIS database.

## 📦 Package Structure

```
tools/
├── db_utils.py                    # Database connection & helper functions
├── ingestion/
│   ├── __init__.py
│   └── standards_loader.py        # Load CAD standards from JSON/CSV
├── embeddings/
│   ├── __init__.py
│   └── embedding_generator.py     # Generate OpenAI embeddings
├── relationships/
│   ├── __init__.py
│   └── graph_builder.py           # Build knowledge graph relationships
├── validation/
│   ├── __init__.py
│   └── data_validator.py          # Validate data quality
├── maintenance/
│   ├── __init__.py
│   └── db_maintenance.py          # Database maintenance tasks
└── api/
    └── toolkit_routes.py          # Flask API endpoints
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# OpenAI package for embeddings (already installed)
pip install openai
```

### 2. Set Environment Variables
```bash
# Required for embedding generation
export OPENAI_API_KEY='your-key-here'

# Database URL (should already be set)
export DATABASE_URL='postgresql://...'
```

### 3. Use the Web Interface
Visit `/toolkit` in your Flask app for a visual interface to:
- View database statistics
- Generate embeddings
- Build relationships
- Validate data
- Run maintenance

### 4. Use Python Scripts
```bash
# Load CAD standards
python examples/load_standards_example.py

# Generate embeddings
python examples/generate_embeddings_example.py

# Build relationships
python examples/build_relationships_example.py

# Validate data
python examples/validate_data_example.py

# Run maintenance
python examples/maintenance_example.py
```

## 📚 Core Modules

### db_utils.py
Database connection pooling and helper functions.

**Key Functions:**
- `get_connection()` - Get pooled database connection
- `execute_query()` - Execute SQL with params
- `get_or_create_entity()` - Entity registry management
- `update_quality_score()` - Quality score calculation
- `refresh_materialized_views()` - Refresh all views
- `get_entity_stats()` - Get entity statistics

**Usage:**
```python
from tools.db_utils import execute_query, get_entity_stats

# Execute query
results = execute_query("SELECT * FROM layer_standards LIMIT 10")

# Get statistics
stats = get_entity_stats()
print(f"Total entities: {stats['total_entities']}")
```

### ingestion/standards_loader.py
Load CAD standards into the database.

**Features:**
- Automatic entity registration
- Tag extraction from categories
- Quality score calculation
- Support for JSON and CSV

**Usage:**
```python
from tools.ingestion.standards_loader import StandardsLoader

loader = StandardsLoader()

# Load layers
layer_data = [
    {
        'name': 'C-TOPO-MAJR',
        'description': 'Major contours',
        'color_name': 'Brown',
        'category': 'Civil'
    }
]
stats = loader.load_layers(layer_data)
print(f"Inserted: {stats['inserted']}, Updated: {stats['updated']}")
```

### embeddings/embedding_generator.py
Generate vector embeddings for semantic search.

**Features:**
- OpenAI text-embedding-3-small (1536 dimensions)
- Batch processing with rate limiting
- Model version tracking
- Quality score updates

**Usage:**
```python
from tools.embeddings.embedding_generator import EmbeddingGenerator

generator = EmbeddingGenerator(provider='openai', model='text-embedding-3-small')

# Generate for a table
stats = generator.generate_for_table(
    table_name='layer_standards',
    text_columns=['name', 'description'],
    where_clause='WHERE entity_id IS NOT NULL LIMIT 100'
)

print(f"Generated: {stats['generated']}, Tokens: {stats['tokens_used']}")
```

**Cost Estimate:**
- text-embedding-3-small: ~$0.02 per 1000 tokens
- Average standard: ~50 tokens
- 1000 standards ≈ $1.00

### relationships/graph_builder.py
Build knowledge graph relationships.

**Features:**
- Spatial relationships (PostGIS)
- Engineering relationships (domain logic)
- Semantic relationships (embedding similarity)
- GraphRAG support

**Usage:**
```python
from tools.relationships.graph_builder import GraphBuilder

builder = GraphBuilder()

# Spatial relationships
count = builder.create_spatial_relationships(
    source_table='parcels',
    target_table='utility_lines',
    relationship_type='contains'
)

# Semantic relationships from embeddings
count = builder.create_semantic_relationships(
    similarity_threshold=0.80,
    limit_per_entity=5
)

# Complete graph
stats = builder.build_complete_graph()
```

### validation/data_validator.py
Validate data quality and integrity.

**Features:**
- Required field checks
- PostGIS geometry validation
- Duplicate detection
- Quality score analysis
- Missing embedding detection

**Usage:**
```python
from tools.validation.data_validator import DataValidator

validator = DataValidator()

# Validate specific table
results = validator.validate_table(
    table_name='layer_standards',
    required_fields=['name'],
    unique_fields=['name']
)

# Validate all standards
results = validator.validate_all_standards()
print(f"Total issues: {results['total_issues']}")
```

### maintenance/db_maintenance.py
Database maintenance and optimization.

**Features:**
- Refresh materialized views
- Recompute quality scores
- VACUUM and ANALYZE
- Index health monitoring
- Database size tracking

**Usage:**
```python
from tools.maintenance.db_maintenance import DatabaseMaintenance

maintenance = DatabaseMaintenance()

# Quick refresh
maintenance.refresh_all_materialized_views()
maintenance.recompute_all_quality_scores()

# Full maintenance
results = maintenance.run_full_maintenance(include_vacuum_full=False)
```

## 🌐 Flask API Endpoints

All API endpoints are available at `/api/toolkit`:

### Statistics
- `GET /api/toolkit/stats` - Get entity statistics
- `GET /api/toolkit/health` - Health check

### Ingestion
- `POST /api/toolkit/load/layers` - Load layers
- `POST /api/toolkit/load/blocks` - Load blocks
- `POST /api/toolkit/load/details` - Load details

### Embeddings
- `POST /api/toolkit/embeddings/generate` - Generate embeddings
- `POST /api/toolkit/embeddings/refresh` - Refresh old embeddings

### Relationships
- `POST /api/toolkit/relationships/spatial` - Create spatial relationships
- `POST /api/toolkit/relationships/semantic` - Create semantic relationships
- `POST /api/toolkit/relationships/build-complete` - Build complete graph

### Validation
- `GET /api/toolkit/validate/all` - Validate all
- `POST /api/toolkit/validate/table` - Validate specific table

### Maintenance
- `POST /api/toolkit/maintenance/refresh-views` - Refresh views
- `POST /api/toolkit/maintenance/recompute-quality` - Recompute quality
- `POST /api/toolkit/maintenance/vacuum` - VACUUM database
- `POST /api/toolkit/maintenance/full` - Full maintenance

## 🔧 Configuration

### Required Environment Variables
```bash
# OpenAI API Key (for embeddings)
OPENAI_API_KEY=sk-...

# Database URL
DATABASE_URL=postgresql://user:pass@host:port/db
```

### Optional Configuration
Edit module files to customize:
- Embedding model (default: text-embedding-3-small)
- Similarity thresholds (default: 0.80)
- Batch sizes (default: 50)
- Quality score weights

## 📊 Database Schema Requirements

The toolkit works with the AI-optimized schema that includes:

**Core Tables:**
- `standards_entities` - Unified entity registry
- `entity_embeddings` - Vector storage
- `entity_relationships` - Graph edges
- `entity_aliases` - Entity resolution
- `embedding_models` - Model tracking

**All domain tables must have:**
- `entity_id UUID` - Link to standards_entities
- `quality_score NUMERIC` - Quality metric
- `tags TEXT[]` - Categories
- `attributes JSONB` - Metadata
- `search_vector tsvector` - Full-text search

See `/database/SCHEMA_VERIFICATION.md` for complete schema details.

## 🎯 Typical Workflows

### Initial Data Load
```python
# 1. Load standards
from tools.ingestion.standards_loader import StandardsLoader
loader = StandardsLoader()
loader.load_layers(layer_data)
loader.load_blocks(block_data)

# 2. Generate embeddings
from tools.embeddings.embedding_generator import EmbeddingGenerator
generator = EmbeddingGenerator()
generator.generate_for_table('layer_standards', ['name', 'description'])

# 3. Build relationships
from tools.relationships.graph_builder import GraphBuilder
builder = GraphBuilder()
builder.build_complete_graph()

# 4. Validate
from tools.validation.data_validator import DataValidator
validator = DataValidator()
results = validator.validate_all_standards()

# 5. Maintenance
from tools.maintenance.db_maintenance import DatabaseMaintenance
maintenance = DatabaseMaintenance()
maintenance.run_full_maintenance()
```

### Regular Updates
```python
# After adding new data
from tools.db_utils import refresh_materialized_views, update_quality_score

# Refresh views
refresh_materialized_views()

# Update quality scores
# (or use maintenance module)
```

### Weekly Maintenance
```python
from tools.maintenance.db_maintenance import DatabaseMaintenance

maintenance = DatabaseMaintenance()
maintenance.run_full_maintenance(include_vacuum_full=False)
```

## 🧪 Testing

### Test Database Connection
```python
from tools.db_utils import execute_query

result = execute_query("SELECT COUNT(*) as count FROM standards_entities")
print(f"Total entities: {result[0]['count']}")
```

### Test Embeddings
```python
from tools.embeddings.embedding_generator import EmbeddingGenerator

generator = EmbeddingGenerator()
print(f"Model: {generator.model}, ID: {generator.model_id}")
```

### Test GraphRAG
```sql
-- Find related entities (2 hops)
SELECT * FROM find_related_entities('entity-uuid', 2);

-- Find similar entities
SELECT * FROM find_similar_entities('entity-uuid', 0.80, 20);

-- Hybrid search
SELECT * FROM hybrid_search('water main', NULL::vector, NULL, 0.5, 10);
```

## 📖 Additional Documentation

- `/examples/README.md` - Example scripts and usage
- `/database/SCHEMA_VERIFICATION.md` - Complete schema docs
- `/database/AI_OPTIMIZATION_SUMMARY.md` - AI architecture overview
- `/replit.md` - Main project documentation

## 🔒 Security

- **API Keys**: Never commit API keys. Use environment variables.
- **Database**: Uses connection pooling. No SQL injection risks (parameterized queries).
- **Rate Limiting**: OpenAI requests automatically rate-limited (1/sec).

## 🐛 Troubleshooting

### "OPENAI_API_KEY not set"
```bash
export OPENAI_API_KEY='your-key-here'
```

### "DATABASE_URL not set"
Check your `.env` file or Replit secrets.

### "Table does not exist"
Make sure schema is created. Check `/database/schema/complete_schema.sql`.

### Slow embedding generation
- Use smaller batches
- Use text-embedding-3-small (faster)
- Check rate limiting

### Import errors
```bash
# Make sure you're in the right directory
cd /path/to/acad-gis

# Add tools to Python path
export PYTHONPATH="${PYTHONPATH}:./tools"
```

## 🚀 Performance Tips

1. **Batch Operations**: Process in batches of 50-100
2. **Parallel Processing**: Multiple tables simultaneously
3. **Index Maintenance**: Run VACUUM ANALYZE regularly
4. **View Refresh**: Only refresh when data changes
5. **Quality Scores**: Recompute after major changes

## 📝 Contributing

To add new toolkit modules:

1. Create module in appropriate directory
2. Follow existing patterns (db_utils, stats tracking)
3. Add API endpoint in `api/toolkit_routes.py`
4. Add example script in `examples/`
5. Update this README

## 📞 Support

See main documentation or check:
- Database schema: `/database/`
- Example scripts: `/examples/`
- API routes: `/tools/api/toolkit_routes.py`
