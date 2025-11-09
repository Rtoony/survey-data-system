// Standards Documentation Export JavaScript

let selectedExportType = null;

// Select export type
function selectExportType(type) {
    selectedExportType = type;
    document.getElementById('exportConfig').style.display = 'block';
    
    // Update modal title based on type
    const titles = {
        'excel': 'Excel Spreadsheet Export',
        'pdf': 'PDF Document Export',
        'html': 'Web Page Export',
        'csv': 'CSV Files Export'
    };
    
    // Scroll to config section
    document.getElementById('exportConfig').scrollIntoView({ behavior: 'smooth' });
}

// Cancel export
function cancelExport() {
    selectedExportType = null;
    document.getElementById('exportConfig').style.display = 'none';
}

// Generate export
async function generateExport() {
    if (!selectedExportType) {
        alert('Please select an export type');
        return;
    }
    
    // Get selected content
    const config = {
        exportType: selectedExportType,
        title: document.getElementById('exportTitle').value,
        description: document.getElementById('exportDescription').value,
        nameMappings: {
            blocks: document.getElementById('includeBlocks').checked,
            details: document.getElementById('includeDetails').checked,
            hatches: document.getElementById('includeHatches').checked,
            materials: document.getElementById('includeMaterials').checked,
            notes: document.getElementById('includeNotes').checked
        },
        relationships: {
            keynoteBlocks: document.getElementById('includeKeynoteBlocks').checked,
            keynoteDetails: document.getElementById('includeKeynoteDetails').checked,
            hatchMaterials: document.getElementById('includeHatchMaterials').checked,
            detailMaterials: document.getElementById('includeDetailMaterials').checked,
            blockSpecs: document.getElementById('includeBlockSpecs').checked
        }
    };
    
    // Show progress
    document.getElementById('exportConfig').style.display = 'none';
    document.getElementById('exportProgress').style.display = 'block';
    updateProgress(10, 'Collecting data...');
    
    try {
        // Call export API
        const response = await fetch('/api/standards-export/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        
        updateProgress(50, 'Generating document...');
        
        if (!response.ok) {
            throw new Error('Export generation failed');
        }
        
        updateProgress(80, 'Finalizing...');
        
        const blob = await response.blob();
        updateProgress(100, 'Complete!');
        
        // Download file
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        const extensions = {
            'excel': 'xlsx',
            'pdf': 'pdf',
            'html': 'html',
            'csv': 'zip'
        };
        
        const timestamp = new Date().toISOString().slice(0,10);
        a.download = `CAD_Standards_${timestamp}.${extensions[selectedExportType]}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        // Reset UI after short delay
        setTimeout(() => {
            document.getElementById('exportProgress').style.display = 'none';
            document.getElementById('exportConfig').style.display = 'block';
            updateProgress(0, '');
            alert('Export generated successfully!');
        }, 1500);
        
    } catch (error) {
        console.error('Export error:', error);
        document.getElementById('exportProgress').style.display = 'none';
        document.getElementById('exportConfig').style.display = 'block';
        alert('Export generation failed: ' + error.message);
    }
}

// Update progress bar
function updateProgress(percent, message) {
    document.getElementById('progressFill').style.width = percent + '%';
    document.getElementById('progressStatus').textContent = message;
}
