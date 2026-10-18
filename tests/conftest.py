from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import pytest
from models.slot import Base
import models.booking  # noqa: F401 - register the Booking table with Base.metadata
from dotenv import load_dotenv
import os

load_dotenv()

@pytest.fixture
def session():
    database = os.getenv("MYSQL_DATABASE", "")
    if "test" not in database.lower():
        pytest.exit(
            "Refusing to run: MYSQL_DATABASE must contain 'test' because the test fixture drops all tables."
        )

    # Use NullPool so every session gets its own fresh MySQL connection (critical for threading)
    db_url = f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{database}"
    engine = create_engine(db_url, poolclass=NullPool)
    Base.metadata.create_all(bind=engine) # for creating the tables
    # creating a sessionmaker instance (shared across main session and thread sessions)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # creating a session instance
    db_session = SessionLocal()

    yield db_session # give the session to the test

    db_session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def session_factory(session):
    # Returns the sessionmaker so threads can create their own independent sessions
    return sessionmaker(autocommit=False, autoflush=False, bind=session.get_bind())
