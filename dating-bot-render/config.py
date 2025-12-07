import os
from dotenv import load_dotenv

# Загружаем переменные из .env (для локальной разработки)
load_dotenv()

# Токен бота - берем из переменных окружения Render
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID администратора
ADMIN_ID_STR = os.getenv("ADMIN_ID", "0")
try:
    ADMIN_ID = int(ADMIN_ID_STR)
except ValueError:
    print(f"⚠️ Ошибка: ADMIN_ID '{ADMIN_ID_STR}' не является числом!")
    ADMIN_ID = 0

# Настройки базы данных для Render
# Render предоставляет DATABASE_URL для PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///dating.db")

# Если URL начинается с postgres://, меняем на postgresql://
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Режим работы (webhook или polling)
MODE = os.getenv("BOT_MODE", "webhook")

# Проверка токена
if not BOT_TOKEN or BOT_TOKEN == "ваш_токен_от_BotFather":
    print("❌ ОШИБКА: Добавьте BOT_TOKEN в переменные окружения Render")
    print("📝 Получите токен у @BotFather в Telegram")
    
    # На Render просто логируем, не выходим
    # exit(1)  # Уберите эту строку для Render!

print(f"✅ Конфигурация загружена!")
print(f"   BOT_TOKEN: {BOT_TOKEN[:10]}..." if BOT_TOKEN else "❌ BOT_TOKEN не указан")
print(f"   ADMIN_ID: {ADMIN_ID}")
print(f"   DATABASE_URL: {DATABASE_URL[:30]}..." if DATABASE_URL else "sqlite")
print(f"   MODE: {MODE}")