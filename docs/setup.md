# Setup

This project supports two development paths:

- fully containerised with `docker-compose`
- native Python virtualenv with Docker only for PostgreSQL and Redis

The Sprint 1 FastAPI scaffold is present. Run migrations before opening
SQLAdmin for the first time.

## Prerequisites

- Python 3.12+
- Docker
- `docker-compose`

## Fully Containerised

Create local environment settings:

```bash
cp infra/docker/.env.example infra/docker/.env
```

Edit `infra/docker/.env` if you need to change ports, database credentials, or
container names.

Docker Compose reads environment values from the file passed with `--env-file`.
In this repo, defaults live in `infra/docker/.env.example` and local values live
in ignored file `infra/docker/.env`.

`infra/docker/docker-compose.yml` keeps stable Compose service keys such as
`app`, `worker`, `db`, and `redis` because `depends_on` needs stable keys. The
configurable names in `infra/docker/.env` are used for container names, internal
host aliases, URLs, ports, database credentials, queue name, and the Postgres
volume name.

Docker build ignores are intentionally duplicated in the root `.dockerignore`
and `infra/docker/Dockerfile.dockerignore`. Older `docker-compose` builds use
the root `.dockerignore` because the build context is the repository root.

For shorter commands in a shell session:

```bash
COMPOSE="docker-compose --env-file infra/docker/.env -f infra/docker/docker-compose.yml"
```

Build all images:

```bash
$COMPOSE build
```

Start the app, PostgreSQL, Redis, and the RQ worker:

```bash
$COMPOSE up
```

If you changed Dockerfile, dependency, image, or Compose settings, prefer a
clean recreate:

```bash
$COMPOSE down --remove-orphans
$COMPOSE up --build
```

After the Sprint 1 app scaffold exists, run migrations:

```bash
$COMPOSE exec app alembic upgrade head
```

Run tests in Docker:

```bash
$COMPOSE run --rm app pytest
```

Run one test file:

```bash
$COMPOSE run --rm app pytest tests/unit/test_availability.py
```

Open the app:

```text
http://127.0.0.1:8000
```

Expected Sprint 1 admin URL:

```text
http://127.0.0.1:8000/admin/sql
```

If you changed `APP_HOST_PORT` in `infra/docker/.env`, use that port instead.

## Infrastructure Checks

Verify infrastructure services directly:

```bash
$COMPOSE ps
```

Check PostgreSQL:

```bash
$COMPOSE exec db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

Check Redis:

```bash
$COMPOSE exec redis redis-cli ping
```

Expected Redis response:

```text
PONG
```

## Native Python With Docker Services

Start PostgreSQL and Redis only:

```bash
$COMPOSE up db redis
```

Create and activate a virtualenv:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

After `pyproject.toml` exists, install the app and dev dependencies:

```bash
pip install -e ".[dev]"
```

Export local service settings:

```bash
export ZMART_BOOKING_DATABASE_HOST=localhost
set -a
. infra/docker/.env
set +a
export ZMART_BOOKING_DATABASE_PORT="$POSTGRES_HOST_PORT"
export ZMART_BOOKING_DATABASE_NAME="$POSTGRES_DB"
export ZMART_BOOKING_DATABASE_USER="$POSTGRES_USER"
export ZMART_BOOKING_DATABASE_PASSWORD="$POSTGRES_PASSWORD"
export ZMART_BOOKING_REDIS_URL="redis://localhost:$REDIS_HOST_PORT/$REDIS_DB"
```

Run migrations:

```bash
alembic upgrade head
```

Run the FastAPI app:

```bash
uvicorn app.main:app --reload
```

Run the RQ worker:

```bash
rq worker --url "$ZMART_BOOKING_REDIS_URL" default
```

Run tests:

```bash
pytest
```

## Common Docker Commands

Show the fully resolved Docker Compose config:

```bash
$COMPOSE config
```

Stop containers:

```bash
$COMPOSE down
```

Stop containers and remove database volume:

```bash
$COMPOSE down -v
```

Rebuild after dependency changes:

```bash
$COMPOSE build --no-cache app worker
```

Open a shell in the app container:

```bash
$COMPOSE run --rm app sh
```

## Troubleshooting

### `KeyError: 'ContainerConfig'`

This is a known failure mode with legacy `docker-compose` v1.29.2 and newer
Docker image metadata when Compose tries to recreate an existing container.

Fix it by removing the existing containers and recreating them. This keeps the
PostgreSQL volume because it does not use `-v`:

```bash
$COMPOSE down --remove-orphans
$COMPOSE up --build
```

If you deliberately want a fresh database too:

```bash
$COMPOSE down -v --remove-orphans
$COMPOSE up --build
```

## Notes For Sprint 1 Implementation

- Keep setup commands in this file accurate.
- Keep the root README pointing here.
- Use `docker-compose`, not `docker compose`.
- Keep local Docker files under `infra/docker/`.
- The containerised path should run the app, database, Redis, worker, migrations,
  and tests.
- The native path should use a virtualenv and Docker-hosted PostgreSQL/Redis.
