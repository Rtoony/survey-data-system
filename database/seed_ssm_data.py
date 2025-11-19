"""
Seed data for SSM (Survey Spatial Management) tables.

This script populates the SSM schema with realistic feature codes, attributes,
mappings, and rulesets for survey data automation.

Usage:
    python database/seed_ssm_data.py

Requirements:
    - Database must be running and accessible
    - Migration 0004 must be applied (SSM schema must exist)
"""

from typing import Dict, List, Any
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import json
import os
import sys


def get_database_url() -> str:
    """Get database URL from environment or use default."""
    return os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/survey_db'
    )


def seed_feature_codes(engine: Engine) -> Dict[str, int]:
    """
    Seed the ssm_feature_codes table with standard survey utility codes.

    Returns:
        Dictionary mapping feature code to database ID
    """
    feature_codes = [
        # SANITARY SEWER
        {
            'code': 'SDMH',
            'description': 'Sanitary Sewer Manhole',
            'geometry_type': 'Point',
            'is_active': True
        },
        {
            'code': 'SDCB',
            'description': 'Sanitary Sewer Cleanout',
            'geometry_type': 'Point',
            'is_active': True
        },
        {
            'code': 'SDL',
            'description': 'Sanitary Sewer Line',
            'geometry_type': 'Line',
            'is_active': True
        },
        # STORM SEWER
        {
            'code': 'STMH',
            'description': 'Storm Sewer Manhole',
            'geometry_type': 'Point',
            'is_active': True
        },
        {
            'code': 'STCB',
            'description': 'Storm Catch Basin',
            'geometry_type': 'Point',
            'is_active': True
        },
        {
            'code': 'STINLET',
            'description': 'Storm Inlet',
            'geometry_type': 'Point',
            'is_active': True
        },
        {
            'code': 'STL',
            'description': 'Storm Sewer Line',
            'geometry_type': 'Line',
            'is_active': True
        },
        # WATER
        {
            'code': 'WV',
            'description': 'Water Valve',
            'geometry_type': 'Point',
            'is_active': True
        },
        {
            'code': 'HYDRANT',
            'description': 'Fire Hydrant',
            'geometry_type': 'Point',
            'is_active': True
        },
        {
            'code': 'WL',
            'description': 'Water Line',
            'geometry_type': 'Line',
            'is_active': True
        },
        {
            'code': 'WMETER',
            'description': 'Water Meter',
            'geometry_type': 'Point',
            'is_active': True
        },
        # GAS
        {
            'code': 'GV',
            'description': 'Gas Valve',
            'geometry_type': 'Point',
            'is_active': True
        },
        {
            'code': 'GL',
            'description': 'Gas Line',
            'geometry_type': 'Line',
            'is_active': True
        },
        # ELECTRICAL
        {
            'code': 'POLE',
            'description': 'Utility Pole',
            'geometry_type': 'Point',
            'is_active': True
        },
        {
            'code': 'XFMR',
            'description': 'Transformer',
            'geometry_type': 'Point',
            'is_active': True
        },
        # TELECOM
        {
            'code': 'HANDHOL',
            'description': 'Telecommunications Handhole',
            'geometry_type': 'Point',
            'is_active': True
        },
    ]

    print("\n" + "=" * 80)
    print("SEEDING FEATURE CODES")
    print("=" * 80)

    code_id_map = {}

    with engine.begin() as conn:
        for fc in feature_codes:
            result = conn.execute(
                text("""
                    INSERT INTO ssm.ssm_feature_codes (code, description, geometry_type, is_active)
                    VALUES (:code, :description, :geometry_type, :is_active)
                    ON CONFLICT (code) DO UPDATE
                    SET description = EXCLUDED.description,
                        geometry_type = EXCLUDED.geometry_type,
                        is_active = EXCLUDED.is_active
                    RETURNING id
                """),
                fc
            )
            code_id = result.scalar()
            code_id_map[fc['code']] = code_id
            print(f"  ✓ {fc['code']:<12} - {fc['description']:<40} (ID: {code_id})")

    print(f"\n  Total: {len(feature_codes)} feature codes seeded")
    return code_id_map


def seed_attributes(engine: Engine, code_id_map: Dict[str, int]) -> None:
    """
    Seed the ssm_attributes table with attribute definitions for each feature code.

    Args:
        code_id_map: Dictionary mapping feature code to database ID
    """
    print("\n" + "=" * 80)
    print("SEEDING ATTRIBUTES")
    print("=" * 80)

    # Define attributes for each feature type
    attributes_config = {
        'SDMH': [
            {'name': 'SIZE', 'data_type': 'Text', 'is_required': True},
            {'name': 'MATERIAL', 'data_type': 'Text', 'is_required': True},
            {'name': 'DEPTH', 'data_type': 'Numeric', 'is_required': False},
            {'name': 'RIM_ELEV', 'data_type': 'Numeric', 'is_required': False},
            {'name': 'INVERT_ELEV', 'data_type': 'Numeric', 'is_required': False},
        ],
        'STMH': [
            {'name': 'SIZE', 'data_type': 'Text', 'is_required': True},
            {'name': 'MATERIAL', 'data_type': 'Text', 'is_required': True},
            {'name': 'DEPTH', 'data_type': 'Numeric', 'is_required': False},
            {'name': 'RIM_ELEV', 'data_type': 'Numeric', 'is_required': False},
            {'name': 'INVERT_ELEV', 'data_type': 'Numeric', 'is_required': False},
            {'name': 'GRATE_TYPE', 'data_type': 'Text', 'is_required': False},
        ],
        'STCB': [
            {'name': 'SIZE', 'data_type': 'Text', 'is_required': True},
            {'name': 'MATERIAL', 'data_type': 'Text', 'is_required': False},
            {'name': 'GRATE_TYPE', 'data_type': 'Text', 'is_required': False},
            {'name': 'RIM_ELEV', 'data_type': 'Numeric', 'is_required': False},
        ],
        'WV': [
            {'name': 'SIZE', 'data_type': 'Text', 'is_required': True},
            {'name': 'TYPE', 'data_type': 'Text', 'is_required': True},
            {'name': 'MATERIAL', 'data_type': 'Text', 'is_required': False},
            {'name': 'DEPTH', 'data_type': 'Numeric', 'is_required': False},
        ],
        'HYDRANT': [
            {'name': 'TYPE', 'data_type': 'Text', 'is_required': False},
            {'name': 'MANUFACTURER', 'data_type': 'Text', 'is_required': False},
            {'name': 'FLOW_RATING', 'data_type': 'Numeric', 'is_required': False},
        ],
        'WL': [
            {'name': 'SIZE', 'data_type': 'Text', 'is_required': True},
            {'name': 'MATERIAL', 'data_type': 'Text', 'is_required': True},
            {'name': 'PRESSURE_RATING', 'data_type': 'Numeric', 'is_required': False},
        ],
        'SDL': [
            {'name': 'SIZE', 'data_type': 'Text', 'is_required': True},
            {'name': 'MATERIAL', 'data_type': 'Text', 'is_required': True},
        ],
        'STL': [
            {'name': 'SIZE', 'data_type': 'Text', 'is_required': True},
            {'name': 'MATERIAL', 'data_type': 'Text', 'is_required': True},
        ],
        'GL': [
            {'name': 'SIZE', 'data_type': 'Text', 'is_required': True},
            {'name': 'MATERIAL', 'data_type': 'Text', 'is_required': False},
            {'name': 'PRESSURE_RATING', 'data_type': 'Text', 'is_required': False},
        ],
        'POLE': [
            {'name': 'TYPE', 'data_type': 'Text', 'is_required': False},
            {'name': 'HEIGHT', 'data_type': 'Numeric', 'is_required': False},
            {'name': 'OWNER', 'data_type': 'Text', 'is_required': False},
        ],
    }

    count = 0
    with engine.begin() as conn:
        for code, attributes in attributes_config.items():
            if code not in code_id_map:
                print(f"  ⚠ Skipping {code} - feature code not found")
                continue

            feature_code_id = code_id_map[code]
            print(f"\n  {code}:")

            for attr in attributes:
                conn.execute(
                    text("""
                        INSERT INTO ssm.ssm_attributes (feature_code_id, name, data_type, is_required)
                        VALUES (:feature_code_id, :name, :data_type, :is_required)
                        ON CONFLICT (feature_code_id, name) DO UPDATE
                        SET data_type = EXCLUDED.data_type,
                            is_required = EXCLUDED.is_required
                    """),
                    {
                        'feature_code_id': feature_code_id,
                        'name': attr['name'],
                        'data_type': attr['data_type'],
                        'is_required': attr['is_required']
                    }
                )
                req_marker = '*' if attr['is_required'] else ' '
                print(f"    {req_marker} {attr['name']:<20} ({attr['data_type']})")
                count += 1

    print(f"\n  Total: {count} attributes seeded")


def seed_mappings(engine: Engine, code_id_map: Dict[str, int]) -> None:
    """
    Seed the ssm_mappings table with conditional CAD mappings.

    Args:
        code_id_map: Dictionary mapping feature code to database ID
    """
    print("\n" + "=" * 80)
    print("SEEDING CAD MAPPINGS")
    print("=" * 80)

    # Define conditional mappings for each feature code
    mappings = [
        # ===== SANITARY MANHOLES =====
        {
            'code': 'SDMH',
            'name': '48-inch Concrete Sanitary Manhole',
            'conditions': {'SIZE': {'operator': '==', 'value': '48IN'}, 'MATERIAL': {'operator': '==', 'value': 'CONC'}},
            'priority': 150,
            'cad_layer': 'U-SSWR-SDMH',
            'cad_block': 'MH-SANITARY-48-CONC',
            'cad_label_style': 'UTILITY-STANDARD'
        },
        {
            'code': 'SDMH',
            'name': '60-inch Concrete Sanitary Manhole',
            'conditions': {'SIZE': {'operator': '==', 'value': '60IN'}, 'MATERIAL': {'operator': '==', 'value': 'CONC'}},
            'priority': 150,
            'cad_layer': 'U-SSWR-SDMH',
            'cad_block': 'MH-SANITARY-60-CONC',
            'cad_label_style': 'UTILITY-STANDARD'
        },
        {
            'code': 'SDMH',
            'name': 'Precast Sanitary Manhole (Any Size)',
            'conditions': {'MATERIAL': {'operator': '==', 'value': 'PRECAST'}},
            'priority': 120,
            'cad_layer': 'U-SSWR-SDMH',
            'cad_block': 'MH-SANITARY-PRECAST',
            'cad_label_style': 'UTILITY-STANDARD'
        },
        {
            'code': 'SDMH',
            'name': 'Generic Sanitary Manhole',
            'conditions': {},  # Default mapping (no conditions)
            'priority': 100,
            'cad_layer': 'U-SSWR-SDMH',
            'cad_block': 'MH-SANITARY-GENERIC',
            'cad_label_style': 'UTILITY-STANDARD'
        },
        # ===== STORM MANHOLES =====
        {
            'code': 'STMH',
            'name': '48-inch Storm Manhole',
            'conditions': {'SIZE': {'operator': '==', 'value': '48IN'}},
            'priority': 140,
            'cad_layer': 'U-STRM-STMH',
            'cad_block': 'MH-STORM-48',
            'cad_label_style': 'UTILITY-STANDARD'
        },
        {
            'code': 'STMH',
            'name': '60-inch Storm Manhole',
            'conditions': {'SIZE': {'operator': '==', 'value': '60IN'}},
            'priority': 140,
            'cad_layer': 'U-STRM-STMH',
            'cad_block': 'MH-STORM-60',
            'cad_label_style': 'UTILITY-STANDARD'
        },
        {
            'code': 'STMH',
            'name': 'Generic Storm Manhole',
            'conditions': {},
            'priority': 100,
            'cad_layer': 'U-STRM-STMH',
            'cad_block': 'MH-STORM-GENERIC',
            'cad_label_style': 'UTILITY-STANDARD'
        },
        # ===== CATCH BASINS =====
        {
            'code': 'STCB',
            'name': 'Type 1 Catch Basin',
            'conditions': {'SIZE': {'operator': '==', 'value': 'TYPE1'}},
            'priority': 130,
            'cad_layer': 'U-STRM-STCB',
            'cad_block': 'CB-TYPE1',
            'cad_label_style': 'UTILITY-STANDARD'
        },
        {
            'code': 'STCB',
            'name': 'Type 2 Catch Basin',
            'conditions': {'SIZE': {'operator': '==', 'value': 'TYPE2'}},
            'priority': 130,
            'cad_layer': 'U-STRM-STCB',
            'cad_block': 'CB-TYPE2',
            'cad_label_style': 'UTILITY-STANDARD'
        },
        {
            'code': 'STCB',
            'name': 'Generic Catch Basin',
            'conditions': {},
            'priority': 100,
            'cad_layer': 'U-STRM-STCB',
            'cad_block': 'CB-GENERIC',
            'cad_label_style': 'UTILITY-STANDARD'
        },
        # ===== WATER VALVES =====
        {
            'code': 'WV',
            'name': '6-inch Gate Valve',
            'conditions': {'SIZE': {'operator': '==', 'value': '6IN'}, 'TYPE': {'operator': '==', 'value': 'GATE'}},
            'priority': 150,
            'cad_layer': 'U-WATR-VALVE',
            'cad_block': 'VALVE-GATE-6',
            'cad_label_style': 'UTILITY-SMALL'
        },
        {
            'code': 'WV',
            'name': '8-inch Gate Valve',
            'conditions': {'SIZE': {'operator': '==', 'value': '8IN'}, 'TYPE': {'operator': '==', 'value': 'GATE'}},
            'priority': 150,
            'cad_layer': 'U-WATR-VALVE',
            'cad_block': 'VALVE-GATE-8',
            'cad_label_style': 'UTILITY-SMALL'
        },
        {
            'code': 'WV',
            'name': 'Butterfly Valve (Any Size)',
            'conditions': {'TYPE': {'operator': '==', 'value': 'BUTTERFLY'}},
            'priority': 130,
            'cad_layer': 'U-WATR-VALVE',
            'cad_block': 'VALVE-BUTTERFLY',
            'cad_label_style': 'UTILITY-SMALL'
        },
        {
            'code': 'WV',
            'name': 'Generic Water Valve',
            'conditions': {},
            'priority': 100,
            'cad_layer': 'U-WATR-VALVE',
            'cad_block': 'VALVE-GENERIC',
            'cad_label_style': 'UTILITY-SMALL'
        },
        # ===== HYDRANTS =====
        {
            'code': 'HYDRANT',
            'name': 'Fire Hydrant',
            'conditions': {},
            'priority': 100,
            'cad_layer': 'U-WATR-HYDR',
            'cad_block': 'HYDRANT-STANDARD',
            'cad_label_style': 'UTILITY-HYDRANT'
        },
        # ===== WATER LINES =====
        {
            'code': 'WL',
            'name': '12-inch Ductile Iron Water Main',
            'conditions': {'SIZE': {'operator': '==', 'value': '12IN'}, 'MATERIAL': {'operator': '==', 'value': 'DI'}},
            'priority': 140,
            'cad_layer': 'U-WATR-DIST',
            'cad_block': None,
            'cad_label_style': 'UTILITY-LINE'
        },
        {
            'code': 'WL',
            'name': 'Generic Water Line',
            'conditions': {},
            'priority': 100,
            'cad_layer': 'U-WATR-DIST',
            'cad_block': None,
            'cad_label_style': 'UTILITY-LINE'
        },
        # ===== SEWER LINES =====
        {
            'code': 'SDL',
            'name': '8-inch PVC Sanitary Line',
            'conditions': {'SIZE': {'operator': '==', 'value': '8IN'}, 'MATERIAL': {'operator': '==', 'value': 'PVC'}},
            'priority': 140,
            'cad_layer': 'U-SSWR-LINE',
            'cad_block': None,
            'cad_label_style': 'UTILITY-LINE'
        },
        {
            'code': 'SDL',
            'name': 'Generic Sanitary Line',
            'conditions': {},
            'priority': 100,
            'cad_layer': 'U-SSWR-LINE',
            'cad_block': None,
            'cad_label_style': 'UTILITY-LINE'
        },
        {
            'code': 'STL',
            'name': '12-inch RCP Storm Line',
            'conditions': {'SIZE': {'operator': '==', 'value': '12IN'}, 'MATERIAL': {'operator': '==', 'value': 'RCP'}},
            'priority': 140,
            'cad_layer': 'U-STRM-LINE',
            'cad_block': None,
            'cad_label_style': 'UTILITY-LINE'
        },
        {
            'code': 'STL',
            'name': 'Generic Storm Line',
            'conditions': {},
            'priority': 100,
            'cad_layer': 'U-STRM-LINE',
            'cad_block': None,
            'cad_label_style': 'UTILITY-LINE'
        },
    ]

    count = 0
    with engine.begin() as conn:
        for mapping in mappings:
            code = mapping['code']
            if code not in code_id_map:
                print(f"  ⚠ Skipping mapping for {code} - feature code not found")
                continue

            feature_code_id = code_id_map[code]

            # Convert conditions dict to JSON string for JSONB
            conditions_json = json.dumps(mapping['conditions'])

            conn.execute(
                text("""
                    INSERT INTO ssm.ssm_mappings
                    (feature_code_id, name, conditions, priority, cad_layer, cad_block, cad_label_style)
                    VALUES (:feature_code_id, :name, :conditions::jsonb, :priority, :cad_layer, :cad_block, :cad_label_style)
                """),
                {
                    'feature_code_id': feature_code_id,
                    'name': mapping['name'],
                    'conditions': conditions_json,
                    'priority': mapping['priority'],
                    'cad_layer': mapping['cad_layer'],
                    'cad_block': mapping['cad_block'],
                    'cad_label_style': mapping['cad_label_style']
                }
            )

            cond_str = json.dumps(mapping['conditions']) if mapping['conditions'] else '(default)'
            print(f"  ✓ [{code}] {mapping['name']:<45} | Priority: {mapping['priority']} | {cond_str}")
            count += 1

    print(f"\n  Total: {count} mappings seeded")


def seed_rulesets(engine: Engine) -> None:
    """
    Seed the ssm_rulesets table with automation ruleset configurations.
    """
    print("\n" + "=" * 80)
    print("SEEDING AUTOMATION RULESETS")
    print("=" * 80)

    rulesets = [
        {
            'name': 'Standard Utility Labeling',
            'configuration': {
                'label_template': '{CODE}-{SIZE}',
                'label_position': 'center',
                'label_rotation': 'auto',
                'show_attributes': ['SIZE', 'MATERIAL'],
            }
        },
        {
            'name': 'Auto-Connect Water Network',
            'configuration': {
                'auto_connect': True,
                'connection_tolerance': 0.5,
                'snap_to_structures': True,
                'valid_connections': ['WV', 'HYDRANT', 'WMETER'],
            }
        },
        {
            'name': 'Storm Drainage Network',
            'configuration': {
                'auto_connect': True,
                'flow_direction': 'downstream',
                'valid_structures': ['STMH', 'STCB', 'STINLET'],
                'check_invert_elevations': True,
            }
        },
        {
            'name': 'Validation Rules - Sanitary Sewer',
            'configuration': {
                'required_attributes': ['SIZE', 'MATERIAL'],
                'valid_materials': ['PVC', 'CONC', 'DI', 'HDPE'],
                'valid_sizes': ['4IN', '6IN', '8IN', '10IN', '12IN', '15IN', '18IN'],
                'check_slope': True,
                'min_slope': 0.004,
            }
        },
    ]

    with engine.begin() as conn:
        for ruleset in rulesets:
            config_json = json.dumps(ruleset['configuration'])

            conn.execute(
                text("""
                    INSERT INTO ssm.ssm_rulesets (name, configuration)
                    VALUES (:name, :configuration::jsonb)
                """),
                {
                    'name': ruleset['name'],
                    'configuration': config_json
                }
            )

            print(f"  ✓ {ruleset['name']}")
            print(f"    Config: {json.dumps(ruleset['configuration'], indent=2)}")
            print()

    print(f"  Total: {len(rulesets)} rulesets seeded")


def verify_seed_data(engine: Engine) -> None:
    """Verify that seed data was inserted correctly."""
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    with engine.connect() as conn:
        # Count feature codes
        result = conn.execute(text("SELECT COUNT(*) FROM ssm.ssm_feature_codes"))
        fc_count = result.scalar()
        print(f"  Feature Codes: {fc_count}")

        # Count attributes
        result = conn.execute(text("SELECT COUNT(*) FROM ssm.ssm_attributes"))
        attr_count = result.scalar()
        print(f"  Attributes: {attr_count}")

        # Count mappings
        result = conn.execute(text("SELECT COUNT(*) FROM ssm.ssm_mappings"))
        map_count = result.scalar()
        print(f"  Mappings: {map_count}")

        # Count rulesets
        result = conn.execute(text("SELECT COUNT(*) FROM ssm.ssm_rulesets"))
        rule_count = result.scalar()
        print(f"  Rulesets: {rule_count}")

        # Sample query: Show mappings for SDMH
        print("\n  Sample Query - SDMH Mappings:")
        result = conn.execute(text("""
            SELECT m.name, m.conditions, m.priority, m.cad_block
            FROM ssm.ssm_mappings m
            JOIN ssm.ssm_feature_codes fc ON m.feature_code_id = fc.id
            WHERE fc.code = 'SDMH'
            ORDER BY m.priority DESC
        """))

        for row in result:
            print(f"    • {row.name} (Priority: {row.priority})")
            print(f"      Conditions: {row.conditions}")
            print(f"      Block: {row.cad_block}")


def main():
    """Main execution function."""
    print("\n" + "=" * 80)
    print("SSM SEED DATA LOADER")
    print("=" * 80)
    print("\nThis script will populate the SSM schema with:")
    print("  • Feature codes (survey utility codes)")
    print("  • Attribute definitions for each code")
    print("  • Conditional CAD mappings")
    print("  • Automation rulesets")
    print("\n" + "=" * 80)

    # Get database connection
    db_url = get_database_url()
    print(f"\nConnecting to database...")
    print(f"URL: {db_url.split('@')[1] if '@' in db_url else 'Local database'}")

    try:
        engine = create_engine(db_url)

        # Verify SSM schema exists
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'ssm'"
            ))
            if not result.scalar():
                print("\n❌ ERROR: SSM schema does not exist!")
                print("   Please run migration 0004 first: alembic upgrade head")
                sys.exit(1)

        print("✓ Connected successfully\n")

        # Seed all data
        code_id_map = seed_feature_codes(engine)
        seed_attributes(engine, code_id_map)
        seed_mappings(engine, code_id_map)
        seed_rulesets(engine)

        # Verify
        verify_seed_data(engine)

        print("\n" + "=" * 80)
        print("✓ SSM SEED DATA LOADED SUCCESSFULLY!")
        print("=" * 80)
        print("\nNext steps:")
        print("  1. Test JSONB queries on ssm_mappings table")
        print("  2. Integrate with SSMRuleService for automation")
        print("  3. Create UI for managing feature codes and mappings")
        print()

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
