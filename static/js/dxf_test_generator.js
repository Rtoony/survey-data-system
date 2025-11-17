/**
 * DXF Test Generator - Frontend JavaScript
 * Database-driven DXF file generation with proper layer classifications
 */

let objectTypes = [];
let downloadUrl = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadObjectTypes();

    // Attach event listeners
    document.getElementById('generateBtn').addEventListener('click', generateDXF);
    document.getElementById('downloadBtn').addEventListener('click', downloadDXF);
});

/**
 * Load object types from the database via API
 */
async function loadObjectTypes() {
    const loadingState = document.getElementById('loadingState');
    const objectTypesGrid = document.getElementById('objectTypesGrid');

    try {
        loadingState.style.display = 'block';
        objectTypesGrid.style.display = 'none';

        const response = await fetch('/api/tools/dxf-test-generator/object-types');
        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Failed to load object types');
        }

        objectTypes = data.object_types;
        renderObjectTypes(objectTypes);

        loadingState.style.display = 'none';
        objectTypesGrid.style.display = 'block';

    } catch (error) {
        console.error('Error loading object types:', error);
        loadingState.innerHTML = `
            <div style="text-align: center; padding: 4rem 2rem; color: var(--mc-critical-red);">
                <i class="fas fa-exclamation-triangle" style="font-size: 4rem; margin-bottom: 1rem;"></i>
                <p style="font-size: 1.1rem;">Error loading object types</p>
                <p style="font-size: 0.9rem;">${error.message}</p>
                <button class="btn btn-primary" onclick="loadObjectTypes()" style="margin-top: 1rem;">
                    <i class="fas fa-redo"></i> Retry
                </button>
            </div>
        `;
    }
}

/**
 * Render object types grouped by category
 */
function renderObjectTypes(objectTypes) {
    const container = document.getElementById('objectTypesList');

    // Group by entity category
    const grouped = {};
    objectTypes.forEach(obj => {
        const category = obj.entity_category || 'Other';
        if (!grouped[category]) {
            grouped[category] = [];
        }
        grouped[category].push(obj);
    });

    // Generate HTML
    let html = '';
    const categoryOrder = [
        'Utility Lines',
        'Utility Structures',
        'BMPs',
        'Pavement',
        'Survey Points',
        'Street Lights',
        'Alignments',
        'Other'
    ];

    categoryOrder.forEach(category => {
        if (grouped[category] && grouped[category].length > 0) {
            html += `
                <div class="object-type-category">
                    <h3>
                        <i class="fas fa-${getCategoryIcon(category)}"></i>
                        ${category}
                    </h3>
            `;

            grouped[category].forEach(obj => {
                const layerExample = buildExampleLayerName(obj);
                html += `
                    <div class="object-type-item">
                        <div class="object-type-info">
                            <h4>
                                <span class="object-type-badge">${obj.object_type_code}</span>
                                ${obj.full_name}
                            </h4>
                            <p>
                                <span style="color: var(--mc-text-dim);">${obj.discipline_code}-${obj.category_code}</span>
                                <span style="margin-left: 1rem; color: var(--mc-primary); font-family: 'Courier New', monospace; font-size: 0.8rem;">
                                    <i class="fas fa-layer-group"></i> ${layerExample}
                                </span>
                            </p>
                        </div>
                        <div>
                            <input
                                type="number"
                                class="quantity-input"
                                data-object-type="${obj.object_type_code}"
                                value="10"
                                min="0"
                                max="1000"
                                step="1"
                            >
                        </div>
                    </div>
                `;
            });

            html += `</div>`;
        }
    });

    container.innerHTML = html;
}

/**
 * Get icon for category
 */
function getCategoryIcon(category) {
    const icons = {
        'Utility Lines': 'pipe',
        'Utility Structures': 'dot-circle',
        'BMPs': 'water',
        'Pavement': 'road',
        'Survey Points': 'map-marker-alt',
        'Street Lights': 'lightbulb',
        'Alignments': 'route',
        'Other': 'shapes'
    };
    return icons[category] || 'shapes';
}

/**
 * Build example layer name for an object type
 */
function buildExampleLayerName(obj) {
    const attrs = getExampleAttributes(obj.object_type_code);
    const parts = [
        obj.discipline_code,
        obj.category_code,
        obj.object_type_code
    ];
    if (attrs) parts.push(attrs);
    parts.push('NEW');
    parts.push(obj.default_geometry);
    return parts.join('-');
}

/**
 * Get example attributes for object type
 */
function getExampleAttributes(objectType) {
    const examples = {
        'STORM': '12IN',
        'SANIT': '8IN',
        'WATER': '6IN',
        'MH': 'CONC',
        'INLET': 'TYPE-A',
        'BIOR': 'STORAGE',
        'SWALE': 'TREATMENT',
        'POND': 'DETENTION'
    };
    return examples[objectType] || '';
}

/**
 * Set preset quantities for all object types
 */
function setPreset(preset) {
    const quantities = {
        'light': 50,
        'medium': 200,
        'heavy': 500
    };

    const value = quantities[preset] || 10;
    const inputs = document.querySelectorAll('.quantity-input');
    inputs.forEach(input => {
        input.value = value;
    });
}

/**
 * Collect entity counts from the form
 */
function collectEntityCounts() {
    const counts = {};
    const inputs = document.querySelectorAll('.quantity-input');

    inputs.forEach(input => {
        const objectType = input.dataset.objectType;
        const quantity = parseInt(input.value) || 0;
        if (quantity > 0) {
            counts[objectType] = quantity;
        }
    });

    return counts;
}

/**
 * Generate DXF file
 */
async function generateDXF() {
    const generateBtn = document.getElementById('generateBtn');
    const statusDisplay = document.getElementById('statusDisplay');
    const downloadBtn = document.getElementById('downloadBtn');

    try {
        // Disable button and show loading state
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';

        // Show status display
        statusDisplay.style.display = 'block';
        statusDisplay.innerHTML = `
            <div class="status-banner info">
                <h3 style="margin: 0 0 0.5rem 0;">
                    <i class="fas fa-cog fa-spin"></i> Generating DXF File...
                </h3>
                <p style="margin: 0;">Please wait while the test DXF is being generated.</p>
            </div>
        `;

        // Collect configuration
        const config = {
            coordinate_system: document.getElementById('coordSystem').value,
            project_name: document.getElementById('projectName').value,
            entity_counts: collectEntityCounts(),
            include_attributes: document.getElementById('includeAttributes').checked,
            randomize_phases: document.getElementById('randomizePhases').checked
        };

        // Validate
        const totalEntities = Object.values(config.entity_counts).reduce((a, b) => a + b, 0);
        if (totalEntities === 0) {
            throw new Error('Please select at least one object type with quantity > 0');
        }

        // Send request
        const response = await fetch('/api/tools/dxf-test-generator/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Failed to generate DXF file');
        }

        // Success! Show download button
        downloadUrl = data.download_url;

        statusDisplay.innerHTML = `
            <div class="status-banner success">
                <h3 style="margin: 0 0 0.5rem 0;">
                    <i class="fas fa-check-circle"></i> DXF File Generated Successfully!
                </h3>
                <p style="margin: 0 0 1rem 0;">
                    <strong>File:</strong> ${data.filename}
                </p>
                ${renderStats(data.stats)}
            </div>
        `;

        downloadBtn.style.display = 'block';

    } catch (error) {
        console.error('Error generating DXF:', error);
        statusDisplay.innerHTML = `
            <div class="status-banner error">
                <h3 style="margin: 0 0 0.5rem 0;">
                    <i class="fas fa-exclamation-triangle"></i> Generation Failed
                </h3>
                <p style="margin: 0;">${error.message}</p>
            </div>
        `;
    } finally {
        // Re-enable button
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fas fa-play"></i> Generate DXF File';
    }
}

/**
 * Render statistics about generated file
 */
function renderStats(stats) {
    if (!stats || stats.error) {
        return '';
    }

    let html = '<div class="stats-grid">';

    html += `
        <div class="stat-item">
            <div class="value">${stats.total_entities || 0}</div>
            <div class="label">Total Entities</div>
        </div>
    `;

    html += `
        <div class="stat-item">
            <div class="value">${stats.layers || 0}</div>
            <div class="label">Layers Created</div>
        </div>
    `;

    // Show entity type breakdown
    if (stats.entity_types) {
        const entityTypes = Object.keys(stats.entity_types).length;
        html += `
            <div class="stat-item">
                <div class="value">${entityTypes}</div>
                <div class="label">Entity Types</div>
            </div>
        `;
    }

    html += '</div>';

    // Show layer names sample
    if (stats.layer_names && stats.layer_names.length > 0) {
        html += `
            <div style="margin-top: 1rem;">
                <h4 style="color: var(--mc-text-dim); font-size: 0.9rem; margin-bottom: 0.5rem;">
                    Sample Layer Names:
                </h4>
                <div style="background: var(--mc-dark-3); padding: 1rem; border-radius: 4px; max-height: 150px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 0.8rem; line-height: 1.6;">
                    ${stats.layer_names.slice(0, 10).map(name => `<div>${name}</div>`).join('')}
                    ${stats.layer_names.length > 10 ? `<div style="color: var(--mc-text-dim); margin-top: 0.5rem;">... and ${stats.layer_names.length - 10} more</div>` : ''}
                </div>
            </div>
        `;
    }

    return html;
}

/**
 * Download generated DXF file
 */
function downloadDXF() {
    if (downloadUrl) {
        window.location.href = downloadUrl;
    }
}
