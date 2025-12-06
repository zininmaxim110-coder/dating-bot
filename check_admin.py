import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID_STR = os.getenv("ADMIN_ID")

print("=" * 50)
print("ПРОВЕРКА КОНФИГУРАЦИИ АДМИНА")
print("=" * 50)

print(f"BOT_TOKEN: {BOT_TOKEN}")
print(f"ADMIN_ID (строка): {ADMIN_ID_STR}")

try:
    ADMIN_ID = int(ADMIN_ID_STR)
    print(f"ADMIN_ID (число): {ADMIN_ID}")
    print(f"Тип ADMIN_ID: {type(ADMIN_ID)}")
except ValueError:
    print(f"❌ Ошибка: ADMIN_ID '{ADMIN_ID_STR}' не является числом!")
    ADMIN_ID = 0

# Тест функции is_admin
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

print("\n🔍 Тест проверки админа:")
test_ids = [7736879593, 123456789]
if ADMIN_ID:
    test_ids.append(ADMIN_ID)

for test_id in test_ids:
    result = is_admin(test_id)
    print(f"  is_admin({test_id}): {'✅ Да' if result else '❌ Нет'}")

print("\n" + "=" * 50)
print("ИНСТРУКЦИЯ:")
print("1. Ваш ID можно узнать командой /myid в боте")
print("2. Добавьте его в .env файл как ADMIN_ID")
print("3. Перезапустите бота")
print("=" * 50)