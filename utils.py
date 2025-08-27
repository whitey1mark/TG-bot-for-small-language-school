from aiogram import types
from aiogram.exceptions import TelegramAPIError

async def send_message_with_cleanup(bot, chat_id, text, reply_markup=None, parse_mode=None, user_last_messages=None):
    # Удаляем предыдущие сообщения бота у этого пользователя
    if user_last_messages and chat_id in user_last_messages:
        for msg_id in user_last_messages[chat_id]:
            try:
                await bot.delete_message(chat_id, msg_id)
            except TelegramAPIError:
                pass  # Игнорируем ошибки удаления

    # Отправляем новое сообщение
    message = await bot.send_message(chat_id=chat_id,
                                     text=text,
                                     reply_markup=reply_markup,
                                     parse_mode=parse_mode)

    # Сохраняем ID нового сообщения
    if user_last_messages:
        if chat_id not in user_last_messages:
            user_last_messages[chat_id] = []
        user_last_messages[chat_id].append(message.message_id)

        # Ограничиваем количество сообщений для хранения (например, последние 5)
        if len(user_last_messages[chat_id]) > 5:
            user_last_messages[chat_id] = user_last_messages[chat_id][-5:]

    return message

async def add_message_to_cleanup(chat_id, message_id, user_last_messages):
    if chat_id not in user_last_messages:
        user_last_messages[chat_id] = []

    user_last_messages[chat_id].append(message_id)

    # Ограничиваем количество сообщений для хранения (например, последние 5)
    if len(user_last_messages[chat_id]) > 5:
        user_last_messages[chat_id] = user_last_messages[chat_id][-5:]

def run_flask(app):
    app.run(host='0.0.0.0', port=8080)