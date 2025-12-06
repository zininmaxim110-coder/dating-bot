# upgrade_db_v3.py - добавляем поле is_bot_profile
import sqlite3

print("🔧 Обновляю базу данных...")

conn = sqlite3.connect('dating.db')
cursor = conn.cursor()

# Проверяем колонки
cursor.execute("PRAGMA table_info(users)")
columns = [col[1] for col in cursor.fetchall()]

if 'is_bot_profile' not in columns:
    print("➕ Добавляю колонку is_bot_profile...")
    cursor.execute("ALTER TABLE users ADD COLUMN is_bot_profile BOOLEAN DEFAULT 0")
    print("✅ Колонка добавлена")
else:
    print("✅ Колонка is_bot_profile уже есть")

conn.commit()
conn.close()
print("🎉 Готово!")