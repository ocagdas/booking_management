# zmart_booking

Configurable booking and resource management platform for service businesses, built incrementally on FastAPI.

## Status

Phase 1 is complete:
- FastAPI app package
- `GET /health`
- PostgreSQL settings
- SQLAlchemy and Alembic setup
- pytest support (verbose output by default)
- Docker Compose support
- Core models: Business, Location, Service, Staff, StaffRole, Resource, Customer, Booking, BookingStaff, BookingResource, AuditLog
- Alembic migrations for all Phase 1 tables
- Unit tests for all Phase 1 acceptance criteria

SQLAdmin is intentionally deferred to the next step.

## Product direction

The platform is intended to support businesses such as garages, barbers, clinics, tutors, equipment hire teams, and mobile service operators.

Planned capabilities include:
- configurable services, staff, resources, and customers
- booking workflows with auto, manual, and hybrid approval
- conflict-aware availability checks for staff and resources
- promotions, vouchers, loyalty, and customer balance support
- internal admin tooling, starting later with SQLAdmin and then HTMX workflows
- billing and subscription support in later phases

## Planned stack

- FastAPI
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- Pydantic v2
- Jinja2
- HTMX later
- Pytest
- Docker Compose
- Redis and RQ later
- Stripe Billing later

## Architecture rules

- business logic must live in service modules
- FastAPI routes should stay thin
- booking, voucher, and balance operations should use transactional workflows
- SQLAdmin and HTMX remain future admin concerns, not part of Phase 0

## Key documents

- roadmap: `docs/roadmaps/fastapi_booking_platform_roadmap.md`
- Copilot instructions: `.github/copilot-instructions.md`

## Project layout

```text
app/
  api/
  core/
  models/
tests/
alembic/
docker-compose.yml
pyproject.toml
```

## Local Docker customisation

Docker Compose automatically merges `docker-compose.override.yml` on top of
`docker-compose.yml`.  This file is gitignored so you can customise your local
setup without affecting other developers.

To create your override:

```bash
cp docker-compose.override.yml.example docker-compose.override.yml
# edit as needed, then:
docker compose up --build
```

Common uses:

| Setting | Default | Override example |
|---|---|---|
| App host port | 8000 | `"8001:8000"` |
| Postgres host port | 5432 | `"5433:5432"` |
| Postgres volume name | `postgres_data` | any name you like |

## Setup paths

The repository supports both Docker-first and local/native-first workflows.

### Option 1: Docker-first

1. Start the application and PostgreSQL:

   ```bash
   docker compose up --build
   ```

2. In another shell, run migrations:

   ```bash
   docker compose exec app alembic upgrade head
   ```

3. Verify the app:

   ```bash
   curl http://127.0.0.1:8000/health
   ```

### Option 2: Local/native-first

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install the app and development dependencies:

   ```bash
   pip install -e ".[dev]"
   ```

3. Start a local PostgreSQL instance and export settings as needed:

   ```bash
   export ZMART_BOOKING_DATABASE_HOST=localhost
   export ZMART_BOOKING_DATABASE_PORT=5432
   export ZMART_BOOKING_DATABASE_NAME=zmart_booking
   export ZMART_BOOKING_DATABASE_USER=postgres
   export ZMART_BOOKING_DATABASE_PASSWORD=postgres
   ```

4. Run migrations:

   ```bash
   alembic upgrade head
   ```

5. Start the app:

   ```bash
   uvicorn app.main:app --reload
   ```

6. Verify the app:

   ```bash
   curl http://127.0.0.1:8000/health
   pytest
   ```

## Current implementation milestone

Phase 1 (core models) is complete.  The next milestone is Phase 2: SQLAdmin.

## Working approach

We can keep refining the roadmap as implementation progresses. The roadmap in `docs/roadmaps/` is intended to stay as the main planning document for future updates.
