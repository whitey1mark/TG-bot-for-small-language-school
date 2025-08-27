import sqlite3

def get_db():
    conn = sqlite3.connect('bot_database.db')
    conn.row_factory = sqlite3.Row  # чтобы получать результаты как словари
    return conn

def init_database():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            surname TEXT NOT NULL,
            name TEXT NOT NULL,
            patronymic TEXT NOT NULL,
            gender TEXT,                  -- Новое поле: пол
            email TEXT,                   -- Новое поле: email
            phone_number TEXT NOT NULL,
            full_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Таблица настроек (для суммы оплаты и других параметров)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL
        )
    ''')

    # Таблица платежей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            category_name TEXT NOT NULL,
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'completed',
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    # Добавляем стандартную сумму оплаты, если её нет
    cursor.execute("SELECT * FROM settings WHERE key = 'payment_amount'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO settings (key, value) VALUES ('payment_amount', '1000')"
        )

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            price INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    migrate_database()
    print("✅ База данных инициализирована")

def migrate_database():
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Проверяем существование новых колонок
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]

        # Добавляем недостающие колонки
        if 'surname' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN surname TEXT")
            cursor.execute("ALTER TABLE users ADD COLUMN name TEXT")
            cursor.execute("ALTER TABLE users ADD COLUMN patronymic TEXT")

            # Переносим данные из full_name в новые колонки
            cursor.execute("SELECT id, full_name FROM users")
            users = cursor.fetchall()

            for user in users:
                # Разбиваем full_name на компоненты (простое разделение по пробелу)
                parts = user['full_name'].split()
                surname = parts[0] if len(parts) > 0 else ""
                name = parts[1] if len(parts) > 1 else ""
                patronymic = parts[2] if len(parts) > 2 else ""

                cursor.execute(
                    "UPDATE users SET surname = ?, name = ?, patronymic = ? WHERE id = ?",
                    (surname, name, patronymic, user['id']))

        conn.commit()
        print("✅ База данных успешно мигрирована")

    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        conn.rollback()

    finally:
        conn.close()