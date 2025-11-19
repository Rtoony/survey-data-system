"""
Unit Tests for Project Management Service
Tests archiving, unarchiving, and status checking functionality
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock
import json

from services.project_management import ProjectManagementService


class TestProjectManagementService:
    """Test suite for ProjectManagementService"""

    def test_archive_project_success(self):
        """Test successful project archiving"""
        project_id = str(uuid4())
        user_id = str(uuid4())

        # Mock database row response
        mock_row = Mock()
        mock_row.is_archived = False
        mock_row.project_id = project_id
        mock_row.project_name = "Test Project"
        mock_row.archived_at = None
        mock_row.archived_by = None

        with patch('services.project_management.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_connection

            # Mock SELECT query
            mock_result = Mock()
            mock_result.fetchone.return_value = mock_row
            mock_connection.execute.side_effect = [
                mock_result,  # SELECT query
                Mock(),       # UPDATE query
                Mock()        # INSERT audit log
            ]

            # Execute
            result = ProjectManagementService.archive_project(
                project_id=project_id,
                user_id=user_id,
                username='test_user',
                ip_address='127.0.0.1'
            )

            # Assert
            assert result['success'] is True
            assert result['project_id'] == project_id
            assert 'archived_at' in result
            assert 'message' in result
            mock_connection.commit.assert_called_once()


    def test_archive_project_already_archived(self):
        """Test archiving a project that is already archived"""
        project_id = str(uuid4())
        archived_timestamp = datetime.utcnow() - timedelta(days=5)

        # Mock already archived project
        mock_row = Mock()
        mock_row.is_archived = True
        mock_row.archived_at = archived_timestamp

        with patch('services.project_management.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_connection

            mock_result = Mock()
            mock_result.fetchone.return_value = mock_row
            mock_connection.execute.return_value = mock_result

            # Execute
            result = ProjectManagementService.archive_project(project_id=project_id)

            # Assert
            assert result['success'] is False
            assert 'already archived' in result['message']
            # Commit should NOT be called since no changes were made
            mock_connection.commit.assert_not_called()


    def test_archive_project_not_found(self):
        """Test archiving a non-existent project"""
        project_id = str(uuid4())

        with patch('services.project_management.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_connection

            mock_result = Mock()
            mock_result.fetchone.return_value = None
            mock_connection.execute.return_value = mock_result

            # Execute and expect ValueError
            with pytest.raises(ValueError, match="Project not found"):
                ProjectManagementService.archive_project(project_id=project_id)


    def test_archive_project_invalid_uuid(self):
        """Test archiving with invalid UUID format"""
        with pytest.raises(ValueError, match="Invalid project_id format"):
            ProjectManagementService.archive_project(project_id="not-a-uuid")


    def test_unarchive_project_success(self):
        """Test successful project restoration"""
        project_id = str(uuid4())
        user_id = str(uuid4())
        archived_timestamp = datetime.utcnow() - timedelta(days=30)

        # Mock archived project
        mock_row = Mock()
        mock_row.is_archived = True
        mock_row.project_id = project_id
        mock_row.archived_at = archived_timestamp
        mock_row.archived_by = user_id

        with patch('services.project_management.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_connection

            mock_result = Mock()
            mock_result.fetchone.return_value = mock_row
            mock_connection.execute.side_effect = [
                mock_result,  # SELECT query
                Mock(),       # UPDATE query
                Mock()        # INSERT audit log
            ]

            # Execute
            result = ProjectManagementService.unarchive_project(
                project_id=project_id,
                user_id=user_id,
                username='test_user'
            )

            # Assert
            assert result['success'] is True
            assert result['project_id'] == project_id
            assert 'restored_at' in result
            mock_connection.commit.assert_called_once()


    def test_unarchive_project_not_archived(self):
        """Test unarchiving a project that is not archived"""
        project_id = str(uuid4())

        # Mock active project
        mock_row = Mock()
        mock_row.is_archived = False

        with patch('services.project_management.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_connection

            mock_result = Mock()
            mock_result.fetchone.return_value = mock_row
            mock_connection.execute.return_value = mock_result

            # Execute
            result = ProjectManagementService.unarchive_project(project_id=project_id)

            # Assert
            assert result['success'] is False
            assert 'not archived' in result['message']
            mock_connection.commit.assert_not_called()


    def test_get_project_archive_status_archived(self):
        """Test getting archive status for an archived project"""
        project_id = str(uuid4())
        user_id = str(uuid4())
        archived_timestamp = datetime.utcnow() - timedelta(days=45)

        # Mock archived project
        mock_row = Mock()
        mock_row.project_id = project_id
        mock_row.is_archived = True
        mock_row.archived_at = archived_timestamp
        mock_row.archived_by = user_id

        with patch('services.project_management.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_connection

            mock_result = Mock()
            mock_result.fetchone.return_value = mock_row
            mock_connection.execute.return_value = mock_result

            # Execute
            result = ProjectManagementService.get_project_archive_status(project_id)

            # Assert
            assert result['project_id'] == project_id
            assert result['is_archived'] is True
            assert result['archived_at'] == archived_timestamp.isoformat()
            assert result['archived_by'] == str(user_id)
            assert result['days_archived'] == 45


    def test_get_project_archive_status_active(self):
        """Test getting archive status for an active project"""
        project_id = str(uuid4())

        # Mock active project
        mock_row = Mock()
        mock_row.project_id = project_id
        mock_row.is_archived = False
        mock_row.archived_at = None
        mock_row.archived_by = None

        with patch('services.project_management.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_connection

            mock_result = Mock()
            mock_result.fetchone.return_value = mock_row
            mock_connection.execute.return_value = mock_result

            # Execute
            result = ProjectManagementService.get_project_archive_status(project_id)

            # Assert
            assert result['project_id'] == project_id
            assert result['is_archived'] is False
            assert result['archived_at'] is None
            assert result['archived_by'] is None
            assert result['days_archived'] is None


    def test_get_project_archive_status_not_found(self):
        """Test getting archive status for non-existent project"""
        project_id = str(uuid4())

        with patch('services.project_management.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_connection

            mock_result = Mock()
            mock_result.fetchone.return_value = None
            mock_connection.execute.return_value = mock_result

            # Execute and expect ValueError
            with pytest.raises(ValueError, match="Project not found"):
                ProjectManagementService.get_project_archive_status(project_id)
