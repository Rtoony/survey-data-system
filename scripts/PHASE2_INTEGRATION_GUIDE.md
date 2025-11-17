# Phase 2 Integration Guide
**Hybrid Search & Auto-Embedding Integration**

This guide shows you how to integrate Phase 2 AI features into your application.

---

## 📋 **What You're Adding**

After Phase 2 integration, your app will have:

- ✅ **Hybrid Search API** - Combines text + vector + quality scoring
- ✅ **Auto-Embedding on DXF Import** - Intelligent objects get embeddings automatically
- ✅ **Enhanced Search UI** - Shows AI similarity scores with visual breakdown
- ✅ **Background Processing** - Worker handles embeddings asynchronously

---

## 🔧 **Integration Steps**

### **Step 1: Add Hybrid Search API Endpoint** (5 minutes)

**File**: `app.py`

**Location**: Add after the existing `/api/search/execute` endpoint (around line 21180)

```python
@app.route('/api/search/hybrid', methods=['POST'])
def execute_hybrid_search():
    """Execute a hybrid search combining full-text, vector, and quality scoring"""
    try:
        data = request.get_json()
        query_text = data.get('query')
        entity_types = data.get('entity_types', ['layer', 'block', 'detail'])
        limit = data.get('limit', 20)
        filters = data.get('filters', {})

        if not query_text:
            return jsonify({'error': 'query text is required'}), 400

        # Build filters for the hybrid_search function
        filter_clause = ""
        params = [query_text, limit]

        # Add entity type filter
        if entity_types:
            filter_clause += " AND se.entity_type = ANY(%s)"
            params.append(entity_types)

        # Add project filter if specified
        if filters.get('project_id'):
            filter_clause += " AND se.source_project_id = %s"
            params.append(filters['project_id'])

        # Execute hybrid search
        query = f"""
            SELECT
                entity_id,
                canonical_name,
                entity_type,
                description,
                combined_score,
                text_score,
                vector_score,
                quality_score,
                source_table,
                source_id
            FROM hybrid_search(%s, %s)
            WHERE 1=1 {filter_clause}
            ORDER BY combined_score DESC
        """

        start_time = datetime.now()
        results = execute_query(query, params)
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

        # Save to search history
        history_query = """
            INSERT INTO search_history
            (entity_type, filter_config, result_count, execution_time_ms, executed_by, search_query)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING search_id
        """
        history_result = execute_query(
            history_query,
            ('hybrid_search', json.dumps(filters), len(results) if results else 0,
             execution_time, 'system', query_text)
        )

        search_id = history_result[0]['search_id'] if history_result else None

        return jsonify({
            'results': results if results else [],
            'count': len(results) if results else 0,
            'execution_time_ms': execution_time,
            'search_id': str(search_id) if search_id else None,
            'query': query_text,
            'filters': filters
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**What this does:**
- Creates `/api/search/hybrid` endpoint
- Uses the `hybrid_search()` database function from Phase 1
- Returns results with text, vector, and quality scores
- Saves search to history for analytics

---

### **Step 2: Add DXF Import Embedding Queue** (10 minutes)

**File**: `dxf_importer.py`

**Part A**: Add new method to the `DXFImporter` class (after `_create_intelligent_objects` method):

```python
def _queue_embeddings_for_intelligent_objects(self, project_id: str, conn, object_count: int):
    """
    Queue embeddings for newly created intelligent objects.
    This ensures AI enrichment happens automatically after DXF import.

    Args:
        project_id: UUID of the project
        conn: Database connection
        object_count: Number of intelligent objects created

    Returns:
        Number of embeddings queued
    """
    if object_count == 0:
        return 0

    cur = conn.cursor()

    try:
        # Queue embeddings for recently created entities from this project
        # that don't already have embeddings
        cur.execute("""
            INSERT INTO embedding_generation_queue (
                entity_id,
                entity_type,
                text_to_embed,
                priority
            )
            SELECT
                se.entity_id,
                se.entity_type,
                COALESCE(se.canonical_name || ' - ' || se.description, se.canonical_name) as text,
                'high'::varchar  -- High priority for DXF imports
            FROM standards_entities se
            WHERE se.source_project_id = %s
              AND se.created_at >= NOW() - INTERVAL '10 minutes'
              AND NOT EXISTS (
                  SELECT 1 FROM entity_embeddings ee
                  WHERE ee.entity_id = se.entity_id
                    AND ee.is_current = TRUE
              )
              AND NOT EXISTS (
                  SELECT 1 FROM embedding_generation_queue q
                  WHERE q.entity_id = se.entity_id
                    AND q.status IN ('pending', 'processing')
              )
            ON CONFLICT (entity_id)
            DO UPDATE SET
                priority = 'high',
                status = 'pending',
                created_at = CURRENT_TIMESTAMP
        """, (project_id,))

        queued_count = cur.rowcount
        cur.close()

        return queued_count

    except Exception as e:
        print(f"Warning: Failed to queue embeddings: {e}")
        return 0
```

**Part B**: Modify `_create_intelligent_objects` method to call the queue function.

Find this section (around line 170-180):

```python
# Create intelligent objects (existing code)
creator = IntelligentObjectCreator(self.db_config)
created_count = creator.create_objects_from_entities(entities, project_id, conn)

return created_count
```

**Replace with**:

```python
# Create intelligent objects (existing code)
creator = IntelligentObjectCreator(self.db_config)
created_count = creator.create_objects_from_entities(entities, project_id, conn)

# NEW CODE: Queue embeddings for AI enrichment
queued_count = self._queue_embeddings_for_intelligent_objects(
    project_id, conn, created_count
)

if queued_count > 0:
    print(f"  ✓ Queued {queued_count} entities for AI embedding generation")

return created_count
```

**What this does:**
- Automatically queues embeddings after DXF import
- High priority for fast processing
- Only queues entities that don't have embeddings yet
- Prevents duplicates

---

### **Step 3: Update Advanced Search UI** (15 minutes)

**File**: `templates/advanced_search.html`

**Part A**: Add search results container (if not already present)

Find the section with search filters and add this after the filters card:

```html
<!-- Search Statistics -->
<div id="searchStats"></div>

<!-- Search Results -->
<div id="searchResults" class="search-results-container">
    <p class="text-muted">Enter a search query to see results</p>
</div>
```

**Part B**: Add JavaScript for hybrid search

Add this `<script>` block before the closing `</body>` tag:

```html
<script>
/**
 * Execute hybrid search combining text, vector, and quality scoring
 */
async function executeHybridSearch() {
    const queryText = document.getElementById('searchTextInput').value;
    const entityType = document.getElementById('entityTypeSelect').value;
    const projectId = document.getElementById('projectFilter').value;

    if (!queryText || queryText.trim().length < 2) {
        showNotification('Please enter at least 2 characters to search', 'warning');
        return;
    }

    // Show loading state
    const resultsContainer = document.getElementById('searchResults');
    resultsContainer.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Searching...</div>';

    try {
        const response = await fetch('/api/search/hybrid', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: queryText,
                entity_types: [entityType],
                limit: 50,
                filters: {
                    project_id: projectId || null
                }
            })
        });

        if (!response.ok) {
            throw new Error(`Search failed: ${response.statusText}`);
        }

        const data = await response.json();

        // Display results
        displayHybridResults(data.results, data.execution_time_ms);

        // Show stats
        showSearchStats(data.count, data.execution_time_ms, queryText);

    } catch (error) {
        console.error('Hybrid search error:', error);
        resultsContainer.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                Search failed: ${error.message}
            </div>
        `;
    }
}

/**
 * Display hybrid search results with score breakdown
 */
function displayHybridResults(results, executionTime) {
    const container = document.getElementById('searchResults');

    if (!results || results.length === 0) {
        container.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search"></i>
                <p>No results found</p>
            </div>
        `;
        return;
    }

    let html = '<div class="search-results-list">';

    results.forEach(result => {
        // Calculate score percentages for visualization
        const textPercent = (result.text_score * 100).toFixed(0);
        const vectorPercent = (result.vector_score * 100).toFixed(0);
        const qualityPercent = (result.quality_score * 100).toFixed(0);
        const combinedPercent = (result.combined_score * 100).toFixed(0);

        html += `
            <div class="result-card" data-entity-id="${result.entity_id}">
                <div class="result-header">
                    <div class="result-title">
                        <i class="fas fa-${getEntityIcon(result.entity_type)}"></i>
                        <strong>${result.canonical_name}</strong>
                    </div>
                    <div class="result-score" title="Combined relevance score">
                        ${combinedPercent}%
                    </div>
                </div>

                <div class="result-body">
                    <div class="result-type">
                        <span class="badge">${result.entity_type}</span>
                        <span class="text-muted">${result.source_table}</span>
                    </div>
                    ${result.description ? `<p class="result-description">${result.description}</p>` : ''}
                </div>

                <div class="result-scores">
                    <div class="score-breakdown">
                        <div class="score-item" title="Text match score">
                            <i class="fas fa-font"></i>
                            <div class="score-bar">
                                <div class="score-fill" style="width: ${textPercent}%"></div>
                            </div>
                            <span>${textPercent}%</span>
                        </div>
                        <div class="score-item" title="AI similarity score">
                            <i class="fas fa-brain"></i>
                            <div class="score-bar">
                                <div class="score-fill" style="width: ${vectorPercent}%"></div>
                            </div>
                            <span>${vectorPercent}%</span>
                        </div>
                        <div class="score-item" title="Data quality score">
                            <i class="fas fa-star"></i>
                            <div class="score-bar">
                                <div class="score-fill" style="width: ${qualityPercent}%"></div>
                            </div>
                            <span>${qualityPercent}%</span>
                        </div>
                    </div>
                </div>

                <div class="result-actions">
                    <button class="btn-link" onclick="viewEntityDetails('${result.entity_id}')">
                        <i class="fas fa-eye"></i> View Details
                    </button>
                    <button class="btn-link" onclick="findSimilar('${result.entity_id}')">
                        <i class="fas fa-network-wired"></i> Find Similar
                    </button>
                </div>
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
}

/**
 * Get icon for entity type
 */
function getEntityIcon(entityType) {
    const icons = {
        'layer': 'layer-group',
        'block': 'cube',
        'detail': 'info-circle',
        'utility_structure': 'hard-hat',
        'survey_point': 'map-marker-alt'
    };
    return icons[entityType] || 'database';
}

/**
 * Show search statistics
 */
function showSearchStats(count, executionTime, query) {
    const statsContainer = document.getElementById('searchStats');
    if (statsContainer) {
        statsContainer.innerHTML = `
            <div class="search-stats">
                <span><strong>${count}</strong> results</span>
                <span class="separator">•</span>
                <span>${executionTime}ms</span>
                <span class="separator">•</span>
                <span class="text-muted">Hybrid Search: "${query}"</span>
            </div>
        `;
    }
}

/**
 * Find similar entities using Graph RAG
 */
async function findSimilar(entityId) {
    console.log('Finding similar entities for:', entityId);
    // Will be implemented in Phase 3
    alert('Graph RAG similarity coming in Phase 3!');
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchTextInput');
    const searchButton = document.getElementById('executeSearchBtn');

    if (searchInput) {
        // Debounced search on typing
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (this.value.length >= 2) {
                    executeHybridSearch();
                }
            }, 500);
        });

        // Search on Enter key
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                executeHybridSearch();
            }
        });
    }

    if (searchButton) {
        searchButton.addEventListener('click', executeHybridSearch);
    }
});
</script>
```

**Part C**: Add CSS styles

Add this `<style>` block in the `<head>` section or in your CSS file:

```html
<style>
/* Hybrid Search Result Styles */
.search-results-container {
    margin-top: 20px;
}

.result-card {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    transition: box-shadow 0.2s, transform 0.2s;
}

.result-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    transform: translateY(-2px);
}

.result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.result-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
}

.result-title i {
    color: #2196F3;
}

.result-score {
    font-size: 24px;
    font-weight: bold;
    color: #4CAF50;
}

.result-body {
    margin-bottom: 12px;
}

.result-type {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}

.result-description {
    color: #666;
    font-size: 14px;
    margin: 8px 0;
    line-height: 1.5;
}

.result-scores {
    background: #f8f9fa;
    border-radius: 6px;
    padding: 12px;
    margin-bottom: 12px;
}

.score-breakdown {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.score-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
}

.score-item i {
    width: 16px;
    color: #666;
}

.score-bar {
    flex: 1;
    height: 6px;
    background: #e0e0e0;
    border-radius: 3px;
    overflow: hidden;
}

.score-fill {
    height: 100%;
    background: linear-gradient(90deg, #4CAF50, #8BC34A);
    transition: width 0.3s ease;
}

.score-item span {
    min-width: 40px;
    text-align: right;
    color: #666;
    font-weight: 500;
}

.result-actions {
    display: flex;
    gap: 16px;
    padding-top: 12px;
    border-top: 1px solid #e0e0e0;
}

.btn-link {
    background: none;
    border: none;
    color: #2196F3;
    cursor: pointer;
    padding: 4px 0;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 4px;
    transition: color 0.2s;
}

.btn-link:hover {
    color: #1976D2;
    text-decoration: underline;
}

.badge {
    background: #E3F2FD;
    color: #1976D2;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
}

.search-stats {
    padding: 12px 16px;
    background: #f8f9fa;
    border-radius: 6px;
    margin-bottom: 16px;
    font-size: 14px;
    color: #666;
    display: flex;
    align-items: center;
    gap: 8px;
}

.search-stats .separator {
    color: #ccc;
}

.search-stats .text-muted {
    color: #999;
}

.loading-spinner {
    text-align: center;
    padding: 60px 20px;
    color: #666;
    font-size: 16px;
}

.loading-spinner i {
    font-size: 32px;
    margin-bottom: 12px;
}

.no-results {
    text-align: center;
    padding: 60px 20px;
    color: #999;
}

.no-results i {
    font-size: 48px;
    margin-bottom: 16px;
    opacity: 0.3;
}

.error-message {
    background: #FFEBEE;
    color: #C62828;
    padding: 20px;
    border-radius: 6px;
    text-align: center;
    font-size: 14px;
}

.error-message i {
    margin-right: 8px;
}
</style>
```

---

## ✅ **Testing the Integration**

### **Test 1: Hybrid Search API**

```bash
# Test the API endpoint directly
curl -X POST http://localhost:5000/api/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "query": "storm drain",
    "entity_types": ["layer"],
    "limit": 10
  }'
```

**Expected**: JSON response with results and score breakdown

---

### **Test 2: UI Search**

1. Navigate to `/tools/advanced-search`
2. Enter "storm" in search box
3. Wait 500ms (debounced search triggers)
4. See results with visual score breakdown

**Expected**:
- Results appear within 1-2 seconds
- Each result shows 3 score bars (text, AI, quality)
- Combined score displayed prominently

---

### **Test 3: DXF Import Auto-Queue**

```bash
# Import a DXF file
curl -X POST http://localhost:5000/api/dxf/import \
  -F "file=@test.dxf" \
  -F "project_id=YOUR_PROJECT_ID"
```

**Check queue**:
```sql
SELECT COUNT(*) FROM embedding_generation_queue
WHERE status = 'pending'
  AND priority = 'high';
```

**Expected**: Queue items created for intelligent objects

---

### **Test 4: Background Worker Processing**

```bash
# Check worker is running
ps aux | grep embedding_worker

# Watch logs
tail -f /var/log/embedding_worker.log
```

**Expected**: Worker processes queue items within 10 seconds

---

## 🐛 **Troubleshooting**

### **Issue: "hybrid_search function does not exist"**

**Solution**: Apply Phase 1 database migrations first
```bash
psql "$DATABASE_URL" < database/migrations/phase1_hybrid_search.sql
```

### **Issue: "embedding_generation_queue table does not exist"**

**Solution**: Apply Phase 2 migration
```bash
psql "$DATABASE_URL" < database/migrations/phase2_01_embedding_queue.sql
```

### **Issue: Search returns no results**

**Check 1**: Embeddings exist?
```sql
SELECT COUNT(*) FROM entity_embeddings WHERE is_current = TRUE;
```

**Check 2**: Text search working?
```sql
SELECT * FROM hybrid_search('storm', 10);
```

### **Issue: DXF import doesn't queue embeddings**

**Check 1**: Queue table exists?
```sql
\dt embedding_generation_queue
```

**Check 2**: Method was added?
```python
# In dxf_importer.py
hasattr(DXFImporter, '_queue_embeddings_for_intelligent_objects')
```

---

## 📊 **Success Criteria**

Phase 2 integration is successful when:

- [x] Hybrid search API endpoint responds
- [x] Advanced Search UI shows score breakdowns
- [x] DXF import auto-queues embeddings
- [x] Background worker processes queue
- [x] Results ranked by combined score

---

## 📈 **Next Steps**

### **Immediate**
1. ✅ Test hybrid search with real queries
2. ✅ Import DXF and verify auto-queueing
3. ✅ Monitor worker performance

### **Phase 3 (Next)**
- Natural language query interface
- Graph visualization
- "Find Similar" functionality
- AI context panel

---

## 💰 **Cost Impact**

| Feature | Cost |\n|---------|------|\n| Hybrid Search | $0 (uses existing embeddings) |
| DXF Auto-Queue | ~$0.0001-0.001 per import |
| Background Worker | ~$0.01-5.00/day depending on volume |

**Budget cap**: Worker has $100/day default cap

---

**Created**: November 17, 2025
**Phase**: 2 of 4 (Auto-Integration)
**Estimated Integration Time**: 30 minutes
**Prerequisites**: Phase 1 completed, worker running
