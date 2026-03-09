from models.slot import Slot
from datetime import datetime, timedelta
from repositories.slot_repository import SlotRepository
import concurrent.futures
from repositories.booking_repository import BookingRepository
from services.booking_service import BookingService
from exceptions import SlotAlreadyBookedException
from sqlalchemy.orm import Session


def test_concurrency(session):
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=1)

    slot = Slot(start_time=start_time, end_time=end_time)

    slot_repo = SlotRepository(session)
    saved_slot = slot_repo.create(slot)
    session.commit()

    # booking_repo = BookingRepository(session)
    # booking_service = BookingService(booking_repo, slot_repo)

    success_count = 0
    failure_count = 0

    def try_booking():
        # creating new session for this specific thread
        # session.get_bind() gets the engine from the main test session
        with Session(session.get_bind()) as thread_session:
            # giving the thread its own repo and service
            thread_booking_repo = BookingRepository(thread_session)
            thread_slot_repo = SlotRepository(thread_session)
            thread_service = BookingService(thread_booking_repo, thread_slot_repo)

            try:
                thread_service.book_slot(user_id=1, slot_id=saved_slot.id) # used thread_service
                thread_session.commit() # added a commit
                return True
            except SlotAlreadyBookedException:
                thread_session.rollback()
                return False
            except Exception as e:
                print(f"Unexpected error: {e}")
                thread_session.rollback()
                return False
        

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(try_booking) for _ in range(10)]
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                success_count += 1
            else:
                failure_count += 1
        
    assert success_count == 1
    assert failure_count == 9