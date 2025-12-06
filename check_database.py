# check_database.py
import sqlite3
import os

print("🔍 Проверяю базу данных...")

# Проверяем существует ли файл базы
if not os.path.exists('dating.db'):
    print("❌ Файл dating.db не найден!")
    print("Запустите бота сначала командой: python main.py")
    exit(1)

# Подключаемся к базе
try:
    conn = sqlite3.connect('dating.db')
    cursor = conn.cursor()
    
    # 1. Проверяем таблицы
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("📊 Таблицы в базе:")
    for table in tables:
        print(f"  ✅ {table[0]}")
    
    # 2. Проверяем таблицу users
    if ('users',) in tables:
        print("\n📋 Структура таблицы 'users':")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            print(f"  📍 {col_name} ({col_type})")
            
            # Проверяем есть ли photo_ids
            if col_name == 'photo_ids':
                print("     ✅ Колонка photo_ids есть!")
    
    # 3. Количество записей
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    print(f"\n👥 Всего пользователей: {count}")
    
    # 4. Показываем первых 3 пользователя
    if count > 0:
        print("\n👤 Первые пользователи:")
        cursor.execute("SELECT id, name, age FROM users LIMIT 3")
        users = cursor.fetchall()
        
        for user in users:
            print(f"  👤 ID: {user[0]}, Имя: {user[1]}, Возраст: {user[2]}")
    
    conn.close()
    print("\n✅ Проверка завершена успешно!")
    
except Exception as e:
    print(f"❌ Ошибка при проверке базы: {e}")