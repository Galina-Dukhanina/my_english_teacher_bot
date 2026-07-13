import sqlite3
import os
from datetime import datetime

# Путь к файлу базы (можно переопределить через DB_PATH в .env)
DB_PATH = os.getenv(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "bot_database.db"),
)
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_connection():
    """Открыть соединение с базой. row_factory позволяет обращаться к полям по имени."""
    db_dir = os.path.dirname(os.path.abspath(DB_PATH))
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Создать все таблицы из schema.sql (безопасно вызывать многократно)."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = f.read()
    conn = get_connection()
    conn.executescript(schema)
    conn.commit()
    conn.close()


def migrate_db():
    """Добавить недостающие колонки в существующие таблицы, не теряя данные.
    Безопасно вызывать при каждом запуске."""
    # Какие колонки должны быть в каждой таблице (имя: SQL-определение)
    expected_columns = {
        "users": {
            "username": "TEXT",
            "first_name": "TEXT",
            "level": "TEXT",
            "goal": "TEXT",
            "style": "TEXT DEFAULT 'friendly'",
            "daily_minutes": "INTEGER DEFAULT 15",
            "timezone": "TEXT DEFAULT 'Europe/Moscow'",
            "reminder_enabled": "INTEGER DEFAULT 1",
            "reminder_time": "TEXT DEFAULT '19:00'",
            "is_premium": "INTEGER DEFAULT 0",
            "premium_until": "TEXT",
            "terms_accepted": "INTEGER DEFAULT 0",
            "terms_accepted_at": "TEXT",
            "onboarding_done": "INTEGER DEFAULT 0",
            "onboarding_step": "TEXT DEFAULT 'start'",
            "pending_action": "TEXT",
            "explanation_language": "TEXT DEFAULT 'auto'",
            "current_activity": "TEXT",
            "current_topic": "TEXT",
            "last_menu_date": "TEXT",
            "challenge_days": "INTEGER",
            "challenge_start": "TEXT",
        },
        "vocabulary": {
            "transcription": "TEXT",
            "topic": "TEXT",
        },
        "usage_limits": {
            "words_sessions_used": "INTEGER DEFAULT 0",
            "grammar_exercises_used": "INTEGER DEFAULT 0",
        },
    }

    conn = get_connection()
    for table, columns in expected_columns.items():
        # Получаем список существующих колонок таблицы
        existing = conn.execute(f"PRAGMA table_info({table})").fetchall()
        existing_names = {row["name"] for row in existing}

        # Добавляем те, которых нет
        for col_name, col_def in columns.items():
            if col_name not in existing_names:
                try:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")
                    print(f"Миграция: добавлена колонка {table}.{col_name}")
                except Exception as e:
                    print(f"Миграция: не удалось добавить {table}.{col_name}: {e}")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            role       TEXT,
            content    TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_conversations_user "
        "ON conversations(user_id, id)"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            user_id    INTEGER NOT NULL,
            kind       TEXT NOT NULL,
            payload    TEXT NOT NULL,
            updated_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (user_id, kind),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS challenge_active_days (
            user_id      INTEGER NOT NULL,
            active_date  TEXT NOT NULL,
            PRIMARY KEY (user_id, active_date),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """
    )
    conn.commit()
    conn.close()


# ---------- История диалогов ----------


def get_conversation_history(user_id, limit=20):
    """Последние N сообщений диалога для AI (хронологический порядок)."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT role, content FROM conversations
           WHERE user_id = ?
           ORDER BY id DESC LIMIT ?""",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]


def add_conversation_message(user_id, role, content):
    """Добавить сообщение в историю диалога."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO conversations (user_id, role, content) VALUES (?, ?, ?)",
        (user_id, role, content),
    )
    conn.commit()
    conn.close()


def trim_conversation_history(user_id, max_messages):
    """Оставить только последние max_messages записей."""
    conn = get_connection()
    conn.execute(
        """DELETE FROM conversations
           WHERE user_id = ? AND id NOT IN (
               SELECT id FROM conversations
               WHERE user_id = ?
               ORDER BY id DESC LIMIT ?
           )""",
        (user_id, user_id, max_messages),
    )
    conn.commit()
    conn.close()


def clear_conversation_history(user_id):
    """Очистить историю диалога пользователя."""
    conn = get_connection()
    conn.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# ---------- Учёт расходов AI ----------


def get_today_ai_spend():
    """Сумма cost_estimate за сегодня (UTC-дата SQLite datetime('now'))."""
    conn = get_connection()
    row = conn.execute(
        """SELECT COALESCE(SUM(cost_estimate), 0) AS total
           FROM ai_usage
           WHERE date(created_at) = date('now')"""
    ).fetchone()
    conn.close()
    return float(row["total"] or 0)


def record_ai_usage(user_id, tokens_in, tokens_out, model, cost_estimate):
    """Записать один AI-запрос в ai_usage."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO ai_usage
           (user_id, tokens_in, tokens_out, model, cost_estimate)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, tokens_in, tokens_out, model, cost_estimate),
    )
    conn.commit()
    conn.close()


# ---------- Сессии (карточки, упражнения) ----------


def get_session_payload(user_id, kind):
    """Получить JSON-сессию или None."""
    import json

    conn = get_connection()
    row = conn.execute(
        "SELECT payload FROM sessions WHERE user_id = ? AND kind = ?",
        (user_id, kind),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return json.loads(row["payload"])


def save_session_payload(user_id, kind, payload: dict):
    """Сохранить или обновить сессию (payload — dict, хранится как JSON)."""
    import json

    conn = get_connection()
    conn.execute(
        """INSERT INTO sessions (user_id, kind, payload, updated_at)
           VALUES (?, ?, ?, datetime('now'))
           ON CONFLICT(user_id, kind) DO UPDATE SET
               payload = excluded.payload,
               updated_at = excluded.updated_at""",
        (user_id, kind, json.dumps(payload, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def delete_session(user_id, kind):
    """Удалить сессию пользователя."""
    conn = get_connection()
    conn.execute(
        "DELETE FROM sessions WHERE user_id = ? AND kind = ?",
        (user_id, kind),
    )
    conn.commit()
    conn.close()


# ---------- Прогресс и streak ----------


def get_progress(user_id):
    """Запись прогресса пользователя или None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM progress WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_progress(user_id, **fields):
    """Обновить поля progress. Создаёт запись, если её нет."""
    if not fields:
        return
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO progress (user_id) VALUES (?)", (user_id,))
    columns = ", ".join(f"{key} = ?" for key in fields)
    values = list(fields.values()) + [user_id]
    conn.execute(f"UPDATE progress SET {columns} WHERE user_id = ?", values)
    conn.commit()
    conn.close()


# ---------- Вызов на дни без пропусков ----------


def mark_challenge_active_day(user_id, active_date):
    """Отметить день как активный в вызове."""
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO challenge_active_days (user_id, active_date) VALUES (?, ?)",
        (user_id, active_date),
    )
    conn.commit()
    conn.close()


def count_challenge_active_days(user_id, start_date, end_date):
    """Число активных дней в периоде [start_date, end_date] включительно."""
    conn = get_connection()
    row = conn.execute(
        """SELECT COUNT(*) AS cnt FROM challenge_active_days
           WHERE user_id = ? AND active_date >= ? AND active_date <= ?""",
        (user_id, start_date, end_date),
    ).fetchone()
    conn.close()
    return row["cnt"] or 0


def sync_progress_words(user_id):
    """Синхронизировать total_words с количеством слов в vocabulary."""
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS cnt FROM vocabulary WHERE user_id = ?", (user_id,)
    ).fetchone()
    total = row["cnt"] or 0
    conn.execute("INSERT OR IGNORE INTO progress (user_id) VALUES (?)", (user_id,))
    conn.execute(
        "UPDATE progress SET total_words = ? WHERE user_id = ?",
        (total, user_id),
    )
    conn.commit()
    conn.close()


# ---------- Напоминания ----------


def get_users_for_reminders():
    """Пользователи с включёнными напоминаниями и завершённым онбордингом."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT user_id, timezone, reminder_time
           FROM users
           WHERE reminder_enabled = 1 AND onboarding_done = 1"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def reminder_sent_today(user_id, date_str):
    """True, если напоминание уже отправляли сегодня (date_str — YYYY-MM-DD)."""
    conn = get_connection()
    row = conn.execute(
        """SELECT COUNT(*) AS cnt FROM reminders
           WHERE user_id = ? AND date(sent_at) = ?""",
        (user_id, date_str),
    ).fetchone()
    conn.close()
    return (row["cnt"] or 0) > 0


def record_reminder_sent(user_id):
    """Записать факт отправки напоминания."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO reminders (user_id) VALUES (?)",
        (user_id,),
    )
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


# ---------- Аналитика (admin /stats) ----------


def count_users():
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()
    conn.close()
    return row["cnt"] or 0


def count_onboarded_users():
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS cnt FROM users WHERE onboarding_done = 1"
    ).fetchone()
    conn.close()
    return row["cnt"] or 0


def get_dau_last_days(days: int = 7):
    """DAU по дням: список (date, count) за последние N дней."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT date(created_at) AS day, COUNT(DISTINCT user_id) AS cnt
           FROM events
           WHERE created_at >= date('now', ?)
           GROUP BY day
           ORDER BY day""",
        (f"-{days - 1} days",),
    ).fetchall()
    conn.close()
    return [(row["day"], row["cnt"]) for row in rows]


def get_top_events(days: int = 7, limit: int = 10):
    conn = get_connection()
    rows = conn.execute(
        """SELECT event_type, COUNT(*) AS cnt
           FROM events
           WHERE created_at >= date('now', ?)
           GROUP BY event_type
           ORDER BY cnt DESC
           LIMIT ?""",
        (f"-{days - 1} days", limit),
    ).fetchall()
    conn.close()
    return [(row["event_type"], row["cnt"]) for row in rows]


def get_funnel_counts():
    """Уникальные пользователи по ключевым этапам воронки."""
    conn = get_connection()
    result = {}
    for event_type in ("start", "onboarding_done", "dialog"):
        row = conn.execute(
            """SELECT COUNT(DISTINCT user_id) AS cnt
               FROM events WHERE event_type = ?""",
            (event_type,),
        ).fetchone()
        result[event_type] = row["cnt"] or 0
    conn.close()
    return result


def count_new_feedback():
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS cnt FROM feedback WHERE status = 'new'"
    ).fetchone()
    conn.close()
    return row["cnt"] or 0


# ---------- Дневные лимиты ----------


def get_user_local_date(user_id) -> str:
    """Сегодняшняя дата в timezone пользователя (YYYY-MM-DD)."""
    import pytz
    from datetime import datetime

    user = get_user(user_id)
    tz_name = (user or {}).get("timezone") or "Europe/Moscow"
    tz = pytz.timezone(tz_name)
    return datetime.now(tz).date().isoformat()


def get_usage_limits(user_id, date_str):
    """Получить или создать запись лимитов на дату."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM usage_limits WHERE user_id = ? AND date = ?",
        (user_id, date_str),
    ).fetchone()
    if not row:
        conn.execute(
            "INSERT INTO usage_limits (user_id, date) VALUES (?, ?)",
            (user_id, date_str),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM usage_limits WHERE user_id = ? AND date = ?",
            (user_id, date_str),
        ).fetchone()
    conn.close()
    return dict(row)


def increment_usage(user_id, date_str, field: str, amount: int = 1):
    """Увеличить счётчик usage_limits (field — имя колонки)."""
    allowed = {
        "messages_used",
        "words_sessions_used",
        "grammar_exercises_used",
        "dialogs_used",
    }
    if field not in allowed:
        raise ValueError(f"Unknown usage field: {field}")
    get_usage_limits(user_id, date_str)
    conn = get_connection()
    conn.execute(
        f"UPDATE usage_limits SET {field} = {field} + ? "
        "WHERE user_id = ? AND date = ?",
        (amount, user_id, date_str),
    )
    conn.commit()
    conn.close()


# ---------- Платежи и premium ----------


def create_payment_record(user_id, provider, provider_payment_id, plan, amount):
    """Создать запись платежа со статусом pending."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO payments
           (user_id, provider, provider_payment_id, plan, amount, status)
           VALUES (?, ?, ?, ?, ?, 'pending')""",
        (user_id, provider, provider_payment_id, plan, amount),
    )
    conn.commit()
    conn.close()


def update_payment_status(provider_payment_id, status, paid_at=None):
    conn = get_connection()
    if paid_at:
        conn.execute(
            """UPDATE payments SET status = ?, paid_at = ?
               WHERE provider_payment_id = ?""",
            (status, paid_at, provider_payment_id),
        )
    else:
        conn.execute(
            "UPDATE payments SET status = ? WHERE provider_payment_id = ?",
            (status, provider_payment_id),
        )
    conn.commit()
    conn.close()


def get_payment_by_provider_id(provider_payment_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM payments WHERE provider_payment_id = ?",
        (provider_payment_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def activate_premium(user_id, days: int):
    """Активировать premium на N дней."""
    from datetime import datetime, timedelta

    until = (datetime.now() + timedelta(days=days)).isoformat(timespec="seconds")
    update_user(user_id, is_premium=1, premium_until=until)


def expire_premium_users() -> list[int]:
    """Снять premium у пользователей с истёкшим сроком. Возвращает их user_id."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT user_id FROM users
           WHERE is_premium = 1
             AND premium_until IS NOT NULL
             AND premium_until < datetime('now')"""
    ).fetchall()
    user_ids = [row["user_id"] for row in rows]
    if user_ids:
        conn.execute(
            """UPDATE users SET is_premium = 0
               WHERE is_premium = 1
                 AND premium_until IS NOT NULL
                 AND premium_until < datetime('now')"""
        )
    conn.commit()
    conn.close()
    return user_ids


def count_premium_users():
    conn = get_connection()
    row = conn.execute(
        """SELECT COUNT(*) AS cnt FROM users
           WHERE is_premium = 1
             AND (premium_until IS NULL OR premium_until >= datetime('now'))"""
    ).fetchone()
    conn.close()
    return row["cnt"] or 0


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


# ---------- Повторение слов ----------


def get_words_to_review(user_id, limit=10):
    """Получить неосвоенные слова для повторения (mastered=0).
    Сначала те, что давно не повторяли."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM vocabulary
           WHERE user_id = ? AND mastered = 0
           ORDER BY times_reviewed ASC, id ASC
           LIMIT ?""",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def review_word_result(word_id, knew_it):
    """Отметить результат повторения слова.
    Знал — растим счетчик, после 3 раз слово освоено.
    Не знал — сбрасываем счетчик."""
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
        conn.execute(
            "UPDATE vocabulary SET times_reviewed = 0, mastered = 0 WHERE id = ?",
            (word_id,),
        )
    conn.commit()
    conn.close()


def count_words_to_review(user_id):
    """Сколько неосвоенных слов ждет повторения."""
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM vocabulary WHERE user_id = ? AND mastered = 0",
        (user_id,),
    ).fetchone()
    conn.close()
    return row["cnt"] or 0


def get_all_words(user_id):
    """Все слова пользователя для просмотра словаря."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT word, translation, transcription, mastered, times_reviewed
           FROM vocabulary WHERE user_id = ?
           ORDER BY mastered ASC, id DESC""",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
