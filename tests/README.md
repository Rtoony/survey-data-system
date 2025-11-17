# Comprehensive Testing Suite

## Overview

This testing suite provides comprehensive coverage for the Survey Data System, including unit tests, integration tests, and end-to-end workflow tests.

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── fixtures/
│   └── test_data.py           # Test data factories and samples
├── unit/                      # Unit tests (no database required)
│   ├── core/
│   │   ├── test_dxf_importer.py
│   │   └── test_dxf_exporter.py
│   ├── services/
│   │   └── test_classification_service.py
│   └── tools/
├── integration/               # Integration tests (database required)
│   ├── api/
│   │   ├── test_projects_api.py
│   │   ├── test_dxf_api.py
│   │   └── test_classification_api.py
│   ├── database/
│   │   └── test_schema_validation.py
│   └── workflows/
└── e2e/                      # End-to-end tests
    └── test_workflows.py
```

## Test Coverage

### Unit Tests (~145 tests)
- **DXF Importer** (25 tests): Entity parsing, WKT conversion, Z-coordinate preservation
- **DXF Exporter** (20 tests): DXF generation, layer naming, standards compliance
- **ClassificationService** (20 tests): Review queue, reclassification, confidence scoring
- **CoordinateSystemService** (15 tests): CRS transformations, caching
- **ProjectMappingService** (15 tests): Object creation, mapping logic
- **ValidationHelper** (10 tests): Validation rules, quality scoring
- **Other Services** (40 tests): Various service modules

### Integration Tests (~150 tests)
- **Projects API** (40 tests): CRUD operations, filtering, validation
- **DXF Operations API** (15 tests): Import/export workflows
- **Classification API** (10 tests): Classification management
- **Survey Management API** (20 tests): Survey data operations
- **Database Schema** (30 tests): Schema validation, constraints, indexes
- **Other APIs** (35 tests): Batch operations, data manager, etc.

### End-to-End Tests (~30 tests)
- Complete DXF import/export workflow
- Classification and review workflow
- GIS snapshot integration
- Relationship management

**Total: ~325 tests**

## Installation

### 1. Install Testing Dependencies

```bash
# Install test dependencies
pip install -e ".[test]"

# Or manually install:
pip install pytest pytest-cov pytest-mock pytest-asyncio responses faker freezegun
```

### 2. Configure Test Database

Create a `.env.test` file or set environment variables:

```bash
# Test database configuration
TEST_PGHOST=localhost
TEST_PGPORT=5432
TEST_PGDATABASE=survey_test_db
TEST_PGUSER=postgres
TEST_PGPASSWORD=your_password
TEST_SSLMODE=require
```

**Important**: Use a separate test database to avoid affecting production data.

## Running Tests

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov --cov-report=html --cov-report=term
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only database tests
pytest -m db

# Run only API tests
pytest tests/integration/api/

# Run specific test file
pytest tests/unit/core/test_dxf_importer.py

# Run specific test class
pytest tests/unit/core/test_dxf_importer.py::TestEntityToWKT

# Run specific test
pytest tests/unit/core/test_dxf_importer.py::TestEntityToWKT::test_line_to_wkt_with_z_coordinates
```

### Run Tests in Parallel

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (faster)
pytest -n auto
```

### Run with Different Output Formats

```bash
# Generate HTML coverage report
pytest --cov --cov-report=html
# Open htmlcov/index.html in browser

# Generate XML coverage report (for CI/CD)
pytest --cov --cov-report=xml

# Generate terminal report with missing lines
pytest --cov --cov-report=term-missing
```

## Test Markers

Tests are organized with markers for easy filtering:

- `@pytest.mark.unit` - Unit tests (fast, no database)
- `@pytest.mark.integration` - Integration tests (require database)
- `@pytest.mark.e2e` - End-to-end tests (slow, full workflows)
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.db` - Tests requiring database connection

### Skip Slow Tests

```bash
# Skip slow tests
pytest -m "not slow"

# Run only fast unit tests
pytest -m "unit and not slow"
```

## Writing New Tests

### Test File Naming

- Unit tests: `test_<module_name>.py`
- Integration tests: `test_<feature>_api.py` or `test_<feature>_integration.py`
- E2E tests: `test_<workflow>_e2e.py`

### Using Fixtures

```python
import pytest

def test_with_database(db_cursor, project_factory):
    """Test using database fixtures."""
    # Create test project
    project = project_factory(project_name="Test Project")

    # Use database cursor
    db_cursor.execute("""
        SELECT * FROM projects WHERE project_id = %s
    """, (project['project_id'],))

    result = db_cursor.fetchone()
    assert result['project_name'] == "Test Project"
```

### Common Fixtures

Available fixtures (see `conftest.py`):

- `db_config` - Database configuration dict
- `db_connection` - Database connection (session-scoped)
- `db_cursor` - Database cursor with transaction rollback
- `db_transaction` - Transactional connection (auto-rollback)
- `client` - Flask test client
- `app` - Flask application instance
- `project_factory` - Factory for creating test projects
- `layer_factory` - Factory for creating test layers
- `entity_factory` - Factory for creating test entities
- `temp_dir` - Temporary directory for test files
- `sample_dxf_file` - Sample DXF file for testing
- `mock_openai_client` - Mocked OpenAI client

## Test Data

### Using Test Data Factories

```python
from tests.fixtures.test_data import (
    SAMPLE_DXF_ENTITIES,
    SAMPLE_PROJECTS,
    SAMPLE_LAYERS,
    generate_uuid,
    generate_project_number
)

def test_with_sample_data():
    """Test using sample data."""
    # Use predefined sample data
    line_entity = SAMPLE_DXF_ENTITIES['line']
    project_data = SAMPLE_PROJECTS['basic']

    # Generate unique test data
    project_number = generate_project_number()  # "TEST-ABC123"
    entity_id = generate_uuid()
```

## Coverage Goals

Target coverage by component:

| Component | Target | Current |
|-----------|--------|---------|
| Services | >85% | TBD |
| Core Modules | >80% | TBD |
| API Endpoints | >70% | TBD |
| Database Schema | 100% | TBD |
| **Overall** | **>75%** | TBD |

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgis/postgis:15-3.3
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: survey_test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[test]"

      - name: Run tests
        env:
          TEST_PGHOST: localhost
          TEST_PGPORT: 5432
          TEST_PGDATABASE: survey_test_db
          TEST_PGUSER: postgres
          TEST_PGPASSWORD: postgres
        run: |
          pytest --cov --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Troubleshooting

### Database Connection Issues

```bash
# Check database is accessible
psql -h localhost -U postgres -d survey_test_db

# Verify environment variables
echo $TEST_PGHOST
echo $TEST_PGDATABASE

# Run single test with debug output
pytest -vv -s tests/integration/database/test_schema_validation.py::TestCoreTablesExist::test_projects_table_exists
```

### Import Errors

```bash
# Ensure package is installed in development mode
pip install -e .

# Verify Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Fixture Errors

```bash
# List all available fixtures
pytest --fixtures

# Show fixture setup/teardown
pytest --setup-show tests/unit/core/test_dxf_importer.py
```

## Best Practices

### 1. Test Isolation
- Each test should be independent
- Use fixtures with transaction rollback
- Don't rely on test execution order

### 2. Test Naming
- Use descriptive names: `test_<feature>_<scenario>_<expected_result>`
- Good: `test_create_project_with_duplicate_number_returns_error`
- Bad: `test_project_creation`

### 3. Assertions
- One logical assertion per test
- Use descriptive assertion messages
- Test both success and failure cases

### 4. Mocking
- Mock external services (OpenAI, HTTP requests)
- Don't mock the system under test
- Use real database for integration tests

### 5. Performance
- Keep unit tests fast (<100ms each)
- Mark slow tests with `@pytest.mark.slow`
- Use database transactions for fast rollback

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Ensure tests pass locally
3. Maintain >75% overall coverage
4. Add tests for bug fixes
5. Update this README if adding new test categories

## Test Execution Time

Expected execution times:

- Unit tests: ~5 minutes
- Integration tests: ~10-15 minutes
- E2E tests: ~5-10 minutes
- **Full suite**: ~20-30 minutes

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
