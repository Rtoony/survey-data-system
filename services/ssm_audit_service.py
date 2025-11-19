# services/ssm_audit_service.py
from typing import Dict, Any, List, Optional
import logging
import json
from datetime import datetime
import uuid

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock data for demonstration
MOCK_STANDARDS_MAPPINGS = [
    {"id": 301, "feature_code": "SDMH", "priority": 300, "layer": "L1"},
    {"id": 201, "feature_code": "SDMH", "priority": 200, "layer": "L2"}
]

# Mock storage structure for ssm_snapshots (key: snapshot_id, value: record)
MOCK_SNAPSHOT_DB: Dict[str, Dict[str, Any]] = {}
MOCK_AUDIT_LOG: List[Dict[str, Any]] = []


class SSMAuditService:
    """
    Service for managing version control, creating immutable snapshots,
    and maintaining an audit trail for all Survey Standards Manager configurations.
    Critical for QA/QC and compliance tracking.
    """

    def __init__(self):
        logger.info("SSMAuditService initialized. Audit logging is active.")

    def create_snapshot(self, version_name: str, user_id: int = 1) -> str:
        """
        Simulates creating an immutable, versioned snapshot of the entire active SSM configuration.
        """
        snapshot_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # 1. Mock reading the entire active configuration from the SSM tables
        active_config = {
            "mappings": json.loads(json.dumps(MOCK_STANDARDS_MAPPINGS)), # Deep copy/serialization mock
            "rulesets": [{"id": 1, "name": "Default Rules"}],
            "metadata": {"timestamp": timestamp, "user": user_id}
        }

        # 2. Store the configuration as an immutable JSON BLOB
        snapshot_record = {
            "id": snapshot_id,
            "version_name": version_name,
            "timestamp": timestamp,
            "user_id": user_id,
            "configuration_jsonb": active_config # Stored as Python dict/JSON
        }

        MOCK_SNAPSHOT_DB[snapshot_id] = snapshot_record

        # 3. Log the creation event
        MOCK_AUDIT_LOG.append({
            "event": "SNAPSHOT_CREATED",
            "snapshot_id": snapshot_id,
            "version": version_name,
            "user_id": user_id,
            "time": timestamp
        })

        logger.info(f"SNAPSHOT CREATED: ID {snapshot_id}, Version: '{version_name}'")
        return snapshot_id

    def get_change_log(self) -> List[Dict[str, Any]]:
        """
        Mocks retrieving the detailed audit trail history (all major events).
        """
        logger.info("Retrieving full audit log.")
        return MOCK_AUDIT_LOG

    def compare_snapshots(self, id_a: str, id_b: str) -> Dict[str, Any]:
        """
        Mocks a crucial function: comparing two versions to see what changed
        (a deep JSON diff).
        """
        if id_a not in MOCK_SNAPSHOT_DB or id_b not in MOCK_SNAPSHOT_DB:
            return {"status": "ERROR", "message": "One or both snapshot IDs not found."}

        config_a = MOCK_SNAPSHOT_DB[id_a]['configuration_jsonb']
        config_b = MOCK_SNAPSHOT_DB[id_b]['configuration_jsonb']

        # Actual comparison logic (diffing the JSONB content) would go here
        # For mock purposes, we simulate detecting a change if the versions aren't identical
        changes_found = 0
        if config_a != config_b:
            changes_found = 1 # Simulate one change detection

        logger.info(f"MOCK: Successfully performed deep JSON diff between version {id_a} and {id_b}.")

        return {
            "status": "DIFF_SUCCESS",
            "summary": f"Detected {changes_found} modified element(s) in Mappings.",
            "changes_found": changes_found,
            "source_versions": [MOCK_SNAPSHOT_DB[id_a]['version_name'], MOCK_SNAPSHOT_DB[id_b]['version_name']]
        }

# --- Example Execution ---
if __name__ == '__main__':
    service = SSMAuditService()

    # 1. Create a baseline snapshot
    id_v1 = service.create_snapshot("Initial V1.0 Release")

    # 2. Simulate a change to the active standard
    # NOTE: This must modify the global MOCK_STANDARDS_MAPPINGS list before V2 is created
    MOCK_STANDARDS_MAPPINGS[0]['priority'] = 400 # Simulate an edit to mapping 301
    MOCK_STANDARDS_MAPPINGS[0]['layer'] = "L1-UPDATED"

    # 3. Create a new version
    id_v2 = service.create_snapshot("V1.1 Priority/Layer Fix")

    print("\n--- AUDIT LOG ---")
    print(json.dumps(service.get_change_log(), indent=4))

    print("\n--- SNAPSHOT COMPARISON (V1 vs V2) ---")
    comparison = service.compare_snapshots(id_v1, id_v2)
    print(json.dumps(comparison, indent=4))
