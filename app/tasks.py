"""
Celery Asynchronous Tasks

This module defines all background tasks that can be executed asynchronously
via Celery. Tasks are designed to handle long-running operations without
blocking the Flask application.

Current Tasks:
    - process_dxf_import: Imports DXF files and creates intelligent objects

Task Design Principles:
    - All tasks accept serializable arguments (strings, ints, dicts)
    - Tasks log their progress to a status tracking system (Redis cache)
    - Tasks are idempotent where possible (can be retried safely)
    - Tasks use their own database connections (thread-safe)
    - Tasks return structured results for monitoring and debugging

Status Tracking:
    Each task updates a status record in the cache with the following states:
        - PENDING: Task has been queued but not started
        - STARTED: Task is currently executing
        - PROGRESS: Task is running with percentage updates
        - SUCCESS: Task completed successfully
        - FAILURE: Task encountered an error

Author: The Builder (Phase 8: Asynchronous Infrastructure)
"""

from typing import Dict, Optional
import os
import traceback
from datetime import datetime

# Import celery instance (will be created by create_celery_app)
# We'll import this from celery_config after it's created
from celery import current_app as celery_app
from flask import current_app

from database import DB_CONFIG
from dxf_importer import DXFImporter


# ==================== Status Tracking ====================

def update_task_status(task_id: str, status: str, progress: int = 0,
                      message: str = '', result: Optional[Dict] = None) -> None:
    """
    Update the status of a task in the cache.

    Args:
        task_id: Unique identifier for the task
        status: Current status (PENDING, STARTED, PROGRESS, SUCCESS, FAILURE)
        progress: Percentage complete (0-100)
        message: Human-readable status message
        result: Optional result data (for SUCCESS status)

    Status Record Structure:
        {
            'task_id': str,
            'status': str,
            'progress': int,
            'message': str,
            'result': dict (optional),
            'started_at': ISO timestamp,
            'updated_at': ISO timestamp,
            'error': str (for FAILURE status)
        }
    """
    try:
        from app.extensions import cache

        # Retrieve existing status record or create new one
        status_key = f'task_status:{task_id}'
        status_record = cache.get(status_key) or {}

        # Update fields
        if not status_record.get('started_at'):
            status_record['started_at'] = datetime.utcnow().isoformat()

        status_record.update({
            'task_id': task_id,
            'status': status,
            'progress': progress,
            'message': message,
            'updated_at': datetime.utcnow().isoformat()
        })

        if result:
            status_record['result'] = result

        # Store in cache with 1 hour TTL
        cache.set(status_key, status_record, timeout=3600)

    except Exception as e:
        # Fail gracefully - status tracking shouldn't break task execution
        print(f"WARNING: Failed to update task status: {e}")


def get_task_status(task_id: str) -> Optional[Dict]:
    """
    Retrieve the current status of a task from the cache.

    Args:
        task_id: Unique identifier for the task

    Returns:
        Status record dictionary or None if not found
    """
    try:
        from app.extensions import cache
        status_key = f'task_status:{task_id}'
        return cache.get(status_key)
    except Exception as e:
        print(f"WARNING: Failed to retrieve task status: {e}")
        return None


# ==================== DXF Import Task ====================

@celery_app.task(bind=True, name='app.tasks.process_dxf_import')
def process_dxf_import(self, file_path: str, project_id: str,
                      coordinate_system: str = 'LOCAL',
                      import_modelspace: bool = True,
                      create_intelligent_objects: bool = True,
                      use_name_translator: bool = True) -> Dict:
    """
    Asynchronous task to import a DXF file and create intelligent objects.

    This task wraps the DXFImporter.import_dxf() method to run as a background
    process. It provides progress tracking and error handling suitable for
    long-running operations.

    Args:
        file_path: Absolute path to the DXF file to import
        project_id: UUID of the project to associate entities with
        coordinate_system: Coordinate system ('LOCAL', 'STATE_PLANE', 'WGS84')
        import_modelspace: Whether to import model space entities
        create_intelligent_objects: Whether to create intelligent civil objects
        use_name_translator: Whether to use ImportMappingManager for layer translation

    Returns:
        Dictionary containing import statistics:
            {
                'entities': int,
                'text': int,
                'dimensions': int,
                'hatches': int,
                'blocks': int,
                'viewports': int,
                'points': int,
                '3dfaces': int,
                'solids': int,
                'meshes': int,
                'leaders': int,
                'intelligent_objects_created': int,
                'layers': int,
                'linetypes': int,
                'errors': list,
                'layer_translations': dict,
                'translation_stats': dict
            }

    Raises:
        Exception: Any errors during import are logged and re-raised

    Example Usage (from Flask route):
        >>> from app.tasks import process_dxf_import
        >>> task = process_dxf_import.delay('/path/to/file.dxf', project_uuid)
        >>> task_id = task.id
        >>> # Later, check status
        >>> result = task.get()  # Blocks until complete
        >>> # Or check async
        >>> status = get_task_status(task_id)

    Celery Invocation:
        The task is queued using:
            process_dxf_import.delay(file_path, project_id)

        Or with options:
            process_dxf_import.apply_async(
                args=[file_path, project_id],
                kwargs={'coordinate_system': 'STATE_PLANE'}
            )
    """
    task_id = self.request.id

    try:
        # Update status: STARTED
        update_task_status(
            task_id=task_id,
            status='STARTED',
            progress=0,
            message=f'Starting DXF import for project {project_id}'
        )

        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"DXF file not found: {file_path}")

        # Update status: PROGRESS (10%)
        update_task_status(
            task_id=task_id,
            status='PROGRESS',
            progress=10,
            message='Initializing DXF importer...'
        )

        # Initialize the importer
        # NOTE: The importer will manage its own database connection
        # to ensure thread-safety in the worker process
        importer = DXFImporter(
            db_config=DB_CONFIG,
            create_intelligent_objects=create_intelligent_objects,
            use_name_translator=use_name_translator
        )

        # Update status: PROGRESS (20%)
        update_task_status(
            task_id=task_id,
            status='PROGRESS',
            progress=20,
            message=f'Reading DXF file: {os.path.basename(file_path)}'
        )

        # Execute the import
        # This is the long-running operation that justifies async execution
        # The importer handles:
        #   - DXF file parsing (ezdxf)
        #   - Database transaction management
        #   - Layer/linetype resolution
        #   - Entity geometry conversion
        #   - Intelligent object creation
        stats = importer.import_dxf(
            file_path=file_path,
            project_id=project_id,
            coordinate_system=coordinate_system,
            import_modelspace=import_modelspace
        )

        # Update status: PROGRESS (90%)
        update_task_status(
            task_id=task_id,
            status='PROGRESS',
            progress=90,
            message='Finalizing import...'
        )

        # Prepare success message
        entities_imported = stats.get('entities', 0)
        objects_created = stats.get('intelligent_objects_created', 0)
        error_count = len(stats.get('errors', []))

        success_message = (
            f"Import complete: {entities_imported} entities, "
            f"{objects_created} intelligent objects created"
        )

        if error_count > 0:
            success_message += f" ({error_count} errors encountered)"

        # Update status: SUCCESS
        update_task_status(
            task_id=task_id,
            status='SUCCESS',
            progress=100,
            message=success_message,
            result=stats
        )

        return stats

    except Exception as e:
        # Capture full traceback for debugging
        error_trace = traceback.format_exc()
        error_message = f"DXF import failed: {str(e)}"

        # Log error to console (visible in worker logs)
        print(f"ERROR in task {task_id}:")
        print(error_trace)

        # Update status: FAILURE
        update_task_status(
            task_id=task_id,
            status='FAILURE',
            progress=0,
            message=error_message
        )

        # Store error in status record
        status_record = get_task_status(task_id) or {}
        status_record['error'] = error_trace

        from app.extensions import cache
        cache.set(f'task_status:{task_id}', status_record, timeout=3600)

        # Re-raise to mark task as failed in Celery
        raise


# ==================== Future Tasks ====================

# Additional tasks can be added here following the same pattern:
#
# @celery_app.task(bind=True, name='app.tasks.task_name')
# def task_name(self, arg1: str, arg2: int) -> Dict:
#     """Task docstring"""
#     task_id = self.request.id
#     try:
#         update_task_status(task_id, 'STARTED', 0, 'Starting...')
#         # ... task logic ...
#         update_task_status(task_id, 'SUCCESS', 100, 'Complete', result=data)
#         return data
#     except Exception as e:
#         update_task_status(task_id, 'FAILURE', 0, str(e))
#         raise
#
# Examples:
#   - process_coordinate_validation
#   - generate_performance_report
#   - batch_export_to_dxf
#   - run_quality_analysis
