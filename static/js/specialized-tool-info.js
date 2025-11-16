/**
 * Specialized Tool Info Card Component
 * Database-driven, reusable component that fetches and displays tool information
 * from the layer_object_tools table via API
 */

async function loadToolInfoCard(objectCode, containerId) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container ${containerId} not found`);
        return;
    }

    container.innerHTML = `
        <div class="mc-card" style="background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(0, 255, 136, 0.1)); border-left: 4px solid var(--mc-primary); padding: var(--mc-spacing-lg);">
            <p style="color: var(--mc-muted); text-align: center;">
                <i class="fas fa-spinner fa-spin"></i> Loading tool information...
            </p>
        </div>
    `;

    try {
        const response = await fetch(`/api/cad-standards/tool-layer-examples?tool_code=${objectCode}`);
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        
        if (!data.success || !data.tools || data.tools.length === 0) {
            container.innerHTML = `
                <div class="mc-card" style="background: rgba(255, 68, 68, 0.1); border-left: 4px solid var(--mc-danger); padding: var(--mc-spacing-lg);">
                    <p style="color: var(--mc-danger);">
                        <i class="fas fa-exclamation-triangle"></i> Tool information not found for: ${objectCode}
                    </p>
                </div>
            `;
            return;
        }

        const tool = data.tools[0];
        const colorClass = objectCode === 'GRAV' ? 'var(--mc-primary)' : 
                          objectCode === 'PRES' ? 'var(--mc-primary)' : 
                          'var(--mc-accent)';
        
        const emoji = tool.tool_icon || '🔧';
        
        let layerExamplesHtml = '';
        if (tool.layer_examples && tool.layer_examples.length > 0) {
            layerExamplesHtml = `
                <div style="margin-top: var(--mc-spacing-md); padding-top: var(--mc-spacing-md); border-top: 1px solid rgba(0,255,255,0.2);">
                    <h4 style="margin: 0 0 var(--mc-spacing-sm) 0; color: var(--mc-accent); font-size: 0.95rem;">
                        <i class="fas fa-layer-group"></i> Example Layer Names
                    </h4>
                    <div style="display: flex; flex-direction: column; gap: 6px;">
                        ${tool.layer_examples.slice(0, 4).map(ex => {
                            const attributeBadge = ex.attribute_code 
                                ? `<span style="background: rgba(255,165,0,0.2); border: 1px solid rgba(255,165,0,0.4); color: #ffaa00; padding: 2px 6px; border-radius: 3px; font-size: 0.75rem; font-weight: 600; margin-left: 8px;">FILTER: ${ex.attribute_code}</span>`
                                : '';
                            return `
                            <div style="background: rgba(0,20,40,0.5); padding: 8px 12px; border-radius: 4px; border-left: 3px solid var(--mc-accent);">
                                <div style="display: flex; align-items: center;">
                                    <code style="color: var(--mc-primary); font-weight: bold; font-size: 0.9rem;">${ex.layer_name}</code>
                                    ${attributeBadge}
                                </div>
                                <div style="color: var(--mc-muted); font-size: 0.85rem; margin-top: 4px;">
                                    <i class="fas fa-arrow-right" style="font-size: 0.7rem;"></i> ${ex.description}
                                </div>
                            </div>
                        `;
                        }).join('')}
                    </div>
                    ${tool.layer_examples.length > 4 ? `
                        <p style="margin-top: 8px; color: var(--mc-muted); font-size: 0.85rem;">
                            <i class="fas fa-info-circle"></i> +${tool.layer_examples.length - 4} more layer format${tool.layer_examples.length - 4 > 1 ? 's' : ''} supported
                        </p>
                    ` : ''}
                </div>
            `;
        }
        
        let objectTypesHtml = '';
        if (tool.mapped_object_types && tool.mapped_object_types.length > 0) {
            objectTypesHtml = `
                <div style="margin-top: var(--mc-spacing-sm);">
                    <span style="font-size: 0.9rem; color: var(--mc-muted);">
                        <i class="fas fa-tags"></i> Manages: ${tool.mapped_object_types.map(obj => {
                            const attributeLabel = obj.attribute_code 
                                ? `+${obj.attribute_code}` 
                                : '';
                            return `<code style="background: rgba(0,255,255,0.15); padding: 2px 6px; border-radius: 3px; margin: 0 2px;">${obj.code}${attributeLabel}</code>`;
                        }).join(' ')}
                    </span>
                </div>
            `;
        }
        
        container.innerHTML = `
            <div class="mc-card" style="background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(0, 255, 136, 0.1)); border-left: 4px solid ${colorClass}; padding: var(--mc-spacing-lg); margin-bottom: var(--mc-spacing-lg);">
                <div style="display: flex; align-items: start; gap: var(--mc-spacing-md);">
                    <div style="font-size: 2rem; color: ${colorClass};">${emoji}</div>
                    <div style="flex: 1;">
                        <h3 style="margin: 0 0 var(--mc-spacing-sm) 0; color: ${colorClass}; font-size: 1.1rem; font-family: 'Orbitron', sans-serif;">
                            <i class="fas fa-info-circle"></i> About This Specialized Tool
                        </h3>
                        <p style="margin: 0 0 var(--mc-spacing-sm) 0; color: var(--mc-text); line-height: 1.5;">
                            ${tool.description}
                        </p>
                        ${objectTypesHtml}
                        ${layerExamplesHtml}
                        <div style="display: flex; gap: var(--mc-spacing-sm); flex-wrap: wrap; align-items: center; margin-top: var(--mc-spacing-md);">
                            <a href="/tools/specialized-tools-directory" style="color: var(--mc-accent); text-decoration: none; font-size: 0.9rem;">
                                <i class="fas fa-compass"></i> Discover more specialized tools
                            </a>
                            <span style="color: var(--mc-muted);">•</span>
                            <a href="/standards/reference-data" style="color: var(--mc-accent); text-decoration: none; font-size: 0.9rem;">
                                <i class="fas fa-cog"></i> Configure mappings
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading tool info:', error);
        container.innerHTML = `
            <div class="mc-card" style="background: rgba(255, 68, 68, 0.1); border-left: 4px solid var(--mc-danger); padding: var(--mc-spacing-lg);">
                <p style="color: var(--mc-danger);">
                    <i class="fas fa-exclamation-triangle"></i> Error loading tool information. Please try again later.
                </p>
            </div>
        `;
    }
}
