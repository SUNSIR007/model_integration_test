from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from apps.config import settings

engine = create_engine(settings.db_url, pool_size=20)

LocalSession = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

Base = declarative_base()


# database session generator
def get_db_session():
    db_session = LocalSession()
    try:
        yield db_session
    finally:
        db_session.close()
