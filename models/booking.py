from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from models.slot import Base


class Booking(Base):
    __tablename__ = "bookings"
    user_id = Column(Integer, nullable = False, index = True)
    id = Column(Integer, primary_key = True, index = True)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable = False)
    # Store naive UTC because this column is a naive DateTime.
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    # slot = relationship("Slot", back_populates = "bookings")
