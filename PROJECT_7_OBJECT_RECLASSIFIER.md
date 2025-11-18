# Project 7: Object Reclassifier - Testing & AI Enhancement Suite

## Executive Summary
Test and enhance the existing Object Reclassifier tool that reviews low-confidence DXF entity classifications. Transform it from a basic manual review interface into an AI-powered classification workbench with intelligent suggestions, batch workflows, visual geometry preview, and spatial context. This 3-week project leverages the AI-first architecture (embeddings) to make reclassification fast and accurate.

## Current State Assessment

### ✅ What Exists (Built but Untested)
1. **Object Reclassifier UI**: `templates/tools/object_reclassifier.html`
2. **Classification Service**: `services/classification_service.py`
   - `reclassify_entity(entity_id, new_type, user_notes)` - Single entity
   - `bulk_reclassify(entity_ids, new_type, user_notes)` - Batch operation
3. **Intelligent Object Creator**: Auto-classification during DXF import
   - Confidence threshold: <70% = `needs_review`, ≥70% = `auto_classified`
   - Creates in target table with `classification_state` flag
4. **Standards Entities Table**: Tracks all classifications
   - `classification_state`: auto_classified, needs_review, user_classified
   - `classification_confidence`: 0.0-1.0
   - `classification_suggestions`: Top 3 alternative types
   - `classification_metadata`: JSONB with spatial context

### ⚠️ What's Missing
1. **Testing**: Zero automated or manual tests performed
2. **AI Suggestions**: Doesn't use embeddings for similar entity matching
3. **Visual Preview**: No geometry visualization during review
4. **Spatial Context**: Spatial hints exist but not surfaced in UI
5. **Batch Workflows**: Bulk reclassify exists but no approval queue UI
6. **Confidence Tuning**: No UI to adjust 70% threshold
7. **Review Analytics**: No metrics on classification accuracy over time

### Current Workflow (Basic)
```
DXF Import → LayerClassifier → <70% confidence → needs_review flag
User opens Object Reclassifier → Manual table view → Select entity → Reclassify
```

### Target Workflow (AI-Enhanced)
```
DXF Import → LayerClassifier → <70% confidence → needs_review flag + AI suggestions
User opens Object Reclassifier → 
  See geometry preview + spatial context +
  AI-ranked suggestions (similarity search via embeddings) +
  One-click approve/reclassify +
  Batch approval queue
```

## Goals & Objectives

### Primary Goals
1. **Test Existing Functionality**: Comprehensive testing of current reclassifier
2. **AI-Powered Suggestions**: Use embeddings to find similar entities and suggest classifications
3. **Visual Geometry Preview**: SVG rendering of entity shapes during review
4. **Spatial Context Display**: Show nearby features, layer analysis, network connectivity
5. **Batch Approval Workflows**: Queue-based review with bulk actions
6. **Analytics Dashboard**: Track classification accuracy, user corrections, confidence trends

### Success Metrics
- 100% of existing reclassifier features tested and working
- AI suggestions have >80% accuracy (correct type in top 3)
- Users can review 10+ entities/minute (vs 2-3 current)
- Batch approval reduces review time by 60%
- Confidence threshold tunable via UI
- Weekly analytics showing classification improvement

## Technical Architecture

### Phase 1: Testing & Bug Fixes

#### Test Cases
```python
# tests/integration/test_object_reclassifier.py

class TestObjectReclassifier:
    def test_import_creates_needs_review_entities(self):
        """Low-confidence DXF import should create entities flagged for review"""
        # Import DXF with ambiguous layer name (e.g., "MISC-STUFF")
        # Verify entity created with classification_state='needs_review'
        # Verify classification_confidence < 0.7
    
    def test_reclassifier_ui_loads(self):
        """Object Reclassifier page should load and display pending entities"""
        response = client.get('/tools/object-reclassifier')
        assert response.status_code == 200
        assert b'needs_review' in response.data
    
    def test_single_reclassify(self):
        """User should be able to reclassify single entity"""
        entity_id = create_test_entity(classification_state='needs_review')
        
        response = client.post(f'/api/reclassify/{entity_id}', json={
            'new_type': 'utility_line',
            'user_notes': 'Clearly a storm drain line'
        })
        
        assert response.status_code == 200
        
        # Verify entity moved to utility_lines table
        # Verify classification_state='user_classified'
        # Verify confidence=1.0 (user override)
    
    def test_bulk_reclassify(self):
        """Batch reclassification should update multiple entities"""
        entity_ids = [create_test_entity() for _ in range(5)]
        
        response = client.post('/api/reclassify/bulk', json={
            'entity_ids': entity_ids,
            'new_type': 'utility_structure',
            'user_notes': 'Batch correction - all manholes'
        })
        
        assert response.json()['success'] == 5
    
    def test_suggestions_stored(self):
        """Classification should store top 3 suggestions"""
        entity_id = create_test_entity()
        
        # Verify classification_suggestions contains array
        # Verify array length <= 3
        # Verify each suggestion has: type, confidence, reason
```

### Phase 2: AI-Powered Suggestions

#### Similarity Search Using Embeddings
```python
# services/ai_classification_service.py

class AIClassificationService:
    def __init__(self, db_config):
        self.db_config = db_config
        self.openai_client = OpenAI()  # Requires OpenAI integration
    
    def get_ai_suggestions(self, entity_id: str, limit: int = 5) -> List[Dict]:
        """
        Find similar classified entities using embedding similarity
        
        Returns:
            [
                {
                    'suggested_type': 'utility_line',
                    'confidence': 0.92,
                    'reason': 'Similar to 12 storm drain lines',
                    'example_entity_id': 'uuid-123',
                    'similarity_score': 0.87
                }
            ]
        """
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Get embedding for target entity
        cur.execute("""
            SELECT e.embedding
            FROM embeddings e
            JOIN standards_entities se ON e.entity_id = se.entity_id
            WHERE se.entity_id = %s
        """, (entity_id,))
        
        target = cur.fetchone()
        if not target or not target['embedding']:
            # Generate embedding if missing
            target_embedding = self._generate_entity_embedding(entity_id)
        else:
            target_embedding = target['embedding']
        
        # 2. Find similar entities with high-confidence classifications
        cur.execute("""
            SELECT 
                se.object_type,
                se.table_name,
                se.classification_confidence,
                e.entity_id,
                1 - (e.embedding <=> %s::vector) as similarity
            FROM embeddings e
            JOIN standards_entities se ON e.entity_id = se.entity_id
            WHERE se.classification_state IN ('auto_classified', 'user_classified')
              AND se.classification_confidence >= 0.8
              AND e.embedding IS NOT NULL
            ORDER BY e.embedding <=> %s::vector
            LIMIT 50
        """, (target_embedding, target_embedding))
        
        similar = cur.fetchall()
        cur.close()
        conn.close()
        
        # 3. Aggregate by object type and calculate confidence
        suggestions = {}
        for row in similar:
            obj_type = row['object_type']
            if obj_type not in suggestions:
                suggestions[obj_type] = {
                    'suggested_type': obj_type,
                    'count': 0,
                    'avg_similarity': 0,
                    'avg_confidence': 0,
                    'example_entity_id': row['entity_id']
                }
            
            suggestions[obj_type]['count'] += 1
            suggestions[obj_type]['avg_similarity'] += row['similarity']
            suggestions[obj_type]['avg_confidence'] += row['classification_confidence']
        
        # 4. Calculate final scores
        ranked_suggestions = []
        for obj_type, data in suggestions.items():
            count = data['count']
            composite_score = (
                (data['avg_similarity'] / count) * 0.6 +  # Similarity weight
                (data['avg_confidence'] / count) * 0.3 +  # Confidence weight
                (min(count / 10, 1.0)) * 0.1              # Frequency weight
            )
            
            ranked_suggestions.append({
                'suggested_type': obj_type,
                'confidence': round(composite_score, 2),
                'reason': f'Similar to {count} classified {obj_type} entities',
                'example_entity_id': data['example_entity_id'],
                'similarity_score': round(data['avg_similarity'] / count, 2)
            })
        
        # 5. Sort by composite score
        ranked_suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return ranked_suggestions[:limit]
    
    def _generate_entity_embedding(self, entity_id: str) -> List[float]:
        """Generate embedding for entity using OpenAI API"""
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get entity attributes
        cur.execute("""
            SELECT 
                de.entity_type,
                l.layer_name,
                ST_GeometryType(de.geometry) as geom_type,
                de.color_aci,
                ST_AsText(de.geometry) as geometry_wkt
            FROM drawing_entities de
            LEFT JOIN layers l ON de.layer_id = l.layer_id
            JOIN standards_entities se ON de.entity_id = se.entity_id
            WHERE se.entity_id = %s
        """, (entity_id,))
        
        entity = cur.fetchone()
        
        # Build semantic description
        description = f"""
        CAD Entity: {entity['entity_type']}
        Layer: {entity['layer_name']}
        Geometry: {entity['geom_type']}
        Color: {entity['color_aci']}
        """
        
        # Call OpenAI embedding API
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=description
        )
        
        embedding = response.data[0].embedding
        
        # Store embedding
        cur.execute("""
            INSERT INTO embeddings (entity_id, embedding, embedding_model)
            VALUES (%s, %s, 'text-embedding-3-small')
            ON CONFLICT (entity_id) DO UPDATE SET
                embedding = EXCLUDED.embedding,
                updated_at = NOW()
        """, (entity_id, embedding))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return embedding
```

### Phase 3: Visual Geometry Preview

#### SVG Renderer for Entity Shapes
```python
# services/geometry_preview_service.py

class GeometryPreviewService:
    def generate_svg(self, entity_id: str, width: int = 400, height: int = 300) -> str:
        """
        Generate SVG preview of entity geometry
        
        Returns:
            SVG string with entity rendered
        """
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                ST_AsText(geometry) as geom_wkt,
                ST_GeometryType(geometry) as geom_type,
                ST_XMin(geometry) as xmin,
                ST_YMin(geometry) as ymin,
                ST_XMax(geometry) as xmax,
                ST_YMax(geometry) as ymax,
                color_aci
            FROM drawing_entities
            WHERE entity_id = (
                SELECT drawing_entity_id FROM standards_entities WHERE entity_id = %s
            )
        """, (entity_id,))
        
        entity = cur.fetchone()
        cur.close()
        conn.close()
        
        if not entity:
            return '<svg></svg>'
        
        # Calculate viewport
        bbox_width = entity['xmax'] - entity['xmin']
        bbox_height = entity['ymax'] - entity['ymin']
        padding = max(bbox_width, bbox_height) * 0.1
        
        viewbox_xmin = entity['xmin'] - padding
        viewbox_ymin = entity['ymin'] - padding
        viewbox_width = bbox_width + 2 * padding
        viewbox_height = bbox_height + 2 * padding
        
        # Build SVG
        svg = f'''
        <svg width="{width}" height="{height}" 
             viewBox="{viewbox_xmin} {viewbox_ymin} {viewbox_width} {viewbox_height}"
             xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#1a1a1a"/>
        '''
        
        # Render based on geometry type
        if entity['geom_type'] == 'ST_LineString':
            svg += self._render_linestring(entity['geom_wkt'], entity['color_aci'])
        elif entity['geom_type'] == 'ST_Point':
            svg += self._render_point(entity['geom_wkt'], entity['color_aci'])
        elif entity['geom_type'] == 'ST_Polygon':
            svg += self._render_polygon(entity['geom_wkt'], entity['color_aci'])
        
        svg += '</svg>'
        return svg
    
    def _render_linestring(self, wkt: str, color_aci: int) -> str:
        """Convert WKT linestring to SVG path"""
        # Parse WKT: LINESTRING(x1 y1, x2 y2, ...)
        coords = wkt.replace('LINESTRING(', '').replace(')', '').split(',')
        points = [tuple(map(float, c.strip().split())) for c in coords]
        
        path_data = f'M {points[0][0]},{points[0][1]}'
        for x, y in points[1:]:
            path_data += f' L {x},{y}'
        
        color = self._aci_to_hex(color_aci)
        return f'<path d="{path_data}" stroke="{color}" stroke-width="2" fill="none"/>'
    
    def _aci_to_hex(self, aci: int) -> str:
        """Convert AutoCAD Color Index to hex"""
        aci_colors = {
            1: '#FF0000',  # Red
            2: '#FFFF00',  # Yellow
            3: '#00FF00',  # Green
            4: '#00FFFF',  # Cyan
            5: '#0000FF',  # Blue
            6: '#FF00FF',  # Magenta
            7: '#FFFFFF',  # White
        }
        return aci_colors.get(aci, '#00FFFF')  # Default cyan
```

### Phase 4: Enhanced UI with Spatial Context

#### Updated Object Reclassifier Interface
```html
<!-- templates/tools/object_reclassifier.html (enhanced) -->

<div class="reclassifier-container">
    <div class="header-section">
        <h1><i class="fas fa-magic"></i> Object Reclassifier</h1>
        <p class="subtitle">Review and correct low-confidence DXF entity classifications</p>
        
        <div class="stats-ribbon">
            <div class="stat-card">
                <span class="stat-value" id="needsReviewCount">0</span>
                <span class="stat-label">Needs Review</span>
            </div>
            <div class="stat-card">
                <span class="stat-value" id="reviewedTodayCount">0</span>
                <span class="stat-label">Reviewed Today</span>
            </div>
            <div class="stat-card">
                <span class="stat-value" id="avgConfidence">0%</span>
                <span class="stat-label">Avg Confidence</span>
            </div>
        </div>
    </div>

    <div class="review-layout">
        <!-- Left: Entity Queue -->
        <div class="entity-queue">
            <div class="queue-header">
                <h3>Review Queue</h3>
                <select id="filterProject">
                    <option value="">All Projects</option>
                </select>
            </div>
            
            <div class="entity-list" id="entityList">
                <!-- Populated via JavaScript -->
            </div>
        </div>

        <!-- Center: Review Panel -->
        <div class="review-panel">
            <div class="entity-details">
                <h3>Entity Details</h3>
                <div id="entityMetadata"></div>
                
                <!-- Geometry Preview -->
                <div class="geometry-preview">
                    <h4>Geometry Preview</h4>
                    <div id="svgPreview"></div>
                </div>
                
                <!-- Spatial Context -->
                <div class="spatial-context">
                    <h4><i class="fas fa-map-marker-alt"></i> Spatial Context</h4>
                    <ul id="spatialHints"></ul>
                </div>
            </div>
            
            <!-- AI Suggestions -->
            <div class="ai-suggestions">
                <h3><i class="fas fa-brain"></i> AI Suggestions</h3>
                <div id="suggestionCards"></div>
            </div>
            
            <!-- Manual Override -->
            <div class="manual-override">
                <h3>Manual Classification</h3>
                <select id="manualTypeSelect">
                    <option value="">Choose type...</option>
                    <option value="utility_line">Utility Line</option>
                    <option value="utility_structure">Utility Structure</option>
                    <option value="bmp">BMP</option>
                    <option value="survey_point">Survey Point</option>
                </select>
                <textarea id="userNotes" placeholder="Optional notes..."></textarea>
                <button class="btn-primary" onclick="reclassifyEntity()">
                    <i class="fas fa-check"></i> Reclassify
                </button>
            </div>
        </div>

        <!-- Right: Batch Actions -->
        <div class="batch-actions">
            <h3>Batch Actions</h3>
            <div class="selected-count">
                <span id="selectedCount">0</span> selected
            </div>
            
            <button class="btn-success" onclick="approveAllSuggestions()">
                <i class="fas fa-thumbs-up"></i> Approve All AI Suggestions
            </button>
            
            <button class="btn-primary" onclick="batchReclassify()">
                <i class="fas fa-layer-group"></i> Batch Reclassify
            </button>
            
            <button class="btn-secondary" onclick="skipSelected()">
                <i class="fas fa-forward"></i> Skip Selected
            </button>
        </div>
    </div>
</div>

<style>
.review-layout {
    display: grid;
    grid-template-columns: 300px 1fr 250px;
    gap: 20px;
    margin-top: 20px;
}

.entity-queue {
    background: var(--surface-color);
    border-radius: 8px;
    padding: 15px;
    max-height: 80vh;
    overflow-y: auto;
}

.entity-list-item {
    padding: 10px;
    margin: 5px 0;
    background: var(--background-color);
    border-radius: 4px;
    cursor: pointer;
    border-left: 3px solid var(--warning-color);
}

.entity-list-item:hover {
    background: var(--hover-color);
}

.entity-list-item.selected {
    border-left-color: var(--primary-color);
    background: var(--primary-color-dim);
}

.geometry-preview {
    margin: 15px 0;
    padding: 10px;
    background: #1a1a1a;
    border-radius: 4px;
}

.ai-suggestions {
    margin: 20px 0;
}

.suggestion-card {
    padding: 12px;
    margin: 8px 0;
    background: var(--surface-color);
    border-radius: 4px;
    border-left: 3px solid var(--success-color);
    cursor: pointer;
}

.suggestion-card:hover {
    background: var(--hover-color);
}

.confidence-badge {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 0.85em;
    font-weight: bold;
}

.confidence-high { background: var(--success-color); color: white; }
.confidence-medium { background: var(--warning-color); color: black; }
.confidence-low { background: var(--danger-color); color: white; }
</style>
```

### API Endpoints

```python
@app.route('/api/reclassifier/queue', methods=['GET'])
def get_review_queue():
    """Get all entities needing review"""
    project_id = request.args.get('project_id')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    query = """
        SELECT 
            se.entity_id,
            se.object_type,
            se.classification_state,
            se.classification_confidence,
            se.classification_suggestions,
            se.classification_metadata,
            de.entity_type,
            l.layer_name,
            p.project_name,
            ST_AsText(de.geometry) as geometry_wkt
        FROM standards_entities se
        JOIN drawing_entities de ON se.drawing_entity_id = de.entity_id
        LEFT JOIN layers l ON de.layer_id = l.layer_id
        JOIN projects p ON de.project_id = p.project_id
        WHERE se.classification_state = 'needs_review'
    """
    
    if project_id:
        query += " AND de.project_id = %s"
        cur.execute(query, (project_id,))
    else:
        cur.execute(query)
    
    entities = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify([dict(row) for row in entities])


@app.route('/api/reclassifier/<entity_id>/ai-suggestions', methods=['GET'])
def get_ai_suggestions(entity_id):
    """Get AI-powered classification suggestions"""
    from services.ai_classification_service import AIClassificationService
    
    ai_service = AIClassificationService(get_db_config())
    suggestions = ai_service.get_ai_suggestions(entity_id, limit=5)
    
    return jsonify(suggestions)


@app.route('/api/reclassifier/<entity_id>/preview', methods=['GET'])
def get_geometry_preview(entity_id):
    """Get SVG geometry preview"""
    from services.geometry_preview_service import GeometryPreviewService
    
    preview_service = GeometryPreviewService(get_db_config())
    svg = preview_service.generate_svg(entity_id)
    
    return Response(svg, mimetype='image/svg+xml')
```

## Implementation Phases

### Phase 1: Testing & Bug Fixes (Week 1)

**Deliverables**:
1. Write 15+ integration tests for existing functionality
2. Test UI loads and displays entities
3. Test single reclassification
4. Test bulk reclassification
5. Fix any bugs discovered
6. Document current limitations

**Testing Checklist**:
- [ ] Import DXF with low-confidence entities
- [ ] Verify `needs_review` flag set correctly
- [ ] UI displays pending entities
- [ ] Single reclassify updates database
- [ ] Bulk reclassify handles 10+ entities
- [ ] Classification metadata preserved
- [ ] User notes stored correctly

### Phase 2: AI Suggestions (Week 2, Days 1-2)

**Deliverables**:
1. Implement `AIClassificationService`
2. Embedding similarity search
3. Top 5 suggestions with confidence scores
4. Example entity links
5. API endpoint for suggestions

**Requirements**:
- OpenAI API key (text-embedding-3-small model)
- Embeddings table populated (see Project #1)

### Phase 3: Visual Preview (Week 2, Days 3-4)

**Deliverables**:
1. `GeometryPreviewService` with SVG rendering
2. Support for LineString, Point, Polygon
3. Color-coded by ACI
4. Viewport auto-scaling
5. API endpoint serving SVG

### Phase 4: Enhanced UI (Week 3, Days 1-3)

**Deliverables**:
1. Three-panel layout (Queue, Review, Batch)
2. Geometry preview integration
3. AI suggestions cards
4. Spatial context display
5. Batch selection with checkboxes

### Phase 5: Batch Workflows (Week 3, Days 4-5)

**Deliverables**:
1. Multi-select entity queue
2. "Approve All AI Suggestions" button
3. Batch reclassify dialog
4. Skip/defer functionality
5. Review analytics dashboard

## Success Criteria

### Must Have
- ✅ All existing features tested and working
- ✅ AI suggestions using embeddings
- ✅ SVG geometry preview
- ✅ Batch approval workflows
- ✅ Spatial context displayed

### Should Have
- ✅ Review analytics (accuracy over time)
- ✅ Confidence threshold tuning UI
- ✅ Example entity previews
- ✅ Keyboard shortcuts for fast review
- ✅ Auto-advance to next entity

### Nice to Have
- ✅ 3D geometry preview (if Z coordinates)
- ✅ Comparison view (suggested vs current)
- ✅ Undo last reclassification
- ✅ Export review audit log
- ✅ Mobile-responsive review UI

## Dependencies
- **Project #1 (AI Agent Toolkit)**: Embeddings table must be populated
- OpenAI API key for embedding generation
- Existing Object Reclassifier UI
- Classification Service

## Timeline
- **Week 1**: Testing & bug fixes
- **Week 2**: AI suggestions + Visual preview
- **Week 3**: Enhanced UI + Batch workflows

**Total Duration**: 3 weeks

## ROI & Business Value

### Time Savings
- **Before**: 2-3 entities/minute (manual review)
- **After**: 10-15 entities/minute (AI-assisted)
- **ROI**: 400% productivity increase

### Accuracy Improvement
- **Before**: 75% correct on first try (guessing)
- **After**: 90%+ correct (AI suggestions)
- **Impact**: Fewer re-imports, cleaner data

### User Experience
- Visual preview eliminates confusion
- AI suggestions reduce cognitive load
- Batch workflows handle bulk corrections

## Conclusion

The Object Reclassifier exists but is untested and basic. This project transforms it into a production-ready, AI-powered classification workbench that makes reviewing low-confidence imports fast, accurate, and even enjoyable. The 3-week timeline delivers immediate value while setting the foundation for advanced features.

**Recommended Start**: After Project #1 (AI Agent Toolkit) populates embeddings table.
