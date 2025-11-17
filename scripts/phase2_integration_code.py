#!/usr/bin/env python3
"""
Phase 2 - Integration Code for Application

This script contains the code snippets to integrate into your application:
1. Hybrid search API endpoint
2. DXF import embedding queue trigger
3. Frontend JavaScript for hybrid search UI

These are copy-paste ready implementations for Phase 2.
"""

# ============================================
# 1. API ENDPOINT FOR HYBRID SEARCH
# ============================================
# Add this to app.py after the existing /api/search/execute endpoint (around line 21180)

HYBRID_SEARCH_ENDPOINT = """
@app.route('/api/search/hybrid', methods=['POST'])
def execute_hybrid_search():
    \"\"\"Execute a hybrid search combining full-text, vector, and quality scoring\"\"\"
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
        query = f\"\"\"
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
        \"\"\"

        start_time = datetime.now()
        results = execute_query(query, params)
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

        # Save to search history
        history_query = \"\"\"
            INSERT INTO search_history
            (entity_type, filter_config, result_count, execution_time_ms, executed_by, search_query)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING search_id
        \"\"\"
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
"""

# ============================================
# 2. DXF IMPORT EMBEDDING QUEUE INTEGRATION
# ============================================
# Add this method to the DXFImporter class in dxf_importer.py
# Place it after the _create_intelligent_objects method (around line 180)

DXF_QUEUE_INTEGRATION = """
def _queue_embeddings_for_intelligent_objects(self, project_id: str, conn, object_count: int):
    \"\"\"
    Queue embeddings for newly created intelligent objects.
    This ensures AI enrichment happens automatically after DXF import.

    Args:
        project_id: UUID of the project
        conn: Database connection
        object_count: Number of intelligent objects created

    Returns:
        Number of embeddings queued
    \"\"\"
    if object_count == 0:
        return 0

    cur = conn.cursor()

    try:
        # Queue embeddings for recently created entities from this project
        # that don't already have embeddings
        cur.execute(\"\"\"
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
        \"\"\", (project_id,))

        queued_count = cur.rowcount
        cur.close()

        return queued_count

    except Exception as e:
        print(f"Warning: Failed to queue embeddings: {e}")
        return 0
"""

# ============================================
# 3. MODIFY _create_intelligent_objects TO CALL QUEUE
# ============================================
# In dxf_importer.py, update the _create_intelligent_objects method
# Add this code after the intelligent objects are created (around line 180):

DXF_CREATOR_MODIFICATION = """
# In the _create_intelligent_objects method, add after creating objects:

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
"""

# ============================================
# 4. FRONTEND JAVASCRIPT FOR HYBRID SEARCH
# ============================================
# Add this to templates/advanced_search.html
# Replace or enhance the existing search execution function

FRONTEND_JAVASCRIPT = """
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
    resultsContainer.innerHTML = '<div class="loading-spinner">Searching...</div>';

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
                <span>Query: "${query}"</span>
            </div>
        `;
    }
}

/**
 * Find similar entities using Graph RAG
 */
async function findSimilar(entityId) {
    // TODO: Implement Graph RAG similarity search
    console.log('Finding similar entities for:', entityId);
    showNotification('Graph RAG integration coming in Phase 3!', 'info');
}

// Add event listener for hybrid search
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
    }

    if (searchButton) {
        searchButton.addEventListener('click', executeHybridSearch);
    }
});
</script>

<style>
/* Hybrid Search Result Styles */
.result-card {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    transition: box-shadow 0.2s;
}

.result-card:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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
    transition: width 0.3s;
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
    padding-top: 8px;
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
}

.search-stats {
    padding: 12px;
    background: #f8f9fa;
    border-radius: 6px;
    margin-bottom: 16px;
    font-size: 14px;
    color: #666;
}

.search-stats .separator {
    margin: 0 8px;
    color: #ccc;
}

.loading-spinner {
    text-align: center;
    padding: 40px;
    color: #666;
}

.no-results {
    text-align: center;
    padding: 40px;
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
    padding: 16px;
    border-radius: 6px;
    text-align: center;
}
</style>
"""

# ============================================
# 5. INSTALLATION INSTRUCTIONS
# ============================================

INSTALLATION_INSTRUCTIONS = """
# Phase 2 Integration Installation

## Step 1: Add Hybrid Search API Endpoint

1. Open `app.py`
2. Find the existing `/api/search/execute` endpoint (around line 21180)
3. Add the new hybrid search endpoint after it:

```python
{HYBRID_SEARCH_ENDPOINT}
```

## Step 2: Integrate DXF Import Queue

1. Open `dxf_importer.py`
2. Add the new method `_queue_embeddings_for_intelligent_objects` to the DXFImporter class:

```python
{DXF_QUEUE_INTEGRATION}
```

3. Modify the `_create_intelligent_objects` method to call the queue function:

```python
{DXF_CREATOR_MODIFICATION}
```

## Step 3: Update Advanced Search UI

1. Open `templates/advanced_search.html`
2. Add the JavaScript and CSS for hybrid search:

{FRONTEND_JAVASCRIPT}

3. Add a search results container if it doesn't exist:

```html
<div id="searchStats"></div>
<div id="searchResults"></div>
```

## Step 4: Restart Application

```bash
# If using Flask development server
python app.py

# If using production server
sudo systemctl restart your-app-service
```

## Step 5: Test Integration

1. Open Advanced Search page
2. Enter search query (e.g., "storm drain")
3. Results should show hybrid scores with breakdown
4. Import a DXF file - embeddings should auto-queue

## Verification

Run the Phase 2 verification script:
```bash
python scripts/phase2_verify.py
```
"""


def main():
    """Print installation guide"""
    print("=" * 70)
    print("PHASE 2 INTEGRATION CODE")
    print("=" * 70)
    print()
    print("This file contains all the code needed to integrate Phase 2 features.")
    print("See the INSTALLATION_INSTRUCTIONS string for step-by-step guide.")
    print()
    print("Files to modify:")
    print("  1. app.py - Add hybrid search API endpoint")
    print("  2. dxf_importer.py - Add embedding queue trigger")
    print("  3. templates/advanced_search.html - Add hybrid search UI")
    print()
    print("Full instructions available in the INSTALLATION_INSTRUCTIONS string")
    print("or see scripts/PHASE2_INTEGRATION_GUIDE.md")


if __name__ == '__main__':
    main()
