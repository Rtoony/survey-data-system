# Database Migration Quick Start Guide

## TL;DR - Get Started in 3 Steps

### Step 1: Configure Database
Edit your `.env` file:
```bash
PGHOST=your-database-host
PGPORT=5432
PGDATABASE=your-database-name
PGUSER=your-username
PGPASSWORD=your-password
```

### Step 2: Apply Migrations
```bash
# For a new/empty database
python migrate.py db upgrade

# For an existing database with tables already created
alembic stamp 0002  # Marks migrations as applied without running them
```

### Step 3: Verify
```bash
python migrate.py db current
# Should show: 0002 (head)
```

## Common Commands

### Check Status
```bash
python migrate.py db current        # What's currently applied?
python migrate.py db history        # Show all migrations
```

### Apply Migrations
```bash
python migrate.py db upgrade        # Apply all pending migrations
python migrate.py db upgrade 0001   # Upgrade to specific version
```

### Create New Migration
```bash
# After editing app/data_models.py:
python migrate.py db migrate --message "add email column"

# Review the generated file in migrations/versions/
# Then apply it:
python migrate.py db upgrade
```

### Rollback
```bash
python migrate.py db downgrade      # Undo last migration
alembic downgrade 0001              # Rollback to specific version
```

## What Migrations Exist?

### 0001_initial_schema.py
Creates all database tables:
- projects, survey_points, easements
- block_definitions, attribute_codes
- entity_relationships, horizontal_alignments
- drawing_hatches, audit_log, ai_query_cache

**Does NOT include archiving columns yet.**

### 0002_add_project_archiving.py
Adds Phase 10 archiving to `projects` table:
- `is_archived` (Boolean)
- `archived_at` (DateTime)
- `archived_by` (UUID)
- Index on `is_archived`

## Troubleshooting

### Database connection failed
```bash
# Check your credentials are loaded correctly:
python -c "from app.config import config; c = config['development']; print(c.SQLALCHEMY_DATABASE_URI)"
```

### "Target database is not up to date"
```bash
# Check what's missing:
python migrate.py db current
python migrate.py db history

# Apply missing migrations:
python migrate.py db upgrade
```

### Tables already exist
```bash
# Tell Alembic they're already there:
alembic stamp 0001  # or 0002 if archiving columns exist
```

## Need More Help?

- **Detailed Guide**: See `migrations/README.md`
- **Complete Setup Info**: See `MIGRATION_SETUP_COMPLETE.md`
- **Migration Code**: Look in `migrations/versions/`

## Directory Structure
```
.
├── alembic.ini                           # Configuration
├── migrate.py                            # CLI tool
├── migrations/
│   ├── README.md                         # Detailed docs
│   ├── env.py                            # Environment config
│   └── versions/
│       ├── 0001_initial_schema.py        # Base schema
│       └── 0002_add_project_archiving.py # Archiving
└── app/
    └── data_models.py                    # Table definitions
```

## Production Deployment

```bash
# 1. ALWAYS backup first!
pg_dump your_database > backup_$(date +%Y%m%d).sql

# 2. Review what will happen
python migrate.py db upgrade --sql

# 3. Apply migration
python migrate.py db upgrade

# 4. Test your application

# 5. If problems, rollback
python migrate.py db downgrade
```

---

**Ready to go!** The migration system is production-ready.
