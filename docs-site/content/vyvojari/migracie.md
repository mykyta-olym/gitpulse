---
title: "Databázové migrácie"
description: "Správa databázových migrácií s Alembic"
---
{{< details >}}
- Pre: Vývojár
- Vyžaduje: Lokálne prostredie podľa príručky pre vývojárov
{{< /details >}}
Sprievodca správou databázových migrácií pomocou Alembic.

## Prehľad

```mermaid
graph LR
    DEV["Vývojár"] --> |alembic revision| NEW["Nová migrácia"]
    NEW --> |alembic upgrade| DB[("Databáza")]
    DB --> |alembic downgrade| PREV["Predchádzajúci stav"]
    
    style NEW fill:#f9f,stroke:#333
    style DB fill:#bbf,stroke:#333
```

## Konfigurácia

### alembic.ini

```ini
# alembic.ini
[alembic]
script_location = alembic
prepend_sys_path = src

# Database URL z environment variable
sqlalchemy.url = 

[post_write_hooks]
hooks = ruff
ruff.type = exec
ruff.executable = ruff
ruff.options = format REVISION_SCRIPT_FILENAME
```

### env.py

```python
# alembic/env.py
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.config import settings
from app.models.base import Base

# Importovať všetky modely
from app.models import *  # noqa

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## Základné príkazy

### Vytvorenie migrácie

```bash
# Automatická detekcia zmien v modeloch
alembic revision --autogenerate -m "add_team_description"

# Prázdna migrácia (manuálna)
alembic revision -m "custom_data_migration"
```

### Aplikovanie migrácií

```bash
# Najnovšia verzia
alembic upgrade head

# Konkrétna verzia
alembic upgrade 003

# Relatívne (2 kroky dopredu)
alembic upgrade +2
```

### Rollback

```bash
# O jeden krok späť
alembic downgrade -1

# Na konkrétnu verziu
alembic downgrade 002

# Na začiatok (pozor!)
alembic downgrade base
```

### Informácie

```bash
# Aktuálna verzia
alembic current

# História migrácií
alembic history --verbose

# Pending migrácie
alembic heads
```

## Existujúce migrácie

GitPulse používa lineárnu históriu 27 Alembic migrácií (`001` až `027`):

| Migrácia | Popis |
|----------|-------|
| `001_core_schema` | Základná schéma platformy GitPulse (courses, teams, users, projects, events) |
| `002_teaching_tools` | Pedagogické nástroje (rubriky, telemetria, LLM) |
| `003_scale_and_telemetry` | Optimalizácie škálovania a pilotná telemetria |
| `004_release_v1_consolidated` | Konsolidovaná schéma release v1 |
| `005_drop_redundant_indexes_and_assignments` | Odstránenie redundantných indexov a assignment tabuliek |
| `006_pipeline_coverage` | Pridanie stĺpca test coverage do tabuľky `pipelines` |
| `007_mr_assignee_reviewers` | Explicitní assignee, reviewers a approvers v `merge_requests` |
| `008_project_gitlab_intel` | JSONB pole `gitlab_intel` v `gitlab_projects` |
| `009_drop_sandbox_features` | Trvalé odstránenie nepoužívaných sandbox funkcií (conflict simulator, docker verify, ci failure) |
| `010_prune_metric_snapshot_backlog` | Zastropovanie rastu histórie metrík a indexov |
| `011_patterns_into_check_configs` | Presun konvenčných vzorov (branch, commit) do per-check konfigurácie |
| `012_user_preferences` | Používateľské predvoľby na úrovni účtu (Preferences) |
| `013_diff_colors` | Používateľské farby riadkov diffov (Preferences > Diffs) |
| `014_notification_prefs` | Notifikačné preferencie podľa kategórií |
| `015_workspace_prefs` | Špecifické preferencie GitPulse pracovného prostredia |
| `016_ticket_queue_pref` | Oddelenie notifikácií o nových požiadavkách podpory pre personál |
| `017_syntax_theme_pref` | Zvýrazňovanie syntaxe kódu podľa preferencie |
| `018_mr_commit_shas` | Zoznam commit SHA pre merge requesty z GitLabu |
| `019_mr_notes_author_index` | Index pre autorov poznámok merge requestov |
| `020_remember_period` | Predvoľba zapamätania vybraného akademického obdobia |
| `021_default_period` | Predvoľba predvoleného obdobia stránok s výberom obdobia |
| `022_drop_remember_period` | Odstránenie stĺpca nahradeného predvoleným obdobím |
| `023_classroom_assistant` | Asistent cvičení: bot účet kurzu a úlohy študentov |
| `024_assistant_language_and_token_state` | Jazyk komentárov asistenta a stav odmietnutého tokenu |
| `025_analytics_snapshot_indexes` | Indexy pre analytiku kurzu bez čítania histórie snímok |
| `026_course_snapshot_freshness_index` | Index najnovšej snímky kurzu |
| `027_drop_usage_telemetry` | Odstránenie tabuliek pilotnej telemetrie používania |

## Písanie migrácií

### Autogenerated migrácia

```python
# alembic/versions/028_example_feature.py
"""add example feature

Revision ID: 028_example_feature
Revises: 027
Create Date: 2026-09-10 10:00:00.000000

"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '028_example_feature'
down_revision: str | None = '019_mr_notes_author_index'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    # ### autogenerated ###
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('theme', sa.String(20), nullable=False, default='light'),
        sa.Column('notifications_enabled', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_preferences_user_id', 'user_preferences', ['user_id'])
    # ### end autogenerated ###

def downgrade() -> None:
    # ### autogenerated ###
    op.drop_index('ix_user_preferences_user_id', 'user_preferences')
    op.drop_table('user_preferences')
    # ### end autogenerated ###
```

### Data migrácia

```python
# alembic/versions/012_populate_default_checks.py
"""populate default checks

Revision ID: 012_populate_default_checks
Revises: 011_add_user_preferences
Create Date: 2026-11-15 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

revision = '012_populate_default_checks'
down_revision = '011_add_user_preferences'

def upgrade() -> None:
    # Definícia tabuľky pre insert
    custom_checks = table(
        'custom_checks',
        column('id', sa.Integer),
        column('course_id', sa.Integer),
        column('check_code', sa.String),
        column('name', sa.String),
        column('description', sa.Text),
        column('is_active', sa.Boolean),
    )
    
    # Batch insert
    op.bulk_insert(custom_checks, [
        {
            'id': 1,
            'course_id': 1,
            'check_code': 'C01',
            'name': 'Repository README',
            'description': 'Project has an up-to-date README',
            'is_active': True,
        },
        {
            'id': 2,
            'course_id': 1,
            'check_code': 'C02',
            'name': 'Deployment notes',
            'description': 'Project documents deployment steps',
            'is_active': True,
        },
    ])

def downgrade() -> None:
    op.execute("DELETE FROM custom_checks WHERE id IN (1, 2)")
```

### Komplexná migrácia

```python
# alembic/versions/013_split_events_table.py
"""split events table for better performance

Revision ID: 013_split_events_table
Revises: 012_populate_default_checks
Create Date: 2026-11-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '013_split_events_table'
down_revision = '012_populate_default_checks'

def upgrade() -> None:
    # 1. Vytvoriť novú tabuľku
    op.create_table(
        'commit_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id')),
        sa.Column('sha', sa.String(40), nullable=False),
        sa.Column('message', sa.Text()),
        sa.Column('author_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('committed_at', sa.DateTime(), nullable=False),
        sa.Column('lines_added', sa.Integer(), default=0),
        sa.Column('lines_removed', sa.Integer(), default=0),
    )
    
    # 2. Migrovať dáta
    op.execute("""
        INSERT INTO commit_events (id, project_id, sha, message, author_id, committed_at, lines_added, lines_removed)
        SELECT id, project_id, data->>'sha', data->>'message', author_id, created_at, 
               COALESCE((data->>'additions')::int, 0),
               COALESCE((data->>'deletions')::int, 0)
        FROM events
        WHERE event_type = 'commit'
    """)
    
    # 3. Vytvoriť index
    op.create_index('ix_commit_events_project_committed', 'commit_events', ['project_id', 'committed_at'])
    
    # 4. Odstrániť staré dáta (voliteľné)
    # op.execute("DELETE FROM events WHERE event_type = 'commit'")

def downgrade() -> None:
    # Migrovať dáta späť
    op.execute("""
        INSERT INTO events (project_id, event_type, data, author_id, created_at)
        SELECT project_id, 'commit', 
               jsonb_build_object('sha', sha, 'message', message, 'additions', lines_added, 'deletions', lines_removed),
               author_id, committed_at
        FROM commit_events
        WHERE NOT EXISTS (
            SELECT 1 FROM events e WHERE e.id = commit_events.id
        )
    """)
    
    op.drop_table('commit_events')
```

## Best practices

### Odporúčania

1. **Vždy testovať up aj down**
   ```bash
   alembic upgrade head
   alembic downgrade -1
   alembic upgrade head
   ```

2. **Atomické zmeny**
   ```python
   # Jedna migrácia = jedna logická zmena
   # Nie: pridať tabuľku + zmeniť inú + migrovať dáta
   ```

3. **Záloha pred produkčnou migráciou**
   ```bash
   pg_dump -Fc gitpulse > backup_before_migration.dump
   alembic upgrade head
   ```

4. **Review autogenerated kód**
   ```python
   # Alembic nedetekuje všetko správne
   # - Premenovanie stĺpca -> drop + add
   # - Zmena typu -> môže stratiť dáta
   ```

### Anti-patterns

```python
# 1. Hardcoded dáta v upgrade
def upgrade():
    op.execute("INSERT INTO users VALUES (1, 'admin', 'admin@example.com')")
    # Čo ak user už existuje?

# 2. DROP bez zálohy dát
def upgrade():
    op.drop_column('users', 'legacy_field')  # Dáta stratené navždy

# 3. Chýbajúci downgrade
def downgrade():
    pass  # Nemožné vrátiť späť!
```

## Produkčný deployment

### Migrácia v CI/CD

```yaml
# .gitlab-ci.yml
migrate:
  stage: deploy
  script:
    - alembic upgrade head
  only:
    - main
  when: manual  # Manuálne spustenie pre bezpečnosť
```

### Docker entrypoint

```bash
#!/bin/bash
# docker-entrypoint.sh

# Čakať na databázu
while ! pg_isready -h $DB_HOST -p $DB_PORT; do
    echo "Waiting for database..."
    sleep 2
done

# Spustiť migrácie
alembic upgrade head

# Spustiť aplikáciu
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Troubleshooting

### "Target database is not up to date"

```bash
# Označiť aktuálny stav ako migrated
alembic stamp head

# Alebo špecifická verzia
alembic stamp 018
```

### "Can't locate revision"

```bash
# Zobraziť históriu
alembic history

# Opraviť broken chain
alembic stamp --purge
alembic stamp head
```

### Konfliktné migrácie

```bash
# Ak dva vývojári vytvorili migrácie súčasne:
# 1. Premenovať jednu (zmeniť revision ID)
# 2. Upraviť down_revision reťaz
```

## Ďalšie čítanie

- [Alembic dokumentácia](https://alembic.sqlalchemy.org/)
- [Štruktúra projektu](struktura.md)
- [Prispievanie](prispievanie.md)

