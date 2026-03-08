import pytest
from models.booking import Booking
from models.slot import Slot, SlotStatus
# from sqlalchemy import Session
from repositories.slot_repository import SlotRepository
from repositories.booking_repository import BookingRepository
from datetime import datetime, timedelta
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

# Second test
def test_booking_status(session):
    start_time = datetime.now()
    end_time = start_time + timedelta(hours = 1)
    slot = Slot(start_time = start_time, end_time = end_time)

    # we need to save the slot in the database (for this we need repository)
    slot_repo = SlotRepository(session)
    saved_slot = slot_repo.create(slot)

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

# Third test
def test_booking_already_booked_raises_exceptions(session):
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=1)
    slot = Slot(start_time = start_time, end_time = end_time)

    slot_repo = SlotRepository(session)
    saved_slot = slot_repo.create(slot)

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
