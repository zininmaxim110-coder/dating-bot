# upgrade_db_v2.py - добавляем новые таблицы для лайков (ИСПРАВЛЕННАЯ ВЕРСИЯ)
import sqlite3
import json
from datetime import datetime

print("🔧 Обновляю базу данных для лайков...")

# Подключаемся к базе
conn = sqlite3.connect('dating.db')
cursor = conn.cursor()

# 1. Проверяем существующие таблицы
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [table[0] for table in cursor.fetchall()]
print(f"Существующие таблицы: {tables}")

# 2. Создаем таблицу likes если её нет
if 'likes' not in tables:
    print("➕ Создаю таблицу likes...")
    cursor.execute("""
        CREATE TABLE likes (
            id INTEGER PRIMARY KEY,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,
            message TEXT,
            is_read BOOLEAN DEFAULT 0,
            created_at DATETIME
        )
    """)
    print("✅ Таблица likes создана")
else:
    print("✅ Таблица likes уже существует")

# 3. Создаем таблицу matches если её нет
if 'matches' not in tables:
    print("➕ Создаю таблицу matches...")
    cursor.execute("""
        CREATE TABLE matches (
            id INTEGER PRIMARY KEY,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            created_at DATETIME,
            is_active BOOLEAN DEFAULT 1
        )
    """)
    print("✅ Таблица matches создана")
else:
    print("✅ Таблица matches уже существует")

# 4. Добавляем колонку target_gender к users если её нет
cursor.execute("PRAGMA table_info(users)")
columns = [column[1] for column in cursor.fetchall()]

if 'target_gender' not in columns:
    print("➕ Добавляю колонку target_gender...")
    cursor.execute("ALTER TABLE users ADD COLUMN target_gender TEXT DEFAULT 'всех'")
    print("✅ Колонка target_gender добавлена")
else:
    print("✅ Колонка target_gender уже существует")

# 5. Добавляем колонку last_active если её нет (БЕЗ DEFAULT!)
if 'last_active' not in columns:
    print("➕ Добавляю колонку last_active...")
    cursor.execute("ALTER TABLE users ADD COLUMN last_active DATETIME")
    
    # Обновляем существующие записи текущей датой
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(f"UPDATE users SET last_active = '{current_time}' WHERE last_active IS NULL")
    print("✅ Колонка last_active добавлена")
else:
    print("✅ Колонка last_active уже существует")

# 6. Добавляем колонку is_active если её нет
if 'is_active' not in columns:
    print("➕ Добавляю колонку is_active...")
    cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
    print("✅ Колонка is_active добавлена")
else:
    print("✅ Колонка is_active уже существует")

conn.commit()
conn.close()

print("\n🎉 База данных полностью обновлена!")
print("Теперь можно запускать бота с уведомлениями о лайках!")