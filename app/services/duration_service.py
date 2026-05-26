from datetime import timedelta

from fastapi import HTTPException, status

from app.models.enums import DurationType, DurationUnit, GapUnit
from app.models.service import Service


def duration_to_minutes(value: int | None, unit: str | None) -> int:
    if value is None or value < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Duration value must be zero or greater",
        )

    if unit == DurationUnit.minutes.value:
        return value
    if unit == DurationUnit.hours.value:
        return value * 60
    if unit == DurationUnit.days.value:
        return value * 24 * 60

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=f"Unsupported duration unit: {unit}",
    )


def gap_to_minutes(value: int | None, unit: str | None) -> int:
    if value is None or value < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Gap value must be zero or greater",
        )

    if unit == GapUnit.minutes.value:
        return value
    if unit == GapUnit.hours.value:
        return value * 60

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=f"Unsupported gap unit: {unit}",
    )


def resolve_service_duration(
    service: Service,
    selected_duration_value: int | None = None,
    selected_duration_unit: str | None = None,
) -> tuple[int, int, str]:
    """Return resolved duration in minutes plus stored value/unit."""
    if service.duration_type == DurationType.fixed.value:
        minutes = duration_to_minutes(service.fixed_duration_value, service.fixed_duration_unit)
        return minutes, service.fixed_duration_value or minutes, service.fixed_duration_unit or "minutes"

    if service.duration_type == DurationType.variable_customer_selected.value:
        if selected_duration_value is None or selected_duration_unit is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Selected duration is required for variable duration services",
            )

        selected_minutes = duration_to_minutes(selected_duration_value, selected_duration_unit)
        min_minutes = duration_to_minutes(
            service.variable_min_duration_value,
            service.variable_min_duration_unit,
        )
        max_minutes = duration_to_minutes(
            service.variable_max_duration_value,
            service.variable_max_duration_unit,
        )
        increment_minutes = duration_to_minutes(
            service.variable_increment_value,
            service.variable_increment_unit,
        )

        if selected_minutes < min_minutes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Selected duration is below the service minimum",
            )
        if selected_minutes > max_minutes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Selected duration is above the service maximum",
            )
        if increment_minutes <= 0 or (selected_minutes - min_minutes) % increment_minutes != 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Selected duration does not match the service increment",
            )

        return selected_minutes, selected_duration_value, selected_duration_unit

    if service.duration_type == DurationType.admin_defined.value:
        value = selected_duration_value or service.admin_duration_value
        unit = selected_duration_unit or service.admin_duration_unit
        minutes = duration_to_minutes(value, unit)
        return minutes, value or minutes, unit or "minutes"

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=f"Unsupported duration type: {service.duration_type}",
    )


def resolve_gap(
    service: Service,
    gap_after_value: int | None = None,
    gap_after_unit: str | None = None,
) -> tuple[int, int, str]:
    value = service.gap_after_value if gap_after_value is None else gap_after_value
    unit = service.gap_after_unit if gap_after_unit is None else gap_after_unit
    return gap_to_minutes(value, unit), value, unit


def add_minutes(minutes: int) -> timedelta:
    return timedelta(minutes=minutes)
