# Project 4: Advanced Utility Network Analysis Suite

## Executive Summary
Transform ACAD-GIS from a passive CAD repository into an active engineering analysis platform. Leverage PostGIS network topology capabilities to build hydraulic solvers, flow path analysis, service area modeling, 3D profile generation, and clash detection. Enable civil engineers to perform sophisticated analyses directly within the database-driven system.

## Current State Assessment

### Existing Infrastructure
- ✅ PostGIS 3.3+ with full spatial analysis capabilities
- ✅ 920 utility lines with 3D geometry (LineString Z)
- ✅ 312 utility structures with elevations
- ✅ Material and structure type standards (FK-constrained)
- ✅ Gravity Pipe Manager and Pressure Pipe Manager UIs
- ✅ Graph edges table (ready for network relationships)

### Current Gaps
- ❌ No network topology enforcement
- ❌ No gravity flow validation (invert elevation checking)
- ❌ No pressure network hydraulic calculations
- ❌ No automated service area analysis
- ❌ No 3D profile generation along alignments
- ❌ No clash detection between utility systems
- ❌ No cost estimation based on network topology

## Goals & Objectives

### Primary Goals
1. **Network Topology**: Build directed graph representation of utility networks
2. **Gravity Flow Solver**: Validate and analyze gravity flow systems (slope, capacity)
3. **Pressure Hydraulics**: Calculate head loss and pressure distribution
4. **Shortest Path Routing**: Optimal utility connection routes
5. **Service Area Analysis**: Determine which structures serve which areas
6. **3D Profiles**: Auto-generate profile drawings along pipe alignments
7. **Clash Detection**: Find conflicts between utility systems
8. **Cost Modeling**: Estimate construction costs based on network metrics

### Success Metrics
- Network topology built for 95%+ of utility lines
- Gravity flow validation catches 100% of reverse-slope errors
- Pressure calculations accurate within ±5 psi
- Service area analysis completes in <10 seconds
- 3D profiles generated in <5 seconds
- Clash detection finds conflicts with 98%+ accuracy

## Technical Architecture

### Core Components

#### 1. Network Topology Builder
Creates directed graph from utility geometry:

**Data Model**:
```sql
-- Network nodes (structures, endpoints)
CREATE TABLE network_nodes (
    node_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_type VARCHAR(50), -- STRUCTURE, ENDPOINT, JUNCTION
    structure_id UUID REFERENCES utility_structures(structure_id),
    geometry GEOMETRY(PointZ, 0),
    elevation DECIMAL(10,3),
    node_properties JSONB
);

-- Network edges (pipes/lines)
CREATE TABLE network_edges (
    edge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    line_id UUID REFERENCES utility_lines(line_id),
    from_node_id UUID REFERENCES network_nodes(node_id),
    to_node_id UUID REFERENCES network_nodes(node_id),
    edge_length DECIMAL(10,3),
    flow_direction VARCHAR(20), -- DOWNSTREAM, UPSTREAM, BIDIRECTIONAL
    edge_properties JSONB,
    
    -- Spatial index
    CONSTRAINT unique_edge UNIQUE (from_node_id, to_node_id)
);

-- Create spatial indexes
CREATE INDEX idx_network_nodes_geom ON network_nodes USING GIST(geometry);
CREATE INDEX idx_network_edges_from ON network_edges(from_node_id);
CREATE INDEX idx_network_edges_to ON network_edges(to_node_id);
```

**Topology Rules**:
- Lines within 0.1 ft of structures snap to structure nodes
- Dangling endpoints create ENDPOINT nodes
- Line intersections create JUNCTION nodes
- Flow direction determined by elevation (gravity) or pressure (pressurized)

#### 2. Gravity Flow Solver
Validates gravity-based systems (storm, sewer):

**Validation Checks**:
```python
class GravityFlowSolver:
    def validate_slope(self, edge):
        """Check if pipe has positive downstream slope"""
        upstream_invert = self.get_invert_elevation(edge.from_node_id, 'OUT')
        downstream_invert = self.get_invert_elevation(edge.to_node_id, 'IN')
        
        slope = (upstream_invert - downstream_invert) / edge.edge_length
        
        if slope <= 0:
            return ValidationError(
                severity='CRITICAL',
                message=f'Pipe {edge.line_id} has reverse slope ({slope:.4f})'
            )
        
        if slope < 0.005:
            return ValidationWarning(
                severity='HIGH',
                message=f'Pipe {edge.line_id} slope ({slope:.4f}) below minimum 0.5%'
            )
        
        return ValidationSuccess()
    
    def calculate_capacity(self, edge):
        """Manning's equation for gravity flow capacity"""
        # Q = (1.486/n) * A * R^(2/3) * S^(1/2)
        n = self.get_manning_n(edge.material)
        diameter = edge.diameter  # inches
        slope = self.get_slope(edge)
        
        # Full flow capacity
        area = math.pi * (diameter/12/2)**2  # sq ft
        wetted_perimeter = math.pi * (diameter/12)
        hydraulic_radius = area / wetted_perimeter
        
        capacity_cfs = (1.486 / n) * area * (hydraulic_radius ** (2/3)) * (slope ** 0.5)
        
        return capacity_cfs
    
    def trace_flow_path(self, start_node_id):
        """Follow gravity flow downstream to outlet"""
        path = []
        current_node = start_node_id
        
        while current_node:
            # Get downstream edge
            downstream_edge = self.get_downstream_edge(current_node)
            
            if not downstream_edge:
                break  # Reached outlet
            
            path.append(downstream_edge)
            current_node = downstream_edge.to_node_id
        
        return FlowPath(path, total_length=sum(e.edge_length for e in path))
```

#### 3. Pressure Network Solver
Hydraulic analysis for pressurized systems (water, sewer force mains):

**Hazen-Williams Formula**:
```python
class PressureNetworkSolver:
    def calculate_head_loss(self, edge, flow_rate_gpm):
        """Hazen-Williams equation for head loss"""
        # hL = 10.67 * L * Q^1.85 / (C^1.85 * D^4.87)
        # Where:
        # hL = head loss (ft)
        # L = pipe length (ft)
        # Q = flow rate (gpm)
        # C = Hazen-Williams coefficient (depends on material)
        # D = pipe diameter (inches)
        
        L = edge.edge_length
        Q = flow_rate_gpm
        C = self.get_hazen_williams_c(edge.material)
        D = edge.diameter
        
        head_loss = 10.67 * L * (Q ** 1.85) / ((C ** 1.85) * (D ** 4.87))
        
        return head_loss
    
    def solve_network_pressures(self, project_id):
        """Solve entire pressure network using iterative method"""
        
        # Build network graph
        network = self.build_network_graph(project_id)
        
        # Identify source nodes (pumps, tanks)
        sources = self.identify_source_nodes(network)
        
        # Identify demand nodes (service connections)
        demands = self.identify_demand_nodes(network)
        
        # Solve using Hardy Cross method or linear solver
        pressures = self.hardy_cross_method(network, sources, demands)
        
        # Check minimum pressure requirements (e.g., 20 psi)
        violations = self.check_pressure_violations(pressures, min_psi=20)
        
        return NetworkSolution(pressures, violations)
```

#### 4. Shortest Path Router
Find optimal routes for new connections:

**Dijkstra's Algorithm with Cost Weights**:
```python
class ShortestPathRouter:
    def find_route(self, start_point, end_point, utility_system='STORM'):
        """Find shortest path considering multiple factors"""
        
        # Build weighted graph
        graph = self.build_weighted_graph(utility_system)
        
        # Cost factors:
        # - Physical distance (primary)
        # - Elevation change (minimize pumping)
        # - ROW availability (prefer existing easements)
        # - Existing utility conflicts (avoid)
        
        edge_costs = {}
        for edge in graph.edges:
            cost = 0
            
            # Distance cost
            cost += edge.edge_length * 1.0
            
            # Elevation cost (uphill is expensive)
            elev_change = edge.to_node.elevation - edge.from_node.elevation
            if elev_change > 0:
                cost += elev_change * 10.0  # Penalty for pumping
            
            # Conflict cost
            conflicts = self.detect_conflicts(edge)
            cost += len(conflicts) * 50.0
            
            edge_costs[edge.edge_id] = cost
        
        # Run Dijkstra
        path = self.dijkstra(graph, start_point, end_point, edge_costs)
        
        return OptimalRoute(
            path=path,
            total_length=sum(e.edge_length for e in path),
            elevation_change=path[-1].to_node.elevation - path[0].from_node.elevation,
            estimated_cost=self.estimate_construction_cost(path)
        )
```

#### 5. Service Area Analysis
Determine catchment areas and service zones:

**Voronoi Diagram Approach**:
```python
class ServiceAreaAnalyzer:
    def calculate_catchment_areas(self, structure_ids):
        """Calculate drainage areas contributing to each structure"""
        
        # Get structure locations
        structures = [self.get_structure(sid) for sid in structure_ids]
        
        # Build Voronoi diagram
        from scipy.spatial import Voronoi
        points = [(s.x, s.y) for s in structures]
        vor = Voronoi(points)
        
        # Convert to PostGIS polygons
        catchments = []
        for i, structure in enumerate(structures):
            # Get Voronoi region for this structure
            region = vor.regions[vor.point_region[i]]
            
            if -1 not in region:  # Skip infinite regions
                polygon_coords = [vor.vertices[j] for j in region]
                polygon_wkt = self.coords_to_polygon(polygon_coords)
                
                catchments.append(CatchmentArea(
                    structure_id=structure.structure_id,
                    geometry=polygon_wkt,
                    area_sqft=self.calculate_area(polygon_wkt)
                ))
        
        return catchments
    
    def trace_service_connections(self, outlet_structure_id):
        """Find all upstream structures that drain to this outlet"""
        
        # Start from outlet, traverse upstream
        upstream_structures = set()
        queue = [outlet_structure_id]
        
        while queue:
            current_structure_id = queue.pop(0)
            
            # Find all pipes flowing INTO this structure
            incoming_edges = self.get_incoming_edges(current_structure_id)
            
            for edge in incoming_edges:
                upstream_structure = edge.from_node.structure_id
                
                if upstream_structure and upstream_structure not in upstream_structures:
                    upstream_structures.add(upstream_structure)
                    queue.append(upstream_structure)
        
        return ServiceArea(
            outlet_id=outlet_structure_id,
            served_structures=list(upstream_structures),
            total_length=self.calculate_total_pipe_length(upstream_structures)
        )
```

#### 6. 3D Profile Generator
Create profile drawings along alignments:

**Profile Calculation**:
```python
class ProfileGenerator:
    def generate_profile(self, alignment_line_ids, station_interval=50):
        """Generate profile data along pipe alignment"""
        
        # Merge lines into continuous alignment
        alignment = self.merge_lines(alignment_line_ids)
        
        # Sample points along alignment at intervals
        stations = self.generate_stations(alignment, station_interval)
        
        profile_data = []
        for station in stations:
            # Get point at this station
            point = self.point_at_distance(alignment, station.distance)
            
            # Sample ground elevation from survey points or DEM
            ground_elev = self.interpolate_ground_elevation(point)
            
            # Get pipe inverts if station intersects a structure
            pipe_inverts = self.get_pipe_inverts_at_point(point, tolerance=1.0)
            
            profile_data.append(ProfilePoint(
                station=station.distance,
                x=point.x,
                y=point.y,
                ground_elevation=ground_elev,
                pipe_inverts=pipe_inverts
            ))
        
        return ProfileDrawing(
            alignment_id=self.generate_id(),
            profile_points=profile_data,
            horizontal_scale='1"=20\'',
            vertical_scale='1"=4\'',
            vertical_exaggeration=5.0
        )
    
    def export_profile_svg(self, profile_drawing):
        """Generate SVG drawing of profile"""
        # SVG generation logic
        # Draw ground line, pipe inverts, structures, annotations
        pass
```

#### 7. Clash Detection Engine
Find conflicts between utility systems:

**3D Interference Checking**:
```python
class ClashDetector:
    def detect_clashes(self, project_id, clearance_ft=3.0):
        """Find where utilities are too close together"""
        
        # Get all utility lines for project
        storm_lines = self.get_utility_lines(project_id, 'STORM')
        sewer_lines = self.get_utility_lines(project_id, 'SEWER')
        water_lines = self.get_utility_lines(project_id, 'WATER')
        
        clashes = []
        
        # Check each pair of systems
        for storm in storm_lines:
            for sewer in sewer_lines:
                # PostGIS 3D distance check
                distance_3d = ST_3DDistance(storm.geometry, sewer.geometry)
                
                if distance_3d < clearance_ft:
                    clash_point = ST_3DClosestPoint(storm.geometry, sewer.geometry)
                    
                    clashes.append(Clash(
                        line1_id=storm.line_id,
                        line2_id=sewer.line_id,
                        system1='STORM',
                        system2='SEWER',
                        distance_ft=distance_3d,
                        location=clash_point,
                        severity='CRITICAL' if distance_3d < 1.0 else 'HIGH'
                    ))
        
        return ClashReport(clashes, total_count=len(clashes))
```

## Implementation Phases

### Phase 1: Network Topology Builder (Week 1-2)

**Tasks**:
1. Create network_nodes and network_edges tables
2. Build topology from existing utility_lines and utility_structures
3. Implement node snapping logic (0.1 ft tolerance)
4. Auto-detect flow direction from elevation
5. Create network visualization in Project Command Center

**Deliverables**:
- Network graph built for all projects
- 95%+ of lines connected to structure nodes
- Flow direction determined for gravity systems
- Interactive network diagram UI

### Phase 2: Gravity Flow Solver (Week 3-4)

**Tasks**:
1. Implement slope validation algorithm
2. Build Manning's equation capacity calculator
3. Create flow path tracing engine
4. Add gravity flow violations to Compliance Dashboard
5. Build Gravity Network Analyzer UI

**Deliverables**:
- Slope validation for all gravity pipes
- Capacity calculations with warnings for undersized pipes
- Flow path visualization from any structure to outlet
- Compliance dashboard showing gravity flow issues

### Phase 3: Pressure Network Solver (Week 5-6)

**Tasks**:
1. Implement Hazen-Williams head loss calculations
2. Build Hardy Cross method solver for network pressures
3. Create pressure zone visualization
4. Add pump and tank node types
5. Build Pressure Network Analyzer UI

**Deliverables**:
- Pressure calculations for water distribution systems
- Minimum pressure violation detection
- Pressure zone heatmap visualization
- Pump sizing recommendations

### Phase 4: Shortest Path Router (Week 7)

**Tasks**:
1. Implement weighted Dijkstra algorithm
2. Build cost function (distance + elevation + conflicts)
3. Create interactive route planning UI
4. Add route cost estimation

**Deliverables**:
- Optimal routing for new utility connections
- Cost comparison of route alternatives
- Interactive route drawing tool
- Export routes to DXF for CAD

### Phase 5: Service Area Analysis (Week 8)

**Tasks**:
1. Implement Voronoi catchment calculation
2. Build upstream structure tracing
3. Create service area polygon generation
4. Add service area visualization to map viewer

**Deliverables**:
- Catchment area polygons for all structures
- Service area reports showing which structures serve which areas
- Visual service area overlay on map
- Export service areas to shapefile

### Phase 6: 3D Profile Generator (Week 9)

**Tasks**:
1. Build alignment merging algorithm
2. Implement station interval sampling
3. Create ground elevation interpolation
4. Build SVG profile drawing generator
5. Add profile export to PDF

**Deliverables**:
- Auto-generated profile drawings
- Interactive profile viewer
- Export to SVG/PDF for printing
- Profile data export to CSV

### Phase 7: Clash Detection Engine (Week 10)

**Tasks**:
1. Implement 3D distance calculations
2. Build clash detection algorithm
3. Create clash visualization in 3D viewer
4. Add clash report to Compliance Dashboard
5. Build clash resolution workflow

**Deliverables**:
- Automated clash detection
- 3D visualization of conflicts
- Clash severity classification
- Resolution tracking and reporting

## Database Schema Extensions

```sql
-- Store network analysis results
CREATE TABLE network_analysis_results (
    analysis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    analysis_type VARCHAR(50), -- GRAVITY_FLOW, PRESSURE, ROUTING, SERVICE_AREA
    result_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Store profile drawings
CREATE TABLE profile_drawings (
    profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    alignment_name VARCHAR(100),
    alignment_geometry GEOMETRY(LineStringZ, 0),
    profile_data JSONB,
    svg_content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Store clash detections
CREATE TABLE utility_clashes (
    clash_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    line1_id UUID REFERENCES utility_lines(line_id),
    line2_id UUID REFERENCES utility_lines(line_id),
    system1 VARCHAR(20),
    system2 VARCHAR(20),
    distance_ft DECIMAL(8,3),
    clash_location GEOMETRY(PointZ, 0),
    severity VARCHAR(20),
    status VARCHAR(20), -- OPEN, RESOLVED, FALSE_POSITIVE
    resolved_at TIMESTAMP
);
```

## API Endpoints

### Network Topology
- `POST /api/network/build-topology/{project_id}` - Build network graph
- `GET /api/network/nodes/{project_id}` - Get all nodes
- `GET /api/network/edges/{project_id}` - Get all edges

### Gravity Flow
- `POST /api/network/validate-gravity/{project_id}` - Run gravity flow validation
- `GET /api/network/flow-path/{structure_id}` - Trace flow path from structure

### Pressure Network
- `POST /api/network/solve-pressure/{project_id}` - Solve pressure network
- `GET /api/network/pressure-zones/{project_id}` - Get pressure zones

### Routing
- `POST /api/network/find-route` - Find shortest path between points
- `GET /api/network/route-cost/{route_id}` - Get route cost estimate

### Service Areas
- `POST /api/network/calculate-catchments/{project_id}` - Calculate catchments
- `GET /api/network/service-area/{structure_id}` - Get service area

### Profiles
- `POST /api/network/generate-profile` - Generate profile drawing
- `GET /api/network/profile/{profile_id}/svg` - Export profile as SVG

### Clash Detection
- `POST /api/network/detect-clashes/{project_id}` - Run clash detection
- `GET /api/network/clashes/{project_id}` - Get clash report

## Dependencies & Requirements

### Python Packages
- `networkx>=3.0` - Graph algorithms
- `scipy>=1.10.0` - Scientific computing (Voronoi)
- `numpy>=1.24.0` - Numerical operations
- `matplotlib>=3.7.0` - Profile plotting (optional)

### PostGIS Functions
- `ST_3DDistance` - 3D distance calculations
- `ST_3DClosestPoint` - Find closest point in 3D
- `ST_LineInterpolatePoint` - Sample points along lines
- `ST_Length` - Line length calculations

## Risk Assessment

### Technical Risks
- **Topology complexity**: Networks may have loops, disconnected segments
  - **Mitigation**: Handle disconnected components separately
- **Performance**: Large networks (10,000+ pipes) may be slow
  - **Mitigation**: Spatial indexing, caching, incremental updates
- **Data quality**: Missing elevations break gravity flow analysis
  - **Mitigation**: Elevation interpolation, data quality warnings

### Engineering Risks
- **Hydraulic accuracy**: Simplified models vs. complex reality
  - **Mitigation**: Document assumptions, compare to industry software
- **Manning's n values**: Material coefficients may vary
  - **Mitigation**: Configurable coefficients, sensitivity analysis

## Success Criteria

### Must Have
- ✅ Network topology built for 95%+ of pipes
- ✅ Gravity flow validation catches all reverse slopes
- ✅ Shortest path routing finds optimal routes
- ✅ Profile generation works for any alignment

### Should Have
- ✅ Pressure calculations accurate within ±5 psi
- ✅ Service area analysis completes in <10 seconds
- ✅ Clash detection finds 98%+ of conflicts
- ✅ 3D visualization of network topology

### Nice to Have
- ✅ Integration with HEC-RAS for advanced hydraulics
- ✅ Time-series flow simulation
- ✅ Pump curve matching and optimization
- ✅ Cost optimization for network design

## Timeline Summary
- **Phase 1**: Weeks 1-2 (Topology)
- **Phase 2**: Weeks 3-4 (Gravity Flow)
- **Phase 3**: Weeks 5-6 (Pressure Network)
- **Phase 4**: Week 7 (Shortest Path)
- **Phase 5**: Week 8 (Service Areas)
- **Phase 6**: Week 9 (Profiles)
- **Phase 7**: Week 10 (Clash Detection)

**Total Duration**: 10 weeks

## ROI & Business Value
- **Design Validation**: Catch errors before construction
- **Optimization**: Find cost-effective routing solutions
- **Client Deliverables**: Auto-generated profiles and reports
- **Competitive Edge**: Advanced analysis capabilities
- **Time Savings**: Automated vs. manual network analysis
- **Quality**: Consistent engineering calculations
