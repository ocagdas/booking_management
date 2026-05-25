# Copilot Instructions For Booking Management

## Product Direction

Build the platform sprint by sprint. Start small, prove one workflow end to end,
and only generalise when a real second use case needs it.

The first use case is a hairdresser booking system with an internal-admin-first
workflow.

## Sprint 1 Scope

Sprint 1 includes:

- FastAPI
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- Pydantic v2
- SQLAdmin
- Jinja2
- HTMX
- Redis
- RQ
- Pytest
- Docker Compose using the `docker-compose` command

Sprint 1 does not include:

- customer accounts or login
- payments
- vouchers
- loyalty
- billing
- SMS or email provider integrations
- multi-industry templates
- complex domain YAML generation
- React or any frontend build pipeline

## Architecture Rules

- Keep routes thin.
- Keep business logic in service modules.
- SQLAdmin views may adapt forms and display data, but must not contain booking
  rules.
- HTMX handlers may return fragments, but must not contain booking rules.
- RQ jobs must call services instead of duplicating domain logic.
- Use SQLAlchemy models directly from services in Sprint 1. Do not add a
  repository layer until repeated query complexity makes it useful.

## Sprint 1 Domain

Use these entities only unless the roadmap is updated first:

- Business
- Location
- LocationWorkingHours
- LocationBreak
- Staff
- Service
- Customer
- Booking
- AuditLog

Domain rules:

- Creating a Business automatically creates one default Location.
- A Business may have more locations later, but Sprint 1 only needs the default
  location plus the ability to add additional locations internally.
- Each Staff member belongs to one Business and one Location.
- Each Service belongs to one Business and can be offered at one or more
  Locations.
- Booking end time is calculated from selected start time plus the resolved
  Service duration.
- Services support fixed duration, customer-selected variable duration, and
  admin-defined duration.
- Services can hide duration information from the customer-facing UI.
- Services can define a fixed gap after bookings, and each Booking can override
  that gap in minutes or hours.
- Availability must account for booking duration plus post-booking gap.
- Available start times must fit fully inside location working hours.
- Available start times must not overlap any location break.
- Available start times must not overlap confirmed or pending approval bookings.
- Rejected and cancelled bookings do not block availability.
- Services support `auto` and `manual` approval modes.
- Auto approval creates a confirmed booking.
- Manual approval creates a pending approval booking and blocks the slot until
  approved or rejected.

## UI And Admin Rules

- Internal admin comes first.
- Use SQLAdmin for Sprint 1 setup and management screens.
- Use HTMX only where it improves a focused workflow, such as refreshing
  available booking start times.
- Put essential and commonly edited SQLAdmin fields near the top of forms.
- Use dropdowns for single-choice lists.
- Use checkboxes or multi-select controls for multiple choices.
- Use radio buttons only for small, high-importance choices.
- Do not require users to type or choose raw database IDs.
- Raw entity IDs may be exposed as read-only technical fields.
- When linking entities, users should select human-readable names from dropdowns
  or multi-select controls.
- Where an entity relationship is obvious, auto-pick it. For example, use the
  default Location when a Business has only one Location.
- Customer information is manually entered during booking in Sprint 1. Future
  login work may prefill it automatically.
- Duration visibility is a display rule only. Hidden duration must still be used
  for availability, end-time calculation, and gap calculation.

## Testing Rules

- Every feature must be tested.
- Every business rule must have service-level tests.
- Every route must have tests.
- UI behavior must be tested, including rendered SQLAdmin-critical pages and
  HTMX fragments.
- Test dropdown and multi-select behavior where it affects user correctness.
- Add regression tests for every bug found during implementation.

## Delivery Rules

- Work one sprint at a time.
- Do not add features outside the active sprint.
- Update the roadmap when scope or design rules change.
- Update this file when implementation rules change.
- Keep setup and test commands accurate for `docker-compose`.
- Keep install, run, migration, worker, and test instructions in `docs/setup.md`.
- Keep the root README pointing to `docs/setup.md`.
- Keep local Docker and Compose files under `infra/docker/`.

## Source Of Truth

- Roadmap: `docs/roadmaps/fastapi_booking_platform_roadmap.md`
- Setup guide: `docs/setup.md`
- Current milestone: Sprint 1, internal-admin-first hairdresser booking foundation
