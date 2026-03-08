from sqlalchemy.orm import Session
from models.booking import Booking

class BookingRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, booking: Booking) -> Booking:
        self.session.add(booking)
        self.session.commit()
        self.session.refresh(booking)
        return booking
    
    def get_by_id(self, booking_id: int) -> Booking | None:
        return self.session.query(Booking).filter(Booking.id == booking_id).first()