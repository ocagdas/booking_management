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
    admin.add_view(BusinessAdmin)
    admin.add_view(LocationAdmin)
    admin.add_view(ServiceAdmin)
    admin.add_view(ServiceExtraAdmin)
    admin.add_view(RoleAdmin)
    admin.add_view(StaffAdmin)
    admin.add_view(ResourceAdmin)
    admin.add_view(CustomerAdmin)
    admin.add_view(BookingAdmin)
    admin.add_view(BookingStaffAdmin)
    admin.add_view(BookingResourceAdmin)
    admin.add_view(BookingExtraAdmin)
    admin.add_view(AuditLogAdmin)
