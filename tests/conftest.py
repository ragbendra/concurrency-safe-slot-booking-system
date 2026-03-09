from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
from models.slot import Base
from sqlalchemy.pool import StaticPool

@pytest.fixture
def session():
    # creating an in-memory db for testing
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine) # for creating the tables
    # creating a sessionmaker instance
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # creating a session instance
    db_session = SessionLocal()

    yield db_session # give the session to the test

    db_session.close()
    Base.metadata.drop_all(bind=engine)
