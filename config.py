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

# Путь к базе данных
# На Amvera данные сохраняются в /data
DATA_DIR = os.getenv("DATA_DIR", "/data")

# Создаём папку если её нет (для локальной разработки)
if DATA_DIR != "/data" and not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

# URL базы данных
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Проверяем, запущено ли на сервере (Amvera) или локально
    if os.path.exists("/data"):
        DATABASE_URL = "sqlite:////data/dating.db"
        print("📁 Amvera: /data/dating.db")
    else:
        DATABASE_URL = "sqlite:///dating.db"
        print("📁 Локальная SQLite база")
else:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    print("🐘 PostgreSQL")

# Проверка токена
if not BOT_TOKEN:
    print("❌ ОШИБКА: Добавьте BOT_TOKEN в переменные окружения")
    exit(1)

if ADMIN_ID == 0:
    print("⚠️ ADMIN_ID не указан")

print(f"✅ Конфигурация загружена!")
print(f"   ADMIN_ID: {ADMIN_ID}")