from sqladmin import ModelView

from app.models.audit import AuditLog
from app.models.booking import Booking, BookingExtra, BookingResource, BookingStaff
from app.models.business import Business, Location
from app.models.customer import Customer
from app.models.resource import Resource
from app.models.service import Service
from app.models.service_extra import ServiceExtra
from app.models.staff import Staff, StaffRole


class BusinessAdmin(ModelView, model=Business):
    name = "Business"
    name_plural = "Businesses"
    details_template = "sqladmin/model_details.html"
    column_list = [Business.id, Business.name, Business.slug, Business.created_at]
    column_searchable_list = [Business.name, Business.slug]
    column_sortable_list = [Business.id, Business.name, Business.created_at]


class LocationAdmin(ModelView, model=Location):
    name = "Location"
    name_plural = "Locations"
    details_template = "sqladmin/model_details.html"
    column_list = [Location.id, Location.name, Location.business, Location.address]
    column_searchable_list = [Location.name]
    column_sortable_list = [Location.id, Location.name]


class ServiceAdmin(ModelView, model=Service):
    name = "Service"
    name_plural = "Services"
    details_template = "sqladmin/model_details.html"
    form_args = {"is_active": {"default": True}}
    column_list = [
        Service.id,
        Service.name,
        Service.business,
        Service.duration_minutes,
        Service.price_unit,
        Service.unit_price,
        Service.approval_mode,
        Service.is_active,
    ]
    column_searchable_list = [Service.name]
    column_sortable_list = [Service.id, Service.name, Service.unit_price]
    # Expose M2M associations in the form so staff/resources can be linked.
    form_include_pk = True


class StaffAdmin(ModelView, model=Staff):
    name = "Staff"
    name_plural = "Staff"
    details_template = "sqladmin/model_details.html"
    column_list = [Staff.id, Staff.name, Staff.business, Staff.email, Staff.is_active]
    column_searchable_list = [Staff.name, Staff.email]
    column_sortable_list = [Staff.id, Staff.name]


class StaffRoleAdmin(ModelView, model=StaffRole):
    name = "Staff Role"
    name_plural = "Staff Roles"
    details_template = "sqladmin/model_details.html"
    column_list = [StaffRole.id, StaffRole.staff_member, StaffRole.role, StaffRole.created_at]
    column_searchable_list = [StaffRole.role]


class ResourceAdmin(ModelView, model=Resource):
    name = "Resource"
    name_plural = "Resources"
    details_template = "sqladmin/model_details.html"
    column_list = [Resource.id, Resource.name, Resource.business, Resource.resource_type, Resource.count, Resource.is_active]
    column_searchable_list = [Resource.name]
    column_sortable_list = [Resource.id, Resource.name]


class CustomerAdmin(ModelView, model=Customer):
    name = "Customer"
    name_plural = "Customers"
    details_template = "sqladmin/model_details.html"
    column_list = [Customer.id, Customer.name, Customer.business, Customer.email, Customer.phone]
    column_searchable_list = [Customer.name, Customer.email]
    column_sortable_list = [Customer.id, Customer.name]


class BookingAdmin(ModelView, model=Booking):
    name = "Booking"
    name_plural = "Bookings"
    details_template = "sqladmin/model_details.html"
    create_template = "sqladmin/booking_create.html"
    edit_template = "sqladmin/booking_edit.html"
    column_list = [
        Booking.id,
        Booking.business,
        Booking.customer,
        Booking.service,
        Booking.status,
        Booking.starts_at,
        Booking.ends_at,
        Booking.amount_due,
    ]
    column_searchable_list = [Booking.status]
    column_sortable_list = [Booking.id, Booking.starts_at, Booking.status]

    async def on_model_change(self, data: dict, model: Booking, is_created: bool, request) -> None:
        """Prevent overlapping bookings from being created via the admin UI."""
        if not is_created:
            return

        starts_at = data.get("starts_at")
        ends_at = data.get("ends_at")
        business_id = data.get("business_id")

        if not (starts_at and ends_at and business_id):
            return

        from app.core.database import SessionLocal
        from app.services.availability_service import is_business_slot_available

        with SessionLocal() as session:
            if not is_business_slot_available(session, business_id, starts_at, ends_at):
                raise ValueError(
                    "No capacity available for this time slot — "
                    "all resources are at full capacity or a booking already exists."
                )


class BookingStaffAdmin(ModelView, model=BookingStaff):
    name = "Booking Staff"
    name_plural = "Booking Staff"
    details_template = "sqladmin/model_details.html"
    column_list = [BookingStaff.id, BookingStaff.booking, BookingStaff.staff_member]


class BookingResourceAdmin(ModelView, model=BookingResource):
    name = "Booking Resource"
    name_plural = "Booking Resources"
    details_template = "sqladmin/model_details.html"
    column_list = [BookingResource.id, BookingResource.booking, BookingResource.resource]


class ServiceExtraAdmin(ModelView, model=ServiceExtra):
    name = "Service Extra"
    name_plural = "Service Extras"
    details_template = "sqladmin/model_details.html"
    column_list = [
        ServiceExtra.id,
        ServiceExtra.service,
        ServiceExtra.name,
        ServiceExtra.default_selected,
        ServiceExtra.sort_order,
    ]
    column_searchable_list = [ServiceExtra.name]
    column_sortable_list = [ServiceExtra.id, ServiceExtra.sort_order]


class BookingExtraAdmin(ModelView, model=BookingExtra):
    name = "Booking Extra"
    name_plural = "Booking Extras"
    details_template = "sqladmin/model_details.html"
    column_list = [BookingExtra.id, BookingExtra.booking, BookingExtra.extra]


class AuditLogAdmin(ModelView, model=AuditLog):
    name = "Audit Log"
    name_plural = "Audit Logs"
    details_template = "sqladmin/model_details.html"
    can_create = False
    can_edit = False
    can_delete = False
    column_list = [
        AuditLog.id,
        AuditLog.entity_type,
        AuditLog.entity_id,
        AuditLog.action,
        AuditLog.created_at,
    ]
    column_searchable_list = [AuditLog.entity_type, AuditLog.action]
    column_sortable_list = [AuditLog.id, AuditLog.created_at]
