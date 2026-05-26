from fastapi import FastAPI
from sqladmin import Admin

from app.admin.sqladmin.views import (
    AuditLogAdmin,
    BookingAdmin,
    BusinessAdmin,
    CustomerAdmin,
    LocationAdmin,
    LocationBreakAdmin,
    LocationWorkingHoursAdmin,
    ServiceAdmin,
    StaffAdmin,
)
from app.core.database import engine


def setup_sqladmin(app: FastAPI) -> None:
    admin = Admin(app, engine, base_url="/admin/sql", title="Booking Admin")
    admin.add_view(BusinessAdmin)
    admin.add_view(LocationAdmin)
    admin.add_view(LocationWorkingHoursAdmin)
    admin.add_view(LocationBreakAdmin)
    admin.add_view(StaffAdmin)
    admin.add_view(ServiceAdmin)
    admin.add_view(CustomerAdmin)
    admin.add_view(BookingAdmin)
    admin.add_view(AuditLogAdmin)
