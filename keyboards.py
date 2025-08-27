from aiogram import types
from database import get_db

def get_admin_keyboard():
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="📢 Рассылка всем")],
                  [types.KeyboardButton(text="📩 Сообщение пользователю")],
                  [types.KeyboardButton(text="🎓 Управление занятиями")],
                  [types.KeyboardButton(text="🗑️ Удалить пользователя")],
                  [types.KeyboardButton(text="📊 Статистика")],
                  [types.KeyboardButton(text="🔙 Выйти из админки")]],
        resize_keyboard=True)
    return keyboard

def get_user_keyboard():
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="💰 Стоимость занятий")],
            [types.KeyboardButton(text="💳 Оплатить занятия")],
            [types.KeyboardButton(text="📞 Связаться с преподавателем")],
            [types.KeyboardButton(text="👤 Мой профиль")],
            [types.KeyboardButton(text="✏️ Редактировать профиль")]
        ],
        resize_keyboard=True)
    return keyboard

def get_categories_keyboard():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()
    conn.close()

    # Создаем список кнопок
    keyboard_buttons = []

    # Добавляем кнопки категорий
    for category in categories:
        keyboard_buttons.append([
            types.KeyboardButton(
                text=f"🎓 {category['name']} - {category['price']} руб.")
        ])

    # Добавляем кнопки действий
    keyboard_buttons.append([types.KeyboardButton(text="➕ Создать категорию")])
    keyboard_buttons.append(
        [types.KeyboardButton(text="🗑️ Удалить категорию")])
    keyboard_buttons.append([types.KeyboardButton(text="🔙 Назад в админку")])

    # Создаем клавиатуру
    keyboard = types.ReplyKeyboardMarkup(keyboard=keyboard_buttons,
                                         resize_keyboard=True)

    return keyboard

def get_cancel_keyboard():
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="❌ Отменить редактирование")]],
        resize_keyboard=True)
    return keyboard