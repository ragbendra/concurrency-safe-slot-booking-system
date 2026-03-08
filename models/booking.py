from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from models.slot import Base


class Booking(Base):
    __tablename__ = "bookings"
    user_id = Column(Integer, nullable = False, index = True)
    id = Column(Integer, primary_key = True, index = True)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable = False)
    created_at = Column(DateTime, default = datetime.now(timezone.utc))
    # slot = relationship("Slot", back_populates = "bookings")
    