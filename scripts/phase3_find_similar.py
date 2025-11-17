#!/usr/bin/env python3
"""
Phase 3 - Find Similar Feature

This script contains the implementation for the "Find Similar" feature that uses
vector similarity and Graph RAG to find related entities.

Copy-paste ready code for integration into your application.
"""

# ============================================
# 1. API ENDPOINT FOR FIND SIMILAR
# ============================================
# Add this to app.py

FIND_SIMILAR_ENDPOINT = """
@app.route('/api/ai/find-similar/<uuid:entity_id>', methods=['GET'])
def find_similar_entities(entity_id):
    \"\"\"
    Find entities similar to the given entity using AI vector similarity
    and Graph RAG traversal.

    Query params:
        - method: 'vector' (default), 'graph', or 'both'
        - limit: number of results (default: 10)
        - threshold: similarity threshold 0-1 (default: 0.7)
        - max_hops: for graph traversal (default: 2)
    \"\"\"
    try:
        method = request.args.get('method', 'both')
        limit = int(request.args.get('limit', 10))
        threshold = float(request.args.get('threshold', 0.7))
        max_hops = int(request.args.get('max_hops', 2))

        # Get source entity details
        source_query = \"\"\"
            SELECT
                entity_id,
                canonical_name,
                entity_type,
                description,
                source_table,
                source_id
            FROM standards_entities
            WHERE entity_id = %s
        \"\"\"
        source_entity = execute_query(source_query, [str(entity_id)])

        if not source_entity:
            return jsonify({'error': 'Entity not found'}), 404

        source_entity = source_entity[0]

        results = {
            'source_entity': source_entity,
            'vector_similar': [],
            'graph_related': [],
            'combined': []
        }

        # Method 1: Vector Similarity
        if method in ['vector', 'both']:
            vector_query = \"\"\"
                SELECT
                    s.entity_id,
                    s.canonical_name,
                    s.entity_type,
                    s.description,
                    s.similarity_score,
                    se.source_table,
                    se.source_id
                FROM find_similar_entities(%s::uuid, %s, %s) s
                JOIN standards_entities se ON s.entity_id = se.entity_id
                ORDER BY s.similarity_score DESC
            \"\"\"
            results['vector_similar'] = execute_query(
                vector_query,
                [str(entity_id), threshold, limit]
            )

        # Method 2: Graph Traversal
        if method in ['graph', 'both']:
            graph_query = \"\"\"
                SELECT
                    r.entity_id,
                    r.canonical_name,
                    r.entity_type,
                    r.hop_distance,
                    r.relationship_path,
                    se.description,
                    se.source_table,
                    se.source_id
                FROM find_related_entities(%s::uuid, %s, NULL) r
                JOIN standards_entities se ON r.entity_id = se.entity_id
                ORDER BY r.hop_distance, r.canonical_name
                LIMIT %s
            \"\"\"
            results['graph_related'] = execute_query(
                graph_query,
                [str(entity_id), max_hops, limit]
            )

        # Method 3: Combined (both vector and graph)
        if method == 'both':
            combined_query = \"\"\"
                WITH vector_results AS (
                    SELECT
                        s.entity_id,
                        s.canonical_name,
                        s.entity_type,
                        s.similarity_score,
                        NULL::integer as hop_distance,
                        'vector'::text as match_type
                    FROM find_similar_entities(%s::uuid, %s, %s) s
                ),
                graph_results AS (
                    SELECT
                        r.entity_id,
                        r.canonical_name,
                        r.entity_type,
                        NULL::real as similarity_score,
                        r.hop_distance,
                        'graph'::text as match_type
                    FROM find_related_entities(%s::uuid, %s, NULL) r
                ),
                combined AS (
                    SELECT * FROM vector_results
                    UNION
                    SELECT * FROM graph_results
                )
                SELECT
                    c.entity_id,
                    c.canonical_name,
                    c.entity_type,
                    c.similarity_score,
                    c.hop_distance,
                    c.match_type,
                    se.description,
                    se.source_table,
                    -- Calculate combined relevance score
                    COALESCE(c.similarity_score, 0) * 0.6 +
                    CASE
                        WHEN c.hop_distance = 1 THEN 0.4
                        WHEN c.hop_distance = 2 THEN 0.2
                        ELSE 0
                    END as relevance_score
                FROM combined c
                JOIN standards_entities se ON c.entity_id = se.entity_id
                ORDER BY relevance_score DESC
                LIMIT %s
            \"\"\"
            results['combined'] = execute_query(
                combined_query,
                [str(entity_id), threshold, limit,
                 str(entity_id), max_hops,
                 limit]
            )

        # Add metadata
        results['metadata'] = {
            'method': method,
            'threshold': threshold,
            'limit': limit,
            'max_hops': max_hops,
            'vector_count': len(results['vector_similar']),
            'graph_count': len(results['graph_related']),
            'combined_count': len(results['combined'])
        }

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/similarity-explanation/<uuid:entity1_id>/<uuid:entity2_id>', methods=['GET'])
def explain_similarity(entity1_id, entity2_id):
    \"\"\"
    Explain why two entities are similar.
    Shows shared attributes, relationships, and semantic similarity.
    \"\"\"
    try:
        # Get both entities
        entity_query = \"\"\"
            SELECT
                entity_id,
                canonical_name,
                entity_type,
                description,
                source_table
            FROM standards_entities
            WHERE entity_id IN (%s, %s)
        \"\"\"
        entities = execute_query(entity_query, [str(entity1_id), str(entity2_id)])

        if len(entities) != 2:
            return jsonify({'error': 'One or both entities not found'}), 404

        entity1, entity2 = entities

        # Get vector similarity
        similarity_query = \"\"\"
            SELECT
                1 - (e1.embedding <=> e2.embedding) as similarity_score
            FROM entity_embeddings e1
            CROSS JOIN entity_embeddings e2
            WHERE e1.entity_id = %s AND e1.is_current = TRUE
              AND e2.entity_id = %s AND e2.is_current = TRUE
        \"\"\"
        similarity = execute_query(
            similarity_query,
            [str(entity1_id), str(entity2_id)]
        )

        vector_similarity = similarity[0]['similarity_score'] if similarity else 0

        # Find relationship paths
        path_query = \"\"\"
            SELECT
                relationship_path,
                hop_distance
            FROM find_related_entities(%s::uuid, 3, NULL)
            WHERE entity_id = %s
            ORDER BY hop_distance
            LIMIT 1
        \"\"\"
        path = execute_query(path_query, [str(entity1_id), str(entity2_id)])

        # Analyze shared characteristics
        explanation = {
            'entity1': entity1,
            'entity2': entity2,
            'vector_similarity': float(vector_similarity) if vector_similarity else 0,
            'relationship_path': path[0] if path else None,
            'reasons': []
        }

        # Generate reasons based on similarity
        if vector_similarity and vector_similarity > 0.8:
            explanation['reasons'].append({
                'type': 'high_similarity',
                'description': 'These entities are very similar semantically based on AI analysis',
                'confidence': 'high'
            })

        if path:
            hop_dist = path[0]['hop_distance']
            if hop_dist == 1:
                explanation['reasons'].append({
                    'type': 'direct_connection',
                    'description': 'These entities are directly connected in the knowledge graph',
                    'confidence': 'high'
                })
            elif hop_dist == 2:
                explanation['reasons'].append({
                    'type': 'indirect_connection',
                    'description': f'These entities are connected through {hop_dist} relationship(s)',
                    'confidence': 'medium'
                })

        if entity1['entity_type'] == entity2['entity_type']:
            explanation['reasons'].append({
                'type': 'same_type',
                'description': f'Both are {entity1["entity_type"]} entities',
                'confidence': 'medium'
            })

        return jsonify(explanation)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
"""

# ============================================
# 2. FRONTEND COMPONENT - FIND SIMILAR MODAL
# ============================================

FIND_SIMILAR_MODAL_HTML = """
<!-- Find Similar Modal -->
<div id="findSimilarModal" class="modal">
    <div class="modal-content large">
        <div class="modal-header">
            <h2><i class="fas fa-network-wired"></i> Find Similar Entities</h2>
            <button class="modal-close" onclick="closeFindSimilarModal()">
                <i class="fas fa-times"></i>
            </button>
        </div>

        <div class="modal-body">
            <!-- Source Entity -->
            <div class="source-entity-card">
                <div class="card-label">Source Entity:</div>
                <div class="entity-display" id="sourceEntityDisplay">
                    <!-- Populated by JavaScript -->
                </div>
            </div>

            <!-- Search Method Selector -->
            <div class="method-selector">
                <div class="method-tabs">
                    <button class="method-tab active" data-method="both">
                        <i class="fas fa-layer-group"></i> Combined
                    </button>
                    <button class="method-tab" data-method="vector">
                        <i class="fas fa-brain"></i> AI Similarity
                    </button>
                    <button class="method-tab" data-method="graph">
                        <i class="fas fa-project-diagram"></i> Graph Connections
                    </button>
                </div>
            </div>

            <!-- Results -->
            <div class="similar-results" id="similarResults">
                <div class="loading-state">
                    <i class="fas fa-spinner fa-spin"></i> Finding similar entities...
                </div>
            </div>
        </div>

        <div class="modal-footer">
            <button class="btn-secondary" onclick="closeFindSimilarModal()">Close</button>
        </div>
    </div>
</div>

<style>
.source-entity-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 24px;
}

.source-entity-card .card-label {
    font-size: 12px;
    opacity: 0.9;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.source-entity-card .entity-display {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 18px;
    font-weight: 600;
}

.method-selector {
    margin-bottom: 24px;
}

.method-tabs {
    display: flex;
    gap: 8px;
    background: #f8f9fa;
    padding: 4px;
    border-radius: 8px;
}

.method-tab {
    flex: 1;
    padding: 12px 16px;
    background: transparent;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-weight: 500;
    color: #666;
    transition: all 0.2s;
}

.method-tab:hover {
    background: rgba(102, 126, 234, 0.1);
    color: #667eea;
}

.method-tab.active {
    background: white;
    color: #667eea;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.similar-results {
    min-height: 400px;
}

.result-item {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    transition: all 0.2s;
    cursor: pointer;
}

.result-item:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    transform: translateX(4px);
}

.result-item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.result-item-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    font-size: 16px;
}

.similarity-meter {
    display: flex;
    align-items: center;
    gap: 8px;
}

.similarity-bar {
    width: 100px;
    height: 8px;
    background: #e0e0e0;
    border-radius: 4px;
    overflow: hidden;
}

.similarity-fill {
    height: 100%;
    background: linear-gradient(90deg, #4CAF50, #8BC34A);
    transition: width 0.3s ease;
}

.similarity-value {
    font-weight: 600;
    font-size: 14px;
    color: #4CAF50;
}

.result-item-meta {
    display: flex;
    gap: 12px;
    font-size: 12px;
    color: #666;
}

.meta-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    background: #f0f0f0;
    border-radius: 4px;
}

.result-item-description {
    margin-top: 8px;
    font-size: 14px;
    color: #666;
}

.match-type-indicator {
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 12px;
    font-weight: 600;
    text-transform: uppercase;
}

.match-type-vector {
    background: #E8F5E9;
    color: #2E7D32;
}

.match-type-graph {
    background: #E3F2FD;
    color: #1976D2;
}

.match-type-both {
    background: #F3E5F5;
    color: #7B1FA2;
}

.loading-state {
    text-align: center;
    padding: 60px 20px;
    color: #666;
    font-size: 16px;
}

.loading-state i {
    font-size: 32px;
    margin-bottom: 12px;
}

.no-results {
    text-align: center;
    padding: 60px 20px;
    color: #999;
}

.explain-link {
    color: #2196F3;
    cursor: pointer;
    font-size: 12px;
    margin-top: 8px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.explain-link:hover {
    text-decoration: underline;
}
</style>

<script>
let currentEntityId = null;
let currentMethod = 'both';

/**
 * Open Find Similar modal for an entity
 */
async function openFindSimilarModal(entityId, entityName, entityType) {
    currentEntityId = entityId;

    const modal = document.getElementById('findSimilarModal');
    const sourceDisplay = document.getElementById('sourceEntityDisplay');

    // Show source entity
    sourceDisplay.innerHTML = `
        <i class="fas fa-${getEntityIcon(entityType)}"></i>
        <span>${entityName}</span>
        <span style="opacity: 0.8; font-size: 14px; font-weight: 400;">
            (${entityType})
        </span>
    `;

    // Show modal
    modal.style.display = 'flex';

    // Fetch similar entities
    await fetchSimilarEntities(entityId, currentMethod);

    // Setup method tabs
    setupMethodTabs();
}

/**
 * Close Find Similar modal
 */
function closeFindSimilarModal() {
    const modal = document.getElementById('findSimilarModal');
    modal.style.display = 'none';
    currentEntityId = null;
}

/**
 * Fetch similar entities
 */
async function fetchSimilarEntities(entityId, method) {
    const resultsContainer = document.getElementById('similarResults');

    resultsContainer.innerHTML = `
        <div class="loading-state">
            <i class="fas fa-spinner fa-spin"></i>
            Finding similar entities...
        </div>
    `;

    try {
        const response = await fetch(
            `/api/ai/find-similar/${entityId}?method=${method}&limit=20&threshold=0.65`
        );
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        displaySimilarResults(data, method);

    } catch (error) {
        console.error('Error fetching similar entities:', error);
        resultsContainer.innerHTML = `
            <div class="no-results">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Failed to find similar entities: ${error.message}</p>
            </div>
        `;
    }
}

/**
 * Display similar results
 */
function displaySimilarResults(data, method) {
    const resultsContainer = document.getElementById('similarResults');

    let results;
    if (method === 'both') {
        results = data.combined;
    } else if (method === 'vector') {
        results = data.vector_similar;
    } else {
        results = data.graph_related;
    }

    if (!results || results.length === 0) {
        resultsContainer.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search"></i>
                <p>No similar entities found</p>
            </div>
        `;
        return;
    }

    let html = '';

    results.forEach(result => {
        const score = result.similarity_score || result.relevance_score || 0;
        const scorePercent = Math.round(score * 100);
        const matchType = result.match_type || method;
        const hopInfo = result.hop_distance ? `${result.hop_distance} hop${result.hop_distance > 1 ? 's' : ''}` : '';

        html += `
            <div class="result-item" onclick="viewEntityDetails('${result.entity_id}')">
                <div class="result-item-header">
                    <div class="result-item-title">
                        <i class="fas fa-${getEntityIcon(result.entity_type)}"></i>
                        ${result.canonical_name}
                    </div>
                    <div class="similarity-meter">
                        <div class="similarity-bar">
                            <div class="similarity-fill" style="width: ${scorePercent}%"></div>
                        </div>
                        <span class="similarity-value">${scorePercent}%</span>
                    </div>
                </div>

                <div class="result-item-meta">
                    <span class="meta-badge">
                        <i class="fas fa-tag"></i> ${result.entity_type}
                    </span>
                    <span class="match-type-indicator match-type-${matchType}">
                        ${matchType === 'vector' ? 'AI Match' :
                          matchType === 'graph' ? 'Graph Connection' :
                          'Combined'}
                    </span>
                    ${hopInfo ? `
                        <span class="meta-badge">
                            <i class="fas fa-project-diagram"></i> ${hopInfo}
                        </span>
                    ` : ''}
                </div>

                ${result.description ? `
                    <div class="result-item-description">
                        ${result.description}
                    </div>
                ` : ''}

                <div class="explain-link" onclick="event.stopPropagation(); explainSimilarity('${currentEntityId}', '${result.entity_id}')">
                    <i class="fas fa-question-circle"></i> Why are these similar?
                </div>
            </div>
        `;
    });

    resultsContainer.innerHTML = html;
}

/**
 * Setup method tabs
 */
function setupMethodTabs() {
    const tabs = document.querySelectorAll('.method-tab');

    tabs.forEach(tab => {
        tab.addEventListener('click', async () => {
            // Update active state
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Update method and fetch
            currentMethod = tab.dataset.method;
            await fetchSimilarEntities(currentEntityId, currentMethod);
        });
    });
}

/**
 * Explain why two entities are similar
 */
async function explainSimilarity(entityId1, entityId2) {
    try {
        const response = await fetch(`/api/ai/similarity-explanation/${entityId1}/${entityId2}`);
        const data = await response.json();

        let explanation = `Similarity between ${data.entity1.canonical_name} and ${data.entity2.canonical_name}:\\n\\n`;

        explanation += `Vector Similarity: ${(data.vector_similarity * 100).toFixed(0)}%\\n\\n`;

        if (data.reasons.length > 0) {
            explanation += 'Reasons:\\n';
            data.reasons.forEach(reason => {
                explanation += `• ${reason.description}\\n`;
            });
        }

        alert(explanation);

    } catch (error) {
        console.error('Error explaining similarity:', error);
        alert('Failed to explain similarity');
    }
}

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
</script>
"""

# ============================================
# 3. INTEGRATION CODE FOR "FIND SIMILAR" BUTTON
# ============================================

FIND_SIMILAR_BUTTON_CODE = """
<!-- Add this button wherever you display entity details -->
<button
    class="btn-action"
    onclick="openFindSimilarModal('{{ entity.entity_id }}', '{{ entity.canonical_name }}', '{{ entity.entity_type }}')"
    title="Find similar entities using AI"
>
    <i class="fas fa-network-wired"></i> Find Similar
</button>

<!-- Example: Add to entity detail page or list item -->
<div class="entity-actions">
    <button class="btn-action" onclick="editEntity('{{ entity.entity_id }}')">
        <i class="fas fa-edit"></i> Edit
    </button>
    <button class="btn-action" onclick="openFindSimilarModal('{{ entity.entity_id }}', '{{ entity.canonical_name }}', '{{ entity.entity_type }}')">
        <i class="fas fa-network-wired"></i> Find Similar
    </button>
    <button class="btn-action" onclick="deleteEntity('{{ entity.entity_id }}')">
        <i class="fas fa-trash"></i> Delete
    </button>
</div>
"""


def main():
    """Print implementation guide"""
    print("=" * 70)
    print("PHASE 3 - FIND SIMILAR FEATURE")
    print("=" * 70)
    print()
    print("This file contains the implementation for the Find Similar feature.")
    print()
    print("Features:")
    print("  - Vector similarity search using AI embeddings")
    print("  - Graph RAG traversal to find connected entities")
    print("  - Combined scoring (vector + graph)")
    print("  - Visual similarity indicators")
    print("  - Explanation of why entities are similar")
    print()
    print("Files to create/modify:")
    print("  1. app.py - Add FIND_SIMILAR_ENDPOINT")
    print("  2. templates/base.html - Add FIND_SIMILAR_MODAL_HTML")
    print("  3. Various templates - Add FIND_SIMILAR_BUTTON_CODE where appropriate")
    print()
    print("See PHASE3_INTEGRATION_GUIDE.md for detailed instructions")


if __name__ == '__main__':
    main()
