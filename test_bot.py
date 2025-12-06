print("=== ТЕСТ БОТА ===")

# Проверка библиотек
try:
    import aiogram
    print("✅ Aiogram установлен")
except ImportError:
    print("❌ Aiogram НЕ установлен")

try:
    import dotenv
    print("✅ python-dotenv установлен")
except ImportError:
    print("❌ python-dotenv НЕ установлен")

try:
    import sqlalchemy
    print("✅ SQLAlchemy установлен")
except ImportError:
    print("❌ SQLAlchemy НЕ установлен")

# Проверка токена
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("BOT_TOKEN")

if token and token != "ваш_токен_от_BotFather":
    print(f"✅ Токен загружен: {token[:10]}...")
else:
    print("❌ Токен НЕ загружен. Проверьте файл .env")

print("\n=== ТЕСТ ЗАВЕРШЕН ===")