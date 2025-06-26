from database import engine, init_db
from models import Base

if __name__ == "__main__":
    # Создает все таблицы из моделей
    Base.metadata.create_all(bind=engine)
    print("Таблицы успешно созданы!")
