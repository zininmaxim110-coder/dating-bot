import sqlite3
import os

def clear_all_users():
    """Удалить всех пользователей из базы"""
    print("🗑️ Очистка базы данных от всех анкет")
    print("=" * 50)
    
    if not os.path.exists('dating.db'):
        print("❌ Файл базы данных не найден!")
        return
    
    conn = sqlite3.connect('dating.db')
    cursor = conn.cursor()
    
    # Считаем сколько записей будет удалено
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM likes")
    like_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM matches")
    match_count = cursor.fetchone()[0]
    
    print(f"📊 Текущая статистика:")
    print(f"👥 Пользователей: {user_count}")
    print(f"💌 Лайков: {like_count}")
    print(f"💞 Совпадений: {match_count}")
    
    confirm = input(f"\n⚠️ УДАЛИТЬ ВСЕ ({user_count} пользователей)? (да/НЕТ): ").lower()
    
    if confirm == 'да':
        # Удаляем в правильном порядке (сначала зависимости)
        cursor.execute("DELETE FROM likes")
        cursor.execute("DELETE FROM matches")
        cursor.execute("DELETE FROM users")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Удалено: {user_count} пользователей, {like_count} лайков, {match_count} совпадений")
        print("🗑️ База данных полностью очищена!")
    else:
        print("❌ Отменено")
        conn.close()

if __name__ == '__main__':
    clear_all_users()