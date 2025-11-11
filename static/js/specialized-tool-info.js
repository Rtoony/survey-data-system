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

    // Show loading state
    container.innerHTML = `
        <div class="mc-card" style="background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(0, 255, 136, 0.1)); border-left: 4px solid var(--mc-primary); padding: var(--mc-spacing-lg);">
            <p style="color: var(--mc-muted); text-align: center;">
                <i class="fas fa-spinner fa-spin"></i> Loading tool information...
            </p>
        </div>
    `;

    try {
        // Fetch all specialized tools from the API
        const response = await fetch('/api/cad-standards/specialized-tools-directory');
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        
        // Find the tool matching the object code
        const tool = data.tools.find(t => t.object_code === objectCode);
        
        if (!tool) {
            container.innerHTML = `
                <div class="mc-card" style="background: rgba(255, 68, 68, 0.1); border-left: 4px solid var(--mc-danger); padding: var(--mc-spacing-lg);">
                    <p style="color: var(--mc-danger);">
                        <i class="fas fa-exclamation-triangle"></i> Tool information not found for object code: ${objectCode}
                    </p>
                </div>
            `;
            return;
        }

        // Render the tool info card
        const colorClass = objectCode === 'GRAV' ? 'var(--mc-primary)' : 
                          objectCode === 'PRES' ? 'var(--mc-primary)' : 
                          'var(--mc-accent)';
        
        const emoji = tool.tool_icon || '🔧';
        
        container.innerHTML = `
            <div class="mc-card" style="background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(0, 255, 136, 0.1)); border-left: 4px solid ${colorClass}; padding: var(--mc-spacing-lg); margin-bottom: var(--mc-spacing-lg);">
                <div style="display: flex; align-items: start; gap: var(--mc-spacing-md);">
                    <div style="font-size: 2rem; color: ${colorClass};">${emoji}</div>
                    <div style="flex: 1;">
                        <h3 style="margin: 0 0 var(--mc-spacing-sm) 0; color: ${colorClass}; font-size: 1.1rem; font-family: 'Orbitron', sans-serif;">
                            <i class="fas fa-info-circle"></i> About This Specialized Tool
                        </h3>
                        <p style="margin: 0 0 var(--mc-spacing-sm) 0; color: var(--mc-text); line-height: 1.5;">
                            This is a <strong>specialized management tool</strong> for CAD layers with object type 
                            <span style="background: rgba(0,255,255,0.2); padding: 2px 8px; border-radius: var(--mc-radius-sm); font-family: monospace;">${tool.object_code}</span> 
                            (${tool.tool_name.replace(' Manager', '')}). 
                            ${tool.description}
                        </p>
                        <div style="display: flex; gap: var(--mc-spacing-sm); flex-wrap: wrap; align-items: center;">
                            <span style="font-size: 0.9rem; color: var(--mc-muted);">
                                <i class="fas fa-layer-group"></i> Works with: <strong>${tool.tool_name}</strong>
                            </span>
                            <span style="color: var(--mc-muted);">•</span>
                            <a href="/tools/specialized-tools-directory" style="color: var(--mc-accent); text-decoration: none; font-size: 0.9rem;">
                                <i class="fas fa-compass"></i> Discover more specialized tools
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
