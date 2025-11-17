# AI Embedding & Graph RAG Implementation Game Plan
**System**: ACAD-GIS Survey Data System
**Date**: November 17, 2025
**Goal**: Activate AI/embedding features and integrate into user workflows

**Prerequisite**: Read `AI_EMBEDDING_GRAPH_RAG_AUDIT.md` for context

---

## 🎯 Phase 1: Quick Wins (Week 1) - Prove Value Immediately

**Goal**: Generate embeddings for one table and demonstrate tangible results to users

### Task 1.1: Environment Setup & Health Check (30 minutes)

```bash
# 1. Set OpenAI API key
cd /home/user/survey-data-system
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# 2. Verify environment
python << EOF
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
if api_key and api_key.startswith('sk-'):
    print('✓ OPENAI_API_KEY configured')
else:
    print('✗ OPENAI_API_KEY missing or invalid')
    exit(1)
EOF

# 3. Run comprehensive health check
python tools/health_check.py
```

**Expected Output**:
```
✓ Database connection
✓ Core schema tables
✓ PostGIS extension
✓ pgvector extension
✓ Helper functions
✓ Materialized views
✓ Embeddings module
🎉 All checks passed! Toolkit is ready to use.
```

---

### Task 1.2: Generate First Batch of Embeddings (2 hours)

**File**: Create `scripts/phase1_generate_embeddings.py`

```python
#!/usr/bin/env python3
"""
Phase 1: Generate embeddings for layer_standards table.
This proves the concept and shows tangible value.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'tools'))

from embeddings.embedding_generator import EmbeddingGenerator
from db_utils import execute_query

def main():
    print("=" * 70)
    print("Phase 1: Generate Embeddings for Layer Standards")
    print("=" * 70)
    print()

    # Initialize generator with conservative budget
    gen = EmbeddingGenerator(
        provider='openai',
        model='text-embedding-3-small',
        budget_cap=10.0,  # $10 initial budget
        dry_run=False
    )

    print(f"✓ Initialized EmbeddingGenerator")
    print(f"  Model: {gen.model_name}")
    print(f"  Dimensions: {gen.dimensions}")
    print(f"  Budget Cap: ${gen.budget_cap}")
    print()

    # Preview cost first
    print("Running dry-run to estimate costs...")
    gen_preview = EmbeddingGenerator(
        provider='openai',
        model='text-embedding-3-small',
        budget_cap=10.0,
        dry_run=True
    )

    preview_stats = gen_preview.generate_for_table(
        table_name='layer_standards',
        text_columns=['name', 'description', 'category'],
        limit=100
    )

    print(f"  Entities to process: {preview_stats['previewed']}")
    print(f"  Estimated cost: ${preview_stats['estimated_cost']:.4f}")
    print()

    # Confirm before proceeding
    response = input("Proceed with embedding generation? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return

    print()
    print("Generating embeddings...")
    print("-" * 70)

    # Generate actual embeddings
    stats = gen.generate_for_table(
        table_name='layer_standards',
        text_columns=['name', 'description', 'category'],
        limit=100,
        batch_size=50
    )

    print()
    print("=" * 70)
    print("Results:")
    print("=" * 70)
    print(f"  Generated: {stats['generated']}")
    print(f"  Skipped (existing): {stats['skipped']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Total cost: ${stats['total_cost']:.4f}")
    print(f"  Tokens used: {stats['total_tokens']:,}")
    print()

    # Verify embeddings were created
    count = execute_query("""
        SELECT COUNT(*) as count
        FROM entity_embeddings ee
        JOIN standards_entities se ON ee.entity_id = se.entity_id
        WHERE se.entity_type = 'layer' AND ee.is_current = TRUE
    """)[0]['count']

    print(f"✓ Verified: {count} layer embeddings in database")
    print()
    print("🎉 Phase 1 Task 1.2 Complete!")
    print()
    print("Next steps:")
    print("  - Run Task 1.3: Build semantic relationships")
    print("  - Test similarity search in database")

if __name__ == '__main__':
    main()
```

**Run it**:
```bash
chmod +x scripts/phase1_generate_embeddings.py
python scripts/phase1_generate_embeddings.py
```

**Deliverable**: 100 layer standards with 1536-dimensional embeddings in `entity_embeddings` table

---

### Task 1.3: Build Initial Relationships (1 hour)

**File**: Create `scripts/phase1_build_relationships.py`

```python
#!/usr/bin/env python3
"""
Phase 1: Build semantic relationships from embeddings.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'tools'))

from relationships.graph_builder import GraphBuilder
from db_utils import execute_query

def main():
    print("=" * 70)
    print("Phase 1: Build Semantic Relationships")
    print("=" * 70)
    print()

    builder = GraphBuilder()

    # Create semantic relationships between layers
    print("Building semantic relationships...")
    print("  Similarity threshold: 0.75 (75%)")
    print("  Max relationships per entity: 5")
    print()

    stats = builder.create_semantic_relationships(
        similarity_threshold=0.75,
        entity_types=['layer'],
        limit_per_entity=5
    )

    print()
    print("=" * 70)
    print("Results:")
    print("=" * 70)
    print(f"  Relationships created: {stats['relationships_created']}")
    print(f"  Entities processed: {stats['entities_processed']}")
    print(f"  Execution time: {stats['execution_time_seconds']:.2f}s")
    print()

    # Verify relationships
    count = execute_query("""
        SELECT COUNT(*) as count
        FROM entity_relationships
        WHERE relationship_type = 'semantic'
    """)[0]['count']

    print(f"✓ Verified: {count} semantic relationships in database")
    print()

    # Show sample relationships
    print("Sample relationships:")
    print("-" * 70)
    samples = execute_query("""
        SELECT
            se1.canonical_name AS subject,
            er.predicate,
            se2.canonical_name AS object,
            er.confidence_score
        FROM entity_relationships er
        JOIN standards_entities se1 ON er.subject_entity_id = se1.entity_id
        JOIN standards_entities se2 ON er.object_entity_id = se2.entity_id
        WHERE er.relationship_type = 'semantic'
        ORDER BY er.confidence_score DESC
        LIMIT 5
    """)

    for rel in samples:
        print(f"  {rel['subject']} → {rel['predicate']} → {rel['object']}")
        print(f"    Confidence: {rel['confidence_score']:.2f}")
        print()

    print("🎉 Phase 1 Task 1.3 Complete!")

if __name__ == '__main__':
    main()
```

**Run it**:
```bash
python scripts/phase1_build_relationships.py
```

**Deliverable**: 500+ semantic relationships in `entity_relationships` table

---

### Task 1.4: Add "Find Similar" to UI (3 hours)

#### Step 1: Update Layer Standards Template

**File**: `templates/standards/layers.html`

Find the table row template (around line 120-150) and add:

```html
<!-- Existing columns -->
<td>{{ layer.name }}</td>
<td>{{ layer.description }}</td>
<td>{{ layer.color_name }}</td>

<!-- NEW: Add Find Similar button -->
<td>
    <div class="btn-group">
        <button class="btn btn-sm btn-primary"
                onclick="openEditModal('{{ layer.layer_id }}')">
            <i class="fas fa-edit"></i> Edit
        </button>
        <button class="btn btn-sm btn-secondary"
                onclick="findSimilar('{{ layer.entity_id }}', '{{ layer.name }}')">
            <i class="fas fa-search"></i> Similar
        </button>
    </div>
</td>
```

Add JavaScript at bottom of file:

```javascript
<script>
async function findSimilar(entityId, entityName) {
    try {
        // Show loading state
        showLoading('Finding similar layers...');

        // Call API
        const response = await fetch(`/api/standards/layers/${entityId}/similar`);
        if (!response.ok) throw new Error('API request failed');

        const results = await response.json();

        // Hide loading
        hideLoading();

        // Show results in modal
        showSimilarLayersModal(entityName, results);

    } catch (error) {
        console.error('Error finding similar layers:', error);
        alert('Failed to find similar layers. Check console for details.');
        hideLoading();
    }
}

function showSimilarLayersModal(originalName, results) {
    const modal = document.createElement('div');
    modal.className = 'modal fade show';
    modal.style.display = 'block';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">
                        <i class="fas fa-search"></i>
                        Layers Similar to "${originalName}"
                    </h3>
                    <button type="button" class="close" onclick="this.closest('.modal').remove()">
                        <span>&times;</span>
                    </button>
                </div>
                <div class="modal-body">
                    ${results.length === 0 ?
                        '<p class="text-muted">No similar layers found.</p>' :
                        `<table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Layer Name</th>
                                    <th>Description</th>
                                    <th>Similarity</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${results.map(r => `
                                    <tr>
                                        <td><strong>${r.canonical_name}</strong></td>
                                        <td>${r.entity_type}</td>
                                        <td>
                                            <div class="progress" style="height: 20px;">
                                                <div class="progress-bar bg-success"
                                                     style="width: ${r.similarity_score * 100}%">
                                                    ${(r.similarity_score * 100).toFixed(0)}%
                                                </div>
                                            </div>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>`
                    }
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">
                        Close
                    </button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function showLoading(message) {
    // Implement your loading indicator
    console.log(message);
}

function hideLoading() {
    // Hide loading indicator
}
</script>
```

#### Step 2: Add API Endpoint

**File**: `app.py`

Add this route (around line 800-900, with other standards routes):

```python
@app.route('/api/standards/layers/<entity_id>/similar')
def get_similar_layers(entity_id):
    """
    Find semantically similar layers using vector similarity.

    Example: User clicks "Similar" on "C-UTIL-STORM-CB-EXIST-PT"
    Returns: ["C-UTIL-STORM-INLET-EXIST-PT", "C-UTIL-DRAINAGE-CATCH-EXIST-PT", ...]
    """
    try:
        from tools.db_utils import execute_query

        # Call the database function find_similar_entities()
        results = execute_query("""
            SELECT
                entity_id,
                canonical_name,
                entity_type,
                similarity_score
            FROM find_similar_entities(
                %s::uuid,
                0.70,  -- 70% similarity threshold
                10     -- top 10 results
            )
            ORDER BY similarity_score DESC
        """, (entity_id,))

        return jsonify({
            'success': True,
            'count': len(results),
            'results': results
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

**Test it**:
1. Navigate to Standards > Layers
2. Click "Similar" on any layer
3. Should see modal with similar layers and similarity scores

**Deliverable**: Working "Find Similar" feature that users can click

---

### Task 1.5: Demo Video (1 hour)

**Script**:
1. **Intro** (15 sec): "I'll show you our new AI-powered semantic search"
2. **Before** (45 sec): Traditional keyword search for "drainage"
   - Shows only layers with "drainage" in name
   - Misses "catch basin", "inlet", "culvert"
3. **After** (90 sec): Click "Find Similar" on a storm drain layer
   - Shows semantically related layers
   - Explain similarity scores
   - Demonstrate graph visualization
4. **Impact** (30 sec): "Found 10x more relevant results in 1 click"

**Tools**:
- Screen recorder: OBS Studio (free) or QuickTime (Mac)
- Video editor: DaVinci Resolve (free) or iMovie (Mac)
- Upload to YouTube (unlisted)
- Embed in README.md

**Deliverable**: 3-minute demo video showing AI in action

---

## 🔥 Phase 2: Core Integration (Week 2-3)

**Goal**: Embed AI features into core workflows so they activate automatically

### Task 2.1: Auto-Generate Embeddings on Entity Creation (4 hours)

#### Step 1: Create Queue Table

**File**: Create `database/migrations/create_embedding_queue.sql`

```sql
-- Queue table for async embedding generation
CREATE TABLE IF NOT EXISTS embedding_generation_queue (
    queue_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id UUID NOT NULL REFERENCES standards_entities(entity_id) ON DELETE CASCADE,
    entity_type VARCHAR(100) NOT NULL,
    text_to_embed TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal',  -- high, normal, low
    status VARCHAR(20) DEFAULT 'pending',   -- pending, processing, completed, failed
    attempt_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

CREATE INDEX idx_queue_status ON embedding_generation_queue(status, priority, created_at);
CREATE INDEX idx_queue_entity ON embedding_generation_queue(entity_id);

-- Trigger function to queue embeddings
CREATE OR REPLACE FUNCTION trigger_queue_embedding()
RETURNS TRIGGER AS $$
BEGIN
    -- Only queue if entity_id exists and text is non-empty
    IF NEW.entity_id IS NOT NULL AND
       (NEW.description IS NOT NULL OR NEW.name IS NOT NULL) THEN

        INSERT INTO embedding_generation_queue (
            entity_id,
            entity_type,
            text_to_embed,
            priority
        ) VALUES (
            NEW.entity_id,
            TG_TABLE_NAME,
            COALESCE(NEW.description, '') || ' ' || COALESCE(NEW.name, ''),
            'normal'
        )
        ON CONFLICT (entity_id) DO NOTHING;  -- Prevent duplicates

    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to layer_standards
CREATE TRIGGER layer_standards_embedding_queue
    AFTER INSERT OR UPDATE ON layer_standards
    FOR EACH ROW
    WHEN (NEW.entity_id IS NOT NULL)
    EXECUTE FUNCTION trigger_queue_embedding();

-- Apply to other major tables
CREATE TRIGGER block_definitions_embedding_queue
    AFTER INSERT OR UPDATE ON block_definitions
    FOR EACH ROW
    WHEN (NEW.entity_id IS NOT NULL)
    EXECUTE FUNCTION trigger_queue_embedding();

-- Repeat for: utility_structures, survey_points, etc.
```

**Run migration**:
```bash
psql $DATABASE_URL < database/migrations/create_embedding_queue.sql
```

#### Step 2: Create Background Worker

**File**: Create `workers/embedding_worker.py`

```python
#!/usr/bin/env python3
"""
Background worker that processes embedding_generation_queue.

Run as: python workers/embedding_worker.py &
Or with systemd service (see deployment guide)
"""
import sys
import time
import signal
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'tools'))

from embeddings.embedding_generator import EmbeddingGenerator
from db_utils import execute_query, get_connection

# Global flag for graceful shutdown
running = True

def signal_handler(signum, frame):
    global running
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    running = False

def process_queue_batch(generator, batch_size=50):
    """Process a batch of pending embeddings."""

    # Mark items as processing
    execute_query("""
        UPDATE embedding_generation_queue
        SET status = 'processing'
        WHERE queue_id IN (
            SELECT queue_id
            FROM embedding_generation_queue
            WHERE status = 'pending'
            ORDER BY
                CASE priority
                    WHEN 'high' THEN 1
                    WHEN 'normal' THEN 2
                    WHEN 'low' THEN 3
                END,
                created_at ASC
            LIMIT %s
            FOR UPDATE SKIP LOCKED
        )
        RETURNING queue_id, entity_id, text_to_embed
    """, (batch_size,))

    # Get pending items
    pending = execute_query("""
        SELECT queue_id, entity_id, text_to_embed
        FROM embedding_generation_queue
        WHERE status = 'processing'
        ORDER BY created_at ASC
        LIMIT %s
    """, (batch_size,))

    if not pending:
        return 0

    print(f"Processing {len(pending)} embeddings...")

    # Generate embeddings in batch
    try:
        results = generator.generate_batch_embeddings(
            entities=[{
                'entity_id': item['entity_id'],
                'text': item['text_to_embed']
            } for item in pending]
        )

        # Mark as completed
        for item, result in zip(pending, results):
            if result.get('success'):
                execute_query("""
                    UPDATE embedding_generation_queue
                    SET status = 'completed', processed_at = CURRENT_TIMESTAMP
                    WHERE queue_id = %s
                """, (item['queue_id'],), fetch=False)
            else:
                execute_query("""
                    UPDATE embedding_generation_queue
                    SET status = 'failed',
                        attempt_count = attempt_count + 1,
                        error_message = %s
                    WHERE queue_id = %s
                """, (result.get('error'), item['queue_id']), fetch=False)

        return len([r for r in results if r.get('success')])

    except Exception as e:
        print(f"Error processing batch: {e}")
        # Mark all as failed
        execute_query("""
            UPDATE embedding_generation_queue
            SET status = 'failed',
                attempt_count = attempt_count + 1,
                error_message = %s
            WHERE status = 'processing'
        """, (str(e),), fetch=False)
        return 0

def main():
    global running

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 70)
    print("Embedding Generation Worker")
    print("=" * 70)
    print("Starting worker process...")
    print("Press Ctrl+C to stop")
    print()

    # Initialize generator
    generator = EmbeddingGenerator(
        model='text-embedding-3-small',
        budget_cap=100.0,  # $100 daily budget
        dry_run=False
    )

    print(f"✓ Initialized EmbeddingGenerator")
    print(f"  Model: {generator.model_name}")
    print(f"  Budget Cap: ${generator.budget_cap}")
    print()

    poll_interval = 10  # seconds

    while running:
        try:
            # Process batch
            processed = process_queue_batch(generator, batch_size=50)

            if processed > 0:
                print(f"✓ Processed {processed} embeddings")

                # Show queue status
                stats = execute_query("""
                    SELECT
                        status,
                        COUNT(*) as count
                    FROM embedding_generation_queue
                    GROUP BY status
                """)
                print(f"  Queue status: {stats}")

            # Sleep before next poll
            time.sleep(poll_interval)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(poll_interval)

    print("\nWorker stopped.")

if __name__ == '__main__':
    main()
```

**Run worker**:
```bash
# Terminal 1: Start worker
python workers/embedding_worker.py

# Terminal 2: Test by creating a layer
psql $DATABASE_URL -c "INSERT INTO layer_standards (name, description, category) VALUES ('TEST-LAYER', 'Test description', 'test')"

# Check queue
psql $DATABASE_URL -c "SELECT * FROM embedding_generation_queue ORDER BY created_at DESC LIMIT 5"
```

**Deliverable**: Background worker that processes embeddings within 10 seconds of entity creation

---

### Task 2.2: Integrate with DXF Import (6 hours)

**File**: `dxf_importer.py`

Find the section after entities are created (search for "intelligent objects created" or similar).

Add this function:

```python
def post_import_ai_enrichment(project_id, conn):
    """
    Run AI enrichment after DXF import.
    Called automatically after entities are created.
    """
    from tools.db_utils import execute_query

    print("\n" + "="*70)
    print("AI Enrichment Phase")
    print("="*70)

    # 1. Register new entities
    print("Registering entities...")
    registered = execute_query("""
        WITH new_entities AS (
            -- Utility lines
            SELECT
                entity_id,
                'utility_line' as entity_type,
                line_type as canonical_name,
                'utility_lines' as source_table,
                line_id as source_id
            FROM utility_lines
            WHERE project_id = %s

            UNION ALL

            -- Survey points
            SELECT
                entity_id,
                'survey_point',
                point_number,
                'survey_points',
                point_id
            FROM survey_points
            WHERE project_id = %s

            UNION ALL

            -- Utility structures
            SELECT
                entity_id,
                'utility_structure',
                structure_type,
                'utility_structures',
                structure_id
            FROM utility_structures
            WHERE project_id = %s
        )
        INSERT INTO standards_entities (
            entity_id, entity_type, canonical_name,
            source_table, source_id
        )
        SELECT * FROM new_entities
        ON CONFLICT (entity_id) DO NOTHING
        RETURNING entity_id
    """, (project_id, project_id, project_id))

    print(f"  ✓ Registered {len(registered)} entities")

    # 2. Queue for embedding generation
    print("Queueing for embedding generation...")
    queued = execute_query("""
        INSERT INTO embedding_generation_queue (
            entity_id, entity_type, text_to_embed, priority
        )
        SELECT
            se.entity_id,
            se.entity_type,
            se.canonical_name || ' ' || COALESCE(se.attributes::text, ''),
            'normal'
        FROM standards_entities se
        WHERE se.source_table IN ('utility_lines', 'survey_points', 'utility_structures')
        AND NOT EXISTS (
            SELECT 1 FROM entity_embeddings ee
            WHERE ee.entity_id = se.entity_id AND ee.is_current = TRUE
        )
        ON CONFLICT (entity_id) DO NOTHING
        RETURNING queue_id
    """)

    print(f"  ✓ Queued {len(queued)} entities for embeddings")

    # 3. Build spatial relationships (run inline, not queued)
    print("Building spatial relationships...")
    from tools.relationships.graph_builder import GraphBuilder
    builder = GraphBuilder()

    # Utility network
    stats = builder.build_utility_network_graph()
    print(f"  ✓ Created {stats.get('relationships_created', 0)} utility relationships")

    # Survey network
    stats = builder.build_survey_network_graph()
    print(f"  ✓ Created {stats.get('relationships_created', 0)} survey relationships")

    print("\n✓ AI Enrichment Complete")
    print(f"  - {len(registered)} entities registered")
    print(f"  - {len(queued)} embeddings queued (will process in ~10 seconds)")
    print(f"  - Spatial relationships created")
    print("="*70)
```

Now find where `intelligent_object_creator.py` is called (search for `process_classification_results` or similar).

After that section, add:

```python
# AI Enrichment Phase
if enable_ai_enrichment:  # Add a flag
    post_import_ai_enrichment(project_id, conn)
```

**Add checkbox to DXF import form**:

**File**: `templates/dxf_tools.html`

```html
<div class="form-check">
    <input class="form-check-input" type="checkbox" id="enableAI" name="enable_ai" checked>
    <label class="form-check-label" for="enableAI">
        <i class="fas fa-brain"></i> Enable AI Enrichment
        <small class="text-muted">(embeddings & relationships)</small>
    </label>
</div>
```

**Deliverable**: DXF imports automatically trigger AI processing

---

### Task 2.3: Hybrid Search in Advanced Search (5 hours)

**File**: `templates/advanced_search.html`

Add search mode selector (find the search form, around line 50-100):

```html
<div class="form-group">
    <label for="searchMode">
        <i class="fas fa-search"></i> Search Mode
    </label>
    <select id="searchMode" name="search_mode" class="form-control">
        <option value="keyword">Keyword (Traditional)</option>
        <option value="semantic">Semantic (AI-Powered)</option>
        <option value="hybrid" selected>Hybrid (Best of Both)</option>
    </select>
    <small class="form-text text-muted">
        Hybrid combines keyword matching with AI semantic understanding
    </small>
</div>
```

Update JavaScript fetch call:

```javascript
async function performSearch() {
    const searchMode = document.getElementById('searchMode').value;
    const query = document.getElementById('searchQuery').value;
    const entityTypes = getSelectedEntityTypes();  // Your existing function

    const response = await fetch('/api/advanced-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            query: query,
            search_mode: searchMode,
            entity_types: entityTypes,
            min_quality: 0.5
        })
    });

    const results = await response.json();
    displayResults(results);
}
```

**File**: `app.py`

Update or create `/api/advanced-search` endpoint:

```python
@app.route('/api/advanced-search', methods=['POST'])
def advanced_search():
    """
    Advanced search with keyword, semantic, or hybrid modes.
    """
    data = request.json
    search_mode = data.get('search_mode', 'keyword')
    query = data.get('query', '')
    entity_types = data.get('entity_types', [])
    min_quality = data.get('min_quality', 0.0)

    try:
        if search_mode == 'hybrid':
            # Use hybrid_search() database function
            results = execute_query("""
                SELECT
                    entity_id,
                    canonical_name,
                    entity_type,
                    quality_score,
                    text_rank,
                    vector_similarity,
                    combined_score
                FROM hybrid_search(
                    search_query := %s,
                    vector_query := (
                        SELECT embedding FROM entity_embeddings
                        WHERE entity_id = (
                            SELECT entity_id FROM standards_entities
                            WHERE canonical_name ILIKE %s LIMIT 1
                        )
                    ),
                    entity_types := %s,
                    min_quality_score := %s,
                    max_results := 100
                )
                ORDER BY combined_score DESC
            """, (query, f'%{query}%', entity_types or None, min_quality))

        elif search_mode == 'semantic':
            # Pure vector similarity search
            # First, generate embedding for query
            from tools.embeddings.embedding_generator import get_embedding
            query_embedding = get_embedding(query)

            results = execute_query("""
                SELECT
                    se.entity_id,
                    se.canonical_name,
                    se.entity_type,
                    se.quality_score,
                    1 - (ee.embedding <=> %s::vector) as similarity
                FROM entity_embeddings ee
                JOIN standards_entities se ON ee.entity_id = se.entity_id
                WHERE ee.is_current = TRUE
                  AND (%s IS NULL OR se.entity_type = ANY(%s))
                  AND 1 - (ee.embedding <=> %s::vector) > 0.60
                ORDER BY similarity DESC
                LIMIT 100
            """, (query_embedding, entity_types, entity_types or None, query_embedding))

        else:  # keyword mode
            # Traditional full-text search
            results = execute_query("""
                SELECT
                    entity_id,
                    canonical_name,
                    entity_type,
                    quality_score,
                    ts_rank(search_vector, plainto_tsquery(%s)) as rank
                FROM standards_entities
                WHERE search_vector @@ plainto_tsquery(%s)
                  AND (%s IS NULL OR entity_type = ANY(%s))
                ORDER BY rank DESC
                LIMIT 100
            """, (query, query, entity_types, entity_types or None))

        return jsonify({
            'success': True,
            'mode': search_mode,
            'count': len(results),
            'results': results
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

**Deliverable**: Advanced search with semantic/hybrid modes

---

### Task 2.4: Quality Score Automation (3 hours)

**File**: Create `database/triggers/auto_quality_scores.sql`

```sql
-- Trigger to update quality score when embedding is added
CREATE OR REPLACE FUNCTION update_quality_on_embedding()
RETURNS TRIGGER AS $$
DECLARE
    relationship_count INTEGER;
    filled_fields INTEGER;
BEGIN
    -- Count relationships
    SELECT COUNT(*) INTO relationship_count
    FROM entity_relationships
    WHERE source_entity_id = NEW.entity_id
       OR target_entity_id = NEW.entity_id;

    -- Count filled attributes (rough estimate)
    SELECT jsonb_object_keys_count(attributes) INTO filled_fields
    FROM standards_entities
    WHERE entity_id = NEW.entity_id;

    -- Update quality score
    UPDATE standards_entities
    SET quality_score = compute_quality_score(
        COALESCE(filled_fields, 0),
        10,  -- Assume 10 required fields
        TRUE,  -- has_embedding (we're in the trigger)
        relationship_count > 0
    ),
    updated_at = CURRENT_TIMESTAMP
    WHERE entity_id = NEW.entity_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER embedding_quality_update
    AFTER INSERT OR UPDATE ON entity_embeddings
    FOR EACH ROW
    WHEN (NEW.is_current = TRUE)
    EXECUTE FUNCTION update_quality_on_embedding();

-- Trigger to update quality score when relationship is added
CREATE OR REPLACE FUNCTION update_quality_on_relationship()
RETURNS TRIGGER AS $$
BEGIN
    -- Update both subject and object entities
    UPDATE standards_entities
    SET quality_score = compute_quality_score(
        (SELECT COUNT(*) FROM jsonb_object_keys(attributes)),
        10,
        EXISTS(SELECT 1 FROM entity_embeddings WHERE entity_id = standards_entities.entity_id AND is_current = TRUE),
        TRUE  -- has_relationships (we're adding one)
    ),
    updated_at = CURRENT_TIMESTAMP
    WHERE entity_id IN (NEW.subject_entity_id, NEW.object_entity_id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER relationship_quality_update
    AFTER INSERT OR UPDATE ON entity_relationships
    FOR EACH ROW
    EXECUTE FUNCTION update_quality_on_relationship();
```

**Run migration**:
```bash
psql $DATABASE_URL < database/triggers/auto_quality_scores.sql
```

**Test it**:
```sql
-- Check quality scores before
SELECT entity_id, canonical_name, quality_score FROM standards_entities LIMIT 5;

-- Add an embedding (will trigger quality update)
-- (Embeddings should be added automatically now)

-- Check quality scores after
SELECT entity_id, canonical_name, quality_score FROM standards_entities LIMIT 5;
-- Should see higher scores for entities with embeddings
```

**Deliverable**: Quality scores auto-update as embeddings/relationships are added

---

## ⚡ Phase 3: User-Facing Features (Week 4-5)

### Task 3.1: Natural Language Query Interface (8 hours)

**File**: `templates/nl_query.html` (already exists, just needs backend)

Update the form to call new API:

```javascript
async function submitNLQuery() {
    const query = document.getElementById('nlQueryInput').value;

    if (!query.trim()) {
        alert('Please enter a question');
        return;
    }

    // Show loading
    document.getElementById('results').innerHTML = '<div class="loading">Processing query...</div>';

    try {
        const response = await fetch('/api/nl-query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        const data = await response.json();

        if (data.success) {
            displayNLResults(data);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('NL query failed:', error);
        alert('Query failed. Check console.');
    }
}

function displayNLResults(data) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = `
        <div class="card mb-3">
            <div class="card-header">
                <h4>Query Understanding</h4>
            </div>
            <div class="card-body">
                <p><strong>Your question:</strong> ${data.original_query}</p>
                <p><strong>SQL generated:</strong></p>
                <pre><code class="language-sql">${data.sql}</code></pre>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h4>Results (${data.result_count})</h4>
            </div>
            <div class="card-body">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            ${Object.keys(data.results[0] || {}).map(k => `<th>${k}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${data.results.map(row => `
                            <tr>
                                ${Object.values(row).map(v => `<td>${v}</td>`).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}
```

**File**: `app.py`

Add NL query endpoint:

```python
from openai import OpenAI

# Schema context for GPT-4 (load once at startup)
SCHEMA_CONTEXT = """
You are a SQL expert for a PostgreSQL database with PostGIS and pgvector extensions.

Key tables:
- standards_entities: All entities (entity_id, canonical_name, entity_type, quality_score, tags, attributes)
- entity_embeddings: Vector embeddings (entity_id, embedding vector(1536), is_current)
- entity_relationships: Graph edges (subject_entity_id, predicate, object_entity_id, relationship_type)
- utility_lines: Pipes/conduits (line_id, entity_id, geometry, utility_system, material, diameter)
- survey_points: Survey points (point_id, entity_id, geometry, point_number, elevation)
- utility_structures: Manholes/structures (structure_id, entity_id, geometry, structure_type)

Key functions:
- find_similar_entities(entity_id, threshold, limit) - Vector similarity
- find_related_entities(entity_id, max_hops, types[]) - GraphRAG traversal
- hybrid_search(query, vector, types[], min_quality, limit) - Hybrid search
- ST_DWithin(geom1, geom2, distance) - Spatial proximity

Generate ONLY the SQL query, no explanation.
"""

@app.route('/api/nl-query', methods=['POST'])
def natural_language_query():
    """
    Convert natural language to SQL using GPT-4.

    Examples:
    - "Find all storm drains within 500ft of schools"
    - "Show me entities similar to catch basin CB-1"
    - "What utilities are connected to survey point SP-101?"
    """
    user_query = request.json.get('query', '')

    if not user_query:
        return jsonify({'success': False, 'error': 'Empty query'}), 400

    try:
        # Check for OpenAI API key
        if not os.environ.get('OPENAI_API_KEY'):
            return jsonify({
                'success': False,
                'error': 'OPENAI_API_KEY not configured'
            }), 500

        # Call GPT-4 to generate SQL
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SCHEMA_CONTEXT},
                {"role": "user", "content": f"Convert to SQL (PostgreSQL with PostGIS): {user_query}"}
            ],
            temperature=0.1,  # Low temperature for consistent SQL
            max_tokens=500
        )

        generated_sql = response.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if generated_sql.startswith('```'):
            generated_sql = generated_sql.split('```')[1]
            if generated_sql.startswith('sql'):
                generated_sql = generated_sql[3:]
        generated_sql = generated_sql.strip()

        # Safety check: Only allow SELECT queries
        if not generated_sql.upper().startswith('SELECT'):
            return jsonify({
                'success': False,
                'error': 'Only SELECT queries are allowed for safety'
            }), 400

        # Execute the query
        from tools.db_utils import execute_query
        results = execute_query(generated_sql)

        return jsonify({
            'success': True,
            'original_query': user_query,
            'sql': generated_sql,
            'result_count': len(results),
            'results': results[:100]  # Limit to 100 rows for safety
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'sql': generated_sql if 'generated_sql' in locals() else None
        }), 500
```

**Test queries**:
- "Find all catch basins"
- "Show me utilities within 100 feet of survey point SP-101"
- "What entities are similar to storm drain inlet?"
- "List all layers related to drainage"

**Deliverable**: Natural language to SQL interface

---

### Task 3.2: Smart Layer Name Suggestions (6 hours)

See detailed implementation in Phase 2 Quick Reference above.

Key files:
- API: `app.py` - `/api/suggest-layer-name`
- UI: `templates/standards/layers.html` - Autocomplete input
- JavaScript: Debounced fetch on input

**Deliverable**: Intelligent autocomplete for layer creation

---

### Task 3.3: Graph Visualization with Real Data (4 hours)

**File**: `app.py`

Fix `/api/toolkit/graph/data` endpoint:

```python
@app.route('/api/toolkit/graph/data')
def get_graph_data():
    """
    Load graph data for Vis.js visualization.
    Returns nodes (entities) and edges (relationships).
    """
    try:
        # Get entities (nodes)
        # Limit to avoid performance issues
        nodes = execute_query("""
            SELECT
                entity_id::text AS id,
                canonical_name AS label,
                entity_type AS "group",
                quality_score,
                (SELECT COUNT(*) FROM entity_embeddings
                 WHERE entity_id = se.entity_id AND is_current = TRUE) > 0 AS has_embedding,
                (SELECT COUNT(*) FROM entity_relationships
                 WHERE subject_entity_id = se.entity_id
                    OR target_entity_id = se.entity_id) AS connection_count
            FROM standards_entities se
            WHERE quality_score > 0.5  -- Only show quality entities
            ORDER BY quality_score DESC, connection_count DESC
            LIMIT 500
        """)

        # Get entity_ids for filtering edges
        entity_ids = [n['id'] for n in nodes]

        # Get relationships (edges)
        edges = execute_query("""
            SELECT
                relationship_id::text AS id,
                subject_entity_id::text AS "from",
                object_entity_id::text AS "to",
                predicate AS label,
                relationship_type,
                confidence_score,
                CASE relationship_type
                    WHEN 'spatial' THEN '#4169e1'
                    WHEN 'semantic' THEN '#10b981'
                    WHEN 'engineering' THEN '#f59e0b'
                    ELSE '#6b7280'
                END AS color
            FROM entity_relationships
            WHERE subject_entity_id::text = ANY(%s)
              AND object_entity_id::text = ANY(%s)
            LIMIT 1000
        """, (entity_ids, entity_ids))

        return jsonify({
            'success': True,
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'node_count': len(nodes),
                'edge_count': len(edges),
                'avg_quality': sum(n['quality_score'] for n in nodes) / len(nodes) if nodes else 0
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

**File**: `templates/graph.html`

The Vis.js code is already there, just needs data. Test by navigating to `/graph` in browser.

**Deliverable**: Interactive graph with 500+ nodes and relationships

---

### Task 3.4: AI Context Panel in Map Viewer (5 hours)

**File**: `templates/map_viewer.html`

Add context panel HTML (after map div):

```html
<div id="aiContextPanel" class="ai-context-panel" style="display: none;">
    <div class="panel-header">
        <h3><i class="fas fa-brain"></i> AI Context</h3>
        <button class="btn-close" onclick="closeContextPanel()">×</button>
    </div>

    <div class="panel-body">
        <div id="contextLoading" class="text-center p-4">
            <div class="spinner"></div>
            <p>Loading context...</p>
        </div>

        <div id="contextContent" style="display: none;">
            <!-- Entity Info -->
            <div class="context-section">
                <h4><i class="fas fa-info-circle"></i> Entity</h4>
                <div id="entityInfo"></div>
            </div>

            <!-- Similar Entities -->
            <div class="context-section">
                <h4><i class="fas fa-lightbulb"></i> Similar Entities</h4>
                <div id="similarEntities"></div>
            </div>

            <!-- Related (GraphRAG) -->
            <div class="context-section">
                <h4><i class="fas fa-project-diagram"></i> Related (Graph)</h4>
                <div id="relatedEntities"></div>
            </div>

            <!-- Nearby (Spatial) -->
            <div class="context-section">
                <h4><i class="fas fa-map-marker-alt"></i> Nearby</h4>
                <div id="nearbyEntities"></div>
            </div>
        </div>
    </div>
</div>

<style>
.ai-context-panel {
    position: fixed;
    right: 0;
    top: 60px;
    width: 400px;
    height: calc(100vh - 60px);
    background: rgba(15, 23, 42, 0.95);
    border-left: 2px solid rgba(59, 130, 246, 0.3);
    box-shadow: -4px 0 20px rgba(0, 0, 0, 0.3);
    z-index: 1000;
    overflow-y: auto;
}

.panel-header {
    padding: 1rem;
    border-bottom: 1px solid rgba(59, 130, 246, 0.3);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.context-section {
    padding: 1rem;
    border-bottom: 1px solid rgba(59, 130, 246, 0.1);
}

.context-section h4 {
    color: var(--color-accent-cyan);
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
}
</style>

<script>
async function showEntityContext(entityId) {
    // Show panel and loading state
    document.getElementById('aiContextPanel').style.display = 'block';
    document.getElementById('contextLoading').style.display = 'block';
    document.getElementById('contextContent').style.display = 'none';

    try {
        const response = await fetch(`/api/entity/${entityId}/context`);
        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error);
        }

        // Hide loading, show content
        document.getElementById('contextLoading').style.display = 'none';
        document.getElementById('contextContent').style.display = 'block';

        // Populate sections
        document.getElementById('entityInfo').innerHTML = renderEntityInfo(data.entity);
        document.getElementById('similarEntities').innerHTML = renderSimilarEntities(data.similar);
        document.getElementById('relatedEntities').innerHTML = renderRelatedEntities(data.related);
        document.getElementById('nearbyEntities').innerHTML = renderNearbyEntities(data.nearby);

    } catch (error) {
        console.error('Failed to load context:', error);
        alert('Failed to load AI context');
        closeContextPanel();
    }
}

function renderEntityInfo(entity) {
    return `
        <div class="entity-card">
            <p><strong>Name:</strong> ${entity.canonical_name}</p>
            <p><strong>Type:</strong> ${entity.entity_type}</p>
            <p><strong>Quality:</strong>
                <span class="quality-badge">${(entity.quality_score * 100).toFixed(0)}%</span>
            </p>
        </div>
    `;
}

function renderSimilarEntities(similar) {
    if (!similar || similar.length === 0) {
        return '<p class="text-muted">No similar entities found</p>';
    }

    return similar.map(s => `
        <div class="similar-item">
            <strong>${s.canonical_name}</strong>
            <div class="similarity-bar">
                <div class="similarity-fill" style="width: ${s.similarity_score * 100}%"></div>
                <span>${(s.similarity_score * 100).toFixed(0)}%</span>
            </div>
        </div>
    `).join('');
}

function renderRelatedEntities(related) {
    if (!related || related.length === 0) {
        return '<p class="text-muted">No related entities found</p>';
    }

    return related.map(r => `
        <div class="related-item">
            <i class="fas fa-arrow-right"></i> ${r.canonical_name}
            <small class="text-muted">(${r.hop_distance} hops)</small>
        </div>
    `).join('');
}

function renderNearbyEntities(nearby) {
    if (!nearby || nearby.length === 0) {
        return '<p class="text-muted">No nearby entities found</p>';
    }

    return nearby.map(n => `
        <div class="nearby-item">
            <i class="fas fa-map-pin"></i> ${n.canonical_name}
            <small class="text-muted">(${n.distance_ft.toFixed(1)}ft)</small>
        </div>
    `).join('');
}

function closeContextPanel() {
    document.getElementById('aiContextPanel').style.display = 'none';
}

// Hook into map click events (modify your existing map click handler)
function onMapFeatureClick(feature) {
    const entityId = feature.properties.entity_id;
    if (entityId) {
        showEntityContext(entityId);
    }
}
</script>
```

**File**: `app.py`

Add context API endpoint:

```python
@app.route('/api/entity/<entity_id>/context')
def get_entity_context(entity_id):
    """
    Get AI-powered context for an entity.
    Returns similar, related, and nearby entities.
    """
    try:
        # Get entity info
        entity = execute_query("""
            SELECT entity_id, canonical_name, entity_type, quality_score
            FROM standards_entities
            WHERE entity_id = %s
        """, (entity_id,))

        if not entity:
            return jsonify({'success': False, 'error': 'Entity not found'}), 404

        # Similar (vector similarity)
        similar = execute_query("""
            SELECT entity_id, canonical_name, entity_type, similarity_score
            FROM find_similar_entities(%s::uuid, 0.70, 5)
        """, (entity_id,))

        # Related (GraphRAG)
        related = execute_query("""
            SELECT entity_id, canonical_name, entity_type, hop_distance, relationship_path
            FROM find_related_entities(%s::uuid, 2, NULL)
        """, (entity_id,))

        # Nearby (spatial) - only if entity has geometry
        nearby = execute_query("""
            WITH entity_geom AS (
                SELECT geometry FROM survey_points WHERE entity_id = %s
                UNION ALL
                SELECT geometry FROM utility_lines WHERE entity_id = %s
                UNION ALL
                SELECT geometry FROM utility_structures WHERE entity_id = %s
            )
            SELECT
                se.entity_id,
                se.canonical_name,
                se.entity_type,
                ST_Distance(eg.geometry,
                    COALESCE(sp.geometry, ul.geometry, us.geometry)) AS distance_ft
            FROM standards_entities se
            CROSS JOIN entity_geom eg
            LEFT JOIN survey_points sp ON se.entity_id = sp.entity_id
            LEFT JOIN utility_lines ul ON se.entity_id = ul.entity_id
            LEFT JOIN utility_structures us ON se.entity_id = us.entity_id
            WHERE se.entity_id != %s
              AND ST_DWithin(eg.geometry,
                    COALESCE(sp.geometry, ul.geometry, us.geometry), 100)
            ORDER BY distance_ft
            LIMIT 10
        """, (entity_id, entity_id, entity_id, entity_id))

        return jsonify({
            'success': True,
            'entity': entity[0],
            'similar': similar,
            'related': related,
            'nearby': nearby
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

**Deliverable**: AI context panel in map viewer

---

## 🚀 Phase 4: Production-Grade (Week 6-8)

### Task 4.1: Automated Pipelines (6 hours)

**File**: Create `workers/ai_pipelines.py`

```python
#!/usr/bin/env python3
"""
Automated AI maintenance pipelines.
Run as systemd service or cron job.
"""
import sys
import time
import schedule
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent / 'tools'))

from db_utils import execute_query
from embeddings.embedding_generator import EmbeddingGenerator
from relationships.graph_builder import GraphBuilder

def refresh_materialized_views():
    """Refresh pre-computed views."""
    print(f"[{datetime.now()}] Refreshing materialized views...")

    views = [
        'mv_entity_graph_summary',
        'mv_survey_points_enriched',
        'mv_spatial_clusters'
    ]

    for view in views:
        try:
            execute_query(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}", fetch=False)
            print(f"  ✓ {view}")
        except Exception as e:
            print(f"  ✗ {view}: {e}")

    print("✓ Materialized views refreshed\n")

def generate_missing_embeddings():
    """Generate embeddings for entities that don't have them."""
    print(f"[{datetime.now()}] Generating missing embeddings...")

    gen = EmbeddingGenerator(
        model='text-embedding-3-small',
        budget_cap=50.0,  # $50 daily budget
        dry_run=False
    )

    stats = gen.refresh_embeddings(older_than_days=30)

    print(f"  Generated: {stats['generated']}")
    print(f"  Cost: ${stats['total_cost']:.4f}")
    print("✓ Embeddings updated\n")

def build_semantic_relationships():
    """Build semantic relationships from embeddings."""
    print(f"[{datetime.now()}] Building semantic relationships...")

    builder = GraphBuilder()
    stats = builder.create_semantic_relationships(
        similarity_threshold=0.75,
        limit_per_entity=5
    )

    print(f"  Created: {stats['relationships_created']}")
    print("✓ Relationships updated\n")

def update_quality_scores():
    """Recalculate all quality scores."""
    print(f"[{datetime.now()}] Updating quality scores...")

    result = execute_query("""
        UPDATE standards_entities
        SET quality_score = compute_quality_score(
            (SELECT COUNT(*) FROM jsonb_object_keys(attributes)),
            10,
            EXISTS(SELECT 1 FROM entity_embeddings WHERE entity_id = standards_entities.entity_id AND is_current = TRUE),
            EXISTS(SELECT 1 FROM entity_relationships WHERE subject_entity_id = standards_entities.entity_id OR target_entity_id = standards_entities.entity_id)
        )
        WHERE updated_at < CURRENT_DATE - INTERVAL '7 days'
        RETURNING entity_id
    """)

    print(f"  Updated: {len(result)} entities")
    print("✓ Quality scores updated\n")

def cleanup_old_queue_items():
    """Clean up old completed/failed queue items."""
    print(f"[{datetime.now()}] Cleaning up old queue items...")

    result = execute_query("""
        DELETE FROM embedding_generation_queue
        WHERE status IN ('completed', 'failed')
          AND processed_at < CURRENT_DATE - INTERVAL '30 days'
        RETURNING queue_id
    """)

    print(f"  Deleted: {len(result)} old queue items")
    print("✓ Cleanup complete\n")

def main():
    print("=" * 70)
    print("AI Pipelines Scheduler")
    print("=" * 70)
    print("Starting automated pipelines...")
    print()

    # Schedule jobs
    schedule.every().day.at("02:00").do(refresh_materialized_views)
    schedule.every().day.at("03:00").do(generate_missing_embeddings)
    schedule.every().week.at("04:00").do(build_semantic_relationships)
    schedule.every().day.at("05:00").do(update_quality_scores)
    schedule.every().week.at("06:00").do(cleanup_old_queue_items)

    print("Scheduled jobs:")
    print("  - 02:00 daily: Refresh materialized views")
    print("  - 03:00 daily: Generate missing embeddings")
    print("  - 04:00 weekly: Build semantic relationships")
    print("  - 05:00 daily: Update quality scores")
    print("  - 06:00 weekly: Cleanup old queue items")
    print()

    # Run once on startup
    print("Running initial jobs...")
    refresh_materialized_views()

    # Main loop
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == '__main__':
    main()
```

**Systemd Service** (Linux):

**File**: `/etc/systemd/system/acad-gis-ai-pipelines.service`

```ini
[Unit]
Description=ACAD-GIS AI Pipelines
After=postgresql.service network.target
Wants=postgresql.service

[Service]
Type=simple
User=acad-gis
WorkingDirectory=/home/user/survey-data-system
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 workers/ai_pipelines.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start**:
```bash
sudo systemctl enable acad-gis-ai-pipelines
sudo systemctl start acad-gis-ai-pipelines
sudo systemctl status acad-gis-ai-pipelines
```

**Deliverable**: Fully automated AI maintenance running 24/7

---

### Task 4.2: Cost Monitoring & Alerts (4 hours)

**File**: Create `tools/cost_monitor.py`

```python
#!/usr/bin/env python3
"""Monitor OpenAI API costs and send alerts."""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent))

from db_utils import execute_query

def check_budget():
    """Check embedding generation costs."""

    # Get costs for last 30 days
    summary = execute_query("""
        SELECT
            COUNT(*) as embedding_count,
            SUM(ee.tokens_used * em.cost_per_1k_tokens / 1000.0) as total_cost,
            MAX(ee.created_at) as last_generated,
            em.model_name
        FROM entity_embeddings ee
        JOIN embedding_models em ON ee.model_id = em.model_id
        WHERE ee.created_at >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY em.model_name
    """)

    if not summary:
        print("No embeddings generated in last 30 days")
        return

    total_cost = sum(s['total_cost'] or 0 for s in summary)
    total_count = sum(s['embedding_count'] for s in summary)

    print("=" * 70)
    print("Cost Summary (Last 30 Days)")
    print("=" * 70)
    print(f"Total embeddings: {total_count:,}")
    print(f"Total cost: ${total_cost:.2f}")
    print()

    for s in summary:
        print(f"  {s['model_name']}: {s['embedding_count']:,} embeddings, ${s['total_cost']:.2f}")

    # Check against budget thresholds
    budget_cap = 100.0  # $100/month

    if total_cost > budget_cap:
        send_alert(f"🚨 BUDGET EXCEEDED: ${total_cost:.2f} / ${budget_cap:.2f}", 'critical')
    elif total_cost > budget_cap * 0.90:
        send_alert(f"⚠️  Budget at 90%: ${total_cost:.2f} / ${budget_cap:.2f}", 'warning')
    elif total_cost > budget_cap * 0.75:
        send_alert(f"ℹ️  Budget at 75%: ${total_cost:.2f} / ${budget_cap:.2f}", 'info')

    return summary

def send_alert(message, level='info'):
    """Send alert via email or webhook."""
    print(f"\n[{level.upper()}] {message}\n")

    # TODO: Implement email sending
    # import smtplib
    # send_email(subject=f"ACAD-GIS Cost Alert ({level})", body=message)

    # TODO: Implement webhook (Slack, Discord, etc.)
    # requests.post(WEBHOOK_URL, json={'text': message})

if __name__ == '__main__':
    check_budget()
```

**Cron Job** (run daily at 9 AM):
```bash
0 9 * * * cd /home/user/survey-data-system && python tools/cost_monitor.py >> /var/log/acad-gis-cost.log 2>&1
```

**Deliverable**: Daily cost monitoring with email alerts

---

### Task 4.3: Analytics Dashboard (8 hours)

**File**: Create `templates/ai_analytics.html`

```html
{% extends "base.html" %}

{% block title %}AI Analytics{% endblock %}

{% block content %}
<div class="page-header">
    <h1><i class="fas fa-chart-line"></i> AI Analytics Dashboard</h1>
    <button class="btn btn-primary" onclick="refreshData()">
        <i class="fas fa-sync-alt"></i> Refresh
    </button>
</div>

<!-- KPI Cards -->
<div class="metrics-grid">
    <div class="metric-card">
        <div class="metric-icon"><i class="fas fa-vector-square"></i></div>
        <div class="metric-value" id="totalEmbeddings">-</div>
        <div class="metric-label">Total Embeddings</div>
    </div>

    <div class="metric-card">
        <div class="metric-icon"><i class="fas fa-project-diagram"></i></div>
        <div class="metric-value" id="totalRelationships">-</div>
        <div class="metric-label">Relationships</div>
    </div>

    <div class="metric-card">
        <div class="metric-icon"><i class="fas fa-percent"></i></div>
        <div class="metric-value" id="embeddingCoverage">-</div>
        <div class="metric-label">Embedding Coverage</div>
    </div>

    <div class="metric-card">
        <div class="metric-icon"><i class="fas fa-dollar-sign"></i></div>
        <div class="metric-value" id="monthlyCost">-</div>
        <div class="metric-label">Monthly Cost</div>
    </div>
</div>

<!-- Charts -->
<div class="charts-grid">
    <!-- Coverage by Entity Type -->
    <div class="card">
        <h3 class="card-title">Embedding Coverage by Type</h3>
        <canvas id="coverageChart"></canvas>
    </div>

    <!-- Quality Distribution -->
    <div class="card">
        <h3 class="card-title">Quality Score Distribution</h3>
        <canvas id="qualityChart"></canvas>
    </div>

    <!-- Relationship Types -->
    <div class="card">
        <h3 class="card-title">Relationship Types</h3>
        <canvas id="relationshipChart"></canvas>
    </div>

    <!-- Cost Over Time -->
    <div class="card">
        <h3 class="card-title">Cost Trend (30 Days)</h3>
        <canvas id="costChart"></canvas>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
let charts = {};

async function loadAnalytics() {
    const response = await fetch('/api/ai-analytics');
    const data = await response.json();

    // Update KPIs
    document.getElementById('totalEmbeddings').textContent = data.total_embeddings.toLocaleString();
    document.getElementById('totalRelationships').textContent = data.total_relationships.toLocaleString();
    document.getElementById('embeddingCoverage').textContent = (data.embedding_coverage * 100).toFixed(1) + '%';
    document.getElementById('monthlyCost').textContent = '$' + data.monthly_cost.toFixed(2);

    // Render charts
    renderCoverageChart(data.coverage_by_type);
    renderQualityChart(data.quality_distribution);
    renderRelationshipChart(data.relationship_types);
    renderCostChart(data.cost_trend);
}

function renderCoverageChart(data) {
    const ctx = document.getElementById('coverageChart').getContext('2d');

    if (charts.coverage) charts.coverage.destroy();

    charts.coverage = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.entity_type),
            datasets: [{
                label: 'With Embeddings',
                data: data.map(d => d.with_embeddings),
                backgroundColor: 'rgba(59, 130, 246, 0.6)'
            }, {
                label: 'Without Embeddings',
                data: data.map(d => d.total - d.with_embeddings),
                backgroundColor: 'rgba(107, 114, 128, 0.3)'
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: { stacked: true },
                y: { stacked: true }
            }
        }
    });
}

function renderQualityChart(data) {
    const ctx = document.getElementById('qualityChart').getContext('2d');

    if (charts.quality) charts.quality.destroy();

    charts.quality = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['0-25%', '25-50%', '50-75%', '75-100%'],
            datasets: [{
                data: [
                    data.q1_count,
                    data.q2_count,
                    data.q3_count,
                    data.q4_count
                ],
                backgroundColor: [
                    'rgba(239, 68, 68, 0.6)',
                    'rgba(245, 158, 11, 0.6)',
                    'rgba(59, 130, 246, 0.6)',
                    'rgba(16, 185, 129, 0.6)'
                ]
            }]
        }
    });
}

// Load on page load
document.addEventListener('DOMContentLoaded', loadAnalytics);
function refreshData() {
    loadAnalytics();
}
</script>

{% endblock %}
```

**File**: `app.py`

```python
@app.route('/api/ai-analytics')
def ai_analytics():
    """Get AI analytics data."""
    try:
        # Total counts
        totals = execute_query("""
            SELECT
                (SELECT COUNT(*) FROM entity_embeddings WHERE is_current = TRUE) as total_embeddings,
                (SELECT COUNT(*) FROM entity_relationships) as total_relationships,
                (SELECT COUNT(*) FROM standards_entities) as total_entities
        """)[0]

        # Coverage by type
        coverage = execute_query("""
            SELECT
                se.entity_type,
                COUNT(*) as total,
                COUNT(ee.entity_id) as with_embeddings
            FROM standards_entities se
            LEFT JOIN (
                SELECT DISTINCT entity_id
                FROM entity_embeddings
                WHERE is_current = TRUE
            ) ee ON se.entity_id = ee.entity_id
            GROUP BY se.entity_type
            ORDER BY total DESC
        """)

        # Quality distribution
        quality = execute_query("""
            SELECT
                SUM(CASE WHEN quality_score < 0.25 THEN 1 ELSE 0 END) as q1_count,
                SUM(CASE WHEN quality_score >= 0.25 AND quality_score < 0.5 THEN 1 ELSE 0 END) as q2_count,
                SUM(CASE WHEN quality_score >= 0.5 AND quality_score < 0.75 THEN 1 ELSE 0 END) as q3_count,
                SUM(CASE WHEN quality_score >= 0.75 THEN 1 ELSE 0 END) as q4_count
            FROM standards_entities
        """)[0]

        # Relationship types
        relationships = execute_query("""
            SELECT relationship_type, COUNT(*) as count
            FROM entity_relationships
            GROUP BY relationship_type
        """)

        # Cost trend (last 30 days)
        cost_trend = execute_query("""
            SELECT
                DATE(ee.created_at) as date,
                COUNT(*) as embeddings,
                SUM(ee.tokens_used * em.cost_per_1k_tokens / 1000.0) as cost
            FROM entity_embeddings ee
            JOIN embedding_models em ON ee.model_id = em.model_id
            WHERE ee.created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(ee.created_at)
            ORDER BY date
        """)

        monthly_cost = sum(d['cost'] or 0 for d in cost_trend)

        return jsonify({
            'total_embeddings': totals['total_embeddings'],
            'total_relationships': totals['total_relationships'],
            'total_entities': totals['total_entities'],
            'embedding_coverage': totals['total_embeddings'] / max(totals['total_entities'], 1),
            'monthly_cost': monthly_cost,
            'coverage_by_type': coverage,
            'quality_distribution': quality,
            'relationship_types': relationships,
            'cost_trend': cost_trend
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**Deliverable**: Executive dashboard for AI adoption and costs

---

### Task 4.4: Documentation & Training (6 hours)

**File**: Create `AI_QUICKSTART.md`

```markdown
# AI Features Quick Start Guide

Get started with AI embeddings and Graph RAG in 5 minutes.

## Prerequisites

- PostgreSQL database with pgvector extension
- OpenAI API key
- ACAD-GIS system installed

## 1. Set OpenAI API Key

```bash
cd /home/user/survey-data-system
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
```

Get your API key from: https://platform.openai.com/api-keys

## 2. Run Health Check

```bash
python tools/health_check.py
```

Expected output: All checks should pass ✓

## 3. Generate Initial Embeddings

```bash
python scripts/phase1_generate_embeddings.py
```

This will:
- Generate embeddings for 100 layer standards
- Cost: ~$0.20
- Time: ~30 seconds

## 4. Build Relationships

```bash
python scripts/phase1_build_relationships.py
```

This creates semantic relationships between similar entities.

## 5. Try It Out!

Navigate to:
- **Standards > Layers** - Click "Find Similar" on any layer
- **Advanced Search** - Select "Hybrid" search mode
- **Knowledge Graph** - View relationship visualization
- **AI Analytics** - See adoption metrics

## What's Next?

- Enable auto-embedding for DXF imports
- Set up natural language queries
- Configure automated nightly pipelines

See `AI_FEATURES_GUIDE.md` for detailed instructions.
```

**File**: Create `AI_FEATURES_GUIDE.md` (full user manual)

**File**: Create video tutorial script and record

**Deliverable**: Complete documentation and training materials

---

## Success Metrics Summary

### Phase 1 (Week 1)
- [ ] 100+ embeddings generated
- [ ] 500+ relationships created
- [ ] "Find Similar" button working
- [ ] Demo video recorded
- **Metric**: Users can find similar entities in <1 second

### Phase 2 (Week 3)
- [ ] DXF imports auto-trigger embeddings
- [ ] Hybrid search functional
- [ ] Quality scores auto-updating
- [ ] 1,000+ embeddings in database
- **Metric**: 80% of new entities get embeddings within 1 hour

### Phase 3 (Week 5)
- [ ] Natural language queries working
- [ ] Smart autocomplete live
- [ ] Graph visualization with 500+ nodes
- [ ] AI context panel in map
- **Metric**: 50% of searches use semantic/hybrid mode

### Phase 4 (Week 8)
- [ ] Automated pipelines running
- [ ] Cost monitoring active
- [ ] Analytics dashboard deployed
- [ ] Documentation complete
- **Metric**: System runs with <5 minutes/day manual intervention

---

## Cost Projection

### Initial Setup
- First 1,000 embeddings: ~$2
- First 10,000 embeddings: ~$20

### Ongoing (Monthly)
- New/updated embeddings: ~$2-5
- Total monthly: ~$5-10

### Total Year 1
- Initial: ~$20-30
- Ongoing: ~$60-120
- **Total: $80-150/year**

---

## Next Steps

1. **Review** this plan with stakeholders
2. **Approve** OpenAI budget ($50 initial cap)
3. **Start** with Phase 1 this week
4. **Demonstrate** value with working demo
5. **Decide** on full rollout (Phases 2-4)

---

**Questions?** See `AI_EMBEDDING_GRAPH_RAG_AUDIT.md` for detailed analysis.

**Ready to start?** Begin with Task 1.1: Environment Setup!
