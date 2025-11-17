#!/usr/bin/env python3
"""
Phase 1 Schema Fix

This script adds missing columns to the embedding_models table that are
required by the Phase 1 embedding generation scripts.

Missing columns:
- cost_per_1k_tokens (numeric) - Tracks cost per 1000 tokens
- max_input_tokens (integer) - Maximum input tokens the model can handle

Usage:
    python3 scripts/phase1_00_fix_schema.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()


def check_columns_exist(cursor):
    """Check if the required columns already exist."""
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'embedding_models'
          AND column_name IN ('cost_per_1k_tokens', 'max_input_tokens')
    """)

    existing_columns = [row[0] for row in cursor.fetchall()]
    return 'cost_per_1k_tokens' in existing_columns, 'max_input_tokens' in existing_columns


def add_missing_columns(cursor):
    """Add missing columns to embedding_models table."""
    print('Adding missing columns to embedding_models table...')

    cursor.execute("""
        ALTER TABLE embedding_models
          ADD COLUMN IF NOT EXISTS cost_per_1k_tokens NUMERIC(10, 6),
          ADD COLUMN IF NOT EXISTS max_input_tokens INTEGER
    """)

    print('  ✓ Columns added')


def set_defaults(cursor):
    """Set default values for OpenAI model if it exists."""
    print('Setting default values for OpenAI model...')

    cursor.execute("""
        UPDATE embedding_models
        SET
          cost_per_1k_tokens = 0.00002,  -- $0.02 per 1M tokens
          max_input_tokens = 8191
        WHERE provider = 'openai'
          AND model_name = 'text-embedding-3-small'
          AND cost_per_1k_tokens IS NULL
    """)

    rows_updated = cursor.rowcount
    if rows_updated > 0:
        print(f'  ✓ Updated {rows_updated} existing OpenAI model record(s)')
    else:
        print('  ℹ No existing OpenAI model records to update (will be created on first run)')


def verify_schema(cursor):
    """Verify the schema is correct."""
    print('\nVerifying schema...')

    cursor.execute("""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = 'embedding_models'
        ORDER BY ordinal_position
    """)

    columns = cursor.fetchall()

    print('\nCurrent embedding_models schema:')
    print('-' * 80)
    print(f'{"Column Name":<30} {"Type":<20} {"Nullable":<10} {"Default":<20}')
    print('-' * 80)

    required_columns = {'cost_per_1k_tokens', 'max_input_tokens'}
    found_columns = set()

    for col in columns:
        col_name, data_type, is_nullable, col_default = col
        nullable = 'YES' if is_nullable == 'YES' else 'NO'
        default = str(col_default) if col_default else '-'
        print(f'{col_name:<30} {data_type:<20} {nullable:<10} {default:<20}')

        if col_name in required_columns:
            found_columns.add(col_name)

    print('-' * 80)

    # Check if all required columns are present
    missing = required_columns - found_columns
    if not missing:
        print('\n✓ All required columns present!')
        return True
    else:
        print(f'\n✗ Missing columns: {", ".join(missing)}')
        return False


def main():
    """Main function."""
    print('=' * 80)
    print('PHASE 1 SCHEMA FIX')
    print('=' * 80)
    print()
    print('This script adds missing columns to the embedding_models table.')
    print()

    # Connect to database
    try:
        conn = psycopg2.connect(
            host=os.getenv('PGHOST') or os.getenv('DB_HOST'),
            port=int(os.getenv('PGPORT') or os.getenv('DB_PORT', 5432)),
            database=os.getenv('PGDATABASE') or os.getenv('DB_NAME'),
            user=os.getenv('PGUSER') or os.getenv('DB_USER'),
            password=os.getenv('PGPASSWORD') or os.getenv('DB_PASSWORD'),
            sslmode='require'
        )

        cursor = conn.cursor()

        # Check current state
        print('Checking current schema...')
        has_cost, has_max_tokens = check_columns_exist(cursor)

        if has_cost and has_max_tokens:
            print('  ✓ All required columns already exist')
            print()
        else:
            if not has_cost:
                print('  ✗ Missing: cost_per_1k_tokens')
            if not has_max_tokens:
                print('  ✗ Missing: max_input_tokens')
            print()

            # Add missing columns
            add_missing_columns(cursor)
            print()

        # Set defaults
        set_defaults(cursor)

        # Commit changes
        conn.commit()

        # Verify
        if verify_schema(cursor):
            print()
            print('=' * 80)
            print('✓ SCHEMA FIX SUCCESSFUL')
            print('=' * 80)
            print()
            print('You can now run Phase 1 scripts:')
            print('  python3 scripts/phase1_01_generate_embeddings.py --dry-run')
            print()
            return 0
        else:
            print()
            print('=' * 80)
            print('✗ SCHEMA FIX FAILED')
            print('=' * 80)
            print()
            print('Please check the error messages above and try again.')
            print()
            return 1

    except psycopg2.Error as e:
        print()
        print('=' * 80)
        print('✗ DATABASE ERROR')
        print('=' * 80)
        print()
        print(f'Error: {e}')
        print()
        print('Please check your database connection and try again.')
        print()
        return 1

    except Exception as e:
        print()
        print('=' * 80)
        print('✗ UNEXPECTED ERROR')
        print('=' * 80)
        print()
        print(f'Error: {e}')
        print()
        import traceback
        traceback.print_exc()
        print()
        return 1

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == '__main__':
    sys.exit(main())
