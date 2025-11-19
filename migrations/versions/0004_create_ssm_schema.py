"""Create SSM (Survey Spatial Management) Schema

Revision ID: 0004
Revises: 0003
Create Date: 2025-11-18 23:00:00.000000

Phase 21: Deploy Survey Spatial Management (SSM) Schema

SCOPE:
This migration creates a new 'ssm' schema and deploys four tables for managing
survey feature codes, their attributes, CAD mappings, and automation rulesets.

TABLES CREATED:
┌──────────────────────┬──────────┬───────────────────────────────────────────┐
│ Table                │ Columns  │ Purpose                                   │
├──────────────────────┼──────────┼───────────────────────────────────────────┤
│ ssm_feature_codes    │ 5        │ Master registry of survey feature codes   │
│ ssm_attributes       │ 5        │ Attribute definitions per feature code    │
│ ssm_mappings         │ 9        │ Conditional CAD mapping logic (JSONB)     │
│ ssm_rulesets         │ 3        │ Automation rule configurations            │
└──────────────────────┴──────────┴───────────────────────────────────────────┘

KEY FEATURES:
✓ Dedicated 'ssm' schema for logical separation
✓ JSONB columns for flexible conditional logic
✓ Foreign key constraints for data integrity
✓ Unique constraints on feature codes and attribute names
✓ Indexes on frequently queried columns

SAFETY NOTES:
✓ Creates new schema - no risk to existing data
✓ PostgreSQL transactional DDL (can rollback)
✓ No dependencies on existing tables
✓ Safe to run on production databases

USAGE EXAMPLE:
After this migration, you can:
1. Insert feature codes: INSERT INTO ssm.ssm_feature_codes (code, description, geometry_type)
2. Define attributes: INSERT INTO ssm.ssm_attributes (feature_code_id, name, data_type, is_required)
3. Create mappings: INSERT INTO ssm.ssm_mappings (feature_code_id, name, conditions, cad_layer, cad_block)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create the SSM schema and deploy all SSM tables.

    This migration:
    1. Creates the 'ssm' schema
    2. Creates ssm_feature_codes table (master feature code registry)
    3. Creates ssm_attributes table (attribute definitions)
    4. Creates ssm_mappings table (conditional CAD mapping logic)
    5. Creates ssm_rulesets table (automation rule configurations)
    """

    print("=" * 80)
    print("Phase 21: Creating SSM (Survey Spatial Management) Schema")
    print("=" * 80)
    print("")

    # ========================================================================
    # PART 1: Create the 'ssm' schema
    # ========================================================================

    print("PART 1: Creating 'ssm' schema...")
    print("-" * 80)

    op.execute("CREATE SCHEMA IF NOT EXISTS ssm")
    print("  ✓ Schema 'ssm' created")
    print("")

    # ========================================================================
    # PART 2: Create ssm_feature_codes table
    # ========================================================================

    print("PART 2: Creating ssm_feature_codes table...")
    print("-" * 80)

    op.create_table(
        'ssm_feature_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('geometry_type', sa.String(length=50), nullable=True, server_default='Point', comment='Point, Line, or Polygon'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('true')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_ssm_feature_codes')),
        sa.UniqueConstraint('code', name='uq_ssm_code'),
        schema='ssm',
        comment='Master list of survey feature codes (e.g., SDMH, WV).'
    )

    op.create_index(
        op.f('ix_ssm_ssm_feature_codes_code'),
        'ssm_feature_codes',
        ['code'],
        unique=False,
        schema='ssm'
    )

    print("  ✓ Table 'ssm.ssm_feature_codes' created with 5 columns")
    print("  ✓ Index on 'code' column created")
    print("  ✓ Unique constraint 'uq_ssm_code' created")
    print("")

    # ========================================================================
    # PART 3: Create ssm_attributes table
    # ========================================================================

    print("PART 3: Creating ssm_attributes table...")
    print("-" * 80)

    op.create_table(
        'ssm_attributes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('feature_code_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('data_type', sa.String(length=50), nullable=True, server_default='Text', comment='Text, Numeric, Boolean, Date'),
        sa.Column('is_required', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.ForeignKeyConstraint(['feature_code_id'], ['ssm.ssm_feature_codes.id'], name=op.f('fk_ssm_attributes_feature_code_id_ssm_feature_codes'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_ssm_attributes')),
        sa.UniqueConstraint('feature_code_id', 'name', name='uq_ssm_attr_name'),
        schema='ssm',
        comment='Defines the attributes collected for each feature code.'
    )

    print("  ✓ Table 'ssm.ssm_attributes' created with 5 columns")
    print("  ✓ Foreign key to 'ssm.ssm_feature_codes' created")
    print("  ✓ Unique constraint 'uq_ssm_attr_name' on (feature_code_id, name)")
    print("")

    # ========================================================================
    # PART 4: Create ssm_mappings table
    # ========================================================================

    print("PART 4: Creating ssm_mappings table...")
    print("-" * 80)

    op.create_table(
        'ssm_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('feature_code_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False, comment='User-friendly name for the mapping (e.g., "48-inch Concrete MH")'),
        sa.Column('conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}', comment='Conditional logic JSON: {"SIZE": {"operator": ">=", "value": "48IN"}}'),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='100', comment='Higher number wins tie-breaks.'),
        sa.Column('cad_layer', sa.String(length=100), nullable=False),
        sa.Column('cad_block', sa.String(length=100), nullable=False),
        sa.Column('cad_label_style', sa.String(length=100), nullable=True),
        sa.Column('ruleset_id', sa.Integer(), nullable=True, comment='Foreign key to the automation ruleset.'),
        sa.ForeignKeyConstraint(['feature_code_id'], ['ssm.ssm_feature_codes.id'], name=op.f('fk_ssm_mappings_feature_code_id_ssm_feature_codes'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_ssm_mappings')),
        schema='ssm',
        comment='Defines the conditional relationship between feature attributes and CAD components.'
    )

    op.create_index(
        op.f('ix_ssm_ssm_mappings_priority'),
        'ssm_mappings',
        ['priority'],
        unique=False,
        schema='ssm'
    )

    print("  ✓ Table 'ssm.ssm_mappings' created with 9 columns")
    print("  ✓ JSONB column 'conditions' for conditional logic")
    print("  ✓ Foreign key to 'ssm.ssm_feature_codes' created")
    print("  ✓ Index on 'priority' column created")
    print("")

    # ========================================================================
    # PART 5: Create ssm_rulesets table
    # ========================================================================

    print("PART 5: Creating ssm_rulesets table...")
    print("-" * 80)

    op.create_table(
        'ssm_rulesets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}', comment='Stores the complex rules configuration (e.g., label template, auto-connect logic flags)'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_ssm_rulesets')),
        schema='ssm',
        comment='Defines sets of automation rules for mappings.'
    )

    print("  ✓ Table 'ssm.ssm_rulesets' created with 3 columns")
    print("  ✓ JSONB column 'configuration' for flexible rule definitions")
    print("")

    # ========================================================================
    # COMPLETION SUMMARY
    # ========================================================================

    print("=" * 80)
    print("✓ Phase 21 Migration Completed Successfully!")
    print("=" * 80)
    print("")
    print("SUMMARY:")
    print("  • Schema 'ssm' created")
    print("  • ssm_feature_codes: 5 columns (master feature registry)")
    print("  • ssm_attributes: 5 columns (attribute definitions)")
    print("  • ssm_mappings: 9 columns (conditional CAD logic)")
    print("  • ssm_rulesets: 3 columns (automation configurations)")
    print("  • TOTAL: 4 tables, 22 columns created")
    print("")
    print("NEXT STEPS:")
    print("  1. Populate ssm_feature_codes with standard survey codes")
    print("  2. Define attributes for each feature code in ssm_attributes")
    print("  3. Create conditional mappings in ssm_mappings")
    print("  4. Test JSONB querying: SELECT * FROM ssm.ssm_mappings WHERE conditions @> '{\"SIZE\": {}}'::jsonb")
    print("  5. Consider adding GIN indexes on JSONB columns for performance")
    print("")


def downgrade() -> None:
    """
    Rollback the SSM schema creation.

    This will:
    1. Drop all SSM tables (in reverse order to respect foreign keys)
    2. Drop the 'ssm' schema

    WARNING: This will permanently delete all SSM data.
    """

    print("=" * 80)
    print("ROLLING BACK: Dropping SSM Schema and Tables")
    print("=" * 80)
    print("")
    print("⚠ WARNING: This will permanently delete all SSM data")
    print("")

    # ========================================================================
    # Drop tables in reverse order to respect foreign key constraints
    # ========================================================================

    print("Dropping SSM tables...")
    print("-" * 80)

    op.drop_table('ssm_rulesets', schema='ssm')
    print("  → Dropped 'ssm.ssm_rulesets'")

    op.drop_table('ssm_mappings', schema='ssm')
    print("  → Dropped 'ssm.ssm_mappings'")

    op.drop_table('ssm_attributes', schema='ssm')
    print("  → Dropped 'ssm.ssm_attributes'")

    op.drop_table('ssm_feature_codes', schema='ssm')
    print("  → Dropped 'ssm.ssm_feature_codes'")

    print("")

    # ========================================================================
    # Drop the schema
    # ========================================================================

    print("Dropping SSM schema...")
    print("-" * 80)

    op.execute("DROP SCHEMA IF EXISTS ssm CASCADE")
    print("  ✓ Schema 'ssm' dropped")
    print("")

    # ========================================================================
    # ROLLBACK SUMMARY
    # ========================================================================

    print("=" * 80)
    print("✓ Migration Rolled Back Successfully")
    print("=" * 80)
    print("")
    print("All SSM tables and schema have been removed.")
    print("You are now back to the schema state of migration 0003.")
    print("")
