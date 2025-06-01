import sqlite3
from config import DB_PATH
from datetime import datetime

# Подключаемся к SQLite
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# --- Инициализация таблиц ---

# Таблица задач
cursor.execute('''
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
''')

# Таблица архива
cursor.execute('''
CREATE TABLE IF NOT EXISTS archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    date TEXT NOT NULL,
    time_spent TEXT,
    comment TEXT
);
''')

# Таблица для дневной нормы
cursor.execute('''
CREATE TABLE IF NOT EXISTS daily_norm (
    user_id INTEGER PRIMARY KEY,
    hours REAL NOT NULL
);
''')

# Таблица для пользовательских настроек (режим работы)
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER PRIMARY KEY,
    mode TEXT NOT NULL
);
''')

# Таблица расписания
cursor.execute('''
CREATE TABLE IF NOT EXISTS schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    event_date TEXT NOT NULL,  -- в формате 'YYYY-MM-DD'
    event_time TEXT            -- в формате 'HH:MM', опционально
);
''')

conn.commit()


# --- Функции для работы с задачами ---

def add_task(user_id: int, title: str) -> int:
    cursor.execute(
        'INSERT INTO tasks (user_id, title) VALUES (?, ?)',
        (user_id, title)
    )
    conn.commit()
    return cursor.lastrowid


def list_tasks(user_id: int, include_done: bool = True) -> list:
    if include_done:
        cursor.execute(
            'SELECT id, title, status FROM tasks WHERE user_id = ? ORDER BY id',
            (user_id,)
        )
    else:
        cursor.execute(
            "SELECT id, title, status FROM tasks WHERE user_id = ? AND status = 'pending' ORDER BY id",
            (user_id,)
        )
    return cursor.fetchall()


def complete_task(user_id: int, task_id: int) -> int:
    cursor.execute(
        'UPDATE tasks SET status = "done" WHERE user_id = ? AND id = ?',
        (user_id, task_id)
    )
    conn.commit()
    return cursor.rowcount


# --- Функции для работы с архивом ---

def add_archive(user_id: int, type_: str, title: str, date: str, time_spent: str, comment: str = ''):
    cursor.execute(
        'INSERT INTO archive (user_id, type, title, date, time_spent, comment) VALUES (?, ?, ?, ?, ?, ?)',
        (user_id, type_, title, date, time_spent, comment)
    )
    conn.commit()


def summarize_archive(user_id: int) -> list:
    cursor.execute(
        'SELECT type, COUNT(*) FROM archive WHERE user_id = ? GROUP BY type',
        (user_id,)
    )
    return cursor.fetchall()


# --- Функции для дневной нормы ---

def set_daily_norm(user_id: int, hours: float):
    cursor.execute(
        'INSERT OR REPLACE INTO daily_norm (user_id, hours) VALUES (?, ?)',
        (user_id, hours)
    )
    conn.commit()


def get_daily_norm(user_id: int) -> float | None:
    cursor.execute(
        'SELECT hours FROM daily_norm WHERE user_id = ?',
        (user_id,)
    )
    row = cursor.fetchone()
    return row[0] if row else None


# --- Функции для пользовательских настроек (mode) ---

def set_user_mode(user_id: int, mode: str):
    """
    Устанавливает или обновляет рабочий режим: 'deep' или 'pomodoro'.
    """
    cursor.execute(
        'INSERT OR REPLACE INTO user_settings (user_id, mode) VALUES (?, ?)',
        (user_id, mode)
    )
    conn.commit()


def get_user_mode(user_id: int) -> str:
    """
    Возвращает текущий режим пользователя. Если не установлен, по умолчанию 'deep'.
    """
    cursor.execute(
        'SELECT mode FROM user_settings WHERE user_id = ?',
        (user_id,)
    )
    row = cursor.fetchone()
    return row[0] if row else 'deep'


# --- Функции для Deep Work ---

def log_focus_session(user_id: int, task_title: str, hours: float):
    date_str = datetime.now().strftime('%Y-%m-%d')
    add_archive(user_id, 'focus', task_title, date_str,
                str(hours), 'Deep Work сессия')


def get_today_focus_time(user_id: int) -> float:
    date_str = datetime.now().strftime('%Y-%m-%d')
    cursor.execute(
        'SELECT SUM(CAST(time_spent AS FLOAT)) '
        'FROM archive '
        'WHERE user_id = ? AND date = ? AND type = "focus"',
        (user_id, date_str)
    )
    result = cursor.fetchone()
    return float(result[0]) if result and result[0] is not None else 0.0


# --- Функции для работы с расписанием ---

def add_event(user_id: int, title: str, event_date: str, event_time: str = None, description: str = None) -> int:
    """
    Сохраняет событие в таблицу schedule.
    event_date: строка 'YYYY-MM-DD'
    event_time: строка 'HH:MM' или None
    description: строка или None
    Возвращает ID нового события.
    """
    cursor.execute(
        'INSERT INTO schedule (user_id, title, description, event_date, event_time) '
        'VALUES (?, ?, ?, ?, ?)',
        (user_id, title, description, event_date, event_time)
    )
    conn.commit()
    return cursor.lastrowid


def get_events_by_date(user_id: int, event_date: str) -> list[tuple]:
    """
    Возвращает список событий (id, title, description, event_time)
    для пользователя на конкретную дату.
    event_date: 'YYYY-MM-DD'
    """
    cursor.execute(
        'SELECT id, title, description, event_time '
        'FROM schedule '
        'WHERE user_id = ? AND event_date = ? '
        'ORDER BY event_time IS NULL, event_time ASC',
        (user_id, event_date)
    )
    return cursor.fetchall()


def get_all_events(user_id: int) -> list[tuple]:
    """
    Возвращает все события пользователя, отсортированные по дате и времени.
    """
    cursor.execute(
        'SELECT id, title, description, event_date, event_time '
        'FROM schedule '
        'WHERE user_id = ? '
        'ORDER BY event_date ASC, event_time IS NULL, event_time ASC',
        (user_id,)
    )
    return cursor.fetchall()


def delete_event(user_id: int, event_id: int) -> bool:
    """
    Удаляет событие по его ID (только если принадлежит данному user_id).
    Возвращает True, если удалено (rowcount == 1), иначе False.
    """
    cursor.execute(
        'DELETE FROM schedule WHERE user_id = ? AND id = ?',
        (user_id, event_id)
    )
    conn.commit()
    return cursor.rowcount == 1
