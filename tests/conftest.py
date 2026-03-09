from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
from models.slot import Base
from dotenv import load_dotenv
import os

load_dotenv()

@pytest.fixture
def session():
    # creating an in-memory db for testing
    engine = create_engine(f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@localhost:3306/slot_booking_test")
    Base.metadata.create_all(bind=engine) # for creating the tables
    # creating a sessionmaker instance
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # creating a session instance
    db_session = SessionLocal()

    yield db_session # give the session to the test

    db_session.close()
    Base.metadata.drop_all(bind=engine)
