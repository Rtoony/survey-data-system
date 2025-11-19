"""
Unit tests for GKGClusteringTool
Tests cross-project asset clustering and similarity matching based on physical attributes.
"""

import unittest
import logging
from unittest.mock import patch
from services.gkg_clustering_tool import (
    GKGClusteringTool,
    MOCK_GKG_ENTITIES
)


class TestGKGClusteringTool(unittest.TestCase):
    """Test suite for GKGClusteringTool asset clustering functionality."""

    def setUp(self):
        """Initialize the service before each test."""
        self.service = GKGClusteringTool()

    def test_service_initialization(self):
        """Test that the service initializes correctly."""
        self.assertIsNotNone(self.service)
        self.assertIsInstance(self.service, GKGClusteringTool)

    def test_find_similar_assets_exact_match(self):
        """Test finding assets with exact attribute matches."""
        # Target: 48-inch CONCRETE SDMH assets
        target_attributes = {"SIZE": "48IN", "MATERIAL": "CONCRETE"}

        results = self.service.find_similar_assets("SDMH", target_attributes)

        # Should find 3 matches from MOCK_GKG_ENTITIES (entity_id: 1001, 2001, 3002)
        self.assertEqual(len(results), 3)

        # Verify all results match the criteria
        for result in results:
            self.assertEqual(result["feature_code"], "SDMH")
            self.assertEqual(result["SIZE"], "48IN")
            self.assertEqual(result["MATERIAL"], "CONCRETE")

    def test_find_similar_assets_case_insensitive_feature_code(self):
        """Test that feature code matching is case-insensitive."""
        target_attributes = {"SIZE": "48IN", "MATERIAL": "CONCRETE"}

        # Test with lowercase
        results_lower = self.service.find_similar_assets("sdmh", target_attributes)

        # Test with uppercase
        results_upper = self.service.find_similar_assets("SDMH", target_attributes)

        # Test with mixed case
        results_mixed = self.service.find_similar_assets("SdMh", target_attributes)

        # All should return the same results
        self.assertEqual(len(results_lower), 3)
        self.assertEqual(len(results_upper), 3)
        self.assertEqual(len(results_mixed), 3)

    def test_find_similar_assets_with_limit(self):
        """Test that the limit parameter correctly restricts results."""
        target_attributes = {"SIZE": "48IN", "MATERIAL": "CONCRETE"}

        # Request only 2 results
        results = self.service.find_similar_assets("SDMH", target_attributes, limit=2)

        self.assertEqual(len(results), 2)

        # Request only 1 result
        results_single = self.service.find_similar_assets("SDMH", target_attributes, limit=1)

        self.assertEqual(len(results_single), 1)

    def test_find_similar_assets_no_matches(self):
        """Test behavior when no assets match the criteria."""
        # Non-existent combination
        target_attributes = {"SIZE": "96IN", "MATERIAL": "GOLD"}

        results = self.service.find_similar_assets("SDMH", target_attributes)

        self.assertEqual(len(results), 0)

    def test_find_similar_assets_partial_attribute_mismatch(self):
        """Test that partial matches are excluded (AND logic)."""
        # This should NOT match entity_id 4001 (SDMH, 48IN, PVC)
        # because MATERIAL doesn't match
        target_attributes = {"SIZE": "48IN", "MATERIAL": "CONCRETE"}

        results = self.service.find_similar_assets("SDMH", target_attributes)

        # Verify entity_id 4001 is NOT in results
        entity_ids = [r["entity_id"] for r in results]
        self.assertNotIn(4001, entity_ids)

    def test_find_similar_assets_wrong_feature_code(self):
        """Test that results are filtered by feature code."""
        target_attributes = {"SIZE": "12IN", "MATERIAL": "DI"}

        # Search for WV (should find entity_id 3001)
        results_wv = self.service.find_similar_assets("WV", target_attributes)
        self.assertEqual(len(results_wv), 1)
        self.assertEqual(results_wv[0]["entity_id"], 3001)

        # Search for SDMH with same attributes (should find none)
        results_sdmh = self.service.find_similar_assets("SDMH", target_attributes)
        self.assertEqual(len(results_sdmh), 0)

    def test_find_similar_assets_enrichment(self):
        """Test that results are enriched with additional metadata."""
        target_attributes = {"SIZE": "48IN", "MATERIAL": "CONCRETE"}

        results = self.service.find_similar_assets("SDMH", target_attributes, limit=1)

        self.assertEqual(len(results), 1)
        result = results[0]

        # Verify enriched fields are added
        self.assertIn("last_inspection_date", result)
        self.assertIn("gkg_relationships_count", result)

        # Verify enriched field values
        self.assertEqual(result["last_inspection_date"], "2025-01-15")
        self.assertIsInstance(result["gkg_relationships_count"], int)
        self.assertGreaterEqual(result["gkg_relationships_count"], 3)
        self.assertLessEqual(result["gkg_relationships_count"], 8)

    def test_find_similar_assets_preserves_original_attributes(self):
        """Test that original entity attributes are preserved in results."""
        target_attributes = {"SIZE": "48IN", "MATERIAL": "CONCRETE"}

        results = self.service.find_similar_assets("SDMH", target_attributes)

        # Check first result (entity_id 1001)
        first_result = results[0]

        # Verify original fields are intact
        self.assertEqual(first_result["entity_id"], 1001)
        self.assertEqual(first_result["project_id"], 1)
        self.assertEqual(first_result["feature_code"], "SDMH")
        self.assertEqual(first_result["status"], "Good")

    def test_find_similar_assets_with_empty_attributes(self):
        """Test behavior with empty attribute dictionary."""
        target_attributes = {}

        # Should match all entities with the feature code
        results = self.service.find_similar_assets("SDMH", target_attributes)

        # From MOCK_GKG_ENTITIES: 1001, 1002, 2001, 3002, 4001 = 5 SDMH entities
        self.assertEqual(len(results), 5)

        for result in results:
            self.assertEqual(result["feature_code"], "SDMH")

    def test_find_similar_assets_with_single_attribute(self):
        """Test matching with only one attribute."""
        target_attributes = {"MATERIAL": "CONCRETE"}

        results = self.service.find_similar_assets("SDMH", target_attributes)

        # Should find all SDMH entities with CONCRETE material
        # entity_id: 1001, 1002, 2001, 3002 = 4 entities
        self.assertEqual(len(results), 4)

        for result in results:
            self.assertEqual(result["MATERIAL"], "CONCRETE")

    def test_find_similar_assets_cross_project_coverage(self):
        """Test that results span multiple projects."""
        target_attributes = {"SIZE": "48IN", "MATERIAL": "CONCRETE"}

        results = self.service.find_similar_assets("SDMH", target_attributes)

        # Extract unique project IDs
        project_ids = {r["project_id"] for r in results}

        # Should find matches from projects 1, 2, and 3
        self.assertGreaterEqual(len(project_ids), 2)
        self.assertIn(1, project_ids)
        self.assertIn(2, project_ids)
        self.assertIn(3, project_ids)

    def test_find_similar_assets_status_preservation(self):
        """Test that entity status values are preserved in results."""
        target_attributes = {"SIZE": "48IN", "MATERIAL": "CONCRETE"}

        results = self.service.find_similar_assets("SDMH", target_attributes)

        # Find the flagged entity (entity_id 2001)
        flagged_entity = next((r for r in results if r["entity_id"] == 2001), None)

        self.assertIsNotNone(flagged_entity)
        self.assertEqual(flagged_entity["status"], "FLAGGED")

    def test_find_similar_assets_default_limit(self):
        """Test that default limit is applied correctly."""
        # Create attributes that would match many entities if limit wasn't applied
        target_attributes = {}  # Match all SDMH

        # Default limit is 10
        results = self.service.find_similar_assets("SDMH", target_attributes)

        # Should not exceed default limit
        self.assertLessEqual(len(results), 10)

    def test_find_similar_assets_logging(self):
        """Test that find_similar_assets logs appropriately."""
        logging.disable(logging.NOTSET)

        target_attributes = {"SIZE": "48IN", "MATERIAL": "CONCRETE"}

        with self.assertLogs('services.gkg_clustering_tool', level='INFO') as cm:
            self.service.find_similar_assets("SDMH", target_attributes)

        # Verify search initiation log
        self.assertTrue(
            any("Searching GKG for similar assets" in log for log in cm.output),
            "Expected search initiation log not found"
        )

        # Verify completion log
        self.assertTrue(
            any("Clustering complete" in log for log in cm.output),
            "Expected completion log not found"
        )

    def test_service_initialization_logging(self):
        """Test that service initialization logs appropriately."""
        logging.disable(logging.NOTSET)

        with self.assertLogs('services.gkg_clustering_tool', level='INFO') as cm:
            # Create a new instance within the logging context
            test_service = GKGClusteringTool()

        # Verify initialization log
        self.assertTrue(
            any("GKGClusteringTool initialized" in log for log in cm.output),
            "Expected initialization log not found"
        )
        self.assertIsNotNone(test_service)

    def test_find_similar_assets_result_immutability(self):
        """Test that modifying results doesn't affect the original mock data."""
        target_attributes = {"SIZE": "48IN", "MATERIAL": "CONCRETE"}

        results = self.service.find_similar_assets("SDMH", target_attributes, limit=1)

        # Modify the result
        original_status = results[0]["status"]
        results[0]["status"] = "MODIFIED"

        # Re-query
        results_2 = self.service.find_similar_assets("SDMH", target_attributes, limit=1)

        # Original data should be unchanged
        self.assertEqual(results_2[0]["status"], original_status)


class TestMockGKGEntities(unittest.TestCase):
    """Test suite for MOCK_GKG_ENTITIES data structure."""

    def test_mock_data_structure(self):
        """Test that mock data has the expected structure."""
        self.assertIsInstance(MOCK_GKG_ENTITIES, list)
        self.assertGreater(len(MOCK_GKG_ENTITIES), 0)

        # Verify required fields in each entity
        required_fields = ["entity_id", "project_id", "feature_code", "SIZE", "MATERIAL", "status"]

        for entity in MOCK_GKG_ENTITIES:
            for field in required_fields:
                self.assertIn(field, entity, f"Missing field: {field}")

    def test_mock_data_entity_count(self):
        """Test that mock data contains the expected number of entities."""
        self.assertEqual(len(MOCK_GKG_ENTITIES), 6)

    def test_mock_data_feature_codes(self):
        """Test that mock data contains expected feature codes."""
        feature_codes = {e["feature_code"] for e in MOCK_GKG_ENTITIES}

        self.assertIn("SDMH", feature_codes)
        self.assertIn("WV", feature_codes)

    def test_mock_data_project_distribution(self):
        """Test that mock data spans multiple projects."""
        project_ids = {e["project_id"] for e in MOCK_GKG_ENTITIES}

        # Should have entities from at least 4 projects
        self.assertGreaterEqual(len(project_ids), 4)


class TestGKGClusteringToolIntegration(unittest.TestCase):
    """Integration tests for GKGClusteringTool with various scenarios."""

    def test_cross_project_anomaly_detection_workflow(self):
        """Test complete workflow for detecting anomalies across projects."""
        service = GKGClusteringTool()

        # Step 1: Find all 48IN CONCRETE SDMH assets
        target_attributes = {"SIZE": "48IN", "MATERIAL": "CONCRETE"}
        cluster = service.find_similar_assets("SDMH", target_attributes)

        # Step 2: Identify anomalies (flagged status)
        flagged_assets = [asset for asset in cluster if asset["status"] == "FLAGGED"]

        # Step 3: Verify detection
        self.assertGreater(len(cluster), 0)
        self.assertGreater(len(flagged_assets), 0)

        # Verify flagged asset details
        self.assertEqual(flagged_assets[0]["entity_id"], 2001)
        self.assertEqual(flagged_assets[0]["project_id"], 2)

    def test_material_substitution_analysis_workflow(self):
        """Test workflow for analyzing material variations across projects."""
        service = GKGClusteringTool()

        # Find all 48IN SDMH regardless of material
        all_48in_sdmh = service.find_similar_assets("SDMH", {"SIZE": "48IN"})

        # Group by material
        materials = {}
        for asset in all_48in_sdmh:
            material = asset["MATERIAL"]
            if material not in materials:
                materials[material] = []
            materials[material].append(asset)

        # Verify material diversity
        self.assertIn("CONCRETE", materials)
        self.assertIn("PVC", materials)

        # Verify counts
        self.assertEqual(len(materials["CONCRETE"]), 3)  # entity_id: 1001, 2001, 3002
        self.assertEqual(len(materials["PVC"]), 1)  # entity_id: 4001

    def test_size_distribution_analysis_workflow(self):
        """Test workflow for analyzing size variations within a feature type."""
        service = GKGClusteringTool()

        # Find all SDMH with CONCRETE material
        all_concrete_sdmh = service.find_similar_assets("SDMH", {"MATERIAL": "CONCRETE"})

        # Group by size
        sizes = {}
        for asset in all_concrete_sdmh:
            size = asset["SIZE"]
            if size not in sizes:
                sizes[size] = []
            sizes[size].append(asset)

        # Verify size diversity
        self.assertIn("48IN", sizes)
        self.assertIn("60IN", sizes)

        # Verify the most common size
        most_common_size = max(sizes.items(), key=lambda x: len(x[1]))[0]
        self.assertEqual(most_common_size, "48IN")

    @patch('services.gkg_clustering_tool.MOCK_GKG_ENTITIES')
    def test_service_with_custom_mock_data(self, mock_entities):
        """Test service behavior with custom injected data."""
        # Setup custom mock data
        mock_entities.__iter__ = lambda x: iter([
            {"entity_id": 9001, "project_id": 99, "feature_code": "TEST",
             "SIZE": "24IN", "MATERIAL": "STEEL", "status": "New"},
            {"entity_id": 9002, "project_id": 99, "feature_code": "TEST",
             "SIZE": "24IN", "MATERIAL": "STEEL", "status": "New"},
        ])

        service = GKGClusteringTool()
        results = service.find_similar_assets("TEST", {"SIZE": "24IN", "MATERIAL": "STEEL"})

        # Verify custom data is used
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["entity_id"], 9001)


if __name__ == '__main__':
    unittest.main()
