from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aegis.config import settings
from aegis.storage.orm import Base

engine = create_engine(settings.db_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
