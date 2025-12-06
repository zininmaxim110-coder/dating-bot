import sqlite3

print("🔧 Обновляю базу данных v6...")

conn = sqlite3.connect('dating.db')
cursor = conn.cursor()

# Users
cursor.execute("PRAGMA table_info(users)")
user_cols = [col[1] for col in cursor.fetchall()]

new_cols = [
    ("language", "TEXT DEFAULT 'ru'"),
    ("country", "TEXT"),
    ("is_shadow_banned", "BOOLEAN DEFAULT 0"),
    ("shadow_ban_reason", "TEXT")
]

for col, ctype in new_cols:
    if col not in user_cols:
        print(f"➕ {col}")
        cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {ctype}")

# Likes
cursor.execute("PRAGMA table_info(likes)")
like_cols = [col[1] for col in cursor.fetchall()]
if 'is_mutual' not in like_cols:
    cursor.execute("ALTER TABLE likes ADD COLUMN is_mutual BOOLEAN DEFAULT 0")

# Новые таблицы
cursor.execute("""
    CREATE TABLE IF NOT EXISTS banned_keywords (
        id INTEGER PRIMARY KEY,
        keyword TEXT UNIQUE,
        created_at DATETIME
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS broadcast_templates (
        id INTEGER PRIMARY KEY,
        name TEXT,
        text_ru TEXT,
        text_uz TEXT,
        text_uk TEXT,
        text_kz TEXT,
        created_at DATETIME
    )
""")

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