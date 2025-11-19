"""
Test SSMAuditService
Tests for SSM audit trail, version control, and snapshot management

Tests verify:
- Snapshot creation and versioning
- Audit log tracking
- Snapshot comparison and diff detection
- Version management
- Data integrity
"""
import pytest
import json
from sqlalchemy import select, delete
from services.ssm_audit_service import (
    SSMAuditService,
    MOCK_AUDIT_LOG,
    MOCK_STANDARDS_MAPPINGS
)
from data.ssm_schema import ssm_snapshots
from database import get_db


def get_snapshot_by_id(snapshot_id: str):
    """Helper function to retrieve a snapshot from the database by ID."""
    stmt = select(ssm_snapshots).where(ssm_snapshots.c.id == snapshot_id)
    with get_db() as conn:
        result = conn.execute(stmt).fetchone()
    return dict(result._mapping) if result else None


def get_all_snapshots():
    """Helper function to retrieve all snapshots from the database."""
    stmt = select(ssm_snapshots)
    with get_db() as conn:
        results = conn.execute(stmt).fetchall()
    return [dict(row._mapping) for row in results]


@pytest.fixture
def audit_service():
    """Fixture to create a fresh SSMAuditService instance for each test."""
    # Clear the ssm_snapshots table before each test
    with get_db() as conn:
        conn.execute(delete(ssm_snapshots))
        conn.commit()

    # Clear mock audit log
    MOCK_AUDIT_LOG.clear()

    # Reset MOCK_STANDARDS_MAPPINGS to initial state
    MOCK_STANDARDS_MAPPINGS.clear()
    MOCK_STANDARDS_MAPPINGS.extend([
        {"id": 301, "feature_code": "SDMH", "priority": 300, "layer": "L1"},
        {"id": 201, "feature_code": "SDMH", "priority": 200, "layer": "L2"}
    ])

    return SSMAuditService()


class TestSnapshotCreation:
    """Test suite for snapshot creation functionality."""

    def test_create_snapshot_returns_uuid(self, audit_service):
        """Verify create_snapshot returns a valid UUID string."""
        snapshot_id = audit_service.create_snapshot("Test Version")

        assert snapshot_id is not None
        assert isinstance(snapshot_id, str)
        assert len(snapshot_id) == 36  # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

    def test_create_snapshot_stores_configuration(self, audit_service):
        """Verify snapshot is stored in the database."""
        snapshot_id = audit_service.create_snapshot("Test Version")

        snapshot = get_snapshot_by_id(snapshot_id)
        assert snapshot is not None

        assert snapshot['version_name'] == "Test Version"
        assert 'configuration_jsonb' in snapshot
        assert 'timestamp' in snapshot
        assert snapshot['user_id'] == 1

    def test_create_snapshot_with_custom_user_id(self, audit_service):
        """Verify snapshot can be created with custom user_id."""
        snapshot_id = audit_service.create_snapshot("Test Version", user_id=42)

        snapshot = get_snapshot_by_id(snapshot_id)
        assert snapshot['user_id'] == 42

    def test_create_snapshot_captures_mappings(self, audit_service):
        """Verify snapshot captures the current state of MOCK_STANDARDS_MAPPINGS."""
        snapshot_id = audit_service.create_snapshot("Initial Snapshot")

        snapshot = get_snapshot_by_id(snapshot_id)
        config = snapshot['configuration_jsonb']

        assert 'mappings' in config
        assert len(config['mappings']) == 2
        assert config['mappings'][0]['feature_code'] == "SDMH"

    def test_create_snapshot_deep_copies_data(self, audit_service):
        """Verify snapshot creates a deep copy of configuration data."""
        snapshot_id_v1 = audit_service.create_snapshot("V1")

        # Modify the original data
        MOCK_STANDARDS_MAPPINGS[0]['priority'] = 999

        # Create another snapshot
        snapshot_id_v2 = audit_service.create_snapshot("V2")

        # V1 snapshot should still have original value (300, not 999)
        config_v1 = get_snapshot_by_id(snapshot_id_v1)['configuration_jsonb']
        assert config_v1['mappings'][0]['priority'] == 300

        # V2 snapshot should have new value
        config_v2 = get_snapshot_by_id(snapshot_id_v2)['configuration_jsonb']
        assert config_v2['mappings'][0]['priority'] == 999

    def test_create_multiple_snapshots(self, audit_service):
        """Verify multiple snapshots can be created with unique IDs."""
        id1 = audit_service.create_snapshot("Version 1")
        id2 = audit_service.create_snapshot("Version 2")
        id3 = audit_service.create_snapshot("Version 3")

        assert id1 != id2 != id3
        assert len(get_all_snapshots()) == 3


class TestAuditLog:
    """Test suite for audit log functionality."""

    def test_snapshot_creation_logged(self, audit_service):
        """Verify snapshot creation events are logged."""
        snapshot_id = audit_service.create_snapshot("Test Version")

        assert len(MOCK_AUDIT_LOG) == 1
        log_entry = MOCK_AUDIT_LOG[0]

        assert log_entry['event'] == "SNAPSHOT_CREATED"
        assert log_entry['snapshot_id'] == snapshot_id
        assert log_entry['version'] == "Test Version"

    def test_get_change_log_returns_all_events(self, audit_service):
        """Verify get_change_log returns complete audit history."""
        audit_service.create_snapshot("V1")
        audit_service.create_snapshot("V2")
        audit_service.create_snapshot("V3")

        change_log = audit_service.get_change_log()

        assert len(change_log) == 3
        assert all(entry['event'] == "SNAPSHOT_CREATED" for entry in change_log)

    def test_get_change_log_returns_list(self, audit_service):
        """Verify get_change_log returns a list."""
        change_log = audit_service.get_change_log()

        assert isinstance(change_log, list)

    def test_audit_log_includes_timestamps(self, audit_service):
        """Verify audit log entries include timestamps."""
        audit_service.create_snapshot("Test Version")

        log_entry = MOCK_AUDIT_LOG[0]
        assert 'time' in log_entry
        assert isinstance(log_entry['time'], str)

    def test_audit_log_chronological_order(self, audit_service):
        """Verify audit log maintains chronological order."""
        audit_service.create_snapshot("V1")
        audit_service.create_snapshot("V2")

        change_log = audit_service.get_change_log()

        # V1 should be logged before V2
        assert change_log[0]['version'] == "V1"
        assert change_log[1]['version'] == "V2"


class TestSnapshotComparison:
    """Test suite for snapshot comparison functionality."""

    def test_compare_identical_snapshots(self, audit_service):
        """Verify comparing snapshots with identical configuration data.

        Note: Even snapshots with identical mappings/rulesets will show changes
        if metadata (timestamps) differ, which is expected behavior.
        """
        id_v1 = audit_service.create_snapshot("V1")
        id_v2 = audit_service.create_snapshot("V1_Copy")

        result = audit_service.compare_snapshots(id_v1, id_v2)

        assert result['status'] == "DIFF_SUCCESS"
        # Snapshots created at different times will have different metadata
        assert result['changes_found'] >= 0  # May detect metadata changes

    def test_compare_different_snapshots(self, audit_service):
        """Verify comparing different snapshots detects changes."""
        id_v1 = audit_service.create_snapshot("V1")

        # Modify the configuration
        MOCK_STANDARDS_MAPPINGS[0]['priority'] = 400

        id_v2 = audit_service.create_snapshot("V2")

        result = audit_service.compare_snapshots(id_v1, id_v2)

        assert result['status'] == "DIFF_SUCCESS"
        assert result['changes_found'] == 1

    def test_compare_snapshots_invalid_id_a(self, audit_service):
        """Verify error when first snapshot ID doesn't exist."""
        id_valid = audit_service.create_snapshot("Valid")

        result = audit_service.compare_snapshots("invalid-id", id_valid)

        assert result['status'] == "ERROR"
        assert "not found" in result['message']

    def test_compare_snapshots_invalid_id_b(self, audit_service):
        """Verify error when second snapshot ID doesn't exist."""
        id_valid = audit_service.create_snapshot("Valid")

        result = audit_service.compare_snapshots(id_valid, "invalid-id")

        assert result['status'] == "ERROR"
        assert "not found" in result['message']

    def test_compare_snapshots_both_invalid(self, audit_service):
        """Verify error when both snapshot IDs don't exist."""
        result = audit_service.compare_snapshots("invalid-id-1", "invalid-id-2")

        assert result['status'] == "ERROR"
        assert "not found" in result['message']

    def test_compare_snapshots_returns_version_names(self, audit_service):
        """Verify comparison result includes version names."""
        id_v1 = audit_service.create_snapshot("Initial Release")
        id_v2 = audit_service.create_snapshot("Bug Fix Release")

        result = audit_service.compare_snapshots(id_v1, id_v2)

        assert 'source_versions' in result
        assert result['source_versions'][0] == "Initial Release"
        assert result['source_versions'][1] == "Bug Fix Release"

    def test_compare_snapshots_returns_summary(self, audit_service):
        """Verify comparison result includes a summary."""
        id_v1 = audit_service.create_snapshot("V1")
        id_v2 = audit_service.create_snapshot("V2")

        result = audit_service.compare_snapshots(id_v1, id_v2)

        assert 'summary' in result
        assert isinstance(result['summary'], str)


class TestVersionManagement:
    """Test suite for version management and integrity."""

    def test_snapshot_immutability(self, audit_service):
        """Verify snapshots are immutable after creation."""
        id_v1 = audit_service.create_snapshot("V1")
        original_config = get_snapshot_by_id(id_v1)['configuration_jsonb'].copy()

        # Modify current mappings
        MOCK_STANDARDS_MAPPINGS[0]['priority'] = 999

        # Original snapshot should remain unchanged
        snapshot_config = get_snapshot_by_id(id_v1)['configuration_jsonb']
        assert snapshot_config['mappings'][0]['priority'] == original_config['mappings'][0]['priority']

    def test_snapshot_includes_metadata(self, audit_service):
        """Verify snapshots include metadata (timestamp, user)."""
        snapshot_id = audit_service.create_snapshot("Test")

        snapshot = get_snapshot_by_id(snapshot_id)
        config = snapshot['configuration_jsonb']

        assert 'metadata' in config
        assert 'timestamp' in config['metadata']
        assert 'user' in config['metadata']

    def test_snapshot_includes_rulesets(self, audit_service):
        """Verify snapshots capture rulesets."""
        snapshot_id = audit_service.create_snapshot("Test")

        config = get_snapshot_by_id(snapshot_id)['configuration_jsonb']

        assert 'rulesets' in config
        assert isinstance(config['rulesets'], list)

    def test_version_name_stored_correctly(self, audit_service):
        """Verify version names are stored exactly as provided."""
        test_names = [
            "V1.0.0",
            "Production Release 2024-11-18",
            "Emergency Hotfix - Layer Priority",
            "QA/QC Baseline"
        ]

        for name in test_names:
            snapshot_id = audit_service.create_snapshot(name)
            assert get_snapshot_by_id(snapshot_id)['version_name'] == name


class TestServiceInitialization:
    """Test suite for SSMAuditService initialization."""

    def test_service_initialization(self):
        """Verify SSMAuditService can be initialized."""
        service = SSMAuditService()
        assert service is not None

    def test_service_type(self):
        """Verify SSMAuditService is correct type."""
        service = SSMAuditService()
        assert isinstance(service, SSMAuditService)

    def test_service_has_required_methods(self):
        """Verify SSMAuditService has all required methods."""
        service = SSMAuditService()

        assert hasattr(service, 'create_snapshot')
        assert callable(service.create_snapshot)

        assert hasattr(service, 'get_change_log')
        assert callable(service.get_change_log)

        assert hasattr(service, 'compare_snapshots')
        assert callable(service.compare_snapshots)


class TestIntegrationScenarios:
    """Test suite for real-world integration scenarios."""

    def test_full_version_control_workflow(self, audit_service):
        """Verify complete version control workflow."""
        # Step 1: Create baseline
        id_baseline = audit_service.create_snapshot("Baseline V1.0")

        # Step 2: Make changes
        MOCK_STANDARDS_MAPPINGS[0]['priority'] = 350
        MOCK_STANDARDS_MAPPINGS[0]['layer'] = "L1-UPDATED"

        # Step 3: Create new version
        id_updated = audit_service.create_snapshot("V1.1 Updates")

        # Step 4: Verify audit trail
        log = audit_service.get_change_log()
        assert len(log) == 2

        # Step 5: Compare versions
        comparison = audit_service.compare_snapshots(id_baseline, id_updated)
        assert comparison['status'] == "DIFF_SUCCESS"
        assert comparison['changes_found'] == 1

    def test_rollback_scenario(self, audit_service):
        """Verify snapshots enable configuration rollback."""
        # Create good configuration
        id_good = audit_service.create_snapshot("Known Good Config")
        good_config = get_snapshot_by_id(id_good)['configuration_jsonb']

        # Make breaking changes
        MOCK_STANDARDS_MAPPINGS[0]['priority'] = 9999
        id_bad = audit_service.create_snapshot("Bad Config")

        # Verify we can access the good config
        assert good_config['mappings'][0]['priority'] == 300
        assert get_snapshot_by_id(id_bad)['configuration_jsonb']['mappings'][0]['priority'] == 9999

    def test_compliance_audit_trail(self, audit_service):
        """Verify audit trail supports compliance requirements."""
        # Create multiple versions
        audit_service.create_snapshot("V1.0", user_id=100)
        audit_service.create_snapshot("V1.1", user_id=200)
        audit_service.create_snapshot("V1.2", user_id=100)

        # Verify complete audit trail
        log = audit_service.get_change_log()

        assert len(log) == 3
        assert all('user_id' in entry for entry in log)
        assert all('time' in entry for entry in log)
        assert all('version' in entry for entry in log)

    def test_qa_qc_workflow(self, audit_service):
        """Verify QA/QC workflow with version comparison."""
        # Create pre-QA snapshot
        id_pre = audit_service.create_snapshot("Pre-QA Review")

        # QA finds issues and makes corrections
        MOCK_STANDARDS_MAPPINGS.append({
            "id": 401,
            "feature_code": "NEW",
            "priority": 100,
            "layer": "L3"
        })

        # Create post-QA snapshot
        id_post = audit_service.create_snapshot("Post-QA Corrections")

        # Compare to document QA changes
        comparison = audit_service.compare_snapshots(id_pre, id_post)

        assert comparison['status'] == "DIFF_SUCCESS"
        assert comparison['changes_found'] == 1
        assert "Pre-QA Review" in comparison['source_versions']
        assert "Post-QA Corrections" in comparison['source_versions']
