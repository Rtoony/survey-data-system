# ACAD-GIS Quick Reference

## API Base
`http://localhost:8000/api`

## Common Endpoints
- `GET /health`, `GET /stats`
- `GET /projects`, `GET /projects/{id}`
- `GET /projects/{id}/drawings`
- `GET /drawings`, `GET /drawings/{id}`, `GET /drawings/{id}/render`
- Planned: `GET /drawings/{id}/extent`, `GET /drawings/{id}/geojson?bbox=&srid=&simplify=`
- Planned: `GET /layers/{layer}/geojson?bbox=&srid=&simplify=&limit=`

## Frontend Paths
- Launcher: `tool_launcher.html:1`
- Tools: `frontend/tools/*.html`
- Shared: `frontend/shared/*`

## CRS Notes
- Canonical: EPSG:4326 (exchange), EPSG:3857 (tiles)
- Known native: EPSG:2226 (State Plane Zone 2, ftUS)

## Troubleshooting
- Duplicate global error (ToastManager already declared): hard refresh (Ctrl+Shift+R) to clear cached script.
- file:// loading: some browsers cache aggressively; consider serving static files during dev.
