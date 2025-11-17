"""
Spec Standards Service
Manages CRUD operations for spec_standards_registry (Reference Data Hub table)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.db_utils import execute_query
from typing import List, Dict, Optional
import uuid

class SpecStandardsService:
    """Service for managing specification standards registry"""

    def get_all(self) -> List[Dict]:
        """Get all spec standards"""
        query = """
            SELECT
                spec_standard_id,
                standard_name,
                governing_body,
                description,
                abbreviation,
                website_url,
                created_at,
                updated_at
            FROM spec_standards_registry
            ORDER BY standard_name
        """
        return execute_query(query)

    def get_by_id(self, spec_standard_id: str) -> Optional[Dict]:
        """Get a single spec standard by ID"""
        query = """
            SELECT * FROM spec_standards_registry
            WHERE spec_standard_id = %s
        """
        results = execute_query(query, (spec_standard_id,))
        return results[0] if results else None

    def create(self, data: Dict) -> Dict:
        """Create new spec standard"""
        query = """
            INSERT INTO spec_standards_registry (
                standard_name, governing_body, description, abbreviation, website_url
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING spec_standard_id, standard_name, abbreviation
        """
        result = execute_query(query, (
            data['standard_name'],
            data.get('governing_body'),
            data.get('description'),
            data.get('abbreviation'),
            data.get('website_url')
        ))
        return result[0] if result else None

    def update(self, spec_standard_id: str, data: Dict) -> bool:
        """Update existing spec standard"""
        query = """
            UPDATE spec_standards_registry SET
                standard_name = %s,
                governing_body = %s,
                description = %s,
                abbreviation = %s,
                website_url = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE spec_standard_id = %s
            RETURNING spec_standard_id
        """
        result = execute_query(query, (
            data['standard_name'],
            data.get('governing_body'),
            data.get('description'),
            data.get('abbreviation'),
            data.get('website_url'),
            spec_standard_id
        ))
        return bool(result)

    def delete(self, spec_standard_id: str) -> bool:
        """Delete spec standard (only if no specs reference it)"""
        query = "DELETE FROM spec_standards_registry WHERE spec_standard_id = %s RETURNING spec_standard_id"
        try:
            result = execute_query(query, (spec_standard_id,), fetch=False)
            return True
        except Exception as e:
            print(f"Cannot delete standard: {e}")
            return False
