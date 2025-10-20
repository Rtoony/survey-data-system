# API Guide

Base URL (dev): `http://localhost:8000/api`
Note: If your FastAPI server runs on 5000, set `API_BASE_URL` accordingly.

## Health and Stats
- `GET /api/health` — DB connectivity and counts
- `GET /api/stats` — totals and recent drawings

## Projects
- `GET /api/projects` — list projects with drawing counts
- `GET /api/projects/{project_id}` — project details
- `GET /api/projects/{project_id}/drawings` — drawings in project
- `POST /api/projects` — create
- `PUT /api/projects/{project_id}` — update
- `DELETE /api/projects/{project_id}` — delete

## Drawings
- `GET /api/drawings` - list
- `GET /api/drawings/{drawing_id}` - details
- `GET /api/drawings/{drawing_id}/render` - summary + bounds (current)
- Planned: `GET /api/drawings/{drawing_id}/extent`
- Planned: `GET /api/drawings/{drawing_id}/geojson?bbox=&srid=&simplify=`

## Layers (planned)
- `GET /api/layers/{layer}/geojson?bbox=&srid=&simplify=&limit=`

## Import/Export
- `POST /api/import/dxf` - upload DXF (stub)
- Planned: Export endpoints for GeoJSON/GPKG and tiles

## CivilMicroTools (New)

### Pipe Networks
- `GET /api/pipe-networks` | `POST /api/pipe-networks`
- `GET /api/pipe-networks/{id}` | `PUT /api/pipe-networks/{id}` | `DELETE /api/pipe-networks/{id}`
- `GET /api/pipes` | `POST /api/pipes` | `GET/PUT/DELETE /api/pipes/{id}`
- `GET /api/structures` | `POST /api/structures` | `GET/PUT/DELETE /api/structures/{id}`
- GeoJSON: `GET /api/pipes/geojson?bbox=&srid=&limit=` | `GET /api/structures/geojson?bbox=&srid=&limit=`

### Alignments
- `GET /api/alignments` | `POST /api/alignments` | `GET/PUT/DELETE /api/alignments/{id}`
- Elements: `GET/POST /api/alignments/{id}/horizontal-elements` | `GET/POST /api/alignments/{id}/vertical-elements`
- GeoJSON: `GET /api/alignments/{id}/geojson`

### BMPs
- `GET /api/bmps` | `POST /api/bmps` | `GET/PUT/DELETE /api/bmps/{id}`
- Child: `GET/POST /api/bmps/{id}/inspections` | `GET/POST /api/bmps/{id}/maintenance`
- GeoJSON: `GET /api/bmps/geojson?bbox=&srid=&type=`

### Utilities & Conflicts
- `GET /api/utilities` | `POST /api/utilities` | `GET/PUT/DELETE /api/utilities/{id}`
- `GET /api/conflicts` | `POST /api/conflicts` | `PUT /api/conflicts/{id}`

### Validation & Analytics
- `POST /api/validate/pipe-slope` (by project/network)
- `POST /api/validate/velocity`
- `POST /api/clash-detection` (e.g., pipes vs utilities; tolerance optional)

### Exports
- `POST /api/export/dxf`
- `POST /api/export/landxml`
- `POST /api/export/svg`
- `POST /api/export/json` | `POST /api/export/csv`

## Notes
- BBOX parameters should be in `minx,miny,maxx,maxy` with SRID specified; server may simplify geometry by scale.

