from aiogram import types, F
from aiogram.types import ReplyKeyboardRemove
import sqlite3

from database import get_db
from states import RegistrationStates
from utils import send_message_with_cleanup
from keyboards import get_user_keyboard

def register_registration_handlers(dp, bot, user_last_messages):
    # Обработчик фамилии
    @dp.message(RegistrationStates.waiting_for_surname)
    async def process_surname(message: types.Message, state):
        await state.update_data(surname=message.text.strip())
        await message.answer("Теперь введите ваше *имя*:", parse_mode="Markdown")
        await state.set_state(RegistrationStates.waiting_for_name)

    # Обработчик имени
    @dp.message(RegistrationStates.waiting_for_name)
    async def process_name(message: types.Message, state):
        await state.update_data(name=message.text.strip())
        await message.answer("Теперь введите ваше *отчество*:",
                             parse_mode="Markdown")
        await state.set_state(RegistrationStates.waiting_for_patronymic)

    # Обработчик отчества
    @dp.message(RegistrationStates.waiting_for_patronymic)
    async def process_patronymic(message: types.Message, state):
        await state.update_data(patronymic=message.text.strip())

        # Клавиатура для выбора пола
        gender_keyboard = types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="👨 Мужской")],
                      [types.KeyboardButton(text="👩 Женский")],
                      [types.KeyboardButton(text="🤷 Не указывать")]],
            resize_keyboard=True)

        await message.answer("Выберите ваш *пол*:",
                             parse_mode="Markdown",
                             reply_markup=gender_keyboard)
        await state.set_state(RegistrationStates.waiting_for_gender)

    # Обработчик пола
    @dp.message(RegistrationStates.waiting_for_gender)
    async def process_gender(message: types.Message, state):
        gender_map = {
            "👨 Мужской": "male",
            "👩 Женский": "female",
            "🤷 Не указывать": "not_specified"
        }

        if message.text not in gender_map:
            await message.answer(
                "Пожалуйста, выберите пол из предложенных вариантов:")
            return

        await state.update_data(gender=gender_map[message.text])
        await message.answer("Теперь введите ваш *email*:",
                             parse_mode="Markdown",
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state(RegistrationStates.waiting_for_email)

    # Обработчик email
    @dp.message(RegistrationStates.waiting_for_email)
    async def process_email(message: types.Message, state):
        email = message.text.strip()

        # Простая валидация email
        if "@" not in email or "." not in email:
            await message.answer("❌ Пожалуйста, введите корректный email адрес:")
            return

        await state.update_data(email=email)

        # Переходим к вводу телефона
        keyboard = types.ReplyKeyboardMarkup(keyboard=[[
            types.KeyboardButton(text="📱 Отправить номер телефона",
                                 request_contact=True)
        ]],
                                             resize_keyboard=True)

        await message.answer("Отлично! Теперь отправьте ваш *номер телефона*:",
                             parse_mode="Markdown",
                             reply_markup=keyboard)
        await state.set_state(RegistrationStates.waiting_for_phone)

    # Обработка номера телефона
    @dp.message(RegistrationStates.waiting_for_phone, F.contact)
    async def process_phone(message: types.Message, state):
        user_data = await state.get_data()
        phone_number = message.contact.phone_number

        # Формируем полное ФИО
        full_name = f"{user_data['surname']} {user_data['name']} {user_data['patronymic']}"

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (user_id, username, surname, name, patronymic, full_name, phone_number) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (message.from_user.id, message.from_user.username,
                 user_data['surname'], user_data['name'], user_data['patronymic'],
                 full_name, phone_number))
            conn.commit()

            await message.answer(
                f"✅ *Регистрация завершена!*\n\n"
                f"👤 *ФИО:* {full_name}\n"
                f"📞 *Телефон:* {phone_number}\n\n"
                f"Теперь вы можете ознакомиться с нашими услугами.",
                parse_mode="Markdown",
                reply_markup=get_user_keyboard())

        except sqlite3.IntegrityError:
            await message.answer("❌ Вы уже зарегистрированы!",
                                 reply_markup=get_user_keyboard())

        finally:
            conn.close()
            await state.clear()