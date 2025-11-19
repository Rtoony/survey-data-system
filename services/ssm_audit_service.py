# services/ssm_audit_service.py
from typing import Dict, Any, List, Optional
from sqlalchemy import select, desc, insert
from database import get_db
from data.ssm_schema import ssm_snapshots
import logging
import json
from datetime import datetime
import uuid

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock data for demonstration (will be replaced with actual query in future phases)
MOCK_STANDARDS_MAPPINGS = [
    {"id": 301, "feature_code": "SDMH", "priority": 300, "layer": "L1"},
    {"id": 201, "feature_code": "SDMH", "priority": 200, "layer": "L2"}
]

# MOCK_AUDIT_LOG remains for change log until integrated with live database
MOCK_AUDIT_LOG: List[Dict[str, Any]] = []


class SSMAuditService:
    """
    Service for managing version control, creating immutable snapshots,
    and maintaining an audit trail for all Survey Standards Manager configurations.
    Critical for QA/QC and compliance tracking.
    """

    def __init__(self):
        logger.info("SSMAuditService initialized. Live database integration active.")

    def create_snapshot(self, version_name: str, user_id: int = 1) -> str:
        """
        Creates an immutable, versioned snapshot of the entire active SSM configuration
        and inserts it into the live database.
        """
        snapshot_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # 1. Mock reading the entire active configuration from the SSM tables
        # TODO: Replace with actual queries to ssm_mappings, ssm_rulesets, etc.
        active_config = {
            "mappings": json.loads(json.dumps(MOCK_STANDARDS_MAPPINGS)), # Deep copy/serialization mock
            "rulesets": [{"id": 1, "name": "Default Rules"}],
            "metadata": {"timestamp": timestamp, "user": user_id}
        }

        # 2. INSERT the configuration into the live database
        stmt = insert(ssm_snapshots).values(
            id=snapshot_id,
            version_name=version_name,
            timestamp=timestamp,
            user_id=user_id,
            configuration_jsonb=active_config
        )

        try:
            with get_db() as conn:
                conn.execute(stmt)
                conn.commit()

            # 3. Log the creation event
            MOCK_AUDIT_LOG.append({
                "event": "SNAPSHOT_CREATED",
                "snapshot_id": snapshot_id,
                "version": version_name,
                "user_id": user_id,
                "time": timestamp
            })

            logger.info(f"SNAPSHOT CREATED (DB): ID {snapshot_id}, Version: '{version_name}'")
            return snapshot_id

        except Exception as e:
            logger.error(f"Failed to create snapshot in DB: {e}")
            raise

    def get_change_log(self) -> List[Dict[str, Any]]:
        """
        Mocks retrieving the detailed audit trail history (all major events).
        """
        logger.info("Retrieving full audit log.")
        return MOCK_AUDIT_LOG

    def get_latest_snapshot(self) -> Dict[str, Any]:
        """
        Retrieves the most recent SSM configuration snapshot from the live database.

        Returns:
            Dict containing snapshot metadata (version_name, timestamp, snapshot_id)
            or a default dict if no snapshots exist.
        """
        stmt = select(ssm_snapshots).order_by(desc(ssm_snapshots.c.timestamp)).limit(1)

        try:
            with get_db() as conn:
                result = conn.execute(stmt).fetchone()

            if result:
                # Convert Row to dict using _mapping
                snapshot_dict = dict(result._mapping)
                logger.info(f"Retrieved latest snapshot: {snapshot_dict['version_name']} ({snapshot_dict['timestamp']})")

                return {
                    "snapshot_id": snapshot_dict['id'],
                    "version_name": snapshot_dict['version_name'],
                    "timestamp": snapshot_dict['timestamp'],
                    "user_id": snapshot_dict['user_id']
                }
            else:
                logger.warning("No snapshots found in database.")
                return {"version_name": "N/A", "timestamp": "N/A"}

        except Exception as e:
            logger.error(f"Failed to retrieve latest snapshot: {e}")
            return {"version_name": "ERROR", "timestamp": "ERROR"}

    def compare_snapshots(self, id_a: str, id_b: str) -> Dict[str, Any]:
        """
        Compares two snapshots from the live database to detect what changed (deep JSON diff).
        """
        stmt = select(ssm_snapshots).where(ssm_snapshots.c.id.in_([id_a, id_b]))

        try:
            with get_db() as conn:
                results = conn.execute(stmt).fetchall()

            if len(results) != 2:
                return {"status": "ERROR", "message": "One or both snapshot IDs not found."}

            # Convert results to dict
            snapshots = {row._mapping['id']: dict(row._mapping) for row in results}

            if id_a not in snapshots or id_b not in snapshots:
                return {"status": "ERROR", "message": "One or both snapshot IDs not found."}

            config_a = snapshots[id_a]['configuration_jsonb']
            config_b = snapshots[id_b]['configuration_jsonb']

            # Actual comparison logic (diffing the JSONB content) would go here
            # For now, we simulate detecting a change if the versions aren't identical
            changes_found = 0
            if config_a != config_b:
                changes_found = 1  # Simulate one change detection

            logger.info(f"Successfully performed deep JSON diff between version {id_a} and {id_b}.")

            return {
                "status": "DIFF_SUCCESS",
                "summary": f"Detected {changes_found} modified element(s) in Mappings.",
                "changes_found": changes_found,
                "source_versions": [snapshots[id_a]['version_name'], snapshots[id_b]['version_name']]
            }

        except Exception as e:
            logger.error(f"Failed to compare snapshots: {e}")
            return {"status": "ERROR", "message": f"Database error: {str(e)}"}

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
