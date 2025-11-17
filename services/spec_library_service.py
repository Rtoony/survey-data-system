"""
Spec Library Service
Manages CRUD operations for spec_library (Master Content Library)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.db_utils import execute_query
from typing import List, Dict, Optional
import json

class SpecLibraryService:
    """Service for managing specification library"""

    def get_all(self, spec_standard_id: Optional[str] = None) -> List[Dict]:
        """Get all spec library entries, optionally filtered by standard"""
        if spec_standard_id:
            query = """
                SELECT
                    sl.*,
                    sr.standard_name,
                    sr.abbreviation
                FROM spec_library sl
                JOIN spec_standards_registry sr ON sl.spec_standard_id = sr.spec_standard_id
                WHERE sl.spec_standard_id = %s
                ORDER BY sl.spec_number
            """
            return execute_query(query, (spec_standard_id,))
        else:
            query = """
                SELECT
                    sl.*,
                    sr.standard_name,
                    sr.abbreviation
                FROM spec_library sl
                JOIN spec_standards_registry sr ON sl.spec_standard_id = sr.spec_standard_id
                ORDER BY sr.standard_name, sl.spec_number
            """
            return execute_query(query)

    def get_by_id(self, spec_library_id: str) -> Optional[Dict]:
        """Get a single spec by ID"""
        query = """
            SELECT
                sl.*,
                sr.standard_name,
                sr.abbreviation,
                sr.governing_body
            FROM spec_library sl
            JOIN spec_standards_registry sr ON sl.spec_standard_id = sr.spec_standard_id
            WHERE sl.spec_library_id = %s
        """
        results = execute_query(query, (spec_library_id,))
        return results[0] if results else None

    def search(self, search_term: str) -> List[Dict]:
        """Search specs by number, title, or content"""
        query = """
            SELECT
                sl.*,
                sr.standard_name,
                sr.abbreviation
            FROM spec_library sl
            JOIN spec_standards_registry sr ON sl.spec_standard_id = sr.spec_standard_id
            WHERE
                sl.spec_number ILIKE %s OR
                sl.spec_title ILIKE %s OR
                sl.content_text ILIKE %s
            ORDER BY sr.standard_name, sl.spec_number
            LIMIT 50
        """
        search_pattern = f'%{search_term}%'
        return execute_query(query, (search_pattern, search_pattern, search_pattern))

    def create(self, data: Dict) -> Dict:
        """Create new spec library entry"""
        query = """
            INSERT INTO spec_library (
                spec_standard_id, spec_number, spec_title, source_document,
                content_structure, content_json, content_text,
                revision_date, effective_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING spec_library_id, spec_number, spec_title
        """

        content_json = data.get('content_json')
        if isinstance(content_json, str):
            content_json = json.loads(content_json)

        result = execute_query(query, (
            data['spec_standard_id'],
            data['spec_number'],
            data['spec_title'],
            data.get('source_document'),
            data.get('content_structure', 'narrative'),
            json.dumps(content_json) if content_json else None,
            data.get('content_text'),
            data.get('revision_date'),
            data.get('effective_date')
        ))
        return result[0] if result else None

    def update(self, spec_library_id: str, data: Dict) -> bool:
        """Update existing spec library entry"""
        query = """
            UPDATE spec_library SET
                spec_standard_id = %s,
                spec_number = %s,
                spec_title = %s,
                source_document = %s,
                content_structure = %s,
                content_json = %s,
                content_text = %s,
                revision_date = %s,
                effective_date = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE spec_library_id = %s
            RETURNING spec_library_id
        """

        content_json = data.get('content_json')
        if isinstance(content_json, str):
            content_json = json.loads(content_json)

        result = execute_query(query, (
            data['spec_standard_id'],
            data['spec_number'],
            data['spec_title'],
            data.get('source_document'),
            data.get('content_structure', 'narrative'),
            json.dumps(content_json) if content_json else None,
            data.get('content_text'),
            data.get('revision_date'),
            data.get('effective_date'),
            spec_library_id
        ))
        return bool(result)

    def delete(self, spec_library_id: str) -> bool:
        """Delete spec library entry"""
        query = "DELETE FROM spec_library WHERE spec_library_id = %s RETURNING spec_library_id"
        try:
            execute_query(query, (spec_library_id,), fetch=False)
            return True
        except Exception as e:
            print(f"Cannot delete spec: {e}")
            return False
