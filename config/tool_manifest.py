# config/tool_manifest.py
from typing import Dict, Any, List

# --- Tool Manifest Structure ---
# Defines the metadata for tools and features accessible from the Command Center UI.
# The UI will consume this to build dynamic menus and authorization checks.

TOOL_MANIFEST: Dict[str, Dict[str, Any]] = {
    # --- Standards Management & QA/QC ---
    "STANDARDS_MANAGER": {
        "title": "Standards Mapping Console",
        "description": "Create, edit, and version control Feature Code to CAD Mappings.",
        "route_prefix": "/ssm/config",
        "is_specialized": False
    },

    # --- Debugging & Validation Tools ---
    "SSM_DEBUGGER": {
        "title": "What If? Scenario Tester",
        "description": "Run raw data through the pipeline step-by-step to debug resolution conflicts.",
        "api_route": "/api/v1/tools/scenario/run",
        "phase": 30,
        "is_specialized": True
    },
    "AUDIT_SNAPSHOT": {
        "title": "Audit & Version Control",
        "description": "Create immutable snapshots and compare standards versions for compliance.",
        "api_route": "/api/v1/audit/snapshot",
        "phase": 31,
        "is_specialized": True
    },

    # --- Specialized GIS & Analysis Tools ---
    "CONFLICT_ANALYZE": {
        "title": "3D Utility Conflict Analyzer",
        "description": "Automated check for spatial clashes between proposed designs and existing utilities.",
        "api_route": "/api/v1/analysis/conflict",
        "phase": 45,
        "is_specialized": True
    },
    "CHANGE_IMPACT": {
        "title": "Standards Change Impact Analyzer",
        "description": "Predict which existing projects will be affected before rolling out a new standard.",
        "api_route": "/api/v1/analysis/impact",
        "phase": 39,
        "is_specialized": True
    },
    "GKG_CLUSTERING": {
        "title": "Cross-Project Asset Clustering Tool",
        "description": "Leverage the Knowledge Graph to find similar physical assets across all projects for anomaly detection.",
        "api_route": "/api/v1/gkg/clustering",
        "phase": 40,
        "is_specialized": True
    },

    # --- Documentation & Compliance Tools ---
    "NOTE_MANAGER": {
        "title": "Sheet Note Compliance Manager",
        "description": "Manage standard boilerplate notes and link them to project compliance requirements.",
        "api_route": "/api/v1/mgmt/notes",
        "phase": 41,
        "is_specialized": True
    },
    "SPEC_MANAGER": {
        "title": "Specification Constraint Enforcer",
        "description": "Manage construction specs and generate high-priority mappings to enforce material constraints.",
        "api_route": "/api/v1/mgmt/specs",
        "phase": 43,
        "is_specialized": True
    },

    # --- Data Ingestion Tools ---
    "IMPORT_WIZARD": {
        "title": "Field Data Import Wizard",
        "description": "Clean, validate, and stage raw survey data files (CSV/TXT) for database loading.",
        "api_route": "/api/v1/data/import",
        "phase": 46,
        "is_specialized": False
    }
}
