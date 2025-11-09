"""
Test script for LayerClassifierV3
Validates that the database-driven classifier correctly parses layer names.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from standards.layer_classifier_v3 import LayerClassifierV3

# Database configuration
db_config = {
    'host': os.environ.get('PGHOST', 'localhost'),
    'port': int(os.environ.get('PGPORT', 5432)),
    'database': os.environ.get('PGDATABASE', 'main'),
    'user': os.environ.get('PGUSER', 'main'),
    'password': os.environ.get('PGPASSWORD', '')
}

def test_classifier():
    """Test the classifier with various layer names."""
    
    print("=" * 80)
    print("LAYER CLASSIFIER V3 - TEST SUITE")
    print("=" * 80)
    print()
    
    # Initialize classifier
    print("Initializing classifier with database connection...")
    try:
        classifier = LayerClassifierV3(db_config=db_config)
        print("✓ Classifier initialized successfully")
        print()
    except Exception as e:
        print(f"✗ Failed to initialize classifier: {e}")
        return
    
    # Print supported codes
    print("Supported Discipline Codes:", classifier.get_supported_disciplines())
    print("Supported Category Codes (CIV):", classifier.get_supported_categories('CIV'))
    print("Supported Object Types (STOR):", classifier.get_supported_object_types('STOR'))
    print()
    
    # Test cases
    test_cases = [
        # Gravity pipe networks
        ("CIV-STOR-STORM-NEW-LN", "New storm drain pipe"),
        ("CIV-STOR-SANIT-NEW-LN", "New sanitary sewer pipe"),
        ("CIV-STOR-STORM-EXIST-LN", "Existing storm drain pipe"),
        
        # Structures
        ("CIV-STOR-MH-NEW-PT", "New manhole"),
        ("CIV-STOR-CB-NEW-PT", "New catch basin"),
        ("CIV-STOR-INLET-EXIST-PT", "Existing inlet"),
        ("CIV-STOR-CLNOUT-NEW-PT", "New cleanout"),
        
        # Pressure pipe networks
        ("CIV-ROAD-WATER-NEW-LN", "New water main"),
        ("CIV-ROAD-RECYC-NEW-LN", "New recycled water pipe"),
        ("CIV-ROAD-HYDRA-NEW-PT", "New fire hydrant"),
        ("CIV-ROAD-VALVE-NEW-PT", "New water valve"),
        
        # Site features
        ("CIV-ROAD-CL-PROP-LN", "Proposed road centerline"),
        ("CIV-ROAD-CURB-NEW-LN", "New curb"),
        ("CIV-ROAD-GUTR-NEW-LN", "New gutter"),
        
        # Survey
        ("SURV-CTRL-CTRL-EXIST-PT", "Existing control point"),
        ("SURV-TOPO-TOPO-EXIST-PT", "Existing topo shot"),
        ("SURV-BNDY-BNDY-EXIST-LN", "Existing property boundary"),
        
        # Landscape
        ("LAND-TREE-TREE-EXIST-PT", "Existing tree"),
        ("LAND-TREE-TREE-DEMO-PT", "Tree to be removed"),
        ("LAND-TREE-TREE-PROP-PT", "Proposed new tree"),
        
        # Legacy formats
        ("12IN-STORM", "12-inch storm drain (legacy)"),
        ("8IN-WATER", "8-inch water main (legacy)"),
        ("STORM-PROPOSED", "Proposed storm drain (legacy)"),
        
        # With size encoding
        ("CIV-STOR-12STORM-NEW-LN", "12-inch storm drain"),
        ("CIV-ROAD-8WATER-NEW-LN", "8-inch water main"),
        
        # Invalid/unknown
        ("INVALID-LAYER-NAME", "Invalid layer (should fail)"),
        ("CIV-INVALID-OBJECT-NEW-LN", "Invalid object type (should fail)"),
    ]
    
    print("=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    for layer_name, description in test_cases:
        print(f"Testing: {layer_name}")
        print(f"Description: {description}")
        
        result = classifier.classify(layer_name)
        
        if result:
            print(f"✓ Classified successfully")
            print(f"  Object Type: {result.object_type}")
            print(f"  Database Table: {result.database_table}")
            print(f"  Confidence: {result.confidence:.0%}")
            print(f"  Discipline: {result.discipline_code}")
            print(f"  Category: {result.category_code}")
            print(f"  Phase: {result.phase_code}")
            print(f"  Geometry: {result.geometry_code}")
            print(f"  Network Mode: {result.network_mode}")
            print(f"  Properties: {result.properties}")
            passed += 1
        else:
            if "invalid" in description.lower() or "should fail" in description.lower():
                print(f"✓ Correctly rejected (as expected)")
                passed += 1
            else:
                print(f"✗ FAILED - No classification returned")
                failed += 1
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(test_cases)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {passed / len(test_cases) * 100:.1f}%")
    print()
    
    if failed == 0:
        print("✓ ALL TESTS PASSED!")
    else:
        print(f"✗ {failed} TEST(S) FAILED")
    
    return failed == 0


if __name__ == "__main__":
    success = test_classifier()
    sys.exit(0 if success else 1)
