"""
ACAD-GIS Toolkit Health Check

Tests all toolkit modules and database connectivity before running operations.
Run this before using the toolkit to ensure everything is configured correctly.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any

# Add tools to path
sys.path.append(str(Path(__file__).parent))

from db_utils import execute_query, get_entity_stats
from ingestion.standards_loader import StandardsLoader
from embeddings.embedding_generator import EmbeddingGenerator
from relationships.graph_builder import GraphBuilder
from validation.data_validator import DataValidator
from maintenance.db_maintenance import DatabaseMaintenance


class ToolkitHealthCheck:
    """Run comprehensive health checks on the toolkit."""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def _test(self, name: str, test_func) -> bool:
        """Run a single test and track results."""
        try:
            test_func()
            self.results.append(('PASS', name))
            self.passed += 1
            return True
        except Exception as e:
            self.results.append(('FAIL', name, str(e)))
            self.failed += 1
            return False
    
    def check_database_connection(self):
        """Test basic database connectivity."""
        result = execute_query("SELECT 1 as test")
        assert result[0]['test'] == 1, "Database query failed"
    
    def check_database_schema(self):
        """Verify core tables exist."""
        tables = [
            'standards_entities',
            'entity_embeddings',
            'entity_relationships',
            'embedding_models',
            'layer_standards',
            'block_definitions'
        ]
        
        for table in tables:
            result = execute_query(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
                (table,)
            )
            assert result[0]['exists'], f"Table {table} does not exist"
    
    def check_postgis_extension(self):
        """Verify PostGIS is installed."""
        result = execute_query(
            "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis')"
        )
        assert result[0]['exists'], "PostGIS extension not installed"
    
    def check_pgvector_extension(self):
        """Verify pgvector is installed."""
        result = execute_query(
            "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"
        )
        assert result[0]['exists'], "pgvector extension not installed"
    
    def check_helper_functions(self):
        """Verify helper functions exist."""
        functions = [
            'calculate_quality_score',
            'find_similar_entities',
            'find_related_entities',
            'hybrid_search'
        ]
        
        for func in functions:
            result = execute_query(
                "SELECT EXISTS (SELECT 1 FROM pg_proc WHERE proname = %s)",
                (func,)
            )
            assert result[0]['exists'], f"Function {func} does not exist"
    
    def check_materialized_views(self):
        """Verify materialized views exist."""
        views = [
            'mv_survey_points_enriched',
            'mv_entity_graph_summary',
            'mv_spatial_clusters'
        ]
        
        for view in views:
            result = execute_query(
                "SELECT EXISTS (SELECT 1 FROM pg_matviews WHERE matviewname = %s)",
                (view,)
            )
            assert result[0]['exists'], f"Materialized view {view} does not exist"
    
    def check_ingestion_module(self):
        """Test standards loader module."""
        loader = StandardsLoader(preview_mode=True)
        assert loader is not None, "Failed to initialize StandardsLoader"
        
        # Test with empty data (preview mode)
        stats = loader.load_layers([])
        assert 'previewed' in stats, "Preview mode not working"
    
    def check_embeddings_module(self):
        """Test embedding generator module (dry run)."""
        # Skip if no API key (that's okay for health check)
        if not os.environ.get('OPENAI_API_KEY'):
            print("      ℹ️  OPENAI_API_KEY not set (optional for testing)")
            return
        
        generator = EmbeddingGenerator(
            provider='openai',
            model='text-embedding-3-small',
            budget_cap=100.0,
            dry_run=True  # Don't make actual API calls
        )
        assert generator is not None, "Failed to initialize EmbeddingGenerator"
        assert generator.model_id is not None, "Model not registered"
        
        # Check cost summary
        summary = generator.get_cost_summary()
        assert 'budget_cap' in summary, "Cost tracking not working"
        assert summary['budget_cap'] == 100.0, "Budget cap not set correctly"
    
    def check_relationships_module(self):
        """Test graph builder module."""
        builder = GraphBuilder()
        assert builder is not None, "Failed to initialize GraphBuilder"
        assert hasattr(builder, 'stats'), "Stats tracking not initialized"
    
    def check_validation_module(self):
        """Test data validator module."""
        validator = DataValidator()
        assert validator is not None, "Failed to initialize DataValidator"
        
        # Test entity stats retrieval
        stats = get_entity_stats()
        assert 'total_entities' in stats, "Entity stats not working"
    
    def check_maintenance_module(self):
        """Test database maintenance module."""
        maintenance = DatabaseMaintenance()
        assert maintenance is not None, "Failed to initialize DatabaseMaintenance"
    
    def check_sample_data_roundtrip(self):
        """Test insert and query a sample entity."""
        # Insert test layer (idempotent)
        loader = StandardsLoader(preview_mode=False)
        test_data = [{
            'name': '_HEALTH_CHECK_TEST_',
            'description': 'Temporary test layer for health check',
            'color_name': 'White',
            'category': 'test'
        }]
        
        stats = loader.load_layers(test_data)
        assert stats['inserted'] + stats['updated'] > 0, "Failed to insert test data"
        
        # Query it back
        result = execute_query(
            "SELECT * FROM layer_standards WHERE name = %s",
            ('_HEALTH_CHECK_TEST_',)
        )
        assert len(result) > 0, "Failed to query test data"
        assert result[0]['name'] == '_HEALTH_CHECK_TEST_', "Data mismatch"
        
        # Clean up
        execute_query(
            "DELETE FROM layer_standards WHERE name = %s",
            ('_HEALTH_CHECK_TEST_',),
            fetch=False
        )
    
    def run_all_checks(self):
        """Run all health checks."""
        print("=" * 70)
        print("ACAD-GIS Toolkit Health Check")
        print("=" * 70)
        print()
        
        # Database checks
        print("Database Connectivity:")
        self._test("  Database connection", self.check_database_connection)
        self._test("  Core schema tables", self.check_database_schema)
        self._test("  PostGIS extension", self.check_postgis_extension)
        self._test("  pgvector extension", self.check_pgvector_extension)
        self._test("  Helper functions", self.check_helper_functions)
        self._test("  Materialized views", self.check_materialized_views)
        print()
        
        # Module checks
        print("Toolkit Modules:")
        self._test("  Ingestion module", self.check_ingestion_module)
        self._test("  Embeddings module", self.check_embeddings_module)
        self._test("  Relationships module", self.check_relationships_module)
        self._test("  Validation module", self.check_validation_module)
        self._test("  Maintenance module", self.check_maintenance_module)
        print()
        
        # Integration checks
        print("Integration Tests:")
        self._test("  Sample data round-trip", self.check_sample_data_roundtrip)
        print()
        
        # Print results
        print("=" * 70)
        print("Results:")
        print("=" * 70)
        
        for result in self.results:
            if result[0] == 'PASS':
                print(f"  ✓ {result[1]}")
            else:
                print(f"  ✗ {result[1]}")
                print(f"    Error: {result[2]}")
        
        print()
        print(f"Total: {self.passed} passed, {self.failed} failed")
        
        if self.failed == 0:
            print()
            print("🎉 All checks passed! Toolkit is ready to use.")
            print("=" * 70)
            return True
        else:
            print()
            print("⚠️  Some checks failed. Please fix the issues before using the toolkit.")
            print("=" * 70)
            return False


def main():
    """Run health check."""
    health_check = ToolkitHealthCheck()
    success = health_check.run_all_checks()
    
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
