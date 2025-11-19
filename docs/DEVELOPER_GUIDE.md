# Survey Data System - Developer Guide

**Version**: 2.0
**Last Updated**: 2025-11-18

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Requirements](#2-system-requirements)
3. [Development Environment Setup](#3-development-environment-setup)
4. [Running the Application](#4-running-the-application)
5. [Testing](#5-testing)
6. [Database Setup](#6-database-setup)
7. [Development Workflow](#7-development-workflow)
8. [Code Style & Standards](#8-code-style--standards)
9. [Debugging](#9-debugging)
10. [Deployment](#10-deployment)
11. [Troubleshooting](#11-troubleshooting)
12. [Contributing](#12-contributing)

---

## 1. Introduction

This guide provides step-by-step instructions for setting up and developing the Survey Data System. The system is a Python/Flask application with PostgreSQL/PostGIS database, designed for civil engineering CAD-GIS integration.

**Architecture**: Hybrid Legacy/Modern (see [ARCHITECTURE.md](ARCHITECTURE.md))

---

## 2. System Requirements

### 2.1 Operating System

The application is primarily developed on:
- **Linux** (Ubuntu 20.04+, Debian 11+)
- **Windows** (via WSL2 - Windows Subsystem for Linux)
- **macOS** (11+)

**Recommended**: WSL2 on Windows or native Linux

### 2.2 Software Dependencies

| Software | Minimum Version | Recommended Version |
|----------|----------------|---------------------|
| Python | 3.11 | 3.12 |
| PostgreSQL | 14 | 15+ |
| PostGIS | 3.0 | 3.3+ |
| Node.js (optional) | 16 | 20+ |
| Git | 2.30 | Latest |

### 2.3 Hardware Requirements

**Minimum**:
- CPU: 2 cores
- RAM: 4 GB
- Disk: 10 GB free space

**Recommended**:
- CPU: 4+ cores
- RAM: 8+ GB
- Disk: 20+ GB free space (for DXF files and database)

---

## 3. Development Environment Setup

### 3.1 Clone the Repository

```bash
git clone https://github.com/your-org/survey-data-system.git
cd survey-data-system
```

### 3.2 Install Python

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip
```

**macOS**:
```bash
brew install python@3.12
```

**Windows (WSL2)**:
```bash
# Follow Ubuntu instructions inside WSL2
```

### 3.3 Create Virtual Environment

```bash
# Create virtual environment
python3.12 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
.\venv\Scripts\activate  # Windows
```

### 3.4 Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Key Dependencies** (see `requirements.txt`):
- Flask 2.2+
- psycopg2-binary (PostgreSQL adapter)
- ezdxf (DXF file processing)
- pyproj (coordinate transformations)
- openai (AI embeddings)
- networkx (graph analytics)
- flask-cors (CORS support)
- flask-caching (caching)
- python-dotenv (environment variables)

### 3.5 Install PostgreSQL + PostGIS

#### Ubuntu/Debian

```bash
# Add PostgreSQL repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update

# Install PostgreSQL 15
sudo apt install postgresql-15 postgresql-contrib-15

# Install PostGIS
sudo apt install postgresql-15-postgis-3

# Install pgvector
sudo apt install postgresql-15-pgvector
```

#### macOS

```bash
brew install postgresql@15
brew install postgis
brew services start postgresql@15
```

### 3.6 Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env  # If example exists
# OR create new .env file:
nano .env
```

**Required Environment Variables**:

```bash
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
SECRET_KEY=your-secret-key-change-in-production

# Database Configuration (Supabase or Local)
PGHOST=your-supabase-host.supabase.co
PGPORT=5432
PGDATABASE=postgres
PGUSER=postgres
PGPASSWORD=your-supabase-password
# OR for local PostgreSQL:
# PGHOST=localhost
# PGDATABASE=survey_data
# PGUSER=postgres
# PGPASSWORD=your-local-password

# OpenAI API (for embeddings and AI features)
OPENAI_API_KEY=sk-your-openai-api-key

# OAuth (Replit Auth)
REPLIT_CLIENT_ID=your-replit-client-id
REPLIT_CLIENT_SECRET=your-replit-client-secret
REPLIT_REDIRECT_URI=http://localhost:5000/auth/callback

# Session Configuration
SESSION_COOKIE_SECURE=false  # true in production
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
SESSION_TIMEOUT_HOURS=8
```

**Important**: Never commit `.env` to version control!

### 3.7 Database Setup

#### Option A: Supabase (Cloud PostgreSQL)

**Recommended for development** - No local database setup required.

1. Create a free Supabase account: https://supabase.com
2. Create a new project
3. Get connection details from Project Settings → Database
4. Copy credentials to `.env` file (PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD)

#### Option B: Local PostgreSQL

1. **Create Database**:
```bash
sudo -u postgres psql

CREATE DATABASE survey_data;
CREATE USER survey_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE survey_data TO survey_user;

\c survey_data

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

\q
```

2. **Update .env**:
```bash
PGHOST=localhost
PGDATABASE=survey_data
PGUSER=survey_user
PGPASSWORD=your-password
```

3. **Run Database Migrations** (if available):
```bash
# Currently manual - schema migrations coming in Phase 3
# For now, schema is created automatically on first run
```

### 3.8 Verify Setup

Test database connection:

```bash
python -c "
from database import get_db
with get_db() as conn:
    print('✓ Database connection successful!')
"
```

---

## 4. Running the Application

### 4.1 Development Server

**Standard Method** (using `run.py`):

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Run the application
python run.py
```

**Output**:
```
==================================================
Database Configuration Status:
DB_HOST: SET
DB_USER: SET
DB_NAME: SET
DB_PASSWORD: SET
==================================================
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://0.0.0.0:5000
Press CTRL+C to quit
```

### 4.2 Access the Application

Open your browser and navigate to:
- **Homepage**: http://localhost:5000
- **Projects**: http://localhost:5000/projects
- **Schema Viewer**: http://localhost:5000/schema
- **API Health**: http://localhost:5000/api/health

### 4.3 Alternative Run Methods

**Using Flask CLI**:
```bash
export FLASK_APP=run.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```

**Using Gunicorn (Production-like)**:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### 4.4 Hot Reload

Flask debug mode enables hot reload - code changes automatically reload the server.

**Note**: Template changes reload automatically, but service layer changes may require manual restart.

---

## 5. Testing

### 5.1 Test Suite Overview

The test suite uses **pytest** with fixtures for database and application setup.

**Test Structure**:
```
tests/
├── conftest.py              # Pytest fixtures (database, app)
├── unit/                    # Unit tests (services, utilities)
│   ├── core/
│   │   ├── test_dxf_importer.py
│   │   └── test_dxf_exporter.py
│   └── services/
│       └── test_classification_service.py
├── integration/             # Integration tests (API, database)
│   ├── api/
│   │   └── test_projects_api.py
│   └── database/
│       └── test_schema_validation.py
└── fixtures/                # Test data factories
    └── test_data.py
```

### 5.2 Running Tests

**Run All Tests**:
```bash
pytest
```

**Run Specific Test File**:
```bash
pytest tests/unit/services/test_classification_service.py
```

**Run Tests with Coverage**:
```bash
pytest --cov=. --cov-report=html
# View coverage report: open htmlcov/index.html
```

**Run Tests with Verbose Output**:
```bash
pytest -v
```

**Run Tests Matching Pattern**:
```bash
pytest -k "classification"
```

### 5.3 Test Configuration

**Test Database**: Tests use a separate test database to avoid affecting development data.

**Environment Variables for Tests**:
```bash
# .env or export
TEST_PGHOST=localhost
TEST_PGDATABASE=survey_data_test
TEST_PGUSER=postgres
TEST_PGPASSWORD=your-password
```

**Create Test Database**:
```bash
sudo -u postgres psql -c "CREATE DATABASE survey_data_test;"
sudo -u postgres psql -d survey_data_test -c "CREATE EXTENSION postgis;"
sudo -u postgres psql -d survey_data_test -c "CREATE EXTENSION vector;"
```

### 5.4 Test Fixtures

**Common Fixtures** (from `conftest.py`):

```python
def test_example(db_connection, db_cursor):
    """Test with database connection and cursor"""
    db_cursor.execute("SELECT 1")
    assert db_cursor.fetchone()[0] == 1

def test_app_context(app):
    """Test with Flask app context"""
    with app.test_client() as client:
        response = client.get('/api/health')
        assert response.status_code == 200
```

### 5.5 Writing Tests

**Example Unit Test**:

```python
# tests/unit/services/test_classification_service.py
import pytest
from services.classification_service import ClassificationService

def test_get_review_queue(db_cursor):
    """Test getting classification review queue"""
    service = ClassificationService()
    queue = service.get_review_queue(confidence_threshold=0.7)

    assert isinstance(queue, list)
    for entity in queue:
        assert entity['classification_confidence'] < 0.7
```

**Example Integration Test**:

```python
# tests/integration/api/test_projects_api.py
import pytest

def test_create_project(app, authenticated_client):
    """Test project creation via API"""
    data = {
        'project_name': 'Test Project',
        'description': 'Test description',
        'epsg_code': '2226'
    }

    response = authenticated_client.post('/api/projects', json=data)

    assert response.status_code == 201
    assert 'project_id' in response.json
```

---

## 6. Database Setup

### 6.1 Schema Overview

The database schema consists of 80+ tables organized into categories (see [ARCHITECTURE.md](ARCHITECTURE.md) for details):

- **Core Tables**: projects, drawing_entities, standards_entities
- **Civil Engineering**: utility_structures, utility_lines, survey_points, parcels, etc.
- **Relationships**: entity_relationships, relationship_types
- **Specifications**: spec_library, spec_geometry_links, csi_masterformat
- **Standards**: layer_standards, block_standards, color_standards
- **AI/Embeddings**: entity_embeddings, query_history
- **Authentication**: users, user_sessions, audit_log

### 6.2 Database Migrations

**Current State**: Manual schema management (migrations coming in Phase 3)

**Future**: Alembic for database migrations

**For now**: Schema tables are created automatically on first run by the application.

### 6.3 Seed Data

**Load Sample Data** (if available):

```bash
# Example: Load layer standards
python scripts/load_layer_standards.py

# Example: Load CSI MasterFormat codes
python scripts/load_csi_masterformat.py
```

### 6.4 Database Utilities

**Backup Database**:
```bash
pg_dump -h localhost -U survey_user -d survey_data -F c -f backup_$(date +%Y%m%d).dump
```

**Restore Database**:
```bash
pg_restore -h localhost -U survey_user -d survey_data -c backup_20241118.dump
```

**Reset Database** (development only):
```bash
# Drop and recreate database
sudo -u postgres psql -c "DROP DATABASE survey_data;"
sudo -u postgres psql -c "CREATE DATABASE survey_data;"
sudo -u postgres psql -d survey_data -c "CREATE EXTENSION postgis;"
sudo -u postgres psql -d survey_data -c "CREATE EXTENSION vector;"

# Restart application to recreate schema
python run.py
```

---

## 7. Development Workflow

### 7.1 Feature Development Process

1. **Create Feature Branch**:
```bash
git checkout -b feature/your-feature-name
```

2. **Write Code**:
   - Follow code style guidelines (see section 8)
   - Add type hints to all functions
   - Write docstrings for public functions

3. **Write Tests**:
   - Add unit tests for business logic
   - Add integration tests for API endpoints
   - Aim for 80%+ code coverage

4. **Run Tests**:
```bash
pytest
```

5. **Commit Changes**:
```bash
git add .
git commit -m "feat: Add classification review queue API"
```

6. **Push to Remote**:
```bash
git push origin feature/your-feature-name
```

7. **Create Pull Request**:
   - Describe changes
   - Reference related issues
   - Request code review

### 7.2 Refactoring Legacy Code

**Current Refactor**: Migrating routes from `app.py` to blueprints

**Process**:

1. **Identify Route Group**:
   - Example: All classification routes

2. **Create Blueprint**:
```python
# api/classification_routes.py
from flask import Blueprint

classification_bp = Blueprint('classification', __name__, url_prefix='/api/classification')

@classification_bp.route('/review-queue', methods=['GET'])
def get_review_queue():
    # Move logic from app.py
    pass
```

3. **Register Blueprint** (in `app/__init__.py`):
```python
from api.classification_routes import classification_bp
flask_app.register_blueprint(classification_bp)
```

4. **Remove from app.py**:
   - Comment out old route
   - Test that new blueprint works
   - Delete commented code

5. **Update Tests**:
   - Update test imports
   - Ensure tests still pass

### 7.3 Adding New Entity Types

**Example**: Adding a new entity type `traffic_signal`

1. **Create Database Table**:
```sql
CREATE TABLE traffic_signals (
    signal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    signal_number VARCHAR(50),
    signal_type VARCHAR(100),
    geometry GEOMETRY(PointZ, 2226),
    -- Add entity-specific columns
    created_at TIMESTAMP DEFAULT NOW()
);
```

2. **Register in Entity Registry** (`services/entity_registry.py`):
```python
ENTITY_REGISTRY = {
    # ... existing types
    'traffic_signal': ('traffic_signals', 'signal_id'),
}
```

3. **Add to Layer Classifier** (`standards/layer_classifier_v3.py`):
```python
PATTERNS = {
    # ... existing patterns
    'traffic_signal': [
        r'^(TRAFFIC|SIGNAL)-?(SIG|SIGNAL)',
        r'^TS-',
    ],
}
```

4. **Add Creation Logic** (`intelligent_object_creator.py`):
```python
def _create_traffic_signal(self, entity_record: dict) -> dict:
    # Creation logic
    pass
```

5. **Write Tests**:
```python
def test_create_traffic_signal(db_cursor):
    # Test creation logic
    pass
```

---

## 8. Code Style & Standards

### 8.1 Python Style Guide

**Follow**: PEP 8 + Type Hints

**Key Rules**:
- **Indentation**: 4 spaces (no tabs)
- **Line Length**: 100 characters max
- **Imports**: Organized (standard library → third-party → local)
- **Type Hints**: Required for all function signatures
- **Docstrings**: Required for public functions (Google style)

**Example**:

```python
from typing import List, Dict, Optional
from flask import jsonify, request

def get_project_entities(
    project_id: str,
    entity_type: Optional[str] = None,
    limit: int = 50
) -> Dict[str, any]:
    """
    Get entities for a project with optional filtering.

    Args:
        project_id: UUID of the project
        entity_type: Optional entity type filter
        limit: Maximum number of entities to return

    Returns:
        Dictionary containing entities list and pagination info

    Raises:
        ValueError: If project_id is invalid
    """
    # Implementation
    pass
```

### 8.2 Naming Conventions

**Variables & Functions**: `snake_case`
```python
project_id = "uuid"
def get_entity_details():
    pass
```

**Classes**: `PascalCase`
```python
class ClassificationService:
    pass
```

**Constants**: `UPPER_SNAKE_CASE`
```python
MAX_UPLOAD_SIZE = 100_000_000  # 100 MB
```

**Private Methods**: Leading underscore
```python
def _internal_helper():
    pass
```

### 8.3 SQL Query Standards

**Use Parameterized Queries** (prevent SQL injection):

```python
# GOOD
query = "SELECT * FROM projects WHERE project_id = %s"
result = execute_query(query, (project_id,))

# BAD - SQL injection risk!
query = f"SELECT * FROM projects WHERE project_id = '{project_id}'"
```

**Formatting**:
```python
query = """
    SELECT
        e.entity_id,
        e.entity_type,
        e.canonical_name
    FROM standards_entities e
    WHERE e.project_id = %s
        AND e.classification_state = %s
    ORDER BY e.created_at DESC
    LIMIT %s
"""
```

### 8.4 Error Handling

**Use Try-Except Blocks**:

```python
@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    try:
        query = "SELECT * FROM projects WHERE project_id = %s"
        result = execute_query(query, (project_id,))

        if not result:
            return jsonify({'error': 'Project not found'}), 404

        return jsonify(result[0])

    except Exception as e:
        print(f"Error getting project: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500
```

### 8.5 Logging

**Use Print Statements for Now** (proper logging coming in Phase 3):

```python
print(f"Processing DXF import for project {project_id}")
print(f"Imported {entity_count} entities in {elapsed_time:.2f} seconds")

# For errors:
import traceback
print(f"Error: {str(e)}")
traceback.print_exc()
```

---

## 9. Debugging

### 9.1 Flask Debug Mode

**Enable Debug Mode** (in `.env`):
```bash
FLASK_DEBUG=True
```

**Features**:
- Automatic reloading on code changes
- Interactive debugger in browser on errors
- Detailed error pages

### 9.2 Python Debugger (pdb)

**Insert Breakpoint**:
```python
def get_project_entities(project_id):
    import pdb; pdb.set_trace()  # Debugger will stop here
    query = "SELECT * FROM ..."
```

**pdb Commands**:
- `n` - Next line
- `s` - Step into function
- `c` - Continue execution
- `p variable_name` - Print variable value
- `l` - List source code
- `q` - Quit debugger

### 9.3 PostgreSQL Query Logging

**Enable Query Logging** (in `postgresql.conf`):
```
log_statement = 'all'
log_duration = on
```

**View Logs**:
```bash
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

### 9.4 Common Issues

**Issue**: Database connection fails

**Solution**:
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection settings
echo $PGHOST $PGPORT $PGDATABASE $PGUSER

# Test connection
psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c "SELECT version();"
```

**Issue**: Import errors

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Issue**: Port 5000 already in use

**Solution**:
```bash
# Find process using port 5000
sudo lsof -i :5000

# Kill process
kill -9 <PID>

# Or use different port
export FLASK_PORT=5001
python run.py
```

---

## 10. Deployment

### 10.1 Production Checklist

Before deploying to production:

- [ ] Set `FLASK_DEBUG=False`
- [ ] Set `SECRET_KEY` to strong random value
- [ ] Set `SESSION_COOKIE_SECURE=true`
- [ ] Use production database (not localhost)
- [ ] Enable HTTPS
- [ ] Set up database backups
- [ ] Configure monitoring/logging
- [ ] Run tests (`pytest`)
- [ ] Review security settings

### 10.2 Production Server Setup

**Install Production WSGI Server**:
```bash
pip install gunicorn
```

**Run with Gunicorn**:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

**Systemd Service** (Linux):

Create `/etc/systemd/system/survey-data.service`:

```ini
[Unit]
Description=Survey Data System
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/survey-data-system
Environment="PATH=/opt/survey-data-system/venv/bin"
ExecStart=/opt/survey-data-system/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable Service**:
```bash
sudo systemctl enable survey-data
sudo systemctl start survey-data
sudo systemctl status survey-data
```

### 10.3 Nginx Reverse Proxy

**Install Nginx**:
```bash
sudo apt install nginx
```

**Configure Nginx** (`/etc/nginx/sites-available/survey-data`):

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/survey-data-system/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Enable Site**:
```bash
sudo ln -s /etc/nginx/sites-available/survey-data /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 10.4 SSL/HTTPS (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 11. Troubleshooting

### 11.1 Database Issues

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
1. Check PostgreSQL is running: `sudo systemctl status postgresql`
2. Verify connection settings in `.env`
3. Check firewall rules
4. For Supabase: Verify API keys and connection pooling settings

**Problem**: `relation "table_name" does not exist`

**Solutions**:
1. Check schema exists: `\dt` in psql
2. Verify SEARCH_PATH includes your schema
3. Run schema creation scripts

### 11.2 Import Issues

**Problem**: `ModuleNotFoundError: No module named 'ezdxf'`

**Solutions**:
1. Activate virtual environment: `source venv/bin/activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Verify Python version: `python --version` (should be 3.11+)

### 11.3 DXF Import Issues

**Problem**: DXF import fails with encoding errors

**Solutions**:
1. Check DXF file encoding (should be UTF-8 or ASCII)
2. Try opening DXF in AutoCAD and re-saving as newer format
3. Check for corrupted entities in DXF file

**Problem**: Entities imported with wrong coordinates

**Solutions**:
1. Verify coordinate system setting (EPSG code)
2. Check if DXF uses correct units (feet vs meters)
3. Verify transformation parameters

### 11.4 Performance Issues

**Problem**: Slow database queries

**Solutions**:
1. Add indexes on frequently queried columns
2. Use `EXPLAIN ANALYZE` to analyze query plans
3. Enable query result caching
4. Optimize PostGIS spatial queries with `ST_DWithin` instead of `ST_Distance`

**Problem**: Slow DXF imports

**Solutions**:
1. Process entities in batches
2. Use database transactions for batch inserts
3. Disable triggers during import (if safe)
4. Generate embeddings asynchronously

---

## 12. Contributing

### 12.1 Contribution Guidelines

1. **Fork the Repository**
2. **Create Feature Branch**: `git checkout -b feature/your-feature`
3. **Write Code**: Follow code style guidelines
4. **Write Tests**: Aim for 80%+ coverage
5. **Run Tests**: `pytest`
6. **Commit Changes**: Use conventional commit messages
7. **Push to Fork**: `git push origin feature/your-feature`
8. **Create Pull Request**: Describe changes and reference issues

### 12.2 Commit Message Format

Use **Conventional Commits**:

```
feat: Add classification review queue API
fix: Fix coordinate transformation bug
docs: Update developer guide
refactor: Extract routes to blueprints
test: Add tests for relationship service
chore: Update dependencies
```

### 12.3 Code Review Process

1. All pull requests require code review
2. At least one approval from maintainer
3. All tests must pass
4. No merge conflicts
5. Code style checks pass

### 12.4 Reporting Issues

**Bug Reports**: Include:
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, database version)
- Error messages and stack traces

**Feature Requests**: Include:
- Use case description
- Proposed solution
- Alternative solutions considered

---

## Appendix A: Useful Commands Cheat Sheet

### Virtual Environment

```bash
# Create virtual environment
python3.12 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
.\venv\Scripts\activate

# Deactivate
deactivate
```

### Application

```bash
# Run development server
python run.py

# Run with Flask CLI
flask run

# Run with Gunicorn
gunicorn -w 4 run:app
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/unit/services/test_classification_service.py

# Run tests matching pattern
pytest -k "classification"
```

### Database

```bash
# Connect to database
psql -h $PGHOST -U $PGUSER -d $PGDATABASE

# List tables
\dt

# Describe table
\d table_name

# Backup database
pg_dump -h localhost -U postgres -d survey_data -F c -f backup.dump

# Restore database
pg_restore -h localhost -U postgres -d survey_data -c backup.dump
```

### Git

```bash
# Create feature branch
git checkout -b feature/your-feature

# Stage changes
git add .

# Commit changes
git commit -m "feat: Add new feature"

# Push to remote
git push origin feature/your-feature

# Pull latest changes
git pull origin main
```

---

## Appendix B: Environment Variable Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FLASK_ENV` | Environment (development, production) | `development` | No |
| `FLASK_DEBUG` | Enable debug mode | `True` | No |
| `FLASK_HOST` | Host to bind to | `0.0.0.0` | No |
| `FLASK_PORT` | Port to bind to | `5000` | No |
| `SECRET_KEY` | Flask secret key for sessions | N/A | Yes |
| `PGHOST` | PostgreSQL host | N/A | Yes |
| `PGPORT` | PostgreSQL port | `5432` | No |
| `PGDATABASE` | PostgreSQL database name | `postgres` | Yes |
| `PGUSER` | PostgreSQL username | `postgres` | Yes |
| `PGPASSWORD` | PostgreSQL password | N/A | Yes |
| `OPENAI_API_KEY` | OpenAI API key for embeddings | N/A | Yes (for AI features) |
| `REPLIT_CLIENT_ID` | Replit OAuth client ID | N/A | Yes (for auth) |
| `REPLIT_CLIENT_SECRET` | Replit OAuth client secret | N/A | Yes (for auth) |
| `SESSION_TIMEOUT_HOURS` | Session timeout in hours | `8` | No |

---

## Conclusion

This developer guide provides comprehensive instructions for setting up, developing, testing, and deploying the Survey Data System. For architecture details, see [ARCHITECTURE.md](ARCHITECTURE.md). For API documentation, see [API_SPEC.md](API_SPEC.md).

**Need Help?**
- Check [Troubleshooting](#11-troubleshooting) section
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Open an issue on GitHub
- Contact the development team

**Happy Coding!** 🚀
