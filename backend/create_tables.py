from app.db.base import Base
from app.db.database import engine
from app.models import Memory


Base.metadata.create_all(bind=engine)

print("Tables created successfully.")