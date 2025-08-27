from aiogram import types, F
from aiogram.filters import Command, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
import sqlite3
import asyncio

from database import get_db
from states import AdminStates
from utils import send_message_with_cleanup
from keyboards import get_admin_keyboard, get_categories_keyboard

def register_admin_handlers(dp, bot, user_last_messages, is_admin_func):
    # Команда админа
    @dp.message(Command("admin"))
    async def cmd_admin(message: types.Message):
        if not is_admin_func(message.from_user.id):
            await message.answer("❌ Доступ запрещен")
            return

        await message.answer("👨‍💻 Панель администратора",
                             reply_markup=get_admin_keyboard())

    # Обработчики кнопок админа
    @dp.message(F.text == "📢 Рассылка всем")
    async def admin_broadcast(message: types.Message, state):
        if not is_admin_func(message.from_user.id):
            return

        await message.answer("Введите сообщение для рассылки:",
                             reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(AdminStates.waiting_broadcast_message)

    @dp.message(F.text == "🗑️ Удалить пользователя")
    async def admin_delete_user(message: types.Message, state):
        if not is_admin_func(message.from_user.id):
            return

        await message.answer(
            "Введите ID пользователя или номер телефона для удаления:",
            reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(AdminStates.waiting_delete_user)

    @dp.message(AdminStates.waiting_delete_user)
    async def process_delete_user(message: types.Message, state):
        if not is_admin_func(message.from_user.id):
            await state.clear()
            return

        user_input = message.text.strip()
        conn = get_db()
        cursor = conn.cursor()

        try:
            user = None

            # Сначала пробуем найти по номеру телефона
            cursor.execute(
                "SELECT user_id, full_name, phone_number FROM users WHERE phone_number LIKE ?",
                (f"%{user_input}%", ))
            user = cursor.fetchone()

            # Если не нашли по номеру, пробуем по ID
            if not user and user_input.isdigit():
                cursor.execute(
                    "SELECT user_id, full_name, phone_number FROM users WHERE user_id = ?",
                    (int(user_input), ))
                user = cursor.fetchone()

            if user:
                # Сохраняем данные пользователя в состоянии
                await state.update_data(delete_user_id=user['user_id'],
                                        delete_user_name=user['full_name'],
                                        delete_user_phone=user['phone_number'])

                # Переходим в состояние подтверждения
                confirm_keyboard = types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="✅ Да, удалить")],
                              [types.KeyboardButton(text="❌ Нет, отменить")]],
                    resize_keyboard=True)

                await message.answer(
                    f"⚠️ *Вы уверены что хотите удалить пользователя?*\n\n"
                    f"👤 *Имя:* {user['full_name']}\n"
                    f"📞 *Телефон:* {user['phone_number']}\n"
                    f"🆔 *ID:* {user['user_id']}\n\n"
                    f"*Это действие нельзя отменить!*",
                    parse_mode="Markdown",
                    reply_markup=confirm_keyboard)

                # ПЕРЕХОДИМ В СОСТОЯНИЕ ПОДТВЕРЖДЕНИЯ
                await state.set_state(AdminStates.waiting_delete_confirm)

            else:
                await message.answer("❌ Пользователь не найден.",
                                     reply_markup=get_admin_keyboard())
                await state.clear()

        except Exception as e:
            await message.answer(f"❌ Ошибка при поиске: {str(e)}",
                                 reply_markup=get_admin_keyboard())
            await state.clear()

        finally:
            conn.close()

    @dp.message(AdminStates.waiting_delete_confirm,
                F.text.in_(["✅ Да, удалить", "❌ Нет, отменить"]))
    async def process_delete_confirm(message: types.Message, state):
        if not is_admin_func(message.from_user.id):
            await state.clear()
            return

        user_data = await state.get_data()

        if message.text == "✅ Да, удалить" and 'delete_user_id' in user_data:
            user_id = user_data['delete_user_id']
            user_name = user_data['delete_user_name']

            conn = get_db()
            cursor = conn.cursor()

            try:
                # Удаляем связанные данные
                cursor.execute("DELETE FROM payments WHERE user_id = ?",
                               (user_id, ))
                # Удаляем пользователя
                cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id, ))
                conn.commit()

                await message.answer(
                    f"✅ Пользователь *{user_name}* успешно удален!",
                    parse_mode="Markdown",
                    reply_markup=get_admin_keyboard())

            except Exception as e:
                await message.answer(f"❌ Ошибка при удалении: {str(e)}",
                                     reply_markup=get_admin_keyboard())

            finally:
                conn.close()

        else:
            await message.answer("❌ Удаление отменено.",
                                 reply_markup=get_admin_keyboard())

        await state.clear()

    # Обработчик кнопки "Управление занятиями"
    @dp.message(F.text == "🎓 Управление занятиями")
    async def admin_manage_categories(message: types.Message):
        if not is_admin_func(message.from_user.id):
            return

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM categories")
        count = cursor.fetchone()[0]
        conn.close()

        if count == 0:
            await message.answer(
                "📚 Категорий занятий пока нет.\n"
                "Вы можете создать новую категорию с помощью кнопки ниже.",
                reply_markup=get_categories_keyboard())
        else:
            await message.answer("🎓 Управление категориями занятий:",
                                 reply_markup=get_categories_keyboard())

    # Обработчик кнопки "Создать категорию"
    @dp.message(F.text == "➕ Создать категорию")
    async def admin_create_category(message: types.Message, state):
        if not is_admin_func(message.from_user.id):
            return

        await message.answer("Введите название новой категории:",
                             reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(AdminStates.waiting_category_name)

    # Обработчик названия категории
    @dp.message(AdminStates.waiting_category_name)
    async def process_category_name(message: types.Message, state):
        if not is_admin_func(message.from_user.id):
            await state.clear()
            return

        category_name = message.text.strip()

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM categories WHERE name = ?",
                           (category_name, ))
            if cursor.fetchone():
                await message.answer(
                    "❌ Категория с таким названием уже существует.\n"
                    "Введите другое название:")
                return

            await state.update_data(category_name=category_name)

            await message.answer("Теперь введите стоимость для этой категории:")
            await state.set_state(AdminStates.waiting_category_price)

        finally:
            conn.close()

    # Обработчик цены категории
    @dp.message(AdminStates.waiting_category_price)
    async def process_category_price(message: types.Message, state):
        if not is_admin_func(message.from_user.id):
            await state.clear()
            return

        try:
            price = int(message.text.strip())
            if price <= 0:
                raise ValueError

            user_data = await state.get_data()
            category_name = user_data['category_name']

            conn = get_db()
            cursor = conn.cursor()

            try:
                cursor.execute(
                    "INSERT INTO categories (name, price) VALUES (?, ?)",
                    (category_name, price))
                conn.commit()

                await message.answer(
                    f"✅ Категория *{category_name}* создана!\n"
                    f"💰 Стоимость: {price} руб.",
                    parse_mode="Markdown",
                    reply_markup=get_categories_keyboard())

            except sqlite3.IntegrityError:
                await message.answer(
                    "❌ Категория с таким названием уже существует.",
                    reply_markup=get_categories_keyboard())

            finally:
                conn.close()

            await state.clear()

        except ValueError:
            await message.answer("❌ Пожалуйста, введите корректную сумму:")

    # Обработчик кнопки "Удалить категорию"
    @dp.message(F.text == "🗑️ Удалить категорию")
    async def admin_delete_category(message: types.Message, state):
        if not is_admin_func(message.from_user.id):
            return

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories")
        categories = cursor.fetchall()
        conn.close()

        if not categories:
            await message.answer("❌ Нет категорий для удаления.",
                                 reply_markup=get_categories_keyboard())
            return

        # Создаем инлайн-клавиатуру с категориями
        builder = InlineKeyboardBuilder()

        for category in categories:
            builder.button(text=f"{category['name']} - {category['price']} руб.",
                           callback_data=f"delete_cat_{category['id']}")

        builder.button(text="❌ Отмена", callback_data="delete_cancel")
        builder.adjust(1)

        await message.answer("🗑️ *Выберите категорию для удаления:*",
                             parse_mode="Markdown",
                             reply_markup=builder.as_markup())

        await state.set_state(AdminStates.waiting_delete_category)

    # Обработчик выбора категории для удаления
    @dp.callback_query(AdminStates.waiting_delete_category,
                       F.data.startswith("delete_cat_"))
    async def process_delete_category_selection(callback: types.CallbackQuery,
                                                state):
        if not is_admin_func(callback.from_user.id):
            await state.clear()
            return

        category_id = int(callback.data.replace("delete_cat_", ""))

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM categories WHERE id = ?",
                           (category_id, ))
            category = cursor.fetchone()

            if category:
                cursor.execute("DELETE FROM categories WHERE id = ?",
                               (category_id, ))
                conn.commit()

                await callback.message.answer(
                    f"✅ Категория *{category['name']}* удалена!",
                    parse_mode="Markdown",
                    reply_markup=get_categories_keyboard())

            else:
                await callback.message.answer("❌ Категория не найдена.",
                                              reply_markup=get_categories_keyboard())

        finally:
            conn.close()

        await state.clear()
        await callback.answer()

    # Обработчик отмены удаления
    @dp.callback_query(AdminStates.waiting_delete_category,
                       F.data == "delete_cancel")
    async def process_delete_cancel(callback: types.CallbackQuery, state):
        await callback.message.answer("❌ Удаление отменено.",
                                      reply_markup=get_categories_keyboard())
        await state.clear()
        await callback.answer()

    # Обработчик кнопки "Сообщение пользователю"
    @dp.message(F.text == "📩 Сообщение пользователю")
    async def admin_message_user(message: types.Message, state):
        if not is_admin_func(message.from_user.id):
            return

        await message.answer(
            "Введите ID пользователя или номер телефона для отправки сообщения:",
            reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(AdminStates.waiting_user_phone)

    # Обработчик ID/телефона пользователя
    @dp.message(AdminStates.waiting_user_phone)
    async def process_user_identifier(message: types.Message, state):
        if not is_admin_func(message.from_user.id):
            await state.clear()
            return

        user_input = message.text.strip()
        conn = get_db()
        cursor = conn.cursor()

        try:
            user = None

            # Сначала пробуем найти по номеру телефона
            cursor.execute(
                "SELECT user_id, full_name FROM users WHERE phone_number LIKE ?",
                (f"%{user_input}%", ))
            user = cursor.fetchone()

            # Если не нашли по номеру, пробуем по ID
            if not user and user_input.isdigit():
                cursor.execute(
                    "SELECT user_id, full_name FROM users WHERE user_id = ?",
                    (int(user_input), ))
                user = cursor.fetchone()

            if user:
                await state.update_data(target_user_id=user['user_id'],
                                        target_user_name=user['full_name'])

                await message.answer(
                    f"👤 Пользователь найден: {user['full_name']}\n"
                    f"Введите сообщение для отправки:")
                await state.set_state(AdminStates.waiting_user_message)

            else:
                await message.answer("❌ Пользователь не найден.",
                                     reply_markup=get_admin_keyboard())
                await state.clear()

        finally:
            conn.close()

    # Обработчик сообщения пользователю
    @dp.message(AdminStates.waiting_user_message)
    async def process_user_message(message: types.Message, state):
        if not is_admin_func(message.from_user.id):
            await state.clear()
            return

        user_data = await state.get_data()
        target_user_id = user_data['target_user_id']
        target_user_name = user_data['target_user_name']
        admin_message = message.text

        try:
            await bot.send_message(
                target_user_id,
                f"📩 *Сообщение от преподавателя:*\n\n{admin_message}",
                parse_mode="Markdown")

            await message.answer(
                f"✅ Сообщение отправлено пользователю {target_user_name}!",
                reply_markup=get_admin_keyboard())

        except Exception as e:
            await message.answer(
                f"❌ Не удалось отправить сообщение: {str(e)}",
                reply_markup=get_admin_keyboard())

        await state.clear()

    # Обработчик кнопки "Статистика"
    @dp.message(F.text == "📊 Статистика")
    async def admin_statistics(message: types.Message):
        if not is_admin_func(message.from_user.id):
            return

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM payments")
        total_payments = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(amount) FROM payments")
        total_revenue = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM categories")
        total_categories = cursor.fetchone()[0]

        conn.close()

        stats_message = (
            f"📊 *Статистика бота:*\n\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"💳 Всего платежей: {total_payments}\n"
            f"💰 Общая выручка: {total_revenue} руб.\n"
            f"🎓 Категорий занятий: {total_categories}"
        )

        await message.answer(stats_message, parse_mode="Markdown")

    # Обработчик кнопки "Выйти из админки"
    @dp.message(F.text == "🔙 Выйти из админки")
    async def admin_exit(message: types.Message):
        if not is_admin_func(message.from_user.id):
            return

        await message.answer("👋 Вы вышли из админ-панели",
                             reply_markup=types.ReplyKeyboardRemove())

    # Обработчик рассылки
    @dp.message(AdminStates.waiting_broadcast_message)
    async def process_broadcast(message: types.Message, state):
        if not is_admin_func(message.from_user.id):
            await state.clear()
            return

        broadcast_text = message.text

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        conn.close()

        success_count = 0
        fail_count = 0

        await message.answer(f"📤 Начинаю рассылку для {len(users)} пользователей...")

        for user in users:
            try:
                await bot.send_message(user['user_id'],
                                       f"📢 *Объявление:*\n\n{broadcast_text}",
                                       parse_mode="Markdown")
                success_count += 1
                await asyncio.sleep(0.1)  # Задержка чтобы не спамить
            except Exception:
                fail_count += 1

        await message.answer(
            f"✅ Рассылка завершена!\n"
            f"✓ Успешно: {success_count}\n"
            f"✗ Не удалось: {fail_count}",
            reply_markup=get_admin_keyboard())

        await state.clear()