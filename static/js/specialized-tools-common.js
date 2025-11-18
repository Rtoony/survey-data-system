/**
 * SPECIALIZED TOOLS COMMON LIBRARY
 * =================================
 * Reusable JavaScript functions for all specialized civil engineering tools
 *
 * Usage: Include this script before tool-specific JavaScript:
 * <script src="/static/js/specialized-tools-common.js"></script>
 */

const SpecializedTools = {
    /**
     * Initialize a Leaflet map with standard configuration
     * @param {string} elementId - DOM element ID for the map
     * @param {object} options - Configuration options
     * @returns {L.Map} Leaflet map instance
     */
    initializeMap(elementId, options = {}) {
        const defaults = {
            center: [37.8, -122.4],
            zoom: 15,
            interactive: false,  // Static map by default
            zoomControl: true
        };

        const config = { ...defaults, ...options };

        const map = L.map(elementId, {
            dragging: config.interactive,
            touchZoom: config.interactive,
            scrollWheelZoom: config.interactive,
            doubleClickZoom: config.interactive,
            boxZoom: config.interactive,
            keyboard: config.interactive,
            zoomControl: config.zoomControl
        }).setView(config.center, config.zoom);

        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 22
        }).addTo(map);

        return map;
    },

    /**
     * Fit map to project extent using API
     * @param {L.Map} map - Leaflet map instance
     * @param {string} projectId - Project UUID
     */
    async fitMapToProjectExtent(map, projectId) {
        try {
            const response = await fetch(`/api/map-viewer/project-extent/${projectId}`);
            const data = await response.json();

            if (data.bbox) {
                map.fitBounds([
                    [data.bbox.min_y, data.bbox.min_x],
                    [data.bbox.max_y, data.bbox.max_x]
                ], { padding: [50, 50] });
            }
        } catch (error) {
            console.warn('Could not fit to project extent:', error);
        }
    },

    /**
     * Fit map to bounds of features
     * @param {L.Map} map - Leaflet map instance
     * @param {Array} features - Array of GeoJSON features or layers
     */
    fitMapToFeatures(map, features) {
        if (!features || features.length === 0) return;

        const bounds = [];
        features.forEach(feature => {
            if (feature.getBounds) {
                bounds.push(feature.getBounds());
            } else if (feature.getLatLng) {
                const latlng = feature.getLatLng();
                bounds.push(L.latLngBounds(latlng, latlng));
            }
        });

        if (bounds.length > 0) {
            const allBounds = bounds.reduce((a, b) => a.extend(b));
            map.fitBounds(allBounds, { padding: [50, 50] });
        }
    },

    /**
     * Render validation results with styled messages
     * @param {Array} issues - Array of validation issues
     * @param {string} containerId - DOM element ID for results
     */
    renderValidationResults(issues, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (!issues || issues.length === 0) {
            container.innerHTML = `
                <div class="validation-issue success">
                    <i class="fas fa-check-circle"></i>
                    <strong>Validation passed!</strong><br>
                    No issues found.
                </div>
            `;
        } else {
            container.innerHTML = issues.map(issue => `
                <div class="validation-issue ${issue.severity}">
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>${issue.type}</strong><br>
                    ${issue.message}
                </div>
            `).join('');
        }
    },

    /**
     * Get color for pipe/line type
     * @param {string} lineType - Line type name
     * @returns {string} Hex color code
     */
    getLineTypeColor(lineType) {
        const colors = {
            'storm_drain': '#0088ff',
            'sanitary_sewer': '#884400',
            'water_distribution': '#0044ff',
            'gravity_main': '#00aaff',
            'pressure_main': '#ff6600',
            'force_main': '#ff0066',
            'recycled_water': '#8800ff',
            'gas': '#ffaa00',
            'electric': '#ff0000',
            'telecom': '#00ff00'
        };
        return colors[lineType] || '#666666';
    },

    /**
     * Get color for structure condition rating
     * @param {number} rating - Condition rating (1-5)
     * @returns {string} Hex color code
     */
    getConditionColor(rating) {
        const colors = {
            5: '#00ff00',  // Excellent
            4: '#00ccff',  // Good
            3: '#ffff00',  // Fair
            2: '#ffa500',  // Poor
            1: '#ff0000'   // Critical
        };
        return colors[rating] || '#666666';
    },

    /**
     * Format number with thousands separator
     * @param {number} value - Number to format
     * @param {number} decimals - Number of decimal places
     * @returns {string} Formatted number
     */
    formatNumber(value, decimals = 0) {
        if (value == null) return 'N/A';
        return value.toLocaleString(undefined, {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    },

    /**
     * Show loading overlay
     * @param {string} elementId - DOM element ID for loading overlay
     * @param {boolean} show - Show or hide
     */
    showLoading(elementId, show = true) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = show ? 'block' : 'none';
        }
    },

    /**
     * Show error message
     * @param {string} message - Error message text
     * @param {number} duration - Duration in ms (0 = permanent)
     */
    showError(message, duration = 5000) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'tool-error-message';
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(255, 68, 68, 0.95);
            color: white;
            padding: 1.5rem;
            border-radius: 8px;
            z-index: 10000;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            border-left: 4px solid #ff0000;
        `;
        errorDiv.innerHTML = `
            <div style="display: flex; align-items: start; gap: 1rem;">
                <i class="fas fa-exclamation-circle" style="font-size: 24px;"></i>
                <div style="flex: 1;">
                    <strong>Error</strong><br>
                    <span style="font-size: 0.9rem;">${message}</span>
                </div>
                <button onclick="this.parentElement.parentElement.remove()"
                        style="background: none; border: none; color: white; cursor: pointer; font-size: 1.2rem;">
                    ×
                </button>
            </div>
        `;
        document.body.appendChild(errorDiv);

        if (duration > 0) {
            setTimeout(() => {
                errorDiv.remove();
            }, duration);
        }
    },

    /**
     * Show success message
     * @param {string} message - Success message text
     * @param {number} duration - Duration in ms
     */
    showSuccess(message, duration = 3000) {
        const successDiv = document.createElement('div');
        successDiv.className = 'tool-success-message';
        successDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 255, 100, 0.95);
            color: #001a00;
            padding: 1.5rem;
            border-radius: 8px;
            z-index: 10000;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            border-left: 4px solid #00ff00;
        `;
        successDiv.innerHTML = `
            <div style="display: flex; align-items: center; gap: 1rem;">
                <i class="fas fa-check-circle" style="font-size: 24px;"></i>
                <span style="font-weight: bold;">${message}</span>
            </div>
        `;
        document.body.appendChild(successDiv);

        setTimeout(() => {
            successDiv.remove();
        }, duration);
    },

    /**
     * Create a sortable table header
     * @param {string} column - Column name
     * @param {string} label - Display label
     * @param {Function} sortCallback - Function to call on sort
     * @returns {string} HTML for table header
     */
    createSortableHeader(column, label, sortCallback) {
        return `
            <th onclick="${sortCallback}('${column}')" style="cursor: pointer; user-select: none;">
                ${label} <i class="fas fa-sort"></i>
            </th>
        `;
    },

    /**
     * Sort array by column
     * @param {Array} data - Data array to sort
     * @param {string} column - Column name
     * @param {boolean} ascending - Sort direction
     * @returns {Array} Sorted array
     */
    sortData(data, column, ascending = true) {
        return [...data].sort((a, b) => {
            let aVal = a[column];
            let bVal = b[column];

            if (typeof aVal === 'string') {
                return ascending
                    ? (aVal || '').localeCompare(bVal || '')
                    : (bVal || '').localeCompare(aVal || '');
            } else {
                return ascending
                    ? (aVal || 0) - (bVal || 0)
                    : (bVal || 0) - (aVal || 0);
            }
        });
    },

    /**
     * Create a condition badge HTML
     * @param {number} rating - Condition rating (1-5)
     * @returns {string} HTML for condition badge
     */
    createConditionBadge(rating) {
        const labels = {
            5: 'Excellent',
            4: 'Good',
            3: 'Fair',
            2: 'Poor',
            1: 'Critical'
        };
        const label = labels[rating] || 'Unknown';
        const className = `condition-${rating}`;

        return `<span class="condition-badge ${className}">${label}</span>`;
    },

    /**
     * Calculate distance between two points (feet)
     * @param {number} x1 - First point X
     * @param {number} y1 - First point Y
     * @param {number} x2 - Second point X
     * @param {number} y2 - Second point Y
     * @returns {number} Distance in feet
     */
    calculateDistance(x1, y1, x2, y2) {
        return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
    },

    /**
     * Get active project ID from session
     * @returns {Promise<string|null>} Project ID or null
     */
    async getActiveProjectId() {
        try {
            if (window.projectContext) {
                const project = await window.projectContext.getActiveProject();
                return project ? project.project_id : null;
            }
            return null;
        } catch (error) {
            console.error('Error getting active project:', error);
            return null;
        }
    },

    /**
     * Debounce function calls
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in ms
     * @returns {Function} Debounced function
     */
    debounce(func, wait = 300) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Export data to CSV
     * @param {Array} data - Array of objects to export
     * @param {string} filename - Output filename
     */
    exportToCSV(data, filename = 'export.csv') {
        if (!data || data.length === 0) {
            this.showError('No data to export');
            return;
        }

        // Get headers from first object
        const headers = Object.keys(data[0]);

        // Build CSV content
        let csv = headers.join(',') + '\n';
        data.forEach(row => {
            const values = headers.map(header => {
                const value = row[header];
                // Escape values containing commas or quotes
                if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                    return '"' + value.replace(/"/g, '""') + '"';
                }
                return value || '';
            });
            csv += values.join(',') + '\n';
        });

        // Download
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);

        this.showSuccess('Data exported successfully');
    },

    /**
     * Format date to readable string
     * @param {string|Date} date - Date to format
     * @returns {string} Formatted date
     */
    formatDate(date) {
        if (!date) return 'N/A';
        const d = new Date(date);
        return d.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },

    /**
     * Calculate Manning's flow capacity
     * @param {number} diameter_in - Pipe diameter in inches
     * @param {number} slope - Pipe slope (ft/ft)
     * @param {string} material - Pipe material
     * @returns {number} Capacity in CFS
     */
    calculateManningsCapacity(diameter_in, slope, material = 'PVC') {
        // Manning's n values
        const n_values = {
            'PVC': 0.010,
            'HDPE': 0.010,
            'DI': 0.012,
            'RCP': 0.013,
            'CMP': 0.024,
            'VCP': 0.013
        };

        const n = n_values[material.toUpperCase()] || 0.013;
        const diameter_ft = diameter_in / 12;

        // Cross-sectional area (circular pipe)
        const area = Math.PI * Math.pow(diameter_ft / 2, 2);

        // Hydraulic radius for circular pipe flowing full
        const hydraulic_radius = diameter_ft / 4;

        // Manning's equation: Q = (1.486/n) * A * R^(2/3) * S^(1/2)
        const capacity = (1.486 / n) * area * Math.pow(hydraulic_radius, 2/3) * Math.pow(slope, 0.5);

        return capacity;
    }
};

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SpecializedTools;
}

console.log('Specialized Tools Common Library loaded');
