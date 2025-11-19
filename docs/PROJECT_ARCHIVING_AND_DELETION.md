# Project Archiving and Deletion System

**Phase 10: Contractual Project Archiving & Deletion**

## Overview

This document describes the two-stage project deletion system designed to meet contractual data retention obligations while providing safeguards against accidental data loss.

## Architecture

### Two-Stage Deletion Process

```
┌─────────────────┐
│  Active Project │
└────────┬────────┘
         │
         │ DELETE /api/projects/{id}
         ▼
┌─────────────────┐
│ Archived Project│  ◄─── Stage 1: Soft Delete (Reversible)
│  (is_archived)  │
└────────┬────────┘
         │
         │ Retention Period: 7 years (2555 days)
         ▼
┌─────────────────┐
│ Permanent Delete│  ◄─── Stage 2: Hard Delete (IRREVERSIBLE)
│  (Data Purged)  │
└─────────────────┘
```

### Stage 1: Soft Delete (Archive)
- **Trigger**: `DELETE /api/projects/<project_id>`
- **Action**: Sets `is_archived = TRUE`, records `archived_at` timestamp
- **Status**: HTTP 202 Accepted (asynchronous/soft deletion)
- **Reversible**: Yes, via `POST /api/projects/<project_id>/unarchive`
- **Data Retention**: All project data remains in database
- **Visibility**: Archived projects excluded from default queries

### Stage 2: Hard Delete (Permanent)
- **Trigger**: Manual execution via `HardDeleteTool` utility
- **Eligibility**: Only projects archived for ≥ retention period (default: 7 years)
- **Action**: Permanent deletion via `DELETE FROM projects`
- **Reversible**: NO - IRREVERSIBLE OPERATION
- **Data Retention**: All data permanently removed
- **Audit Trail**: Final audit log entry created before deletion

## Database Schema

### Projects Table Additions

```sql
-- Archiving columns added in migration 012
ALTER TABLE projects ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE projects ADD COLUMN archived_at TIMESTAMP;
ALTER TABLE projects ADD COLUMN archived_by UUID;

-- Index for efficient filtering
CREATE INDEX idx_projects_archived ON projects(is_archived);
CREATE INDEX idx_projects_archived_timestamp ON projects(is_archived, archived_at)
  WHERE is_archived = TRUE;
```

### Audit Log Integration

All archiving operations create audit log entries with action types:
- `ARCHIVE`: Project soft deleted
- `UNARCHIVE`: Archived project restored
- `HARD_DELETE`: Project permanently deleted (final audit entry)

## API Endpoints

### Archive a Project (Soft Delete)

```http
DELETE /api/projects/{project_id}
```

**Response**: HTTP 202 Accepted
```json
{
  "success": true,
  "archived": true,
  "project_id": "abc-123-...",
  "archived_at": "2025-11-18T20:15:30.123Z",
  "message": "Project successfully archived. Data will be retained per contractual obligations."
}
```

### Restore an Archived Project

```http
POST /api/projects/{project_id}/unarchive
```

**Response**: HTTP 200 OK
```json
{
  "success": true,
  "restored": true,
  "project_id": "abc-123-...",
  "restored_at": "2025-11-18T20:20:00.456Z",
  "message": "Project successfully restored from archive"
}
```

### Check Archive Status

```http
GET /api/projects/{project_id}/archive-status
```

**Response**: HTTP 200 OK
```json
{
  "project_id": "abc-123-...",
  "is_archived": true,
  "archived_at": "2024-01-15T10:30:00.000Z",
  "archived_by": "user-456-...",
  "days_archived": 672
}
```

### List All Archived Projects

```http
GET /api/projects/archived
```

**Response**: HTTP 200 OK
```json
{
  "archived_projects": [
    {
      "project_id": "abc-123-...",
      "project_name": "Old Highway Project",
      "archived_at": "2018-03-20T14:00:00.000Z",
      "is_archived": true
    }
  ],
  "count": 1
}
```

### Query Parameters for Project Retrieval

All project retrieval endpoints support `?include_archived=true`:

```http
GET /api/projects?include_archived=true
GET /api/projects/{project_id}?include_archived=true
```

By default, archived projects are **excluded** from all queries.

## Service Layer

### ProjectManagementService

Located in: `services/project_management.py`

#### Methods

**`archive_project(project_id, user_id, username, ip_address, user_agent)`**
- Archives a project and creates audit log entry
- Returns: Dict with success status, timestamps, and message
- Raises: `ValueError` if project not found or already archived

**`unarchive_project(project_id, user_id, username, ip_address, user_agent)`**
- Restores an archived project
- Returns: Dict with success status and restoration timestamp
- Raises: `ValueError` if project not found or not archived

**`get_project_archive_status(project_id)`**
- Retrieves archive status and metadata
- Returns: Dict with archive status, timestamps, and days archived
- Raises: `ValueError` if project not found

### Example Usage

```python
from services.project_management import ProjectManagementService

# Archive a project
result = ProjectManagementService.archive_project(
    project_id='abc-123-...',
    user_id='user-456-...',
    username='john.doe',
    ip_address='192.168.1.100',
    user_agent='Mozilla/5.0...'
)

# Check status
status = ProjectManagementService.get_project_archive_status('abc-123-...')
print(f"Archived for {status['days_archived']} days")

# Restore if needed
restore_result = ProjectManagementService.unarchive_project(
    project_id='abc-123-...',
    user_id='user-456-...'
)
```

## Hard Delete Tool

Located in: `utils/hard_delete_tool.py`

### HardDeleteTool Class

⚠️ **WARNING**: This tool performs IRREVERSIBLE database operations.

#### Methods

**`is_eligible_for_hard_delete(project_id, retention_period_days=2555)`**
- Checks if project meets retention period for permanent deletion
- Default retention: 2555 days (~7 years)
- Returns: Dict with eligibility status and detailed reasoning

**`permanently_delete_archived_project(project_id, retention_period_days, authorized_by, compliance_ticket, skip_eligibility_check=False)`**
- Permanently deletes project from database
- Requires eligibility check by default
- Creates final audit log entry before deletion
- Returns: Dict with deletion confirmation and cascade details

**`get_projects_eligible_for_deletion(retention_period_days=2555, limit=100)`**
- Lists all projects that have exceeded retention period
- Useful for compliance reporting
- Returns: List of eligible projects with metadata

### Example Usage

```python
from utils.hard_delete_tool import HardDeleteTool

# Check eligibility
eligibility = HardDeleteTool.is_eligible_for_hard_delete(
    project_id='old-project-123',
    retention_period_days=2555  # 7 years
)

if eligibility['is_eligible']:
    print(f"Project eligible: {eligibility['reason']}")

    # DANGER: Permanent deletion
    result = HardDeleteTool.permanently_delete_archived_project(
        project_id='old-project-123',
        retention_period_days=2555,
        authorized_by='admin_user_id',
        compliance_ticket='LEGAL-2025-0042'
    )

    print(result['message'])
else:
    print(f"Not eligible: {eligibility['reason']}")

# Generate compliance report
eligible_projects = HardDeleteTool.get_projects_eligible_for_deletion()
print(f"Found {len(eligible_projects)} projects ready for deletion")
```

### Safety Features

1. **Eligibility Check**: Projects must be archived for ≥ retention period
2. **Audit Trail**: Final audit log entry created before deletion
3. **Authorization Tracking**: Requires `authorized_by` and optional `compliance_ticket`
4. **Explicit Confirmation**: No accidental deletions - requires explicit method call
5. **Cascade Documentation**: Logs which related tables will be affected

### Bypass Safety (DANGEROUS)

The `skip_eligibility_check=True` parameter allows bypassing the retention period check. This should **ONLY** be used in extraordinary circumstances with documented legal approval.

## Operational Procedures

### Routine Archiving

1. User initiates project deletion via frontend
2. Frontend sends `DELETE /api/projects/{id}`
3. Backend archives project (soft delete)
4. HTTP 202 Accepted returned
5. Project disappears from normal listings
6. Audit log entry created

### Restoration Procedure

1. Identify archived project via `/api/projects/archived`
2. Send `POST /api/projects/{id}/unarchive`
3. Project becomes active again
4. Appears in normal project listings
5. Audit log entry created

### Permanent Deletion Workflow

**Prerequisites**:
- Legal/compliance approval documented
- Retention period verification (default: 7 years)
- Compliance ticket reference

**Steps**:
1. Generate eligibility report:
   ```python
   eligible = HardDeleteTool.get_projects_eligible_for_deletion()
   ```
2. Review each project with legal team
3. Obtain documented approval (compliance ticket)
4. For each approved project:
   ```python
   HardDeleteTool.permanently_delete_archived_project(
       project_id=project_id,
       authorized_by='admin_user_id',
       compliance_ticket='LEGAL-2025-XXXX'
   )
   ```
5. Verify audit log entries
6. Update external compliance tracking system

### Compliance Reporting

**Monthly Archive Report**:
```python
archived = execute_query("""
    SELECT
        project_id, project_name, archived_at, archived_by,
        EXTRACT(EPOCH FROM (NOW() - archived_at))/86400 AS days_archived
    FROM projects
    WHERE is_archived = TRUE
    ORDER BY archived_at ASC
""")
```

**Deletion Eligibility Report**:
```python
from utils.hard_delete_tool import HardDeleteTool

eligible = HardDeleteTool.get_projects_eligible_for_deletion(
    retention_period_days=2555,
    limit=1000
)
# Export to CSV for legal review
```

## Database Migration

**File**: `migrations/012_project_archiving_schema.sql`

### Applying the Migration

```bash
# Connect to PostgreSQL
psql -U your_user -d survey_data_system

# Run migration
\i migrations/012_project_archiving_schema.sql

# Verify columns were added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'projects'
  AND column_name IN ('is_archived', 'archived_at', 'archived_by');
```

### Rollback (if needed)

```sql
-- WARNING: This removes all archiving data
DROP INDEX IF EXISTS idx_projects_archived_timestamp;
DROP INDEX IF EXISTS idx_projects_archived;
ALTER TABLE projects DROP COLUMN IF EXISTS archived_by;
ALTER TABLE projects DROP COLUMN IF EXISTS archived_at;
ALTER TABLE projects DROP COLUMN IF EXISTS is_archived;
```

## Testing

### Unit Tests

**File**: `tests/unit/test_project_management_service.py`
- Tests archiving, unarchiving, and status checking
- Mocks database connections
- Validates audit log creation

**File**: `tests/unit/test_hard_delete_tool.py`
- Tests eligibility checking
- Tests permanent deletion
- Tests safety mechanisms

### Running Tests

```bash
# Run all archiving tests
pytest tests/unit/test_project_management_service.py -v
pytest tests/unit/test_hard_delete_tool.py -v

# Run with coverage
pytest tests/unit/test_project_management_service.py --cov=services.project_management
pytest tests/unit/test_hard_delete_tool.py --cov=utils.hard_delete_tool
```

### Integration Testing

```python
# Test full archiving workflow
def test_archive_restore_workflow(test_client, test_db):
    # Create project
    response = test_client.post('/api/projects', json={
        'project_name': 'Test Project',
        'description': 'For testing'
    })
    project_id = response.json['project_id']

    # Archive it
    response = test_client.delete(f'/api/projects/{project_id}')
    assert response.status_code == 202

    # Verify excluded from listings
    response = test_client.get('/api/projects')
    assert project_id not in [p['project_id'] for p in response.json['projects']]

    # Verify in archived list
    response = test_client.get('/api/projects/archived')
    assert project_id in [p['project_id'] for p in response.json['archived_projects']]

    # Restore it
    response = test_client.post(f'/api/projects/{project_id}/unarchive')
    assert response.status_code == 200

    # Verify back in normal listings
    response = test_client.get('/api/projects')
    assert project_id in [p['project_id'] for p in response.json['projects']]
```

## Security Considerations

1. **Authorization**: Ensure only authorized users can archive/delete projects
2. **Audit Logging**: All operations logged with user, IP, and timestamp
3. **Retention Enforcement**: Hard delete tool enforces minimum retention period
4. **Compliance Tracking**: Require legal approval documentation for permanent deletions
5. **Cascade Awareness**: Document all related records that will be cascade deleted

## Performance Considerations

1. **Index Usage**: `idx_projects_archived` enables efficient filtering
2. **Query Performance**: Default queries exclude archived projects automatically
3. **Cascade Deletes**: Hard delete triggers CASCADE on foreign keys - may be slow for large projects
4. **Batch Processing**: For bulk deletions, process in batches to avoid lock contention

## Recommendations

1. **Retention Period**: Default is 7 years (2555 days) - verify with legal team
2. **Regular Reviews**: Monthly review of archived projects
3. **Compliance Documentation**: Maintain external log of all permanent deletions
4. **Testing**: Always test hard delete tool in staging environment first
5. **Backup Policy**: Ensure backups are retained per compliance requirements
6. **User Training**: Educate users that DELETE archives (not permanently deletes)

## Frontend Integration

### Archive Project Flow

```javascript
// Archive project
async function archiveProject(projectId) {
  const response = await fetch(`/api/projects/${projectId}`, {
    method: 'DELETE'
  });

  if (response.status === 202) {
    const data = await response.json();
    showNotification(
      'Project Archived',
      `Project archived on ${data.archived_at}. Can be restored for 7 years.`
    );
    refreshProjectList(); // Will exclude archived project
  }
}

// Restore project
async function restoreProject(projectId) {
  const response = await fetch(`/api/projects/${projectId}/unarchive`, {
    method: 'POST'
  });

  if (response.ok) {
    showNotification('Project Restored', 'Project is now active again');
    refreshProjectList();
  }
}

// Show archived projects
async function showArchivedProjects() {
  const response = await fetch('/api/projects/archived');
  const data = await response.json();

  displayArchivedList(data.archived_projects);
}
```

## Monitoring and Alerts

Recommended monitoring metrics:

1. **Archive Rate**: Track number of projects archived per month
2. **Restoration Rate**: Track unarchive operations (high rate may indicate UX issues)
3. **Age Distribution**: Monitor age of archived projects approaching retention limit
4. **Deletion Tracking**: Alert when projects become eligible for permanent deletion
5. **Audit Log Volume**: Monitor audit_log table growth

## Conclusion

This two-stage deletion system provides:
- ✅ Compliance with data retention requirements
- ✅ Protection against accidental data loss
- ✅ Clear audit trail for all operations
- ✅ Flexible restoration workflow
- ✅ Safe permanent deletion process with multiple safeguards

For questions or issues, refer to:
- Source code: `services/project_management.py`, `utils/hard_delete_tool.py`
- Tests: `tests/unit/test_project_management_service.py`
- Migration: `migrations/012_project_archiving_schema.sql`
