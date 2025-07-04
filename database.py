from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from models import Base

DATABASE_URL = "sqlite:///app.db"


engine = create_engine(
    DATABASE_URL, echo=False
)  # echo=False для продакшен-окружения, чтобы уменьшить логи
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Инициализировать базу данных путём создания всех таблиц, определённых в метаданных."""
    Base.metadata.create_all(bind=engine)
    update_schema()


def update_schema():
    """Обновить схему базы данных, добавляя новые столбцы при необходимости."""
    try:
        with engine.connect() as conn:
            # Проверяем, существует ли столбец created_at в таблице orders
            result = conn.execute(text("PRAGMA table_info(orders)"))
            columns = [row[1] for row in result]
            if "created_at" not in columns:
                conn.execute(text("ALTER TABLE orders ADD COLUMN created_at TEXT"))
                print("Added created_at column to orders table.")
    except SQLAlchemyError as e:
        print(f"Error updating schema: {e}")


if __name__ == "__main__":
    init_db()
