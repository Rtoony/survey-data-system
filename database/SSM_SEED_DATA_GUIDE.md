# SSM Seed Data Guide

## Overview

The SSM (Survey Spatial Management) seed data provides a comprehensive set of feature codes, attributes, mappings, and automation rules for survey utility management.

## Files

- **`data/ssm_schema.py`** - SQLAlchemy Core table definitions
- **`migrations/versions/0004_create_ssm_schema.py`** - Alembic migration to create the schema
- **`database/seed_ssm_data.py`** - Seed data loader script

## Installation

### 1. Apply the Migration

First, ensure the SSM schema exists in your database:

```bash
# Check current migration status
alembic current

# Apply the SSM schema migration
alembic upgrade head
```

### 2. Load Seed Data

Run the seed data script to populate the SSM tables:

```bash
# Using default database URL from environment
python database/seed_ssm_data.py

# Or specify a custom database URL
DATABASE_URL="postgresql://user:pass@host:5432/dbname" python database/seed_ssm_data.py
```

## What Gets Seeded

### Feature Codes (16 codes)

| Code      | Description                      | Geometry Type |
|-----------|----------------------------------|---------------|
| SDMH      | Sanitary Sewer Manhole          | Point         |
| SDCB      | Sanitary Sewer Cleanout         | Point         |
| SDL       | Sanitary Sewer Line             | Line          |
| STMH      | Storm Sewer Manhole             | Point         |
| STCB      | Storm Catch Basin               | Point         |
| STINLET   | Storm Inlet                     | Point         |
| STL       | Storm Sewer Line                | Line          |
| WV        | Water Valve                     | Point         |
| HYDRANT   | Fire Hydrant                    | Point         |
| WL        | Water Line                      | Line          |
| WMETER    | Water Meter                     | Point         |
| GV        | Gas Valve                       | Point         |
| GL        | Gas Line                        | Line          |
| POLE      | Utility Pole                    | Point         |
| XFMR      | Transformer                     | Point         |
| HANDHOL   | Telecommunications Handhole     | Point         |

### Attributes (Per Feature Code)

Each feature code has defined attributes. Examples:

**SDMH (Sanitary Manhole):**
- SIZE* (Text, Required)
- MATERIAL* (Text, Required)
- DEPTH (Numeric)
- RIM_ELEV (Numeric)
- INVERT_ELEV (Numeric)

**WV (Water Valve):**
- SIZE* (Text, Required)
- TYPE* (Text, Required)
- MATERIAL (Text)
- DEPTH (Numeric)

### Mappings (20+ conditional mappings)

Each mapping defines how feature codes + attributes map to CAD layers/blocks.

**Example: Sanitary Manholes**

```sql
-- 48-inch Concrete Sanitary Manhole
{
  "feature_code": "SDMH",
  "conditions": {
    "SIZE": {"operator": "==", "value": "48IN"},
    "MATERIAL": {"operator": "==", "value": "CONC"}
  },
  "priority": 150,
  "cad_layer": "U-SSWR-SDMH",
  "cad_block": "MH-SANITARY-48-CONC"
}

-- Generic Sanitary Manhole (Default)
{
  "feature_code": "SDMH",
  "conditions": {},  -- Matches when no specific conditions met
  "priority": 100,
  "cad_layer": "U-SSWR-SDMH",
  "cad_block": "MH-SANITARY-GENERIC"
}
```

**Mapping Priority Logic:**
- Higher priority values win when multiple mappings match
- Empty conditions `{}` act as default/fallback mappings
- Priority range: 100 (default) to 150+ (specific)

### Rulesets (4 automation rulesets)

1. **Standard Utility Labeling** - Label formatting rules
2. **Auto-Connect Water Network** - Water network connection logic
3. **Storm Drainage Network** - Storm network flow rules
4. **Validation Rules - Sanitary Sewer** - Data validation rules

## Usage Examples

### 1. Query All Feature Codes

```sql
SELECT code, description, geometry_type
FROM ssm.ssm_feature_codes
WHERE is_active = true
ORDER BY code;
```

### 2. Find Attributes for a Feature Code

```sql
SELECT a.name, a.data_type, a.is_required
FROM ssm.ssm_attributes a
JOIN ssm.ssm_feature_codes fc ON a.feature_code_id = fc.id
WHERE fc.code = 'SDMH'
ORDER BY a.is_required DESC, a.name;
```

### 3. Find CAD Mapping for Specific Attributes

```sql
-- Find the correct CAD block for a 48-inch concrete manhole
SELECT m.name, m.cad_layer, m.cad_block, m.priority
FROM ssm.ssm_mappings m
JOIN ssm.ssm_feature_codes fc ON m.feature_code_id = fc.id
WHERE fc.code = 'SDMH'
  AND m.conditions @> '{"SIZE": {"operator": "==", "value": "48IN"}}'::jsonb
  AND m.conditions @> '{"MATERIAL": {"operator": "==", "value": "CONC"}}'::jsonb
ORDER BY m.priority DESC
LIMIT 1;
```

### 4. Get Best Mapping Match (Including Default)

```sql
-- Get the highest priority mapping for SDMH
-- This will return specific mapping if conditions match, otherwise the default
SELECT m.name, m.cad_layer, m.cad_block, m.priority, m.conditions
FROM ssm.ssm_mappings m
JOIN ssm.ssm_feature_codes fc ON m.feature_code_id = fc.id
WHERE fc.code = 'SDMH'
ORDER BY
  CASE
    -- Exact matches get highest priority
    WHEN m.conditions @> '{"SIZE": {"operator": "==", "value": "48IN"}}'::jsonb
         AND m.conditions @> '{"MATERIAL": {"operator": "==", "value": "CONC"}}'::jsonb
    THEN m.priority + 1000
    -- Partial matches get medium priority
    WHEN jsonb_typeof(m.conditions) != 'null' AND m.conditions != '{}'::jsonb
    THEN m.priority
    -- Default mapping (empty conditions) gets base priority
    ELSE m.priority - 1000
  END DESC
LIMIT 1;
```

### 5. List All Mappings for a Code with Priority

```sql
SELECT
  fc.code,
  m.name,
  m.conditions,
  m.priority,
  m.cad_block
FROM ssm.ssm_mappings m
JOIN ssm.ssm_feature_codes fc ON m.feature_code_id = fc.id
WHERE fc.code = 'WV'
ORDER BY m.priority DESC;
```

### 6. Get Automation Ruleset Configuration

```sql
SELECT name, configuration
FROM ssm.ssm_rulesets
WHERE name = 'Auto-Connect Water Network';
```

## Python Usage Example

```python
from sqlalchemy import create_engine, text
import json

engine = create_engine('postgresql://user:pass@host:5432/dbname')

# Find the appropriate CAD block for a survey feature
def get_cad_mapping(feature_code: str, attributes: dict) -> dict:
    """
    Find the best CAD mapping for a feature code with given attributes.

    Args:
        feature_code: Feature code (e.g., 'SDMH')
        attributes: Dict of attribute values (e.g., {'SIZE': '48IN', 'MATERIAL': 'CONC'})

    Returns:
        Dictionary with cad_layer, cad_block, cad_label_style
    """
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT m.name, m.cad_layer, m.cad_block, m.cad_label_style, m.priority
            FROM ssm.ssm_mappings m
            JOIN ssm.ssm_feature_codes fc ON m.feature_code_id = fc.id
            WHERE fc.code = :code
            ORDER BY m.priority DESC
        """), {'code': feature_code})

        mappings = list(result)

        # Find best matching mapping based on conditions
        best_match = None
        best_score = -1

        for mapping in mappings:
            # Parse conditions from database
            # Logic to evaluate conditions against attributes
            # (Implementation would check JSON conditions)

            # For now, return highest priority mapping
            if best_match is None:
                best_match = mapping

        return {
            'cad_layer': best_match.cad_layer,
            'cad_block': best_match.cad_block,
            'cad_label_style': best_match.cad_label_style
        }

# Example usage
mapping = get_cad_mapping('SDMH', {'SIZE': '48IN', 'MATERIAL': 'CONC'})
print(f"Layer: {mapping['cad_layer']}")
print(f"Block: {mapping['cad_block']}")
```

## Integration with SSMRuleService

The seed data is designed to work with the `SSMRuleService` (from `services/ssm_rule_service.py`):

```python
from services.ssm_rule_service import SSMRuleService

service = SSMRuleService(db_config)

# Evaluate rules for a survey point
result = service.evaluate_feature(
    feature_code='SDMH',
    attributes={'SIZE': '48IN', 'MATERIAL': 'CONC', 'DEPTH': 8.5}
)

print(f"Matched Mapping: {result['mapping_name']}")
print(f"CAD Layer: {result['cad_layer']}")
print(f"CAD Block: {result['cad_block']}")
```

## Customization

### Adding New Feature Codes

```sql
INSERT INTO ssm.ssm_feature_codes (code, description, geometry_type, is_active)
VALUES ('CUSTOM', 'Custom Feature Code', 'Point', true);
```

### Adding Attributes to Existing Codes

```sql
INSERT INTO ssm.ssm_attributes (feature_code_id, name, data_type, is_required)
SELECT id, 'CUSTOM_ATTR', 'Text', false
FROM ssm.ssm_feature_codes
WHERE code = 'SDMH';
```

### Adding New Mappings

```sql
INSERT INTO ssm.ssm_mappings
(feature_code_id, name, conditions, priority, cad_layer, cad_block, cad_label_style)
SELECT
  fc.id,
  'Custom Mapping Name',
  '{"CUSTOM_ATTR": {"operator": "==", "value": "VALUE"}}'::jsonb,
  160,
  'U-CUSTOM-LAYER',
  'CUSTOM-BLOCK',
  'UTILITY-STANDARD'
FROM ssm.ssm_feature_codes fc
WHERE fc.code = 'SDMH';
```

## JSONB Query Tips

### Check if conditions contain a specific key

```sql
SELECT * FROM ssm.ssm_mappings
WHERE conditions ? 'SIZE';  -- Has SIZE key
```

### Check if conditions match specific value

```sql
SELECT * FROM ssm.ssm_mappings
WHERE conditions @> '{"SIZE": {"value": "48IN"}}'::jsonb;
```

### Get all mappings with empty conditions (defaults)

```sql
SELECT * FROM ssm.ssm_mappings
WHERE conditions = '{}'::jsonb;
```

## Performance Optimization

For better query performance on large datasets, consider adding GIN indexes:

```sql
-- Index on JSONB conditions column
CREATE INDEX idx_ssm_mappings_conditions
ON ssm.ssm_mappings USING GIN (conditions);

-- Index on feature_code_id for faster joins
CREATE INDEX idx_ssm_mappings_feature_code_id
ON ssm.ssm_mappings (feature_code_id);

-- Index on priority for faster sorting
CREATE INDEX idx_ssm_mappings_priority
ON ssm.ssm_mappings (priority DESC);
```

## Troubleshooting

### Seed Script Fails

1. **Check database connection:**
   ```bash
   psql $DATABASE_URL -c "SELECT version();"
   ```

2. **Verify migration applied:**
   ```bash
   alembic current
   ```

3. **Check SSM schema exists:**
   ```sql
   SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'ssm';
   ```

### No Mappings Returned

1. Verify feature code exists and is active
2. Check conditions JSONB syntax
3. Verify priority ordering logic

## Next Steps

1. ✅ Schema created (`0004_create_ssm_schema.py`)
2. ✅ Seed data loaded (`seed_ssm_data.py`)
3. 🔄 Create UI for managing SSM data
4. 🔄 Integrate with SSMRuleService
5. 🔄 Build automation workflows using rulesets
6. 🔄 Create validation service using attribute definitions

---

**Related Documentation:**
- `data/ssm_schema.py` - Schema definitions
- `services/ssm_rule_service.py` - Rule evaluation service
- `SURVEY_CODE_SYSTEM_GUIDE.md` - Overall survey code system guide
