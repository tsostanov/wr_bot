import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

from config import DB_PATH


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS archive (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                entry_type TEXT NOT NULL,
                title TEXT NOT NULL,
                entry_date TEXT NOT NULL,
                minutes_spent INTEGER,
                comment TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS daily_norm (
                user_id INTEGER PRIMARY KEY,
                hours REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                mode TEXT NOT NULL DEFAULT 'deep'
            );

            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                event_date TEXT NOT NULL,
                event_time TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_user_status
            ON tasks(user_id, status, id);

            CREATE INDEX IF NOT EXISTS idx_archive_user_date_type
            ON archive(user_id, entry_date, entry_type);

            CREATE INDEX IF NOT EXISTS idx_schedule_user_date_time
            ON schedule(user_id, event_date, event_time);
            """
        )


def add_task(user_id: int, title: str) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (user_id, title) VALUES (?, ?)",
            (user_id, title),
        )
        return int(cursor.lastrowid)


def list_tasks(user_id: int, include_done: bool = True) -> list[tuple[int, str, str]]:
    query = "SELECT id, title, status FROM tasks WHERE user_id = ?"
    params: tuple[object, ...] = (user_id,)

    if not include_done:
        query += " AND status = 'pending'"

    query += " ORDER BY id"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [(row["id"], row["title"], row["status"]) for row in rows]


def get_task(user_id: int, task_id: int) -> tuple[int, str, str] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, title, status FROM tasks WHERE user_id = ? AND id = ?",
            (user_id, task_id),
        ).fetchone()
        if row is None:
            return None
        return row["id"], row["title"], row["status"]


def complete_task(user_id: int, task_id: int) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT title, status FROM tasks WHERE user_id = ? AND id = ?",
            (user_id, task_id),
        ).fetchone()
        if row is None:
            return None

        if row["status"] != "done":
            conn.execute(
                "UPDATE tasks SET status = 'done' WHERE user_id = ? AND id = ?",
                (user_id, task_id),
            )

        return str(row["title"])


def add_archive(
    user_id: int,
    entry_type: str,
    title: str,
    entry_date: str,
    minutes_spent: int | None = None,
    comment: str = "",
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO archive (user_id, entry_type, title, entry_date, minutes_spent, comment)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, entry_type, title, entry_date, minutes_spent, comment),
        )


def summarize_archive(user_id: int) -> list[tuple[str, int]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT entry_type, COUNT(*) AS total
            FROM archive
            WHERE user_id = ?
            GROUP BY entry_type
            ORDER BY entry_type
            """,
            (user_id,),
        ).fetchall()
        return [(row["entry_type"], row["total"]) for row in rows]


def get_recent_archive_entries(
    user_id: int,
    limit: int = 10,
) -> list[tuple[str, str, str, int | None, str]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT entry_type, title, entry_date, minutes_spent, comment
            FROM archive
            WHERE user_id = ?
            ORDER BY entry_date DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [
            (
                row["entry_type"],
                row["title"],
                row["entry_date"],
                row["minutes_spent"],
                row["comment"],
            )
            for row in rows
        ]


def set_daily_norm(user_id: int, hours: float) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO daily_norm (user_id, hours)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET hours = excluded.hours
            """,
            (user_id, hours),
        )


def get_daily_norm(user_id: int) -> float | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT hours FROM daily_norm WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            return None
        return float(row["hours"])


def set_user_mode(user_id: int, mode: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_settings (user_id, mode)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET mode = excluded.mode
            """,
            (user_id, mode),
        )


def get_user_mode(user_id: int) -> str:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT mode FROM user_settings WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            return "deep"
        return str(row["mode"])


def log_focus_session(user_id: int, task_title: str, hours: float, comment: str) -> None:
    minutes_spent = max(0, round(hours * 60))
    add_archive(
        user_id=user_id,
        entry_type="focus",
        title=task_title,
        entry_date=datetime.now().date().isoformat(),
        minutes_spent=minutes_spent,
        comment=comment,
    )


def get_today_focus_time(user_id: int, date_str: str) -> float:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(minutes_spent), 0) AS total_minutes
            FROM archive
            WHERE user_id = ? AND entry_date = ? AND entry_type = 'focus'
            """,
            (user_id, date_str),
        ).fetchone()
        return float(row["total_minutes"]) / 60 if row is not None else 0.0


def add_event(
    user_id: int,
    title: str,
    event_date: str,
    event_time: str | None = None,
    description: str | None = None,
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO schedule (user_id, title, description, event_date, event_time)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, title, description, event_date, event_time),
        )
        return int(cursor.lastrowid)


def get_events_by_date(
    user_id: int,
    event_date: str,
) -> list[tuple[int, str, str | None, str | None]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, title, description, event_time
            FROM schedule
            WHERE user_id = ? AND event_date = ?
            ORDER BY event_time IS NULL, event_time ASC, id ASC
            """,
            (user_id, event_date),
        ).fetchall()
        return [
            (row["id"], row["title"], row["description"], row["event_time"])
            for row in rows
        ]


def get_all_events(
    user_id: int,
) -> list[tuple[int, str, str | None, str, str | None]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, title, description, event_date, event_time
            FROM schedule
            WHERE user_id = ?
            ORDER BY event_date ASC, event_time IS NULL, event_time ASC, id ASC
            """,
            (user_id,),
        ).fetchall()
        return [
            (
                row["id"],
                row["title"],
                row["description"],
                row["event_date"],
                row["event_time"],
            )
            for row in rows
        ]


def delete_event(user_id: int, event_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM schedule WHERE user_id = ? AND id = ?",
            (user_id, event_id),
        )
        return cursor.rowcount == 1
