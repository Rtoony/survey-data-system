# ACAD-GIS Visualization Tools

Complete guide to the spatial visualization and project management interfaces in ACAD-GIS.

## Overview

ACAD-GIS provides two powerful visualization interfaces optimized for different workflows:

1. **Enhanced Map Viewer** - Full-featured spatial workbench for detailed CAD/GIS analysis
2. **Project Command Center** - Compact project management dashboard with context map

Both tools feature optional full-screen modes optimized for wide-screen monitors (20", 27", ultrawide).

---

## 🗺️ Enhanced Map Viewer

**Route:** `/map-viewer-v2`

A comprehensive spatial workbench for viewing, analyzing, and exporting CAD/GIS entities with advanced layer controls, measurement tools, and multi-format export capabilities.

### Core Features

#### Interactive Map Display
- **Leaflet-based interface** with smooth pan and zoom
- **Coordinate transformation** between SRID 0 (CAD) ↔ SRID 2226 (State Plane) ↔ SRID 4326 (WGS84)
- **Auto-fit to project extent** with configurable padding
- **Real-time layer rendering** with color-coded entities

#### Layer Management
- **Toggle individual layers** with checkboxes
- **Layer grouping** by category and object type
- **Feature counts** displayed per layer
- **Expandable layer groups** to see constituent layer names
- **Color-coded visualization** for easy identification
- **Toggle All** button for quick show/hide

#### Basemap Selection
Choose from 4 basemap options for context:
- **Streets** - OpenStreetMap standard view
- **Satellite** - ESRI World Imagery
- **Topo** - OpenTopoMap with terrain
- **Dark** - CartoDB dark theme

#### Measurement Tools
- **Distance measurement** - Click points to measure linear distances
- **Area measurement** - Draw polygons to calculate area
- **Clear measurements** - Remove all measurement overlays

#### Bounding Box Export
- **Draw rectangle tool** to define export area
- **Visual feedback** with overlay rectangle
- **Coordinate display** showing min/max bounds
- **Clear selection** button to reset

#### Multi-Format Export
Export selected areas or entire project in multiple formats:

**DXF Export:**
- Standard CAD format with layers
- Preserves geometry types (lines, polylines, points)
- Maintains coordinate system (SRID 0 or 2226)
- Layer naming follows project standards

**KML Export:**
- Google Earth compatible format
- Automatic coordinate transformation to WGS84
- Styled features with colors and labels
- Folder organization by layer

**Shapefile Export:**
- Industry-standard GIS format
- Separate files for points, lines, polygons
- Includes .shp, .shx, .dbf, .prj files
- Attribute preservation

**PNG Export:**
- Screenshot of current map view
- High-resolution image capture
- Includes basemap and overlays
- Perfect for reports and presentations

#### Address Search
- **Geocoding integration** for address lookup
- **Auto-zoom** to searched location
- **Marker placement** at found address
- **Clear search** to remove marker

### Full-Screen Mode

**Activate:** Press `F` key or click the Full Screen button (top-right corner)  
**Exit:** Press `ESC` key or click the Exit Full Screen button

**Features in Full-Screen:**
- ✓ Navbar hidden to maximize workspace
- ✓ Map fills entire monitor
- ✓ All tools remain accessible (sidebar, export, measurement)
- ✓ Export modals appear correctly (proper z-index)
- ✓ Map automatically resizes
- ✓ Optimized for wide-screen monitors (20", 27", ultrawide)

### User Interface Layout

```
┌─────────────────────────────────────────────────────────┐
│ Navbar (sticky top)                          [F] Button │
├──────────┬──────────────────────────────────────────────┤
│          │                                              │
│ Sidebar  │           Interactive Map                    │
│          │                                              │
│ Project  │     - Leaflet layers                         │
│ Info     │     - Basemap tiles                          │
│          │     - Entity geometries                      │
│ Layer    │     - Measurement tools                      │
│ Controls │     - Bounding box selection                 │
│          │                                              │
│ Basemap  │                                              │
│ Selector │                                              │
│          │                                              │
│ Export   │                                              │
│ Tools    │                                              │
│          │                                              │
└──────────┴──────────────────────────────────────────────┘
```

### Typical Workflow

1. **Select Project** - Choose active project from navbar dropdown
2. **Review Layers** - Expand layer groups to see what's loaded
3. **Toggle Visibility** - Check/uncheck layers to focus on relevant data
4. **Choose Basemap** - Select appropriate background context
5. **Measure Features** - Use distance/area tools for analysis
6. **Define Export Area** - Draw bounding box around area of interest
7. **Export Data** - Choose format (DXF/KML/SHP/PNG) and download
8. **Full-Screen (Optional)** - Press `F` for maximum workspace

### Performance Notes

- **Entity Limit:** Hard limit of 5,000 entities for performance
- **Layer Groups:** Entities grouped by layer name parsing
- **Coordinate Transform:** Real-time transformation for all geometries
- **Lazy Loading:** Layers load on-demand when toggled visible

---

## 🎯 Project Command Center

**Route:** `/projects/{project_id}/command-center`

A streamlined project management dashboard providing quick access to all project tools, CAD standards, and a read-only context map with layer controls.

### Core Features

#### Collapsible Sidebar (250px)
Organized dropdown sections with all project operations:

**🎯 Quick Actions**
- Map Viewer link
- Refresh Data button

**🔧 Project Tools** (10 specialized tools)
- Entity Viewer
- Gravity Pipe Manager
- Pressure Pipe Manager
- BMP Manager
- Relationship Sets
- Survey Points
- Sheet Notes
- Usage Analytics
- DXF Export
- Batch Import

**📚 CAD Standards** (24 standards interfaces)
Complete access to all standards management tools organized by category

**🗺️ Map Controls**
- Basemap selector (Streets/Satellite/Topo/Dark)
- Layer toggles with checkboxes
- Feature counts per layer
- Toggle All button

**🧭 Navigation**
- Home link
- All Projects link

#### Read-Only Context Map
- **Non-interactive map** for visual context only
- **No zoom/pan/drag** - optimized for overview
- **Auto-fit to project extent** on load
- **Layer visibility control** via sidebar toggles
- **Basemap selection** for different contexts
- **Real-time updates** when data refreshed

#### Health Metrics Ribbon
Bottom ribbon displaying project statistics:
- **Total Entities** - All drawing entities count
- **Layers** - Unique layer count
- **Intelligent Objects** - Classified objects count
- **Drawings** - Associated drawing count

#### Project Info Box
Displays current project details:
- Project name
- Project ID
- Client information
- Quick metadata access

### Full-Screen Mode

**Activate:** Press `F` key or click the Full Screen button (top-right of map)
**Exit:** Press `ESC` key or click the Exit Full Screen button

**Features in Full-Screen:**
- ✓ Navbar hidden to maximize workspace
- ✓ Command Center fills entire monitor
- ✓ Sidebar remains accessible with all tools
- ✓ Map resizes to fill available space
- ✓ Health ribbon stays visible at bottom
- ✓ All controls remain functional
- ✓ Optimized for wide-screen monitors

### User Interface Layout

```
┌─────────────────────────────────────────────────────────┐
│ Navbar (sticky top)                                     │
├──────────┬──────────────────────────────────────────────┤
│          │ Project Overview Map            [F] Button   │
│ Sidebar  ├──────────────────────────────────────────────┤
│ (250px)  │                                              │
│          │                                              │
│ Project  │           Read-Only Map                      │
│ Info     │                                              │
│          │     - Auto-fit to extent                     │
│ Quick    │     - Layer visualization                    │
│ Actions  │     - No zoom/pan/drag                       │
│          │     - Basemap selection                      │
│ Project  │     - Context only                           │
│ Tools    │                                              │
│ (10)     │                                              │
│          │                                              │
│ CAD      │                                              │
│ Standards│                                              │
│ (24)     │                                              │
│          │                                              │
│ Map      │                                              │
│ Controls │                                              │
│          │                                              │
│ Navigation│                                             │
│          │                                              │
├──────────┴──────────────────────────────────────────────┤
│ Health Metrics: [92] [43] [93] [2]                     │
└─────────────────────────────────────────────────────────┘
```

### Typical Workflow

1. **View Project Context** - Map auto-loads with all project entities
2. **Check Health Metrics** - Review entity counts at bottom
3. **Toggle Layers** - Show/hide specific layers via Map Controls
4. **Select Basemap** - Choose appropriate background context
5. **Access Tools** - Click any tool from dropdown sections
6. **Quick Actions** - Use shortcuts for common operations
7. **Full-Screen (Optional)** - Click button for maximum workspace

### When to Use Command Center vs. Map Viewer

**Use Command Center when:**
- You need quick access to multiple project tools
- You want an overview dashboard for a specific project
- You need to check project health metrics
- You're navigating between different tools frequently
- You want a read-only map for context only

**Use Map Viewer when:**
- You need detailed spatial analysis
- You want to measure distances or areas
- You need to export data in specific formats
- You require precise zoom/pan control
- You're working with bounding box selections
- You need interactive map exploration

---

## Common Features Across Both Tools

### Full-Screen Mode Comparison

| Feature | Map Viewer | Command Center |
|---------|-----------|----------------|
| **Keyboard Shortcut** | `F` key | ESC only |
| **Exit Method** | `ESC` or button | `ESC` or button |
| **Navbar Hidden** | ✓ | ✓ |
| **Sidebar Accessible** | ✓ | ✓ |
| **Map Resizes** | ✓ | ✓ |
| **Tools Preserved** | All tools | All tools |
| **Z-Index Management** | ✓ | ✓ |
| **Wide-Screen Optimized** | ✓ | ✓ |

### Layer Control System

Both tools use the same underlying layer system:
- Layers derived from `drawing_entities` table
- Grouping by category and object type
- Color-coded visualization
- Feature count tracking
- Toggle visibility per layer

### Project Context

Both tools are project-aware:
- Active project selected via navbar
- Project data loaded automatically
- Real-time updates when project changes
- Project statistics displayed

### Mission Control Design Theme

Both tools follow the Mission Control design system:
- Cyan/neon color palette (`#00FF88`)
- Dark background (`#0a0e1a`)
- Orbitron and Rajdhani fonts
- Consistent button styles
- Hover effects and transitions

---

## Technical Architecture

### Coordinate Systems

All visualization tools handle three coordinate systems:

1. **SRID 0** - CAD native coordinates (no projection)
   - **Use for:** Raw DXF data, internal CAD work without geolocation
   - **Note:** No real-world location, relative coordinates only

2. **SRID 2226** - California State Plane Zone III (feet)
   - **Use for:** Projects in California (Alameda, Contra Costa, San Francisco, San Mateo counties)
   - **Units:** US Survey Feet
   - **Regional limitation:** California-specific projection only
   - **Accuracy:** High precision for local surveying and engineering

3. **SRID 4326** - WGS84 (latitude/longitude for web maps)
   - **Use for:** Web-based mapping, GPS coordinates, global positioning
   - **Units:** Decimal degrees
   - **Note:** Universal but less precise for local measurements
   - **Required for:** Leaflet.js basemaps and online mapping services

**Automatic Transformations:** PostGIS handles conversions between coordinate systems seamlessly. The Map Viewer displays in SRID 4326 for web compatibility while preserving accuracy from source data.

### Data Flow

```
PostgreSQL/PostGIS
    ↓
Flask API (/api/projects/{id}/drawing-entities-map)
    ↓
GeoJSON with properties
    ↓
Leaflet.js L.geoJSON()
    ↓
Layer Groups by Category
    ↓
User Toggles/Filters
    ↓
Rendered Map Display
```

### Performance Optimizations

- **5,000 Entity Limit** - Hard cap to prevent browser slowdown
- **Layer Grouping** - Reduces number of map objects
- **Lazy Layer Addition** - Layers added to map only when visible
- **Coordinate Caching** - Transformations cached where possible
- **Debounced Resize** - Map resize throttled during window changes

### Browser Compatibility

- **Modern Browsers** - Chrome, Firefox, Safari, Edge (latest 2 versions)
- **Mobile Support** - Touch-enabled but optimized for desktop
- **Wide-Screen Focus** - Best experience on 20"+ monitors
- **Resolution** - Optimized for 1920x1080 and higher

---

## API Endpoints Used

Both tools consume the same core API:

### `/api/projects/{project_id}/drawing-entities-map`
Returns GeoJSON feature collection with:
- Layer groups with features
- Bounding box extent
- Color assignments
- Feature counts
- Category metadata

**Response Structure:**
```json
{
  "project_id": "uuid",
  "project_name": "Project Name",
  "bbox": {
    "min_x": -122.5,
    "min_y": 37.7,
    "max_x": -122.3,
    "max_y": 37.8
  },
  "layer_groups": [
    {
      "id": "group-id",
      "name": "Layer Name",
      "category": "Category",
      "color": "#00FF88",
      "feature_count": 150,
      "features": [/* GeoJSON features */]
    }
  ],
  "total_entities": 5000,
  "total_layers": 43,
  "total_intelligent_objects": 93
}
```

### `/api/active-project`
Returns currently selected project metadata

### `/api/projects`
Returns list of all projects for selection

---

## Keyboard Shortcuts

### Map Viewer
- **F** - Toggle full-screen mode
- **ESC** - Exit full-screen mode

### Command Center
- **ESC** - Toggle full-screen mode (both enter and exit)

---

## Troubleshooting

### Map Not Loading
- Check that project has entities with valid geometries
- Verify coordinate system is SRID 0, 2226, or 4326
- Check browser console for transformation errors
- Ensure project_id exists in database

### Layers Not Toggling
- Refresh the page to reload layer groups
- Check that layer checkbox is clickable
- Verify layer has features (count > 0)
- Clear browser cache if layers appear stuck

### Export Not Working
- Ensure bounding box is drawn (for area exports)
- Check that you have entities in the selected area
- Verify export modal appears (z-index issue if not)
- Try full-screen mode if modal is hidden

### Full-Screen Issues
- If navbar doesn't hide, press ESC and try again
- If map doesn't resize, wait 100ms for transition
- Check browser allows full-screen (some block it)
- Try refreshing page if keyboard shortcuts fail

---

## Future Enhancements

Potential improvements for future releases:

### Map Viewer
- Pagination for >5,000 entities
- Advanced filtering by attributes
- Print layout mode
- Custom color schemes
- Save/load views
- Annotation tools

### Command Center
- Customizable sidebar sections
- Widget-based layout
- Real-time collaboration indicators
- Task management integration
- Timeline view of project history

### Both Tools
- Mobile-optimized layouts
- Offline mode support
- Advanced search across all entities
- Integration with external GIS services
- Custom basemap uploads

---

## Related Documentation

- [README.md](README.md) - Project overview and quick start
- [replit.md](replit.md) - Architecture and technical details
- [CAD_STANDARDS_GUIDE.md](CAD_STANDARDS_GUIDE.md) - Layer naming conventions
- [PROJECTS_ONLY_MIGRATION_GUIDE.md](archive/completed-migrations/PROJECTS_ONLY_MIGRATION_GUIDE.md) - Project-centric architecture

---

**Last Updated:** November 16, 2025  
**Version:** 1.0  
**Maintained by:** ACAD-GIS Development Team
