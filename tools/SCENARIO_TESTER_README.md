# Scenario Tester Tool

## Overview

The **Scenario Tester Tool** is a debugging and validation utility for the Survey Standards Management (SSM) pipeline. It provides a "What If" testing interface that allows you to run raw survey data through the entire pipeline and receive detailed logs of the decision-making process.

## Purpose

- **Debug Standards Resolution**: Understand exactly how the system resolves feature codes to CAD standards
- **Validate Pipeline Behavior**: Test edge cases and verify expected behavior
- **"What If" Analysis**: Test scenarios before implementing them in production
- **Training & Documentation**: Demonstrate how the SSM pipeline processes data

## Pipeline Flow

The tool orchestrates the complete SSM pipeline:

1. **Phase 25: Data Normalization** - Clean text, calculate derived attributes (e.g., DEPTH)
2. **Phase 28: Mapping Resolution** - Find best matching standards mapping by priority/specificity
3. **Phase 20: Rule Execution** - Generate labels, apply automation rules
4. **Phase 27: Export Formatting** - Format final output for Civil 3D or Trimble FXL

## Installation

The tool is located at:
```
tools/scenario_tester_tool.py
```

No additional installation required - it uses the existing SSM pipeline services.

## Usage

### Basic Usage

```python
from tools.scenario_tester_tool import ScenarioTesterTool

# Initialize the tool (mock mode - no database required)
tool = ScenarioTesterTool(use_mock=True)

# Run a scenario
test_data = {
    "SIZE": "48IN",
    "RIM_ELEV": 105.00,
    "INVERT_ELEV": 100.00,
    "MATERIAL": "CONCRETE"
}

result = tool.run_scenario("SDMH", test_data, "civil3d")

# Print formatted report
tool.print_scenario_report(result)
```

### With Database

```python
# Initialize with database connection
tool = ScenarioTesterTool(
    db_url="postgresql://user:pass@localhost/db_name",
    use_mock=False
)

result = tool.run_scenario("SDMH", test_data, "civil3d")
```

### Batch Testing

```python
scenarios = [
    {
        "feature_code": "SDMH",
        "attributes": {"SIZE": 24, "RIM_ELEV": 100.0},
        "export_format": "civil3d",
        "description": "Small manhole test"
    },
    {
        "feature_code": "SWP",
        "attributes": {"MATERIAL": "PVC", "DEPTH": 6.5},
        "export_format": "trimble_fxl",
        "description": "PVC pipe test"
    }
]

results = tool.run_batch_scenarios(scenarios)

for result in results:
    print(f"{result['scenario_description']}: {result['status']}")
```

## Return Structure

The `run_scenario()` method returns a comprehensive dictionary:

```python
{
    "status": "SUCCESS" | "FAILURE",
    "resolved_feature": "SDMH",
    "pipeline_log": [
        "✓ Step 1: Phase 25: Data Normalization - SUCCESS",
        "  Message: Cleaned text attributes and calculated derived values",
        # ... more log entries
    ],
    "raw_input_data": { ... },
    "normalized_attributes": { ... },
    "resolved_mapping": {
        "source_mapping_id": 301,
        "cad_layer": "C-SSWR-MH-48IN-CONC",
        "cad_block": "MH-48-CONC-BLOCK"
    },
    "rule_results": {
        "label_text": "MH-48IN / INV: 100.0 / D:5.0ft",
        "validation_status": "PASS"
    },
    "final_cad_preview": "... CAD export output ...",
    "export_format": "civil3d",
    "timestamp": "2025-11-18T23:44:27.447184",
    "notes": "Scenario run successfully. ..."
}
```

## Export Formats

The tool supports two export formats:

- `"civil3d"` - Civil 3D Description Key format
- `"trimble_fxl"` - Trimble FXL XML format

## Command Line Usage

Run the example scenarios directly:

```bash
python3 tools/scenario_tester_tool.py
```

## Testing

Comprehensive unit tests are available:

```bash
# Run tests
TEST_PGDATABASE=test_db pytest tests/test_scenario_tester_tool.py -v

# With coverage
TEST_PGDATABASE=test_db pytest tests/test_scenario_tester_tool.py --cov=tools.scenario_tester_tool
```

## Common Use Cases

### 1. Debug a Failing Scenario

```python
tool = ScenarioTesterTool(use_mock=True)

# Test data that's failing in production
failing_data = {
    "SIZE": "UNKNOWN_SIZE",
    "RIM_ELEV": None  # Missing data
}

result = tool.run_scenario("SDMH", failing_data, "civil3d")

# Review detailed pipeline log
for log_line in result['pipeline_log']:
    print(log_line)
```

### 2. Validate New Standards Mapping

```python
# Test if new standards mapping works correctly
tool = ScenarioTesterTool(db_url=DB_URL, use_mock=False)

# Test with conditions that should trigger new mapping
test_data = {
    "SIZE": "60IN",
    "MATERIAL": "CONCRETE",
    "JURISDICTION": "COUNTY"
}

result = tool.run_scenario("SDMH", test_data, "civil3d")

# Verify correct mapping was resolved
print(f"Resolved to Mapping ID: {result['resolved_mapping']['source_mapping_id']}")
print(f"Layer: {result['resolved_mapping']['cad_layer']}")
```

### 3. Compare Export Formats

```python
tool = ScenarioTesterTool(use_mock=True)

test_data = {"SIZE": "48IN", "RIM_ELEV": 105.0, "INVERT_ELEV": 100.0}

# Generate both formats
civil3d_result = tool.run_scenario("SDMH", test_data, "civil3d")
fxl_result = tool.run_scenario("SDMH", test_data, "trimble_fxl")

print("Civil 3D Output:")
print(civil3d_result['final_cad_preview'])

print("\nTrimble FXL Output:")
print(fxl_result['final_cad_preview'])
```

## API Integration

The tool can be integrated into API endpoints for real-time "What If" analysis:

```python
from flask import Blueprint, request, jsonify
from tools.scenario_tester_tool import ScenarioTesterTool

scenario_bp = Blueprint('scenario', __name__)
tool = ScenarioTesterTool(use_mock=True)

@scenario_bp.route('/api/scenario/test', methods=['POST'])
def test_scenario():
    data = request.json
    result = tool.run_scenario(
        feature_code=data['feature_code'],
        raw_attributes=data['attributes'],
        export_format=data.get('export_format', 'civil3d')
    )
    return jsonify(result)
```

## Performance Notes

- **Mock Mode**: Instant execution, no database queries
- **Database Mode**: Performance depends on database query optimization
- **Batch Scenarios**: Processes scenarios sequentially

## Troubleshooting

### Import Errors

If you encounter import errors, ensure PYTHONPATH includes the project root:

```bash
export PYTHONPATH=/path/to/survey-data-system:$PYTHONPATH
```

### Mock vs Database Mode

- Use **mock mode** for quick testing and development
- Use **database mode** for production validation with real standards mappings

## Related Services

- `StandardsPreviewService` (services/standards_preview_service.py) - Pipeline orchestrator
- `DataNormalizationService` (services/data_normalization_service.py) - Phase 25
- `GKGSyncService` (services/ssm_mapping_service.py) - Phase 28
- `SSMRuleService` (services/ssm_rule_service.py) - Phase 20
- `ExportTemplateService` (services/export_template_service.py) - Phase 27

## Version History

- **v1.0** (2025-11-18): Initial implementation
  - Core `run_scenario()` functionality
  - Batch scenario testing
  - Detailed pipeline logging
  - Support for Civil 3D and Trimble FXL formats
  - Comprehensive unit tests (92% coverage)
