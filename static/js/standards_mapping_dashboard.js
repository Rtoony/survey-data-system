// Standards Mapping Dashboard JavaScript
let allMappings = {
    blocks: [],
    details: [],
    hatches: [],
    materials: [],
    notes: []
};

// Initialize dashboard on load
document.addEventListener('DOMContentLoaded', async () => {
    await loadDashboardStats();
    await loadAllMappings();
});

// Load statistics
async function loadDashboardStats() {
    try {
        const response = await fetch('/api/standards-mapping/stats');
        const data = await response.json();
        
        if (data.error) {
            console.error('Error loading stats:', data.error);
            return;
        }
        
        const stats = data.stats;
        document.getElementById('blockCount').textContent = stats.block_mappings || 0;
        document.getElementById('detailCount').textContent = stats.detail_mappings || 0;
        document.getElementById('hatchCount').textContent = stats.hatch_mappings || 0;
        document.getElementById('materialCount').textContent = stats.material_mappings || 0;
        document.getElementById('noteCount').textContent = stats.note_mappings || 0;
        document.getElementById('relationshipCount').textContent = stats.total_relationships || 0;
    } catch (error) {
        console.error('Failed to load statistics:', error);
    }
}

// Load all mapping data
async function loadAllMappings() {
    try {
        const [blocks, details, hatches, materials, notes] = await Promise.all([
            fetch('/api/standards-mapping/block-mappings').then(r => r.json()),
            fetch('/api/standards-mapping/detail-mappings').then(r => r.json()),
            fetch('/api/standards-mapping/hatch-mappings').then(r => r.json()),
            fetch('/api/standards-mapping/material-mappings').then(r => r.json()),
            fetch('/api/standards-mapping/note-mappings').then(r => r.json())
        ]);
        
        allMappings.blocks = blocks.mappings || [];
        allMappings.details = details.mappings || [];
        allMappings.hatches = hatches.mappings || [];
        allMappings.materials = materials.mappings || [];
        allMappings.notes = notes.mappings || [];
        
        renderMappingTable('block');
        renderMappingTable('detail');
        renderMappingTable('hatch');
        renderMappingTable('material');
        renderMappingTable('note');
    } catch (error) {
        console.error('Failed to load mappings:', error);
    }
}

// Render mapping table
function renderMappingTable(type) {
    const mappings = allMappings[type + 's'] || [];
    const tableId = type + 'MappingsTable';
    const container = document.getElementById(tableId);
    
    if (!container) return;
    
    if (mappings.length === 0) {
        container.innerHTML = `
            <div class="alert" style="text-align: center;">
                <i class="fas fa-inbox"></i> No ${type} mappings found. 
                <a href="/data-manager/${type}-mappings">Add your first mapping</a>
            </div>
        `;
        return;
    }
    
    const html = `
        <table class="mapping-table">
            <thead>
                <tr>
                    <th>Canonical Name (Database)</th>
                    <th>DXF Alias</th>
                    <th>Direction</th>
                    <th>Description</th>
                    <th>Confidence</th>
                </tr>
            </thead>
            <tbody>
                ${mappings.map(m => `
                    <tr>
                        <td><strong>${m.canonical_name || '-'}</strong></td>
                        <td><code>${m.dxf_alias || '-'}</code></td>
                        <td>${getDirectionBadges(m.import_direction, m.export_direction)}</td>
                        <td>${m.description || '-'}</td>
                        <td>${m.confidence_score ? (m.confidence_score * 100).toFixed(0) + '%' : '-'}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    container.innerHTML = html;
}

// Get direction badges
function getDirectionBadges(importDir, exportDir) {
    let badges = '';
    if (importDir) badges += '<span class="badge badge-import">Import</span> ';
    if (exportDir) badges += '<span class="badge badge-export">Export</span>';
    if (importDir && exportDir) {
        badges = '<span class="badge badge-both">Both</span>';
    }
    return badges || '-';
}

// Filter mappings
function filterMappings(type) {
    const searchId = type + 'Search';
    const searchInput = document.getElementById(searchId);
    if (!searchInput) return;
    
    const searchTerm = searchInput.value.toLowerCase();
    const mappings = allMappings[type + 's'] || [];
    
    const filtered = mappings.filter(m => {
        return (m.canonical_name && m.canonical_name.toLowerCase().includes(searchTerm)) ||
               (m.dxf_alias && m.dxf_alias.toLowerCase().includes(searchTerm)) ||
               (m.description && m.description.toLowerCase().includes(searchTerm));
    });
    
    allMappings[type + 's'] = filtered;
    renderMappingTable(type);
    
    if (searchTerm === '') {
        loadAllMappings();
    }
}

// Tab switching
function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(tabName + '-tab').classList.add('active');
}

// Subtab switching
function switchSubtab(subtabName) {
    const parentTab = event.target.closest('.tab-content');
    
    parentTab.querySelectorAll('.subtab-btn').forEach(btn => btn.classList.remove('active'));
    parentTab.querySelectorAll('.subtab-content').forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(subtabName + '-subtab').classList.add('active');
}

// Universal search
async function performUniversalSearch() {
    const searchTerm = document.getElementById('universalSearch').value.toLowerCase();
    const resultsContainer = document.getElementById('searchResults');
    
    if (!searchTerm) {
        resultsContainer.innerHTML = '<div class="alert">Please enter a search term</div>';
        return;
    }
    
    resultsContainer.innerHTML = '<div class="alert"><i class="fas fa-spinner fa-spin"></i> Searching...</div>';
    
    const allResults = [];
    
    Object.keys(allMappings).forEach(type => {
        const mappings = allMappings[type];
        mappings.forEach(m => {
            if ((m.canonical_name && m.canonical_name.toLowerCase().includes(searchTerm)) ||
                (m.dxf_alias && m.dxf_alias.toLowerCase().includes(searchTerm)) ||
                (m.description && m.description.toLowerCase().includes(searchTerm))) {
                allResults.push({
                    type: type,
                    mapping: m
                });
            }
        });
    });
    
    if (allResults.length === 0) {
        resultsContainer.innerHTML = '<div class="alert">No results found</div>';
        return;
    }
    
    const html = `
        <h4>Found ${allResults.length} result(s)</h4>
        <table class="mapping-table">
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Canonical Name</th>
                    <th>DXF Alias</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                ${allResults.map(r => `
                    <tr>
                        <td><span class="badge">${r.type.toUpperCase()}</span></td>
                        <td><strong>${r.mapping.canonical_name || '-'}</strong></td>
                        <td><code>${r.mapping.dxf_alias || '-'}</code></td>
                        <td>${r.mapping.description || '-'}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    resultsContainer.innerHTML = html;
}
