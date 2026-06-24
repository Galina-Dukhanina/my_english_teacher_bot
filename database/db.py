import sqlite3
import os
from datetime import datetime

# Путь к файлу базы (ляжет в корень проекта)
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "bot_database.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_connection():
    """Открыть соединение с базой. row_factory позволяет обращаться к полям по имени."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Создать все таблицы из schema.sql (безопасно вызывать многократно)."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = f.read()
    conn = get_connection()
    conn.executescript(schema)
    conn.commit()
    conn.close()


# ---------- Пользователи ----------


def get_user(user_id):
    """Вернуть пользователя как словарь или None, если не найден."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(user_id, username, first_name):
    """Создать пользователя, если его ещё нет. Заодно создаёт запись прогресса."""
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
        (user_id, username, first_name),
    )
    conn.execute(
        "INSERT OR IGNORE INTO progress (user_id) VALUES (?)",
        (user_id,),
    )
    conn.commit()
    conn.close()


def update_user(user_id, **fields):
    """Обновить произвольные поля пользователя.
    Пример: update_user(123, level='beginner', style='simple')"""
    if not fields:
        return
    columns = ", ".join(f"{key} = ?" for key in fields)
    values = list(fields.values()) + [user_id]
    conn = get_connection()
    conn.execute(f"UPDATE users SET {columns} WHERE user_id = ?", values)
    conn.commit()
    conn.close()


# ---------- Аналитика ----------


def log_event(user_id, event_type):
    """Записать событие для аналитики (start, onboarding_done, dialog ...)."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO events (user_id, event_type) VALUES (?, ?)",
        (user_id, event_type),
    )
    conn.commit()
    conn.close()


# ---------- Обратная связь ----------


def save_feedback(user_id, message):
    """Сохранить отзыв пользователя."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO feedback (user_id, message) VALUES (?, ?)",
        (user_id, message),
    )
    conn.commit()
    conn.close()


# ---------- Состояние ожидания (для кнопок-инструментов) ----------


def set_pending_action(user_id, action):
    """Установить, что бот ждет от пользователя (или None — ничего не ждет)."""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET pending_action = ? WHERE user_id = ?",
        (action, user_id),
    )
    conn.commit()
    conn.close()


def get_pending_action(user_id):
    """Узнать, что бот сейчас ждет от пользователя."""
    conn = get_connection()
    row = conn.execute(
        "SELECT pending_action FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return row["pending_action"] if row else None


# ---------- Активность (режимы: поговорить / слова / грамматика) ----------


def set_activity(user_id, activity):
    """Установить активный режим (talk / words / grammar / None)."""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET current_activity = ? WHERE user_id = ?",
        (activity, user_id),
    )
    conn.commit()
    conn.close()


def get_activity(user_id):
    """Узнать текущий активный режим пользователя."""
    conn = get_connection()
    row = conn.execute(
        "SELECT current_activity FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return row["current_activity"] if row else None


def should_show_menu(user_id) -> bool:
    """Нужно ли показать меню при заходе.
    True, если сегодня меню еще не показывали (первое сообщение за день)."""
    from datetime import date

    today = date.today().isoformat()
    conn = get_connection()
    row = conn.execute(
        "SELECT last_menu_date FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        return False
    return row["last_menu_date"] != today


def mark_menu_shown(user_id):
    """Отметить, что меню показано сегодня (чтобы не показывать повторно за день)."""
    from datetime import date

    today = date.today().isoformat()
    conn = get_connection()
    conn.execute(
        "UPDATE users SET last_menu_date = ? WHERE user_id = ?",
        (today, user_id),
    )
    conn.commit()
    conn.close()


def set_topic(user_id, topic):
    """Установить тему разговора (или None)."""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET current_topic = ? WHERE user_id = ?", (topic, user_id)
    )
    conn.commit()
    conn.close()


# ---------- Карточки слов ----------


def add_words_batch(user_id, words, topic):
    """Сохранить набор слов в словарь.
    words — список словарей [{"word":..., "translation":..., "transcription":..., "example":...}]"""
    conn = get_connection()
    for w in words:
        conn.execute(
            """INSERT INTO vocabulary (user_id, word, translation, transcription, example, topic)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                w.get("word"),
                w.get("translation"),
                w.get("transcription"),
                w.get("example"),
                topic,
            ),
        )
    conn.commit()
    conn.close()


def get_recent_words(user_id, limit=10):
    """Получить последние добавленные слова пользователя (для текущей сессии)."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM vocabulary WHERE user_id = ?
           ORDER BY id DESC LIMIT ?""",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_word_result(word_id, knew_it):
    """Отметить результат по слову: знал (True) или нет (False).
    Увеличивает счетчик повторений, обновляет статус 'выучено'."""
    conn = get_connection()
    if knew_it:
        conn.execute(
            """UPDATE vocabulary
               SET times_reviewed = times_reviewed + 1,
                   mastered = CASE WHEN times_reviewed + 1 >= 3 THEN 1 ELSE 0 END
               WHERE id = ?""",
            (word_id,),
        )
    else:
        # Не знал — сбрасываем "выучено", счетчик не растим
        conn.execute(
            "UPDATE vocabulary SET mastered = 0 WHERE id = ?",
            (word_id,),
        )
    conn.commit()
    conn.close()


def get_vocab_stats(user_id):
    """Статистика словаря: сколько всего слов и сколько выучено."""
    conn = get_connection()
    row = conn.execute(
        """SELECT COUNT(*) as total,
                  SUM(CASE WHEN mastered = 1 THEN 1 ELSE 0 END) as learned
           FROM vocabulary WHERE user_id = ?""",
        (user_id,),
    ).fetchone()
    conn.close()
    return {"total": row["total"] or 0, "learned": row["learned"] or 0}
