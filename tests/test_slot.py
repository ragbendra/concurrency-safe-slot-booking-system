from datetime import datetime, timedelta
from models.slot import Slot, SlotStatus
from repositories.slot_repository import SlotRepository
from sqlalchemy.exc import IntegrityError
import pytest

def test_slot_create():
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=1)
    slot = Slot(start_time=start_time, end_time=end_time)
    assert slot.start_time == start_time
    assert slot.end_time == end_time

def test_slot_default_status():
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=1)
    slot = Slot(start_time=start_time, end_time=end_time)
    assert slot.status == SlotStatus.AVAILABLE

def test_slot_persistence(session):
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=1)

    # creating slots
    slot = Slot(start_time=start_time, end_time=end_time)

    # use a repo to save it
    repo = SlotRepository(session)
    saved_slot = repo.create(slot)

    # assert that the slot was saved
    assert saved_slot.id is not None

    # fetching it back
    fetched_slot = repo.get_by_id(saved_slot.id)
    assert fetched_slot is not None
    assert fetched_slot.start_time == start_time
    assert fetched_slot.end_time == end_time
    assert fetched_slot.status == SlotStatus.AVAILABLE


def test_prevent_dup_slots(session):
    start_time = datetime.now()
    end_time = start_time + timedelta(hours = 1)

    # create and save the first slot
    slot1 = Slot(start_time=start_time, end_time=end_time)
    repo = SlotRepository(session)
    repo.create(slot1)

    # try to create and save the second slot with exact times
    slot2 = Slot(start_time=start_time, end_time=end_time)

    # assert that doing so throws an IntegrityError
    with pytest.raises(IntegrityError):
        repo.create(slot2)
    