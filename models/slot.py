from enum import Enum
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import declarative_base
from sqlalchemy import UniqueConstraint

Base = declarative_base()

class SlotStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    HELD = "HELD"
    BOOKED = "BOOKED"

class Slot(Base):
    __tablename__ = "slots"
    __table_args__ = (UniqueConstraint('start_time', 'end_time', name='_start_end_uc'),)
    id = Column(Integer, primary_key = True, index = True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(SQLAlchemyEnum(SlotStatus), default = SlotStatus.AVAILABLE, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, 'status') and self.status is None:
            self.status = SlotStatus.AVAILABLE