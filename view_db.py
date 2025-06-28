import sqlite3

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Получаем список всех таблиц
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]
print("Таблицы в базе данных:", tables)

for table in tables:
    print(f"\nСодержимое таблицы {table}:")
    try:
        cursor.execute(f"SELECT * FROM {table};")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        if not rows:
            print("(Пусто)")
    except Exception as e:
        print(f"Ошибка при чтении таблицы {table}: {e}")

conn.close() 