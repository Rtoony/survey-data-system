"""
Database Maintenance Module

Refresh materialized views, recompute quality scores,
run VACUUM, update statistics, and monitor database health.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
import time

sys.path.append(str(Path(__file__).parent.parent))

from db_utils import execute_query, get_table_stats, get_entity_stats, refresh_materialized_views


class DatabaseMaintenance:
    """Manage database maintenance tasks."""
    
    def __init__(self):
        self.maintenance_log = []
    
    def _log(self, message: str):
        """Log maintenance action."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.maintenance_log.append(log_entry)
        print(log_entry)
    
    def refresh_all_materialized_views(self) -> Dict[str, Any]:
        """Refresh all materialized views with timing."""
        self._log("Starting materialized view refresh...")
        start = time.time()
        
        try:
            refresh_materialized_views()
            duration = time.time() - start
            self._log(f"Materialized views refreshed successfully ({duration:.2f}s)")
            return {'success': True, 'duration': duration}
        except Exception as e:
            self._log(f"ERROR refreshing views: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def recompute_all_quality_scores(self) -> Dict[str, Any]:
        """Recompute quality scores for all entities."""
        self._log("Recomputing quality scores...")
        start = time.time()
        
        query = """
            UPDATE standards_entities
            SET quality_score = compute_quality_score(
                CASE
                    WHEN canonical_name IS NOT NULL AND canonical_name != '' THEN 10
                    ELSE 5
                END,
                10,
                EXISTS(SELECT 1 FROM entity_embeddings WHERE entity_id = standards_entities.entity_id AND is_current = true),
                EXISTS(SELECT 1 FROM entity_relationships WHERE source_entity_id = standards_entities.entity_id OR target_entity_id = standards_entities.entity_id)
            ),
            updated_at = CURRENT_TIMESTAMP
        """
        
        try:
            execute_query(query, fetch=False)
            duration = time.time() - start
            
            # Get updated stats
            stats_query = """
                SELECT 
                    COUNT(*) as total,
                    AVG(quality_score) as avg_quality,
                    COUNT(CASE WHEN quality_score >= 0.8 THEN 1 END) as high_quality,
                    COUNT(CASE WHEN quality_score < 0.5 THEN 1 END) as low_quality
                FROM standards_entities
            """
            result = execute_query(stats_query)
            stats = result[0] if result else {}
            
            self._log(f"Quality scores recomputed ({duration:.2f}s)")
            self._log(f"  Total entities: {stats.get('total', 0)}")
            self._log(f"  Avg quality: {float(stats.get('avg_quality', 0)):.3f}")
            self._log(f"  High quality (>=0.8): {stats.get('high_quality', 0)}")
            self._log(f"  Low quality (<0.5): {stats.get('low_quality', 0)}")
            
            return {
                'success': True,
                'duration': duration,
                'stats': stats
            }
        except Exception as e:
            self._log(f"ERROR recomputing quality scores: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def vacuum_analyze(self, full: bool = False) -> Dict[str, Any]:
        """Run VACUUM and ANALYZE on database."""
        vacuum_type = "FULL" if full else "ANALYZE"
        self._log(f"Running VACUUM {vacuum_type}...")
        start = time.time()
        
        try:
            if full:
                execute_query("VACUUM FULL ANALYZE", fetch=False)
            else:
                execute_query("VACUUM ANALYZE", fetch=False)
            
            duration = time.time() - start
            self._log(f"VACUUM {vacuum_type} completed ({duration:.2f}s)")
            return {'success': True, 'duration': duration}
        except Exception as e:
            self._log(f"ERROR during VACUUM: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def update_table_statistics(self) -> Dict[str, Any]:
        """Update PostgreSQL table statistics."""
        self._log("Updating table statistics...")
        
        query = """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
        """
        
        try:
            result = execute_query(query)
            tables = [row['tablename'] for row in result] if result else []
            
            for table in tables:
                try:
                    execute_query(f"ANALYZE {table}", fetch=False)
                except Exception:
                    pass
            
            self._log(f"Statistics updated for {len(tables)} tables")
            return {'success': True, 'tables_analyzed': len(tables)}
        except Exception as e:
            self._log(f"ERROR updating statistics: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def check_index_health(self) -> Dict[str, Any]:
        """Check index usage and bloat."""
        self._log("Checking index health...")
        
        # Check for unused indexes
        unused_query = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
              AND idx_scan = 0
            ORDER BY tablename, indexname
        """
        
        # Check index sizes
        size_query = """
            SELECT 
                tablename,
                indexname,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            ORDER BY pg_relation_size(indexrelid) DESC
            LIMIT 20
        """
        
        try:
            unused_result = execute_query(unused_query)
            size_result = execute_query(size_query)
            
            unused_count = len(unused_result) if unused_result else 0
            
            self._log(f"  Unused indexes: {unused_count}")
            if unused_count > 0:
                self._log("  Top unused indexes:")
                for idx in (unused_result or [])[:5]:
                    self._log(f"    - {idx['tablename']}.{idx['indexname']}")
            
            self._log("  Largest indexes:")
            for idx in (size_result or [])[:5]:
                self._log(f"    - {idx['tablename']}.{idx['indexname']}: {idx['index_size']}")
            
            return {
                'success': True,
                'unused_indexes': unused_count,
                'unused': unused_result or [],
                'largest': size_result or []
            }
        except Exception as e:
            self._log(f"ERROR checking index health: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_database_size(self) -> Dict[str, Any]:
        """Get database and table sizes."""
        self._log("Checking database sizes...")
        
        # Total database size
        db_query = """
            SELECT pg_size_pretty(pg_database_size(current_database())) as size
        """
        
        # Largest tables
        table_query = """
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 20
        """
        
        try:
            db_result = execute_query(db_query)
            table_result = execute_query(table_query)
            
            db_size = db_result[0]['size'] if db_result else 'Unknown'
            
            self._log(f"  Database size: {db_size}")
            self._log("  Largest tables:")
            for table in (table_result or [])[:10]:
                self._log(f"    - {table['tablename']}: {table['total_size']} (table: {table['table_size']}, indexes: {table['index_size']})")
            
            return {
                'success': True,
                'database_size': db_size,
                'tables': table_result or []
            }
        except Exception as e:
            self._log(f"ERROR checking database size: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def run_full_maintenance(self, include_vacuum_full: bool = False) -> Dict[str, Any]:
        """Run complete maintenance routine."""
        print()
        print("=" * 70)
        print("ACAD-GIS Database Maintenance")
        print("=" * 70)
        print()
        
        results = {}
        
        # 1. Database health check
        self._log("1. Database Health Check")
        results['size'] = self.get_database_size()
        
        print()
        
        # 2. Table statistics
        self._log("2. Table Statistics")
        table_stats = get_table_stats()
        self._log(f"  Tables with data: {len(table_stats)}")
        
        print()
        
        # 3. Entity statistics
        self._log("3. Entity Statistics")
        entity_stats = get_entity_stats()
        self._log(f"  Total entities: {entity_stats.get('total_entities', 0)}")
        self._log(f"  Total embeddings: {entity_stats.get('embeddings', {}).get('total', 0)}")
        self._log(f"  Total relationships: {entity_stats.get('relationships', 0)}")
        
        print()
        
        # 4. Recompute quality scores
        self._log("4. Quality Score Recalculation")
        results['quality'] = self.recompute_all_quality_scores()
        
        print()
        
        # 5. Refresh materialized views
        self._log("5. Materialized Views")
        results['views'] = self.refresh_all_materialized_views()
        
        print()
        
        # 6. Update statistics
        self._log("6. Table Statistics Update")
        results['stats'] = self.update_table_statistics()
        
        print()
        
        # 7. VACUUM
        self._log("7. Database Vacuum")
        results['vacuum'] = self.vacuum_analyze(full=include_vacuum_full)
        
        print()
        
        # 8. Index health
        self._log("8. Index Health Check")
        results['indexes'] = self.check_index_health()
        
        print()
        print("=" * 70)
        print("Maintenance Complete!")
        print("=" * 70)
        
        return results


if __name__ == '__main__':
    # Example usage
    maintenance = DatabaseMaintenance()
    
    # Run full maintenance
    results = maintenance.run_full_maintenance(include_vacuum_full=False)
