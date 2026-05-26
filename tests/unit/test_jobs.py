from app.jobs import booking_created_placeholder


def test_booking_created_placeholder_job_returns_booking_id():
    assert booking_created_placeholder(123) == {"status": "queued", "booking_id": 123}
