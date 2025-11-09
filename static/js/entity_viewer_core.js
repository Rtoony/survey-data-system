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
            padding: config.padding || 50,
            enableZoomPan: config.enableZoomPan !== false,
            showGrid: config.showGrid !== false,
            showNorthArrow: config.showNorthArrow !== false,
            showScaleBar: config.showScaleBar !== false
        };
        
        this.viewerEntities = [];
        this.viewerBbox = null;
        this.selectedEntityId = null;
        
        this.zoomLevel = 1.0;
        this.panX = 0;
        this.panY = 0;
        this.isPanning = false;
        this.panStartX = 0;
        this.panStartY = 0;
        
        this.baseViewBox = { x: 0, y: 0, width: this.config.width, height: this.config.height };
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
            
            this.scale = Math.min((width - padding * 2) / bboxWidth, (height - padding * 2) / bboxHeight);
            
            this.projectPoint = (lon, lat) => {
                const x = padding + (lon - this.viewerBbox.minX) * this.scale;
                const y = height - padding - (lat - this.viewerBbox.minY) * this.scale;
                return { x, y };
            };
            
            svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
            this.baseViewBox = { x: 0, y: 0, width, height };
            svg.innerHTML = '';
            
            const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
            const arrowMarker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
            arrowMarker.setAttribute('id', 'arrow');
            arrowMarker.setAttribute('markerWidth', '10');
            arrowMarker.setAttribute('markerHeight', '10');
            arrowMarker.setAttribute('refX', '5');
            arrowMarker.setAttribute('refY', '3');
            arrowMarker.setAttribute('orient', 'auto');
            arrowMarker.setAttribute('markerUnits', 'strokeWidth');
            const arrowPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            arrowPath.setAttribute('d', 'M0,0 L0,6 L9,3 z');
            arrowPath.setAttribute('fill', '#00ffff');
            arrowMarker.appendChild(arrowPath);
            defs.appendChild(arrowMarker);
            svg.appendChild(defs);
            
            if (this.config.showGrid) {
                this.renderGrid(svg);
            }
            
            this.viewerEntities.forEach((entity, idx) => {
                const geom = entity.geometry;
                const color = entity.color || '#00ffff';
                const entityType = entity.entity_type;
                const entityId = entity.entity_id;
                
                if (geom.type === 'Point') {
                    const pt = this.projectPoint(geom.coordinates[0], geom.coordinates[1]);
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
                    
                    circle.addEventListener('click', (e) => {
                        e.stopPropagation();
                        this.selectEntity(entityId, entityType);
                    });
                    
                    svg.appendChild(circle);
                    
                } else if (geom.type === 'LineString') {
                    const points = geom.coordinates.map(coord => this.projectPoint(coord[0], coord[1]));
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
                    
                    path.addEventListener('click', (e) => {
                        e.stopPropagation();
                        this.selectEntity(entityId, entityType);
                    });
                    
                    svg.appendChild(path);
                } else if (geom.type === 'Polygon') {
                    const points = geom.coordinates[0].map(coord => this.projectPoint(coord[0], coord[1]));
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
                    
                    path.addEventListener('click', (e) => {
                        e.stopPropagation();
                        this.selectEntity(entityId, entityType);
                    });
                    
                    svg.appendChild(path);
                }
            });
            
            if (this.config.showNorthArrow) {
                this.renderNorthArrow(svg);
            }
            
            if (this.config.showScaleBar) {
                this.renderScaleBar(svg);
            }
            
            if (this.config.enableZoomPan) {
                this.initializeZoomPan(svg);
                this.createZoomControls();
            }
            
            this.updateLegend();
            loadingEl.style.display = 'none';
            
        } catch (error) {
            console.error('Error loading entities:', error);
            svg.innerHTML = `<text x="50%" y="50%" text-anchor="middle" fill="#ff6b6b" font-size="16">Error loading viewer data</text>`;
            loadingEl.style.display = 'none';
        }
    }
    
    renderGrid(svg) {
        const { width, height, padding } = this.config;
        const bboxWidth = this.viewerBbox.maxX - this.viewerBbox.minX;
        const bboxHeight = this.viewerBbox.maxY - this.viewerBbox.minY;
        
        const avgDimension = (bboxWidth + bboxHeight) / 2;
        let gridInterval = Math.pow(10, Math.floor(Math.log10(avgDimension / 10)));
        
        if (avgDimension / gridInterval > 20) {
            gridInterval *= 2;
        } else if (avgDimension / gridInterval < 5) {
            gridInterval /= 2;
        }
        
        const gridGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        gridGroup.setAttribute('id', 'gridLayer');
        
        const startX = Math.floor(this.viewerBbox.minX / gridInterval) * gridInterval;
        const endX = Math.ceil(this.viewerBbox.maxX / gridInterval) * gridInterval;
        const startY = Math.floor(this.viewerBbox.minY / gridInterval) * gridInterval;
        const endY = Math.ceil(this.viewerBbox.maxY / gridInterval) * gridInterval;
        
        for (let x = startX; x <= endX; x += gridInterval) {
            const pt1 = this.projectPoint(x, this.viewerBbox.minY);
            const pt2 = this.projectPoint(x, this.viewerBbox.maxY);
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', pt1.x);
            line.setAttribute('y1', pt1.y);
            line.setAttribute('x2', pt2.x);
            line.setAttribute('y2', pt2.y);
            line.setAttribute('stroke', '#00ffff');
            line.setAttribute('stroke-width', '0.5');
            line.setAttribute('opacity', '0.15');
            gridGroup.appendChild(line);
        }
        
        for (let y = startY; y <= endY; y += gridInterval) {
            const pt1 = this.projectPoint(this.viewerBbox.minX, y);
            const pt2 = this.projectPoint(this.viewerBbox.maxX, y);
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', pt1.x);
            line.setAttribute('y1', pt1.y);
            line.setAttribute('x2', pt2.x);
            line.setAttribute('y2', pt2.y);
            line.setAttribute('stroke', '#00ffff');
            line.setAttribute('stroke-width', '0.5');
            line.setAttribute('opacity', '0.15');
            gridGroup.appendChild(line);
        }
        
        svg.appendChild(gridGroup);
    }
    
    renderNorthArrow(svg) {
        const arrowX = this.config.width - 60;
        const arrowY = 60;
        
        const arrowGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        arrowGroup.setAttribute('id', 'northArrow');
        
        const arrow = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        arrow.setAttribute('d', `M${arrowX},${arrowY - 25} L${arrowX - 8},${arrowY + 5} L${arrowX},${arrowY} L${arrowX + 8},${arrowY + 5} Z`);
        arrow.setAttribute('fill', '#00ffff');
        arrow.setAttribute('opacity', '0.8');
        arrowGroup.appendChild(arrow);
        
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', arrowX);
        text.setAttribute('y', arrowY + 20);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('fill', '#00ffff');
        text.setAttribute('font-size', '12');
        text.setAttribute('font-family', 'Rajdhani, sans-serif');
        text.textContent = 'N';
        arrowGroup.appendChild(text);
        
        svg.appendChild(arrowGroup);
    }
    
    renderScaleBar(svg) {
        const scaleBarX = 30;
        const scaleBarY = this.config.height - 40;
        const barLength = 100;
        
        const bboxWidth = this.viewerBbox.maxX - this.viewerBbox.minX;
        const realWorldLength = (barLength / this.scale) / this.zoomLevel;
        
        let displayLength = realWorldLength;
        let unit = 'ft';
        
        if (displayLength >= 5280) {
            displayLength = displayLength / 5280;
            unit = 'mi';
        }
        
        displayLength = Math.round(displayLength * 10) / 10;
        
        const scaleGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        scaleGroup.setAttribute('id', 'scaleBar');
        
        const background = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        background.setAttribute('x', scaleBarX - 5);
        background.setAttribute('y', scaleBarY - 20);
        background.setAttribute('width', barLength + 10);
        background.setAttribute('height', 35);
        background.setAttribute('fill', 'rgba(0, 0, 0, 0.6)');
        background.setAttribute('stroke', '#00ffff');
        background.setAttribute('stroke-width', '1');
        background.setAttribute('opacity', '0.8');
        scaleGroup.appendChild(background);
        
        const bar = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        bar.setAttribute('x1', scaleBarX);
        bar.setAttribute('y1', scaleBarY);
        bar.setAttribute('x2', scaleBarX + barLength);
        bar.setAttribute('y2', scaleBarY);
        bar.setAttribute('stroke', '#00ffff');
        bar.setAttribute('stroke-width', '2');
        scaleGroup.appendChild(bar);
        
        const tick1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        tick1.setAttribute('x1', scaleBarX);
        tick1.setAttribute('y1', scaleBarY - 5);
        tick1.setAttribute('x2', scaleBarX);
        tick1.setAttribute('y2', scaleBarY + 5);
        tick1.setAttribute('stroke', '#00ffff');
        tick1.setAttribute('stroke-width', '2');
        scaleGroup.appendChild(tick1);
        
        const tick2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        tick2.setAttribute('x1', scaleBarX + barLength);
        tick2.setAttribute('y1', scaleBarY - 5);
        tick2.setAttribute('x2', scaleBarX + barLength);
        tick2.setAttribute('y2', scaleBarY + 5);
        tick2.setAttribute('stroke', '#00ffff');
        tick2.setAttribute('stroke-width', '2');
        scaleGroup.appendChild(tick2);
        
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', scaleBarX + barLength / 2);
        label.setAttribute('y', scaleBarY - 8);
        label.setAttribute('text-anchor', 'middle');
        label.setAttribute('fill', '#00ffff');
        label.setAttribute('font-size', '11');
        label.setAttribute('font-family', 'Rajdhani, sans-serif');
        label.textContent = `${displayLength} ${unit}`;
        scaleGroup.appendChild(label);
        
        svg.appendChild(scaleGroup);
    }
    
    initializeZoomPan(svg) {
        svg.addEventListener('wheel', (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            this.zoom(delta);
        });
        
        svg.addEventListener('mousedown', (e) => {
            if (e.target === svg || e.target.id === 'gridLayer') {
                this.isPanning = true;
                this.panStartX = e.clientX - this.panX;
                this.panStartY = e.clientY - this.panY;
                svg.style.cursor = 'grabbing';
            }
        });
        
        svg.addEventListener('mousemove', (e) => {
            if (this.isPanning) {
                this.panX = e.clientX - this.panStartX;
                this.panY = e.clientY - this.panStartY;
                this.updateViewBox();
            }
        });
        
        svg.addEventListener('mouseup', () => {
            this.isPanning = false;
            svg.style.cursor = 'default';
        });
        
        svg.addEventListener('mouseleave', () => {
            this.isPanning = false;
            svg.style.cursor = 'default';
        });
    }
    
    zoom(delta) {
        const oldZoom = this.zoomLevel;
        this.zoomLevel *= delta;
        
        this.zoomLevel = Math.max(0.5, Math.min(10, this.zoomLevel));
        
        if (this.zoomLevel !== oldZoom) {
            this.updateViewBox();
            this.updateScaleBar();
            this.updateZoomIndicator();
        }
    }
    
    updateViewBox() {
        const svg = document.getElementById(this.config.svgId);
        const centerX = this.baseViewBox.width / 2;
        const centerY = this.baseViewBox.height / 2;
        
        const newWidth = this.baseViewBox.width / this.zoomLevel;
        const newHeight = this.baseViewBox.height / this.zoomLevel;
        
        const panFactorX = this.panX / this.zoomLevel / 5;
        const panFactorY = this.panY / this.zoomLevel / 5;
        
        const x = centerX - newWidth / 2 - panFactorX;
        const y = centerY - newHeight / 2 - panFactorY;
        
        svg.setAttribute('viewBox', `${x} ${y} ${newWidth} ${newHeight}`);
    }
    
    resetView() {
        this.zoomLevel = 1.0;
        this.panX = 0;
        this.panY = 0;
        this.updateViewBox();
        this.updateScaleBar();
        this.updateZoomIndicator();
    }
    
    updateScaleBar() {
        const scaleBar = document.getElementById('scaleBar');
        if (scaleBar) {
            scaleBar.remove();
            const svg = document.getElementById(this.config.svgId);
            this.renderScaleBar(svg);
        }
    }
    
    createZoomControls() {
        const svg = document.getElementById(this.config.svgId);
        const container = svg.parentElement;
        
        const controlsDiv = document.createElement('div');
        controlsDiv.id = 'viewerZoomControls';
        controlsDiv.style.position = 'absolute';
        controlsDiv.style.top = '10px';
        controlsDiv.style.right = '10px';
        controlsDiv.style.display = 'flex';
        controlsDiv.style.flexDirection = 'column';
        controlsDiv.style.gap = '5px';
        controlsDiv.style.zIndex = '10';
        
        const zoomInBtn = this.createControlButton('+', 'Zoom In', () => this.zoom(1.2));
        const zoomOutBtn = this.createControlButton('-', 'Zoom Out', () => this.zoom(0.8));
        const resetBtn = this.createControlButton('⌂', 'Reset View', () => this.resetView());
        
        const zoomIndicator = document.createElement('div');
        zoomIndicator.id = 'zoomIndicator';
        zoomIndicator.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
        zoomIndicator.style.color = '#00ffff';
        zoomIndicator.style.padding = '4px 8px';
        zoomIndicator.style.borderRadius = '3px';
        zoomIndicator.style.fontSize = '11px';
        zoomIndicator.style.fontFamily = 'Rajdhani, sans-serif';
        zoomIndicator.style.textAlign = 'center';
        zoomIndicator.style.border = '1px solid #00ffff';
        zoomIndicator.textContent = '100%';
        
        controlsDiv.appendChild(zoomInBtn);
        controlsDiv.appendChild(zoomOutBtn);
        controlsDiv.appendChild(resetBtn);
        controlsDiv.appendChild(zoomIndicator);
        
        container.style.position = 'relative';
        container.appendChild(controlsDiv);
    }
    
    createControlButton(text, title, onClick) {
        const btn = document.createElement('button');
        btn.textContent = text;
        btn.title = title;
        btn.style.width = '32px';
        btn.style.height = '32px';
        btn.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
        btn.style.color = '#00ffff';
        btn.style.border = '1px solid #00ffff';
        btn.style.borderRadius = '3px';
        btn.style.cursor = 'pointer';
        btn.style.fontSize = '16px';
        btn.style.fontWeight = 'bold';
        btn.style.display = 'flex';
        btn.style.alignItems = 'center';
        btn.style.justifyContent = 'center';
        btn.style.fontFamily = 'Rajdhani, sans-serif';
        
        btn.addEventListener('mouseenter', () => {
            btn.style.backgroundColor = '#00ffff';
            btn.style.color = '#000';
        });
        
        btn.addEventListener('mouseleave', () => {
            btn.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
            btn.style.color = '#00ffff';
        });
        
        btn.addEventListener('click', onClick);
        
        return btn;
    }
    
    updateZoomIndicator() {
        const indicator = document.getElementById('zoomIndicator');
        if (indicator) {
            indicator.textContent = Math.round(this.zoomLevel * 100) + '%';
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
