from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Slot(Base):
    __tablename__ = "slots"
    id = Column(Integer, primary_key = True, index = True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(SQLAlchemyEnum(SlotStatus), default = SlotStatus.AVAILABLE, nullable=False)


class SlotStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    HELD = "HELD"
    BOOKED = "BOOKED"

