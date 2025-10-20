# ACAD‑GIS Beginner’s Guide

Last Updated: October 2025

## What This Is
ACAD‑GIS is a web-based system for managing CAD drawings with GIS context. The backend is a FastAPI server in Python; the frontend is a set of simple HTML pages that load React from a CDN (no build step). Data ultimately lives in PostgreSQL with PostGIS for spatial features.

## The Big Idea (Data‑First)
- Store structured engineering data in a database first.
- Generate outputs (DXF, LandXML, SVG, JSON, CSV) from that data.
- Use small, focused tools (pages) rather than one huge app.

## Architecture (How It Fits Together)
- Browser UI (HTML + React) → calls `http://localhost:8000/api/...` → FastAPI → PostgreSQL/PostGIS.
- Frontend uses shared helpers (`frontend/shared/`) for API calls, components, and styles.
- The backend exposes REST endpoints for projects, drawings, health/stats, and stubs for future civil tools.

## Tools/Tech Used
- Backend: Python 3.12, FastAPI, Uvicorn, psycopg2, Pydantic.
- Database: PostgreSQL (Supabase) + PostGIS.
- Frontend: React 18 via CDN, Babel Standalone (for inline JSX), plain HTML files.
- No build system required; edit files and refresh the browser.

## What’s Working Today
- FastAPI server with health (`/api/health`) and stats (`/api/stats`).
- Project and drawing endpoints (basic CRUD patterns present).
- DXF import/export stubs.
- Frontend: Tool Launcher, Project Manager, Drawing Browser, Map Viewer.
- CivilMicroTools (mock): Pipe Network Editor, Alignment Editor, BMP Manager, Utility Coordination, Plot & Profile Manager, Sheet Note Manager. These call stub endpoints so you can explore UI flows while the schema is planned.

## Where Things Live (Repo Map)
- Backend (API): `backend/api_server_ENHANCED.py`, DB helpers `backend/database.py`.
- Frontend (tools): `frontend/tools/*.html` (each tool is its own page).
- Shared frontend: `frontend/shared/styles.css`, `frontend/shared/components.js`, `frontend/shared/api.js`, `frontend/shared/react-components.js`.
- Docs: `docs/` (roadmap, setup guides, API, schema, CivilMicroTools plan, this guide).
- Prototypes: `prototypes/` (exploration and inspiration code/data).

## Run It Locally (Dev)
1) Start the API server
- In your Python env: `python backend/api_server_ENHANCED.py`
- You should see: `Server running at: http://localhost:8000`
- Open API docs: `http://localhost:8000/docs`

2) Open the frontend
- Open `tool_launcher.html` in your browser (double-click or serve statically).
- The top-right status shows API Online/Offline.

3) Try a few tools
- Project Manager: `frontend/tools/project-manager.html`
- Drawing Browser: `frontend/tools/drawing-browser.html`
- Map Viewer: `frontend/tools/map_viewer.html`
- Civil (mocked): `pipe-network-editor.html`, `alignment-editor.html`, `bmp-manager.html`, `utility-coordination.html`, `plot-profile-manager.html`, `sheet-note-manager.html`

Tip: You can also launch tools from the cards in `tool_launcher.html`.

## API Base URL (Frontend)
- Default: `http://localhost:8000/api`.
- Change it by editing `frontend/shared/components.js` (the `API_BASE_URL` constant) if your server runs on a different port.

## Database Setup (Simple View)
- The API reads connection info from environment variables (.env). See `backend/database.py` for required variables: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
- With no database configured, you can still explore the frontend and mocked civil tools; API health may show “disconnected”.
- PostGIS should be enabled on your database when spatial data is added later.

## CivilMicroTools (Future, Mocked Now)
- Data-first civil tools inspired by CivilOS: Pipe Networks, Alignments, BMPs, Utilities, Plot/Profile, Sheet Notes.
- Endpoints exist as stubs so UIs can be prototyped before the database schema is finalized.
- See `docs/CIVILMICROTOOLS_PLAN.md` for the phased plan and example DDL.

## Troubleshooting
- API Offline in launcher: confirm FastAPI is running at `http://localhost:8000` and CORS is allowed (it is by default).
- 404s from new civil endpoints: stubs should respond; if not, ensure you pulled latest changes and restarted the API.
- DB connection errors on `/api/health`: verify `.env` values; Supabase should be reachable; for local dev you can proceed without DB while you explore UI.

## What’s Next (High-Level)
- Finalize schemas for Pipe Networks, Alignments, BMPs, Utilities.
- Replace mock endpoints with real CRUD and GeoJSON queries.
- Add validations (pipe slope minimums, BMP compliance, clash detection).
- Implement exports (DXF/LandXML/SVG/JSON/CSV) from database state.

## Glossary
- DXF: CAD drawing file format; used for import/export.
- GeoJSON: JSON format for map features and geometries.
- PostGIS: PostgreSQL extension for spatial types and queries.
- DataTable: Reusable React table with search/sort/pagination.

## Quick Checklist
- Backend running on port 8000.
- Frontend pages open and hitting `http://localhost:8000/api`.
- Tools visible in `tool_launcher.html`.
- Civil tools load and show tables (data is mocked for now).

You’re ready to explore. When the schema is finalized, we’ll flip the stubs to real endpoints and wire the tools to the database.

