import sqlite3

print("⚠️ УДАЛЕНИЕ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ")
print("=" * 50)

conn = sqlite3.connect('dating.db')
cursor = conn.cursor()

# Считаем пользователей (если таблицы users вообще нет — тоже обработаем)
try:
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
except sqlite3.OperationalError:
    print("❌ Таблица 'users' не найдена. База данных повреждена или ещё не создана.")
    conn.close()
    exit()

print(f"👥 Найдено пользователей: {count}")

if count > 0:
    confirm = input(f"\n❓ УДАЛИТЬ ВСЕХ {count} ПОЛЬЗОВАТЕЛЕЙ? (введите точно 'УДАЛИТЬ'): ")
    
    if confirm == 'УДАЛИТЬ':
        # Удаляем только существующие таблицы
        tables_to_clear = ['likes', 'matches', 'users']
        
        for table in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM {table}")
                print(f"✔ Очищена таблица {table}")
            except sqlite3.OperationalError:
                print(f"⚠ Таблица {table} не существует — пропущена")
        
        # Можно дополнительно сбросить автоинкремент (если используете INTEGER PRIMARY KEY)
        for table in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
            except sqlite3.OperationalError:
                pass  # sqlite_sequence может отсутствовать

        conn.commit()
        print(f"\n✅ Успешно удалено {count} пользователей и связанные данные")
    else:
        print("❌ Отменено пользователем")
else:
    print("📭 В таблице users уже пусто")

conn.close()