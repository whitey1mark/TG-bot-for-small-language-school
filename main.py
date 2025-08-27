import os
import asyncio
import logging
import threading
from flask import Flask
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError

from database import init_database
from handlers.admin import register_admin_handlers
from handlers.user import register_user_handlers
from handlers.registration import register_registration_handlers
from handlers.common import register_common_handlers
from config import BOT_TOKEN, ADMIN_IDS

# Настройка логирования
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_last_messages = {}  # Будет хранить {user_id: [message_ids]}

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# Создаем Flask app для пробуждения
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

async def main():
    logging.info("🤖 Бот запускается...")
    # Инициализируем базу данных
    init_database()
    
    # Регистрируем обработчики
    register_admin_handlers(dp, bot, user_last_messages, is_admin)
    register_user_handlers(dp, bot, user_last_messages)
    register_registration_handlers(dp, bot, user_last_messages)
    register_common_handlers(dp, bot, user_last_messages, is_admin)

    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Запускаем polling
    await dp.start_polling(bot)

# Запуск бота
if __name__ == "__main__":
    asyncio.run(main())