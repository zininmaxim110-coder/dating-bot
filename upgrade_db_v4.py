import sqlite3

print("🔧 Обновляю базу данных v4...")

conn = sqlite3.connect('dating.db')
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(users)")
columns = [col[1] for col in cursor.fetchall()]

new_columns = [
    ("city", "TEXT"),
    ("city_normalized", "TEXT"),
    ("latitude", "REAL"),
    ("longitude", "REAL"),
    ("is_bot_profile", "BOOLEAN DEFAULT 0")
]

for col_name, col_type in new_columns:
    if col_name not in columns:
        print(f"➕ Добавляю {col_name}...")
        cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")

# Создаём таблицу просмотренных
cursor.execute("""
    CREATE TABLE IF NOT EXISTS viewed_profiles (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        viewed_user_id INTEGER,
        created_at DATETIME
    )
""")

conn.commit()
conn.close()
print("🎉 Готово!")