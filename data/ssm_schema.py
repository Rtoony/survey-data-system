# data/ssm_schema.py
from sqlalchemy import MetaData, Table, Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

# --- Metadata and Schema Definition ---
# Using a specific schema name 'ssm' to keep these standards separate in the database
# from the core 'acad_gis' tables.
SSM_METADATA = MetaData(schema="ssm")

# 1. Master Feature Codes Table
ssm_feature_codes = Table(
    'ssm_feature_codes', SSM_METADATA,
    Column('id', Integer, primary_key=True),
    Column('code', String(10), nullable=False, index=True),
    Column('description', String(255), nullable=False),
    Column('geometry_type', String(50), default='Point', comment='Point, Line, or Polygon'),
    Column('is_active', Boolean, default=True),
    UniqueConstraint('code', name='uq_ssm_code'),
    comment='Master list of survey feature codes (e.g., SDMH, WV).'
)

# 2. Attribute Definitions Table (What data belongs to which code)
ssm_attributes = Table(
    'ssm_attributes', SSM_METADATA,
    Column('id', Integer, primary_key=True),
    Column('feature_code_id', Integer, ForeignKey('ssm.ssm_feature_codes.id', ondelete='CASCADE'), nullable=False),
    Column('name', String(50), nullable=False),
    Column('data_type', String(50), default='Text', comment='Text, Numeric, Boolean, Date'),
    Column('is_required', Boolean, default=False),
    UniqueConstraint('feature_code_id', 'name', name='uq_ssm_attr_name'),
    comment='Defines the attributes collected for each feature code.'
)

# 3. Mappings Table (THE CORE LOGIC DEFINITION)
ssm_mappings = Table(
    'ssm_mappings', SSM_METADATA,
    Column('id', Integer, primary_key=True),
    Column('feature_code_id', Integer, ForeignKey('ssm.ssm_feature_codes.id', ondelete='CASCADE'), nullable=False),
    Column('name', String(255), nullable=False, comment='User-friendly name for the mapping (e.g., "48-inch Concrete MH")'),

    # CRITICAL: Stores the conditional logic JSON: {"SIZE": {"operator": ">=", "value": "48IN"}}
    Column('conditions', JSONB, nullable=False, default={}),

    Column('priority', Integer, default=100, index=True, comment='Higher number wins tie-breaks.'),

    # CAD Output Components
    Column('cad_layer', String(100), nullable=False),
    Column('cad_block', String(100), nullable=False),
    Column('cad_label_style', String(100)),

    # Foreign Key to a future Ruleset table, linking this mapping to an automation ruleset
    Column('ruleset_id', Integer, comment='Foreign key to the automation ruleset.'),

    comment='Defines the conditional relationship between feature attributes and CAD components.'
)

# Optional: Ruleset table structure (for future Phase 20 refinement)
ssm_rulesets = Table(
    'ssm_rulesets', SSM_METADATA,
    Column('id', Integer, primary_key=True),
    Column('name', String(255), nullable=False),

    # Stores the complex rules configuration (e.g., label template, auto-connect logic flags)
    Column('configuration', JSONB, nullable=False, default={}),

    comment='Defines sets of automation rules for mappings.'
)

if __name__ == '__main__':
    # This block is used for quick verification of the schema definition
    print("SSM Schema Tables Defined:")
    for table in SSM_METADATA.tables.values():
        print(f" - {table.fullname}: {len(table.columns)} columns")

    # To deploy this schema, you would call:
    # SSM_METADATA.create_all(engine)
