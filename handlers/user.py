from aiogram import types, F
from aiogram.filters import Command, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio

from database import get_db
from states import EditProfileStates
from utils import send_message_with_cleanup
from keyboards import get_user_keyboard, get_cancel_keyboard

def register_user_handlers(dp, bot, user_last_messages):
    # Команда для пользователей - цены
    @dp.message(Command("prices"))
    async def cmd_prices(message: types.Message):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name, price FROM categories ORDER BY price")
        categories = cursor.fetchall()
        conn.close()

        if not categories:
            await message.answer(
                "📚 На данный момент нет доступных категорий занятий.\n"
                "Свяжитесь с перподавателем для уточнения информации.")
            return

        # Формируем красивое сообщение с ценами
        price_list = "💰 *Стоимость занятий:*\n\n"

        for category in categories:
            price_list += f"• {category['name']}: {category['price']} руб.\n"

        price_list += "\n📞 Для записи свяжитесь с преподавателем."

        await message.answer(price_list, parse_mode="Markdown")

    # Обработчик кнопки "Стоимость занятий"
    @dp.message(F.text == "💰 Стоимость занятий")
    async def user_prices_button(message: types.Message):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name, price FROM categories ORDER BY price")
        categories = cursor.fetchall()
        conn.close()

        if not categories:
            await message.answer(
                "📚 На данный момент нет доступных категорий занятий.\n"
                "Свяжитесь с преподавателем для уточнения информации.")
            return

        price_list = "💰 *Стоимость занятий:*\n\n"

        for category in categories:
            price_list += f"• {category['name']}: {category['price']} руб.\n"

        price_list += "\n📞 Для записи нажмите кнопку ниже!"

        await message.answer(price_list, parse_mode="Markdown")

    # Обработчик кнопки профиля
    @dp.message(F.text == "👤 Мой профиль")
    async def user_profile(message: types.Message):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?",
                       (message.from_user.id, ))
        user = cursor.fetchone()
        conn.close()

        if user:
            await message.answer(
                f"👤 *Ваш профиль:*\n\n"
                f"• Имя: {user['full_name']}\n"
                f"• Телефон: {user['phone_number']}\n"
                f"• Дата регистрации: {user['created_at']}\n\n",
                parse_mode="Markdown")
        else:
            await message.answer("❌ Сначала завершите регистрацию через /start")

    # Обработчик кнопки редактирования
    @dp.message(F.text == "✏️ Редактировать профиль")
    async def edit_profile_start(message: types.Message, state):
        builder = InlineKeyboardBuilder()
        builder.button(text="Фамилия", callback_data="edit_surname")
        builder.button(text="Имя", callback_data="edit_name")
        builder.button(text="Отчество", callback_data="edit_patronymic")
        builder.button(text="Телефон", callback_data="edit_phone")
        builder.button(text="❌ Отмена", callback_data="edit_cancel")
        builder.adjust(2)

        await send_message_with_cleanup(bot, message.chat.id,
                                        "📝 *Что вы хотите изменить?*",
                                        parse_mode="Markdown",
                                        reply_markup=builder.as_markup(),
                                        user_last_messages=user_last_messages)
        await state.set_state(EditProfileStates.waiting_edit_choice)

    # Обработчик отмены редактирования
    @dp.callback_query(EditProfileStates.waiting_edit_choice,
                       F.data == "edit_cancel")
    async def process_edit_cancel(callback: types.CallbackQuery,
                                  state):
        await callback.message.answer("❌ Редактирование отменено.",
                                      reply_markup=get_user_keyboard())
        await state.clear()
        await callback.answer()

    # Обработчик выбора поля для редактирования
    @dp.callback_query(EditProfileStates.waiting_edit_choice,
                       F.data.startswith("edit_"))
    async def process_edit_choice(callback: types.CallbackQuery,
                                  state):
        field = callback.data.replace("edit_", "")
        field_messages = {
            "surname": "Введите новую фамилию:",
            "name": "Введите новое имя:",
            "patronymic": "Введите новое отчество:",
            "phone": "Введите новый номер телефона:"
        }

        await state.update_data(edit_field=field)

        # Удаляем предыдущее сообщение с инлайн-клавиатурой
        try:
            await bot.delete_message(callback.message.chat.id,
                                     callback.message.message_id)
        except:
            pass

        message = await send_message_with_cleanup(
            bot,
            callback.message.chat.id,
            field_messages[field],
            reply_markup=get_cancel_keyboard(),
            user_last_messages=user_last_messages)

        # Устанавливаем соответствующее состояние
        if field == "surname":
            await state.set_state(EditProfileStates.waiting_edit_surname)
        elif field == "name":
            await state.set_state(EditProfileStates.waiting_edit_name)
        elif field == "patronymic":
            await state.set_state(EditProfileStates.waiting_edit_patronymic)
        elif field == "phone":
            await state.set_state(EditProfileStates.waiting_edit_phone)

        await callback.answer()

    # Обработчики редактирования с фильтром
    @dp.message(EditProfileStates.waiting_edit_surname, F.text
                != "❌ Отменить редактирование")
    async def process_edit_surname(message: types.Message, state):
        await update_user_field(message, state, "surname", message.text)

    @dp.message(EditProfileStates.waiting_edit_name, F.text
                != "❌ Отменить редактирование")
    async def process_edit_name(message: types.Message, state):
        await update_user_field(message, state, "name", message.text)

    @dp.message(EditProfileStates.waiting_edit_patronymic, F.text
                != "❌ Отменить редактирование")
    async def process_edit_patronymic(message: types.Message, state):
        await update_user_field(message, state, "patronymic", message.text)

    @dp.message(EditProfileStates.waiting_edit_phone, F.text
                != "❌ Отменить редактирование")
    async def process_edit_phone(message: types.Message, state):
        await update_user_field(message, state, "phone_number", message.text)

    # Обработчик отмены для всех состояний редактирования
    @dp.message(
        F.text == "❌ Отменить редактирование",
        StateFilter(EditProfileStates.waiting_edit_surname,
                    EditProfileStates.waiting_edit_name,
                    EditProfileStates.waiting_edit_patronymic,
                    EditProfileStates.waiting_edit_phone))
    async def cancel_editing(message: types.Message, state):
        await send_message_with_cleanup(bot, message.chat.id,
                                        "❌ Редактирование отменено.",
                                        reply_markup=get_user_keyboard(),
                                        user_last_messages=user_last_messages)
        await state.clear()

    # Обработчик кнопки оплаты
    @dp.message(F.text == "💳 Оплатить занятия")
    async def pay_for_lessons(message: types.Message):
        # Сначала показываем доступные категории
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name, price FROM categories ORDER BY price")
        categories = cursor.fetchall()
        conn.close()

        if not categories:
            await message.answer(
                "📚 На данный момент нет доступных категорий для оплаты.\n"
                "Свяжитесь с преподавателем для уточнения информации.")
            return

        # Создаем инлайн-клавиатуру с категориями
        builder = InlineKeyboardBuilder()

        for category in categories:
            builder.button(text=f"{category['name']} - {category['price']} руб.",
                           callback_data=f"pay_{category['name']}")

        builder.adjust(1)  # По одной кнопке в строке

        await message.answer(
            "🎯 *Выберите категорию для оплаты:*\n\n"
            "После выбора вы будете перенаправлены на страницу оплаты.",
            parse_mode="Markdown",
            reply_markup=builder.as_markup())

    # Обработчик выбора категории
    @dp.callback_query(F.data.startswith("pay_"))
    async def process_payment_selection(callback: types.CallbackQuery):
        category_name = callback.data.replace("pay_", "")

        await callback.message.answer(
            f"💳 *Оплата: {category_name}*\n\n"
            f"Перейдите по ссылке для оплаты: https://www.tbank.ru/cf/1Tmq99zZo95\n\n"
            f"После оплаты свяжитесь с преподавателем для подтверждения.",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

        await callback.answer()

async def update_user_field(message: types.Message, state, field: str, new_value: str, bot, user_last_messages):
    user_data = await state.get_data()

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?",
                       (new_value.strip(), message.from_user.id))
        conn.commit()

        if field in ["surname", "name", "patronymic"]:
            cursor.execute(
                "SELECT surname, name, patronymic FROM users WHERE user_id = ?",
                (message.from_user.id, ))
            user = cursor.fetchone()
            if user:
                full_name = f"{user['surname']} {user['name']} {user['patronymic']}"
                cursor.execute(
                    "UPDATE users SET full_name = ? WHERE user_id = ?",
                    (full_name, message.from_user.id))
                conn.commit()

        await send_message_with_cleanup(bot, message.chat.id,
                                        "✅ Данные успешно обновлены!",
                                        reply_markup=get_user_keyboard(),
                                        user_last_messages=user_last_messages)

    except Exception as e:
        await send_message_with_cleanup(bot, message.chat.id,
                                        f"❌ Ошибка при обновлении: {str(e)}",
                                        reply_markup=get_user_keyboard(),
                                        user_last_messages=user_last_messages)

    finally:
        conn.close()
        await state.clear()