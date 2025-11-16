# Specialized Tool Template Guide

## Overview

The Specialized Tool Template provides a consistent, professional layout for all specialized tools in the ACAD-GIS system. It mimics the Project Command Center's presentation with full-screen mode, command-strip styling, and flexible content areas.

## Template Location

Base template: `templates/base_specialized_tool.html`

## Key Features

- ✅ **Full-screen mode** (press F or click button)
- ✅ **Command Center styling** (same colors, fonts, and design system)
- ✅ **Left sidebar** (250px) for filters, controls, and stats
- ✅ **Flexible layouts** (simple or complex)
- ✅ **Resizable panels** (for complex layouts)
- ✅ **Tabbed data views** (built-in support)
- ✅ **Keyboard shortcuts** (F for fullscreen)

---

## Layout Options

### Layout A: Simple
**Use Case:** Tools with straightforward interfaces (forms, lists, simple visualizations)

**Structure:**
```
┌─────────────────────────────────┐
│  Sidebar  │  Main Content Area  │
└─────────────────────────────────┘
```

**Example Use Cases:**
- Form-based configuration tools
- Simple data browsers
- Report generators
- Settings managers

### Layout B: Complex
**Use Case:** Tools requiring both visual/map displays AND detailed data tables

**Structure:**
```
┌─────────────────────────────────┐
│           │  Top Area (Map)     │
│  Sidebar  ├─────────────────────┤
│           │  Bottom (Tables)    │
└─────────────────────────────────┘
```

**Example Use Cases:**
- Pipe Network Managers (visual map + data tables)
- BMP Managers (map view + BMP properties)
- Site Analysis Tools (visual + calculations)

---

## About This Specialized Tool Section

Every specialized tool automatically includes an **"About This Specialized Tool"** section at the bottom of the page. This section provides context about what the tool manages, example layer names, and links to related resources.

### Default Structure

The About section includes:
- **Tool description**: Detailed explanation of tool capabilities
- **Manages tags**: Object type codes the tool handles (badges)
- **Example layer names**: Real CAD layer examples with descriptions
- **Links**: Discover more tools and configure mappings

### Customizing the About Section

Override these blocks in your tool template to customize the About section:

```html
{# Description - appears at the top of About section #}
{% block about_tool_description %}
Your detailed tool description explaining capabilities, features, and use cases.
{% endblock %}

{# Object type tags - badge-style tags showing what the tool manages #}
{% block about_tool_tags %}
<span class="about-tool-tag">OBJECT1</span>
<span class="about-tool-tag">OBJECT2</span>
<span class="about-tool-tag">OBJECT3</span>
{% endblock %}

{# Layer name examples - shows real CAD layer naming examples #}
{% block about_tool_examples %}
<div class="about-tool-example">
    <div class="about-tool-example-layer">CIV-CAT-OBJ-PROP-LN</div>
    <div class="about-tool-example-desc">→ Proposed Object - Civil/Category</div>
</div>
<div class="about-tool-example">
    <div class="about-tool-example-layer">CIV-CAT-OBJ-EXST-PT</div>
    <div class="about-tool-example-desc">→ Existing Points - Civil/Category</div>
</div>
{% endblock %}
```

### Full About Section Example

```html
{% block about_tool_description %}
Interactive tool for analyzing, editing, and managing gravity pipe networks with hydraulic calculations. 
Supports storm drain and sanitary sewer systems with automatic slope validation, invert elevation management, 
and network connectivity analysis.
{% endblock %}

{% block about_tool_tags %}
<span class="about-tool-tag">STORM</span>
<span class="about-tool-tag">SANIT</span>
<span class="about-tool-tag">MH</span>
<span class="about-tool-tag">INLET</span>
<span class="about-tool-tag">GRAV</span>
{% endblock %}

{% block about_tool_examples %}
<div class="about-tool-example">
    <div class="about-tool-example-layer">CIV-STM-STORM-PROP-LN</div>
    <div class="about-tool-example-desc">→ Proposed Storm Drain Pipes - Civil/Storm Drainage</div>
</div>
<div class="about-tool-example">
    <div class="about-tool-example-layer">CIV-SAN-SANIT-EXST-LN</div>
    <div class="about-tool-example-desc">→ Existing Sanitary Sewer Pipes - Civil/Sanitary</div>
</div>
<div class="about-tool-example">
    <div class="about-tool-example-layer">CIV-STM-MH-PROP-PT</div>
    <div class="about-tool-example-desc">→ Proposed Manholes - Civil/Storm Drainage</div>
</div>
{% endblock %}
```

### Hiding the About Section

If you want to hide the About section entirely for a specific tool:

```html
{% block about_tool_section %}
{# Empty block - hides the entire About section #}
{% endblock %}
```

---

## How to Create a New Specialized Tool

### Step 1: Create Your Template File

Create a new file in `templates/` directory, e.g., `my_tool_manager.html`

### Step 2: Extend the Base Template

```html
{% extends "base_specialized_tool.html" %}
```

### Step 3: Define Required Blocks

```html
{# Tool metadata #}
{% block tool_title %}My Tool Name{% endblock %}
{% block tool_icon %}fas fa-wrench{% endblock %}
{% block tool_description %}Brief description of what this tool does{% endblock %}

{# Choose layout mode #}
{% block content_layout_class %}tool-simple-layout{% endblock %}
{# OR for complex: tool-complex-layout #}

{# Sidebar content #}
{% block sidebar_content %}
  <!-- Your filters, controls, stats here -->
{% endblock %}

{# Main workspace #}
{% block main_content %}
  <!-- Your main content here -->
{% endblock %}
```

### Step 4: Add Route in app.py

```python
@app.route('/my-tool-manager')
def my_tool_manager():
    """My Tool Manager page"""
    return render_template('my_tool_manager.html')
```

---

## Complete Examples

### Example 1: Simple Layout Tool

**File:** `templates/settings_manager.html`

```html
{% extends "base_specialized_tool.html" %}

{% block tool_title %}Settings Manager{% endblock %}
{% block tool_icon %}fas fa-cog{% endblock %}
{% block tool_description %}Configure system settings and preferences{% endblock %}

{% block content_layout_class %}tool-simple-layout{% endblock %}

{% block sidebar_content %}
<div class="tool-filter-section">
    <h4>Categories</h4>
    <div class="tool-checkbox-item">
        <input type="checkbox" id="catGeneral" checked>
        <label for="catGeneral">General</label>
    </div>
    <div class="tool-checkbox-item">
        <input type="checkbox" id="catDisplay" checked>
        <label for="catDisplay">Display</label>
    </div>
</div>

<div class="tool-stats-section">
    <h4>Quick Stats</h4>
    <div class="tool-stat-item">
        <span class="tool-stat-label">Total Settings:</span>
        <span class="tool-stat-value">24</span>
    </div>
</div>
{% endblock %}

{% block main_content %}
<div style="padding: 2rem;">
    <h3 style="color: var(--mc-accent); margin-bottom: 1rem;">General Settings</h3>
    <!-- Your settings form here -->
</div>
{% endblock %}
```

### Example 2: Complex Layout Tool (with Map + Tables)

**File:** `templates/gravity_network_manager.html` (reference implementation)

```html
{% extends "base_specialized_tool.html" %}

{% block tool_title %}Gravity Pipe Network Manager{% endblock %}
{% block tool_icon %}fas fa-water{% endblock %}
{% block tool_description %}Interactive tool for gravity pipe networks{% endblock %}

{% block content_layout_class %}tool-complex-layout{% endblock %}

{% block sidebar_content %}
<!-- Network selector -->
<div class="tool-filter-section">
    <h4>Network Selection</h4>
    <div class="tool-filter-item">
        <label>Select Network:</label>
        <select id="networkSelect" onchange="loadNetwork()">
            <option value="">Select...</option>
        </select>
    </div>
</div>

<!-- Filters -->
<div class="tool-filter-section">
    <h4>Filters</h4>
    <div class="tool-checkbox-item">
        <input type="checkbox" id="filterStorm" checked>
        <label for="filterStorm">Storm Drain</label>
    </div>
</div>

<!-- Stats -->
<div class="tool-stats-section" id="stats">
    <h4>Network Stats</h4>
    <div class="tool-stat-item">
        <span class="tool-stat-label">Total Pipes:</span>
        <span class="tool-stat-value" id="statPipes">0</span>
    </div>
</div>

<!-- Actions -->
<button class="tool-action-btn" onclick="saveChanges()">
    <i class="fas fa-save"></i> Save Changes
</button>
{% endblock %}

{% block main_content %}
<!-- Top Area: Map -->
<div class="tool-top-area">
    <svg id="myCanvas" width="100%" height="100%"></svg>
</div>

<!-- Resizer -->
<div class="tool-resizer" id="resizer"></div>

<!-- Bottom Area: Data Tables -->
<div class="tool-bottom-area">
    <div class="tool-data-tabs">
        <button class="tool-data-tab active" data-tab="pipes" 
                onclick="switchTab('pipes', 'network')">
            Pipes
        </button>
        <button class="tool-data-tab" data-tab="structures"
                onclick="switchTab('structures', 'network')">
            Structures
        </button>
    </div>
    
    <div class="tool-data-content">
        <div class="tool-tab-content" data-tab="pipes" data-tab-group="network">
            <table class="tool-data-table">
                <!-- Your table here -->
            </table>
        </div>
        <div class="tool-tab-content" data-tab="structures" 
             data-tab-group="network" style="display:none;">
            <table class="tool-data-table">
                <!-- Your table here -->
            </table>
        </div>
    </div>
</div>
{% endblock %}
```

---

## CSS Classes Reference

### Sidebar Components

| Class | Purpose |
|-------|---------|
| `.tool-filter-section` | Container for filter controls |
| `.tool-stats-section` | Container for statistics display |
| `.tool-filter-item` | Individual filter input wrapper |
| `.tool-checkbox-item` | Checkbox with label wrapper |
| `.tool-stat-item` | Individual stat display (label + value) |
| `.tool-action-btn` | Primary action button |
| `.tool-action-btn.secondary` | Secondary action button |

### Main Content Components

| Class | Purpose |
|-------|---------|
| `.tool-simple-layout` | Use for simple single-area layout |
| `.tool-complex-layout` | Use for top+bottom split layout |
| `.tool-top-area` | Top area in complex layout (usually map) |
| `.tool-bottom-area` | Bottom area in complex layout (usually tables) |
| `.tool-resizer` | Resizable divider between top/bottom |
| `.tool-data-tabs` | Tab navigation container |
| `.tool-data-tab` | Individual tab button |
| `.tool-data-tab.active` | Active tab state |
| `.tool-data-content` | Content area for tabs |
| `.tool-tab-content` | Individual tab content panel |
| `.tool-data-table` | Styled data table |
| `.tool-loading` | Loading message overlay |
| `.tool-empty-state` | Empty state placeholder |
| `.tool-status-message` | Status/notification message |

### Utility Classes

| Class | Purpose |
|-------|---------|
| `.selected` | Mark table row as selected |
| `.error` | Error state for status messages |

---

## CSS Variables

The template uses Command Center CSS variables:

```css
--mc-primary: #00ffff        /* Primary cyan color */
--mc-accent: #00ff88         /* Accent green color */
--mc-bg-dark: rgba(0, 20, 40, 0.95)  /* Dark background */
--mc-bg-section: rgba(0, 40, 80, 0.6) /* Section background */
--mc-text: #e0f0ff           /* Text color */
--header-height: 140px       /* Header height (auto-calculated) */
--sidebar-width: 250px       /* Sidebar width */
```

---

## JavaScript Functions

### Built-in Functions

```javascript
// Fullscreen toggle
toggleFullscreen()  // Toggle fullscreen mode
// Also triggered by pressing 'F' key

// Tab switching
switchTab(tabName, tabGroup)
// Example: switchTab('pipes', 'network')
```

### Panel Resizing (Complex Layout)

The template includes automatic resizer functionality. To enable:

```javascript
function setupResizer() {
    const resizer = document.getElementById('resizer');
    const bottomArea = document.querySelector('.tool-bottom-area');
    let isResizing = false;
    
    resizer.addEventListener('mousedown', function(e) {
        isResizing = true;
        document.body.style.cursor = 'ns-resize';
    });
    
    document.addEventListener('mousemove', function(e) {
        if (!isResizing) return;
        
        const container = document.querySelector('.main-content-area');
        const containerRect = container.getBoundingClientRect();
        const newHeight = containerRect.bottom - e.clientY;
        
        if (newHeight >= 200 && newHeight <= containerRect.height * 0.8) {
            bottomArea.style.height = newHeight + 'px';
        }
    });
    
    document.addEventListener('mouseup', function() {
        isResizing = false;
        document.body.style.cursor = 'default';
    });
}

// Call on page load
document.addEventListener('DOMContentLoaded', setupResizer);
```

---

## Best Practices

### 1. Sidebar Organization

**DO:**
- Group related filters together
- Show quick stats relevant to the tool
- Provide clear action buttons
- Use collapsible sections for complex filters

**DON'T:**
- Overload with too many options
- Hide critical actions
- Use unclear labels

### 2. Table Design

**DO:**
- Use sticky headers for scrolling tables
- Show row counts in tab labels
- Enable row selection with visual feedback
- Support inline editing when appropriate

**DON'T:**
- Show too many columns (prioritize key data)
- Forget to handle empty states
- Neglect loading states

### 3. Performance

**DO:**
- Lazy-load data when network loads
- Use pagination for large datasets
- Debounce filter changes
- Show loading indicators

**DON'T:**
- Load all data upfront
- Block UI during operations
- Forget error handling

### 4. User Experience

**DO:**
- Provide fullscreen mode for focused work
- Show clear feedback for actions
- Enable keyboard shortcuts
- Support undo/redo where possible

**DON'T:**
- Force users into fullscreen
- Use modal dialogs excessively
- Hide important status information

---

## Testing Checklist

Before deploying a new specialized tool:

- [ ] Fullscreen mode works (F key and button)
- [ ] Sidebar filters function correctly
- [ ] Data loads without errors
- [ ] Tables display properly
- [ ] Tab switching works
- [ ] Resizer works (complex layout only)
- [ ] Empty states show correctly
- [ ] Loading states display
- [ ] Error messages appear when needed
- [ ] Responsive on different screen sizes
- [ ] Keyboard navigation works
- [ ] Action buttons are enabled/disabled appropriately

---

## Troubleshooting

### Issue: Fullscreen button not visible

**Solution:** Check z-index conflicts. The button should be at `z-index: 1000`.

### Issue: Tables not filling container

**Solution:** Ensure `.tool-data-content` has `flex: 1` and `overflow: auto`.

### Issue: Resizer not working

**Solution:** Call `setupResizer()` after DOM loads. Verify `tool-resizer` element exists.

### Issue: Tabs not switching

**Solution:** Verify:
- Tab buttons have `data-tab` and `data-tab-group` attributes
- Content divs have matching `data-tab` and `data-tab-group` attributes
- `switchTab()` function is called with correct parameters

---

## Example: Adding a New BMP Manager

Here's a step-by-step example:

### 1. Create template file

**File:** `templates/bmp_manager.html`

```html
{% extends "base_specialized_tool.html" %}

{% block tool_title %}BMP Manager{% endblock %}
{% block tool_icon %}fas fa-leaf{% endblock %}
{% block tool_description %}Manage Best Management Practices{% endblock %}

{% block content_layout_class %}tool-complex-layout{% endblock %}

{% block sidebar_content %}
<div class="tool-filter-section">
    <h4>BMP Type</h4>
    <div class="tool-checkbox-item">
        <input type="checkbox" id="bioretention" checked onchange="applyFilters()">
        <label for="bioretention">Bioretention</label>
    </div>
    <div class="tool-checkbox-item">
        <input type="checkbox" id="infiltration" checked onchange="applyFilters()">
        <label for="infiltration">Infiltration</label>
    </div>
</div>

<button class="tool-action-btn" onclick="addBMP()">
    <i class="fas fa-plus"></i> Add BMP
</button>
{% endblock %}

{% block main_content %}
<!-- Top: Map -->
<div class="tool-top-area">
    <div id="bmpMap"></div>
</div>

<div class="tool-resizer"></div>

<!-- Bottom: Data -->
<div class="tool-bottom-area">
    <div class="tool-data-tabs">
        <button class="tool-data-tab active" data-tab="list" 
                data-tab-group="bmp" onclick="switchTab('list', 'bmp')">
            BMP List
        </button>
        <button class="tool-data-tab" data-tab="properties"
                data-tab-group="bmp" onclick="switchTab('properties', 'bmp')">
            Properties
        </button>
    </div>
    <div class="tool-data-content">
        <!-- Tab content here -->
    </div>
</div>
{% endblock %}

{% block extra_js %}
function applyFilters() {
    // Your filter logic
}

function addBMP() {
    // Your add logic
}
{% endblock %}
```

### 2. Add route

**File:** `app.py`

```python
@app.route('/tools/bmp-manager')
def bmp_manager():
    """BMP Manager page"""
    return render_template('bmp_manager.html')
```

### 3. Test

Visit `/tools/bmp-manager` and verify all functionality.

---

## Support

For questions or issues with the template:
1. Check this documentation
2. Review the `gravity_network_manager.html` reference implementation
3. Inspect `base_specialized_tool.html` source code

---

## Version History

- **v1.0** (Nov 2025) - Initial release with simple and complex layouts
