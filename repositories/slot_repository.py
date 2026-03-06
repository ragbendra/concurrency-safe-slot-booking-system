from sqlalchemy.orm import Session
from models.slot import Slot, SlotStatus

class SlotRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, slot: Slot) -> Slot:
        self.session.add(slot) # adding the slot to the db_session
        self.session.commit() # commiting the transactions so it's saved
        self.session.refresh(slot) # refresh the slot model so it gets new id from db
        return slot
    
    def get_by_id(self, slot_id: int) -> Slot | None:
        return self.session.query(Slot).filter(Slot.id == slot_id).first()
        # query the slot model to find the one matching the given id, and .first() returns the obj or none if doesn't exist
