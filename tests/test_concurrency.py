from models.slot import Slot
from datetime import datetime, timedelta
from repositories.slot_repository import SlotRepository
from repositories.booking_repository import BookingRepository
from services.booking_service import BookingService
from exceptions import SlotAlreadyBookedException
import concurrent.futures


def test_concurrency(session, session_factory):
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=1)

    slot = Slot(start_time=start_time, end_time=end_time)

    slot_repo = SlotRepository(session)
    saved_slot = slot_repo.create(slot)
    session.commit()

    success_count = 0
    failure_count = 0

    def try_booking():
        thread_session = session_factory()
        try:
            thread_booking_repo = BookingRepository(thread_session)
            thread_slot_repo = SlotRepository(thread_session)
            thread_service = BookingService(thread_booking_repo, thread_slot_repo)

            try:
                thread_service.book_slot(user_id=1, slot_id=saved_slot.id)
                return True
            except SlotAlreadyBookedException:
                thread_session.rollback()
                return False
            except Exception as e:
                print(f"Unexpected error: {e}")
                thread_session.rollback()
                return False
        finally:
            thread_session.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(try_booking) for _ in range(10)]
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                success_count += 1
            else:
                failure_count += 1
        
    assert success_count == 1
    assert failure_count == 9


def test_concurrency_stress(session, session_factory):
    
    for i in range(50):
        success_count = 0
        failure_count = 0
        slot = Slot(start_time=datetime.now() + timedelta(days=i), end_time=datetime.now() + timedelta(days=i, hours=1))
        slot_repo = SlotRepository(session)
        saved_slot = slot_repo.create(slot)
        session.commit()

        # Capture slot_id via default arg to avoid Python closure-in-loop bug
        def try_booking(slot_id=saved_slot.id):
            thread_session = session_factory()
            try:
                thread_booking_repo = BookingRepository(thread_session)
                thread_slot_repo = SlotRepository(thread_session)
                thread_service = BookingService(thread_booking_repo, thread_slot_repo)

                try:
                    thread_service.book_slot(user_id=1, slot_id=slot_id)
                    return True
                except SlotAlreadyBookedException:
                    thread_session.rollback()
                    return False
                except Exception as e:
                    print(f"Unexpected error in iteration {i}: {e}")
                    thread_session.rollback()
                    return False
            finally:
                thread_session.close()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(try_booking) for _ in range(10)]
            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    success_count += 1
                else:
                    failure_count += 1
        
        assert success_count == 1, f"Iteration {i}: expected 1 success, got {success_count}"
        assert failure_count == 9, f"Iteration {i}: expected 9 failures, got {failure_count}"
        print(f"Iteration {i+1}/50 passed")