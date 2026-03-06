from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# creating an in-memory db for testing
engine = create_engine("sqlite:///:memory:")
# creating a sessionmaker instance
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# creating a session instance
session = SessionLocal()

