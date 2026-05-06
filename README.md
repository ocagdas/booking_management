# Booking Management

Configurable booking and resource management platform for service businesses, planned around a FastAPI-based architecture.

## Status

This repository is currently in the planning and setup stage.

## Product direction

The platform is intended to support businesses such as garages, barbers, clinics, tutors, equipment hire teams, and mobile service operators.

Planned capabilities include:
- configurable services, staff, resources, and customers
- booking workflows with auto, manual, and hybrid approval
- conflict-aware availability checks for staff and resources
- promotions, vouchers, loyalty, and customer balance support
- internal admin tooling with SQLAdmin first and HTMX workflows later
- billing and subscription support in later phases

## Planned stack

- FastAPI
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- Pydantic v2
- SQLAdmin
- Jinja2
- HTMX
- Redis and RQ
- Stripe Billing later

## Architecture rules

- business logic must live in service modules
- FastAPI routes should stay thin
- SQLAdmin views must not contain business logic
- HTMX handlers must not contain business logic
- booking, voucher, and balance operations should use transactional workflows

## Key documents

- roadmap: `/home/runner/work/booking_management/booking_management/docs/roadmaps/fastapi_booking_platform_roadmap.md`
- Copilot instructions: `/home/runner/work/booking_management/booking_management/.github/copilot-instructions.md`

## Initial implementation target

The first build milestone is Phase 0 from the roadmap:
- create the FastAPI project skeleton
- add a health endpoint
- configure PostgreSQL and Alembic
- add pytest support
- add Docker Compose
- keep the repository structure aligned with the planned architecture

## Working approach

We can keep refining the roadmap as implementation progresses. The roadmap in `docs/roadmaps/` is intended to stay as the main planning document for future updates.
