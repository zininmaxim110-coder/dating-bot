import os
from dotenv import load_dotenv

# Загружаем .env только локально
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID администратора
ADMIN_ID_STR = os.getenv("ADMIN_ID", "0")
try:
    ADMIN_ID = int(ADMIN_ID_STR)
except ValueError:
    print(f"⚠️ Ошибка: ADMIN_ID '{ADMIN_ID_STR}' не является числом!")
    ADMIN_ID = 0

# URL базы данных (Railway PostgreSQL или локальный SQLite)
DATABASE_URL = os.getenv("DATABASE_URL")

# Если DATABASE_URL не указан - используем локальный SQLite
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///dating.db"
    print("📁 Используется локальная SQLite база")
else:
    # Railway даёт postgres://, но SQLAlchemy нужен postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    print("🐘 Используется PostgreSQL")

# Проверка токена
if not BOT_TOKEN or BOT_TOKEN == "ваш_токен_от_BotFather":
    print("❌ ОШИБКА: Добавьте BOT_TOKEN в переменные окружения")
    exit(1)

if ADMIN_ID == 0:
    print("⚠️ Внимание: ADMIN_ID не указан. Админ-панель недоступна")

print(f"✅ Конфигурация загружена!")
print(f"   BOT_TOKEN: {BOT_TOKEN[:10]}...")
print(f"   ADMIN_ID: {ADMIN_ID}")