from aiogram import types, F
from aiogram.filters import Command
from aiogram.exceptions import TelegramAPIError

from database import get_db
from utils import send_message_with_cleanup
from keyboards import get_user_keyboard  # Добавьте этот импорт
from states import RegistrationStates  # Добавьте этот импорт

def register_common_handlers(dp, bot, user_last_messages, is_admin_func):
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message, state):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE user_id = ?",
                       (message.from_user.id, ))
        user = cursor.fetchone()

        conn.close()

        if user:
            await send_message_with_cleanup(bot, message.chat.id,
                                            "С возвращением! Чем могу помочь?",
                                            reply_markup=get_user_keyboard(),
                                            user_last_messages=user_last_messages)
        else:
            await send_message_with_cleanup(
                bot,
                message.chat.id,
                "Добро пожаловать! Для регистрации введите вашу *фамилию*:",
                parse_mode="Markdown",
                user_last_messages=user_last_messages)
            await state.set_state(RegistrationStates.waiting_for_surname)

    @dp.message(F.text == "📞 Связаться с преподавателем")
    async def contact_admin(message: types.Message):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT phone_number FROM users WHERE user_id = ?",
                       (message.from_user.id, ))
        user = cursor.fetchone()
        conn.close()

        if user:
            await message.answer(
                f"📞 Ваш номер: {user['phone_number']}\n"
                f"Преподаватель свяжется с вами в ближайшее время!")

                # Уведомляем админа
            try:
                for admin_id in is_admin_func:
                    try:
                        await bot.send_message(
                            admin_id,
                            f"👤 Пользователь @{message.from_user.username} запросил связь!\n"
                            f"Телефон: {user['phone_number']}\n"
                            f"Имя: {message.from_user.full_name}")
                    except TelegramAPIError:
                        pass  # Игнорируем ошибки отправки уведомлений
            except Exception as e:
                print(f"Error sending message to admin: {e}")
            else:
                await message.answer("❌ Сначала завершите регистрацию через /start")