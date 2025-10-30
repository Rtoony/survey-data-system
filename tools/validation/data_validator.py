"""
Data Validation Module

Validate data quality, detect duplicates, check required fields,
and validate PostGIS geometries.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

sys.path.append(str(Path(__file__).parent.parent))

from db_utils import execute_query


class DataValidator:
    """Validate data quality and integrity."""
    
    def __init__(self):
        self.validation_results = {
            'tables_checked': 0,
            'total_issues': 0,
            'issues_by_type': {},
            'issues_by_table': {}
        }
    
    def check_required_fields(
        self,
        table_name: str,
        required_columns: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Check for missing required field values.
        
        Args:
            table_name: Table to check
            required_columns: List of column names that shouldn't be NULL
            
        Returns:
            List of issues found
        """
        issues = []
        
        for column in required_columns:
            query = f"""
                SELECT COUNT(*) as count
                FROM {table_name}
                WHERE {column} IS NULL OR {column} = ''
            """
            
            try:
                result = execute_query(query)
                count = result[0]['count'] if result else 0
                
                if count > 0:
                    issues.append({
                        'table': table_name,
                        'type': 'missing_required_field',
                        'column': column,
                        'count': count,
                        'severity': 'high'
                    })
                    
            except Exception as e:
                issues.append({
                    'table': table_name,
                    'type': 'validation_error',
                    'column': column,
                    'error': str(e),
                    'severity': 'error'
                })
        
        return issues
    
    def check_geometry_validity(self, table_name: str, geometry_column: str = 'geometry') -> List[Dict[str, Any]]:
        """
        Validate PostGIS geometries.
        
        Args:
            table_name: Table with geometry column
            geometry_column: Name of geometry column
            
        Returns:
            List of geometry issues
        """
        issues = []
        
        # Check for invalid geometries
        query = f"""
            SELECT COUNT(*) as count
            FROM {table_name}
            WHERE {geometry_column} IS NOT NULL 
              AND NOT ST_IsValid({geometry_column})
        """
        
        try:
            result = execute_query(query)
            count = result[0]['count'] if result else 0
            
            if count > 0:
                issues.append({
                    'table': table_name,
                    'type': 'invalid_geometry',
                    'column': geometry_column,
                    'count': count,
                    'severity': 'high'
                })
                
        except Exception as e:
            issues.append({
                'table': table_name,
                'type': 'geometry_check_error',
                'error': str(e),
                'severity': 'error'
            })
        
        # Check for NULL geometries
        query = f"""
            SELECT COUNT(*) as count
            FROM {table_name}
            WHERE {geometry_column} IS NULL
        """
        
        try:
            result = execute_query(query)
            count = result[0]['count'] if result else 0
            
            if count > 0:
                issues.append({
                    'table': table_name,
                    'type': 'null_geometry',
                    'column': geometry_column,
                    'count': count,
                    'severity': 'medium'
                })
                
        except Exception as e:
            pass
        
        return issues
    
    def check_duplicate_entities(self, table_name: str, unique_columns: List[str]) -> List[Dict[str, Any]]:
        """
        Find duplicate entities based on unique columns.
        
        Args:
            table_name: Table to check
            unique_columns: Columns that should be unique together
            
        Returns:
            List of duplicate issues
        """
        issues = []
        
        columns_str = ', '.join(unique_columns)
        query = f"""
            SELECT {columns_str}, COUNT(*) as count
            FROM {table_name}
            GROUP BY {columns_str}
            HAVING COUNT(*) > 1
        """
        
        try:
            result = execute_query(query)
            
            if result and len(result) > 0:
                issues.append({
                    'table': table_name,
                    'type': 'duplicate_records',
                    'columns': unique_columns,
                    'count': len(result),
                    'severity': 'medium',
                    'examples': result[:5]
                })
                
        except Exception as e:
            issues.append({
                'table': table_name,
                'type': 'duplicate_check_error',
                'error': str(e),
                'severity': 'error'
            })
        
        return issues
    
    def check_quality_scores(self, min_quality_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Find entities with low quality scores.
        
        Args:
            min_quality_threshold: Minimum acceptable quality score
            
        Returns:
            List of quality issues
        """
        issues = []
        
        query = """
            SELECT entity_type, COUNT(*) as count,
                   AVG(quality_score) as avg_quality,
                   MIN(quality_score) as min_quality
            FROM standards_entities
            WHERE quality_score < %s
            GROUP BY entity_type
        """
        
        try:
            result = execute_query(query, (min_quality_threshold,))
            
            if result and len(result) > 0:
                for row in result:
                    issues.append({
                        'table': 'standards_entities',
                        'type': 'low_quality_score',
                        'entity_type': row['entity_type'],
                        'count': row['count'],
                        'avg_quality': float(row['avg_quality']) if row['avg_quality'] else 0,
                        'min_quality': float(row['min_quality']) if row['min_quality'] else 0,
                        'severity': 'medium'
                    })
                    
        except Exception as e:
            issues.append({
                'table': 'standards_entities',
                'type': 'quality_check_error',
                'error': str(e),
                'severity': 'error'
            })
        
        return issues
    
    def check_missing_embeddings(self) -> List[Dict[str, Any]]:
        """Find entities without current embeddings."""
        issues = []
        
        query = """
            SELECT entity_type, COUNT(*) as count
            FROM standards_entities se
            WHERE NOT EXISTS (
                SELECT 1 FROM entity_embeddings ee
                WHERE ee.entity_id = se.entity_id AND ee.is_current = true
            )
            GROUP BY entity_type
        """
        
        try:
            result = execute_query(query)
            
            if result and len(result) > 0:
                for row in result:
                    issues.append({
                        'table': 'standards_entities',
                        'type': 'missing_embedding',
                        'entity_type': row['entity_type'],
                        'count': row['count'],
                        'severity': 'low'
                    })
                    
        except Exception as e:
            issues.append({
                'table': 'standards_entities',
                'type': 'embedding_check_error',
                'error': str(e),
                'severity': 'error'
            })
        
        return issues
    
    def validate_table(
        self,
        table_name: str,
        required_fields: Optional[List[str]] = None,
        unique_fields: Optional[List[str]] = None,
        has_geometry: bool = False
    ) -> Dict[str, Any]:
        """
        Comprehensive validation for a single table.
        
        Args:
            table_name: Table to validate
            required_fields: List of required columns
            unique_fields: Columns that should be unique together
            has_geometry: Whether table has geometry column to validate
            
        Returns:
            Dict with validation results
        """
        all_issues = []
        
        if required_fields:
            all_issues.extend(self.check_required_fields(table_name, required_fields))
        
        if unique_fields:
            all_issues.extend(self.check_duplicate_entities(table_name, unique_fields))
        
        if has_geometry:
            all_issues.extend(self.check_geometry_validity(table_name))
        
        return {
            'table': table_name,
            'issue_count': len(all_issues),
            'issues': all_issues
        }
    
    def validate_all_standards(self) -> Dict[str, Any]:
        """Validate all CAD standards tables."""
        print("Validating CAD Standards Tables...")
        print("=" * 60)
        
        all_issues = []
        
        # Layer standards
        print("  Checking layer_standards...")
        issues = self.validate_table(
            'layer_standards',
            required_fields=['name'],
            unique_fields=['name']
        )
        all_issues.extend(issues['issues'])
        
        # Block definitions
        print("  Checking block_definitions...")
        issues = self.validate_table(
            'block_definitions',
            required_fields=['name'],
            unique_fields=['name']
        )
        all_issues.extend(issues['issues'])
        
        # Detail standards
        print("  Checking detail_standards...")
        issues = self.validate_table(
            'detail_standards',
            required_fields=['detail_number'],
            unique_fields=['detail_number']
        )
        all_issues.extend(issues['issues'])
        
        # Quality scores
        print("  Checking quality scores...")
        all_issues.extend(self.check_quality_scores(min_quality_threshold=0.5))
        
        # Missing embeddings
        print("  Checking for missing embeddings...")
        all_issues.extend(self.check_missing_embeddings())
        
        print()
        print("Validation Complete!")
        print("=" * 60)
        print(f"Total issues found: {len(all_issues)}")
        
        # Group by severity
        severity_counts = {}
        for issue in all_issues:
            severity = issue.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        for severity, count in severity_counts.items():
            print(f"  {severity.upper()}: {count}")
        
        return {
            'total_issues': len(all_issues),
            'issues_by_severity': severity_counts,
            'issues': all_issues
        }


if __name__ == '__main__':
    # Example usage
    validator = DataValidator()
    
    print("Data Validator Example")
    print("=" * 50)
    
    results = validator.validate_all_standards()
    
    print()
    print("Sample issues:")
    for issue in results['issues'][:10]:
        print(f"  {issue['type']}: {issue.get('table')} - {issue.get('count', 'N/A')}")
