#!/usr/bin/env python3
"""
Phase 3 - Natural Language Query Interface

This script contains the implementation for a ChatGPT-style natural language
query interface that leverages hybrid search and Graph RAG.

Copy-paste ready code for integration into your application.
"""

# ============================================
# 1. API ENDPOINT FOR NATURAL LANGUAGE QUERIES
# ============================================
# Add this to app.py

NL_QUERY_ENDPOINT = """
@app.route('/api/ai/query', methods=['POST'])
def natural_language_query():
    \"\"\"
    Process natural language queries and return intelligent results.

    This endpoint:
    1. Extracts intent and entities from natural language
    2. Uses hybrid search for semantic matching
    3. Follows Graph RAG relationships for context
    4. Returns formatted results with explanations
    \"\"\"
    try:
        data = request.get_json()
        query_text = data.get('query')
        context_id = data.get('context_entity_id')  # Optional context for follow-up questions
        include_related = data.get('include_related', True)
        max_results = data.get('max_results', 10)

        if not query_text or len(query_text.strip()) < 2:
            return jsonify({'error': 'Query text must be at least 2 characters'}), 400

        # Parse query intent (simple keyword extraction for now)
        intent = parse_query_intent(query_text)

        # Execute hybrid search
        search_query = \"\"\"
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
            ORDER BY combined_score DESC
        \"\"\"

        search_results = execute_query(search_query, [query_text, max_results])

        # If include_related, fetch Graph RAG context for top results
        enhanced_results = []
        for result in search_results[:5]:  # Enhance top 5
            enhanced = dict(result)

            if include_related:
                # Get related entities via Graph RAG
                related_query = \"\"\"
                    SELECT
                        entity_id,
                        canonical_name,
                        entity_type,
                        hop_distance,
                        relationship_path
                    FROM find_related_entities(%s::uuid, 2, NULL)
                    WHERE hop_distance <= 2
                    ORDER BY hop_distance
                    LIMIT 5
                \"\"\"
                related = execute_query(related_query, [result['entity_id']])
                enhanced['related_entities'] = related

            enhanced_results.append(enhanced)

        # Generate natural language explanation
        explanation = generate_explanation(query_text, enhanced_results, intent)

        return jsonify({
            'success': True,
            'query': query_text,
            'intent': intent,
            'explanation': explanation,
            'results': enhanced_results,
            'result_count': len(enhanced_results),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def parse_query_intent(query_text):
    \"\"\"
    Extract intent from natural language query.
    Simple keyword-based approach (can be enhanced with OpenAI later).
    \"\"\"
    query_lower = query_text.lower()

    intent = {
        'type': 'general_search',
        'action': None,
        'entity_type': None,
        'location': None,
        'filters': []
    }

    # Detect action intent
    if any(word in query_lower for word in ['find', 'search', 'show', 'list']):
        intent['action'] = 'find'
    elif any(word in query_lower for word in ['similar', 'like', 'related']):
        intent['action'] = 'similar'
        intent['type'] = 'similarity_search'
    elif any(word in query_lower for word in ['compare', 'difference']):
        intent['action'] = 'compare'
        intent['type'] = 'comparison'

    # Detect entity type
    if 'layer' in query_lower:
        intent['entity_type'] = 'layer'
    elif 'block' in query_lower:
        intent['entity_type'] = 'block'
    elif any(word in query_lower for word in ['storm', 'sewer', 'utility']):
        intent['entity_type'] = 'utility'

    # Detect location/municipality
    if 'where' in query_lower or 'location' in query_lower:
        intent['filters'].append('location')

    return intent


def generate_explanation(query_text, results, intent):
    \"\"\"Generate natural language explanation of results.\"\"\"
    if not results:
        return f\"I couldn't find any results matching '{query_text}'. Try rephrasing your query or using different keywords.\"

    count = len(results)
    top_result = results[0]
    entity_type = top_result.get('entity_type', 'item')

    explanation = f\"I found {count} {entity_type}(s) matching '{query_text}'. \"

    if intent['action'] == 'similar':
        explanation += f\"These are semantically similar based on AI analysis. \"

    if top_result.get('combined_score', 0) > 0.8:
        explanation += f\"The top result '{top_result['canonical_name']}' is a very strong match ({top_result['combined_score']*100:.0f}% confidence).\"
    elif top_result.get('combined_score', 0) > 0.6:
        explanation += f\"The top result '{top_result['canonical_name']}' is a good match ({top_result['combined_score']*100:.0f}% confidence).\"
    else:
        explanation += f\"The best match is '{top_result['canonical_name']}', though it's not a perfect match ({top_result['combined_score']*100:.0f}% confidence).\"

    if top_result.get('related_entities'):
        related_count = len(top_result['related_entities'])
        explanation += f\" This entity is connected to {related_count} other entities in the knowledge graph.\"

    return explanation
"""

# ============================================
# 2. FRONTEND COMPONENT
# ============================================
# Add this to a new template: templates/ai_query.html or integrate into existing page

NL_QUERY_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-Powered Search</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .ai-query-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .chat-interface {
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            height: 80vh;
        }

        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px 12px 0 0;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .chat-header h2 {
            margin: 0;
            font-size: 20px;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }

        .message {
            margin-bottom: 20px;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .message.user {
            display: flex;
            justify-content: flex-end;
        }

        .message.ai {
            display: flex;
            justify-content: flex-start;
        }

        .message-bubble {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
        }

        .message.user .message-bubble {
            background: #667eea;
            color: white;
        }

        .message.ai .message-bubble {
            background: white;
            border: 1px solid #e0e0e0;
            color: #333;
        }

        .message-meta {
            font-size: 11px;
            color: #999;
            margin-top: 4px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .ai-explanation {
            background: #E3F2FD;
            padding: 12px;
            border-radius: 8px;
            margin: 12px 0;
            font-size: 14px;
            color: #1976D2;
            border-left: 3px solid #2196F3;
        }

        .result-card-compact {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
            cursor: pointer;
            transition: all 0.2s;
        }

        .result-card-compact:hover {
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transform: translateX(4px);
        }

        .result-header-compact {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .result-title-compact {
            font-weight: 600;
            color: #333;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .confidence-badge {
            background: #4CAF50;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }

        .related-entities {
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid #f0f0f0;
        }

        .related-tag {
            display: inline-block;
            background: #f0f0f0;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin: 2px;
        }

        .chat-input-container {
            padding: 20px;
            background: white;
            border-radius: 0 0 12px 12px;
            border-top: 1px solid #e0e0e0;
        }

        .chat-input-wrapper {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .chat-input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 24px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }

        .chat-input:focus {
            border-color: #667eea;
        }

        .send-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            width: 48px;
            height: 48px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s;
        }

        .send-button:hover {
            transform: scale(1.1);
        }

        .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 12px;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #999;
            animation: typing 1.4s infinite;
        }

        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }

        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }

        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
                opacity: 0.5;
            }
            30% {
                transform: translateY(-10px);
                opacity: 1;
            }
        }

        .quick-actions {
            display: flex;
            gap: 8px;
            margin-top: 12px;
            flex-wrap: wrap;
        }

        .quick-action-btn {
            background: #f0f0f0;
            border: 1px solid #e0e0e0;
            padding: 8px 12px;
            border-radius: 16px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .quick-action-btn:hover {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
    </style>
</head>
<body>
    <div class="ai-query-container">
        <div class="chat-interface">
            <div class="chat-header">
                <i class="fas fa-robot fa-2x"></i>
                <div>
                    <h2>AI Assistant</h2>
                    <p style="margin: 0; font-size: 13px; opacity: 0.9;">Ask me anything about your CAD data</p>
                </div>
            </div>

            <div class="chat-messages" id="chatMessages">
                <div class="message ai">
                    <div>
                        <div class="message-bubble">
                            👋 Hi! I'm your AI assistant. Ask me about layers, blocks, utilities, or any CAD data.
                            I can search semantically, find related items, and explain connections in your data.
                        </div>
                        <div class="message-meta">
                            <i class="fas fa-robot"></i> AI Assistant • Just now
                        </div>
                        <div class="quick-actions">
                            <button class="quick-action-btn" onclick="askQuestion('Find all storm drain layers')">
                                <i class="fas fa-search"></i> Find storm drains
                            </button>
                            <button class="quick-action-btn" onclick="askQuestion('Show me utility structures')">
                                <i class="fas fa-hard-hat"></i> Show utilities
                            </button>
                            <button class="quick-action-btn" onclick="askQuestion('What layers are similar to C-UTIL-STORM?')">
                                <i class="fas fa-network-wired"></i> Find similar
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div class="chat-input-container">
                <div class="chat-input-wrapper">
                    <input
                        type="text"
                        class="chat-input"
                        id="queryInput"
                        placeholder="Ask a question about your data..."
                        onkeypress="handleKeyPress(event)"
                    >
                    <button class="send-button" id="sendButton" onclick="sendQuery()">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        const chatMessages = document.getElementById('chatMessages');
        const queryInput = document.getElementById('queryInput');
        const sendButton = document.getElementById('sendButton');

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendQuery();
            }
        }

        function askQuestion(question) {
            queryInput.value = question;
            sendQuery();
        }

        async function sendQuery() {
            const query = queryInput.value.trim();
            if (!query) return;

            // Add user message
            addMessage('user', query);
            queryInput.value = '';

            // Show typing indicator
            const typingId = addTypingIndicator();

            // Disable input
            sendButton.disabled = true;
            queryInput.disabled = true;

            try {
                const response = await fetch('/api/ai/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        query: query,
                        include_related: true,
                        max_results: 10
                    })
                });

                const data = await response.json();

                // Remove typing indicator
                removeTypingIndicator(typingId);

                if (data.success) {
                    // Add AI response with results
                    addAIResponse(data);
                } else {
                    addMessage('ai', `Sorry, I encountered an error: ${data.error}`);
                }

            } catch (error) {
                removeTypingIndicator(typingId);
                addMessage('ai', `Sorry, I couldn't process your request: ${error.message}`);
            } finally {
                // Re-enable input
                sendButton.disabled = false;
                queryInput.disabled = false;
                queryInput.focus();
            }
        }

        function addMessage(sender, text) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;

            const bubble = document.createElement('div');
            bubble.className = 'message-bubble';
            bubble.textContent = text;

            const meta = document.createElement('div');
            meta.className = 'message-meta';
            meta.innerHTML = sender === 'user'
                ? '<i class="fas fa-user"></i> You • Just now'
                : '<i class="fas fa-robot"></i> AI Assistant • Just now';

            const container = document.createElement('div');
            container.appendChild(bubble);
            container.appendChild(meta);

            messageDiv.appendChild(container);
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function addAIResponse(data) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ai';

            const container = document.createElement('div');
            container.style.maxWidth = '100%';

            // Explanation
            if (data.explanation) {
                const explanationDiv = document.createElement('div');
                explanationDiv.className = 'ai-explanation';
                explanationDiv.innerHTML = `<i class="fas fa-lightbulb"></i> ${data.explanation}`;
                container.appendChild(explanationDiv);
            }

            // Results
            if (data.results && data.results.length > 0) {
                data.results.forEach(result => {
                    const card = createResultCard(result);
                    container.appendChild(card);
                });
            }

            const meta = document.createElement('div');
            meta.className = 'message-meta';
            meta.innerHTML = '<i class="fas fa-robot"></i> AI Assistant • Just now';
            container.appendChild(meta);

            messageDiv.appendChild(container);
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function createResultCard(result) {
            const card = document.createElement('div');
            card.className = 'result-card-compact';

            const confidence = Math.round(result.combined_score * 100);
            const confidenceColor = confidence > 80 ? '#4CAF50' : confidence > 60 ? '#FF9800' : '#9E9E9E';

            card.innerHTML = `
                <div class="result-header-compact">
                    <div class="result-title-compact">
                        <i class="fas fa-${getEntityIcon(result.entity_type)}"></i>
                        ${result.canonical_name}
                    </div>
                    <span class="confidence-badge" style="background: ${confidenceColor}">
                        ${confidence}%
                    </span>
                </div>
                ${result.description ? `<div style="font-size: 12px; color: #666; margin-top: 4px;">${result.description}</div>` : ''}
                ${result.related_entities && result.related_entities.length > 0 ? `
                    <div class="related-entities">
                        <div style="font-size: 11px; color: #999; margin-bottom: 4px;">
                            <i class="fas fa-network-wired"></i> Related:
                        </div>
                        ${result.related_entities.slice(0, 3).map(r =>
                            `<span class="related-tag">${r.canonical_name}</span>`
                        ).join('')}
                        ${result.related_entities.length > 3 ?
                            `<span class="related-tag">+${result.related_entities.length - 3} more</span>`
                            : ''}
                    </div>
                ` : ''}
            `;

            card.onclick = () => viewEntityDetails(result.entity_id);

            return card;
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

        function addTypingIndicator() {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ai';
            messageDiv.id = 'typing-indicator-' + Date.now();

            const container = document.createElement('div');
            const bubble = document.createElement('div');
            bubble.className = 'message-bubble typing-indicator';
            bubble.innerHTML = `
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            `;

            container.appendChild(bubble);
            messageDiv.appendChild(container);
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            return messageDiv.id;
        }

        function removeTypingIndicator(id) {
            const indicator = document.getElementById(id);
            if (indicator) {
                indicator.remove();
            }
        }

        function viewEntityDetails(entityId) {
            // Navigate to entity details page or open modal
            console.log('View details for:', entityId);
            // TODO: Implement entity details view
        }

        // Focus input on load
        window.addEventListener('load', () => {
            queryInput.focus();
        });
    </script>
</body>
</html>
"""

# ============================================
# 3. ROUTE TO SERVE THE PAGE
# ============================================
# Add this to app.py

NL_QUERY_ROUTE = """
@app.route('/ai/query')
def ai_query_interface():
    \"\"\"Serve the AI-powered natural language query interface.\"\"\"
    return render_template('ai_query.html')
"""


def main():
    """Print implementation guide"""
    print("=" * 70)
    print("PHASE 3 - NATURAL LANGUAGE QUERY INTERFACE")
    print("=" * 70)
    print()
    print("This file contains the implementation for a ChatGPT-style")
    print("natural language query interface.")
    print()
    print("Files to create/modify:")
    print("  1. app.py - Add NL_QUERY_ENDPOINT and NL_QUERY_ROUTE")
    print("  2. templates/ai_query.html - Create new template with NL_QUERY_HTML")
    print()
    print("See PHASE3_INTEGRATION_GUIDE.md for detailed instructions")


if __name__ == '__main__':
    main()
