from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import DATABASE_URL


engine = create_engine(DATABASE_URL)


def get_db():
    db = Session(engine)

    try:
        yield db
    finally:
        db.close()