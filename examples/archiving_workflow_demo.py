#!/usr/bin/env python3
"""
Project Archiving Workflow Demo
Demonstrates the two-stage deletion process for projects

This script shows how to:
1. Archive a project (soft delete)
2. Check archive status
3. Restore an archived project
4. Check deletion eligibility
5. Generate compliance reports
"""

import sys
from datetime import datetime, timedelta
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, '/home/josh_patheal/projects/survey-data-system')

from services.project_management import ProjectManagementService
from utils.hard_delete_tool import HardDeleteTool


def demo_archive_workflow():
    """Demonstrate the archiving workflow"""
    print("=" * 80)
    print("PROJECT ARCHIVING WORKFLOW DEMO")
    print("=" * 80)
    print()

    # Example project ID (replace with actual UUID from your database)
    example_project_id = str(uuid4())
    example_user_id = str(uuid4())

    print("STEP 1: Archive a Project (Soft Delete)")
    print("-" * 80)
    print(f"Project ID: {example_project_id}")
    print(f"User ID: {example_user_id}")
    print()
    print("Code:")
    print("""
    from services.project_management import ProjectManagementService

    result = ProjectManagementService.archive_project(
        project_id='abc-123-...',
        user_id='user-456-...',
        username='john.doe',
        ip_address='192.168.1.100',
        user_agent='Mozilla/5.0...'
    )
    """)
    print()
    print("Expected Response:")
    print("""
    {
        'success': True,
        'project_id': 'abc-123-...',
        'archived_at': '2025-11-18T20:30:00.123Z',
        'message': 'Project successfully archived. Data will be retained per contractual obligations.'
    }
    """)
    print()

    print("STEP 2: Check Archive Status")
    print("-" * 80)
    print("Code:")
    print("""
    status = ProjectManagementService.get_project_archive_status('abc-123-...')
    print(f"Archived: {status['is_archived']}")
    print(f"Days archived: {status['days_archived']}")
    """)
    print()
    print("Expected Response:")
    print("""
    {
        'project_id': 'abc-123-...',
        'is_archived': True,
        'archived_at': '2025-11-18T20:30:00.123Z',
        'archived_by': 'user-456-...',
        'days_archived': 0
    }
    """)
    print()

    print("STEP 3: Restore an Archived Project")
    print("-" * 80)
    print("Code:")
    print("""
    result = ProjectManagementService.unarchive_project(
        project_id='abc-123-...',
        user_id='user-456-...',
        username='john.doe'
    )
    """)
    print()
    print("Expected Response:")
    print("""
    {
        'success': True,
        'project_id': 'abc-123-...',
        'restored_at': '2025-11-18T21:00:00.456Z',
        'message': 'Project successfully restored from archive'
    }
    """)
    print()

    print("STEP 4: Check Deletion Eligibility (After 7+ Years)")
    print("-" * 80)
    print("Code:")
    print("""
    from utils.hard_delete_tool import HardDeleteTool

    eligibility = HardDeleteTool.is_eligible_for_hard_delete(
        project_id='old-project-123',
        retention_period_days=2555  # 7 years
    )

    if eligibility['is_eligible']:
        print(f"Ready for deletion: {eligibility['reason']}")
    else:
        print(f"Not ready: {eligibility['reason']}")
    """)
    print()
    print("Expected Response (NOT eligible):")
    print("""
    {
        'is_eligible': False,
        'project_id': 'old-project-123',
        'is_archived': True,
        'archived_at': '2025-01-15T10:30:00.000Z',
        'days_archived': 307,
        'retention_period_days': 2555,
        'reason': 'Project cannot be deleted yet. Must wait 2248 more days. Eligible for deletion on: 2032-02-15'
    }
    """)
    print()
    print("Expected Response (eligible):")
    print("""
    {
        'is_eligible': True,
        'project_id': 'old-project-123',
        'is_archived': True,
        'archived_at': '2018-01-15T10:30:00.000Z',
        'days_archived': 2863,
        'retention_period_days': 2555,
        'reason': 'Project is eligible for permanent deletion (archived 2863 days ago, retention period: 2555 days)'
    }
    """)
    print()

    print("STEP 5: Generate Compliance Report")
    print("-" * 80)
    print("Code:")
    print("""
    eligible_projects = HardDeleteTool.get_projects_eligible_for_deletion(
        retention_period_days=2555,
        limit=100
    )

    print(f"Found {len(eligible_projects)} projects eligible for deletion")
    for project in eligible_projects:
        print(f"  - {project['project_name']}: archived {project['days_archived']} days ago")
    """)
    print()
    print("Expected Output:")
    print("""
    Found 3 projects eligible for deletion
      - Old Highway Project: archived 2863 days ago
      - Legacy Survey 2015: archived 2701 days ago
      - Discontinued Development: archived 2598 days ago
    """)
    print()

    print("STEP 6: Permanent Deletion (After Legal Approval)")
    print("-" * 80)
    print("⚠️  WARNING: THIS OPERATION IS IRREVERSIBLE ⚠️")
    print()
    print("Code:")
    print("""
    # ONLY run with documented legal approval
    result = HardDeleteTool.permanently_delete_archived_project(
        project_id='old-project-123',
        retention_period_days=2555,
        authorized_by='admin_user_id',
        compliance_ticket='LEGAL-2025-0042'
    )

    print(result['message'])
    """)
    print()
    print("Expected Response:")
    print("""
    {
        'success': True,
        'project_id': 'old-project-123',
        'project_name': 'Old Highway Project',
        'deleted_at': '2025-11-18T22:00:00.000Z',
        'authorized_by': 'admin_user_id',
        'compliance_ticket': 'LEGAL-2025-0042',
        'cascaded_deletes': {
            'note': 'All related records deleted via CASCADE constraints',
            'tables_affected': ['survey_points', 'entities', 'relationships', '...']
        },
        'message': 'Project "Old Highway Project" permanently deleted. This operation is IRREVERSIBLE. Audit trail preserved in audit_log table.'
    }
    """)
    print()

    print("=" * 80)
    print("API ENDPOINTS")
    print("=" * 80)
    print()
    print("Archive a project (soft delete):")
    print("  DELETE /api/projects/{project_id}")
    print("  Returns: 202 Accepted")
    print()
    print("Restore an archived project:")
    print("  POST /api/projects/{project_id}/unarchive")
    print("  Returns: 200 OK")
    print()
    print("Check archive status:")
    print("  GET /api/projects/{project_id}/archive-status")
    print("  Returns: 200 OK")
    print()
    print("List all archived projects:")
    print("  GET /api/projects/archived")
    print("  Returns: 200 OK")
    print()
    print("List active projects (excludes archived):")
    print("  GET /api/projects")
    print("  Returns: 200 OK")
    print()
    print("Include archived in query:")
    print("  GET /api/projects?include_archived=true")
    print("  Returns: 200 OK")
    print()

    print("=" * 80)
    print("SAFETY FEATURES")
    print("=" * 80)
    print()
    print("✅ Soft delete prevents accidental permanent data loss")
    print("✅ Retention period enforcement (default: 7 years)")
    print("✅ Full audit trail for all operations")
    print("✅ Authorization and compliance ticket tracking")
    print("✅ Multiple safety checks before permanent deletion")
    print("✅ Reversible restoration workflow")
    print("✅ Comprehensive logging for legal compliance")
    print()

    print("=" * 80)
    print("COMPLIANCE WORKFLOW")
    print("=" * 80)
    print()
    print("1. User deletes project via frontend")
    print("   → Project archived (soft delete)")
    print("   → HTTP 202 Accepted returned")
    print("   → Audit log entry created")
    print()
    print("2. Project excluded from normal queries")
    print("   → Appears in archived projects list")
    print("   → Can be restored within 7 years")
    print()
    print("3. After 7 years:")
    print("   → Project becomes eligible for permanent deletion")
    print("   → Legal team reviews compliance report")
    print("   → Documented approval obtained")
    print()
    print("4. Permanent deletion:")
    print("   → HardDeleteTool checks eligibility")
    print("   → Final audit log entry created")
    print("   → Project and all related data permanently removed")
    print("   → Audit trail preserved indefinitely")
    print()


if __name__ == '__main__':
    demo_archive_workflow()
