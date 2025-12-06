import sqlite3

print("🔧 Обновляю базу данных v5...")

conn = sqlite3.connect('dating.db')
cursor = conn.cursor()

# Проверяем колонки users
cursor.execute("PRAGMA table_info(users)")
user_columns = [col[1] for col in cursor.fetchall()]

new_user_columns = [
    ("is_shadow_banned", "BOOLEAN DEFAULT 0"),
    ("shadow_ban_reason", "TEXT")
]

for col_name, col_type in new_user_columns:
    if col_name not in user_columns:
        print(f"➕ Добавляю {col_name}...")
        cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")

# Проверяем колонки likes
cursor.execute("PRAGMA table_info(likes)")
like_columns = [col[1] for col in cursor.fetchall()]

if 'is_mutual' not in like_columns:
    print("➕ Добавляю is_mutual в likes...")
    cursor.execute("ALTER TABLE likes ADD COLUMN is_mutual BOOLEAN DEFAULT 0")

# Создаём таблицу ключевых слов
cursor.execute("""
    CREATE TABLE IF NOT EXISTS banned_keywords (
        id INTEGER PRIMARY KEY,
        keyword TEXT UNIQUE,
        created_at DATETIME
    )
""")

conn.commit()
conn.close()
print("🎉 Готово!")