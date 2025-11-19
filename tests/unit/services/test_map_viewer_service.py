"""
Comprehensive unit tests for MapViewerService.

Tests cover:
- Service initialization
- Vector tile data retrieval (MVT generation)
- Zoom level, tile coordinate handling
- Layer name and extent parameters
- Edge cases with missing data
- Error handling for query failures
- Mock PostGIS ST_AsMVTGeom and ST_TileEnvelope behavior
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import Optional

from services.map_viewer_service import MapViewerService, _mock_get_connection


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def map_viewer_service():
    """Create MapViewerService instance."""
    return MapViewerService()


# ============================================================================
# Initialization Tests
# ============================================================================

class TestServiceInitialization:
    """Tests for MapViewerService initialization."""

    def test_service_initialization(self, map_viewer_service):
        """Test that the service initializes successfully."""
        assert map_viewer_service is not None
        assert isinstance(map_viewer_service, MapViewerService)

    @patch('services.map_viewer_service.logger')
    def test_initialization_logging(self, mock_logger):
        """Test that initialization is logged."""
        service = MapViewerService()
        mock_logger.info.assert_called_with(
            "MapViewerService initialized. Optimized spatial retrieval is active."
        )


# ============================================================================
# Vector Tile Data Retrieval Tests
# ============================================================================

class TestVectorTileRetrieval:
    """Tests for get_vector_tile_data method."""

    def test_successful_tile_retrieval(self, map_viewer_service):
        """Test successful retrieval of vector tile data."""
        result = map_viewer_service.get_vector_tile_data(
            z=16,
            x=12345,
            y=6789,
            layer_name="ssm_points_layer",
            extent_wkt="BBOX(WKT)"
        )

        assert result is not None
        assert isinstance(result, str)
        assert result == "MVT_TILE_DATA_012345"

    def test_tile_retrieval_different_zoom_levels(self, map_viewer_service):
        """Test tile retrieval at various zoom levels."""
        zoom_levels = [0, 10, 15, 18, 22]

        for zoom in zoom_levels:
            result = map_viewer_service.get_vector_tile_data(
                z=zoom,
                x=100,
                y=200,
                layer_name="test_layer",
                extent_wkt="BBOX(WKT)"
            )
            assert result is not None, f"Failed for zoom level {zoom}"

    def test_tile_retrieval_different_coordinates(self, map_viewer_service):
        """Test tile retrieval with various tile coordinates."""
        test_cases = [
            (0, 0, 0),        # Origin tile
            (5, 15, 10),      # Mid-range coordinates
            (18, 262143, 262143),  # Max tile at zoom 18
        ]

        for z, x, y in test_cases:
            result = map_viewer_service.get_vector_tile_data(
                z=z,
                x=x,
                y=y,
                layer_name="test_layer",
                extent_wkt="BBOX(WKT)"
            )
            assert result is not None, f"Failed for Z={z}, X={x}, Y={y}"

    def test_tile_retrieval_different_layers(self, map_viewer_service):
        """Test tile retrieval from different layer names."""
        layers = [
            "ssm_points_layer",
            "utility_lines",
            "parcel_boundaries",
            "survey_monuments"
        ]

        for layer in layers:
            result = map_viewer_service.get_vector_tile_data(
                z=16,
                x=1000,
                y=2000,
                layer_name=layer,
                extent_wkt="BBOX(WKT)"
            )
            assert result is not None, f"Failed for layer {layer}"

    @patch('services.map_viewer_service.logger')
    def test_successful_tile_logging(self, mock_logger, map_viewer_service):
        """Test that successful tile generation is logged."""
        map_viewer_service.get_vector_tile_data(
            z=16,
            x=12345,
            y=6789,
            layer_name="test_layer",
            extent_wkt="BBOX(WKT)"
        )

        # Check that appropriate log messages were called
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Requesting vector tile Z=16, X=12345, Y=6789" in call for call in info_calls)
        assert any("MVT tile successfully generated and retrieved" in call for call in info_calls)


# ============================================================================
# No Data Handling Tests
# ============================================================================

class TestNoDataHandling:
    """Tests for handling cases where no data is found."""

    @patch('services.map_viewer_service._mock_get_connection')
    def test_no_data_found(self, mock_connection_ctx, map_viewer_service):
        """Test handling when no data is found for the requested tile."""
        # Mock connection that returns empty results
        mock_conn = MagicMock()
        mock_conn.execute.return_value = []
        mock_connection_ctx.return_value.__enter__.return_value = mock_conn

        result = map_viewer_service.get_vector_tile_data(
            z=16,
            x=99999,
            y=99999,
            layer_name="empty_layer",
            extent_wkt="BBOX(WKT)"
        )

        assert result is None

    @patch('services.map_viewer_service._mock_get_connection')
    @patch('services.map_viewer_service.logger')
    def test_no_data_warning_logged(self, mock_logger, mock_connection_ctx, map_viewer_service):
        """Test that a warning is logged when no data is found."""
        # Mock connection that returns empty results
        mock_conn = MagicMock()
        mock_conn.execute.return_value = []
        mock_connection_ctx.return_value.__enter__.return_value = mock_conn

        map_viewer_service.get_vector_tile_data(
            z=16,
            x=99999,
            y=99999,
            layer_name="empty_layer",
            extent_wkt="BBOX(WKT)"
        )

        mock_logger.warning.assert_called_with("No data found for the requested tile extent.")


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error handling during tile generation."""

    @patch('services.map_viewer_service._mock_get_connection')
    def test_query_execution_error(self, mock_connection_ctx, map_viewer_service):
        """Test handling of query execution errors."""
        # Mock connection that raises an exception
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("Database connection failed")
        mock_connection_ctx.return_value.__enter__.return_value = mock_conn

        result = map_viewer_service.get_vector_tile_data(
            z=16,
            x=1000,
            y=2000,
            layer_name="test_layer",
            extent_wkt="BBOX(WKT)"
        )

        assert result is None

    @patch('services.map_viewer_service._mock_get_connection')
    @patch('services.map_viewer_service.logger')
    def test_error_logging(self, mock_logger, mock_connection_ctx, map_viewer_service):
        """Test that errors are properly logged."""
        # Mock connection that raises an exception
        mock_conn = MagicMock()
        error_message = "Spatial query failed"
        mock_conn.execute.side_effect = Exception(error_message)
        mock_connection_ctx.return_value.__enter__.return_value = mock_conn

        map_viewer_service.get_vector_tile_data(
            z=16,
            x=1000,
            y=2000,
            layer_name="test_layer",
            extent_wkt="BBOX(WKT)"
        )

        # Check that error was logged
        assert mock_logger.error.called
        error_call = mock_logger.error.call_args[0][0]
        assert "Error executing vector tile query" in error_call


# ============================================================================
# SQL Query Generation Tests
# ============================================================================

class TestQueryGeneration:
    """Tests for SQL query construction."""

    @patch('services.map_viewer_service._mock_get_connection')
    def test_query_includes_correct_tile_parameters(self, mock_connection_ctx, map_viewer_service):
        """Test that the generated query includes correct Z/X/Y parameters."""
        mock_conn = MagicMock()
        mock_conn.execute.return_value = [("MVT_TILE_DATA_012345",)]
        mock_connection_ctx.return_value.__enter__.return_value = mock_conn

        map_viewer_service.get_vector_tile_data(
            z=16,
            x=12345,
            y=6789,
            layer_name="test_layer",
            extent_wkt="BBOX(WKT)"
        )

        # Verify that execute was called
        assert mock_conn.execute.called
        executed_query = mock_conn.execute.call_args[0][0]

        # The query should be a SQLAlchemy text object
        query_string = str(executed_query)
        assert "16" in query_string
        assert "12345" in query_string
        assert "6789" in query_string

    @patch('services.map_viewer_service._mock_get_connection')
    def test_query_includes_layer_name(self, mock_connection_ctx, map_viewer_service):
        """Test that the generated query includes the layer name."""
        mock_conn = MagicMock()
        mock_conn.execute.return_value = [("MVT_TILE_DATA_012345",)]
        mock_connection_ctx.return_value.__enter__.return_value = mock_conn

        layer_name = "custom_layer_name"
        map_viewer_service.get_vector_tile_data(
            z=16,
            x=1000,
            y=2000,
            layer_name=layer_name,
            extent_wkt="BBOX(WKT)"
        )

        executed_query = mock_conn.execute.call_args[0][0]
        query_string = str(executed_query)
        assert layer_name in query_string

    @patch('services.map_viewer_service._mock_get_connection')
    def test_query_uses_postgis_functions(self, mock_connection_ctx, map_viewer_service):
        """Test that the query uses PostGIS ST_AsMVTGeom and ST_TileEnvelope functions."""
        mock_conn = MagicMock()
        mock_conn.execute.return_value = [("MVT_TILE_DATA_012345",)]
        mock_connection_ctx.return_value.__enter__.return_value = mock_conn

        map_viewer_service.get_vector_tile_data(
            z=16,
            x=1000,
            y=2000,
            layer_name="test_layer",
            extent_wkt="BBOX(WKT)"
        )

        executed_query = mock_conn.execute.call_args[0][0]
        query_string = str(executed_query)

        # Verify PostGIS functions are used
        assert "ST_AsMVTGeom" in query_string
        assert "ST_TileEnvelope" in query_string
        assert "ST_Intersects" in query_string


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_zoom_level_zero(self, map_viewer_service):
        """Test tile retrieval at zoom level 0 (world view)."""
        result = map_viewer_service.get_vector_tile_data(
            z=0,
            x=0,
            y=0,
            layer_name="world_layer",
            extent_wkt="BBOX(WKT)"
        )
        assert result is not None

    def test_maximum_zoom_level(self, map_viewer_service):
        """Test tile retrieval at maximum typical zoom level (22)."""
        result = map_viewer_service.get_vector_tile_data(
            z=22,
            x=1000000,
            y=2000000,
            layer_name="detail_layer",
            extent_wkt="BBOX(WKT)"
        )
        assert result is not None

    def test_layer_name_with_schema(self, map_viewer_service):
        """Test layer name that includes schema prefix."""
        result = map_viewer_service.get_vector_tile_data(
            z=16,
            x=1000,
            y=2000,
            layer_name="public.ssm_points",
            extent_wkt="BBOX(WKT)"
        )
        assert result is not None

    def test_empty_extent_wkt(self, map_viewer_service):
        """Test with empty extent_wkt (currently unused parameter)."""
        result = map_viewer_service.get_vector_tile_data(
            z=16,
            x=1000,
            y=2000,
            layer_name="test_layer",
            extent_wkt=""
        )
        assert result is not None

    @patch('services.map_viewer_service._mock_get_connection')
    def test_result_tuple_access(self, mock_connection_ctx, map_viewer_service):
        """Test proper extraction of MVT data from result tuple."""
        mock_conn = MagicMock()
        # Mock returns a list with a tuple containing the MVT data
        expected_data = "CUSTOM_MVT_DATA_XYZ"
        mock_conn.execute.return_value = [(expected_data,)]
        mock_connection_ctx.return_value.__enter__.return_value = mock_conn

        result = map_viewer_service.get_vector_tile_data(
            z=16,
            x=1000,
            y=2000,
            layer_name="test_layer",
            extent_wkt="BBOX(WKT)"
        )

        assert result == expected_data


# ============================================================================
# Mock Connection Tests
# ============================================================================

class TestMockConnection:
    """Tests for the mock connection context manager."""

    def test_mock_connection_context_manager(self):
        """Test that the mock connection context manager works correctly."""
        with _mock_get_connection() as conn:
            assert conn is not None
            assert hasattr(conn, 'execute')

    def test_mock_connection_execute(self):
        """Test that the mock connection execute method returns expected data."""
        from sqlalchemy import text

        with _mock_get_connection() as conn:
            query = text("SELECT * FROM test")
            result = conn.execute(query)
            assert result is not None
            assert len(result) == 1
            assert result[0][0] == "MVT_TILE_DATA_012345"

    @patch('services.map_viewer_service.logger')
    def test_mock_connection_logs_query(self, mock_logger):
        """Test that mock connection logs query execution."""
        from sqlalchemy import text

        with _mock_get_connection() as conn:
            query = text("SELECT ST_AsMVTGeom(geom) FROM layer")
            conn.execute(query)

        # Check that logging occurred
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("MOCK QUERY" in call for call in info_calls)
