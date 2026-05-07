# FastAPI Booking Platform Roadmap

## 1. Product goal

Build a configurable booking, resource allocation, approval, voucher, loyalty and billing platform for small service businesses.

The system should support businesses such as:

| Business type | Example resources |
|---|---|
| Garage | MOT bay, service bay, mechanic |
| Barber | Chair, barber |
| Clinic | Room, practitioner |
| Tutor | Room, tutor |
| Equipment hire | Equipment item |
| Mobile service | Staff member, travel slot |

The platform should not be a Booksy clone. It should be a **configurable operations engine** for businesses that need more control than simple appointment scheduling.

---

## 2. Core architecture decision

Use:

```text
FastAPI
PostgreSQL
SQLAlchemy
Alembic
Pydantic
SQLAdmin
Jinja2
HTMX
Redis
RQ
Stripe later
```

### Key design rule

```text
Business logic must not live inside SQLAdmin, HTMX routes or API routes.
```

All business rules must live in service modules.

---

## 3. High level architecture

```text
FastAPI application
    ↓
API routes
    ↓
Application services
    ↓
Domain services
    ↓
Repositories
    ↓
SQLAlchemy models
    ↓
PostgreSQL
```

Admin interfaces:

```text
Admin adapters
    ↓
SQLAdmin for quick CRUD
HTMX admin for business workflows
API admin for future frontend
```

This allows SQLAdmin and custom HTMX admin to run side by side.

---

## 4. Admin strategy

### Phase 1 admin

Use SQLAdmin for quick internal CRUD.

```text
/admin/sql
```

Use it for:

| Area | Purpose |
|---|---|
| Businesses | Create and edit business records |
| Services | Manage service definitions |
| Staff | Manage staff records |
| Resources | Manage bays, rooms, chairs, equipment |
| Customers | View and edit customer records |
| Bookings | Inspect bookings |
| Promotions | Inspect vouchers and discounts |
| Loyalty | Inspect loyalty accounts |
| Audit logs | Inspect system activity |

### Phase 2 admin

Build custom HTMX admin pages for real workflows.

```text
/admin/app
```

Use it for:

| Page | Purpose |
|---|---|
| Pending bookings | Approve or reject bookings |
| Booking calendar | View bookings by time, staff and resource |
| Customer benefits | Award free sessions, credit and discounts |
| Voucher generator | Generate single use codes and campaign codes |
| Loyalty dashboard | View completed bookings and issued rewards |
| Billing status | View subscription state |
| Audit viewer | Search important admin actions |

### Phase 3 admin

Restrict SQLAdmin to platform owner only.

Business customers use HTMX admin.

---

## 5. Database choice

Use PostgreSQL as the main system of record.

Do not use MongoDB for the core platform.

Reason:

| Area | PostgreSQL advantage |
|---|---|
| Booking conflicts | Transactions and locking |
| Voucher redemption | Atomic updates |
| Customer balance | Prevent negative balance |
| Billing records | Strong consistency |
| Audit trail | Reliable joins and filtering |
| Resource allocation | Relational constraints |

Use PostgreSQL `JSONB` for flexible config snapshots and custom form data.

---

## 6. Tenant and deployment strategy

### Early pilot model

Use one deployment per customer.

```text
customer subdomain
    ↓
customer app instance
    ↓
customer database
    ↓
customer backup job
```

Example:

```text
abcgarage.yourdomain.co.uk
xyzclinic.yourdomain.co.uk
```

### Later model

Move to shared platform only when security tests and tenant isolation tests are mature.

Possible later options:

| Model | Use when |
|---|---|
| Separate deployment per customer | Early pilots |
| Shared app with separate database per customer | Safer paid tier |
| Shared app with shared database | Mature SaaS stage |

---

## 7. Domain and website strategy

Support two customer cases.

### Case 1: customer has no website

Generate a small business website.

Pages:

```text
Home
Services
Book appointment
Contact
Terms
Cancellation policy
```

Default domain:

```text
customername.yourdomain.co.uk
```

### Case 2: customer already has a website

Provide integration options.

| Option | Difficulty | Description |
|---|---:|---|
| Booking link | Easy | Button links to hosted booking page |
| Iframe embed | Medium | Booking page embedded into existing site |
| JavaScript widget | Later | Configurable booking widget |
| API integration | Later | Website calls backend directly |

Example booking link:

```html
<a href="https://abcgarage.yourdomain.co.uk/book">
  Book now
</a>
```

Example iframe:

```html
<iframe
  src="https://abcgarage.yourdomain.co.uk/embed/book"
  width="100%"
  height="800"
  style="border:0;">
</iframe>
```

---

## 8. Theme and branding

Use controlled theme configuration.

Example:

```yaml
theme:
  logo_url: "https://cdn.yourdomain.co.uk/abcgarage/logo.png"
  primary_colour: "#0f172a"
  accent_colour: "#2563eb"
  font_family: "Inter"
  border_radius: "8px"
  button_style: "filled"
```

Do not allow arbitrary custom CSS in the MVP.

---

## 9. Main modules

| Module | Responsibility |
|---|---|
| Businesses | Business profile, config, domain, theme |
| Services | Service names, duration, price, approval rules |
| Staff | Staff records, roles, availability |
| Resources | Rooms, bays, chairs, equipment |
| Customers | Customer details and history |
| Bookings | Appointment lifecycle |
| Availability | Staff and resource conflict detection |
| Approval | Auto, manual and hybrid approval |
| Promotions | Vouchers, discounts, free sessions |
| Loyalty | Rewards after completed bookings |
| Balance | Customer account credit |
| Notifications | Email, SMS later, reminders |
| Billing | Subscription plans and Stripe integration later |
| Accounting | Push invoices and credit notes to Xero, Sage, QuickBooks |
| Audit | Full history of important actions |
| Config loader | YAML or JSON driven business setup |

---

## 10. Booking state machine

Booking statuses:

```text
requested
pending_approval
confirmed
completed
cancelled
rejected
no_show
```

Allowed transitions:

| From | To |
|---|---|
| requested | pending_approval |
| requested | confirmed |
| pending_approval | confirmed |
| pending_approval | rejected |
| confirmed | completed |
| confirmed | cancelled |
| confirmed | no_show |

Invalid transitions must fail.

Example:

```text
completed cannot move back to confirmed
cancelled cannot move to completed
rejected cannot move to confirmed without a new booking request
```

---

## 11. Approval modes

Support three modes.

| Mode | Behaviour |
|---|---|
| auto | Booking is confirmed immediately if available |
| manual | Booking waits for admin approval |
| hybrid | Rules decide whether booking is auto confirmed or pending approval |

Example config:

```yaml
approval:
  mode: hybrid
  rules:
    mot:
      action: auto_approve
    full_service:
      action: require_approval
    diagnostic:
      action: require_approval
```

---

## 12. Promotion and benefit features

### Admin can award

| Benefit | Example |
|---|---|
| Free session | One free MOT |
| Account balance | £25 credit |
| Fixed discount | £10 off |
| Percentage discount | 10 percent off |
| Service specific discount | 15 percent off oil change |
| Customer specific code | Only one customer can use it |

### Customer can redeem

| Code type | Example | Behaviour |
|---|---|---|
| Public campaign code | MAY10 | Many customers can use it, once per customer |
| Single use code | X7K9P2Q1 | One use globally |
| Customer assigned code | OZFREE1 | Only assigned customer can use it |
| Loyalty code | LOYALTY10ABC | Generated after loyalty milestone |

---

## 13. Promotion validation rules

When a customer enters a code, check:

| Check | Required |
|---|---:|
| Code exists | Yes |
| Code is active | Yes |
| Within date window | Yes |
| Customer is allowed | Yes |
| Total use limit not exceeded | Yes |
| Per customer use limit not exceeded | Yes |
| Service is eligible | Yes |
| Minimum booking value is met | Yes |
| Code is not revoked | Yes |
| Code is not expired | Yes |
| Code stacking rules pass | Yes |

Voucher redemption must be transactional.

---

## 14. Loyalty rules

Start simple.

```text
After five completed bookings, issue one single use reward code.
```

Important rules:

| Event | Loyalty effect |
|---|---|
| Booking completed | Counts |
| Booking cancelled | Does not count |
| Booking no show | Does not count |
| Booking rejected | Does not count |
| Booking pending approval | Does not count |

Example config:

```yaml
loyalty:
  enabled: true
  mode: completed_booking_count
  rules:
    five_completed_bookings:
      threshold: 5
      reward:
        type: percentage_discount
        value: 10
        valid_days: 60
        max_uses_total: 1
        max_uses_per_customer: 1
```

---

## 15. Billing and subscriptions

This is for charging business customers.

Keep separate from customer appointment payments.

### Platform billing

Use Stripe Billing later.

| Item | Purpose |
|---|---|
| Plans | Starter, Professional, Operations |
| Subscriptions | Business subscription state |
| Usage records | SMS, bookings, staff, locations |
| Invoices | Stripe invoice references |
| Billing events | Stripe webhook audit |
| Cost records | Internal cost tracking |

Subscription states:

| State | Meaning |
|---|---|
| trialing | Trial active |
| active | Paid and active |
| past_due | Payment failed but grace period active |
| unpaid | Payment unresolved |
| cancel_at_period_end | Cancelled but active until period end |
| cancelled | Ended |
| suspended | Manually blocked |

MVP can start with manual billing before Stripe.

---

## 16. Recommended repository structure

```text
booking_platform/
  app/
    main.py

    core/
      config.py
      database.py
      security.py
      settings.py
      errors.py

    models/
      business.py
      location.py
      service.py
      staff.py
      resource.py
      customer.py
      booking.py
      promotion.py
      loyalty.py
      billing.py
      notification.py
      audit.py

    schemas/
      business.py
      booking.py
      promotion.py
      loyalty.py
      billing.py
      config.py

    repositories/
      booking_repository.py
      customer_repository.py
      promotion_repository.py
      resource_repository.py

    services/
      availability_service.py
      approval_service.py
      booking_service.py
      promotion_service.py
      loyalty_service.py
      balance_service.py
      notification_service.py
      billing_service.py
      accounting_service.py
      audit_service.py

    accounting/
      base.py           (AccountingProvider abstract base)
      xero.py           (XeroAdapter)
      sage.py           (SageAdapter)
      quickbooks.py     (QuickBooksAdapter)
      jobs.py           (RQ job functions for push and reconciliation)

    api/
      routes/
        health.py
        public_booking.py
        admin_bookings.py
        admin_promotions.py
        admin_customers.py
        billing.py

    admin/
      sqladmin/
        setup.py
        views.py
      htmx/
        routes.py
        templates/

    templates/
      public/
      admin/

    static/

  configs/
    templates/
      garage.yaml
      barber.yaml
      clinic.yaml

  tests/
    unit/
    integration/
    api/

  alembic/
  docker-compose.yml
  pyproject.toml
  README.md
```

---

## 17. Development roadmap

### Phase 0: Project skeleton

Goal:

```text
Create a working FastAPI project with database, migrations, tests and Docker.
```

Deliverables:

| Deliverable | Acceptance criteria |
|---|---|
| FastAPI app | App starts locally |
| Health endpoint | `GET /health` returns ok |
| PostgreSQL connection | App connects to database |
| SQLAlchemy setup | Base model works |
| Alembic setup | Migration runs |
| Pytest setup | Tests run |
| Docker Compose | App and database start |
| README | Setup instructions exist |

---

### Phase 1: Core models

Goal:

```text
Create the first database model set.
```

Models:

```text
Business
Location
Service
Staff
StaffRole
Resource
Customer
Booking
BookingStaff
BookingResource
AuditLog
```

Acceptance criteria:

| Test | Expected result |
|---|---|
| Create business | Succeeds |
| Create service | Linked to business |
| Create resource | Linked to business |
| Create customer | Linked to business |
| Create booking | Succeeds |
| Invalid booking time | Fails |
| Booking status choices | Enforced |

---

### Phase 2: SQLAdmin

Goal:

```text
Add SQLAdmin for fast internal CRUD.
```

Deliverables:

| Deliverable | Acceptance criteria |
|---|---|
| SQLAdmin mounted | `/admin/sql` loads |
| Model views | Core models visible |
| Basic filtering | Bookings and customers searchable |
| Restricted access placeholder | Admin auth plan documented |

---

### Phase 3: Availability engine

Goal:

```text
Prevent resource and staff conflicts.
```

Rules:

```text
Same resource cannot be booked for overlapping time
Same staff member cannot be booked for overlapping time
Non overlapping bookings are allowed
```

Acceptance tests:

| Test | Expected |
|---|---|
| Same resource overlapping | Rejected |
| Same resource non overlapping | Accepted |
| Different resource overlapping | Accepted |
| Same staff overlapping | Rejected |
| Same staff non overlapping | Accepted |

---

### Phase 4: Booking and approval engine

Goal:

```text
Create booking requests and apply approval rules.
```

Features:

| Feature | Description |
|---|---|
| Customer booking request | Creates booking |
| Auto approval | Booking becomes confirmed |
| Manual approval | Booking becomes pending approval |
| Admin approve | Booking becomes confirmed |
| Admin reject | Booking becomes rejected |
| Audit logging | Every status change logged |

Acceptance tests:

| Scenario | Expected |
|---|---|
| Auto approved service | Booking confirmed |
| Manual approval service | Booking pending approval |
| Admin approves booking | Booking confirmed |
| Admin rejects booking | Booking rejected |
| Invalid transition | Error |
| Status change | Audit log created |

---

### Phase 5: Public booking page

Goal:

```text
Create a simple customer booking page.
```

Use:

```text
Jinja2
HTMX
Server rendered forms
```

Pages:

| Page | Purpose |
|---|---|
| Services | Show available services |
| Select slot | Choose date and time |
| Customer details | Enter name, phone, email |
| Confirm request | Submit booking |
| Result | Show confirmed or pending approval |

Acceptance criteria:

| Test | Expected |
|---|---|
| Customer can select service | Works |
| Customer can submit booking | Works |
| Auto booking shows confirmed | Works |
| Manual booking shows pending approval | Works |

---

### Phase 6: HTMX admin workflows

Goal:

```text
Create business friendly admin pages for daily operations.
```

Pages:

| Page | Purpose |
|---|---|
| Pending approvals | Approve or reject bookings |
| Booking list | View bookings |
| Booking detail | View booking and customer details |
| Customer detail | View history and benefits |
| Audit log | View important actions |

Acceptance criteria:

| Action | Expected |
|---|---|
| Admin sees pending booking | Works |
| Admin approves from page | Booking confirmed |
| Admin rejects from page | Booking rejected |
| Audit log visible | Works |

Planned addition — Staff and Resource Availability Schedules:

```text
Staff and resources need a means to define when they are available.
Three modes must be supported:

1. Periodic — repeating weekly schedule (e.g. Mon–Fri 09:00–17:00).
2. Recurring — repeating on a custom cadence (e.g. every other Saturday).
3. Fully custom — arbitrary date/time windows with no recurrence pattern.

The availability engine must use these schedules to block slots where a
staff member or resource is not available, in addition to blocking slots
already occupied by existing bookings.
```

---

### Phase 7: Promotions and vouchers

Goal:

```text
Support public codes, single use codes and customer assigned codes.
```

Models:

```text
Promotion
PromotionRedemption
```

Features:

| Feature | Required |
|---|---:|
| Percentage discount | Yes |
| Fixed discount | Yes |
| Free session | Yes |
| Public campaign code | Yes |
| Single use generated code | Yes |
| Customer assigned code | Yes |
| Max uses total | Yes |
| Max uses per customer | Yes |
| Date window | Yes |
| Service restrictions | Yes |
| Revocation | Yes |

Acceptance tests:

| Scenario | Expected |
|---|---|
| MAY10 in valid month | Accepted |
| MAY10 outside valid month | Rejected |
| Same customer uses MAY10 twice | Second use rejected |
| Different customer uses MAY10 | Accepted |
| Single use code used twice | Second use rejected |
| Wrong service | Rejected |
| Revoked code | Rejected |

---

### Phase 8: Admin awarded benefits

Goal:

```text
Allow admin to award free sessions, account balance and discounts.
```

Models:

```text
AdminAward
CustomerBalance
CustomerBalanceTransaction
```

Admin actions:

| Action | Result |
|---|---|
| Award free session | Customer gets single use benefit |
| Award £ credit | Customer balance increases |
| Award fixed discount | Customer gets discount code |
| Award percentage discount | Customer gets discount code |
| Revoke award | Benefit becomes unusable |

Acceptance tests:

| Scenario | Expected |
|---|---|
| Award free session | Redeemable once |
| Award £25 credit | Balance increases |
| Spend £10 credit | Balance becomes £15 |
| Spend more than balance | Rejected |
| Revoke award | Cannot redeem |
| Award action | Audit log created |

---

### Phase 9: Loyalty engine

Goal:

```text
Reward customers after completed bookings.
```

Features:

| Feature | Required |
|---|---:|
| Loyalty account | Yes |
| Completed booking counter | Yes |
| Reward generation | Yes |
| Single use reward code | Yes |
| Expiry date | Yes |
| No reward for cancellation | Yes |
| No reward for no show | Yes |

Acceptance tests:

| Scenario | Expected |
|---|---|
| Five completed bookings | Reward generated |
| Four completed bookings | No reward |
| Cancelled booking | Does not count |
| No show booking | Does not count |
| Reward redeemed once | Works |
| Reward reused | Rejected |

---

### Phase 10: Notifications foundation

Goal:

```text
Create notification records before integrating real providers.
```

Models:

```text
Notification
NotificationTemplate
```

Events:

| Event | Notification |
|---|---|
| Booking requested | Customer and admin |
| Booking confirmed | Customer |
| Booking pending approval | Customer and admin |
| Booking rejected | Customer |
| Booking cancelled | Customer and admin |
| Reward issued | Customer |
| Voucher redeemed | Customer optional |

Acceptance criteria:

| Scenario | Expected |
|---|---|
| Booking confirmed | Notification row created |
| Booking rejected | Notification row created |
| Loyalty reward issued | Notification row created |

Real email can be added later.

---

### Phase 11: Billing foundation

Goal:

```text
Track business plans and feature access.
```

Models:

```text
Plan
Subscription
UsageRecord
BillingEvent
Invoice
CostRecord
```

Initial billing can be manual.

Features:

| Feature | Required |
|---|---:|
| Business plan | Yes |
| Subscription status | Yes |
| Feature gating | Yes |
| Usage records | Yes |
| Stripe later | Not in first version |

Acceptance tests:

| Scenario | Expected |
|---|---|
| Starter plan cannot use loyalty | Blocked |
| Professional plan can use loyalty | Allowed |
| Cancelled subscription | Read only mode |
| Past due subscription | Warning state |

---

### Phase 12: Stripe integration

Goal:

```text
Add real subscription billing.
```

Use:

```text
Stripe Checkout
Stripe Billing
Stripe Customer Portal
Stripe webhooks
```

Webhook handling must be idempotent.

Events:

```text
checkout.session.completed
customer.subscription.created
customer.subscription.updated
customer.subscription.deleted
invoice.paid
invoice.payment_failed
```

Acceptance tests:

| Scenario | Expected |
|---|---|
| Subscription created webhook | Local subscription active |
| Duplicate webhook | Ignored safely |
| Payment failed | Subscription past due |
| Subscription cancelled | Read only mode |
| Customer portal session | Created |

---

### Phase 13: Accounting software integration

Goal:

```text
Allow businesses to push invoices, credit notes and contact records to external
accounting platforms such as Xero, Sage Business Cloud and QuickBooks Online.

This phase is independent of payment collection. Businesses can use accounting
integration without Stripe. Invoices can be raised immediately for cash
transactions or with a future due date for deferred payment.
```

Design:

```text
Provider-agnostic adapter pattern.
Each accounting platform is a concrete adapter behind a common interface.
Business configuration drives which provider is active per business.
```

Independence from payment collection:

```text
Accounting integration does not require Stripe to be configured.
Stripe integration does not require accounting integration to be configured.
Both can be active at the same time, or either can be used alone.
Invoice due dates are controlled by payment_terms_days on AccountingSettings,
not by any Stripe payment schedule.
```

Models:

```text
AccountingSettings
  business_id
  provider (xero, sage, quickbooks, freeagent, none)
  client_id (encrypted at rest)
  client_secret (encrypted at rest)
  access_token (encrypted at rest)
  refresh_token (encrypted at rest)
  token_expires_at
  tenant_id (provider organisation or tenant reference)
  account_code_services (chart of accounts code for service lines)
  account_code_extras (chart of accounts code for extra lines)
  tax_rate_id (provider tax rate reference)
  invoice_prefix
  payment_terms_days (0 = due today, N = net N days)
  is_active

AccountingPushLog
  business_id
  booking_id (nullable)
  event_type (invoice_pushed, credit_note_pushed, contact_pushed, reconciliation)
  provider
  provider_reference (invoice or contact ID in the accounting system)
  status (queued, success, failed, retrying)
  attempts
  last_attempt_at
  error_message
  created_at
```

Adapter interface:

```text
AccountingProvider (abstract base)
  push_invoice(booking, settings) -> provider_reference
  push_credit_note(refund_or_cancellation, settings) -> provider_reference
  push_contact(customer, settings) -> provider_reference
  verify_connection(settings) -> bool

Concrete adapters (all behind the same interface):
  XeroAdapter        (OAuth 2.0 with PKCE)
  SageAdapter        (OAuth 2.0)
  QuickBooksAdapter  (OAuth 2.0)
```

Invoice behaviour:

| Mode | Behaviour |
|---|---|
| Cash (payment_terms_days = 0) | Invoice issued with due date set to today |
| Deferred (payment_terms_days > 0) | Invoice issued with due date set to today + N days |
| Credit note | Issued when a booking is cancelled after its invoice was already pushed |

Event triggers:

| Event | Action |
|---|---|
| Booking transitions to completed | Push invoice job enqueued |
| Booking cancelled (invoice already pushed) | Push credit note job enqueued |
| Customer record created or updated | Push or update contact job enqueued |
| Nightly schedule | Reconciliation job runs |

Queue behaviour:

```text
All pushes are dispatched as RQ background jobs.
Failed jobs are retried with exponential back-off.
Maximum five attempts before marking status as failed.
Failed pushes appear in the admin AccountingPushLog view and can be retried manually.
```

Webhook receiver:

```text
POST /webhooks/accounting/{provider}

Receives real-time events from accounting platforms.
Example: invoice marked as paid in Xero updates booking payment status.
All incoming events are written to AccountingPushLog before processing.
Webhook signatures must be verified before any action is taken.
```

Nightly reconciliation job:

```text
Runs via RQ scheduler.
Compares invoices pushed to the accounting system with completed bookings.
Flags discrepancies in AccountingPushLog.
Does not automatically overwrite data in either system.
```

Admin UI additions:

| View | Purpose |
|---|---|
| AccountingSettings list | View and edit per-business accounting provider config |
| Test Connection action | Calls verify_connection on the active provider |
| AccountingPushLog list | View push history, status and error messages |
| Retry action | Re-queue a failed push job |

Acceptance criteria:

| Test | Expected |
|---|---|
| AccountingSettings saved | Credentials stored encrypted, not in plaintext |
| Test Connection with valid credentials | Returns success |
| Test Connection with invalid credentials | Returns error message |
| Booking completed, provider active | Invoice push job enqueued |
| Push job succeeds | AccountingPushLog created with provider_reference |
| Push job fails transiently | Retried with exponential back-off |
| Push job fails five times | Status set to failed, visible in admin |
| Manual retry from admin | Job re-enqueued, attempt counter reset |
| Booking cancelled after invoice pushed | Credit note job enqueued |
| payment_terms_days is 0 | Invoice due date is today |
| payment_terms_days is 30 | Invoice due date is 30 days from today |
| Stripe not configured | Accounting integration still works |
| Accounting not configured | Stripe integration still works |
| Webhook received with valid signature | Event logged, action taken |
| Webhook received with invalid signature | Rejected with 400 |
| Nightly reconciliation runs | Discrepancies flagged in AccountingPushLog |

---

### Phase 14: Deployment and backups

Goal:

```text
Deploy first pilot customer safely.
```

Early deployment model:

```text
One customer
One app instance
One database
One backup pipeline
One subdomain
```

Required:

| Item | Required |
|---|---:|
| HTTPS | Yes |
| Environment variables | Yes |
| Database backups | Yes |
| Restore test | Yes |
| Error logging | Yes |
| Audit logging | Yes |
| Admin access control | Yes |

---

## 18. Testing strategy

### Unit tests

Test pure business logic.

```text
availability_service
approval_service
booking_service
promotion_service
balance_service
loyalty_service
billing_service
```

### Integration tests

Test database transactions.

```text
resource conflict
voucher redemption
balance spending
booking state changes
loyalty generation
```

### API tests

Test HTTP routes.

```text
create booking
approve booking
reject booking
validate voucher
apply voucher
award benefit
```

### UI tests later

Use Playwright later for important HTMX pages.

```text
pending approval page
customer award page
voucher generation page
booking form
```

---

## 19. Security requirements

### Do not build these from scratch

| Area | Use |
|---|---|
| Payment cards | Stripe Checkout |
| Subscription billing | Stripe Billing |
| Email delivery | Postmark, SendGrid or Mailgun |
| SMS | Twilio |
| Password auth in production | External auth provider or carefully reviewed library |

### Required security rules

| Rule | Required |
|---|---:|
| All secrets in environment variables | Yes |
| No secrets committed to Git | Yes |
| HTTPS in production | Yes |
| Business data isolation | Yes |
| Admin actions audited | Yes |
| Stripe webhooks verified | Yes |
| Raw SQL avoided | Yes |
| Inputs validated with Pydantic | Yes |
| Database transactions for critical actions | Yes |
| Backups tested | Yes |

---

## 20. Copilot agent master prompt

Use this as the prompt to start Copilot agent work.

```text
You are building a configurable appointment, resource allocation, approval, voucher, loyalty and billing platform.

Use this stack:
FastAPI
PostgreSQL
SQLAlchemy 2.x
Alembic
Pydantic v2
SQLAdmin
Jinja2
HTMX later
Pytest
Docker Compose
Redis and RQ later

The platform must support:
Business configuration
Services
Staff
Resources
Customers
Bookings
Resource conflict prevention
Staff conflict prevention
Auto approval
Manual approval
Hybrid approval
Promotions
Public voucher codes
Single use voucher codes
Customer assigned codes
Admin awarded free sessions
Admin awarded account balance
Admin awarded fixed discounts
Admin awarded percentage discounts
Loyalty rewards after completed bookings
Notification records
Audit logs
Subscription plan gating
Stripe Billing later

Important architecture rules:
Do not put business logic inside FastAPI route handlers.
Do not put business logic inside SQLAdmin views.
Do not put business logic inside HTMX handlers.
All business logic must live inside service modules.
Routes and admin views must call service functions.
Every important service function must have tests.
Use PostgreSQL transactions for booking creation, voucher redemption and balance spending.
Do not allow overlapping bookings for the same resource or same staff member.
Do not allow single use codes to be redeemed twice.
Do not allow customer balance to go negative.
Do not award loyalty for cancelled, rejected, pending or no show bookings.
Only award loyalty when a booking becomes completed.
Every booking status change must create an audit log.
Every admin award must create an audit log.
Every promotion redemption must create a redemption record.
SQLAdmin and HTMX admin must be able to coexist.
SQLAdmin is for early internal CRUD.
HTMX admin is for business workflows later.

Initial task:
Create the project skeleton.

Acceptance criteria:
1. FastAPI app starts.
2. GET /health returns ok.
3. PostgreSQL connection works.
4. SQLAlchemy base model is configured.
5. Alembic migration setup works.
6. Pytest runs.
7. Docker Compose starts app and database.
8. README explains setup, migration and test commands.
9. Project structure matches the planned architecture.
```

---

## 21. First Copilot task

```text
Create the initial FastAPI project skeleton.

Requirements:
1. Create a Python package called app.
2. Add app/main.py with FastAPI application.
3. Add app/core/settings.py for environment based settings.
4. Add app/core/database.py for SQLAlchemy engine and session.
5. Add app/api/routes/health.py with GET /health.
6. Add PostgreSQL support.
7. Add Alembic support.
8. Add Pytest support.
9. Add Docker Compose with app and PostgreSQL.
10. Add README with setup commands.

Acceptance criteria:
1. docker compose up starts the app.
2. GET /health returns {"status": "ok"}.
3. pytest runs successfully.
4. alembic upgrade head runs successfully.
5. No business logic is added yet.
```

---

## 22. Second Copilot task

```text
Implement the first domain models and migrations.

Create SQLAlchemy models:
Business
Location
Service
Staff
StaffRole
Resource
Customer
Booking
BookingStaff
BookingResource
AuditLog

Requirements:
1. Every business owned model must include business_id.
2. Booking must include status, start_time and end_time.
3. Booking status must support:
   requested
   pending_approval
   confirmed
   completed
   cancelled
   rejected
   no_show
4. Add created_at and updated_at where useful.
5. Add Alembic migration.
6. Add SQLAdmin views for the models.
7. Add tests for model persistence.

Acceptance criteria:
1. Migration creates all tables.
2. Tests can create a business, service, customer, resource and booking.
3. Booking with end_time before start_time fails validation.
4. SQLAdmin loads at /admin/sql.
```

---

## 23. Third Copilot task

```text
Implement resource and staff availability checking.

Create:
availability_service.py

Requirements:
1. Check if a resource is available between start_time and end_time.
2. Check if a staff member is available between start_time and end_time.
3. Reject overlapping bookings for the same resource.
4. Reject overlapping bookings for the same staff member.
5. Allow non overlapping bookings.
6. Allow overlapping bookings for different resources.
7. Use database queries that are scoped by business_id.

Acceptance tests:
1. Same resource overlapping is rejected.
2. Same resource non overlapping is allowed.
3. Different resource overlapping is allowed.
4. Same staff overlapping is rejected.
5. Same staff non overlapping is allowed.
```

---

## 24. Fourth Copilot task

```text
Implement booking creation and approval flow.

Create:
booking_service.py
approval_service.py

Requirements:
1. Customer can request a booking.
2. Booking service checks availability.
3. Approval service decides status based on service approval mode.
4. Auto approved booking becomes confirmed.
5. Manual approval booking becomes pending_approval.
6. Admin can approve pending booking.
7. Admin can reject pending booking.
8. Every status change creates an audit log.
9. Invalid status transitions fail.

Acceptance tests:
1. Auto approved service creates confirmed booking.
2. Manual approval service creates pending_approval booking.
3. Admin approval changes pending_approval to confirmed.
4. Admin rejection changes pending_approval to rejected.
5. Invalid transition fails.
6. Audit log is created for every status change.
```

---

## 25. Fifth Copilot task

```text
Implement promotions and vouchers.

Create models:
Promotion
PromotionRedemption

Create service:
promotion_service.py

Promotion types:
percentage_discount
fixed_discount
free_session

Code types:
public_campaign
single_use
customer_assigned
admin_awarded
loyalty_reward

Requirements:
1. Validate code.
2. Apply code to booking.
3. Enforce valid_from and valid_until.
4. Enforce max_uses_total.
5. Enforce max_uses_per_customer.
6. Enforce assigned_customer_id where present.
7. Enforce service restrictions.
8. Enforce revoked flag.
9. Create redemption record.
10. Use transaction for redemption.

Acceptance tests:
1. MAY10 applies 10 percent discount when valid.
2. Expired code is rejected.
3. Same customer cannot use MAY10 twice if max_uses_per_customer is 1.
4. Different customer can use MAY10 while total uses remain.
5. Single use code cannot be used twice.
6. Customer assigned code cannot be used by another customer.
7. Wrong service is rejected.
8. Revoked code is rejected.
9. Redemption record is created.
```

---

## 26. Sixth Copilot task

```text
Implement admin awarded benefits and customer balance.

Create models:
AdminAward
CustomerBalance
CustomerBalanceTransaction

Create service:
balance_service.py
admin_award_service.py

Admin can award:
1. Free session
2. Account balance
3. Fixed discount
4. Percentage discount

Requirements:
1. Awarding free session creates a customer assigned single use promotion.
2. Awarding account balance increases customer balance.
3. Awarding fixed discount creates customer assigned promotion.
4. Awarding percentage discount creates customer assigned promotion.
5. Spending balance reduces balance.
6. Balance cannot go negative.
7. Revoking award prevents use.
8. Every admin award creates audit log.

Acceptance tests:
1. Admin awards free session and customer redeems it once.
2. Admin awards £25 balance and balance increases.
3. Customer spends £10 and balance becomes £15.
4. Customer cannot spend more than available balance.
5. Revoked award cannot be used.
6. Audit log is created.
```

---

## 27. Seventh Copilot task

```text
Implement loyalty engine.

Create models:
LoyaltyAccount
LoyaltyTransaction

Create service:
loyalty_service.py

Requirements:
1. Create loyalty account per customer.
2. Track completed booking count.
3. Award reward after configured threshold.
4. Reward must be a single use promotion code.
5. Cancelled bookings do not count.
6. No show bookings do not count.
7. Rejected bookings do not count.
8. Pending bookings do not count.

Acceptance tests:
1. Five completed bookings generate reward.
2. Four completed bookings do not generate reward.
3. Cancelled booking does not count.
4. No show booking does not count.
5. Reward code can be redeemed once.
6. Reward code cannot be redeemed twice.
```

---

### Phase 15: Dashboards and reporting

Goal:

```text
Give business owners queryable summaries of bookings, earnings, staff activity and resource usage over configurable time periods.
```

Infrastructure notes:

```text
Start with server-rendered Jinja2 + HTMX pages showing pre-computed summaries.
Charts can be simple HTML progress bars or a lightweight JavaScript chart library (e.g. Chart.js via CDN) included without a build step.
Move to a dedicated reporting service or BI tool only if query complexity demands it.
```

Report types:

| Report | Dimensions |
|---|---|
| Bookings over time | Count by day, week, month |
| Revenue over time | Sum of amount_due by period |
| Booking status breakdown | Confirmed, cancelled, no-show counts per period |
| Staff utilisation | Bookings per staff member per period |
| Resource utilisation | Bookings per resource per period |
| Earnings by service | Revenue per service per period |
| Top customers | Booking count and spend per customer |

Filters:

| Filter | Options |
|---|---|
| Period | Today, this week, this month, last 30 days, custom range |
| Business | All or specific business |
| Location | All or specific location |
| Service | All or specific service |

Implementation plan:

| Layer | Approach |
|---|---|
| Queries | Service module functions using SQLAlchemy aggregations |
| API | Internal admin-only FastAPI routes returning summary data |
| UI | HTMX admin pages with date-range pickers and period tabs |
| Caching | Redis cache on expensive aggregations, invalidated on booking change |

Acceptance criteria:

| Test | Expected |
|---|---|
| Booking count query for period | Returns correct count |
| Revenue sum for period | Returns correct total |
| Staff utilisation query | Returns bookings per staff member |
| Resource utilisation query | Returns bookings per resource |
| Admin page loads summary | Works with HTMX |

---

### Phase 16: Authentication, SSO and bootstrap flow

Goal:

```text
Allow secure login for admin and staff users. Bootstrap the system with a default admin account that can then be linked to email/password or SSO.
```

Bootstrap flow:

```text
System starts with one default admin user (no password, no SSO)
Admin visits /setup to claim the account
Admin chooses email/password or SSO provider to link
Once linked, /setup is locked and cannot be accessed again
Admin can then invite staff
```

Authentication options:

| Method | Use |
|---|---|
| Email and password | Simple login with hashed password |
| Google OAuth | SSO via Google |
| Microsoft OAuth | SSO via Microsoft Entra |
| Magic link | Passwordless email link login |

Models:

```text
User
UserCredential (email + hashed password)
OAuthAccount (provider, provider_user_id, access token)
UserSession
```

Rules:

| Rule | Required |
|---|---:|
| Passwords hashed with bcrypt or argon2 | Yes |
| OAuth tokens never stored in plaintext | Yes |
| Sessions short-lived with refresh | Yes |
| Setup route locked after first admin claim | Yes |
| Staff linked to User account | Yes |
| Role-based access control | Yes |

Roles:

| Role | Access |
|---|---|
| platform_admin | Full access to all businesses |
| business_admin | Full access to own business |
| staff | Access to own schedule and booking actions |

Acceptance criteria:

| Test | Expected |
|---|---|
| /setup not accessible once admin linked | Locked |
| Email/password login | Works |
| OAuth login | Works |
| Staff login with invited account | Works |
| Wrong password | Rejected |
| Expired session | Redirected to login |

---

### Phase 17: Staff invitations

Goal:

```text
Allow business admin to create staff records and send email invitations to register with email/password or SSO.
```

Invitation flow:

```text
Admin creates staff record with name and email
System generates a unique invitation token
System sends invitation email with registration link
Staff member clicks link and registers with email/password or SSO
Invitation token is consumed and cannot be reused
Staff account is linked to their User record
```

Models:

```text
StaffInvitation
  staff_id
  token (unique, hashed)
  invited_by (user_id)
  expires_at
  accepted_at
  status (pending, accepted, expired, revoked)
```

Email content:

```text
Subject: You have been invited to join {business_name}
Body: Link to accept invitation and register
Expiry: 7 days
```

Acceptance criteria:

| Test | Expected |
|---|---|
| Admin invites staff | Invitation row created, email queued |
| Staff clicks valid link | Registration page shown |
| Staff registers | Account linked, invitation consumed |
| Same link used twice | Rejected |
| Expired link | Rejected |
| Admin revokes invitation | Link rejected |

---

### Phase 18: Appointment reminders and SMS

Goal:

```text
Send reminder emails and SMS to customers before their appointment. Allow businesses to configure reminder timing and channel.
```

Channels:

| Channel | Provider |
|---|---|
| Email | Postmark, SendGrid or Mailgun |
| SMS | Twilio |

Reminder triggers:

| Trigger | Default timing |
|---|---|
| 24 hours before appointment | Day before reminder |
| 2 hours before appointment | Same day reminder |
| On booking confirmation | Immediate confirmation |
| On booking cancellation | Immediate cancellation notice |

Business config example:

```yaml
notifications:
  email_reminders: true
  sms_reminders: true
  reminder_hours_before: [24, 2]
  sender_email: "bookings@abcgarage.co.uk"
  sender_name: "ABC Garage"
  sms_from: "+447700900000"
```

Implementation plan:

| Layer | Approach |
|---|---|
| Scheduling | RQ scheduled jobs via Redis |
| Email | Postmark or SendGrid HTTP API |
| SMS | Twilio REST API |
| Templates | Jinja2 templates stored per event type |
| Retry | RQ retry on failure with backoff |
| Audit | Notification record updated with sent status |

Notification model additions:

```text
Notification
  channel (email, sms)
  event_type (confirmation, reminder_24h, reminder_2h, cancellation)
  recipient_email
  recipient_phone
  sent_at
  status (pending, sent, failed)
  provider_message_id
```

Acceptance criteria:

| Test | Expected |
|---|---|
| Booking confirmed | Confirmation email queued |
| 24h before booking | Reminder email and SMS queued |
| 2h before booking | Reminder email and SMS queued |
| Booking cancelled | Cancellation notice queued |
| SMS disabled in config | No SMS sent |
| Notification record updated on send | Works |

---

## 28. Eighth Copilot task

```text
Implement accounting software integration.

Create models:
AccountingSettings
AccountingPushLog

Create adapter package:
app/accounting/base.py    (AccountingProvider abstract base)
app/accounting/xero.py    (XeroAdapter — OAuth 2.0 with PKCE)
app/accounting/sage.py    (SageAdapter — OAuth 2.0)
app/accounting/quickbooks.py (QuickBooksAdapter — OAuth 2.0)
app/accounting/jobs.py    (RQ job functions)

Create service:
accounting_service.py

Requirements:
1. AccountingSettings stores per-business provider config with encrypted credentials.
2. AccountingProvider abstract base defines push_invoice, push_credit_note,
   push_contact and verify_connection methods.
3. Each concrete adapter implements the full interface.
4. When a booking transitions to completed and a provider is active, enqueue a
   push_invoice RQ job.
5. When a booking is cancelled and its invoice was already pushed, enqueue a
   push_credit_note RQ job.
6. Invoice due date is today when payment_terms_days is 0.
   Invoice due date is today + payment_terms_days when positive.
7. Accounting integration must not require Stripe to be configured.
8. Stripe integration must not require accounting integration to be configured.
9. Failed jobs are retried with exponential back-off up to five attempts.
10. Every push attempt is recorded in AccountingPushLog.
11. A webhook receiver at POST /webhooks/accounting/{provider} accepts real-time
    events from accounting platforms. Signatures must be verified before processing.
12. A nightly RQ scheduled job compares pushed invoices with completed bookings
    and flags discrepancies in AccountingPushLog without overwriting either system.
13. Add SQLAdmin views for AccountingSettings and AccountingPushLog.
14. Add a Test Connection admin action that calls verify_connection.
15. Add a Retry admin action that re-queues a failed push job.

Acceptance tests:
1. Booking completed with Xero provider active enqueues push_invoice job.
2. Push invoice job creates AccountingPushLog with status success.
3. Transient failure retries with back-off.
4. Five consecutive failures set status to failed.
5. Manual retry re-enqueues job and resets attempt counter.
6. Booking cancelled after invoice pushed enqueues push_credit_note job.
7. payment_terms_days 0 produces due date of today.
8. payment_terms_days 30 produces due date of today + 30 days.
9. Stripe not configured does not block accounting push.
10. Accounting not configured does not block Stripe.
11. Webhook with invalid signature returns 400 and no action taken.
12. Nightly reconciliation flags missing push records.
```

---

## 29. Final instruction for Copilot

```text
Work incrementally.

After each task:
1. Show changed files.
2. Run tests.
3. Fix failing tests.
4. Update README if setup or usage changed.
5. Do not add features outside the current task.
6. Do not introduce React, Stripe, SMS or advanced frontend until requested.
7. Keep the service layer independent from SQLAdmin and HTMX.
```
