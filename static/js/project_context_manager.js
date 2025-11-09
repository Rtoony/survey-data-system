let currentProject = null;
let currentRelationshipType = null;
let currentEditingId = null;

document.addEventListener('DOMContentLoaded', function() {
    loadProjects();
});

async function loadProjects() {
    try {
        const response = await fetch('/api/projects');
        const data = await response.json();
        
        const select = document.getElementById('projectSelect');
        select.innerHTML = '<option value="">-- Select a Project --</option>';
        
        data.projects.forEach(project => {
            const option = document.createElement('option');
            option.value = project.project_id;
            option.textContent = `${project.project_name} ${project.project_number ? '(' + project.project_number + ')' : ''}`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading projects:', error);
        showNotification('Error loading projects', 'error');
    }
}

async function loadProjectMappings() {
    const projectId = document.getElementById('projectSelect').value;
    
    if (!projectId) {
        document.getElementById('projectContent').style.display = 'none';
        document.getElementById('emptyMessage').style.display = 'block';
        currentProject = null;
        return;
    }
    
    currentProject = projectId;
    document.getElementById('projectContent').style.display = 'block';
    document.getElementById('emptyMessage').style.display = 'none';
    
    await Promise.all([
        loadKeynoteBlocks(projectId),
        loadKeynoteDetails(projectId),
        loadHatchMaterials(projectId),
        loadDetailMaterials(projectId),
        loadBlockSpecs(projectId)
    ]);
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(tabName + '-tab').classList.add('active');
}

async function loadKeynoteBlocks(projectId) {
    try {
        const response = await fetch(`/api/project-context/keynote-blocks?project_id=${projectId}`);
        const data = await response.json();
        
        const container = document.getElementById('keynoteBlocksTable');
        
        if (!data.mappings || data.mappings.length === 0) {
            container.innerHTML = '<p style="text-align: center; padding: 20px; color: var(--text-muted);">No keynote-block relationships defined yet.</p>';
            return;
        }
        
        let html = `
            <table class="mapping-table">
                <thead>
                    <tr>
                        <th>Keynote Number</th>
                        <th>Keynote Text</th>
                        <th>Block Name</th>
                        <th>Relationship Type</th>
                        <th>Context</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        data.mappings.forEach(mapping => {
            html += `
                <tr>
                    <td>${escapeHtml(mapping.keynote_number || '')}</td>
                    <td>${escapeHtml(mapping.note_text || '')}</td>
                    <td>${escapeHtml(mapping.block_name || '')}</td>
                    <td>${escapeHtml(mapping.relationship_type || '')}</td>
                    <td>${escapeHtml(mapping.usage_context || '')}</td>
                    <td>
                        <button onclick="editKeynoteBlock('${mapping.mapping_id}')" class="btn btn-sm btn-secondary" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="deleteMapping('keynote-blocks', '${mapping.mapping_id}')" class="btn btn-sm btn-danger" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading keynote-blocks:', error);
        showNotification('Error loading keynote-block relationships', 'error');
    }
}

async function loadKeynoteDetails(projectId) {
    try {
        const response = await fetch(`/api/project-context/keynote-details?project_id=${projectId}`);
        const data = await response.json();
        
        const container = document.getElementById('keynoteDetailsTable');
        
        if (!data.mappings || data.mappings.length === 0) {
            container.innerHTML = '<p style="text-align: center; padding: 20px; color: var(--text-muted);">No keynote-detail relationships defined yet.</p>';
            return;
        }
        
        let html = `
            <table class="mapping-table">
                <thead>
                    <tr>
                        <th>Keynote Number</th>
                        <th>Keynote Text</th>
                        <th>Detail Name</th>
                        <th>Detail Callout</th>
                        <th>Sheet Number</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        data.mappings.forEach(mapping => {
            html += `
                <tr>
                    <td>${escapeHtml(mapping.keynote_number || '')}</td>
                    <td>${escapeHtml(mapping.note_text || '')}</td>
                    <td>${escapeHtml(mapping.detail_name || '')}</td>
                    <td>${escapeHtml(mapping.detail_callout || '')}</td>
                    <td>${escapeHtml(mapping.sheet_number || '')}</td>
                    <td>
                        <button onclick="editKeynoteDetail('${mapping.mapping_id}')" class="btn btn-sm btn-secondary" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="deleteMapping('keynote-details', '${mapping.mapping_id}')" class="btn btn-sm btn-danger" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading keynote-details:', error);
        showNotification('Error loading keynote-detail relationships', 'error');
    }
}

async function loadHatchMaterials(projectId) {
    try {
        const response = await fetch(`/api/project-context/hatch-materials?project_id=${projectId}`);
        const data = await response.json();
        
        const container = document.getElementById('hatchMaterialsTable');
        
        if (!data.mappings || data.mappings.length === 0) {
            container.innerHTML = '<p style="text-align: center; padding: 20px; color: var(--text-muted);">No hatch-material relationships defined yet.</p>';
            return;
        }
        
        let html = `
            <table class="mapping-table">
                <thead>
                    <tr>
                        <th>Hatch Pattern</th>
                        <th>Material Name</th>
                        <th>Thickness</th>
                        <th>Legend Item</th>
                        <th>Notes</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        data.mappings.forEach(mapping => {
            html += `
                <tr>
                    <td>${escapeHtml(mapping.hatch_name || '')}</td>
                    <td>${escapeHtml(mapping.material_name || '')}</td>
                    <td>${escapeHtml(mapping.material_thickness || '')}</td>
                    <td>${mapping.is_legend_item ? '<i class="fas fa-check" style="color: var(--neon-cyan);"></i>' : ''}</td>
                    <td>${escapeHtml(mapping.material_notes || '')}</td>
                    <td>
                        <button onclick="editHatchMaterial('${mapping.mapping_id}')" class="btn btn-sm btn-secondary" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="deleteMapping('hatch-materials', '${mapping.mapping_id}')" class="btn btn-sm btn-danger" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading hatch-materials:', error);
        showNotification('Error loading hatch-material relationships', 'error');
    }
}

async function loadDetailMaterials(projectId) {
    try {
        const response = await fetch(`/api/project-context/detail-materials?project_id=${projectId}`);
        const data = await response.json();
        
        const container = document.getElementById('detailMaterialsTable');
        
        if (!data.mappings || data.mappings.length === 0) {
            container.innerHTML = '<p style="text-align: center; padding: 20px; color: var(--text-muted);">No detail-material relationships defined yet.</p>';
            return;
        }
        
        let html = `
            <table class="mapping-table">
                <thead>
                    <tr>
                        <th>Detail Name</th>
                        <th>Material Name</th>
                        <th>Role</th>
                        <th>Thickness</th>
                        <th>Layer Order</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        data.mappings.forEach(mapping => {
            html += `
                <tr>
                    <td>${escapeHtml(mapping.detail_name || '')}</td>
                    <td>${escapeHtml(mapping.material_name || '')}</td>
                    <td>${escapeHtml(mapping.material_role || '')}</td>
                    <td>${escapeHtml(mapping.material_thickness || '')}</td>
                    <td>${escapeHtml(mapping.material_layer_order || '')}</td>
                    <td>
                        <button onclick="editDetailMaterial('${mapping.mapping_id}')" class="btn btn-sm btn-secondary" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="deleteMapping('detail-materials', '${mapping.mapping_id}')" class="btn btn-sm btn-danger" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading detail-materials:', error);
        showNotification('Error loading detail-material relationships', 'error');
    }
}

async function loadBlockSpecs(projectId) {
    try {
        const response = await fetch(`/api/project-context/block-specs?project_id=${projectId}`);
        const data = await response.json();
        
        const container = document.getElementById('blockSpecsTable');
        
        if (!data.mappings || data.mappings.length === 0) {
            container.innerHTML = '<p style="text-align: center; padding: 20px; color: var(--text-muted);">No block-specification relationships defined yet.</p>';
            return;
        }
        
        let html = `
            <table class="mapping-table">
                <thead>
                    <tr>
                        <th>Block Name</th>
                        <th>Spec Section</th>
                        <th>Manufacturer</th>
                        <th>Model Number</th>
                        <th>Jurisdiction</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        data.mappings.forEach(mapping => {
            html += `
                <tr>
                    <td>${escapeHtml(mapping.block_name || '')}</td>
                    <td>${escapeHtml(mapping.spec_section || '')}</td>
                    <td>${escapeHtml(mapping.manufacturer || '')}</td>
                    <td>${escapeHtml(mapping.model_number || '')}</td>
                    <td>${escapeHtml(mapping.jurisdiction || '')}</td>
                    <td>
                        <button onclick="editBlockSpec('${mapping.mapping_id}')" class="btn btn-sm btn-secondary" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="deleteMapping('block-specs', '${mapping.mapping_id}')" class="btn btn-sm btn-danger" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading block-specs:', error);
        showNotification('Error loading block-specification relationships', 'error');
    }
}

async function showAddKeynoteBlockModal() {
    currentRelationshipType = 'keynote-blocks';
    currentEditingId = null;
    
    const [keynotes, blocks] = await Promise.all([
        fetchKeynotes(),
        fetchBlocks()
    ]);
    
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = 'Add Keynote→Block Relationship';
    
    modalBody.innerHTML = `
        <form id="relationshipForm">
            <div class="form-group">
                <label for="noteId">Keynote: <span style="color: red;">*</span></label>
                <select id="noteId" required>
                    <option value="">-- Select Keynote --</option>
                    ${keynotes.map(k => `<option value="${k.note_id}">${k.note_number || ''} - ${k.note_text || ''}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="keynoteNumber">Keynote Number:</label>
                <input type="text" id="keynoteNumber" placeholder="e.g., 5, G-12, CIV-001">
            </div>
            <div class="form-group">
                <label for="blockId">Block: <span style="color: red;">*</span></label>
                <select id="blockId" required>
                    <option value="">-- Select Block --</option>
                    ${blocks.map(b => `<option value="${b.block_id}">${b.block_name || ''} - ${b.description || ''}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="relationshipType">Relationship Type:</label>
                <select id="relationshipType">
                    <option value="references">References</option>
                    <option value="defines">Defines</option>
                    <option value="specifies">Specifies</option>
                </select>
            </div>
            <div class="form-group">
                <label for="usageContext">Usage Context:</label>
                <textarea id="usageContext" rows="3" placeholder="Describe when/how this relationship applies"></textarea>
            </div>
        </form>
    `;
    
    document.getElementById('relationshipModal').style.display = 'block';
}

async function showAddKeynoteDetailModal() {
    currentRelationshipType = 'keynote-details';
    currentEditingId = null;
    
    const [keynotes, details] = await Promise.all([
        fetchKeynotes(),
        fetchDetails()
    ]);
    
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = 'Add Keynote→Detail Relationship';
    
    modalBody.innerHTML = `
        <form id="relationshipForm">
            <div class="form-group">
                <label for="noteId">Keynote: <span style="color: red;">*</span></label>
                <select id="noteId" required>
                    <option value="">-- Select Keynote --</option>
                    ${keynotes.map(k => `<option value="${k.note_id}">${k.note_number || ''} - ${k.note_text || ''}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="keynoteNumber">Keynote Number:</label>
                <input type="text" id="keynoteNumber" placeholder="e.g., 5, G-12">
            </div>
            <div class="form-group">
                <label for="detailId">Detail: <span style="color: red;">*</span></label>
                <select id="detailId" required>
                    <option value="">-- Select Detail --</option>
                    ${details.map(d => `<option value="${d.detail_id}">${d.detail_name || ''} - ${d.detail_description || ''}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="detailCallout">Detail Callout:</label>
                <input type="text" id="detailCallout" placeholder="e.g., Detail 5/C-3.1">
            </div>
            <div class="form-group">
                <label for="sheetNumber">Sheet Number:</label>
                <input type="text" id="sheetNumber" placeholder="e.g., C-3.1">
            </div>
            <div class="form-group">
                <label for="usageContext">Usage Context:</label>
                <textarea id="usageContext" rows="3"></textarea>
            </div>
        </form>
    `;
    
    document.getElementById('relationshipModal').style.display = 'block';
}

async function showAddHatchMaterialModal() {
    currentRelationshipType = 'hatch-materials';
    currentEditingId = null;
    
    const [hatches, materials] = await Promise.all([
        fetchHatches(),
        fetchMaterials()
    ]);
    
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = 'Add Hatch→Material Relationship';
    
    modalBody.innerHTML = `
        <form id="relationshipForm">
            <div class="form-group">
                <label for="hatchId">Hatch Pattern: <span style="color: red;">*</span></label>
                <select id="hatchId" required>
                    <option value="">-- Select Hatch Pattern --</option>
                    ${hatches.map(h => `<option value="${h.hatch_id}">${h.pattern_name || ''} - ${h.description || ''}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="materialId">Material: <span style="color: red;">*</span></label>
                <select id="materialId" required>
                    <option value="">-- Select Material --</option>
                    ${materials.map(m => `<option value="${m.material_id}">${m.material_name || ''} - ${m.material_code || ''}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="materialThickness">Material Thickness:</label>
                <input type="text" id="materialThickness" placeholder="e.g., 4 inch, 6 inch">
            </div>
            <div class="form-group">
                <label for="materialNotes">Material Notes:</label>
                <textarea id="materialNotes" rows="3"></textarea>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="isLegendItem" checked>
                    Show in drawing legend
                </label>
            </div>
        </form>
    `;
    
    document.getElementById('relationshipModal').style.display = 'block';
}

async function showAddDetailMaterialModal() {
    currentRelationshipType = 'detail-materials';
    currentEditingId = null;
    
    const [details, materials] = await Promise.all([
        fetchDetails(),
        fetchMaterials()
    ]);
    
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = 'Add Detail→Material Relationship';
    
    modalBody.innerHTML = `
        <form id="relationshipForm">
            <div class="form-group">
                <label for="detailId">Detail: <span style="color: red;">*</span></label>
                <select id="detailId" required>
                    <option value="">-- Select Detail --</option>
                    ${details.map(d => `<option value="${d.detail_id}">${d.detail_name || ''}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="materialId">Material: <span style="color: red;">*</span></label>
                <select id="materialId" required>
                    <option value="">-- Select Material --</option>
                    ${materials.map(m => `<option value="${m.material_id}">${m.material_name || ''}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="materialRole">Material Role:</label>
                <select id="materialRole">
                    <option value="primary">Primary</option>
                    <option value="secondary">Secondary</option>
                    <option value="alternate">Alternate</option>
                    <option value="background">Background</option>
                </select>
            </div>
            <div class="form-group">
                <label for="materialLayerOrder">Layer Order:</label>
                <input type="number" id="materialLayerOrder" min="1" placeholder="1 = bottom">
            </div>
            <div class="form-group">
                <label for="materialThickness">Material Thickness:</label>
                <input type="text" id="materialThickness" placeholder="e.g., 6 inch PCC">
            </div>
            <div class="form-group">
                <label for="materialNotes">Material Notes:</label>
                <textarea id="materialNotes" rows="3"></textarea>
            </div>
        </form>
    `;
    
    document.getElementById('relationshipModal').style.display = 'block';
}

async function showAddBlockSpecModal() {
    currentRelationshipType = 'block-specs';
    currentEditingId = null;
    
    const blocks = await fetchBlocks();
    
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = 'Add Block→Specification Relationship';
    
    modalBody.innerHTML = `
        <form id="relationshipForm">
            <div class="form-group">
                <label for="blockId">Block: <span style="color: red;">*</span></label>
                <select id="blockId" required>
                    <option value="">-- Select Block --</option>
                    ${blocks.map(b => `<option value="${b.block_id}">${b.block_name || ''}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="specSection">Specification Section:</label>
                <input type="text" id="specSection" placeholder="e.g., Section 33 11 00, AWWA C502">
            </div>
            <div class="form-group">
                <label for="specDescription">Specification Description:</label>
                <textarea id="specDescription" rows="3"></textarea>
            </div>
            <div class="form-group">
                <label for="manufacturer">Manufacturer:</label>
                <input type="text" id="manufacturer">
            </div>
            <div class="form-group">
                <label for="modelNumber">Model Number:</label>
                <input type="text" id="modelNumber">
            </div>
            <div class="form-group">
                <label for="productUrl">Product URL:</label>
                <input type="url" id="productUrl">
            </div>
            <div class="form-group">
                <label for="jurisdiction">Jurisdiction:</label>
                <input type="text" id="jurisdiction" placeholder="e.g., City of Los Angeles">
            </div>
        </form>
    `;
    
    document.getElementById('relationshipModal').style.display = 'block';
}

async function editKeynoteBlock(mappingId) {
    currentRelationshipType = 'keynote-blocks';
    currentEditingId = mappingId;
    
    const response = await fetch(`/api/project-context/keynote-blocks/${mappingId}`);
    const mapping = await response.json();
    
    const [keynotes, blocks] = await Promise.all([
        fetchKeynotes(),
        fetchBlocks()
    ]);
    
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = 'Edit Keynote→Block Relationship';
    
    modalBody.innerHTML = `
        <form id="relationshipForm">
            <div class="form-group">
                <label for="noteId">Keynote: <span style="color: red;">*</span></label>
                <select id="noteId" required>
                    <option value="">-- Select Keynote --</option>
                    ${keynotes.map(k => `<option value="${k.note_id}" ${k.note_id === mapping.note_id ? 'selected' : ''}>${k.note_number || ''} - ${k.note_text || ''}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="keynoteNumber">Keynote Number:</label>
                <input type="text" id="keynoteNumber" value="${mapping.keynote_number || ''}">
            </div>
            <div class="form-group">
                <label for="blockId">Block: <span style="color: red;">*</span></label>
                <select id="blockId" required>
                    <option value="">-- Select Block --</option>
                    ${blocks.map(b => `<option value="${b.block_id}" ${b.block_id === mapping.block_id ? 'selected' : ''}>${b.block_name || ''}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="relationshipType">Relationship Type:</label>
                <select id="relationshipType">
                    <option value="references" ${mapping.relationship_type === 'references' ? 'selected' : ''}>References</option>
                    <option value="defines" ${mapping.relationship_type === 'defines' ? 'selected' : ''}>Defines</option>
                    <option value="specifies" ${mapping.relationship_type === 'specifies' ? 'selected' : ''}>Specifies</option>
                </select>
            </div>
            <div class="form-group">
                <label for="usageContext">Usage Context:</label>
                <textarea id="usageContext" rows="3">${mapping.usage_context || ''}</textarea>
            </div>
        </form>
    `;
    
    document.getElementById('relationshipModal').style.display = 'block';
}

async function editKeynoteDetail(mappingId) {
    currentRelationshipType = 'keynote-details';
    currentEditingId = mappingId;
    
    const response = await fetch(`/api/project-context/keynote-details/${mappingId}`);
    const mapping = await response.json();
    
    const [keynotes, details] = await Promise.all([
        fetchKeynotes(),
        fetchDetails()
    ]);
    
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = 'Edit Keynote→Detail Relationship';
    
    modalBody.innerHTML = `
        <form id="relationshipForm">
            <div class="form-group">
                <label for="noteId">Keynote: <span style="color: red;">*</span></label>
                <select id="noteId" required>
                    <option value="">-- Select Keynote --</option>
                    ${keynotes.map(k => `<option value="${k.note_id}" ${k.note_id === mapping.note_id ? 'selected' : ''}>${k.note_number || ''} - ${k.note_text || ''}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="keynoteNumber">Keynote Number:</label>
                <input type="text" id="keynoteNumber" value="${mapping.keynote_number || ''}">
            </div>
            <div class="form-group">
                <label for="detailId">Detail: <span style="color: red;">*</span></label>
                <select id="detailId" required>
                    <option value="">-- Select Detail --</option>
                    ${details.map(d => `<option value="${d.detail_id}" ${d.detail_id === mapping.detail_id ? 'selected' : ''}>${d.detail_name || ''}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="detailCallout">Detail Callout:</label>
                <input type="text" id="detailCallout" value="${mapping.detail_callout || ''}">
            </div>
            <div class="form-group">
                <label for="sheetNumber">Sheet Number:</label>
                <input type="text" id="sheetNumber" value="${mapping.sheet_number || ''}">
            </div>
            <div class="form-group">
                <label for="usageContext">Usage Context:</label>
                <textarea id="usageContext" rows="3">${mapping.usage_context || ''}</textarea>
            </div>
        </form>
    `;
    
    document.getElementById('relationshipModal').style.display = 'block';
}

async function editHatchMaterial(mappingId) {
    currentRelationshipType = 'hatch-materials';
    currentEditingId = mappingId;
    
    const response = await fetch(`/api/project-context/hatch-materials/${mappingId}`);
    const mapping = await response.json();
    
    const [hatches, materials] = await Promise.all([
        fetchHatches(),
        fetchMaterials()
    ]);
    
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = 'Edit Hatch→Material Relationship';
    
    modalBody.innerHTML = `
        <form id="relationshipForm">
            <div class="form-group">
                <label for="hatchId">Hatch Pattern: <span style="color: red;">*</span></label>
                <select id="hatchId" required>
                    <option value="">-- Select Hatch Pattern --</option>
                    ${hatches.map(h => `<option value="${h.hatch_id}" ${h.hatch_id === mapping.hatch_id ? 'selected' : ''}>${h.pattern_name || ''}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="materialId">Material: <span style="color: red;">*</span></label>
                <select id="materialId" required>
                    <option value="">-- Select Material --</option>
                    ${materials.map(m => `<option value="${m.material_id}" ${m.material_id === mapping.material_id ? 'selected' : ''}>${m.material_name || ''}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="materialThickness">Material Thickness:</label>
                <input type="text" id="materialThickness" value="${mapping.material_thickness || ''}">
            </div>
            <div class="form-group">
                <label for="materialNotes">Material Notes:</label>
                <textarea id="materialNotes" rows="3">${mapping.material_notes || ''}</textarea>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="isLegendItem" ${mapping.is_legend_item ? 'checked' : ''}>
                    Show in drawing legend
                </label>
            </div>
        </form>
    `;
    
    document.getElementById('relationshipModal').style.display = 'block';
}

async function editDetailMaterial(mappingId) {
    currentRelationshipType = 'detail-materials';
    currentEditingId = mappingId;
    
    const response = await fetch(`/api/project-context/detail-materials/${mappingId}`);
    const mapping = await response.json();
    
    const [details, materials] = await Promise.all([
        fetchDetails(),
        fetchMaterials()
    ]);
    
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = 'Edit Detail→Material Relationship';
    
    modalBody.innerHTML = `
        <form id="relationshipForm">
            <div class="form-group">
                <label for="detailId">Detail: <span style="color: red;">*</span></label>
                <select id="detailId" required>
                    <option value="">-- Select Detail --</option>
                    ${details.map(d => `<option value="${d.detail_id}" ${d.detail_id === mapping.detail_id ? 'selected' : ''}>${d.detail_name || ''}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="materialId">Material: <span style="color: red;">*</span></label>
                <select id="materialId" required>
                    <option value="">-- Select Material --</option>
                    ${materials.map(m => `<option value="${m.material_id}" ${m.material_id === mapping.material_id ? 'selected' : ''}>${m.material_name || ''}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="materialRole">Material Role:</label>
                <select id="materialRole">
                    <option value="primary" ${mapping.material_role === 'primary' ? 'selected' : ''}>Primary</option>
                    <option value="secondary" ${mapping.material_role === 'secondary' ? 'selected' : ''}>Secondary</option>
                    <option value="alternate" ${mapping.material_role === 'alternate' ? 'selected' : ''}>Alternate</option>
                    <option value="background" ${mapping.material_role === 'background' ? 'selected' : ''}>Background</option>
                </select>
            </div>
            <div class="form-group">
                <label for="materialLayerOrder">Layer Order:</label>
                <input type="number" id="materialLayerOrder" value="${mapping.material_layer_order || ''}" min="1">
            </div>
            <div class="form-group">
                <label for="materialThickness">Material Thickness:</label>
                <input type="text" id="materialThickness" value="${mapping.material_thickness || ''}">
            </div>
            <div class="form-group">
                <label for="materialNotes">Material Notes:</label>
                <textarea id="materialNotes" rows="3">${mapping.material_notes || ''}</textarea>
            </div>
        </form>
    `;
    
    document.getElementById('relationshipModal').style.display = 'block';
}

async function editBlockSpec(mappingId) {
    currentRelationshipType = 'block-specs';
    currentEditingId = mappingId;
    
    const response = await fetch(`/api/project-context/block-specs/${mappingId}`);
    const mapping = await response.json();
    
    const blocks = await fetchBlocks();
    
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = 'Edit Block→Specification Relationship';
    
    modalBody.innerHTML = `
        <form id="relationshipForm">
            <div class="form-group">
                <label for="blockId">Block: <span style="color: red;">*</span></label>
                <select id="blockId" required>
                    <option value="">-- Select Block --</option>
                    ${blocks.map(b => `<option value="${b.block_id}" ${b.block_id === mapping.block_id ? 'selected' : ''}>${b.block_name || ''}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="specSection">Specification Section:</label>
                <input type="text" id="specSection" value="${mapping.spec_section || ''}">
            </div>
            <div class="form-group">
                <label for="specDescription">Specification Description:</label>
                <textarea id="specDescription" rows="3">${mapping.spec_description || ''}</textarea>
            </div>
            <div class="form-group">
                <label for="manufacturer">Manufacturer:</label>
                <input type="text" id="manufacturer" value="${mapping.manufacturer || ''}">
            </div>
            <div class="form-group">
                <label for="modelNumber">Model Number:</label>
                <input type="text" id="modelNumber" value="${mapping.model_number || ''}">
            </div>
            <div class="form-group">
                <label for="productUrl">Product URL:</label>
                <input type="url" id="productUrl" value="${mapping.product_url || ''}">
            </div>
            <div class="form-group">
                <label for="jurisdiction">Jurisdiction:</label>
                <input type="text" id="jurisdiction" value="${mapping.jurisdiction || ''}">
            </div>
        </form>
    `;
    
    document.getElementById('relationshipModal').style.display = 'block';
}

async function saveRelationship() {
    if (!currentRelationshipType || !currentProject) {
        showNotification('Error: Missing context', 'error');
        return;
    }
    
    const form = document.getElementById('relationshipForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    let data = { project_id: currentProject };
    
    if (currentRelationshipType === 'keynote-blocks') {
        data.note_id = document.getElementById('noteId').value;
        data.keynote_number = document.getElementById('keynoteNumber').value;
        data.block_id = document.getElementById('blockId').value;
        data.relationship_type = document.getElementById('relationshipType').value;
        data.usage_context = document.getElementById('usageContext').value;
    } else if (currentRelationshipType === 'keynote-details') {
        data.note_id = document.getElementById('noteId').value;
        data.keynote_number = document.getElementById('keynoteNumber').value;
        data.detail_id = document.getElementById('detailId').value;
        data.detail_callout = document.getElementById('detailCallout').value;
        data.sheet_number = document.getElementById('sheetNumber').value;
        data.usage_context = document.getElementById('usageContext').value;
    } else if (currentRelationshipType === 'hatch-materials') {
        data.hatch_id = document.getElementById('hatchId').value;
        data.material_id = document.getElementById('materialId').value;
        data.material_thickness = document.getElementById('materialThickness').value;
        data.material_notes = document.getElementById('materialNotes').value;
        data.is_legend_item = document.getElementById('isLegendItem').checked;
    } else if (currentRelationshipType === 'detail-materials') {
        data.detail_id = document.getElementById('detailId').value;
        data.material_id = document.getElementById('materialId').value;
        data.material_role = document.getElementById('materialRole').value;
        data.material_layer_order = document.getElementById('materialLayerOrder').value;
        data.material_thickness = document.getElementById('materialThickness').value;
        data.material_notes = document.getElementById('materialNotes').value;
    } else if (currentRelationshipType === 'block-specs') {
        data.block_id = document.getElementById('blockId').value;
        data.spec_section = document.getElementById('specSection').value;
        data.spec_description = document.getElementById('specDescription').value;
        data.manufacturer = document.getElementById('manufacturer').value;
        data.model_number = document.getElementById('modelNumber').value;
        data.product_url = document.getElementById('productUrl').value;
        data.jurisdiction = document.getElementById('jurisdiction').value;
    }
    
    try {
        let url = `/api/project-context/${currentRelationshipType}`;
        let method = 'POST';
        
        if (currentEditingId) {
            url = `/api/project-context/${currentRelationshipType}/${currentEditingId}`;
            method = 'PUT';
        }
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('Failed to save relationship');
        }
        
        closeModal();
        showNotification('Relationship saved successfully', 'success');
        await loadProjectMappings();
    } catch (error) {
        console.error('Error saving relationship:', error);
        showNotification('Error saving relationship', 'error');
    }
}

async function deleteMapping(type, mappingId) {
    if (!confirm('Are you sure you want to delete this relationship?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/project-context/${type}/${mappingId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete relationship');
        }
        
        showNotification('Relationship deleted successfully', 'success');
        await loadProjectMappings();
    } catch (error) {
        console.error('Error deleting relationship:', error);
        showNotification('Error deleting relationship', 'error');
    }
}

function closeModal() {
    document.getElementById('relationshipModal').style.display = 'none';
    currentEditingId = null;
}

async function fetchKeynotes() {
    try {
        const response = await fetch('/api/standards/notes');
        const data = await response.json();
        return data.notes || [];
    } catch (error) {
        console.error('Error fetching keynotes:', error);
        return [];
    }
}

async function fetchBlocks() {
    try {
        const response = await fetch('/api/data-manager/blocks');
        const data = await response.json();
        return data.blocks || [];
    } catch (error) {
        console.error('Error fetching blocks:', error);
        return [];
    }
}

async function fetchDetails() {
    try {
        const response = await fetch('/api/data-manager/details');
        const data = await response.json();
        return data.details || [];
    } catch (error) {
        console.error('Error fetching details:', error);
        return [];
    }
}

async function fetchHatches() {
    try {
        const response = await fetch('/api/data-manager/hatches');
        const data = await response.json();
        return data.hatches || [];
    } catch (error) {
        console.error('Error fetching hatches:', error);
        return [];
    }
}

async function fetchMaterials() {
    try {
        const response = await fetch('/api/data-manager/materials');
        const data = await response.json();
        return data.materials || [];
    } catch (error) {
        console.error('Error fetching materials:', error);
        return [];
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'error' ? 'rgba(255, 50, 50, 0.9)' : 'rgba(0, 200, 100, 0.9)'};
        color: white;
        border-radius: 4px;
        z-index: 10000;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

window.onclick = function(event) {
    const modal = document.getElementById('relationshipModal');
    if (event.target === modal) {
        closeModal();
    }
}
