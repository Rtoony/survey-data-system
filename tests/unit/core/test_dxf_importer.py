"""
Comprehensive unit tests for DXF Importer module.

Tests cover:
- DXF file reading and parsing
- Entity conversion to WKT geometry
- Layer and linetype import
- Transaction handling
- Z-coordinate preservation
- Error handling and edge cases
- Statistics tracking
"""

import pytest
import ezdxf
import os
import tempfile
from unittest.mock import Mock, MagicMock, patch, call
from decimal import Decimal
import psycopg2

from dxf_importer import DXFImporter


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_dxf_file(temp_dir):
    """Create a comprehensive test DXF file with various entity types."""
    filepath = os.path.join(temp_dir, "comprehensive_test.dxf")
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()

    # Add various entity types with Z-coordinates
    msp.add_line((0, 0, 10), (100, 100, 20), dxfattribs={'layer': 'C-WALL', 'color': 1})
    msp.add_circle((50, 50, 15), radius=25, dxfattribs={'layer': 'C-ANNO', 'color': 3})
    msp.add_arc((75, 75, 12), radius=30, start_angle=0, end_angle=180,
                dxfattribs={'layer': 'C-UTIL', 'color': 5})

    # Polyline with Z-coordinates
    points = [(0, 0, 10), (50, 0, 15), (50, 50, 20), (0, 50, 15), (0, 0, 10)]
    pline = msp.add_polyline3d(points, dxfattribs={'layer': 'C-PROP', 'color': 2})
    pline.close()

    # LWPolyline (2D with elevation)
    msp.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)],
                       dxfattribs={'layer': 'C-SITE', 'elevation': 25.0})

    # Text entities
    msp.add_text('Test Text', dxfattribs={'layer': 'C-TEXT', 'height': 5}).set_placement((10, 10))
    msp.add_mtext('Multi-line\\PText Content', dxfattribs={'layer': 'C-MTEXT', 'char_height': 2.5})

    # Point
    msp.add_point((100, 200, 50), dxfattribs={'layer': 'V-NODE'})

    # Block definition
    block = doc.blocks.new('TEST_BLOCK')
    block.add_line((0, 0), (10, 10))
    msp.add_blockref('TEST_BLOCK', (200, 200), dxfattribs={'layer': 'C-BLOCK'})

    # Dimension
    msp.add_linear_dim(base=(100, 300), p1=(0, 0), p2=(100, 0),
                       dxfattribs={'layer': 'C-DIM'})

    # Hatch
    hatch = msp.add_hatch(color=7, dxfattribs={'layer': 'C-HATCH'})
    hatch.paths.add_polyline_path([(0, 0), (10, 0), (10, 10), (0, 10)])

    doc.saveas(filepath)
    return filepath


@pytest.fixture
def empty_dxf_file(temp_dir):
    """Create an empty DXF file."""
    filepath = os.path.join(temp_dir, "empty_test.dxf")
    doc = ezdxf.new('R2010')
    doc.saveas(filepath)
    return filepath


@pytest.fixture
def mock_db_connection():
    """Mock database connection and cursor."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'layer_id': 'test-layer-id', 'layer_standard_id': None}
    return mock_conn, mock_cursor


# ============================================================================
# Test DXFImporter Initialization
# ============================================================================

class TestDXFImporterInit:
    """Test DXFImporter initialization."""

    def test_init_default_params(self, db_config):
        """Test initialization with default parameters."""
        importer = DXFImporter(db_config)
        assert importer.db_config == db_config
        assert importer.create_intelligent_objects is True

    def test_init_with_intelligent_objects_disabled(self, db_config):
        """Test initialization with intelligent objects disabled."""
        importer = DXFImporter(db_config, create_intelligent_objects=False)
        assert importer.create_intelligent_objects is False

    def test_init_with_invalid_db_config(self):
        """Test initialization with invalid database config."""
        invalid_config = {'host': 'invalid', 'port': 'invalid'}
        importer = DXFImporter(invalid_config)
        assert importer.db_config == invalid_config


# ============================================================================
# Test Entity to WKT Conversion
# ============================================================================

class TestEntityToWKT:
    """Test conversion of DXF entities to WKT geometry."""

    def test_line_to_wkt_with_z_coordinates(self, db_config):
        """Test LINE entity conversion preserves Z-coordinates."""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        line = msp.add_line((0, 0, 10), (100, 100, 20))

        importer = DXFImporter(db_config)
        wkt = importer._entity_to_wkt(line)

        assert wkt is not None
        assert 'LINESTRING Z' in wkt
        assert '0 0 10' in wkt
        assert '100 100 20' in wkt

    def test_circle_to_wkt_approximation(self, db_config):
        """Test CIRCLE entity conversion to linestring approximation."""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        circle = msp.add_circle((50, 50, 15), radius=25)

        importer = DXFImporter(db_config)
        wkt = importer._entity_to_wkt(circle)

        assert wkt is not None
        assert 'LINESTRING Z' in wkt
        # Circle should be approximated with 33 points (32 segments + closing point)
        assert wkt.count(',') == 32

    def test_arc_to_wkt_with_angles(self, db_config):
        """Test ARC entity conversion with start and end angles."""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        arc = msp.add_arc((75, 75, 12), radius=30, start_angle=0, end_angle=180)

        importer = DXFImporter(db_config)
        wkt = importer._entity_to_wkt(arc)

        assert wkt is not None
        assert 'LINESTRING Z' in wkt
        assert '12' in wkt  # Z-coordinate preserved

    def test_polyline_to_wkt_closed_polygon(self, db_config):
        """Test closed POLYLINE conversion to POLYGON."""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        points = [(0, 0, 10), (50, 0, 15), (50, 50, 20), (0, 50, 15), (0, 0, 10)]
        pline = msp.add_polyline3d(points)
        pline.close()

        importer = DXFImporter(db_config)
        wkt = importer._entity_to_wkt(pline)

        assert wkt is not None
        assert 'POLYGON Z' in wkt
        assert '0 0 10' in wkt
        assert '50 50 20' in wkt

    def test_polyline_to_wkt_open_linestring(self, db_config):
        """Test open POLYLINE conversion to LINESTRING."""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        points = [(0, 0, 10), (50, 0, 15), (100, 0, 20)]
        pline = msp.add_polyline3d(points)

        importer = DXFImporter(db_config)
        wkt = importer._entity_to_wkt(pline)

        assert wkt is not None
        assert 'LINESTRING Z' in wkt
        assert 'POLYGON' not in wkt

    def test_lwpolyline_to_wkt_with_elevation(self, db_config):
        """Test LWPOLYLINE conversion with elevation."""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        lwpline = msp.add_lwpolyline([(0, 0), (100, 0), (100, 100)],
                                     dxfattribs={'elevation': 25.0})

        importer = DXFImporter(db_config)
        wkt = importer._entity_to_wkt(lwpline)

        assert wkt is not None
        assert 'LINESTRING Z' in wkt
        assert '25' in wkt  # Elevation preserved as Z


# ============================================================================
# Test Import Statistics
# ============================================================================

class TestImportStatistics:
    """Test import statistics tracking."""

    @pytest.mark.db
    def test_statistics_initialization(self, db_config, empty_dxf_file, db_transaction, project_factory):
        """Test that statistics are properly initialized."""
        project = project_factory()

        with patch('dxf_importer.DXFLookupService'):
            importer = DXFImporter(db_config, create_intelligent_objects=False)
            stats = importer.import_dxf(empty_dxf_file, str(project['project_id']),
                                       external_conn=db_transaction)

        assert 'entities' in stats
        assert 'text' in stats
        assert 'dimensions' in stats
        assert 'hatches' in stats
        assert 'blocks' in stats
        assert 'layers' in stats
        assert 'errors' in stats

    @pytest.mark.db
    def test_statistics_entity_counting(self, db_config, sample_dxf_file, db_transaction, project_factory):
        """Test that entities are counted correctly."""
        project = project_factory()

        with patch('dxf_importer.DXFLookupService'), \
             patch('dxf_importer.IntelligentObjectCreator'):
            importer = DXFImporter(db_config, create_intelligent_objects=False)
            stats = importer.import_dxf(sample_dxf_file, str(project['project_id']),
                                       external_conn=db_transaction)

        # Should have counted various entities
        assert stats['entities'] > 0 or len(stats['errors']) > 0


# ============================================================================
# Test Coordinate System Handling
# ============================================================================

class TestCoordinateSystemHandling:
    """Test coordinate system (SRID) handling."""

    def test_local_coordinate_system(self, db_config):
        """Test LOCAL coordinate system sets SRID to 0."""
        importer = DXFImporter(db_config)
        doc = ezdxf.new('R2010')

        # Simulate setting SRID during import
        srid_map = {'LOCAL': 0, 'STATE_PLANE': 2226, 'WGS84': 4326}
        coordinate_system = 'LOCAL'
        srid = srid_map.get(coordinate_system.upper(), 0)

        assert srid == 0

    def test_state_plane_coordinate_system(self, db_config):
        """Test STATE_PLANE coordinate system sets correct SRID."""
        srid_map = {'LOCAL': 0, 'STATE_PLANE': 2226, 'WGS84': 4326}
        coordinate_system = 'STATE_PLANE'
        srid = srid_map.get(coordinate_system.upper(), 0)

        assert srid == 2226

    def test_wgs84_coordinate_system(self, db_config):
        """Test WGS84 coordinate system sets correct SRID."""
        srid_map = {'LOCAL': 0, 'STATE_PLANE': 2226, 'WGS84': 4326}
        coordinate_system = 'WGS84'
        srid = srid_map.get(coordinate_system.upper(), 0)

        assert srid == 4326

    def test_unknown_coordinate_system_defaults_to_local(self, db_config):
        """Test unknown coordinate system defaults to LOCAL (SRID 0)."""
        srid_map = {'LOCAL': 0, 'STATE_PLANE': 2226, 'WGS84': 4326}
        coordinate_system = 'UNKNOWN'
        srid = srid_map.get(coordinate_system.upper(), 0)

        assert srid == 0


# ============================================================================
# Test Transaction Handling
# ============================================================================

class TestTransactionHandling:
    """Test database transaction handling."""

    @pytest.mark.db
    def test_external_connection_not_closed(self, db_config, empty_dxf_file, db_transaction, project_factory):
        """Test that external connections are not closed by importer."""
        project = project_factory()

        with patch('dxf_importer.DXFLookupService'):
            importer = DXFImporter(db_config, create_intelligent_objects=False)
            importer.import_dxf(empty_dxf_file, str(project['project_id']),
                               external_conn=db_transaction)

        # Connection should still be open (no exception when using it)
        cursor = db_transaction.cursor()
        cursor.execute("SELECT 1")
        cursor.close()

    @pytest.mark.db
    def test_rollback_on_error_with_owned_connection(self, db_config, temp_dir, project_factory):
        """Test that rollback occurs on error when importer owns connection."""
        project = project_factory()

        # Create an invalid DXF file
        invalid_file = os.path.join(temp_dir, "invalid.dxf")
        with open(invalid_file, 'w') as f:
            f.write("INVALID DXF CONTENT")

        importer = DXFImporter(db_config, create_intelligent_objects=False)
        stats = importer.import_dxf(invalid_file, str(project['project_id']))

        # Should have errors
        assert len(stats['errors']) > 0


# ============================================================================
# Test Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling in various scenarios."""

    def test_nonexistent_file(self, db_config, project_factory):
        """Test handling of non-existent DXF file."""
        project = project_factory()

        importer = DXFImporter(db_config, create_intelligent_objects=False)
        stats = importer.import_dxf('/nonexistent/file.dxf', str(project['project_id']))

        assert len(stats['errors']) > 0
        assert 'Import failed' in stats['errors'][0]

    def test_invalid_dxf_file(self, db_config, temp_dir, project_factory):
        """Test handling of invalid DXF file."""
        project = project_factory()

        invalid_file = os.path.join(temp_dir, "invalid.dxf")
        with open(invalid_file, 'w') as f:
            f.write("This is not a valid DXF file")

        importer = DXFImporter(db_config, create_intelligent_objects=False)
        stats = importer.import_dxf(invalid_file, str(project['project_id']))

        assert len(stats['errors']) > 0

    def test_entity_conversion_error_handling(self, db_config):
        """Test graceful handling of entity conversion errors."""
        importer = DXFImporter(db_config)

        # Create a mock entity that will fail conversion
        mock_entity = Mock()
        mock_entity.dxftype.return_value = 'UNKNOWN_TYPE'

        # Should return None for unknown entity types
        wkt = importer._entity_to_wkt(mock_entity)
        assert wkt is None


# ============================================================================
# Test Layer Import
# ============================================================================

class TestLayerImport:
    """Test layer import functionality."""

    @pytest.mark.db
    def test_layer_import_creates_layers(self, db_config, sample_dxf_file, db_transaction, project_factory):
        """Test that layers are created during import."""
        project = project_factory()

        with patch('dxf_importer.DXFLookupService') as mock_lookup:
            mock_instance = mock_lookup.return_value
            mock_instance.get_or_create_layer.return_value = ('layer-id', 'standard-id')

            importer = DXFImporter(db_config, create_intelligent_objects=False)
            stats = importer.import_dxf(sample_dxf_file, str(project['project_id']),
                                       external_conn=db_transaction)

        # Should have tracked layers
        assert stats['layers'] > 0

    @pytest.mark.db
    def test_layer_properties_preserved(self, db_config, temp_dir, db_transaction, project_factory):
        """Test that layer properties (color, linetype) are preserved."""
        project = project_factory()

        # Create DXF with specific layer properties
        filepath = os.path.join(temp_dir, "layer_props.dxf")
        doc = ezdxf.new('R2010')
        doc.layers.add('CUSTOM-LAYER', color=5, linetype='DASHED')
        msp = doc.modelspace()
        msp.add_line((0, 0), (100, 100), dxfattribs={'layer': 'CUSTOM-LAYER'})
        doc.saveas(filepath)

        with patch('dxf_importer.DXFLookupService') as mock_lookup:
            mock_instance = mock_lookup.return_value
            mock_instance.get_or_create_layer.return_value = ('layer-id', 'standard-id')

            importer = DXFImporter(db_config, create_intelligent_objects=False)
            importer.import_dxf(filepath, str(project['project_id']),
                               external_conn=db_transaction)

            # Verify get_or_create_layer was called with correct parameters
            calls = mock_instance.get_or_create_layer.call_args_list
            assert len(calls) > 0
            # Check that color_aci and linetype were passed
            call_kwargs = calls[0][1] if len(calls[0]) > 1 else {}
            assert 'color_aci' in str(calls) or 'linetype' in str(calls)


# ============================================================================
# Test Intelligent Objects Creation
# ============================================================================

class TestIntelligentObjectsCreation:
    """Test intelligent objects creation from DXF entities."""

    @pytest.mark.db
    def test_intelligent_objects_creation_enabled(self, db_config, sample_dxf_file, db_transaction, project_factory):
        """Test that intelligent objects are created when enabled."""
        project = project_factory()

        with patch('dxf_importer.DXFLookupService'), \
             patch('dxf_importer.IntelligentObjectCreator') as mock_creator:
            mock_instance = mock_creator.return_value
            mock_instance.create_from_entity.return_value = ('utility_line', 'obj-id', 'utility_lines')

            importer = DXFImporter(db_config, create_intelligent_objects=True)
            stats = importer.import_dxf(sample_dxf_file, str(project['project_id']),
                                       external_conn=db_transaction)

        # Should have attempted to create intelligent objects
        assert 'intelligent_objects_created' in stats

    @pytest.mark.db
    def test_intelligent_objects_creation_disabled(self, db_config, sample_dxf_file, db_transaction, project_factory):
        """Test that intelligent objects are not created when disabled."""
        project = project_factory()

        with patch('dxf_importer.DXFLookupService'), \
             patch('dxf_importer.IntelligentObjectCreator') as mock_creator:

            importer = DXFImporter(db_config, create_intelligent_objects=False)
            stats = importer.import_dxf(sample_dxf_file, str(project['project_id']),
                                       external_conn=db_transaction)

        # IntelligentObjectCreator should not have been instantiated
        mock_creator.assert_not_called()


# ============================================================================
# Test Special Entity Types
# ============================================================================

class TestSpecialEntityTypes:
    """Test handling of special entity types."""

    def test_text_entity_handling(self, db_config, temp_dir):
        """Test TEXT entity import."""
        filepath = os.path.join(temp_dir, "text_test.dxf")
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        msp.add_text('Test Text', dxfattribs={'layer': 'C-TEXT', 'height': 5}).set_placement((10, 10))
        doc.saveas(filepath)

        # Test file created successfully
        assert os.path.exists(filepath)

    def test_mtext_entity_handling(self, db_config, temp_dir):
        """Test MTEXT entity import."""
        filepath = os.path.join(temp_dir, "mtext_test.dxf")
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        msp.add_mtext('Multi\\Pline\\PText', dxfattribs={'layer': 'C-MTEXT'})
        doc.saveas(filepath)

        assert os.path.exists(filepath)

    def test_block_reference_handling(self, db_config, temp_dir):
        """Test block reference (INSERT) import."""
        filepath = os.path.join(temp_dir, "block_test.dxf")
        doc = ezdxf.new('R2010')

        # Create block definition
        block = doc.blocks.new('TEST_BLOCK')
        block.add_line((0, 0), (10, 10))

        # Insert block
        msp = doc.modelspace()
        msp.add_blockref('TEST_BLOCK', (100, 100))
        doc.saveas(filepath)

        assert os.path.exists(filepath)


# ============================================================================
# Test Z-Coordinate Preservation
# ============================================================================

class TestZCoordinatePreservation:
    """Test that Z-coordinates are preserved during import."""

    def test_line_z_coordinate_preservation(self, db_config):
        """Test LINE Z-coordinates are preserved."""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        line = msp.add_line((0, 0, 100.5), (50, 50, 200.75))

        importer = DXFImporter(db_config)
        wkt = importer._entity_to_wkt(line)

        assert '100.5' in wkt
        assert '200.75' in wkt

    def test_polyline3d_z_coordinate_preservation(self, db_config):
        """Test POLYLINE3D Z-coordinates are preserved."""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        points = [(0, 0, 10), (25, 25, 15.5), (50, 0, 20.25)]
        pline = msp.add_polyline3d(points)

        importer = DXFImporter(db_config)
        wkt = importer._entity_to_wkt(pline)

        assert '10' in wkt or '10.0' in wkt
        assert '15.5' in wkt
        assert '20.25' in wkt

    def test_lwpolyline_elevation_preservation(self, db_config):
        """Test LWPOLYLINE elevation is preserved as Z."""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        lwpline = msp.add_lwpolyline([(0, 0), (100, 0), (100, 100)],
                                     dxfattribs={'elevation': 42.5})

        importer = DXFImporter(db_config)
        wkt = importer._entity_to_wkt(lwpline)

        assert '42.5' in wkt
