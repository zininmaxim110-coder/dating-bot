import os
import asyncio
import logging
from flask import Flask, request
import threading
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask приложение для keep-alive
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "🤖 Дейтинг-бот работает на Render!"

@flask_app.route('/health')
def health():
    return {"status": "healthy", "service": "dating-bot"}, 200

@flask_app.route('/ping')
def ping():
    return "pong", 200

async def start_bot_polling():
    """Запуск бота в режиме polling (для Render бесплатного тарифа)"""
    try:
        # Динамический импорт вашего бота
        from bot import main
        
        logger.info("🚀 Запуск бота в режиме polling...")
        await main()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        import traceback
        traceback.print_exc()

def run_bot():
    """Запуск бота в отдельном потоке"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_bot_polling())
    except Exception as e:
        logger.error(f"❌ Ошибка в потоке бота: {e}")

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("🤖 Запуск дейтинг-бота на Render")
    logger.info("=" * 50)
    
    # Запускаем бот в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("✅ Бот запущен в фоновом потоке")
    
    # Запускаем Flask сервер
    port = int(os.getenv('PORT', 8443))
    logger.info(f"🌐 Flask сервер запускается на порту {port}")
    
    # Для production используем waitress
    try:
        from waitress import serve
        logger.info("🚀 Запуск через Waitress (production)...")
        serve(flask_app, host='0.0.0.0', port=port)
    except ImportError:
        logger.info("⚡ Запуск через Flask (development)...")
        flask_app.run(host='0.0.0.0', port=port, debug=False)