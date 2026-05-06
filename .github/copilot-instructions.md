# Copilot instructions for booking_management

## Project scope

Build a configurable booking, resource allocation, approval, voucher, loyalty, and billing platform for service businesses.

## Primary stack

- FastAPI
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- Pydantic v2
- SQLAdmin
- Jinja2
- HTMX later
- Pytest
- Docker Compose
- Redis and RQ later
- Stripe Billing later

## Architecture rules

- Keep business logic in service modules.
- Keep FastAPI route handlers thin.
- Do not place business logic inside SQLAdmin views.
- Do not place business logic inside HTMX handlers.
- Routes and admin adapters should call service functions.
- SQLAdmin and HTMX admin should be able to coexist.

## Domain rules

- Prevent overlapping bookings for the same resource.
- Prevent overlapping bookings for the same staff member.
- Use transactions for booking creation, voucher redemption, and balance spending.
- Do not allow single-use codes to be redeemed twice.
- Do not allow customer balance to go negative.
- Only award loyalty when a booking becomes completed.
- Create audit logs for important booking, award, and promotion events.

## Delivery rules

- Work incrementally by roadmap phase.
- Do not add features outside the current task.
- Update the README when setup or usage changes.
- Add tests for important service-layer behavior.

## Source of truth

- Roadmap: `docs/roadmaps/fastapi_booking_platform_roadmap.md`
- Current starting point: Phase 0 project skeleton
