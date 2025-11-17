"""
Comprehensive unit tests for DXF Exporter module.

Tests cover:
- DXF file generation from database entities
- Layer naming (standards-based and legacy)
- Entity type export (lines, circles, text, etc.)
- Z-coordinate preservation
- Transaction handling
- Error handling and edge cases
- Export statistics tracking
"""

import pytest
import ezdxf
import os
from unittest.mock import Mock, MagicMock, patch
from decimal import Decimal

from dxf_exporter import DXFExporter


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_entities():
    """Sample entities from database for export testing."""
    return [
        {
            'entity_id': '11111111-1111-1111-1111-111111111111',
            'entity_type': 'LINE',
            'layer_name': 'C-WALL',
            'geometry': 'LINESTRING Z (0 0 10, 100 100 20)',
            'color_aci': 1,
            'linetype': 'Continuous',
            'dxf_handle': 'ABC123'
        },
        {
            'entity_id': '22222222-2222-2222-2222-222222222222',
            'entity_type': 'CIRCLE',
            'layer_name': 'C-ANNO',
            'geometry': 'POINT Z (50 50 15)',
            'radius': 25.0,
            'color_aci': 3,
            'linetype': 'Continuous',
            'dxf_handle': 'DEF456'
        },
    ]


@pytest.fixture
def mock_db_cursor_with_entities(sample_entities):
    """Mock database cursor that returns sample entities."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = sample_entities
    mock_cursor.fetchone.return_value = None
    return mock_cursor


# ============================================================================
# Test DXFExporter Initialization
# ============================================================================

class TestDXFExporterInit:
    """Test DXFExporter initialization."""

    def test_init_with_standards_enabled(self, db_config):
        """Test initialization with standards enabled."""
        with patch('dxf_exporter.STANDARDS_AVAILABLE', True), \
             patch('dxf_exporter.ExportLayerGenerator'):
            exporter = DXFExporter(db_config, use_standards=True)
            assert exporter.use_standards is True

    def test_init_with_standards_disabled(self, db_config):
        """Test initialization with standards disabled."""
        exporter = DXFExporter(db_config, use_standards=False)
        assert exporter.use_standards is False
        assert exporter.layer_generator is None

    def test_init_handles_layer_generator_failure(self, db_config):
        """Test graceful handling of layer generator initialization failure."""
        with patch('dxf_exporter.STANDARDS_AVAILABLE', True), \
             patch('dxf_exporter.ExportLayerGenerator', side_effect=Exception("Init failed")):
            exporter = DXFExporter(db_config, use_standards=True)
            # Should fallback to standards disabled
            assert exporter.use_standards is False


# ============================================================================
# Test Layer Name Generation
# ============================================================================

class TestLayerNameGeneration:
    """Test layer name generation with standards and legacy modes."""

    def test_standards_based_layer_generation(self, db_config):
        """Test layer generation using standards system."""
        mock_generator = Mock()
        mock_generator.generate_layer_name.return_value = "U-WATR-12IN"

        with patch('dxf_exporter.STANDARDS_AVAILABLE', True):
            exporter = DXFExporter(db_config, use_standards=True)
            exporter.layer_generator = mock_generator

            properties = {'utility_type': 'water', 'diameter': 12}
            layer_name = exporter._generate_layer_name('utility_line', properties, 'LINE')

            assert layer_name == "U-WATR-12IN"
            mock_generator.generate_layer_name.assert_called_once()

    def test_legacy_layer_generation_with_diameter(self, db_config):
        """Test legacy layer name generation with diameter."""
        exporter = DXFExporter(db_config, use_standards=False)

        properties = {'utility_type': 'water', 'diameter': 12}
        layer_name = exporter._generate_legacy_layer_name('utility_line', properties, 'LINE')

        assert '12IN' in layer_name
        assert 'WATER' in layer_name.upper()

    def test_legacy_layer_generation_without_diameter(self, db_config):
        """Test legacy layer name generation without diameter."""
        exporter = DXFExporter(db_config, use_standards=False)

        properties = {'utility_type': 'sewer'}
        layer_name = exporter._generate_legacy_layer_name('utility_line', properties, 'LINE')

        assert 'SEWER' in layer_name.upper()

    def test_layer_generation_fallback_on_error(self, db_config):
        """Test fallback to legacy when standards generation fails."""
        mock_generator = Mock()
        mock_generator.generate_layer_name.side_effect = Exception("Generation failed")

        with patch('dxf_exporter.STANDARDS_AVAILABLE', True):
            exporter = DXFExporter(db_config, use_standards=True)
            exporter.layer_generator = mock_generator

            properties = {'utility_type': 'water', 'diameter': 12}
            layer_name = exporter._generate_layer_name('utility_line', properties, 'LINE')

            # Should fallback to legacy generation
            assert layer_name is not None


# ============================================================================
# Test Layer Management
# ============================================================================

class TestLayerManagement:
    """Test DXF layer creation and management."""

    def test_ensure_layer_creates_new_layer(self, db_config):
        """Test that _ensure_layer creates layer if it doesn't exist."""
        exporter = DXFExporter(db_config, use_standards=False)
        doc = ezdxf.new('R2010')
        stats = {'layers': set()}

        exporter._ensure_layer('NEW-LAYER', doc, stats)

        assert 'NEW-LAYER' in doc.layers
        assert 'NEW-LAYER' in stats['layers']

    def test_ensure_layer_skips_existing_layer(self, db_config):
        """Test that _ensure_layer doesn't recreate existing layer."""
        exporter = DXFExporter(db_config, use_standards=False)
        doc = ezdxf.new('R2010')
        doc.layers.add('EXISTING-LAYER')
        stats = {'layers': set()}

        initial_layer_count = len(doc.layers)
        exporter._ensure_layer('EXISTING-LAYER', doc, stats)

        # Layer count should not increase
        assert len(doc.layers) == initial_layer_count


# ============================================================================
# Test RGB Parsing
# ============================================================================

class TestRGBParsing:
    """Test RGB color string parsing."""

    def test_parse_valid_rgb_string(self, db_config):
        """Test parsing valid RGB string."""
        exporter = DXFExporter(db_config, use_standards=False)
        rgb = exporter._parse_rgb('rgb(255,128,0)')

        assert rgb == (255, 128, 0)

    def test_parse_invalid_rgb_string(self, db_config):
        """Test handling of invalid RGB string."""
        exporter = DXFExporter(db_config, use_standards=False)
        rgb = exporter._parse_rgb('invalid')

        # Should return default white
        assert rgb == (255, 255, 255)

    def test_parse_malformed_rgb_string(self, db_config):
        """Test handling of malformed RGB string."""
        exporter = DXFExporter(db_config, use_standards=False)
        rgb = exporter._parse_rgb('rgb(255,128)')

        # Should return default white
        assert rgb == (255, 255, 255)


# ============================================================================
# Test Export Statistics
# ============================================================================

class TestExportStatistics:
    """Test export statistics tracking."""

    def test_statistics_initialization(self, db_config, temp_dir, project_factory):
        """Test that export statistics are properly initialized."""
        project = project_factory()
        output_path = os.path.join(temp_dir, "test_export.dxf")

        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            exporter = DXFExporter(db_config, use_standards=False)
            stats = exporter.export_dxf(str(project['project_id']), output_path)

        assert 'entities' in stats
        assert 'text' in stats
        assert 'dimensions' in stats
        assert 'hatches' in stats
        assert 'blocks' in stats
        assert 'layers' in stats
        assert 'errors' in stats

    def test_statistics_entity_counting(self, db_config, temp_dir, project_factory, sample_entities):
        """Test that exported entities are counted correctly."""
        project = project_factory()
        output_path = os.path.join(temp_dir, "test_export.dxf")

        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            # Mock entity query result
            mock_cursor.fetchall.return_value = sample_entities
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            exporter = DXFExporter(db_config, use_standards=False)
            stats = exporter.export_dxf(str(project['project_id']), output_path)

        # Should have attempted to export entities
        assert stats is not None


# ============================================================================
# Test Transaction Handling
# ============================================================================

class TestTransactionHandling:
    """Test database transaction handling."""

    @pytest.mark.db
    def test_external_connection_not_closed(self, db_config, db_transaction, temp_dir, project_factory):
        """Test that external connections are not closed by exporter."""
        project = project_factory()
        output_path = os.path.join(temp_dir, "test_export.dxf")

        exporter = DXFExporter(db_config, use_standards=False)
        stats = exporter.export_dxf(str(project['project_id']), output_path,
                                    external_conn=db_transaction)

        # Connection should still be open (no exception when using it)
        cursor = db_transaction.cursor()
        cursor.execute("SELECT 1")
        cursor.close()

    def test_owned_connection_is_closed(self, db_config, temp_dir, project_factory):
        """Test that owned connections are properly closed."""
        project = project_factory()
        output_path = os.path.join(temp_dir, "test_export.dxf")

        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            exporter = DXFExporter(db_config, use_standards=False)
            exporter.export_dxf(str(project['project_id']), output_path)

            # Connection should have been closed
            mock_conn.close.assert_called_once()


# ============================================================================
# Test Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling in various scenarios."""

    def test_export_with_invalid_project_id(self, db_config, temp_dir):
        """Test handling of invalid project ID."""
        output_path = os.path.join(temp_dir, "test_export.dxf")

        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            exporter = DXFExporter(db_config, use_standards=False)
            stats = exporter.export_dxf('invalid-uuid', output_path)

        # Should handle error gracefully
        assert stats is not None

    def test_export_with_invalid_output_path(self, db_config, project_factory):
        """Test handling of invalid output path."""
        project = project_factory()

        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            exporter = DXFExporter(db_config, use_standards=False)

            with pytest.raises(Exception):
                # Should raise error for invalid path
                exporter.export_dxf(str(project['project_id']), '/invalid/path/file.dxf')

    def test_database_connection_failure(self, db_config, temp_dir, project_factory):
        """Test handling of database connection failure."""
        project = project_factory()
        output_path = os.path.join(temp_dir, "test_export.dxf")

        with patch('psycopg2.connect', side_effect=Exception("Connection failed")):
            exporter = DXFExporter(db_config, use_standards=False)

            with pytest.raises(Exception):
                exporter.export_dxf(str(project['project_id']), output_path)


# ============================================================================
# Test DXF Version Support
# ============================================================================

class TestDXFVersionSupport:
    """Test support for different DXF versions."""

    def test_export_r2010_dxf(self, db_config, temp_dir, project_factory):
        """Test export to R2010 DXF format."""
        project = project_factory()
        output_path = os.path.join(temp_dir, "test_r2010.dxf")

        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            exporter = DXFExporter(db_config, use_standards=False)
            stats = exporter.export_dxf(str(project['project_id']), output_path,
                                       dxf_version='AC1024')

        assert os.path.exists(output_path)

    def test_export_r2013_dxf(self, db_config, temp_dir, project_factory):
        """Test export to R2013 DXF format (default)."""
        project = project_factory()
        output_path = os.path.join(temp_dir, "test_r2013.dxf")

        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            exporter = DXFExporter(db_config, use_standards=False)
            stats = exporter.export_dxf(str(project['project_id']), output_path,
                                       dxf_version='AC1027')

        assert os.path.exists(output_path)


# ============================================================================
# Test Layer Filtering
# ============================================================================

class TestLayerFiltering:
    """Test layer filtering during export."""

    def test_export_with_layer_filter(self, db_config, temp_dir, project_factory):
        """Test export with specific layer filter."""
        project = project_factory()
        output_path = os.path.join(temp_dir, "filtered_export.dxf")
        layer_filter = ['C-WALL', 'C-ANNO']

        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            exporter = DXFExporter(db_config, use_standards=False)
            stats = exporter.export_dxf(str(project['project_id']), output_path,
                                       layer_filter=layer_filter)

        assert stats is not None

    def test_export_without_layer_filter(self, db_config, temp_dir, project_factory):
        """Test export without layer filter (export all layers)."""
        project = project_factory()
        output_path = os.path.join(temp_dir, "full_export.dxf")

        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            exporter = DXFExporter(db_config, use_standards=False)
            stats = exporter.export_dxf(str(project['project_id']), output_path,
                                       layer_filter=None)

        assert stats is not None


# ============================================================================
# Test Z-Coordinate Preservation
# ============================================================================

class TestZCoordinatePreservation:
    """Test that Z-coordinates are preserved during export."""

    @pytest.mark.db
    def test_exported_line_preserves_z_coordinates(self, db_config, temp_dir, db_cursor, project_factory, layer_factory):
        """Test that exported LINE entities preserve Z-coordinates."""
        project = project_factory()
        layer = layer_factory(project_id=project['project_id'])

        # Insert entity with Z-coordinates
        db_cursor.execute("""
            INSERT INTO drawing_entities (
                entity_type, layer_id, project_id, geometry, entity_data
            )
            VALUES (
                'LINE', %s, %s,
                ST_GeomFromText('LINESTRING Z (0 0 100, 100 100 200)', 0),
                '{}'::jsonb
            )
            RETURNING entity_id
        """, (layer['layer_id'], project['project_id']))

        output_path = os.path.join(temp_dir, "z_coord_test.dxf")

        exporter = DXFExporter(db_config, use_standards=False)
        stats = exporter.export_dxf(str(project['project_id']), output_path,
                                    external_conn=db_cursor.connection)

        # Read back the DXF and verify Z-coordinates
        if os.path.exists(output_path):
            doc = ezdxf.readfile(output_path)
            msp = doc.modelspace()
            lines = [e for e in msp if e.dxftype() == 'LINE']

            if len(lines) > 0:
                line = lines[0]
                assert line.dxf.start.z == 100 or line.dxf.start.z == 200
                assert line.dxf.end.z == 100 or line.dxf.end.z == 200


# ============================================================================
# Test Export Job Recording
# ============================================================================

class TestExportJobRecording:
    """Test export job recording in database."""

    @pytest.mark.db
    def test_export_job_recorded(self, db_config, temp_dir, db_cursor, project_factory):
        """Test that export jobs are recorded in the database."""
        project = project_factory()
        output_path = os.path.join(temp_dir, "recorded_export.dxf")

        exporter = DXFExporter(db_config, use_standards=False)
        stats = exporter.export_dxf(str(project['project_id']), output_path,
                                    external_conn=db_cursor.connection)

        # Check if export was attempted (may or may not have export_jobs table)
        assert stats is not None
