import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID администратора (ваш Telegram ID)
ADMIN_ID_STR = os.getenv("ADMIN_ID", "0")
try:
    ADMIN_ID = int(ADMIN_ID_STR)
except ValueError:
    print(f"⚠️ Ошибка: ADMIN_ID '{ADMIN_ID_STR}' не является числом!")
    ADMIN_ID = 0

# Проверка токена
if not BOT_TOKEN or BOT_TOKEN == "ваш_токен_от_BotFather":
    print("❌ ОШИБКА: Добавьте BOT_TOKEN в файл .env")
    print("📝 Получите токен у @BotFather в Telegram")
    exit(1)

if ADMIN_ID == 0:
    print("⚠️ Внимание: ADMIN_ID не указан или указан неверно. Админ-панель недоступна")
    print(f"   Текущее значение: {ADMIN_ID_STR}")

print(f"✅ Конфигурация загружена!")
print(f"   BOT_TOKEN: {BOT_TOKEN[:10]}...")
print(f"   ADMIN_ID: {ADMIN_ID}")