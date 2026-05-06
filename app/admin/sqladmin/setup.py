from fastapi import FastAPI
from sqladmin import Admin

from app.core.database import engine
from app.admin.sqladmin.views import (
    AuditLogAdmin,
    BookingAdmin,
    BookingResourceAdmin,
    BookingStaffAdmin,
    BusinessAdmin,
    CustomerAdmin,
    LocationAdmin,
    ResourceAdmin,
    ServiceAdmin,
    StaffAdmin,
    StaffRoleAdmin,
)


def setup_sqladmin(app: FastAPI) -> None:
    admin = Admin(app, engine, base_url="/admin/sql")
    admin.add_view(BusinessAdmin)
    admin.add_view(LocationAdmin)
    admin.add_view(ServiceAdmin)
    admin.add_view(StaffAdmin)
    admin.add_view(StaffRoleAdmin)
    admin.add_view(ResourceAdmin)
    admin.add_view(CustomerAdmin)
    admin.add_view(BookingAdmin)
    admin.add_view(BookingStaffAdmin)
    admin.add_view(BookingResourceAdmin)
    admin.add_view(AuditLogAdmin)
