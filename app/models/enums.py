from enum import StrEnum


class ApprovalMode(StrEnum):
    auto = "auto"
    manual = "manual"


class BookingStatus(StrEnum):
    pending_approval = "pending_approval"
    confirmed = "confirmed"
    rejected = "rejected"
    cancelled = "cancelled"
    completed = "completed"
    no_show = "no_show"


class DurationType(StrEnum):
    fixed = "fixed"
    variable_customer_selected = "variable_customer_selected"
    admin_defined = "admin_defined"


class DurationUnit(StrEnum):
    minutes = "minutes"
    hours = "hours"
    days = "days"


class GapUnit(StrEnum):
    minutes = "minutes"
    hours = "hours"
