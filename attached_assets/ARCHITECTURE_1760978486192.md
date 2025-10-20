# ACAD-GIS Architecture

## Overview
Open, Python-first system where PostGIS is the source of truth. The UI is a thin client to visualize and operate on data; design work happens in Python.

## Components
- Ingest: DXF via ezdxf → extract primitives/blocks/attributes
- Normalize: transform to canonical PostGIS geometries with metadata and lineage
- Store: PostgreSQL + PostGIS with SRID/units policies
- Serve: FastAPI endpoints (CRUD + spatial, bbox GeoJSON)
- Visualize: Leaflet-based tools reading API responses
- Tools: Python “mini-apps” (e.g., subdivision, pipe networks, grading) that read/write DB and output DXF/GeoJSON

## Data Flow
```
DXF → ezdxf → Normalize (CRS/units) → PostGIS → FastAPI (GeoJSON/bbox) → Leaflet
```

## Trust Boundaries
- Server: owns DB credentials; performs validation and transformations
- Client: read-only by default; uploads DXF via authenticated endpoints

## Storage Conventions
- Canonical SRID: EPSG:4326 for exchange; EPSG:3857 for tiles
- Retain native EPSG per drawing; record unit and conversion factor
- Index geometries (GIST) and common attributes (BTREE)

## Artifacts
- DXF/GeoJSON exports stored on disk or object storage; DB stores metadata and hashes

