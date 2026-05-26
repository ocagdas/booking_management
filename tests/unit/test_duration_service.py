from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.enums import DurationType, DurationUnit, GapUnit
from app.models.service import Service
from app.services.duration_service import resolve_gap, resolve_service_duration


def test_fixed_duration_resolves_to_minutes():
    service = Service(
        business_id=1,
        name="Haircut",
        duration_type=DurationType.fixed.value,
        fixed_duration_value=2,
        fixed_duration_unit=DurationUnit.hours.value,
        gap_after_value=0,
        gap_after_unit=GapUnit.minutes.value,
        price=Decimal("10.00"),
    )

    minutes, value, unit = resolve_service_duration(service)

    assert minutes == 120
    assert value == 2
    assert unit == "hours"


def test_variable_duration_rejects_below_minimum():
    service = Service(
        business_id=1,
        name="Colour",
        duration_type=DurationType.variable_customer_selected.value,
        variable_min_duration_value=1,
        variable_min_duration_unit=DurationUnit.hours.value,
        variable_max_duration_value=3,
        variable_max_duration_unit=DurationUnit.hours.value,
        variable_increment_value=30,
        variable_increment_unit=DurationUnit.minutes.value,
        gap_after_value=0,
        gap_after_unit=GapUnit.minutes.value,
        price=Decimal("10.00"),
    )

    with pytest.raises(HTTPException):
        resolve_service_duration(service, selected_duration_value=30, selected_duration_unit="minutes")


def test_variable_duration_rejects_outside_increment():
    service = Service(
        business_id=1,
        name="Colour",
        duration_type=DurationType.variable_customer_selected.value,
        variable_min_duration_value=60,
        variable_min_duration_unit=DurationUnit.minutes.value,
        variable_max_duration_value=180,
        variable_max_duration_unit=DurationUnit.minutes.value,
        variable_increment_value=30,
        variable_increment_unit=DurationUnit.minutes.value,
        gap_after_value=0,
        gap_after_unit=GapUnit.minutes.value,
        price=Decimal("10.00"),
    )

    with pytest.raises(HTTPException):
        resolve_service_duration(service, selected_duration_value=75, selected_duration_unit="minutes")


def test_admin_defined_duration_uses_selected_duration():
    service = Service(
        business_id=1,
        name="Consultation",
        duration_type=DurationType.admin_defined.value,
        gap_after_value=0,
        gap_after_unit=GapUnit.minutes.value,
        price=Decimal("10.00"),
    )

    minutes, value, unit = resolve_service_duration(
        service,
        selected_duration_value=1,
        selected_duration_unit="hours",
    )

    assert minutes == 60
    assert value == 1
    assert unit == "hours"


def test_resolve_gap_supports_hours():
    service = Service(
        business_id=1,
        name="Reset",
        duration_type=DurationType.fixed.value,
        fixed_duration_value=30,
        fixed_duration_unit=DurationUnit.minutes.value,
        gap_after_value=1,
        gap_after_unit=GapUnit.hours.value,
        price=Decimal("10.00"),
    )

    minutes, value, unit = resolve_gap(service)

    assert minutes == 60
    assert value == 1
    assert unit == "hours"
