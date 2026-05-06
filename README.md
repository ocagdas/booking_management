# zmart_booking

Configurable booking and resource management platform for service businesses, built incrementally on FastAPI.

## Status

Phase 0 is now scaffolded:
- FastAPI app package
- `GET /health`
- PostgreSQL settings
- SQLAlchemy and Alembic setup
- pytest support
- Docker Compose support

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

## Initial implementation target

The current build milestone is Phase 0 from the roadmap:
- create the FastAPI project skeleton
- add a health endpoint
- configure PostgreSQL and Alembic
- add pytest support
- add Docker Compose
- keep the repository structure aligned with the planned architecture

## Working approach

We can keep refining the roadmap as implementation progresses. The roadmap in `docs/roadmaps/` is intended to stay as the main planning document for future updates.
