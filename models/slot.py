from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class SlotStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    HELD = "HELD"
    BOOKED = "BOOKED"

class Slot(Base):
    __tablename__ = "slots"
    id = Column(Integer, primary_key = True, index = True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(SQLAlchemyEnum(SlotStatus), default = SlotStatus.AVAILABLE, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, 'status') and self.status is None:
            self.status = SlotStatus.AVAILABLE