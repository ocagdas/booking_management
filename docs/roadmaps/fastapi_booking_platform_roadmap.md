# FastAPI Booking Platform Roadmap

## Reset Decision

The previous implementation became too broad too quickly. The project is reset
to a sprint-style delivery model.

The implementation is wiped at reset. The repo keeps only planning files and
minimal setup/container files so the next sprint has a known run path:

- `.github/copilot-instructions.md`
- `infra/docker/Dockerfile`
- `infra/docker/docker-compose.yml`
- `infra/docker/.env.example`
- `docs/setup.md`
- `docs/roadmaps/fastapi_booking_platform_roadmap.md`
- `README.md`

All implementation files will be recreated from the active sprint plan.

## Product Goal

Build a booking management platform one business workflow at a time.

The first workflow is an internal-admin-first hairdresser booking system. The
goal is to prove the core admin setup, booking lifecycle, availability logic,
and approval flow before expanding into a more generic platform.

## Core Architecture Decision

Sprint 1 uses:

- FastAPI for the web application
- PostgreSQL as the system of record
- SQLAlchemy 2.x for models and database access
- Alembic for migrations
- Pydantic v2 for request and response validation
- SQLAdmin for internal admin screens
- Jinja2 for server-rendered HTML
- HTMX for focused dynamic UI fragments
- Redis and RQ for background job infrastructure
- Pytest for tests
- Docker Compose using the `docker-compose` command

Do not introduce React, a frontend build pipeline, payments, vouchers, loyalty,
or customer login in Sprint 1.

## High Level Architecture

Sprint 1 should stay intentionally simple:

```text
FastAPI app
    ↓
Routes and SQLAdmin adapters
    ↓
Service modules
    ↓
SQLAlchemy models
    ↓
PostgreSQL
```

Rules:

- Routes collect input and return responses.
- SQLAdmin adapts database models for internal users.
- HTMX handlers return focused HTML fragments.
- Services contain business decisions.
- Models describe persistence.
- RQ jobs call services.

Do not add a repository layer in Sprint 1 unless the roadmap is updated first.

## Sprint 1 Theme

Internal-admin-first hairdresser booking foundation.

The admin user should be able to configure a hairdresser business, locations,
staff, services, working hours, breaks, customers, and bookings.

The public/customer-facing experience can remain minimal. Sprint 1 focuses on
the internal admin workflow and correctness of booking rules.

## Sprint 1 Entities

### Business

Represents one hairdresser business.

Essential fields:

- ID, read-only
- name
- slug
- created_at, read-only
- updated_at, read-only

Rules:

- Creating a Business automatically creates one default Location.
- The default Location should use a clear name such as `Default location` unless
  a better name is provided.

### Location

Represents a branch or physical place where services are delivered.

Essential fields:

- ID, read-only
- business, selected by name
- business_id, read-only
- name
- is_default
- created_at, read-only
- updated_at, read-only

Rules:

- Every Location belongs to one Business.
- A Business may have multiple Locations.
- Sprint 1 should auto-pick the default Location when a Business has only one
  Location.
- Location selection should use a dropdown by name.
- Raw location IDs may be displayed as read-only technical fields.

### LocationWorkingHours

Represents opening and closing times for a Location on a day of the week.

Essential fields:

- ID, read-only
- location, selected by name
- location_id, read-only
- day_of_week
- opens_at
- closes_at
- is_closed

Rules:

- Use one row per Location and day of week.
- Available booking start times must fit fully between `opens_at` and
  `closes_at`.
- If `is_closed` is true, no booking start times are available for that day.

### LocationBreak

Represents one break window inside a Location's working day.

Essential fields:

- ID, read-only
- location, selected by name
- location_id, read-only
- day_of_week
- starts_at
- ends_at

Rules:

- A Location can have zero, one, or many breaks per day.
- Booking windows must not overlap breaks.

### Staff

Represents a hairdresser or internal team member who can deliver a service.

Essential fields:

- ID, read-only
- business, selected by name
- business_id, read-only
- location, selected by name
- location_id, read-only
- name
- role
- is_active

Rules:

- Every Staff member belongs to one Business.
- Every Staff member belongs to one Location in Sprint 1.
- If the Business has one Location, auto-pick it.

### Service

Represents a service such as haircut, colour, or treatment.

Essential fields:

- ID, read-only
- business, selected by name
- business_id, read-only
- name
- duration_type
- fixed_duration_value
- fixed_duration_unit
- variable_min_duration_value
- variable_min_duration_unit
- variable_max_duration_value
- variable_max_duration_unit
- variable_increment_value
- variable_increment_unit
- admin_duration_value
- admin_duration_unit
- hide_duration_from_customer
- hide_duration_completely
- gap_after_value
- gap_after_unit
- price
- approval_mode
- offered locations, multi-select by name
- is_active

Rules:

- Every Service belongs to one Business.
- A Service can be offered at one or more Locations.
- Location assignment should use a multi-select or checkbox control.
- Approval mode is either `auto` or `manual`.
- Duration type is selected by the admin.
- Fixed duration means the Service always takes a configured amount of time,
  such as 30 minutes, 2 hours, or 1 day.
- Variable duration means the customer or admin selects a duration within
  configured minimum, maximum, and increment values.
- Admin-defined duration means the duration is set by the admin during booking
  or approval instead of being selected by the customer.
- Duration units are minutes, hours, or days.
- Booking end time is calculated from selected start time plus the resolved
  Service duration.
- `hide_duration_from_customer` hides duration details from customer-facing
  screens but still allows internal admins to see them.
- `hide_duration_completely` hides duration from all non-technical displays
  where possible, while still using it internally for availability.
- `gap_after_value` and `gap_after_unit` define a default buffer after each
  Booking.
- The default gap after a Service can be adjusted per Booking.

### Service Duration Types

| Type | Meaning | Example |
|---|---|---|
| fixed | Service always has the same duration. | Haircut is 30 minutes. |
| variable_customer_selected | Duration is selected within min, max, and increment rules. | Colour treatment from 1 to 3 hours in 30 minute increments. |
| admin_defined | Admin sets duration during booking or approval. | Consultation length confirmed internally. |

Duration rules:

- Fixed duration requires a duration value and unit.
- Variable duration requires minimum, maximum, increment, and unit values.
- Variable duration start times must only be offered if the selected duration
  plus gap can fit.
- Admin-defined duration must be resolved before a Booking can be confirmed.
- Duration visibility does not affect booking calculations.
- Hidden duration is still used for availability and end-time calculation.
- For customer-facing screens, hidden duration should not appear in labels,
  summaries, or confirmation copy.
- For internal admin screens, hidden duration can remain available as a
  technical or operational field unless `hide_duration_completely` is set.

### Gap After Service

The gap after a booking is extra blocked time after the service ends. It can be
used for cleanup, preparation, travel, or reset time.

Rules:

- A Service can define a default gap after booking.
- Gap units are minutes or hours.
- Each Booking can override the Service gap.
- Booking `ends_at` represents the service end time.
- Availability blocking uses `ends_at` plus the resolved gap.
- Available start times must not overlap another Booking's service window or
  blocked gap window.

### Customer

Represents the person receiving the service.

Essential fields:

- ID, read-only
- business, selected by name
- business_id, read-only
- name
- email
- phone

Rules:

- Customer details are manually entered in Sprint 1 booking screens.
- Future login work may prefill customer details automatically.

### Booking

Represents one appointment request.

Essential fields:

- ID, read-only
- business, selected by name
- business_id, read-only
- location, selected by name or auto-picked
- location_id, read-only
- service, selected by name
- service_id, read-only
- staff, selected by name
- staff_id, read-only
- customer, selected by name or created from entered details
- customer_id, read-only
- selected_duration_value
- selected_duration_unit
- starts_at
- ends_at, read-only and calculated
- gap_after_value
- gap_after_unit
- blocked_until, read-only and calculated
- status
- notes

Statuses:

- pending_approval
- confirmed
- rejected
- cancelled
- completed
- no_show

Rules:

- User selects start time only.
- System calculates end time from resolved Service duration.
- Fixed duration Services auto-fill the selected duration.
- Variable duration Services require a selected duration within Service limits.
- Admin-defined duration Services require an admin-provided duration before
  confirmation.
- System calculates `blocked_until` from `ends_at` plus the resolved gap after.
- Available start times must not go beyond close time minus resolved Service
  duration and resolved gap.
- Available start times must not overlap breaks.
- Available start times must not overlap confirmed bookings.
- Available start times must not overlap pending approval bookings.
- Auto approval Services create confirmed Bookings.
- Manual approval Services create pending approval Bookings.
- Pending approval Bookings block the time slot.
- Rejecting a pending approval Booking releases the time slot.
- Cancelling a Booking releases the time slot.

### AuditLog

Represents important internal events.

Essential fields:

- ID, read-only
- business_id, read-only
- entity_type
- entity_id, read-only where possible
- action
- payload
- created_at, read-only

Rules:

- Booking creation creates an audit log.
- Booking approval creates an audit log.
- Booking rejection creates an audit log.
- Booking cancellation creates an audit log.

## UI And Form Design Rules

- Internal admin comes first.
- Put essential and commonly edited SQLAdmin fields near the top of forms.
- Use dropdowns for single-choice lists.
- Use checkboxes or multi-select controls for multiple choices.
- Use radio buttons only for small, high-importance choices.
- Do not require users to type or choose raw database IDs.
- Raw entity IDs may be displayed as read-only fields.
- When linking entities, users select human-readable names.
- When an entity relationship is obvious, auto-pick it.
- If a Business has exactly one Location, default to that Location.
- If a Service is offered at exactly one Location, default to that Location.
- If Staff belongs to one Location, infer the Location where appropriate.

## Availability Rules

To generate available start times:

1. Read the selected Service duration.
2. Resolve duration from fixed, variable, or admin-defined rules.
3. Read Location working hours for the selected date.
4. Exclude the day if the Location is closed.
5. Generate candidate start times at the configured interval.
6. Calculate candidate end time as start time plus resolved Service duration.
7. Calculate candidate blocked-until time as end time plus resolved gap after.
8. Exclude candidates where blocked-until time is after closing time.
9. Exclude candidates overlapping any LocationBreak.
10. Exclude candidates overlapping any confirmed Booking.
11. Exclude candidates overlapping any pending approval Booking.
12. Return only valid start times.

Rejected and cancelled Bookings do not block availability.

## Approval Rules

Services support two approval modes:

| Mode | Booking behavior |
|---|---|
| auto | Booking is created as confirmed and blocks the slot. |
| manual | Booking is created as pending approval and blocks the slot. |

Admin workflow for manual approval:

```text
Pending approval list
    ↓
Admin opens booking
    ↓
Approve or reject
    ↓
Approved becomes confirmed
Rejected releases slot
```

## RQ Scope

Sprint 1 should wire Redis and RQ but keep the job simple.

Acceptable first jobs:

- enqueue booking-created audit side effect
- enqueue placeholder booking confirmation job

Do not integrate email, SMS, Stripe, accounting, or external providers in
Sprint 1.

## Testing Rules

Everything in Sprint 1 must be tested.

Required test types:

- model tests
- migration smoke tests
- service tests
- route tests
- SQLAdmin page tests for critical model pages
- HTMX fragment tests
- RQ job tests
- UI HTML tests for dropdowns, multi-selects, and read-only IDs where relevant

Minimum service tests:

- Business creation creates default Location.
- Service can be linked to multiple Locations.
- Booking end time is calculated automatically.
- Fixed duration service calculates expected end time.
- Variable duration service rejects durations below minimum.
- Variable duration service rejects durations above maximum.
- Variable duration service rejects durations outside configured increment.
- Admin-defined duration must be resolved before confirmation.
- Hidden duration does not appear in customer-facing HTML.
- Service default gap blocks availability after service end.
- Booking-level gap override changes blocked-until time.
- Available start times do not exceed close time minus duration and gap.
- Available start times exclude breaks.
- Confirmed bookings block availability.
- Pending approval bookings block availability.
- Rejected bookings do not block availability.
- Cancelled bookings do not block availability.
- Auto approval creates confirmed Booking.
- Manual approval creates pending approval Booking.
- Rejecting a pending approval Booking releases the slot.

## Sprint 1 Deliverables

1. Fresh FastAPI project scaffold.
2. Docker Compose setup using `docker-compose`.
3. PostgreSQL database setup.
4. SQLAlchemy models for Sprint 1 entities.
5. Alembic migrations.
6. SQLAdmin mounted for internal admin.
7. SQLAdmin forms ordered around essential editable fields.
8. HTMX fragment for available booking start times.
9. Redis and RQ wired with one minimal job.
10. Booking service with availability and approval rules.
11. Tests for models, services, routes, SQLAdmin pages, HTMX fragments, and RQ.
12. README created with local, Docker, test, migration, app, worker commands.
13. `docs/setup.md` kept as the source of truth for install, run, and test
    commands.

## Future Sprints

Potential future work, not Sprint 1:

- public customer booking polish
- customer login
- automatic customer info prefill
- staff-specific working hours
- staff breaks
- service categories
- payments
- vouchers
- loyalty
- notifications
- multi-business deployment strategy
- branded customer pages
