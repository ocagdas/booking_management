from fastapi import FastAPI
from sqladmin import Admin

from app.core.database import engine
from app.admin.sqladmin.views import (
    AuditLogAdmin,
    BookingAdmin,
    BookingExtraAdmin,
    BookingResourceAdmin,
    BookingStaffAdmin,
    BusinessAdmin,
    CustomerAdmin,
    LocationAdmin,
    ResourceAdmin,
    RoleAdmin,
    ServiceAdmin,
    ServiceExtraAdmin,
    StaffAdmin,
)


def setup_sqladmin(app: FastAPI) -> None:
    admin = Admin(app, engine, base_url="/admin/sql", templates_dir="app/templates")
    # Standalone entities
    admin.add_view(BusinessAdmin)
    admin.add_view(LocationAdmin)
    admin.add_view(CustomerAdmin)
    admin.add_view(ResourceAdmin)
    # --- Service Management ---
    admin.add_view(ServiceAdmin)
    admin.add_view(ServiceExtraAdmin)
    # --- Staff Management ---
    admin.add_view(RoleAdmin)
    admin.add_view(StaffAdmin)
    # --- Booking Management ---
    admin.add_view(BookingAdmin)
    admin.add_view(BookingStaffAdmin)
    admin.add_view(BookingResourceAdmin)
    admin.add_view(BookingExtraAdmin)
    # Audit
    admin.add_view(AuditLogAdmin)
