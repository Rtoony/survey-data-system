#!/usr/bin/env python3
"""
Database Layer Refactoring Script
Migrates files from legacy database.py to new app/db_session.py

This script performs the following transformations:
1. Updates imports from 'database' to 'app.db_session' and 'sqlalchemy'
2. Converts execute_query() calls to use get_db_connection() with text()
3. Converts get_db() context managers to get_db_connection()
4. Removes DB_CONFIG usage where possible
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def refactor_imports(content: str) -> str:
    """Replace legacy database imports with new imports."""

    # Pattern 1: from database import execute_query, get_db, DB_CONFIG
    # Pattern 2: from database import execute_query
    # Pattern 3: from database import get_db, execute_query, DB_CONFIG

    # First, check what's being imported
    import_match = re.search(r'from database import (.+)', content)

    if not import_match:
        return content

    imports = import_match.group(1)

    # Build new imports
    new_imports = []

    if 'execute_query' in imports or 'get_db' in imports:
        new_imports.append('from app.db_session import get_db_connection')
        new_imports.append('from sqlalchemy import text')

    if 'DB_CONFIG' in imports:
        # DB_CONFIG is trickier - it may need special handling per file
        new_imports.append('# NOTE: DB_CONFIG removed - update manually if needed')

    # Replace the import line
    new_import_block = '\n'.join(new_imports)
    content = re.sub(r'from database import .+\n', new_import_block + '\n', content)

    return content


def convert_execute_query_simple(content: str) -> str:
    """
    Convert simple execute_query() calls to new pattern.

    Pattern:
        result = execute_query("SELECT ...", (params,))
    Becomes:
        with get_db_connection() as conn:
            result = conn.execute(text("SELECT ..."), {"param0": params[0], ...})
            rows = [dict(row._mapping) for row in result]
    """

    # This is complex and error-prone to automate fully
    # For now, just add a comment marker
    if 'execute_query(' in content:
        # Add a marker comment at the top
        if '# TODO: REFACTOR execute_query calls' not in content:
            content = '# TODO: REFACTOR execute_query calls to use get_db_connection()\n' + content

    return content


def convert_get_db_context(content: str) -> str:
    """
    Convert get_db() context managers to get_db_connection().

    Pattern:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("...", params)
    Becomes:
        with get_db_connection() as conn:
            conn.execute(text("..."), {...})
    """

    # Add marker for manual refactoring
    if 'with get_db()' in content:
        if '# TODO: REFACTOR get_db() calls' not in content:
            content = '# TODO: REFACTOR get_db() calls to use get_db_connection()\n' + content

    return content


def refactor_file(file_path: Path) -> bool:
    """Refactor a single file. Returns True if changes were made."""

    try:
        content = file_path.read_text()

        # Check if file uses database.py
        if 'from database import' not in content and 'import database' not in content:
            return False

        print(f"Refactoring: {file_path}")

        # Apply transformations
        original_content = content
        content = refactor_imports(content)
        content = convert_execute_query_simple(content)
        content = convert_get_db_context(content)

        # Write back if changed
        if content != original_content:
            file_path.write_text(content)
            return True

        return False

    except Exception as e:
        print(f"Error refactoring {file_path}: {e}")
        return False


def main():
    """Main entry point."""

    # Files to refactor (Python files only, excluding documentation and backups)
    files_to_check = [
        'services/relationship_validation_service.py',
        'services/relationship_graph_service.py',
        'services/semantic_search_service.py',
        'services/validation_helper.py',
        'services/graph_analytics_service.py',
        'services/graphrag_service.py',
        'services/project_mapping_service.py',
        'services/rbac_service.py',
        'app/blueprints/classification.py',
        'app/blueprints/survey_codes.py',
        'app/blueprints/specialized_tools.py',
        'app/blueprints/pipe_networks.py',
        'app/blueprints/details_management.py',
        'app/blueprints/blocks_management.py',
        'app/blueprints/projects.py',
        'app/blueprints/gis_engine.py',
        'app/blueprints/standards.py',
        'app/tasks.py',
        'api/quality_routes.py',
        'db.py',
        'scripts/run_migration_041.py',
        'scripts/z_stress_harness.py',
        'tools/backfill_entity_layers.py',
    ]

    base_dir = Path(__file__).parent

    refactored_count = 0
    for file_rel_path in files_to_check:
        file_path = base_dir / file_rel_path
        if file_path.exists():
            if refactor_file(file_path):
                refactored_count += 1
        else:
            print(f"Warning: File not found: {file_path}")

    print(f"\nRefactored {refactored_count} files")
    print("Note: This script only handles import replacements and adds TODO markers.")
    print("Manual refactoring is still required for execute_query() and get_db() calls.")


if __name__ == '__main__':
    main()
