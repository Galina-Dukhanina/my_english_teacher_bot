-- Пользователи и их профиль
CREATE TABLE IF NOT EXISTS users (
    user_id          INTEGER PRIMARY KEY,
    username         TEXT,
    first_name       TEXT,
    level            TEXT,
    goal             TEXT,
    style            TEXT DEFAULT 'friendly',
    daily_minutes    INTEGER DEFAULT 15,
    timezone         TEXT DEFAULT 'Europe/Moscow',
    reminder_enabled INTEGER DEFAULT 1,
    reminder_time    TEXT DEFAULT '19:00',
    is_premium       INTEGER DEFAULT 0,
    premium_until    TEXT,
    terms_accepted   INTEGER DEFAULT 0,
    terms_accepted_at TEXT,
    onboarding_done  INTEGER DEFAULT 0,
    created_at       TEXT DEFAULT (datetime('now'))
);

-- Прогресс и удержание (1:1 с users)
CREATE TABLE IF NOT EXISTS progress (
    user_id        INTEGER PRIMARY KEY,
    streak_days    INTEGER DEFAULT 0,
    last_active    TEXT,
    total_words    INTEGER DEFAULT 0,
    total_dialogs  INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Персональный словарь
CREATE TABLE IF NOT EXISTS vocabulary (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER,
    word           TEXT,
    translation    TEXT,
    example        TEXT,
    added_at       TEXT DEFAULT (datetime('now')),
    times_reviewed INTEGER DEFAULT 0,
    mastered       INTEGER DEFAULT 0,
    next_review    TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Дневные лимиты (для бесплатного тарифа)
CREATE TABLE IF NOT EXISTS usage_limits (
    user_id       INTEGER,
    date          TEXT,
    dialogs_used  INTEGER DEFAULT 0,
    messages_used INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, date),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Лог напоминаний (защита от повторной отправки)
CREATE TABLE IF NOT EXISTS reminders (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    sent_at TEXT DEFAULT (datetime('now')),
    opened  INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Обратная связь
CREATE TABLE IF NOT EXISTS feedback (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER,
    message    TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    status     TEXT DEFAULT 'new',
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Аналитика событий
CREATE TABLE IF NOT EXISTS events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER,
    event_type TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Учёт расходов на AI
CREATE TABLE IF NOT EXISTS ai_usage (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER,
    tokens_in     INTEGER,
    tokens_out    INTEGER,
    model         TEXT,
    cost_estimate REAL,
    created_at    TEXT DEFAULT (datetime('now'))
);

-- История платежей (задел под ЮKassa, работает и с заглушкой)
CREATE TABLE IF NOT EXISTS payments (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER,
    provider            TEXT,
    provider_payment_id TEXT,
    plan                TEXT,
    amount              REAL,
    currency            TEXT DEFAULT 'RUB',
    status              TEXT DEFAULT 'pending',
    created_at          TEXT DEFAULT (datetime('now')),
    paid_at             TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);