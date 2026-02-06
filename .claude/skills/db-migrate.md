---
name: db-migrate
description: Create and verify Alembic database migrations
user-invocable: true
---

# Database Migration

Create, verify, and apply Alembic database migrations for the job-searcher backend.

## Instructions

1. **Understand current schema**: Read all models in `backend/app/models/` to understand the current state:
   - `saved_analysis.py` - Analyzed job results
   - `analysis_queue.py` - Job analysis queue items
   - `user_preferences.py` - CV, guidelines, preferences
   - `digest.py` - Email digest records

2. **Check latest migration**: Read the most recent file in `backend/alembic/versions/` (sorted by prefix number, currently `006_add_retry_columns.py`) to understand the current DB state.

3. **Apply schema changes**: If the user describes a schema change:
   - Update the relevant model file(s) in `backend/app/models/`
   - Ensure proper imports in `backend/app/models/__init__.py`
   - Follow existing patterns: use `mapped_column`, `BigInteger` for IDs, `func.now()` for timestamps

4. **Generate migration**:
   ```bash
   cd backend && alembic revision --autogenerate -m "<description>"
   ```

5. **Verify the migration**: Read the generated migration file and check:
   - `upgrade()` contains the expected changes (CREATE TABLE, ADD COLUMN, etc.)
   - `downgrade()` correctly reverses all changes
   - No unexpected changes are included (alembic sometimes detects spurious diffs)
   - Column types and constraints are correct

6. **Apply the migration** (only if user confirms):
   ```bash
   cd backend && alembic upgrade head
   ```

7. **Report**: Summarize what tables/columns were added/modified/removed.

## Naming Convention

Migration files follow the pattern: `NNN_description.py` where NNN is a zero-padded sequence number (next is `007`).
