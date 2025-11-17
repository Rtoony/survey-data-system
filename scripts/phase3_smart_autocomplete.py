#!/usr/bin/env python3
"""
Phase 3 - Smart Autocomplete with AI

This script contains the implementation for AI-powered autocomplete that uses
vector similarity to suggest relevant items as users type.

Copy-paste ready code for integration into your application.
"""

# ============================================
# 1. API ENDPOINT FOR SMART AUTOCOMPLETE
# ============================================
# Add this to app.py

SMART_AUTOCOMPLETE_ENDPOINT = """
@app.route('/api/ai/autocomplete', methods=['POST'])
def smart_autocomplete():
    \"\"\"
    Provide AI-powered autocomplete suggestions.

    This endpoint:
    1. Takes partial input text
    2. Uses hybrid search for semantic matching
    3. Returns top suggestions with metadata
    4. Learns from user selections (optional)
    \"\"\"
    try:
        data = request.get_json()
        partial_text = data.get('text', '').strip()
        entity_type = data.get('entity_type')  # Optional filter
        limit = data.get('limit', 10)
        context = data.get('context', {})  # Optional context (e.g., current project)

        # Minimum 2 characters to search
        if len(partial_text) < 2:
            return jsonify({
                'success': True,
                'suggestions': [],
                'count': 0
            })

        # Build filter clause
        filter_clause = ""
        params = [partial_text, limit]

        if entity_type:
            filter_clause += " AND se.entity_type = %s"
            params.append(entity_type)

        if context.get('project_id'):
            filter_clause += " AND se.source_project_id = %s"
            params.append(context['project_id'])

        # Use hybrid search for intelligent suggestions
        query = f\"\"\"
            WITH search_results AS (
                SELECT
                    entity_id,
                    canonical_name,
                    entity_type,
                    description,
                    combined_score,
                    source_table
                FROM hybrid_search(%s, %s)
                WHERE combined_score > 0.3  -- Only relevant suggestions
                {filter_clause}
            )
            SELECT
                sr.*,
                -- Add usage frequency (if tracking user selections)
                COALESCE(
                    (SELECT COUNT(*) FROM user_autocomplete_selections
                     WHERE entity_id = sr.entity_id
                       AND created_at >= CURRENT_DATE - INTERVAL '30 days'),
                    0
                ) as usage_count
            FROM search_results sr
            ORDER BY
                -- Prioritize: exact matches, then usage, then AI score
                CASE WHEN LOWER(canonical_name) LIKE LOWER(%s) || '%%' THEN 0 ELSE 1 END,
                usage_count DESC,
                combined_score DESC
            LIMIT %s
        \"\"\"

        # Add partial_text prefix match param and limit
        params.extend([partial_text, limit])

        suggestions = execute_query(query, params)

        # Format suggestions for autocomplete UI
        formatted_suggestions = []
        for suggestion in suggestions:
            formatted_suggestions.append({
                'value': suggestion['canonical_name'],
                'label': suggestion['canonical_name'],
                'entity_id': str(suggestion['entity_id']),
                'entity_type': suggestion['entity_type'],
                'description': suggestion.get('description'),
                'score': float(suggestion['combined_score']),
                'source': suggestion['source_table'],
                'metadata': {
                    'usage_count': suggestion.get('usage_count', 0),
                    'is_popular': suggestion.get('usage_count', 0) > 10
                }
            })

        return jsonify({
            'success': True,
            'suggestions': formatted_suggestions,
            'count': len(formatted_suggestions),
            'query': partial_text
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'suggestions': []
        }), 500


@app.route('/api/ai/autocomplete/track', methods=['POST'])
def track_autocomplete_selection():
    \"\"\"
    Track user selections to improve future suggestions.
    This creates a feedback loop for learning user preferences.
    \"\"\"
    try:
        data = request.get_json()
        entity_id = data.get('entity_id')
        query_text = data.get('query_text')
        user_id = data.get('user_id', 'anonymous')  # Get from session

        if not entity_id:
            return jsonify({'error': 'entity_id required'}), 400

        # Store selection for analytics
        query = \"\"\"
            INSERT INTO user_autocomplete_selections
            (entity_id, query_text, user_id, created_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        \"\"\"

        execute_query(query, [entity_id, query_text, user_id])

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
"""

# ============================================
# 2. DATABASE MIGRATION FOR TRACKING
# ============================================
# Optional: Create this table to track selections and improve suggestions

TRACKING_TABLE_SQL = """
-- Track autocomplete selections for learning
CREATE TABLE IF NOT EXISTS user_autocomplete_selections (
    selection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES standards_entities(entity_id),
    query_text TEXT NOT NULL,
    user_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_autocomplete_selections_entity
ON user_autocomplete_selections(entity_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_autocomplete_selections_user
ON user_autocomplete_selections(user_id, created_at DESC);

-- View for popular suggestions
CREATE OR REPLACE VIEW popular_autocomplete_suggestions AS
SELECT
    se.entity_id,
    se.canonical_name,
    se.entity_type,
    COUNT(*) as selection_count,
    COUNT(DISTINCT uas.user_id) as unique_users,
    MAX(uas.created_at) as last_selected
FROM user_autocomplete_selections uas
JOIN standards_entities se ON uas.entity_id = se.entity_id
WHERE uas.created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY se.entity_id, se.canonical_name, se.entity_type
HAVING COUNT(*) >= 5
ORDER BY selection_count DESC;
"""

# ============================================
# 3. FRONTEND JAVASCRIPT COMPONENT
# ============================================

AUTOCOMPLETE_JAVASCRIPT = """
/**
 * Smart Autocomplete Component
 * Provides AI-powered suggestions with debouncing and keyboard navigation
 */
class SmartAutocomplete {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.options = {
            minChars: 2,
            debounceMs: 300,
            maxSuggestions: 10,
            entityType: null,
            context: {},
            onSelect: null,
            trackSelections: true,
            ...options
        };

        this.suggestions = [];
        this.selectedIndex = -1;
        this.debounceTimer = null;
        this.isLoading = false;

        this.init();
    }

    init() {
        // Create suggestions container
        this.container = document.createElement('div');
        this.container.className = 'autocomplete-container';
        this.container.style.display = 'none';

        // Position relative to input
        this.input.parentElement.style.position = 'relative';
        this.input.parentElement.appendChild(this.container);

        // Add event listeners
        this.input.addEventListener('input', this.handleInput.bind(this));
        this.input.addEventListener('keydown', this.handleKeydown.bind(this));
        this.input.addEventListener('focus', this.handleFocus.bind(this));
        this.input.addEventListener('blur', this.handleBlur.bind(this));

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.container.contains(e.target)) {
                this.hide();
            }
        });
    }

    handleInput(e) {
        const text = e.target.value.trim();

        // Clear debounce timer
        clearTimeout(this.debounceTimer);

        if (text.length < this.options.minChars) {
            this.hide();
            return;
        }

        // Show loading state
        this.showLoading();

        // Debounce API call
        this.debounceTimer = setTimeout(() => {
            this.fetchSuggestions(text);
        }, this.options.debounceMs);
    }

    handleKeydown(e) {
        if (!this.container.style.display || this.container.style.display === 'none') {
            return;
        }

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectedIndex = Math.min(
                    this.selectedIndex + 1,
                    this.suggestions.length - 1
                );
                this.updateSelection();
                break;

            case 'ArrowUp':
                e.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, -1);
                this.updateSelection();
                break;

            case 'Enter':
                e.preventDefault();
                if (this.selectedIndex >= 0) {
                    this.selectSuggestion(this.suggestions[this.selectedIndex]);
                }
                break;

            case 'Escape':
                this.hide();
                break;
        }
    }

    handleFocus() {
        if (this.suggestions.length > 0) {
            this.show();
        }
    }

    handleBlur() {
        // Delay hide to allow click on suggestion
        setTimeout(() => this.hide(), 200);
    }

    async fetchSuggestions(text) {
        this.isLoading = true;

        try {
            const response = await fetch('/api/ai/autocomplete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    entity_type: this.options.entityType,
                    limit: this.options.maxSuggestions,
                    context: this.options.context
                })
            });

            const data = await response.json();

            if (data.success) {
                this.suggestions = data.suggestions;
                this.renderSuggestions();
            } else {
                console.error('Autocomplete error:', data.error);
                this.hide();
            }

        } catch (error) {
            console.error('Autocomplete fetch error:', error);
            this.hide();
        } finally {
            this.isLoading = false;
        }
    }

    renderSuggestions() {
        if (this.suggestions.length === 0) {
            this.hide();
            return;
        }

        this.container.innerHTML = '';
        this.selectedIndex = -1;

        this.suggestions.forEach((suggestion, index) => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.dataset.index = index;

            // Highlight matching text
            const matchText = this.highlightMatch(
                suggestion.label,
                this.input.value
            );

            item.innerHTML = `
                <div class="autocomplete-item-main">
                    <div class="autocomplete-item-label">
                        <i class="fas fa-${this.getEntityIcon(suggestion.entity_type)}"></i>
                        ${matchText}
                    </div>
                    ${suggestion.metadata.is_popular ?
                        '<span class="autocomplete-badge popular"><i class="fas fa-fire"></i> Popular</span>' : ''}
                    ${suggestion.score > 0.8 ?
                        '<span class="autocomplete-badge high-match"><i class="fas fa-check-circle"></i> Best match</span>' : ''}
                </div>
                ${suggestion.description ?
                    `<div class="autocomplete-item-description">${suggestion.description}</div>` : ''}
            `;

            item.addEventListener('click', () => {
                this.selectSuggestion(suggestion);
            });

            item.addEventListener('mouseenter', () => {
                this.selectedIndex = index;
                this.updateSelection();
            });

            this.container.appendChild(item);
        });

        this.show();
    }

    updateSelection() {
        const items = this.container.querySelectorAll('.autocomplete-item');
        items.forEach((item, index) => {
            if (index === this.selectedIndex) {
                item.classList.add('selected');
                // Scroll into view if needed
                item.scrollIntoView({ block: 'nearest' });
            } else {
                item.classList.remove('selected');
            }
        });
    }

    selectSuggestion(suggestion) {
        this.input.value = suggestion.value;

        // Track selection for learning
        if (this.options.trackSelections) {
            this.trackSelection(suggestion, this.input.value);
        }

        // Call user callback
        if (this.options.onSelect) {
            this.options.onSelect(suggestion);
        }

        this.hide();

        // Trigger change event
        const event = new Event('change', { bubbles: true });
        this.input.dispatchEvent(event);
    }

    async trackSelection(suggestion, queryText) {
        try {
            await fetch('/api/ai/autocomplete/track', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    entity_id: suggestion.entity_id,
                    query_text: queryText
                })
            });
        } catch (error) {
            console.error('Error tracking selection:', error);
        }
    }

    highlightMatch(text, query) {
        if (!query) return text;

        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<strong>$1</strong>');
    }

    getEntityIcon(entityType) {
        const icons = {
            'layer': 'layer-group',
            'block': 'cube',
            'detail': 'info-circle',
            'utility_structure': 'hard-hat',
            'survey_point': 'map-marker-alt'
        };
        return icons[entityType] || 'database';
    }

    showLoading() {
        this.container.innerHTML = `
            <div class="autocomplete-loading">
                <i class="fas fa-spinner fa-spin"></i> Searching...
            </div>
        `;
        this.show();
    }

    show() {
        this.container.style.display = 'block';
    }

    hide() {
        this.container.style.display = 'none';
    }

    destroy() {
        this.container.remove();
        clearTimeout(this.debounceTimer);
    }
}

// Usage example:
/*
const layerInput = document.getElementById('layer-name-input');
const autocomplete = new SmartAutocomplete(layerInput, {
    entityType: 'layer',
    onSelect: (suggestion) => {
        console.log('Selected:', suggestion);
        // Do something with the selection
    }
});
*/
"""

# ============================================
# 4. CSS STYLES
# ============================================

AUTOCOMPLETE_CSS = """
/* Smart Autocomplete Styles */
.autocomplete-container {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #e0e0e0;
    border-top: none;
    border-radius: 0 0 8px 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    max-height: 400px;
    overflow-y: auto;
    z-index: 1000;
    margin-top: 4px;
}

.autocomplete-item {
    padding: 12px 16px;
    cursor: pointer;
    border-bottom: 1px solid #f0f0f0;
    transition: background-color 0.2s;
}

.autocomplete-item:last-child {
    border-bottom: none;
}

.autocomplete-item:hover,
.autocomplete-item.selected {
    background-color: #f8f9fa;
}

.autocomplete-item-main {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
}

.autocomplete-item-label {
    font-weight: 500;
    color: #333;
    display: flex;
    align-items: center;
    gap: 8px;
}

.autocomplete-item-label i {
    color: #2196F3;
}

.autocomplete-item-label strong {
    color: #667eea;
    font-weight: 600;
}

.autocomplete-item-description {
    font-size: 12px;
    color: #666;
    margin-left: 28px;
}

.autocomplete-badge {
    font-size: 10px;
    padding: 3px 8px;
    border-radius: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.autocomplete-badge.popular {
    background: #FFF3E0;
    color: #F57C00;
}

.autocomplete-badge.high-match {
    background: #E8F5E9;
    color: #2E7D32;
}

.autocomplete-loading {
    padding: 16px;
    text-align: center;
    color: #666;
}

.autocomplete-loading i {
    margin-right: 8px;
}

/* Enhance input styling when autocomplete is active */
.autocomplete-input-wrapper {
    position: relative;
}

.autocomplete-input-wrapper input {
    padding-right: 40px;
}

.autocomplete-input-wrapper .autocomplete-indicator {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: #999;
    pointer-events: none;
}

.autocomplete-input-wrapper input:focus + .autocomplete-indicator {
    color: #667eea;
}
"""


def main():
    """Print implementation guide"""
    print("=" * 70)
    print("PHASE 3 - SMART AUTOCOMPLETE WITH AI")
    print("=" * 70)
    print()
    print("This file contains the implementation for AI-powered autocomplete.")
    print()
    print("Features:")
    print("  - Semantic matching using hybrid search")
    print("  - Learns from user selections")
    print("  - Keyboard navigation (arrows, enter, escape)")
    print("  - Debounced API calls")
    print("  - Popular suggestions highlighted")
    print()
    print("Files to create/modify:")
    print("  1. app.py - Add SMART_AUTOCOMPLETE_ENDPOINT")
    print("  2. database/migrations/ - Optional: Add TRACKING_TABLE_SQL")
    print("  3. static/js/autocomplete.js - Add AUTOCOMPLETE_JAVASCRIPT")
    print("  4. static/css/autocomplete.css - Add AUTOCOMPLETE_CSS")
    print()
    print("See PHASE3_INTEGRATION_GUIDE.md for detailed instructions")


if __name__ == '__main__':
    main()
