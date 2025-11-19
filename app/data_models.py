"""
SQLAlchemy Core Table Definitions
Declarative schema definitions for all database tables

This module defines the database schema using SQLAlchemy Core Table objects.
It provides type-safe, parameterized query building while maintaining the
flexibility and performance of Core (vs ORM).

IMPORTANT: This uses SQLAlchemy Core, NOT the ORM. This means:
- Table objects instead of Model classes
- No sessions or query() methods
- Direct SQL construction via select(), insert(), update(), delete()
- Better performance for bulk operations
- Full control over SQL generation

Usage:
    >>> from app.db_session import get_db_connection
    >>> from app.data_models import projects, survey_points
    >>>
    >>> with get_db_connection() as conn:
    >>>     # SELECT
    >>>     result = conn.execute(
    >>>         projects.select().where(projects.c.project_name == 'Demo')
    >>>     )
    >>>     rows = result.fetchall()
    >>>
    >>>     # INSERT
    >>>     conn.execute(
    >>>         projects.insert().values(
    >>>             project_name='New Project',
    >>>             project_number='PRJ-001'
    >>>         )
    >>>     )
"""

from datetime import datetime
from typing import List
import uuid

from sqlalchemy import (
    Table, Column, MetaData, ForeignKey, Index, CheckConstraint,
    String, Text, Integer, Numeric, Boolean, DateTime, Date,
    ARRAY, UUID, text
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from geoalchemy2 import Geometry

# ============================================================================
# METADATA REGISTRY
# ============================================================================

# Central metadata registry for all tables
# This is used for reflection, DDL generation, and migrations
metadata = MetaData()


# ============================================================================
# CUSTOM TYPES & HELPERS
# ============================================================================

# Standard UUID generation function (PostgreSQL-specific)
UUID_DEFAULT = text("gen_random_uuid()")

# Standard timestamp defaults
TIMESTAMP_DEFAULT = text("CURRENT_TIMESTAMP")


# ============================================================================
# CORE ENTITY TABLES
# ============================================================================

projects = Table(
    'projects',
    metadata,
    # Primary Key
    Column('project_id', UUID, primary_key=True, server_default=UUID_DEFAULT,
           comment='Unique identifier for the project'),

    # Core Attributes
    Column('project_name', String(255), nullable=False,
           comment='Display name of the project'),
    Column('project_number', String(100), nullable=True,
           comment='Client or internal project number'),
    Column('client_name', String(255), nullable=True,
           comment='Name of the client organization'),
    Column('description', Text, nullable=True,
           comment='Detailed project description'),

    # Coordinate System
    Column('default_coordinate_system_id', UUID, nullable=False,
           comment='Reference to the default coordinate system for this project'),

    # Entity Registry Integration
    Column('entity_id', UUID, nullable=True,
           comment='Link to unified entity registry for relationships'),

    # Quality & Classification
    Column('quality_score', Numeric(4, 3), nullable=True,
           comment='Data completeness and quality score (0.000-1.000)'),

    # Flexible Attributes
    Column('tags', ARRAY(Text), nullable=True,
           comment='Flexible tagging system for categorization'),
    Column('attributes', JSONB, nullable=True,
           comment='Additional flexible attributes as JSON'),

    # Full-Text Search
    Column('search_vector', TSVECTOR, nullable=True,
           comment='Generated full-text search vector'),

    # Audit Fields
    Column('created_at', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT,
           comment='Timestamp when record was created'),
    Column('updated_at', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT,
           comment='Timestamp when record was last updated'),

    # Archiving & Deletion (Two-Stage Deletion Process)
    Column('is_archived', Boolean, nullable=False, server_default=text('false'),
           comment='Soft delete flag - project is archived but not permanently deleted'),
    Column('archived_at', DateTime, nullable=True,
           comment='Timestamp when project was archived'),
    Column('archived_by', UUID, nullable=True,
           comment='User ID who archived the project'),

    # Indexes
    Index('idx_projects_name', 'project_name'),
    Index('idx_projects_number', 'project_number'),
    Index('idx_projects_entity', 'entity_id'),
    Index('idx_projects_search', 'search_vector', postgresql_using='gin'),
    Index('idx_projects_archived', 'is_archived'),

    comment='Master table for civil engineering projects'
)


survey_points = Table(
    'survey_points',
    metadata,
    # Primary Key
    Column('point_id', UUID, primary_key=True, server_default=UUID_DEFAULT,
           comment='Unique identifier for the survey point'),

    # Entity & Project Links
    Column('entity_id', UUID, nullable=True,
           comment='Link to unified entity registry'),
    Column('project_id', UUID, ForeignKey('projects.project_id', ondelete='CASCADE'),
           nullable=True, comment='Project this point belongs to'),

    # Survey Identification
    Column('point_number', String(50), nullable=False,
           comment='Survey point number (e.g., "1001", "CP-1")'),
    Column('point_description', Text, nullable=True,
           comment='Human-readable description of the point'),
    Column('point_code', String(50), nullable=True,
           comment='Feature code for the point (e.g., "IP", "MON", "CONC")'),
    Column('point_type', String(50), nullable=True,
           comment='Type classification (control, monument, feature, etc.)'),

    # Geometry (PostGIS PointZ with elevation)
    Column('geometry', Geometry('POINTZ', srid=2226), nullable=False,
           comment='3D point geometry in State Plane CA Zone 2 (EPSG:2226)'),

    # Coordinate Values (denormalized for query performance)
    Column('northing', Numeric(15, 4), nullable=True,
           comment='Northing coordinate (Y-axis)'),
    Column('easting', Numeric(15, 4), nullable=True,
           comment='Easting coordinate (X-axis)'),
    Column('elevation', Numeric(10, 4), nullable=True,
           comment='Elevation/height (Z-axis)'),

    # Coordinate System
    Column('coordinate_system', String(100), nullable=True,
           comment='Human-readable coordinate system name'),
    Column('epsg_code', String(20), nullable=True,
           comment='EPSG code for the coordinate system'),

    # Survey Metadata
    Column('survey_date', Date, nullable=True,
           comment='Date when the point was surveyed'),
    Column('surveyed_by', String(255), nullable=True,
           comment='Surveyor or survey crew identifier'),
    Column('survey_method', String(100), nullable=True,
           comment='Survey method (GPS, Total Station, Level, etc.)'),
    Column('instrument_used', String(100), nullable=True,
           comment='Instrument model/serial number'),

    # Accuracy Metrics
    Column('horizontal_accuracy', Numeric(8, 4), nullable=True,
           comment='Horizontal accuracy/precision value'),
    Column('vertical_accuracy', Numeric(8, 4), nullable=True,
           comment='Vertical accuracy/precision value'),
    Column('accuracy_units', String(20), nullable=False, server_default=text("'Feet'"),
           comment='Units for accuracy values'),
    Column('quality_code', String(50), nullable=True,
           comment='Quality/accuracy classification code'),

    # Control Point Management
    Column('is_control_point', Boolean, nullable=False, server_default=text('false'),
           comment='Flag indicating if this is a control point'),
    Column('is_active', Boolean, nullable=False, server_default=text('true'),
           comment='Flag indicating if this point is currently active'),
    Column('superseded_by', UUID, ForeignKey('survey_points.point_id'),
           nullable=True, comment='Reference to point that supersedes this one'),

    # Notes & Quality
    Column('notes', Text, nullable=True,
           comment='Additional notes about the survey point'),
    Column('quality_score', Numeric(3, 2), nullable=True, server_default=text('0.0'),
           comment='Data quality score (0.00-1.00)'),

    # Flexible Attributes
    Column('tags', ARRAY(Text), nullable=True,
           comment='Flexible tagging system'),
    Column('attributes', JSONB, nullable=True,
           comment='Additional attributes as JSON'),

    # Full-Text Search
    Column('search_vector', TSVECTOR, nullable=True,
           comment='Full-text search vector'),

    # Usage Tracking
    Column('usage_frequency', Integer, nullable=False, server_default=text('0'),
           comment='Number of times this point has been referenced'),

    # Audit Fields
    Column('created_at', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT),
    Column('updated_at', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT),

    # Indexes
    Index('idx_survey_points_project', 'project_id'),
    Index('idx_survey_points_entity', 'entity_id'),
    Index('idx_survey_points_number', 'point_number'),
    Index('idx_survey_points_code', 'point_code'),
    Index('idx_survey_points_type', 'point_type'),
    Index('idx_survey_points_geometry', 'geometry', postgresql_using='gist'),
    Index('idx_survey_points_search', 'search_vector', postgresql_using='gin'),

    comment='Survey points with 3D coordinates and metadata'
)


easements = Table(
    'easements',
    metadata,
    # Primary Key
    Column('easement_id', UUID, primary_key=True, server_default=UUID_DEFAULT,
           comment='Unique identifier for the easement'),

    # Entity & Project Links
    Column('entity_id', UUID, nullable=True,
           comment='Link to unified entity registry'),
    Column('project_id', UUID, ForeignKey('projects.project_id', ondelete='CASCADE'),
           nullable=True, comment='Project this easement belongs to'),

    # Easement Identification
    Column('easement_number', String(100), nullable=True,
           comment='Easement number or identifier'),
    Column('easement_type', String(100), nullable=True,
           comment='Type of easement (utility, access, drainage, etc.)'),
    Column('easement_purpose', Text, nullable=True,
           comment='Purpose or description of the easement'),

    # Legal Information
    Column('grantor', String(255), nullable=True,
           comment='Party granting the easement'),
    Column('grantee', String(255), nullable=True,
           comment='Party receiving the easement rights'),
    Column('recording_info', String(255), nullable=True,
           comment='Recording information (book/page, document number)'),
    Column('recorded_date', Date, nullable=True,
           comment='Date the easement was recorded'),

    # Physical Dimensions
    Column('width', Numeric(10, 4), nullable=True,
           comment='Easement width in feet'),

    # Geometry (PostGIS polygon/line with elevation)
    Column('boundary_geometry', Geometry('GEOMETRYZ', srid=2226), nullable=False,
           comment='3D boundary geometry (polygon, line, or multipolygon)'),
    Column('area_sqft', Numeric(15, 4), nullable=True,
           comment='Calculated area in square feet'),

    # Notes & Quality
    Column('notes', Text, nullable=True,
           comment='Additional notes about the easement'),
    Column('quality_score', Numeric(3, 2), nullable=True, server_default=text('0.0'),
           comment='Data quality score (0.00-1.00)'),

    # Flexible Attributes
    Column('tags', ARRAY(Text), nullable=True,
           comment='Flexible tagging system'),
    Column('attributes', JSONB, nullable=True,
           comment='Additional attributes as JSON'),

    # Full-Text Search
    Column('search_vector', TSVECTOR, nullable=True,
           comment='Full-text search vector'),

    # Usage Tracking
    Column('usage_frequency', Integer, nullable=False, server_default=text('0'),
           comment='Number of times referenced'),

    # Audit Fields
    Column('created_at', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT),
    Column('updated_at', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT),

    # Indexes
    Index('idx_easements_project', 'project_id'),
    Index('idx_easements_entity', 'entity_id'),
    Index('idx_easements_type', 'easement_type'),
    Index('idx_easements_geometry', 'boundary_geometry', postgresql_using='gist'),
    Index('idx_easements_search', 'search_vector', postgresql_using='gin'),

    comment='Easement and right-of-way records with legal and spatial data'
)


block_definitions = Table(
    'block_definitions',
    metadata,
    # Primary Key
    Column('block_id', UUID, primary_key=True, server_default=UUID_DEFAULT,
           comment='Unique identifier for the block definition'),

    # Block Identification
    Column('block_name', String(255), nullable=False,
           comment='Name of the block (from DXF BLOCK definition)'),
    Column('block_type', String(50), nullable=True,
           comment='Type classification (symbol, detail, annotation, etc.)'),
    Column('description', Text, nullable=True,
           comment='Human-readable description'),
    Column('category', String(100), nullable=True,
           comment='Category for organization (electrical, plumbing, etc.)'),

    # Insertion Point (base point of the block)
    Column('insertion_point_x', Numeric(15, 4), nullable=True,
           comment='X coordinate of block insertion point'),
    Column('insertion_point_y', Numeric(15, 4), nullable=True,
           comment='Y coordinate of block insertion point'),
    Column('insertion_point_z', Numeric(15, 4), nullable=True,
           comment='Z coordinate of block insertion point'),

    # Block Characteristics
    Column('has_attributes', Boolean, nullable=False, server_default=text('false'),
           comment='Flag indicating if block contains attribute definitions'),
    Column('is_dynamic', Boolean, nullable=False, server_default=text('false'),
           comment='Flag indicating if block is a dynamic block'),

    # Entity Registry Integration
    Column('entity_id', UUID, nullable=True,
           comment='Link to unified entity registry'),

    # Quality & Performance Metrics
    Column('quality_score', Numeric(4, 3), nullable=True,
           comment='Data completeness score (0.000-1.000)'),
    Column('usage_frequency', Integer, nullable=False, server_default=text('0'),
           comment='Number of times this block has been inserted'),
    Column('complexity_score', Numeric(4, 3), nullable=True,
           comment='Complexity metric based on entity count'),

    # Flexible Attributes
    Column('tags', ARRAY(Text), nullable=True,
           comment='Flexible tagging system'),
    Column('attributes', JSONB, nullable=True,
           comment='Additional attributes as JSON'),

    # Full-Text Search
    Column('search_vector', TSVECTOR, nullable=True,
           comment='Full-text search vector'),

    # File References
    Column('dxf_file_path', Text, nullable=True,
           comment='Path to DXF file containing block definition'),
    Column('preview_image_path', Text, nullable=True,
           comment='Path to preview image for the block'),

    # Lifecycle Management
    Column('is_active', Boolean, nullable=False, server_default=text('true'),
           comment='Flag indicating if block is active'),
    Column('superseded_by', UUID, ForeignKey('block_definitions.block_id'),
           nullable=True, comment='Reference to block that supersedes this one'),

    # Audit Fields
    Column('created_at', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT),
    Column('updated_at', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT),

    # Indexes
    Index('idx_block_definitions_name', 'block_name'),
    Index('idx_block_definitions_type', 'block_type'),
    Index('idx_block_definitions_category', 'category'),
    Index('idx_block_definitions_entity', 'entity_id'),
    Index('idx_block_definitions_search', 'search_vector', postgresql_using='gin'),

    comment='CAD block definitions (symbols, details, annotations)'
)


attribute_codes = Table(
    'attribute_codes',
    metadata,
    # Primary Key
    Column('code_id', UUID, primary_key=True, server_default=UUID_DEFAULT,
           comment='Unique identifier for the attribute code'),

    # Code Identification
    Column('code_category', String(100), nullable=False,
           comment='Category of the code (material, status, type, etc.)'),
    Column('code_value', String(100), nullable=False,
           comment='The actual code value'),
    Column('code_description', Text, nullable=False,
           comment='Human-readable description of the code'),

    # Hierarchical Organization
    Column('parent_code_id', UUID, ForeignKey('attribute_codes.code_id'),
           nullable=True, comment='Parent code for hierarchical organization'),
    Column('display_order', Integer, nullable=True,
           comment='Sort order for display'),

    # Applicability
    Column('applies_to_entity_type', String(100), nullable=True,
           comment='Entity type this code applies to (if restricted)'),

    # Lifecycle Management
    Column('is_active', Boolean, nullable=False, server_default=text('true'),
           comment='Flag indicating if code is active'),
    Column('effective_date', Date, nullable=True,
           comment='Date when code becomes effective'),
    Column('expiration_date', Date, nullable=True,
           comment='Date when code expires'),

    # Flexible Attributes
    Column('attributes', JSONB, nullable=True,
           comment='Additional code attributes as JSON'),

    # Audit Fields
    Column('created_at', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT),
    Column('updated_at', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT),

    # Indexes
    Index('idx_attribute_codes_category', 'code_category'),
    Index('idx_attribute_codes_value', 'code_value'),
    Index('idx_attribute_codes_entity_type', 'applies_to_entity_type'),
    Index('idx_attribute_codes_category_value', 'code_category', 'code_value', unique=True),

    comment='Standardized attribute codes and lookup values'
)


entity_relationships = Table(
    'entity_relationships',
    metadata,
    # Primary Key
    Column('relationship_id', UUID, primary_key=True, server_default=UUID_DEFAULT,
           comment='Unique identifier for the relationship'),

    # Relationship Triple (Subject-Predicate-Object)
    Column('subject_entity_id', UUID, nullable=False,
           comment='Source entity in the relationship'),
    Column('predicate', String(100), nullable=False,
           comment='Relationship type/verb (contains, references, connects_to, etc.)'),
    Column('object_entity_id', UUID, nullable=False,
           comment='Target entity in the relationship'),

    # Relationship Classification
    Column('relationship_type', String(50), nullable=False,
           comment='High-level relationship type (spatial, semantic, hierarchical)'),
    Column('confidence_score', Numeric(4, 3), nullable=True, server_default=text('1.0'),
           comment='Confidence in the relationship (0.000-1.000)'),

    # Relationship Flags
    Column('spatial_relationship', Boolean, nullable=False, server_default=text('false'),
           comment='Flag indicating spatial relationship'),
    Column('engineering_relationship', Boolean, nullable=False, server_default=text('false'),
           comment='Flag indicating engineering/functional relationship'),
    Column('ai_generated', Boolean, nullable=False, server_default=text('false'),
           comment='Flag indicating AI-generated relationship'),

    # Flexible Attributes
    Column('attributes', JSONB, nullable=True,
           comment='Additional relationship metadata as JSON'),

    # Audit Fields
    Column('created_at', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT),
    Column('updated_at', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT),

    # Indexes
    Index('idx_entity_relationships_subject', 'subject_entity_id'),
    Index('idx_entity_relationships_object', 'object_entity_id'),
    Index('idx_entity_relationships_predicate', 'predicate'),
    Index('idx_entity_relationships_type', 'relationship_type'),
    Index('idx_entity_relationships_triple', 'subject_entity_id', 'predicate', 'object_entity_id'),

    comment='Unified relationship graph between all entities'
)


horizontal_alignments = Table(
    'horizontal_alignments',
    metadata,
    # Primary Key
    Column('alignment_id', UUID, primary_key=True, server_default=UUID_DEFAULT,
           comment='Unique identifier for the alignment'),

    # Entity & Project Links
    Column('entity_id', UUID, nullable=True,
           comment='Link to unified entity registry'),
    Column('project_id', UUID, ForeignKey('projects.project_id', ondelete='CASCADE'),
           nullable=True, comment='Project this alignment belongs to'),

    # Alignment Identification
    Column('alignment_name', String(255), nullable=False,
           comment='Name of the alignment (road name, centerline ID, etc.)'),
    Column('description', Text, nullable=True,
           comment='Detailed description of the alignment'),
    Column('alignment_type', String(50), nullable=True,
           comment='Type of alignment (road, rail, pipeline, etc.)'),

    # Design Parameters
    Column('design_speed', Numeric(6, 2), nullable=True,
           comment='Design speed in MPH'),

    # Geometry (PostGIS LineStringZ)
    Column('alignment_geometry', Geometry('LINESTRINGZ', srid=2226), nullable=True,
           comment='3D centerline geometry'),

    # Stationing
    Column('start_station', Numeric(10, 4), nullable=True,
           comment='Starting station value'),
    Column('end_station', Numeric(10, 4), nullable=True,
           comment='Ending station value'),

    # Metadata
    Column('created_by', String(255), nullable=True,
           comment='Designer or creator identifier'),

    # Quality & Usage
    Column('quality_score', Numeric(3, 2), nullable=True, server_default=text('0.0'),
           comment='Data quality score (0.00-1.00)'),

    # Flexible Attributes
    Column('tags', ARRAY(Text), nullable=True,
           comment='Flexible tagging system'),
    Column('attributes', JSONB, nullable=True,
           comment='Additional attributes as JSON'),

    # Full-Text Search
    Column('search_vector', TSVECTOR, nullable=True,
           comment='Full-text search vector'),

    # Usage Tracking
    Column('usage_frequency', Integer, nullable=False, server_default=text('0'),
           comment='Number of times referenced'),

    # Audit Fields
    Column('created_at', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT),
    Column('updated_at', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT),

    # Indexes
    Index('idx_horizontal_alignments_project', 'project_id'),
    Index('idx_horizontal_alignments_entity', 'entity_id'),
    Index('idx_horizontal_alignments_name', 'alignment_name'),
    Index('idx_horizontal_alignments_type', 'alignment_type'),
    Index('idx_horizontal_alignments_geometry', 'alignment_geometry', postgresql_using='gist'),
    Index('idx_horizontal_alignments_search', 'search_vector', postgresql_using='gin'),

    comment='Horizontal alignment definitions for civil design'
)


drawing_hatches = Table(
    'drawing_hatches',
    metadata,
    # Primary Key
    Column('hatch_id', UUID, primary_key=True, server_default=UUID_DEFAULT,
           comment='Unique identifier for the hatch'),

    # Project Links
    Column('layer_id', UUID, nullable=True,
           comment='Layer this hatch belongs to'),
    Column('project_id', UUID, ForeignKey('projects.project_id', ondelete='CASCADE'),
           nullable=True, comment='Project this hatch belongs to'),

    # Pattern Reference
    Column('pattern_id', UUID, nullable=True,
           comment='Reference to hatch pattern definition'),
    Column('hatch_pattern', String(255), nullable=True,
           comment='Name of the hatch pattern (ANSI31, SOLID, etc.)'),

    # Geometry (PostGIS PolygonZ)
    Column('boundary_geometry', Geometry('POLYGONZ', srid=2226), nullable=False,
           comment='3D boundary polygon for the hatch'),

    # Pattern Parameters
    Column('hatch_scale', Numeric(10, 4), nullable=True, server_default=text('1.0'),
           comment='Scale factor for the hatch pattern'),
    Column('hatch_angle', Numeric(10, 4), nullable=True, server_default=text('0.0'),
           comment='Rotation angle for the pattern (degrees)'),

    # DXF Reference
    Column('dxf_handle', String(100), nullable=True,
           comment='Original DXF handle for traceability'),

    # Quality & Usage
    Column('quality_score', Numeric(3, 2), nullable=True, server_default=text('0.5'),
           comment='Data quality score (0.00-1.00)'),

    # Flexible Attributes
    Column('tags', ARRAY(Text), nullable=True,
           comment='Flexible tagging system'),
    Column('attributes', JSONB, nullable=True,
           comment='Additional attributes as JSON'),

    # Full-Text Search
    Column('search_vector', TSVECTOR, nullable=True,
           comment='Full-text search vector'),

    # Audit Fields
    Column('created_at', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT),
    Column('updated_at', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT),

    # Indexes
    Index('idx_drawing_hatches_project', 'project_id'),
    Index('idx_drawing_hatches_layer', 'layer_id'),
    Index('idx_drawing_hatches_pattern', 'hatch_pattern'),
    Index('idx_drawing_hatches_geometry', 'boundary_geometry', postgresql_using='gist'),

    comment='Hatch patterns and area fills from CAD drawings'
)


# ============================================================================
# AUDIT & LOGGING TABLES
# ============================================================================

audit_log = Table(
    'audit_log',
    metadata,
    # Primary Key
    Column('log_id', UUID, primary_key=True, server_default=UUID_DEFAULT,
           comment='Unique identifier for the audit log entry'),

    # Action Details
    Column('table_name', String(100), nullable=False,
           comment='Name of the table that was modified'),
    Column('record_id', UUID, nullable=False,
           comment='ID of the record that was modified'),
    Column('action', String(20), nullable=False,
           comment='Action performed (INSERT, UPDATE, DELETE)'),

    # User & Timestamp
    Column('user_id', UUID, nullable=True,
           comment='User who performed the action'),
    Column('username', String(255), nullable=True,
           comment='Username who performed the action'),
    Column('action_timestamp', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT,
           comment='When the action occurred'),

    # Change Details
    Column('old_values', JSONB, nullable=True,
           comment='Previous values before change (JSON)'),
    Column('new_values', JSONB, nullable=True,
           comment='New values after change (JSON)'),

    # Context
    Column('ip_address', String(45), nullable=True,
           comment='IP address of the user'),
    Column('user_agent', String(500), nullable=True,
           comment='User agent string'),

    # Indexes
    Index('idx_audit_log_table_record', 'table_name', 'record_id'),
    Index('idx_audit_log_timestamp', 'action_timestamp'),
    Index('idx_audit_log_user', 'user_id'),
    Index('idx_audit_log_action', 'action'),

    comment='Audit trail for all data modifications'
)


ai_query_cache = Table(
    'ai_query_cache',
    metadata,
    # Primary Key
    Column('cache_id', UUID, primary_key=True, server_default=UUID_DEFAULT,
           comment='Unique identifier for the cache entry'),

    # Query Information
    Column('query_hash', String(64), nullable=False, unique=True,
           comment='SHA-256 hash of the query for deduplication'),
    Column('query_text', Text, nullable=False,
           comment='Original natural language query'),
    Column('query_type', String(50), nullable=True,
           comment='Type of query (search, analysis, export, etc.)'),

    # Results
    Column('result_sql', Text, nullable=True,
           comment='Generated SQL query'),
    Column('result_count', Integer, nullable=True,
           comment='Number of results returned'),
    Column('result_data', JSONB, nullable=True,
           comment='Cached result data (if applicable)'),

    # Performance Metrics
    Column('execution_time_ms', Integer, nullable=True,
           comment='Query execution time in milliseconds'),
    Column('cache_hit_count', Integer, nullable=False, server_default=text('0'),
           comment='Number of times this cache entry was reused'),

    # Context
    Column('user_id', UUID, nullable=True,
           comment='User who initiated the query'),
    Column('project_id', UUID, nullable=True,
           comment='Project context for the query'),

    # Expiration
    Column('created_at', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT,
           comment='When the cache entry was created'),
    Column('last_accessed_at', DateTime, nullable=False, server_default=TIMESTAMP_DEFAULT,
           comment='When the cache entry was last accessed'),
    Column('expires_at', DateTime, nullable=True,
           comment='When the cache entry expires'),

    # Indexes
    Index('idx_ai_query_cache_hash', 'query_hash'),
    Index('idx_ai_query_cache_type', 'query_type'),
    Index('idx_ai_query_cache_user', 'user_id'),
    Index('idx_ai_query_cache_project', 'project_id'),
    Index('idx_ai_query_cache_expires', 'expires_at'),

    comment='Cache for AI-generated queries and results'
)


# ============================================================================
# TABLE REGISTRY
# ============================================================================

# Export all table objects for easy import
__all__ = [
    'metadata',
    'projects',
    'survey_points',
    'easements',
    'block_definitions',
    'attribute_codes',
    'entity_relationships',
    'horizontal_alignments',
    'drawing_hatches',
    'audit_log',
    'ai_query_cache',
]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_table_by_name(table_name: str) -> Table:
    """
    Get a Table object by name.

    Args:
        table_name: Name of the table

    Returns:
        Table object

    Raises:
        KeyError: If table does not exist

    Example:
        >>> from app.data_models import get_table_by_name
        >>> projects = get_table_by_name('projects')
    """
    return metadata.tables[table_name]


def get_all_table_names() -> List[str]:
    """
    Get list of all table names in the metadata.

    Returns:
        List of table names

    Example:
        >>> from app.data_models import get_all_table_names
        >>> tables = get_all_table_names()
        >>> print(f"Database has {len(tables)} tables")
    """
    return list(metadata.tables.keys())


def create_all_tables(engine):
    """
    Create all tables in the database.

    WARNING: This will create tables but NOT handle migrations.
    For production, use Alembic migrations instead.

    Args:
        engine: SQLAlchemy engine

    Example:
        >>> from app.db_session import get_engine
        >>> from app.data_models import create_all_tables
        >>> engine = get_engine()
        >>> create_all_tables(engine)
    """
    metadata.create_all(engine)


def drop_all_tables(engine):
    """
    Drop all tables in the database.

    WARNING: This is DESTRUCTIVE and will delete all data!
    Only use for testing or development.

    Args:
        engine: SQLAlchemy engine

    Example:
        >>> from app.db_session import get_engine
        >>> from app.data_models import drop_all_tables
        >>> engine = get_engine()
        >>> drop_all_tables(engine)  # DANGER!
    """
    metadata.drop_all(engine)
