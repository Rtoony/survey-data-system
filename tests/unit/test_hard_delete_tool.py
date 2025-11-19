"""
Unit Tests for Hard Delete Tool
Tests permanent deletion eligibility and execution
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock

from utils.hard_delete_tool import HardDeleteTool


class TestHardDeleteTool:
    """Test suite for HardDeleteTool"""

    def test_is_eligible_for_hard_delete_eligible_project(self):
        """Test eligibility check for a project that meets retention period"""
        project_id = str(uuid4())
        archived_timestamp = datetime.utcnow() - timedelta(days=2600)  # Over 7 years

        # Mock archived project
        mock_row = Mock()
        mock_row.project_id = project_id
        mock_row.project_name = "Old Project"
        mock_row.is_archived = True
        mock_row.archived_at = archived_timestamp

        with patch('utils.hard_delete_tool.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_connection

            mock_result = Mock()
            mock_result.fetchone.return_value = mock_row
            mock_connection.execute.return_value = mock_result

            # Execute
            result = HardDeleteTool.is_eligible_for_hard_delete(
                project_id=project_id,
                retention_period_days=2555  # 7 years
            )

            # Assert
            assert result['is_eligible'] is True
            assert result['project_id'] == project_id
            assert result['is_archived'] is True
            assert result['days_archived'] >= 2555
            assert 'eligible for permanent deletion' in result['reason']


    def test_is_eligible_for_hard_delete_not_old_enough(self):
        """Test eligibility check for a recently archived project"""
        project_id = str(uuid4())
        archived_timestamp = datetime.utcnow() - timedelta(days=30)  # Only 30 days

        # Mock recently archived project
        mock_row = Mock()
        mock_row.project_id = project_id
        mock_row.project_name = "Recent Project"
        mock_row.is_archived = True
        mock_row.archived_at = archived_timestamp

        with patch('utils.hard_delete_tool.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_connection

            mock_result = Mock()
            mock_result.fetchone.return_value = mock_row
            mock_connection.execute.return_value = mock_result

            # Execute
            result = HardDeleteTool.is_eligible_for_hard_delete(
                project_id=project_id,
                retention_period_days=2555
            )

            # Assert
            assert result['is_eligible'] is False
            assert result['days_archived'] == 30
            assert 'Must wait' in result['reason']
            assert 'Eligible for deletion on:' in result['reason']


    def test_is_eligible_for_hard_delete_not_archived(self):
        """Test eligibility check for an active (non-archived) project"""
        project_id = str(uuid4())

        # Mock active project
        mock_row = Mock()
        mock_row.project_id = project_id
        mock_row.is_archived = False
        mock_row.archived_at = None

        with patch('utils.hard_delete_tool.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_connection

            mock_result = Mock()
            mock_result.fetchone.return_value = mock_row
            mock_connection.execute.return_value = mock_result

            # Execute
            result = HardDeleteTool.is_eligible_for_hard_delete(project_id=project_id)

            # Assert
            assert result['is_eligible'] is False
            assert result['is_archived'] is False
            assert 'not archived' in result['reason']
            assert 'Must archive project first' in result['reason']


    def test_is_eligible_for_hard_delete_project_not_found(self):
        """Test eligibility check for non-existent project"""
        project_id = str(uuid4())

        with patch('utils.hard_delete_tool.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_connection

            mock_result = Mock()
            mock_result.fetchone.return_value = None
            mock_connection.execute.return_value = mock_result

            # Execute
            result = HardDeleteTool.is_eligible_for_hard_delete(project_id=project_id)

            # Assert
            assert result['is_eligible'] is False
            assert 'not found' in result['reason']


    def test_is_eligible_for_hard_delete_missing_timestamp(self):
        """Test eligibility check for archived project with missing timestamp (data integrity issue)"""
        project_id = str(uuid4())

        # Mock archived project with missing timestamp
        mock_row = Mock()
        mock_row.project_id = project_id
        mock_row.project_name = "Broken Project"
        mock_row.is_archived = True
        mock_row.archived_at = None  # Data integrity issue

        with patch('utils.hard_delete_tool.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_connection

            mock_result = Mock()
            mock_result.fetchone.return_value = mock_row
            mock_connection.execute.return_value = mock_result

            # Execute
            result = HardDeleteTool.is_eligible_for_hard_delete(project_id=project_id)

            # Assert
            assert result['is_eligible'] is False
            assert 'timestamp is missing' in result['reason']
            assert 'data integrity issue' in result['reason']


    def test_permanently_delete_archived_project_success(self):
        """Test successful permanent deletion of eligible project"""
        project_id = str(uuid4())
        archived_timestamp = datetime.utcnow() - timedelta(days=2600)

        # Mock eligible project
        mock_row = Mock()
        mock_row.project_id = project_id
        mock_row.project_name = "Old Project"
        mock_row.is_archived = True
        mock_row.archived_at = archived_timestamp
        mock_row._mapping = {
            'project_id': project_id,
            'project_name': 'Old Project',
            'is_archived': True,
            'archived_at': archived_timestamp
        }

        with patch('utils.hard_delete_tool.get_db_connection') as mock_conn, \
             patch('utils.hard_delete_tool.HardDeleteTool.is_eligible_for_hard_delete') as mock_eligible:

            # Mock eligibility check
            mock_eligible.return_value = {
                'is_eligible': True,
                'reason': 'Eligible for deletion'
            }

            mock_connection = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_connection

            # Mock SELECT, INSERT audit, DELETE
            mock_select_result = Mock()
            mock_select_result.fetchone.return_value = mock_row
            mock_delete_result = Mock()
            mock_delete_result.rowcount = 1

            mock_connection.execute.side_effect = [
                mock_select_result,  # SELECT project
                Mock(),              # INSERT audit log
                mock_delete_result   # DELETE project
            ]

            # Execute
            result = HardDeleteTool.permanently_delete_archived_project(
                project_id=project_id,
                authorized_by='admin_user',
                compliance_ticket='LEGAL-2025-001'
            )

            # Assert
            assert result['success'] is True
            assert result['project_id'] == project_id
            assert result['authorized_by'] == 'admin_user'
            assert result['compliance_ticket'] == 'LEGAL-2025-001'
            assert 'IRREVERSIBLE' in result['message']
            mock_connection.commit.assert_called_once()


    def test_permanently_delete_archived_project_not_eligible(self):
        """Test attempting to delete project that doesn't meet retention period"""
        project_id = str(uuid4())

        with patch('utils.hard_delete_tool.HardDeleteTool.is_eligible_for_hard_delete') as mock_eligible:
            # Mock ineligible project
            mock_eligible.return_value = {
                'is_eligible': False,
                'reason': 'Must wait 2000 more days'
            }

            # Execute and expect ValueError
            with pytest.raises(ValueError, match="not eligible for permanent deletion"):
                HardDeleteTool.permanently_delete_archived_project(project_id=project_id)


    def test_permanently_delete_archived_project_skip_eligibility_check(self):
        """Test permanent deletion with eligibility check bypassed (DANGEROUS)"""
        project_id = str(uuid4())

        # Mock project
        mock_row = Mock()
        mock_row.project_id = project_id
        mock_row.project_name = "Bypass Project"
        mock_row._mapping = {
            'project_id': project_id,
            'project_name': 'Bypass Project'
        }

        with patch('utils.hard_delete_tool.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_connection

            mock_select_result = Mock()
            mock_select_result.fetchone.return_value = mock_row
            mock_delete_result = Mock()
            mock_delete_result.rowcount = 1

            mock_connection.execute.side_effect = [
                mock_select_result,
                Mock(),
                mock_delete_result
            ]

            # Execute with skip flag
            result = HardDeleteTool.permanently_delete_archived_project(
                project_id=project_id,
                skip_eligibility_check=True,  # BYPASS SAFETY CHECK
                authorized_by='admin_override'
            )

            # Assert - should succeed despite not checking eligibility
            assert result['success'] is True


    def test_permanently_delete_archived_project_delete_failed(self):
        """Test handling of deletion failure (no rows affected)"""
        project_id = str(uuid4())
        archived_timestamp = datetime.utcnow() - timedelta(days=2600)

        mock_row = Mock()
        mock_row.project_id = project_id
        mock_row._mapping = {'project_id': project_id}

        with patch('utils.hard_delete_tool.get_db_connection') as mock_conn, \
             patch('utils.hard_delete_tool.HardDeleteTool.is_eligible_for_hard_delete') as mock_eligible:

            mock_eligible.return_value = {'is_eligible': True}

            mock_connection = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_connection

            mock_select_result = Mock()
            mock_select_result.fetchone.return_value = mock_row
            mock_delete_result = Mock()
            mock_delete_result.rowcount = 0  # No rows deleted

            mock_connection.execute.side_effect = [
                mock_select_result,
                Mock(),
                mock_delete_result
            ]

            # Execute and expect ValueError
            with pytest.raises(ValueError, match="deletion failed - no rows affected"):
                HardDeleteTool.permanently_delete_archived_project(project_id=project_id)


    def test_get_projects_eligible_for_deletion(self):
        """Test getting list of projects eligible for deletion"""
        # Mock 3 eligible projects
        mock_rows = [
            Mock(
                project_id=uuid4(),
                project_name=f"Old Project {i}",
                archived_at=datetime.utcnow() - timedelta(days=2600 + i*10)
            )
            for i in range(3)
        ]

        with patch('utils.hard_delete_tool.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_connection

            mock_result = Mock()
            mock_result.fetchall.return_value = mock_rows
            mock_connection.execute.return_value = mock_result

            # Execute
            result = HardDeleteTool.get_projects_eligible_for_deletion(
                retention_period_days=2555,
                limit=100
            )

            # Assert
            assert len(result) == 3
            for project in result:
                assert 'project_id' in project
                assert 'project_name' in project
                assert 'archived_at' in project
                assert 'days_archived' in project
                assert 'eligible_deletion_date' in project
                assert project['days_archived'] >= 2555


    def test_get_projects_eligible_for_deletion_empty(self):
        """Test getting eligible projects when none exist"""
        with patch('utils.hard_delete_tool.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_connection

            mock_result = Mock()
            mock_result.fetchall.return_value = []
            mock_connection.execute.return_value = mock_result

            # Execute
            result = HardDeleteTool.get_projects_eligible_for_deletion()

            # Assert
            assert result == []
