import pytest
from models.booking import Booking
from models.slot import Slot, SlotStatus
# from sqlalchemy import Session
from repositories.slot_repository import SlotRepository
from repositories.booking_repository import BookingRepository
from datetime import datetime, timedelta
from datetime import timezone
from exceptions import SlotAlreadyBookedException, SlotNotFoundException
from services.booking_service import BookingService

# First test
def test_booking_create():
    # arrange and act
    user_id = 1
    slot_id = 100
    booking = Booking(user_id = user_id, slot_id = slot_id)

    # assert
    assert booking.user_id == user_id
    assert booking.slot_id == slot_id


def test_booking_created_at_default_is_callable():
    assert Booking.__table__.c.created_at.default.is_callable

# Second test
def test_booking_status(session):
    start_time = datetime.now()
    end_time = start_time + timedelta(hours = 1)
    slot = Slot(start_time = start_time, end_time = end_time)

    # we need to save the slot in the database (for this we need repository)
    slot_repo = SlotRepository(session)
    saved_slot = slot_repo.create(slot)
    session.commit()

    # init the service (we assume it requires both repo to function)
    booking_repo = BookingRepository(session)
    booking_service = BookingService(booking_repo, slot_repo)

    user_id = 1

    # call the service to book the slot, we expect here a booking obj(returns)
    booking = booking_service.book_slot(user_id = user_id, slot_id = saved_slot.id)
    
    # checks if it actually works
    assert booking is not None
    assert booking.user_id == user_id
    assert booking.slot_id == saved_slot.id

    # we fetch it from db to make sure it works
    updated_slot = slot_repo.get_by_id(saved_slot.id)
    assert updated_slot.status == SlotStatus.BOOKED



def test_booking_created_at_is_current_utc(session):
    start_time = datetime.now()
    slot = Slot(start_time=start_time, end_time=start_time + timedelta(hours=1))
    slot_repo = SlotRepository(session)
    saved_slot = slot_repo.create(slot)
    session.commit()

    booking_service = BookingService(
        BookingRepository(session),
        slot_repo,
    )
    booking = booking_service.book_slot(user_id=2, slot_id=saved_slot.id)

    saved_created_at = session.query(Booking).filter_by(id=booking.id).one().created_at
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    assert abs(saved_created_at - now_utc) <= timedelta(seconds=60)

# Third test
def test_booking_already_booked_raises_exceptions(session):
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=1)
    slot = Slot(start_time = start_time, end_time = end_time)

    slot_repo = SlotRepository(session)
    saved_slot = slot_repo.create(slot)
    session.commit()

    saved_slot.status = SlotStatus.BOOKED
    session.commit()

    booking_repo = BookingRepository(session)
    booking_service = BookingService(booking_repo, slot_repo)

    user_id = 1

    with pytest.raises(SlotAlreadyBookedException):
        booking_service.book_slot(user_id = user_id, slot_id = saved_slot.id)

# Fourth test
def test_booking_nonexistent_slot_raises_exception(session):
    
    slot_repo = SlotRepository(session)

    booking_repo = BookingRepository(session)
    booking_service = BookingService(booking_repo, slot_repo)

    user_id = 1

    slot_id = 999

    with pytest.raises(SlotNotFoundException):
        booking_service.book_slot(user_id=user_id, slot_id=slot_id)
