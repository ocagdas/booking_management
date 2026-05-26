from sqladmin import ModelView
from wtforms import SelectField

from app.models.audit import AuditLog
from app.models.booking import Booking
from app.models.business import Business
from app.models.customer import Customer
from app.models.enums import ApprovalMode, DurationType, DurationUnit, GapUnit
from app.models.location import Location, LocationBreak, LocationWorkingHours
from app.models.service import Service
from app.models.staff import Staff


class BusinessAdmin(ModelView, model=Business):
    name = "Business"
    name_plural = "Businesses"
    column_list = [Business.id, Business.name, Business.slug, Business.created_at]
    form_columns = [Business.name, Business.slug]
    column_searchable_list = [Business.name, Business.slug]


class LocationAdmin(ModelView, model=Location):
    name = "Location"
    column_list = [Location.id, Location.business, Location.name, Location.is_default]
    form_columns = [Location.business, Location.name, Location.is_default]
    column_searchable_list = [Location.name]


class LocationWorkingHoursAdmin(ModelView, model=LocationWorkingHours):
    name = "Working Hours"
    column_list = [
        LocationWorkingHours.id,
        LocationWorkingHours.location,
        LocationWorkingHours.day_of_week,
        LocationWorkingHours.opens_at,
        LocationWorkingHours.closes_at,
        LocationWorkingHours.is_closed,
    ]
    form_columns = [
        LocationWorkingHours.location,
        LocationWorkingHours.day_of_week,
        LocationWorkingHours.opens_at,
        LocationWorkingHours.closes_at,
        LocationWorkingHours.is_closed,
    ]


class LocationBreakAdmin(ModelView, model=LocationBreak):
    name = "Location Break"
    column_list = [
        LocationBreak.id,
        LocationBreak.location,
        LocationBreak.day_of_week,
        LocationBreak.starts_at,
        LocationBreak.ends_at,
    ]
    form_columns = [
        LocationBreak.location,
        LocationBreak.day_of_week,
        LocationBreak.starts_at,
        LocationBreak.ends_at,
    ]


class StaffAdmin(ModelView, model=Staff):
    name = "Staff"
    column_list = [Staff.id, Staff.business, Staff.location, Staff.name, Staff.role, Staff.is_active]
    form_columns = [Staff.business, Staff.location, Staff.name, Staff.role, Staff.is_active]
    column_searchable_list = [Staff.name, Staff.role]


class ServiceAdmin(ModelView, model=Service):
    name = "Service"
    column_list = [
        Service.id,
        Service.business,
        Service.name,
        Service.duration_type,
        Service.price,
        Service.approval_mode,
        Service.is_active,
    ]
    form_columns = [
        Service.business,
        Service.name,
        Service.duration_type,
        Service.fixed_duration_value,
        Service.fixed_duration_unit,
        Service.variable_min_duration_value,
        Service.variable_min_duration_unit,
        Service.variable_max_duration_value,
        Service.variable_max_duration_unit,
        Service.variable_increment_value,
        Service.variable_increment_unit,
        Service.admin_duration_value,
        Service.admin_duration_unit,
        Service.hide_duration_from_customer,
        Service.hide_duration_completely,
        Service.gap_after_value,
        Service.gap_after_unit,
        Service.price,
        Service.approval_mode,
        Service.locations,
        Service.is_active,
    ]
    form_overrides = {
        "duration_type": SelectField,
        "fixed_duration_unit": SelectField,
        "variable_min_duration_unit": SelectField,
        "variable_max_duration_unit": SelectField,
        "variable_increment_unit": SelectField,
        "admin_duration_unit": SelectField,
        "gap_after_unit": SelectField,
        "approval_mode": SelectField,
    }
    form_args = {
        "duration_type": {"choices": [(item.value, item.value) for item in DurationType]},
        "fixed_duration_unit": {"choices": [(item.value, item.value) for item in DurationUnit]},
        "variable_min_duration_unit": {
            "choices": [(item.value, item.value) for item in DurationUnit],
        },
        "variable_max_duration_unit": {
            "choices": [(item.value, item.value) for item in DurationUnit],
        },
        "variable_increment_unit": {
            "choices": [(item.value, item.value) for item in DurationUnit],
        },
        "admin_duration_unit": {"choices": [(item.value, item.value) for item in DurationUnit]},
        "gap_after_unit": {"choices": [(item.value, item.value) for item in GapUnit]},
        "approval_mode": {"choices": [(item.value, item.value) for item in ApprovalMode]},
    }
    column_searchable_list = [Service.name]


class CustomerAdmin(ModelView, model=Customer):
    name = "Customer"
    column_list = [Customer.id, Customer.business, Customer.name, Customer.email, Customer.phone]
    form_columns = [Customer.business, Customer.name, Customer.email, Customer.phone]
    column_searchable_list = [Customer.name, Customer.email, Customer.phone]


class BookingAdmin(ModelView, model=Booking):
    name = "Booking"
    column_list = [
        Booking.id,
        Booking.business,
        Booking.location,
        Booking.service,
        Booking.staff,
        Booking.customer,
        Booking.starts_at,
        Booking.ends_at,
        Booking.blocked_until,
        Booking.status,
    ]
    form_columns = [
        Booking.business,
        Booking.location,
        Booking.service,
        Booking.staff,
        Booking.customer,
        Booking.selected_duration_value,
        Booking.selected_duration_unit,
        Booking.starts_at,
        Booking.gap_after_value,
        Booking.gap_after_unit,
        Booking.status,
        Booking.notes,
    ]


class AuditLogAdmin(ModelView, model=AuditLog):
    name = "Audit Log"
    can_create = False
    can_edit = False
    column_list = [
        AuditLog.id,
        AuditLog.business_id,
        AuditLog.entity_type,
        AuditLog.entity_id,
        AuditLog.action,
        AuditLog.created_at,
    ]
