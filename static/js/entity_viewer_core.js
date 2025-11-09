class EntityViewerCore {
    constructor(config) {
        this.config = {
            svgId: config.svgId || 'networkCanvas',
            legendId: config.legendId || 'viewerLegend',
            infoId: config.infoId || 'entityInfo',
            loadingId: config.loadingId || 'loadingMessage',
            fetchEntitiesUrl: config.fetchEntitiesUrl,
            entityTypeColors: config.entityTypeColors || {},
            infoPropertyMap: config.infoPropertyMap || [],
            onEntitySelect: config.onEntitySelect || null,
            width: config.width || 1000,
            height: config.height || 1000,
            padding: config.padding || 50
        };
        
        this.viewerEntities = [];
        this.viewerBbox = null;
        this.selectedEntityId = null;
    }
    
    async renderViewer() {
        const loadingEl = document.getElementById(this.config.loadingId);
        const svg = document.getElementById(this.config.svgId);
        
        if (!this.config.fetchEntitiesUrl) {
            console.error('No fetchEntitiesUrl configured');
            return;
        }
        
        loadingEl.style.display = 'block';
        
        try {
            const response = await fetch(this.config.fetchEntitiesUrl);
            const data = await response.json();
            
            this.viewerEntities = data.entities || [];
            this.viewerBbox = data.bbox;
            
            if (!this.viewerBbox || this.viewerEntities.length === 0) {
                svg.innerHTML = '<text x="50%" y="50%" text-anchor="middle" fill="#00ffff" font-size="16">No geometry data to display</text>';
                loadingEl.style.display = 'none';
                return;
            }
            
            const { width, height, padding } = this.config;
            
            const bboxWidth = this.viewerBbox.maxX - this.viewerBbox.minX;
            const bboxHeight = this.viewerBbox.maxY - this.viewerBbox.minY;
            
            const scale = Math.min((width - padding * 2) / bboxWidth, (height - padding * 2) / bboxHeight);
            
            const projectPoint = (lon, lat) => {
                const x = padding + (lon - this.viewerBbox.minX) * scale;
                const y = height - padding - (lat - this.viewerBbox.minY) * scale;
                return { x, y };
            };
            
            svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
            svg.innerHTML = '';
            
            this.viewerEntities.forEach((entity, idx) => {
                const geom = entity.geometry;
                const color = entity.color || '#00ffff';
                const entityType = entity.entity_type;
                const entityId = entity.entity_id;
                
                if (geom.type === 'Point') {
                    const pt = projectPoint(geom.coordinates[0], geom.coordinates[1]);
                    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                    circle.setAttribute('cx', pt.x);
                    circle.setAttribute('cy', pt.y);
                    circle.setAttribute('r', 5);
                    circle.setAttribute('fill', color);
                    circle.setAttribute('stroke', color);
                    circle.setAttribute('stroke-width', '1');
                    circle.setAttribute('data-entity-id', entityId);
                    circle.setAttribute('data-entity-type', entityType);
                    circle.setAttribute('data-entity-idx', idx);
                    circle.style.cursor = 'pointer';
                    circle.style.opacity = '0.8';
                    
                    circle.addEventListener('mouseenter', () => {
                        circle.classList.add('entity-highlighted');
                        this.updateEntityInfo(this.viewerEntities[idx]);
                    });
                    
                    circle.addEventListener('mouseleave', () => {
                        circle.classList.remove('entity-highlighted');
                    });
                    
                    circle.addEventListener('click', () => {
                        this.selectEntity(entityId, entityType);
                    });
                    
                    svg.appendChild(circle);
                    
                } else if (geom.type === 'LineString') {
                    const points = geom.coordinates.map(coord => projectPoint(coord[0], coord[1]));
                    const pathData = 'M ' + points.map(p => `${p.x},${p.y}`).join(' L ');
                    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    path.setAttribute('d', pathData);
                    path.setAttribute('stroke', color);
                    path.setAttribute('stroke-width', 2);
                    path.setAttribute('fill', 'none');
                    path.setAttribute('data-entity-id', entityId);
                    path.setAttribute('data-entity-type', entityType);
                    path.setAttribute('data-entity-idx', idx);
                    path.style.cursor = 'pointer';
                    path.style.opacity = '0.7';
                    
                    path.addEventListener('mouseenter', () => {
                        path.classList.add('entity-highlighted');
                        this.updateEntityInfo(this.viewerEntities[idx]);
                    });
                    
                    path.addEventListener('mouseleave', () => {
                        path.classList.remove('entity-highlighted');
                    });
                    
                    path.addEventListener('click', () => {
                        this.selectEntity(entityId, entityType);
                    });
                    
                    svg.appendChild(path);
                } else if (geom.type === 'Polygon') {
                    const points = geom.coordinates[0].map(coord => projectPoint(coord[0], coord[1]));
                    const pathData = 'M ' + points.map(p => `${p.x},${p.y}`).join(' L ') + ' Z';
                    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    path.setAttribute('d', pathData);
                    path.setAttribute('fill', color);
                    path.setAttribute('stroke', color);
                    path.setAttribute('stroke-width', 1);
                    path.setAttribute('data-entity-id', entityId);
                    path.setAttribute('data-entity-type', entityType);
                    path.setAttribute('data-entity-idx', idx);
                    path.style.cursor = 'pointer';
                    path.style.opacity = '0.4';
                    
                    path.addEventListener('mouseenter', () => {
                        path.classList.add('entity-highlighted');
                        this.updateEntityInfo(this.viewerEntities[idx]);
                    });
                    
                    path.addEventListener('mouseleave', () => {
                        path.classList.remove('entity-highlighted');
                    });
                    
                    path.addEventListener('click', () => {
                        this.selectEntity(entityId, entityType);
                    });
                    
                    svg.appendChild(path);
                }
            });
            
            this.updateLegend();
            loadingEl.style.display = 'none';
            
        } catch (error) {
            console.error('Error loading entities:', error);
            svg.innerHTML = `<text x="50%" y="50%" text-anchor="middle" fill="#ff6b6b" font-size="16">Error loading viewer data</text>`;
            loadingEl.style.display = 'none';
        }
    }
    
    updateLegend() {
        const legendEl = document.getElementById(this.config.legendId);
        
        const typeCounts = {};
        this.viewerEntities.forEach(entity => {
            const type = entity.entity_type || 'Unknown';
            typeCounts[type] = (typeCounts[type] || 0) + 1;
        });
        
        let legendHTML = '';
        
        Object.entries(typeCounts).forEach(([type, count]) => {
            const color = this.config.entityTypeColors[type] || '#00ffff';
            const displayName = type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            const isLine = type.includes('pipe') || type.includes('line');
            const isPolygon = type.includes('bmp') || type.includes('area');
            
            legendHTML += `
                <div class="legend-item">
                    <div class="legend-color ${isLine ? '' : isPolygon ? 'polygon' : 'point'}" style="background: ${color};"></div>
                    <span class="legend-label">${displayName}</span>
                    <span class="legend-count">${count}</span>
                </div>
            `;
        });
        
        if (legendHTML === '') {
            legendHTML = '<p style="color: var(--mc-text); font-size: 0.85rem;">No entities to display</p>';
        }
        
        legendEl.innerHTML = legendHTML;
    }
    
    updateEntityInfo(entity) {
        const infoEl = document.getElementById(this.config.infoId);
        
        if (!entity) {
            infoEl.innerHTML = '<p style="color: var(--mc-text); font-size: 0.85rem;">Hover or click an entity</p>';
            return;
        }
        
        const displayName = (entity.entity_type || 'Unknown').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        
        let infoHTML = `
            <div style="margin-bottom: 0.5rem; color: ${entity.color}; font-weight: 600;">
                ${displayName}
            </div>
        `;
        
        const props = entity.properties || {};
        
        this.config.infoPropertyMap.forEach(({ key, label }) => {
            if (props[key] !== undefined && props[key] !== null && props[key] !== '') {
                let value = props[key];
                if (typeof value === 'number') {
                    value = value.toFixed(2);
                }
                infoHTML += `
                    <div style="display: flex; justify-content: space-between; padding: 0.25rem 0; border-bottom: 1px solid rgba(0, 255, 255, 0.1); font-size: 0.85rem;">
                        <span style="color: var(--mc-primary);">${label}:</span>
                        <span style="color: var(--mc-text);">${value}</span>
                    </div>
                `;
            }
        });
        
        infoEl.innerHTML = infoHTML;
    }
    
    findEntityById(entityId) {
        return this.viewerEntities.find(entity => entity.entity_id === entityId);
    }
    
    selectEntity(entityId, entityType) {
        const svg = document.getElementById(this.config.svgId);
        
        this.selectedEntityId = entityId;
        
        const allSvgEntities = svg.querySelectorAll('[data-entity-id]');
        allSvgEntities.forEach(el => el.classList.remove('entity-selected'));
        
        const svgEntity = svg.querySelector(`[data-entity-id="${entityId}"]`);
        if (svgEntity) {
            svgEntity.classList.add('entity-selected');
        }
        
        const allTableRows = document.querySelectorAll('.table-row');
        allTableRows.forEach(row => row.classList.remove('table-row-selected'));
        
        const tableRow = document.querySelector(`.table-row[data-entity-id="${entityId}"]`);
        if (tableRow) {
            tableRow.classList.add('table-row-selected');
            tableRow.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        
        const entity = this.findEntityById(entityId);
        if (entity) {
            this.updateEntityInfo(entity);
        }
        
        if (this.config.onEntitySelect) {
            this.config.onEntitySelect(entityId, entityType, entity);
        }
    }
    
    selectEntityFromTable(event, entityId, entityType) {
        this.selectEntity(entityId, entityType);
        event.stopPropagation();
    }
    
    getEntities() {
        return this.viewerEntities;
    }
    
    getBoundingBox() {
        return this.viewerBbox;
    }
    
    getSelectedEntityId() {
        return this.selectedEntityId;
    }
}
