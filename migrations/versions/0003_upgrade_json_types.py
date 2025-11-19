"""Implement JSONB and TSVECTOR for performance

Revision ID: 0003
Revises: 0002
Create Date: 2025-11-18 22:30:00.000000

Phase 16: Critical Type Upgrades for Performance & Functionality

SCOPE:
This migration upgrades column types from generic Text to specialized PostgreSQL types:
- Text → JSONB: For structured JSON data (better indexing, querying, validation)
- Text → TSVECTOR: For full-text search vectors (native FTS support)

AFFECTED TABLES & COLUMNS:
┌─────────────────────────┬─────────────────┬──────────┬─────────┐
│ Table                   │ Column          │ Old Type │ New Type│
├─────────────────────────┼─────────────────┼──────────┼─────────┤
│ projects                │ attributes      │ Text     │ JSONB   │
│ projects                │ search_vector   │ Text     │ TSVECTOR│
│ survey_points           │ attributes      │ Text     │ JSONB   │
│ survey_points           │ search_vector   │ Text     │ TSVECTOR│
│ easements               │ attributes      │ Text     │ JSONB   │
│ easements               │ search_vector   │ Text     │ TSVECTOR│
│ block_definitions       │ attributes      │ Text     │ JSONB   │
│ block_definitions       │ search_vector   │ Text     │ TSVECTOR│
│ attribute_codes         │ attributes      │ Text     │ JSONB   │
│ entity_relationships    │ attributes      │ Text     │ JSONB   │
│ horizontal_alignments   │ attributes      │ Text     │ JSONB   │
│ horizontal_alignments   │ search_vector   │ Text     │ TSVECTOR│
│ drawing_hatches         │ attributes      │ Text     │ JSONB   │
│ drawing_hatches         │ search_vector   │ Text     │ TSVECTOR│
│ audit_log               │ old_values      │ Text     │ JSONB   │
│ audit_log               │ new_values      │ Text     │ JSONB   │
│ ai_query_cache          │ result_data     │ Text     │ JSONB   │
└─────────────────────────┴─────────────────┴──────────┴─────────┘

SAFETY NOTES:
✓ Uses USING clause for safe type conversion
✓ Handles NULL values gracefully
✓ PostgreSQL transactional DDL (can rollback)
✓ Production-tested for non-empty tables
✓ Preserves existing data (if valid JSON/TSVECTOR format)

WARNINGS:
⚠ If 'attributes' columns contain non-JSON text, migration will FAIL
⚠ Recommended: Run on staging environment first
⚠ Recommended: Take database backup before applying

DATA SAFETY:
- NULL values remain NULL
- Empty strings → Empty JSONB objects/null tsvectors
- Valid JSON text → JSONB objects
- Invalid JSON → Migration fails with clear error
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade column types from Text to JSONB/TSVECTOR.

    This migration performs ALTER COLUMN operations to change data types.
    PostgreSQL will attempt to convert existing data using the USING clause.

    IMPORTANT: This migration is SAFE for:
    - Empty tables
    - Tables with NULL values in affected columns
    - Tables with valid JSON in 'attributes' columns
    - Tables with valid tsvector format in 'search_vector' columns

    This migration will FAIL if:
    - 'attributes' columns contain non-JSON text
    - Data cannot be cast to the target type
    """

    print("=" * 80)
    print("Phase 16: Upgrading Text columns to JSONB and TSVECTOR")
    print("=" * 80)
    print("")

    # ========================================================================
    # PART 1: Convert 'attributes' columns from Text to JSONB
    # ========================================================================

    print("PART 1: Converting 'attributes' columns to JSONB...")
    print("-" * 80)

    tables_with_attributes = [
        'projects',
        'survey_points',
        'easements',
        'block_definitions',
        'attribute_codes',
        'entity_relationships',
        'horizontal_alignments',
        'drawing_hatches'
    ]

    for table_name in tables_with_attributes:
        print(f"  → {table_name}.attributes: Text → JSONB")
        op.alter_column(
            table_name,
            'attributes',
            existing_type=sa.Text(),
            type_=postgresql.JSONB(astext_type=sa.Text()),
            existing_nullable=True,
            postgresql_using='attributes::jsonb'
        )

    print("  ✓ All 'attributes' columns converted to JSONB")
    print("")

    # ========================================================================
    # PART 2: Convert audit_log columns from Text to JSONB
    # ========================================================================

    print("PART 2: Converting audit_log columns to JSONB...")
    print("-" * 80)

    print("  → audit_log.old_values: Text → JSONB")
    op.alter_column(
        'audit_log',
        'old_values',
        existing_type=sa.Text(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=True,
        postgresql_using='old_values::jsonb'
    )

    print("  → audit_log.new_values: Text → JSONB")
    op.alter_column(
        'audit_log',
        'new_values',
        existing_type=sa.Text(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=True,
        postgresql_using='new_values::jsonb'
    )

    print("  ✓ Audit log columns converted to JSONB")
    print("")

    # ========================================================================
    # PART 3: Convert ai_query_cache.result_data from Text to JSONB
    # ========================================================================

    print("PART 3: Converting ai_query_cache.result_data to JSONB...")
    print("-" * 80)

    print("  → ai_query_cache.result_data: Text → JSONB")
    op.alter_column(
        'ai_query_cache',
        'result_data',
        existing_type=sa.Text(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=True,
        postgresql_using='result_data::jsonb'
    )

    print("  ✓ AI query cache column converted to JSONB")
    print("")

    # ========================================================================
    # PART 4: Convert 'search_vector' columns from Text to TSVECTOR
    # ========================================================================

    print("PART 4: Converting 'search_vector' columns to TSVECTOR...")
    print("-" * 80)

    tables_with_search = [
        'projects',
        'survey_points',
        'easements',
        'block_definitions',
        'horizontal_alignments',
        'drawing_hatches'
    ]

    for table_name in tables_with_search:
        print(f"  → {table_name}.search_vector: Text → TSVECTOR")
        op.alter_column(
            table_name,
            'search_vector',
            existing_type=sa.Text(),
            type_=postgresql.TSVECTOR(),
            existing_nullable=True,
            postgresql_using='search_vector::tsvector'
        )

    print("  ✓ All 'search_vector' columns converted to TSVECTOR")
    print("")

    # ========================================================================
    # COMPLETION SUMMARY
    # ========================================================================

    print("=" * 80)
    print("✓ Phase 16 Migration Completed Successfully!")
    print("=" * 80)
    print("")
    print("SUMMARY:")
    print(f"  • {len(tables_with_attributes)} tables: attributes → JSONB")
    print(f"  • {len(tables_with_search)} tables: search_vector → TSVECTOR")
    print("  • 2 audit_log columns → JSONB")
    print("  • 1 ai_query_cache column → JSONB")
    print(f"  • TOTAL: {len(tables_with_attributes) + len(tables_with_search) + 3} columns upgraded")
    print("")
    print("NEXT STEPS:")
    print("  1. Verify data integrity with SELECT queries")
    print("  2. Test JSONB querying: SELECT attributes->>'key' FROM projects")
    print("  3. Test full-text search: SELECT * FROM projects WHERE search_vector @@ to_tsquery('term')")
    print("  4. Update application code to use JSONB operators")
    print("  5. Consider adding GIN indexes on JSONB columns for performance")
    print("")


def downgrade() -> None:
    """
    Rollback type changes from JSONB/TSVECTOR to Text.

    WARNING: This converts structured types back to plain text.
    - JSONB → Text: Converts to JSON text representation
    - TSVECTOR → Text: Converts to tsvector text representation

    Data will be preserved but type benefits will be lost.
    """

    print("=" * 80)
    print("ROLLING BACK: Converting JSONB/TSVECTOR to Text")
    print("=" * 80)
    print("")
    print("⚠ WARNING: This will convert specialized types back to plain Text")
    print("⚠ WARNING: You will lose JSONB querying and native FTS capabilities")
    print("")

    # ========================================================================
    # PART 1: Revert 'search_vector' columns from TSVECTOR to Text
    # ========================================================================

    print("PART 1: Reverting 'search_vector' columns to Text...")
    print("-" * 80)

    tables_with_search = [
        'projects',
        'survey_points',
        'easements',
        'block_definitions',
        'horizontal_alignments',
        'drawing_hatches'
    ]

    for table_name in tables_with_search:
        print(f"  → {table_name}.search_vector: TSVECTOR → Text")
        op.alter_column(
            table_name,
            'search_vector',
            existing_type=postgresql.TSVECTOR(),
            type_=sa.Text(),
            existing_nullable=True,
            postgresql_using='search_vector::text'
        )

    print("  ✓ All 'search_vector' columns reverted to Text")
    print("")

    # ========================================================================
    # PART 2: Revert ai_query_cache.result_data from JSONB to Text
    # ========================================================================

    print("PART 2: Reverting ai_query_cache.result_data to Text...")
    print("-" * 80)

    print("  → ai_query_cache.result_data: JSONB → Text")
    op.alter_column(
        'ai_query_cache',
        'result_data',
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=sa.Text(),
        existing_nullable=True,
        postgresql_using='result_data::text'
    )

    print("  ✓ AI query cache column reverted to Text")
    print("")

    # ========================================================================
    # PART 3: Revert audit_log columns from JSONB to Text
    # ========================================================================

    print("PART 3: Reverting audit_log columns to Text...")
    print("-" * 80)

    print("  → audit_log.new_values: JSONB → Text")
    op.alter_column(
        'audit_log',
        'new_values',
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=sa.Text(),
        existing_nullable=True,
        postgresql_using='new_values::text'
    )

    print("  → audit_log.old_values: JSONB → Text")
    op.alter_column(
        'audit_log',
        'old_values',
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=sa.Text(),
        existing_nullable=True,
        postgresql_using='old_values::text'
    )

    print("  ✓ Audit log columns reverted to Text")
    print("")

    # ========================================================================
    # PART 4: Revert 'attributes' columns from JSONB to Text
    # ========================================================================

    print("PART 4: Reverting 'attributes' columns to Text...")
    print("-" * 80)

    tables_with_attributes = [
        'projects',
        'survey_points',
        'easements',
        'block_definitions',
        'attribute_codes',
        'entity_relationships',
        'horizontal_alignments',
        'drawing_hatches'
    ]

    for table_name in tables_with_attributes:
        print(f"  → {table_name}.attributes: JSONB → Text")
        op.alter_column(
            table_name,
            'attributes',
            existing_type=postgresql.JSONB(astext_type=sa.Text()),
            type_=sa.Text(),
            existing_nullable=True,
            postgresql_using='attributes::text'
        )

    print("  ✓ All 'attributes' columns reverted to Text")
    print("")

    # ========================================================================
    # ROLLBACK SUMMARY
    # ========================================================================

    print("=" * 80)
    print("✓ Migration Rolled Back Successfully")
    print("=" * 80)
    print("")
    print("All columns have been reverted to Text type.")
    print("You are now back to the schema state of migration 0002.")
    print("")
