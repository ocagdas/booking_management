def booking_created_placeholder(booking_id: int) -> dict[str, int | str]:
    return {"status": "queued", "booking_id": booking_id}
