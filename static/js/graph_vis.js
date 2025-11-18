/**
 * Graph Visualization with Cytoscape.js
 * Handles knowledge graph rendering and interactions
 */

let cy = null;
let currentLayout = 'cola';
let graphData = { nodes: [], edges: [] };

// Initialize Cytoscape
function initializeCytoscape() {
    cy = cytoscape({
        container: document.getElementById('cy'),

        style: [
            {
                selector: 'node',
                style: {
                    'label': 'data(label)',
                    'background-color': 'data(color)',
                    'color': '#fff',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'font-size': '12px',
                    'width': 'data(size)',
                    'height': 'data(size)',
                    'border-width': 2,
                    'border-color': '#fff',
                    'text-wrap': 'wrap',
                    'text-max-width': '80px'
                }
            },
            {
                selector: 'node:selected',
                style: {
                    'border-width': 4,
                    'border-color': '#00ff00',
                    'background-color': '#00bcd4'
                }
            },
            {
                selector: 'node.highlighted',
                style: {
                    'background-color': '#ff4444',
                    'border-color': '#ff4444',
                    'border-width': 4
                }
            },
            {
                selector: 'node.community-0',
                style: { 'background-color': '#00bcd4' }
            },
            {
                selector: 'node.community-1',
                style: { 'background-color': '#4caf50' }
            },
            {
                selector: 'node.community-2',
                style: { 'background-color': '#ff9800' }
            },
            {
                selector: 'node.community-3',
                style: { 'background-color': '#9c27b0' }
            },
            {
                selector: 'node.community-4',
                style: { 'background-color': '#f44336' }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#555',
                    'target-arrow-color': '#555',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'opacity': 0.6
                }
            },
            {
                selector: 'edge:selected',
                style: {
                    'line-color': '#00ff00',
                    'target-arrow-color': '#00ff00',
                    'width': 4,
                    'opacity': 1
                }
            },
            {
                selector: 'edge.bridge',
                style: {
                    'line-color': '#ff4444',
                    'target-arrow-color': '#ff4444',
                    'width': 4,
                    'opacity': 1
                }
            }
        ],

        layout: {
            name: 'cola',
            animate: true,
            animationDuration: 500
        }
    });

    // Add event listeners
    addCytoscapeEventListeners();
}

function addCytoscapeEventListeners() {
    // Node hover tooltip
    cy.on('mouseover', 'node', function(evt) {
        const node = evt.target;
        const tooltip = document.getElementById('nodeTooltip');
        const data = node.data();

        tooltip.innerHTML = `
            <div class="tooltip-title">${data.label}</div>
            <div class="tooltip-item"><strong>Type:</strong> ${data.entity_type}</div>
            ${data.quality_score !== undefined ? `<div class="tooltip-item"><strong>Quality:</strong> ${(data.quality_score * 100).toFixed(0)}%</div>` : ''}
            ${data.pagerank !== undefined ? `<div class="tooltip-item"><strong>PageRank:</strong> ${data.pagerank.toFixed(4)}</div>` : ''}
            ${data.degree !== undefined ? `<div class="tooltip-item"><strong>Connections:</strong> ${data.degree}</div>` : ''}
        `;

        const renderedPosition = node.renderedPosition();
        tooltip.style.left = (renderedPosition.x + 20) + 'px';
        tooltip.style.top = (renderedPosition.y - 20) + 'px';
        tooltip.style.display = 'block';
    });

    cy.on('mouseout', 'node', function() {
        document.getElementById('nodeTooltip').style.display = 'none';
    });

    // Node click - show details
    cy.on('tap', 'node', function(evt) {
        const node = evt.target;
        console.log('Node clicked:', node.data());
        // Could open a modal with full entity details
    });

    // Edge click
    cy.on('tap', 'edge', function(evt) {
        const edge = evt.target;
        console.log('Edge clicked:', edge.data());
    });
}

// Load graph data from API
async function loadGraph(projectId = null, entityType = null) {
    const loadBtn = document.getElementById('loadGraphBtn');
    loadBtn.disabled = true;
    loadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';

    try {
        // For demo, we'll load entities and relationships separately
        // In production, you might have a dedicated endpoint

        // Load structure analysis for stats
        let statsUrl = '/api/graphrag/analytics/structure';
        if (projectId) {
            statsUrl += `?project_id=${projectId}`;
        }

        const statsResponse = await fetch(statsUrl);
        const stats = await statsResponse.json();

        updateGraphStats(stats);

        // Build sample graph data
        // In production, you'd fetch actual entities and relationships
        graphData = await buildGraphData(projectId, entityType);

        renderGraph(graphData);

    } catch (error) {
        console.error('Error loading graph:', error);
        alert('Error loading graph: ' + error.message);
    } finally {
        loadBtn.disabled = false;
        loadBtn.innerHTML = '<i class="fas fa-sync"></i> Load Graph';
    }
}

async function buildGraphData(projectId, entityType) {
    // This is a simplified version
    // In production, you'd query entities and relationships from your API

    const nodes = [];
    const edges = [];

    // Sample data structure
    const sampleEntities = [
        { id: '1', label: 'Basin MH-101', type: 'utility_structure', quality: 0.95 },
        { id: '2', label: 'Pipe P-001', type: 'utility_line', quality: 0.88 },
        { id: '3', label: 'Basin MH-102', type: 'utility_structure', quality: 0.92 },
        { id: '4', label: 'Survey Point SP-1', type: 'survey_point', quality: 0.85 },
        { id: '5', label: 'Pipe P-002', type: 'utility_line', quality: 0.90 }
    ];

    const sampleRelationships = [
        { source: '1', target: '2', type: 'connected_to' },
        { source: '2', target: '3', type: 'connected_to' },
        { source: '4', target: '1', type: 'near' },
        { source: '3', target: '5', type: 'connected_to' }
    ];

    // Convert to Cytoscape format
    sampleEntities.forEach(entity => {
        nodes.push({
            data: {
                id: entity.id,
                label: entity.label,
                entity_type: entity.type,
                quality_score: entity.quality,
                color: getNodeColor(entity.type),
                size: 40 + (entity.quality * 20)
            }
        });
    });

    sampleRelationships.forEach(rel => {
        edges.push({
            data: {
                id: `${rel.source}-${rel.target}`,
                source: rel.source,
                target: rel.target,
                label: rel.type
            }
        });
    });

    return { nodes, edges };
}

function getNodeColor(entityType) {
    const colors = {
        'utility_structure': '#00bcd4',
        'utility_line': '#4caf50',
        'survey_point': '#ff9800',
        'bmp': '#9c27b0'
    };
    return colors[entityType] || '#999';
}

function renderGraph(data) {
    if (!cy) {
        initializeCytoscape();
    }

    cy.elements().remove();
    cy.add(data.nodes);
    cy.add(data.edges);

    applyLayout(currentLayout);

    // Update stats
    document.getElementById('nodeCount').textContent = data.nodes.length;
    document.getElementById('edgeCount').textContent = data.edges.length;
}

function applyLayout(layoutName) {
    currentLayout = layoutName;

    const layoutOptions = {
        cola: {
            name: 'cola',
            animate: true,
            animationDuration: 500,
            nodeSpacing: 50,
            edgeLength: 100
        },
        circle: {
            name: 'circle',
            animate: true,
            animationDuration: 500
        },
        grid: {
            name: 'grid',
            animate: true,
            animationDuration: 500,
            rows: Math.ceil(Math.sqrt(cy.nodes().length))
        },
        concentric: {
            name: 'concentric',
            animate: true,
            animationDuration: 500,
            concentric: function(node) {
                return node.degree();
            },
            levelWidth: function() {
                return 2;
            }
        }
    };

    const layout = cy.layout(layoutOptions[layoutName] || layoutOptions.cola);
    layout.run();
}

function updateGraphStats(stats) {
    document.getElementById('nodeCount').textContent = stats.num_nodes || 0;
    document.getElementById('edgeCount').textContent = stats.num_edges || 0;
    document.getElementById('densityValue').textContent = (stats.density || 0).toFixed(4);
}

// Highlight influential nodes using PageRank
async function highlightInfluentialNodes() {
    const btn = document.getElementById('highlightInfluentialBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Computing...';

    try {
        const projectId = document.getElementById('projectSelect').value;
        let url = '/api/graphrag/analytics/influential-nodes?top_k=5&metric=pagerank';
        if (projectId) {
            url += `&project_id=${projectId}`;
        }

        const response = await fetch(url);
        const influential = await response.json();

        // Remove previous highlights
        cy.nodes().removeClass('highlighted');

        // Highlight influential nodes
        influential.forEach(entity => {
            const node = cy.getElementById(entity.entity_id);
            if (node.length > 0) {
                node.addClass('highlighted');
                node.data('pagerank', entity.pagerank_score);
            }
        });

        alert(`Highlighted top ${influential.length} influential nodes`);

    } catch (error) {
        console.error('Error highlighting nodes:', error);
        alert('Error: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-star"></i> Highlight Influential';
    }
}

// Detect and visualize communities
async function findCommunities() {
    const btn = document.getElementById('findCommunitiesBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Detecting...';

    try {
        const projectId = document.getElementById('projectSelect').value;
        let url = '/api/graphrag/analytics/communities?algorithm=louvain';
        if (projectId) {
            url += `&project_id=${projectId}`;
        }

        const response = await fetch(url);
        const result = await response.json();

        // Remove previous community classes
        cy.nodes().removeClass(['community-0', 'community-1', 'community-2', 'community-3', 'community-4']);

        // Apply community colors
        result.communities.forEach((community, index) => {
            community.entity_ids.forEach(entityId => {
                const node = cy.getElementById(entityId);
                if (node.length > 0) {
                    node.addClass(`community-${index % 5}`);
                }
            });
        });

        document.getElementById('communityCount').textContent = result.num_communities;
        alert(`Found ${result.num_communities} communities (Modularity: ${result.modularity.toFixed(3)})`);

    } catch (error) {
        console.error('Error detecting communities:', error);
        alert('Error: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-users"></i> Detect Communities';
    }
}

// Find and highlight bridge edges
async function findBridges() {
    const btn = document.getElementById('findBridgesBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Finding...';

    try {
        const projectId = document.getElementById('projectSelect').value;
        let url = '/api/graphrag/analytics/bridges';
        if (projectId) {
            url += `?project_id=${projectId}`;
        }

        const response = await fetch(url);
        const result = await response.json();

        // Remove previous bridge highlights
        cy.edges().removeClass('bridge');

        // Highlight bridges
        result.bridges.forEach(([source, target]) => {
            const edge = cy.edges(`[source="${source}"][target="${target}"], [source="${target}"][target="${source}"]`);
            if (edge.length > 0) {
                edge.addClass('bridge');
            }
        });

        alert(`Found ${result.count} bridge edges (critical connections)`);

    } catch (error) {
        console.error('Error finding bridges:', error);
        alert('Error: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-bridge"></i> Find Bridges';
    }
}

// Export functions
function exportPNG() {
    const png = cy.png({ full: true, scale: 2 });
    const link = document.createElement('a');
    link.download = 'knowledge-graph.png';
    link.href = png;
    link.click();
}

function exportJSON() {
    const data = {
        nodes: cy.nodes().map(n => n.data()),
        edges: cy.edges().map(e => e.data())
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.download = 'knowledge-graph.json';
    link.href = url;
    link.click();
    URL.revokeObjectURL(url);
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeCytoscape();

    // Load graph button
    document.getElementById('loadGraphBtn').addEventListener('click', function() {
        const projectId = document.getElementById('projectSelect').value;
        const entityType = document.getElementById('entityTypeSelect').value;
        loadGraph(projectId || null, entityType || null);
    });

    // Layout buttons
    document.querySelectorAll('.layout-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.layout-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            applyLayout(this.dataset.layout);
        });
    });

    // Control buttons
    document.getElementById('zoomInBtn').addEventListener('click', () => cy.zoom(cy.zoom() * 1.2));
    document.getElementById('zoomOutBtn').addEventListener('click', () => cy.zoom(cy.zoom() * 0.8));
    document.getElementById('fitBtn').addEventListener('click', () => cy.fit());
    document.getElementById('resetBtn').addEventListener('click', () => cy.reset());

    // Analytics buttons
    document.getElementById('highlightInfluentialBtn').addEventListener('click', highlightInfluentialNodes);
    document.getElementById('findCommunitiesBtn').addEventListener('click', findCommunities);
    document.getElementById('findBridgesBtn').addEventListener('click', findBridges);

    // Export buttons
    document.getElementById('exportPngBtn').addEventListener('click', exportPNG);
    document.getElementById('exportJsonBtn').addEventListener('click', exportJSON);

    // Load initial graph with sample data
    loadGraph();
});
