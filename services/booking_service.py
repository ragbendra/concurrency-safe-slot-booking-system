from repositories.booking_repository import BookingRepository
from repositories.slot_repository import SlotRepository
from exceptions import SlotNotFoundException, SlotAlreadyBookedException
from models.slot import SlotStatus
from models.booking import Booking

class BookingService:
    def __init__(self, booking_repo: BookingRepository, slot_repo: SlotRepository):
        self.booking_repo = booking_repo
        self.slot_repo = slot_repo
    
    def book_slot(self, user_id: int, slot_id: int):
        # fetch the slot
        slot = self.slot_repo.get_by_id(slot_id)

        # check if it exists
        if not slot:
            raise SlotNotFoundException("Slot not found")

        # check if the slot is already booked
        if slot.status == SlotStatus.BOOKED:
            raise SlotAlreadyBookedException("Slot is already booked")
        
        # book the slot
        booking = Booking(user_id=user_id, slot_id=slot_id)
        saved_booking = self.booking_repo.create(booking)

        # update the slot status
        slot.status = SlotStatus.BOOKED

        self.slot_repo.session.commit()

        return saved_booking