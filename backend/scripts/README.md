# Backend maintenance scripts

This directory contains operational utilities that are not part of the FastAPI
runtime.

## Migrations

`migrations/migrate_prd17.py` is a compatibility migration for databases created
before the PRD-17 schema expansion. Run it only when upgrading such an existing
database, from the `backend` directory:

```powershell
python -m scripts.migrations.migrate_prd17
```

Fresh installations use the current SQLModel metadata and Alembic migration chain
and do not need this script.
