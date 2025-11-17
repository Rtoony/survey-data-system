"""
Project Spec Service
Manages project-level spec instances with variance tracking (Sheet Notes pattern)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.db_utils import execute_query
from typing import List, Dict, Optional
import json

class ProjectSpecService:
    """Service for managing project spec instances"""

    def get_project_specs(self, project_id: str) -> List[Dict]:
        """Get all specs for a project with effective content"""
        query = """
            SELECT * FROM vw_project_spec_content
            WHERE project_id = %s
            ORDER BY standard_name, effective_spec_number
        """
        return execute_query(query, (project_id,))

    def get_by_id(self, project_spec_id: str) -> Optional[Dict]:
        """Get a single project spec by ID"""
        query = """
            SELECT * FROM vw_project_spec_content
            WHERE project_spec_id = %s
        """
        results = execute_query(query, (project_spec_id,))
        return results[0] if results else None

    def add_standard_to_project(self, project_id: str, spec_library_id: str) -> Dict:
        """Add a library spec to project as 'standard' (unmodified)"""
        query = """
            INSERT INTO project_specs (
                project_id, spec_library_id, source_type
            ) VALUES (%s, %s, 'standard')
            RETURNING project_spec_id
        """
        result = execute_query(query, (project_id, spec_library_id))
        if result:
            return self.get_by_id(result[0]['project_spec_id'])
        return None

    def modify_standard_in_project(self, project_spec_id: str, new_content: Dict, deviation_reason: str = None, modified_by: str = None) -> bool:
        """Modify a spec for this project (changes source_type to 'modified_standard')"""
        query = """
            UPDATE project_specs SET
                source_type = 'modified_standard',
                project_content_json = %s,
                deviation_reason = %s,
                modified_by = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE project_spec_id = %s
            RETURNING project_spec_id
        """

        if isinstance(new_content, str):
            new_content = json.loads(new_content)

        result = execute_query(query, (
            json.dumps(new_content),
            deviation_reason,
            modified_by,
            project_spec_id
        ))
        return bool(result)

    def create_custom_spec(self, project_id: str, spec_data: Dict) -> Dict:
        """Create a fully custom spec for this project (not based on library)"""
        query = """
            INSERT INTO project_specs (
                project_id, source_type, project_content_json,
                project_spec_number, project_spec_title, deviation_reason, modified_by
            ) VALUES (%s, 'custom', %s, %s, %s, %s, %s)
            RETURNING project_spec_id
        """

        content_json = spec_data.get('content_json')
        if isinstance(content_json, str):
            content_json = json.loads(content_json)

        result = execute_query(query, (
            project_id,
            json.dumps(content_json) if content_json else None,
            spec_data['spec_number'],
            spec_data['spec_title'],
            spec_data.get('deviation_reason'),
            spec_data.get('modified_by')
        ))

        if result:
            return self.get_by_id(result[0]['project_spec_id'])
        return None

    def delete(self, project_spec_id: str) -> bool:
        """Delete a project spec"""
        query = "DELETE FROM project_specs WHERE project_spec_id = %s RETURNING project_spec_id"
        try:
            execute_query(query, (project_spec_id,), fetch=False)
            return True
        except Exception as e:
            print(f"Cannot delete project spec: {e}")
            return False

    def revert_to_standard(self, project_spec_id: str) -> bool:
        """Revert a modified spec back to standard (remove project overrides)"""
        query = """
            UPDATE project_specs SET
                source_type = 'standard',
                project_content_json = NULL,
                deviation_reason = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE project_spec_id = %s AND spec_library_id IS NOT NULL
            RETURNING project_spec_id
        """
        result = execute_query(query, (project_spec_id,))
        return bool(result)
