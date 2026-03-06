from datetime import datetime, timedelta
from models.slot import Slot, SlotStatus

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