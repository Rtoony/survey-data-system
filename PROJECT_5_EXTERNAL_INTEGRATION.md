# Project 5: External GIS Data Integration Hub

## Executive Summary
Break ACAD-GIS out of the file-based silo and connect it to the real-world GIS ecosystem. Build connectors for municipal data sources (WMS/WFS), geocoding services, survey equipment formats, cloud GIS platforms (ArcGIS Online), and automated export to industry-standard formats. Transform ACAD-GIS into a true data integration platform that bridges CAD and GIS workflows.

## Current State Assessment

### Existing Capabilities
- ✅ DXF import/export (CAD format)
- ✅ KML/Shapefile export (basic GIS formats)
- ✅ PostGIS database (spatial data storage)
- ✅ Coordinate system support (SRID 2226 for GIS, SRID 0 for CAD)
- ✅ OWSLib library installed (WMS/WFS client capability)

### Current Limitations
- ❌ No live data feeds from municipalities
- ❌ No automated aerial imagery basemaps
- ❌ No address geocoding/reverse geocoding
- ❌ No survey equipment integration (Trimble, Leica)
- ❌ No ArcGIS Online/ESRI integration
- ❌ No export to Civil 3D or Geodatabase formats
- ❌ Manual coordinate transformations
- ❌ No weather data for stormwater modeling

## Goals & Objectives

### Primary Goals
1. **Municipal Data Integration**: Connect to city/county GIS servers (parcels, zoning, utilities)
2. **Live Imagery Basemaps**: Stream aerial photos and topographic maps
3. **Geocoding Services**: Convert addresses to coordinates and vice versa
4. **Survey Data Import**: Support Trimble, Leica, Topcon formats
5. **Cloud GIS Export**: Publish to ArcGIS Online, QGIS Cloud
6. **Industry Format Export**: Civil 3D, ESRI Geodatabase, LandXML
7. **Weather Integration**: Rainfall data for stormwater calculations
8. **Automated Coordinate Transforms**: Seamless SRID conversion

### Success Metrics
- Connect to 10+ municipal WMS/WFS data sources
- Geocoding success rate >95% for project addresses
- Survey import supports 5+ equipment brands
- Export to Civil 3D preserves all attributes
- Weather data automatically fetched for projects
- Coordinate transformations accurate to <0.1 ft

## Technical Architecture

### Core Components

#### 1. WMS/WFS Municipal Data Connector
Stream live GIS data from government servers:

**Supported Data Sources**:
- Parcels (property boundaries)
- Zoning districts
- Existing utilities (if available)
- Street centerlines
- Aerial imagery
- Topographic contours

**Implementation**:
```python
# services/wms_connector.py
from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService

class MunicipalDataConnector:
    def __init__(self):
        self.wms_sources = {
            'santa_clara_county': 'https://gis.sccgov.org/arcgis/services/...',
            'city_of_san_jose': 'https://gis.sanjoseca.gov/arcgis/services/...',
            # Add more municipalities
        }
    
    def fetch_parcels(self, municipality, bbox):
        """Fetch parcel data within bounding box"""
        wfs = WebFeatureService(self.wms_sources[municipality], version='2.0.0')
        
        # Query parcels layer
        response = wfs.getfeature(
            typename='Parcels',
            bbox=bbox,
            srsname='EPSG:2226'  # California State Plane Zone 3
        )
        
        # Parse GML response
        parcels = self.parse_gml(response)
        
        # Store in database
        for parcel in parcels:
            self.insert_parcel(parcel)
        
        return parcels
    
    def stream_aerial_imagery(self, bbox, zoom_level):
        """Stream aerial imagery as WMS tiles"""
        wms = WebMapService(self.wms_sources['santa_clara_county'])
        
        # Request map image
        img = wms.getmap(
            layers=['Aerials_2023'],
            srs='EPSG:2226',
            bbox=bbox,
            size=(1024, 1024),
            format='image/png',
            transparent=True
        )
        
        return img.read()
```

**Database Storage**:
```sql
-- Store fetched external data
CREATE TABLE external_parcels (
    parcel_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    apn VARCHAR(50), -- Assessor's Parcel Number
    owner_name VARCHAR(200),
    address VARCHAR(255),
    zoning VARCHAR(50),
    geometry GEOMETRY(Polygon, 2226),
    source_municipality VARCHAR(100),
    fetched_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(apn, source_municipality)
);

CREATE INDEX idx_external_parcels_geom ON external_parcels USING GIST(geometry);
```

#### 2. Geocoding Service Integration
Convert addresses to coordinates:

**Service Providers**:
- Google Maps Geocoding API (high accuracy, costs money)
- OpenStreetMap Nominatim (free, lower accuracy)
- ESRI World Geocoding Service (good for addresses)
- Census.gov Geocoding (US addresses, free)

**Implementation**:
```python
# services/geocoding_service.py
import requests

class GeocodingService:
    def __init__(self, provider='nominatim'):
        self.provider = provider
        self.api_keys = {
            'google': os.getenv('GOOGLE_MAPS_API_KEY'),
            'esri': os.getenv('ESRI_API_KEY')
        }
    
    def geocode_address(self, address, municipality=None, state='CA'):
        """Convert address to coordinates"""
        
        if self.provider == 'nominatim':
            return self._geocode_nominatim(address)
        elif self.provider == 'google':
            return self._geocode_google(address)
        elif self.provider == 'census':
            return self._geocode_census(address)
    
    def _geocode_nominatim(self, address):
        """OpenStreetMap Nominatim (free)"""
        url = 'https://nominatim.openstreetmap.org/search'
        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }
        
        response = requests.get(url, params=params, headers={'User-Agent': 'ACAD-GIS'})
        data = response.json()
        
        if data:
            return GeocodeResult(
                latitude=float(data[0]['lat']),
                longitude=float(data[0]['lon']),
                confidence=float(data[0].get('importance', 0.5)),
                source='nominatim'
            )
        
        return None
    
    def reverse_geocode(self, latitude, longitude):
        """Convert coordinates to address"""
        url = 'https://nominatim.openstreetmap.org/reverse'
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json'
        }
        
        response = requests.get(url, params=params, headers={'User-Agent': 'ACAD-GIS'})
        data = response.json()
        
        return data.get('display_name')
```

**UI Integration**:
- Add address search bar to Map Viewer
- Click-to-geocode feature on map
- Batch geocoding for project lists
- Geocoding confidence indicator

#### 3. Survey Equipment Data Import
Support industry-standard survey formats:

**Supported Formats**:
- Trimble JobXML (.jxl)
- Trimble DC file (.dc)
- Leica GSI format (.gsi)
- Topcon GTS format (.gts)
- Carlson SurvCE (.rwx)
- Generic CSV/TXT (PNEZD)

**Implementation**:
```python
# services/survey_import.py
class SurveyDataImporter:
    def import_trimble_jobxml(self, file_path, project_id):
        """Parse Trimble JobXML format"""
        import xml.etree.ElementTree as ET
        
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        points = []
        for point in root.findall('.//Point'):
            point_id = point.find('ID').text
            north = float(point.find('North').text)
            east = float(point.find('East').text)
            elevation = float(point.find('Elevation').text)
            description = point.find('Description').text
            
            points.append(SurveyPoint(
                point_id=point_id,
                northing=north,
                easting=east,
                elevation=elevation,
                description=description,
                coord_system_id=1  # From coordinate_systems table
            ))
        
        # Insert into database
        self.insert_survey_points(points, project_id)
        
        return ImportResult(
            total_points=len(points),
            success=True
        )
    
    def import_leica_gsi(self, file_path, project_id):
        """Parse Leica GSI format"""
        # GSI format: fixed-width text with word index codes
        # Example: *110001+0000000000000001 21.....+00000000001234567 ...
        
        points = []
        with open(file_path, 'r') as f:
            for line in f:
                point = self.parse_gsi_line(line)
                if point:
                    points.append(point)
        
        self.insert_survey_points(points, project_id)
        
        return ImportResult(total_points=len(points), success=True)
```

#### 4. ArcGIS Online Integration
Publish projects to ESRI cloud platform:

**Capabilities**:
- Export feature layers to ArcGIS Online
- Create web maps with ACAD-GIS data
- Share projects with clients via ArcGIS Portal
- Sync changes bidirectionally (optional)

**Implementation**:
```python
# services/arcgis_connector.py
from arcgis.gis import GIS
from arcgis.features import FeatureLayer

class ArcGISConnector:
    def __init__(self, username, password, portal_url='https://www.arcgis.com'):
        self.gis = GIS(portal_url, username, password)
    
    def publish_project(self, project_id):
        """Publish project to ArcGIS Online"""
        
        # Get project data
        project = get_project(project_id)
        utility_lines = get_utility_lines(project_id)
        structures = get_utility_structures(project_id)
        
        # Convert to feature collections
        lines_fc = self.convert_to_feature_collection(utility_lines, 'Polyline')
        structures_fc = self.convert_to_feature_collection(structures, 'Point')
        
        # Create feature layers
        lines_layer = self.gis.content.add(
            {
                'title': f'{project.project_name} - Utility Lines',
                'type': 'Feature Service',
                'data': lines_fc
            }
        )
        
        structures_layer = self.gis.content.add(
            {
                'title': f'{project.project_name} - Structures',
                'type': 'Feature Service',
                'data': structures_fc
            }
        )
        
        # Create web map
        webmap = self.gis.map()
        webmap.add_layer(lines_layer)
        webmap.add_layer(structures_layer)
        webmap.save({
            'title': f'{project.project_name} - Web Map',
            'snippet': 'Published from ACAD-GIS',
            'tags': ['ACAD-GIS', 'CAD', project.project_name]
        })
        
        return PublishResult(
            webmap_url=webmap.url,
            success=True
        )
```

#### 5. Civil 3D Export
Export to Autodesk Civil 3D format:

**Export Formats**:
- LandXML (.xml) - Industry standard for civil engineering
- AutoCAD DWG with Civil 3D objects
- Pipe network data

**Implementation**:
```python
# services/civil3d_exporter.py
import xml.etree.ElementTree as ET

class Civil3DExporter:
    def export_to_landxml(self, project_id, output_path):
        """Export project to LandXML format"""
        
        # Create LandXML structure
        landxml = ET.Element('LandXML', {
            'version': '1.2',
            'xmlns': 'http://www.landxml.org/schema/LandXML-1.2'
        })
        
        # Add project units
        units = ET.SubElement(landxml, 'Units')
        ET.SubElement(units, 'Metric', {
            'areaUnit': 'squareMeter',
            'linearUnit': 'meter',
            'volumeUnit': 'cubicMeter'
        })
        
        # Add pipe networks
        pipe_networks = ET.SubElement(landxml, 'PipeNetworks')
        
        project = get_project(project_id)
        utility_lines = get_utility_lines(project_id)
        structures = get_utility_structures(project_id)
        
        # Add network
        network = ET.SubElement(pipe_networks, 'PipeNetwork', {
            'name': project.project_name
        })
        
        # Add structures
        for structure in structures:
            struct_elem = ET.SubElement(network, 'Struct', {
                'name': structure.structure_number
            })
            ET.SubElement(struct_elem, 'Center').text = f'{structure.x} {structure.y} {structure.z}'
            ET.SubElement(struct_elem, 'Rim').text = str(structure.rim_elevation)
        
        # Add pipes
        for line in utility_lines:
            pipe_elem = ET.SubElement(network, 'Pipe', {
                'name': line.line_number,
                'material': line.material
            })
            # Add geometry
        
        # Write to file
        tree = ET.ElementTree(landxml)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        
        return ExportResult(success=True, file_path=output_path)
```

#### 6. Weather Data Integration
Fetch rainfall data for stormwater modeling:

**Data Sources**:
- NOAA National Weather Service API (free)
- OpenWeatherMap API (free tier available)
- Weather Underground (historical data)

**Implementation**:
```python
# services/weather_service.py
class WeatherService:
    def fetch_rainfall_data(self, latitude, longitude, start_date, end_date):
        """Fetch historical rainfall data from NOAA"""
        
        # NOAA API endpoint
        url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/data'
        
        headers = {
            'token': os.getenv('NOAA_API_KEY')
        }
        
        params = {
            'datasetid': 'GHCND',  # Daily summaries
            'datatypeid': 'PRCP',  # Precipitation
            'locationid': f'FIPS:06',  # California
            'startdate': start_date,
            'enddate': end_date,
            'units': 'standard',
            'limit': 1000
        }
        
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        # Parse rainfall data
        rainfall_events = []
        for result in data.get('results', []):
            rainfall_events.append(RainfallEvent(
                date=result['date'],
                precipitation_inches=result['value'] / 10.0,  # Convert from mm
                station=result['station']
            ))
        
        return rainfall_events
    
    def get_design_storm(self, latitude, longitude, return_period_years=10):
        """Get design storm intensity for location"""
        # Use NOAA Atlas 14 or similar
        # Return intensity-duration-frequency (IDF) curves
        pass
```

#### 7. Coordinate Transformation Service
Automated SRID conversion:

**Implementation**:
```python
# services/coordinate_transformer.py
from pyproj import Transformer

class CoordinateTransformService:
    def __init__(self):
        # Cache transformers for performance
        self.transformers = {}
    
    def transform(self, geometry, from_srid, to_srid):
        """Transform geometry between coordinate systems"""
        
        # Get or create transformer
        transformer_key = f'{from_srid}_{to_srid}'
        if transformer_key not in self.transformers:
            self.transformers[transformer_key] = Transformer.from_crs(
                f'EPSG:{from_srid}',
                f'EPSG:{to_srid}',
                always_xy=True
            )
        
        transformer = self.transformers[transformer_key]
        
        # Transform coordinates
        if geometry.geom_type == 'Point':
            x, y = transformer.transform(geometry.x, geometry.y)
            return Point(x, y)
        
        elif geometry.geom_type == 'LineString':
            coords = [transformer.transform(x, y) for x, y in geometry.coords]
            return LineString(coords)
        
        # Handle other geometry types...
    
    def auto_detect_srid(self, sample_coordinates):
        """Attempt to detect coordinate system from sample points"""
        # Check coordinate ranges to guess SRID
        # California State Plane Zone 3: X ~6M-7M, Y ~2M-2.5M
        # WGS84: X ~-122, Y ~37
        
        x, y = sample_coordinates[0]
        
        if -180 <= x <= 180 and -90 <= y <= 90:
            return 4326  # WGS84 (lat/lon)
        
        elif 6000000 <= x <= 7000000 and 2000000 <= y <= 2500000:
            return 2226  # California State Plane Zone 3
        
        return None  # Unknown
```

## Implementation Phases

### Phase 1: WMS/WFS Municipal Connector (Week 1-2)

**Tasks**:
1. Catalog 10+ municipal WMS/WFS services in California
2. Build WMS/WFS connector service
3. Create external data storage tables
4. Build UI for browsing available layers
5. Integrate WMS imagery into Map Viewer as basemap option

**Deliverables**:
- Working connections to 10+ municipalities
- Parcel data import functional
- Live aerial imagery basemaps
- UI for selecting data sources

### Phase 2: Geocoding Service (Week 3)

**Tasks**:
1. Integrate Nominatim (free) and Google Maps (paid) APIs
2. Build geocoding service wrapper
3. Add address search to Map Viewer
4. Implement reverse geocoding (click map → address)
5. Batch geocoding for project list

**Deliverables**:
- Address search working in Map Viewer
- Geocoding confidence scores
- Batch geocoding tool
- API endpoints for geocoding

### Phase 3: Survey Equipment Import (Week 4-5)

**Tasks**:
1. Build Trimble JobXML parser
2. Build Leica GSI parser
3. Build Topcon GTS parser
4. Create unified survey import UI
5. Add coordinate system auto-detection

**Deliverables**:
- Support for 3+ survey equipment formats
- Enhanced Batch Point Import tool
- Coordinate system validation
- Import preview with stats

### Phase 4: ArcGIS Online Export (Week 6-7)

**Tasks**:
1. Set up Replit integration for ESRI API key
2. Build ArcGIS Online connector
3. Implement feature layer publishing
4. Create web map generation
5. Add "Publish to ArcGIS" button in Project Command Center

**Deliverables**:
- One-click publish to ArcGIS Online
- Automated web map creation
- Share link generation
- Sync status tracking

### Phase 5: Civil 3D Export (Week 8)

**Tasks**:
1. Build LandXML exporter
2. Implement pipe network XML schema
3. Add alignment export
4. Create surface/terrain export (optional)
5. Add "Export to Civil 3D" option in DXF Tools

**Deliverables**:
- LandXML export functional
- Civil 3D can import ACAD-GIS projects
- All attributes preserved
- Validation against LandXML schema

### Phase 6: Weather Data Integration (Week 9)

**Tasks**:
1. Set up NOAA API integration
2. Build rainfall data fetcher
3. Create design storm calculator
4. Add weather data to Project metadata
5. Build rainfall analysis dashboard

**Deliverables**:
- Historical rainfall data retrieval
- Design storm calculations
- Weather dashboard in Project Command Center
- API endpoints for weather data

### Phase 7: Coordinate Transformation (Week 10)

**Tasks**:
1. Build coordinate transformation service
2. Implement auto-SRID detection
3. Create batch transformation tool
4. Add transformation preview
5. Integrate with all import/export tools

**Deliverables**:
- Automated coordinate transformations
- SRID detection from coordinates
- Transformation accuracy validation
- Integration with existing workflows

## Database Schema Extensions

```sql
-- External data sources registry
CREATE TABLE external_data_sources (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name VARCHAR(100),
    source_type VARCHAR(50), -- WMS, WFS, GEOCODING, WEATHER
    base_url TEXT,
    api_key_required BOOLEAN,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB
);

-- Geocoding cache
CREATE TABLE geocoding_cache (
    cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    address_input TEXT,
    latitude DECIMAL(10,7),
    longitude DECIMAL(11,7),
    formatted_address TEXT,
    confidence DECIMAL(3,2),
    geocoder_source VARCHAR(50),
    cached_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(address_input, geocoder_source)
);

-- Weather data storage
CREATE TABLE weather_data (
    weather_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    data_type VARCHAR(50), -- RAINFALL, TEMPERATURE
    measurement_date DATE,
    value DECIMAL(10,3),
    units VARCHAR(20),
    data_source VARCHAR(100),
    fetched_at TIMESTAMP DEFAULT NOW()
);

-- ArcGIS Online publications
CREATE TABLE arcgis_publications (
    publication_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    webmap_id VARCHAR(100),
    webmap_url TEXT,
    published_at TIMESTAMP DEFAULT NOW(),
    published_by UUID,
    status VARCHAR(20) -- ACTIVE, OUTDATED, DELETED
);
```

## API Endpoints

### Municipal Data
- `GET /api/external/sources` - List available data sources
- `POST /api/external/fetch-parcels` - Fetch parcel data
- `GET /api/external/wms-layers/{source_id}` - List WMS layers

### Geocoding
- `POST /api/geocoding/forward` - Address → coordinates
- `POST /api/geocoding/reverse` - Coordinates → address
- `POST /api/geocoding/batch` - Batch geocoding

### Survey Import
- `POST /api/survey/import` - Import survey data file
- `GET /api/survey/formats` - List supported formats

### ArcGIS Online
- `POST /api/arcgis/publish/{project_id}` - Publish to ArcGIS
- `GET /api/arcgis/publications/{project_id}` - List publications
- `DELETE /api/arcgis/publication/{publication_id}` - Remove publication

### Export
- `POST /api/export/landxml/{project_id}` - Export to LandXML
- `POST /api/export/geodatabase/{project_id}` - Export to geodatabase

### Weather
- `GET /api/weather/rainfall/{project_id}` - Get rainfall data
- `GET /api/weather/design-storm` - Calculate design storm

## Dependencies & Requirements

### Python Packages
- `owslib>=0.29.0` - WMS/WFS client (already installed)
- `arcgis>=2.1.0` - ArcGIS Python API
- `requests>=2.31.0` - HTTP client
- `lxml>=4.9.0` - XML processing

### Replit Integrations
- Search for Google Maps API connector (for geocoding)
- Search for ESRI ArcGIS connector (for ArcGIS Online)
- Search for NOAA API connector (for weather data)

### External API Keys Required
- Google Maps API key (optional, for better geocoding)
- ESRI Developer account (for ArcGIS Online)
- NOAA API token (free)

## Risk Assessment

### Technical Risks
- **External API dependencies**: Services may be down or rate-limited
  - **Mitigation**: Caching, fallback providers, graceful degradation
- **Data format changes**: External data schemas may change
  - **Mitigation**: Version detection, schema validation
- **Coordinate accuracy**: Transformations may introduce errors
  - **Mitigation**: Validation checks, tolerance warnings

### Cost Risks
- **API usage costs**: Google Maps charges per request
  - **Mitigation**: Use free tier (Nominatim), implement caching
- **ArcGIS Online credits**: Publishing consumes credits
  - **Mitigation**: Inform users of costs, optimize data transfer

## Success Criteria

### Must Have
- ✅ Connect to 10+ municipal data sources
- ✅ Geocoding working with 95%+ success rate
- ✅ Survey import supports 3+ equipment formats
- ✅ Export to LandXML preserves all data

### Should Have
- ✅ ArcGIS Online publishing functional
- ✅ Weather data integration working
- ✅ Coordinate transformations accurate to <0.1 ft
- ✅ WMS imagery integrated into Map Viewer

### Nice to Have
- ✅ Bidirectional sync with ArcGIS Online
- ✅ Real-time weather alerts
- ✅ Auto-update external data nightly
- ✅ Export to QGIS format

## Timeline Summary
- **Phase 1**: Weeks 1-2 (Municipal Connector)
- **Phase 2**: Week 3 (Geocoding)
- **Phase 3**: Weeks 4-5 (Survey Import)
- **Phase 4**: Weeks 6-7 (ArcGIS Online)
- **Phase 5**: Week 8 (Civil 3D Export)
- **Phase 6**: Week 9 (Weather Data)
- **Phase 7**: Week 10 (Coordinate Transform)

**Total Duration**: 10 weeks

## ROI & Business Value
- **Data Access**: Leverage free government GIS data
- **Client Collaboration**: Share projects via ArcGIS Online
- **Interoperability**: Export to any industry format
- **Survey Integration**: Direct import from field equipment
- **Engineering Analysis**: Weather data for calculations
- **Time Savings**: Automated data retrieval vs. manual download
- **Competitive Edge**: Seamless CAD/GIS integration
