from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from models import Base

DATABASE_URL = "sqlite:///app.db"


engine = create_engine(DATABASE_URL, echo=True)  # echo=True для отладки
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
