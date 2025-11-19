"""initial_schema

Revision ID: 0001
Revises:
Create Date: 2025-01-18 20:00:00.000000

This migration represents the initial database schema as defined in
app/data_models.py. It creates all tables WITHOUT the Phase 10 archiving
columns (is_archived, archived_at, archived_by).

IMPORTANT: This migration assumes a fresh database. If you have an existing
database, you may need to use `alembic stamp 0001` to mark this as applied
without running it.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from geoalchemy2 import Geometry


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create initial database schema.

    This includes:
    - All core tables (projects, survey_points, easements, etc.)
    - All indexes and constraints
    - PostGIS extension (if not already enabled)

    NOTE: This does NOT include the Phase 10 archiving columns yet.
    """

    # Enable PostGIS extension (safe to run if already enabled)
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ========================================================================
    # PROJECTS TABLE (without archiving columns)
    # ========================================================================
    op.create_table(
        'projects',
        sa.Column('project_id', sa.UUID(), server_default=text('gen_random_uuid()'), nullable=False,
                  comment='Unique identifier for the project'),
        sa.Column('project_name', sa.String(length=255), nullable=False,
                  comment='Display name of the project'),
        sa.Column('project_number', sa.String(length=100), nullable=True,
                  comment='Client or internal project number'),
        sa.Column('client_name', sa.String(length=255), nullable=True,
                  comment='Name of the client organization'),
        sa.Column('description', sa.Text(), nullable=True,
                  comment='Detailed project description'),
        sa.Column('default_coordinate_system_id', sa.UUID(), nullable=False,
                  comment='Reference to the default coordinate system for this project'),
        sa.Column('entity_id', sa.UUID(), nullable=True,
                  comment='Link to unified entity registry for relationships'),
        sa.Column('quality_score', sa.Numeric(precision=4, scale=3), nullable=True,
                  comment='Data completeness and quality score (0.000-1.000)'),
        sa.Column('tags', sa.ARRAY(sa.Text()), nullable=True,
                  comment='Flexible tagging system for categorization'),
        sa.Column('attributes', sa.Text(), nullable=True,
                  comment='Additional flexible attributes as JSON'),
        sa.Column('search_vector', sa.Text(), nullable=True,
                  comment='Generated full-text search vector'),
        sa.Column('created_at', sa.DateTime(), server_default=text('CURRENT_TIMESTAMP'), nullable=False,
                  comment='Timestamp when record was created'),
        sa.Column('updated_at', sa.DateTime(), server_default=text('CURRENT_TIMESTAMP'), nullable=False,
                  comment='Timestamp when record was last updated'),
        sa.PrimaryKeyConstraint('project_id'),
        comment='Master table for civil engineering projects'
    )

    # Create indexes for projects table
    op.create_index('idx_projects_name', 'projects', ['project_name'])
    op.create_index('idx_projects_number', 'projects', ['project_number'])
    op.create_index('idx_projects_entity', 'projects', ['entity_id'])
    op.create_index('idx_projects_search', 'projects', ['search_vector'], postgresql_using='gin')

    # ========================================================================
    # SURVEY_POINTS TABLE
    # ========================================================================
    op.create_table(
        'survey_points',
        sa.Column('point_id', sa.UUID(), server_default=text('gen_random_uuid()'), nullable=False,
                  comment='Unique identifier for the survey point'),
        sa.Column('entity_id', sa.UUID(), nullable=True,
                  comment='Link to unified entity registry'),
        sa.Column('project_id', sa.UUID(), nullable=True,
                  comment='Project this point belongs to'),
        sa.Column('point_number', sa.String(length=50), nullable=False,
                  comment='Survey point number (e.g., "1001", "CP-1")'),
        sa.Column('point_description', sa.Text(), nullable=True,
                  comment='Human-readable description of the point'),
        sa.Column('point_code', sa.String(length=50), nullable=True,
                  comment='Feature code for the point (e.g., "IP", "MON", "CONC")'),
        sa.Column('point_type', sa.String(length=50), nullable=True,
                  comment='Type classification (control, monument, feature, etc.)'),
        sa.Column('geometry', Geometry('POINTZ', srid=2226), nullable=False,
                  comment='3D point geometry in State Plane CA Zone 2 (EPSG:2226)'),
        sa.Column('northing', sa.Numeric(precision=15, scale=4), nullable=True,
                  comment='Northing coordinate (Y-axis)'),
        sa.Column('easting', sa.Numeric(precision=15, scale=4), nullable=True,
                  comment='Easting coordinate (X-axis)'),
        sa.Column('elevation', sa.Numeric(precision=10, scale=4), nullable=True,
                  comment='Elevation/height (Z-axis)'),
        sa.Column('coordinate_system', sa.String(length=100), nullable=True,
                  comment='Human-readable coordinate system name'),
        sa.Column('epsg_code', sa.String(length=20), nullable=True,
                  comment='EPSG code for the coordinate system'),
        sa.Column('survey_date', sa.Date(), nullable=True,
                  comment='Date when the point was surveyed'),
        sa.Column('surveyed_by', sa.String(length=255), nullable=True,
                  comment='Surveyor or survey crew identifier'),
        sa.Column('survey_method', sa.String(length=100), nullable=True,
                  comment='Survey method (GPS, Total Station, Level, etc.)'),
        sa.Column('instrument_used', sa.String(length=100), nullable=True,
                  comment='Instrument model/serial number'),
        sa.Column('horizontal_accuracy', sa.Numeric(precision=8, scale=4), nullable=True,
                  comment='Horizontal accuracy/precision value'),
        sa.Column('vertical_accuracy', sa.Numeric(precision=8, scale=4), nullable=True,
                  comment='Vertical accuracy/precision value'),
        sa.Column('accuracy_units', sa.String(length=20), server_default=text("'Feet'"), nullable=False,
                  comment='Units for accuracy values'),
        sa.Column('quality_code', sa.String(length=50), nullable=True,
                  comment='Quality/accuracy classification code'),
        sa.Column('is_control_point', sa.Boolean(), server_default=text('false'), nullable=False,
                  comment='Flag indicating if this is a control point'),
        sa.Column('is_active', sa.Boolean(), server_default=text('true'), nullable=False,
                  comment='Flag indicating if this point is currently active'),
        sa.Column('superseded_by', sa.UUID(), nullable=True,
                  comment='Reference to point that supersedes this one'),
        sa.Column('notes', sa.Text(), nullable=True,
                  comment='Additional notes about the survey point'),
        sa.Column('quality_score', sa.Numeric(precision=3, scale=2), server_default=text('0.0'), nullable=True,
                  comment='Data quality score (0.00-1.00)'),
        sa.Column('tags', sa.ARRAY(sa.Text()), nullable=True,
                  comment='Flexible tagging system'),
        sa.Column('attributes', sa.Text(), nullable=True,
                  comment='Additional attributes as JSON'),
        sa.Column('search_vector', sa.Text(), nullable=True,
                  comment='Full-text search vector'),
        sa.Column('usage_frequency', sa.Integer(), server_default=text('0'), nullable=False,
                  comment='Number of times this point has been referenced'),
        sa.Column('created_at', sa.DateTime(), server_default=text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['superseded_by'], ['survey_points.point_id']),
        sa.PrimaryKeyConstraint('point_id'),
        comment='Survey points with 3D coordinates and metadata'
    )

    # Create indexes for survey_points table
    op.create_index('idx_survey_points_project', 'survey_points', ['project_id'])
    op.create_index('idx_survey_points_entity', 'survey_points', ['entity_id'])
    op.create_index('idx_survey_points_number', 'survey_points', ['point_number'])
    op.create_index('idx_survey_points_code', 'survey_points', ['point_code'])
    op.create_index('idx_survey_points_type', 'survey_points', ['point_type'])
    op.create_index('idx_survey_points_geometry', 'survey_points', ['geometry'], postgresql_using='gist')
    op.create_index('idx_survey_points_search', 'survey_points', ['search_vector'], postgresql_using='gin')

    # ========================================================================
    # EASEMENTS TABLE
    # ========================================================================
    op.create_table(
        'easements',
        sa.Column('easement_id', sa.UUID(), server_default=text('gen_random_uuid()'), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=True),
        sa.Column('project_id', sa.UUID(), nullable=True),
        sa.Column('easement_number', sa.String(length=100), nullable=True),
        sa.Column('easement_type', sa.String(length=100), nullable=True),
        sa.Column('easement_purpose', sa.Text(), nullable=True),
        sa.Column('grantor', sa.String(length=255), nullable=True),
        sa.Column('grantee', sa.String(length=255), nullable=True),
        sa.Column('recording_info', sa.String(length=255), nullable=True),
        sa.Column('recorded_date', sa.Date(), nullable=True),
        sa.Column('width', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('boundary_geometry', Geometry('GEOMETRYZ', srid=2226), nullable=False),
        sa.Column('area_sqft', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('quality_score', sa.Numeric(precision=3, scale=2), server_default=text('0.0'), nullable=True),
        sa.Column('tags', sa.ARRAY(sa.Text()), nullable=True),
        sa.Column('attributes', sa.Text(), nullable=True),
        sa.Column('search_vector', sa.Text(), nullable=True),
        sa.Column('usage_frequency', sa.Integer(), server_default=text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('easement_id'),
        comment='Easement and right-of-way records with legal and spatial data'
    )

    op.create_index('idx_easements_project', 'easements', ['project_id'])
    op.create_index('idx_easements_entity', 'easements', ['entity_id'])
    op.create_index('idx_easements_type', 'easements', ['easement_type'])
    op.create_index('idx_easements_geometry', 'easements', ['boundary_geometry'], postgresql_using='gist')
    op.create_index('idx_easements_search', 'easements', ['search_vector'], postgresql_using='gin')

    # ========================================================================
    # BLOCK_DEFINITIONS TABLE
    # ========================================================================
    op.create_table(
        'block_definitions',
        sa.Column('block_id', sa.UUID(), server_default=text('gen_random_uuid()'), nullable=False),
        sa.Column('block_name', sa.String(length=255), nullable=False),
        sa.Column('block_type', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('insertion_point_x', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('insertion_point_y', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('insertion_point_z', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('has_attributes', sa.Boolean(), server_default=text('false'), nullable=False),
        sa.Column('is_dynamic', sa.Boolean(), server_default=text('false'), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=True),
        sa.Column('quality_score', sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column('usage_frequency', sa.Integer(), server_default=text('0'), nullable=False),
        sa.Column('complexity_score', sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column('tags', sa.ARRAY(sa.Text()), nullable=True),
        sa.Column('attributes', sa.Text(), nullable=True),
        sa.Column('search_vector', sa.Text(), nullable=True),
        sa.Column('dxf_file_path', sa.Text(), nullable=True),
        sa.Column('preview_image_path', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=text('true'), nullable=False),
        sa.Column('superseded_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['superseded_by'], ['block_definitions.block_id']),
        sa.PrimaryKeyConstraint('block_id'),
        comment='CAD block definitions (symbols, details, annotations)'
    )

    op.create_index('idx_block_definitions_name', 'block_definitions', ['block_name'])
    op.create_index('idx_block_definitions_type', 'block_definitions', ['block_type'])
    op.create_index('idx_block_definitions_category', 'block_definitions', ['category'])
    op.create_index('idx_block_definitions_entity', 'block_definitions', ['entity_id'])
    op.create_index('idx_block_definitions_search', 'block_definitions', ['search_vector'], postgresql_using='gin')

    # ========================================================================
    # ATTRIBUTE_CODES TABLE
    # ========================================================================
    op.create_table(
        'attribute_codes',
        sa.Column('code_id', sa.UUID(), server_default=text('gen_random_uuid()'), nullable=False),
        sa.Column('code_category', sa.String(length=100), nullable=False),
        sa.Column('code_value', sa.String(length=100), nullable=False),
        sa.Column('code_description', sa.Text(), nullable=False),
        sa.Column('parent_code_id', sa.UUID(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('applies_to_entity_type', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=text('true'), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=True),
        sa.Column('expiration_date', sa.Date(), nullable=True),
        sa.Column('attributes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['parent_code_id'], ['attribute_codes.code_id']),
        sa.PrimaryKeyConstraint('code_id'),
        comment='Standardized attribute codes and lookup values'
    )

    op.create_index('idx_attribute_codes_category', 'attribute_codes', ['code_category'])
    op.create_index('idx_attribute_codes_value', 'attribute_codes', ['code_value'])
    op.create_index('idx_attribute_codes_entity_type', 'attribute_codes', ['applies_to_entity_type'])
    op.create_index('idx_attribute_codes_category_value', 'attribute_codes', ['code_category', 'code_value'], unique=True)

    # ========================================================================
    # ENTITY_RELATIONSHIPS TABLE
    # ========================================================================
    op.create_table(
        'entity_relationships',
        sa.Column('relationship_id', sa.UUID(), server_default=text('gen_random_uuid()'), nullable=False),
        sa.Column('subject_entity_id', sa.UUID(), nullable=False),
        sa.Column('predicate', sa.String(length=100), nullable=False),
        sa.Column('object_entity_id', sa.UUID(), nullable=False),
        sa.Column('relationship_type', sa.String(length=50), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=4, scale=3), server_default=text('1.0'), nullable=True),
        sa.Column('spatial_relationship', sa.Boolean(), server_default=text('false'), nullable=False),
        sa.Column('engineering_relationship', sa.Boolean(), server_default=text('false'), nullable=False),
        sa.Column('ai_generated', sa.Boolean(), server_default=text('false'), nullable=False),
        sa.Column('attributes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('relationship_id'),
        comment='Unified relationship graph between all entities'
    )

    op.create_index('idx_entity_relationships_subject', 'entity_relationships', ['subject_entity_id'])
    op.create_index('idx_entity_relationships_object', 'entity_relationships', ['object_entity_id'])
    op.create_index('idx_entity_relationships_predicate', 'entity_relationships', ['predicate'])
    op.create_index('idx_entity_relationships_type', 'entity_relationships', ['relationship_type'])
    op.create_index('idx_entity_relationships_triple', 'entity_relationships', ['subject_entity_id', 'predicate', 'object_entity_id'])

    # ========================================================================
    # HORIZONTAL_ALIGNMENTS TABLE
    # ========================================================================
    op.create_table(
        'horizontal_alignments',
        sa.Column('alignment_id', sa.UUID(), server_default=text('gen_random_uuid()'), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=True),
        sa.Column('project_id', sa.UUID(), nullable=True),
        sa.Column('alignment_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('alignment_type', sa.String(length=50), nullable=True),
        sa.Column('design_speed', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('alignment_geometry', Geometry('LINESTRINGZ', srid=2226), nullable=True),
        sa.Column('start_station', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('end_station', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('quality_score', sa.Numeric(precision=3, scale=2), server_default=text('0.0'), nullable=True),
        sa.Column('tags', sa.ARRAY(sa.Text()), nullable=True),
        sa.Column('attributes', sa.Text(), nullable=True),
        sa.Column('search_vector', sa.Text(), nullable=True),
        sa.Column('usage_frequency', sa.Integer(), server_default=text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('alignment_id'),
        comment='Horizontal alignment definitions for civil design'
    )

    op.create_index('idx_horizontal_alignments_project', 'horizontal_alignments', ['project_id'])
    op.create_index('idx_horizontal_alignments_entity', 'horizontal_alignments', ['entity_id'])
    op.create_index('idx_horizontal_alignments_name', 'horizontal_alignments', ['alignment_name'])
    op.create_index('idx_horizontal_alignments_type', 'horizontal_alignments', ['alignment_type'])
    op.create_index('idx_horizontal_alignments_geometry', 'horizontal_alignments', ['alignment_geometry'], postgresql_using='gist')
    op.create_index('idx_horizontal_alignments_search', 'horizontal_alignments', ['search_vector'], postgresql_using='gin')

    # ========================================================================
    # DRAWING_HATCHES TABLE
    # ========================================================================
    op.create_table(
        'drawing_hatches',
        sa.Column('hatch_id', sa.UUID(), server_default=text('gen_random_uuid()'), nullable=False),
        sa.Column('layer_id', sa.UUID(), nullable=True),
        sa.Column('project_id', sa.UUID(), nullable=True),
        sa.Column('pattern_id', sa.UUID(), nullable=True),
        sa.Column('hatch_pattern', sa.String(length=255), nullable=True),
        sa.Column('boundary_geometry', Geometry('POLYGONZ', srid=2226), nullable=False),
        sa.Column('hatch_scale', sa.Numeric(precision=10, scale=4), server_default=text('1.0'), nullable=True),
        sa.Column('hatch_angle', sa.Numeric(precision=10, scale=4), server_default=text('0.0'), nullable=True),
        sa.Column('dxf_handle', sa.String(length=100), nullable=True),
        sa.Column('quality_score', sa.Numeric(precision=3, scale=2), server_default=text('0.5'), nullable=True),
        sa.Column('tags', sa.ARRAY(sa.Text()), nullable=True),
        sa.Column('attributes', sa.Text(), nullable=True),
        sa.Column('search_vector', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('hatch_id'),
        comment='Hatch patterns and area fills from CAD drawings'
    )

    op.create_index('idx_drawing_hatches_project', 'drawing_hatches', ['project_id'])
    op.create_index('idx_drawing_hatches_layer', 'drawing_hatches', ['layer_id'])
    op.create_index('idx_drawing_hatches_pattern', 'drawing_hatches', ['hatch_pattern'])
    op.create_index('idx_drawing_hatches_geometry', 'drawing_hatches', ['boundary_geometry'], postgresql_using='gist')

    # ========================================================================
    # AUDIT_LOG TABLE
    # ========================================================================
    op.create_table(
        'audit_log',
        sa.Column('log_id', sa.UUID(), server_default=text('gen_random_uuid()'), nullable=False),
        sa.Column('table_name', sa.String(length=100), nullable=False),
        sa.Column('record_id', sa.UUID(), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('action_timestamp', sa.DateTime(), server_default=text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('old_values', sa.Text(), nullable=True),
        sa.Column('new_values', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('log_id'),
        comment='Audit trail for all data modifications'
    )

    op.create_index('idx_audit_log_table_record', 'audit_log', ['table_name', 'record_id'])
    op.create_index('idx_audit_log_timestamp', 'audit_log', ['action_timestamp'])
    op.create_index('idx_audit_log_user', 'audit_log', ['user_id'])
    op.create_index('idx_audit_log_action', 'audit_log', ['action'])

    # ========================================================================
    # AI_QUERY_CACHE TABLE
    # ========================================================================
    op.create_table(
        'ai_query_cache',
        sa.Column('cache_id', sa.UUID(), server_default=text('gen_random_uuid()'), nullable=False),
        sa.Column('query_hash', sa.String(length=64), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('query_type', sa.String(length=50), nullable=True),
        sa.Column('result_sql', sa.Text(), nullable=True),
        sa.Column('result_count', sa.Integer(), nullable=True),
        sa.Column('result_data', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('cache_hit_count', sa.Integer(), server_default=text('0'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('project_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(), server_default=text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('cache_id'),
        sa.UniqueConstraint('query_hash'),
        comment='Cache for AI-generated queries and results'
    )

    op.create_index('idx_ai_query_cache_hash', 'ai_query_cache', ['query_hash'])
    op.create_index('idx_ai_query_cache_type', 'ai_query_cache', ['query_type'])
    op.create_index('idx_ai_query_cache_user', 'ai_query_cache', ['user_id'])
    op.create_index('idx_ai_query_cache_project', 'ai_query_cache', ['project_id'])
    op.create_index('idx_ai_query_cache_expires', 'ai_query_cache', ['expires_at'])


def downgrade() -> None:
    """
    Drop all tables created by this migration.

    WARNING: This will delete all data!
    """
    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_table('ai_query_cache')
    op.drop_table('audit_log')
    op.drop_table('drawing_hatches')
    op.drop_table('horizontal_alignments')
    op.drop_table('entity_relationships')
    op.drop_table('attribute_codes')
    op.drop_table('block_definitions')
    op.drop_table('easements')
    op.drop_table('survey_points')
    op.drop_table('projects')

    # Note: We do NOT drop PostGIS extension as it may be used by other databases
