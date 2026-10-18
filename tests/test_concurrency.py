from models.slot import Slot, SlotStatus
from models.booking import Booking
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

    slot_id = saved_slot.id

    def try_booking(slot_id):
        thread_session = None
        try:
            thread_session = session_factory()
            thread_booking_repo = BookingRepository(thread_session)
            thread_slot_repo = SlotRepository(thread_session)
            thread_service = BookingService(thread_booking_repo, thread_slot_repo)

            thread_service.book_slot(user_id=1, slot_id=slot_id)
            return "booked", ""
        except SlotAlreadyBookedException:
            if thread_session is not None:
                thread_session.rollback()
            return "already_booked", ""
        except Exception as e:
            if thread_session is not None:
                thread_session.rollback()
            return "error", f"{type(e).__name__}: {e}"
        finally:
            if thread_session is not None:
                thread_session.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(try_booking, slot_id) for _ in range(10)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
    categories = [category for category, _ in results]
    errors = [message for category, message in results if category == "error"]
    assert categories.count("booked") == 1
    assert categories.count("already_booked") == 9
    assert categories.count("error") == 0, f"Unexpected worker errors: {errors}"

    verification_session = session_factory()
    try:
        assert verification_session.query(Booking).filter(Booking.slot_id == slot_id).count() == 1
        verified_slot = verification_session.query(Slot).filter(Slot.id == slot_id).one()
        assert verified_slot.status == SlotStatus.BOOKED
    finally:
        verification_session.close()


def test_concurrency_stress(session, session_factory):
    
    for i in range(50):
        slot = Slot(start_time=datetime.now() + timedelta(days=i), end_time=datetime.now() + timedelta(days=i, hours=1))
        slot_repo = SlotRepository(session)
        saved_slot = slot_repo.create(slot)
        session.commit()
        slot_id = saved_slot.id

        def try_booking(slot_id):
            thread_session = None
            try:
                thread_session = session_factory()
                thread_booking_repo = BookingRepository(thread_session)
                thread_slot_repo = SlotRepository(thread_session)
                thread_service = BookingService(thread_booking_repo, thread_slot_repo)

                thread_service.book_slot(user_id=1, slot_id=slot_id)
                return "booked", ""
            except SlotAlreadyBookedException:
                if thread_session is not None:
                    thread_session.rollback()
                return "already_booked", ""
            except Exception as e:
                if thread_session is not None:
                    thread_session.rollback()
                return "error", f"{type(e).__name__}: {e}"
            finally:
                if thread_session is not None:
                    thread_session.close()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(try_booking, slot_id) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        categories = [category for category, _ in results]
        errors = [message for category, message in results if category == "error"]
        assert categories.count("booked") == 1, f"Iteration {i}: expected 1 booked result"
        assert categories.count("already_booked") == 9, f"Iteration {i}: expected 9 already_booked results"
        assert categories.count("error") == 0, f"Iteration {i}: unexpected worker errors: {errors}"

        verification_session = session_factory()
        try:
            assert verification_session.query(Booking).filter(Booking.slot_id == slot_id).count() == 1, (
                f"Iteration {i}: expected one booking row"
            )
            verified_slot = verification_session.query(Slot).filter(Slot.id == slot_id).one()
            assert verified_slot.status == SlotStatus.BOOKED, f"Iteration {i}: slot was not booked"
        finally:
            verification_session.close()
