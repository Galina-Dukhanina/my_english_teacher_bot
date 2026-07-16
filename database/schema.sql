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
    onboarding_step  TEXT DEFAULT 'start',
    pending_action   TEXT DEFAULT NULL,
    explanation_language TEXT DEFAULT 'auto',
    current_activity TEXT DEFAULT NULL,
    current_topic    TEXT DEFAULT NULL,
    last_menu_date   TEXT DEFAULT NULL,
    challenge_days   INTEGER DEFAULT NULL,
    challenge_start  TEXT DEFAULT NULL,
    level_test_at    TEXT DEFAULT NULL,
    created_at       TEXT DEFAULT (datetime('now'))
);

-- Активные дни в рамках вызова (без пропусков)
CREATE TABLE IF NOT EXISTS challenge_active_days (
    user_id      INTEGER NOT NULL,
    active_date  TEXT NOT NULL,
    PRIMARY KEY (user_id, active_date),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
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
    transcription  TEXT,
    example        TEXT,
    topic          TEXT,
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
    words_sessions_used INTEGER DEFAULT 0,
    grammar_exercises_used INTEGER DEFAULT 0,
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

-- История диалогов для контекста AI
CREATE TABLE IF NOT EXISTS conversations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER,
    role       TEXT,
    content    TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Активные сессии (карточки, упражнения) — JSON в payload
CREATE TABLE IF NOT EXISTS sessions (
    user_id    INTEGER NOT NULL,
    kind       TEXT NOT NULL,
    payload    TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, kind),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
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

-- === Premium learning (MVP) ===

CREATE TABLE IF NOT EXISTS learning_profiles (
    user_id             INTEGER PRIMARY KEY,
    cefr_level          TEXT,
    display_level       TEXT,
    goal                TEXT,
    exam_type           TEXT,
    exam_date           TEXT,
    exam_current_score  REAL,
    exam_target_score   REAL,
    weak_skill          TEXT,
    daily_minutes       INTEGER DEFAULT 15,
    interests_json      TEXT,
    profession          TEXT,
    ui_language         TEXT DEFAULT 'ru',
    premium_setup_done  INTEGER DEFAULT 0,
    updated_at          TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS skill_profiles (
    user_id       INTEGER PRIMARY KEY,
    grammar       TEXT,
    vocabulary    TEXT,
    reading       TEXT,
    listening     TEXT,
    writing       TEXT,
    speaking      TEXT,
    diagnostic_at TEXT,
    source        TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS curriculum_modules (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    goal          TEXT NOT NULL,
    cefr_level    TEXT NOT NULL,
    stage         INTEGER DEFAULT 1,
    week_number   INTEGER DEFAULT 1,
    sort_order    INTEGER DEFAULT 0,
    title         TEXT NOT NULL,
    outcome_ru    TEXT,
    core_ratio    REAL DEFAULT 0.7,
    target_ratio  REAL DEFAULT 0.3,
    is_active     INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS curriculum_lessons (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id         INTEGER NOT NULL,
    day_number        INTEGER NOT NULL,
    title             TEXT NOT NULL,
    estimated_minutes INTEGER DEFAULT 15,
    is_active         INTEGER DEFAULT 1,
    FOREIGN KEY (module_id) REFERENCES curriculum_modules(id)
);

CREATE TABLE IF NOT EXISTS lesson_steps (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id    INTEGER NOT NULL,
    sort_order   INTEGER NOT NULL,
    step_type    TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY (lesson_id) REFERENCES curriculum_lessons(id)
);

CREATE TABLE IF NOT EXISTS content_assets (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    slug             TEXT UNIQUE NOT NULL,
    kind             TEXT NOT NULL,
    path             TEXT,
    telegram_file_id TEXT,
    meta_json        TEXT,
    created_at       TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_module_progress (
    user_id          INTEGER NOT NULL,
    module_id        INTEGER NOT NULL,
    status           TEXT DEFAULT 'not_started',
    started_at       TEXT,
    completed_at     TEXT,
    week_check_score REAL,
    PRIMARY KEY (user_id, module_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (module_id) REFERENCES curriculum_modules(id)
);

CREATE TABLE IF NOT EXISTS user_lesson_progress (
    user_id           INTEGER NOT NULL,
    lesson_id         INTEGER NOT NULL,
    status            TEXT DEFAULT 'not_started',
    current_step_id   INTEGER,
    started_at        TEXT,
    completed_at      TEXT,
    score_summary_json TEXT,
    PRIMARY KEY (user_id, lesson_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (lesson_id) REFERENCES curriculum_lessons(id)
);

CREATE TABLE IF NOT EXISTS user_learning_items (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER NOT NULL,
    item_type        TEXT NOT NULL,
    ref_id           TEXT NOT NULL,
    content_json     TEXT,
    status           TEXT DEFAULT 'new',
    ease_factor      REAL DEFAULT 2.5,
    interval_days    INTEGER DEFAULT 1,
    next_review_at   TEXT,
    correct_streak   INTEGER DEFAULT 0,
    error_count      INTEGER DEFAULT 0,
    last_reviewed_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_learning_items_review
    ON user_learning_items(user_id, next_review_at);

CREATE TABLE IF NOT EXISTS exercise_attempts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL,
    lesson_id      INTEGER,
    lesson_step_id INTEGER,
    answer_text    TEXT,
    result_json    TEXT,
    score          REAL,
    created_at     TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS daily_phrases_log (
    user_id    INTEGER NOT NULL,
    phrase_date TEXT NOT NULL,
    phrase_id  TEXT NOT NULL,
    module_id  INTEGER,
    shown_at   TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, phrase_date),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);