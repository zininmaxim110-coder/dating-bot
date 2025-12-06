# create_db.py - принудительно создает базу
import database
print("✅ База должна быть создана при импорте database")

# Проверяем
import sqlite3
conn = sqlite3.connect('dating.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(users)")
cols = [col[1] for col in cursor.fetchall()]
print(f"Колонки: {cols}")
conn.close()