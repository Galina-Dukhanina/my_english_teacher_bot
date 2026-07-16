"""UI string catalog: ru (default) and en."""

from __future__ import annotations

CATALOG: dict[str, dict] = {
    # --- Common ---
    "ONBOARDING_REQUIRED": {
        "ru": "Сначала пройди онбординг: /start",
        "en": "Please complete onboarding first: /start",
    },
    "CHOOSE_OPTION": {
        "ru": "Выбери:",
        "en": "Choose:",
    },
    "KEYBOARD_UPDATED": {
        "ru": "Готово — клавиатура обновлена.",
        "en": "Done — keyboard updated.",
    },
    "EMPTY_MESSAGE": {
        "ru": "Напиши мне что-нибудь текстом, и я отвечу.",
        "en": "Send me a text message and I'll reply.",
    },
    "ONBOARDING_START": {
        "ru": "Давай сначала настроим все под тебя. Нажми /start",
        "en": "Let's set things up first. Tap /start",
    },
    "UI_LANG_NAME_RU": {"ru": "Русский", "en": "Russian"},
    "UI_LANG_NAME_EN": {"ru": "Английский", "en": "English"},
    "UI_LANG_CHANGED": {
        "ru": "Готово! Язык интерфейса: {lang}",
        "en": "Done! Interface language: {lang}",
    },
    "ASK_UI_LANG": {
        "ru": "На каком языке показывать меню и кнопки?\n\nСейчас: {current}",
        "en": "Which language for menus and buttons?\n\nCurrent: {current}",
    },
    # --- Main keyboard & menu ---
    "BTN_MENU": {"ru": "Чем займемся?", "en": "What shall we do?"},
    "BTN_PRONOUNCE": {"ru": "Как читается", "en": "How to pronounce"},
    "BTN_MEANING": {"ru": "Непонятно слово", "en": "Unknown word"},
    "BTN_LANG": {"ru": "Язык правил", "en": "Rule language"},
    "BTN_MAIN": {"ru": "Главное меню", "en": "Main menu"},
    "MAIN_MENU": {"ru": "Выбери команду:", "en": "Choose a command:"},
    "MAIN_MENU_ITEMS": {
        "ru": {
            "settings": "Настройки",
            "reminders": "Напоминания",
            "progress": "Прогресс",
            "premium": "Premium",
            "feedback": "Отзыв",
            "help": "Справка",
        },
        "en": {
            "settings": "Settings",
            "reminders": "Reminders",
            "progress": "Progress",
            "premium": "Premium",
            "feedback": "Feedback",
            "help": "Help",
        },
    },
    "HELP": {
        "ru": (
            "Вот что я умею.\n\n"
            "Просто пиши мне по-английски — я отвечу, поддержу разговор "
            "и мягко поправлю ошибки. Можно спросить, как сказать что-то, "
            "попросить объяснить правило или начать диалог на любую тему.\n\n"
            "Команды:\n"
            "/settings — настройки\n"
            "/reminders — настроить напоминания о занятиях\n"
            "/progress — прогресс и серия дней\n"
            "/premium — Premium, в разработке\n"
            "/feedback — оставить отзыв или предложение\n"
            "/help — это сообщение"
        ),
        "en": (
            "Here's what I can do.\n\n"
            "Just write to me in English — I'll reply, keep the conversation going, "
            "and gently correct mistakes. Ask how to say something, request a grammar "
            "explanation, or start a chat on any topic.\n\n"
            "Commands:\n"
            "/settings — settings\n"
            "/reminders — practice reminders\n"
            "/progress — progress and streak\n"
            "/premium — Premium (in development)\n"
            "/feedback — send feedback or suggestions\n"
            "/help — this message"
        ),
    },
    "HELP_SALES": {
        "ru": (
            "Вот что я умею.\n\n"
            "Просто пиши мне по-английски — я отвечу, поддержу разговор "
            "и мягко поправлю ошибки.\n\n"
            "Команды:\n"
            "/settings — настройки\n"
            "/reminders — напоминания\n"
            "/progress — прогресс\n"
            "/premium — Premium: план обучения и оплата\n"
            "/feedback — отзыв\n"
            "/help — это сообщение"
        ),
        "en": (
            "Here's what I can do.\n\n"
            "Write to me in English — I'll reply and gently correct mistakes.\n\n"
            "Commands:\n"
            "/settings — settings\n"
            "/reminders — reminders\n"
            "/progress — progress\n"
            "/premium — Premium: learning plan and payment\n"
            "/feedback — feedback\n"
            "/help — this message"
        ),
    },
    # --- Settings ---
    "SETTINGS_MENU": {
        "ru": "Что хочешь изменить?",
        "en": "What would you like to change?",
    },
    "BTN_SETTINGS_UI_LANG": {
        "ru": "Язык интерфейса",
        "en": "Interface language",
    },
    "BTN_SETTINGS_LANG": {
        "ru": "Язык правил",
        "en": "Rule language",
    },
    "BTN_SETTINGS_LEVEL": {
        "ru": "Уровень английского",
        "en": "English level",
    },
    "BTN_SETTINGS_GOAL": {
        "ru": "Цель обучения",
        "en": "Learning goal",
    },
    "BTN_SETTINGS_TIMEZONE": {
        "ru": "Часовой пояс",
        "en": "Time zone",
    },
    "BTN_SETTINGS_REMINDERS": {
        "ru": "Напоминания",
        "en": "Reminders",
    },
    "BTN_SETTINGS_CHALLENGE": {
        "ru": "Вызов на дни",
        "en": "Day challenge",
    },
    "BTN_SETTINGS_BACK": {"ru": "« Назад", "en": "« Back"},
    "SETTINGS_SAVED": {
        "ru": "Готово! Выбрано: {setting}",
        "en": "Done! Selected: {setting}",
    },
    "SETTINGS_MORE": {
        "ru": "\n\n/settings — изменить ещё что-то",
        "en": "\n\n/settings — change something else",
    },
    "ASK_LEVEL": {
        "ru": "Какой у тебя уровень английского?",
        "en": "What's your English level?",
    },
    "ASK_GOAL": {
        "ru": "Для чего тебе английский в первую очередь?",
        "en": "What do you need English for most?",
    },
    "ASK_TIMEZONE": {
        "ru": "В каком часовом поясе ты находишься? Выбери свой город.",
        "en": "What's your time zone? Choose your city.",
    },
    "ASK_CHALLENGE": {
        "ru": (
            "🎯 На сколько дней без пропусков выбираешь вызов?\n\n"
            "Я буду считать активные дни в этом периоде. "
            "Пропуск не обнуляет прогресс — просто покажу, сколько дней осталось."
        ),
        "en": (
            "🎯 How many days in a row for your challenge?\n\n"
            "I'll count active days in this period. "
            "A missed day won't reset progress — I'll show how many days are left."
        ),
    },
    "BTN_LEVELS": {
        "ru": {
            "beginner": "Начинающий",
            "intermediate": "Средний",
            "advanced": "Продвинутый",
            "unknown": "Не знаю — пройти тест",
        },
        "en": {
            "beginner": "Beginner",
            "intermediate": "Intermediate",
            "advanced": "Advanced",
            "unknown": "Not sure — take a test",
        },
    },
    "BTN_GOALS": {
        "ru": {
            "work": "Работа",
            "travel": "Путешествия",
            "exams": "Экзамены",
            "speaking": "Разговор",
            "self": "Для себя",
        },
        "en": {
            "work": "Work",
            "travel": "Travel",
            "exams": "Exams",
            "speaking": "Speaking",
            "self": "For myself",
        },
    },
    "BTN_CHALLENGE_DAYS": {
        "ru": {"5": "5 дней", "7": "7 дней", "14": "14 дней", "30": "30 дней"},
        "en": {"5": "5 days", "7": "7 days", "14": "14 days", "30": "30 days"},
    },
    "BTN_TIMEZONES": {
        "ru": {
            "Europe/Kaliningrad": "UTC+2 — Калининград",
            "Europe/Moscow": "UTC+3 — Москва, Санкт-Петербург",
            "Europe/Samara": "UTC+4 — Самара, Ижевск",
            "Asia/Yekaterinburg": "UTC+5 — Екатеринбург, Пермь",
            "Asia/Omsk": "UTC+6 — Омск",
            "Asia/Novosibirsk": "UTC+7 — Новосибирск, Красноярск",
            "Asia/Irkutsk": "UTC+8 — Иркутск",
            "Asia/Yakutsk": "UTC+9 — Якутск",
            "Asia/Vladivostok": "UTC+10 — Владивосток",
            "Asia/Magadan": "UTC+11 — Магадан, Сахалин",
            "Asia/Kamchatka": "UTC+12 — Камчатка",
        },
        "en": {
            "Europe/Kaliningrad": "UTC+2 — Kaliningrad",
            "Europe/Moscow": "UTC+3 — Moscow, St. Petersburg",
            "Europe/Samara": "UTC+4 — Samara, Izhevsk",
            "Asia/Yekaterinburg": "UTC+5 — Yekaterinburg, Perm",
            "Asia/Omsk": "UTC+6 — Omsk",
            "Asia/Novosibirsk": "UTC+7 — Novosibirsk, Krasnoyarsk",
            "Asia/Irkutsk": "UTC+8 — Irkutsk",
            "Asia/Yakutsk": "UTC+9 — Yakutsk",
            "Asia/Vladivostok": "UTC+10 — Vladivostok",
            "Asia/Magadan": "UTC+11 — Magadan, Sakhalin",
            "Asia/Kamchatka": "UTC+12 — Kamchatka",
        },
    },
    "ASK_LANG": {
        "ru": "На каком языке объяснять правила и грамматику?\n\nСейчас стоит: {current}",
        "en": "Which language for grammar explanations?\n\nCurrent: {current}",
    },
    "BTN_LANGS": {
        "ru": {
            "auto": "Автоматически (по уровню)",
            "ru": "Русский",
            "en": "Английский",
            "both": "Оба языка",
        },
        "en": {
            "auto": "Automatic (by level)",
            "ru": "Russian",
            "en": "English",
            "both": "Both languages",
        },
    },
    "LANG_NAMES": {
        "ru": {
            "auto": "автоматически по уровню",
            "ru": "русский",
            "en": "английский",
            "both": "оба языка",
        },
        "en": {
            "auto": "automatic by level",
            "ru": "Russian",
            "en": "English",
            "both": "both languages",
        },
    },
    "LANG_CHANGED": {
        "ru": "Готово! Теперь правила объясняю: {lang}",
        "en": "Done! Grammar explanations: {lang}",
    },
    "ASK_WORD_PRONOUNCE": {
        "ru": "Какое слово или фразу озвучить? Напиши, и я покажу, как это читается.",
        "en": "Which word or phrase should I pronounce? Type it and I'll show you how it sounds.",
    },
    "ASK_WORD_MEANING": {
        "ru": "Какое слово непонятно? Напиши его, и я объясню, что оно значит.",
        "en": "Which word is unclear? Type it and I'll explain what it means.",
    },
    # --- Activities ---
    "ACTIVITY_MENU": {"ru": "Чем займемся?", "en": "What shall we do?"},
    "ACTIVITY_CHOOSE": {"ru": "Выбери режим:", "en": "Choose a mode:"},
    "BTN_ACTIVITIES": {
        "ru": {
            "talk": "Поговорить",
            "words": "Учить слова",
            "review": "Повторить слова",
            "grammar": "Грамматика",
        },
        "en": {
            "talk": "Chat",
            "words": "Learn words",
            "review": "Review words",
            "grammar": "Grammar",
        },
    },
    # --- Progress & limits ---
    "CHALLENGE_NONE": {
        "ru": "🎯 Вызов не выбран — выбери в /settings или ниже.",
        "en": "🎯 No challenge selected — pick one in /settings or below.",
    },
    "CHALLENGE_UPDATING": {
        "ru": "🎯 Вызов: данные обновляются...",
        "en": "🎯 Challenge: updating...",
    },
    "PROGRESS": {
        "ru": (
            "{streak_block}\n"
            "📚 Новых слов: {new_words} | Освоено: {mastered_words} | "
            "На повторении: {to_review}\n"
            "\n{limits_block}"
        ),
        "en": (
            "{streak_block}\n"
            "📚 New words: {new_words} | Mastered: {mastered_words} | "
            "To review: {to_review}\n"
            "\n{limits_block}"
        ),
    },
    "PROGRESS_LIMITS_HEADER": {
        "ru": "📊 Лимиты на сегодня:",
        "en": "📊 Today's limits:",
    },
    "PROGRESS_LIMIT_MESSAGES": {
        "ru": "💬 Диалог с ботом: {used} из {limit}",
        "en": "💬 Chat with bot: {used} of {limit}",
    },
    "PROGRESS_LIMIT_WORDS": {
        "ru": "📇 «Учить слова»: {used} из {limit}",
        "en": "📇 «Learn words»: {used} of {limit}",
    },
    "PROGRESS_LIMIT_GRAMMAR": {
        "ru": "📝 Упражнения по грамматике: {used} из {limit}",
        "en": "📝 Grammar exercises: {used} of {limit}",
    },
    "PROGRESS_LIMITS_FOOTNOTE": {
        "ru": (
            "«Диалог с ботом» — свободные сообщения в чат, «Поговорить», "
            "«Как читается» и «Непонятно слово».\n"
            "«Повторить слова» — без лимита."
        ),
        "en": (
            "«Chat with bot» — free messages, «Chat», "
            "«How to pronounce» and «Unknown word».\n"
            "«Review words» — unlimited."
        ),
    },
    "PROGRESS_LIMITS_SEPARATOR": {"ru": "───────────────", "en": "───────────────"},
    "PROGRESS_LIMITS_PREMIUM": {
        "ru": "💎 Premium — дневные лимиты не действуют.",
        "en": "💎 Premium — no daily limits.",
    },
    "LIMIT_MESSAGES": {
        "ru": (
            "На сегодня лимит сообщений исчерпан ({used}/{limit}). "
            "Завтра счётчик обновится."
        ),
        "en": (
            "Daily message limit reached ({used}/{limit}). "
            "Counter resets tomorrow."
        ),
    },
    "LIMIT_WORDS": {
        "ru": (
            "Бесплатно доступна 1 сессия «Учить слова» в день ({used}/{limit}). "
            "Завтра можно снова."
        ),
        "en": (
            "Free plan: 1 «Learn words» session per day ({used}/{limit}). "
            "Try again tomorrow."
        ),
    },
    "LIMIT_GRAMMAR": {
        "ru": (
            "Бесплатно доступен 1 блок упражнений в день ({used}/{limit}). "
            "Завтра можно снова."
        ),
        "en": (
            "Free plan: 1 grammar exercise block per day ({used}/{limit}). "
            "Try again tomorrow."
        ),
    },
    "LIMIT_GENERIC": {
        "ru": "Дневной лимит исчерпан ({used}/{limit}). Завтра счётчик обновится.",
        "en": "Daily limit reached ({used}/{limit}). Counter resets tomorrow.",
    },
    # --- Premium progress ---
    "PREMIUM_PROGRESS_HEADER": {
        "ru": "⭐ Premium-программа",
        "en": "⭐ Premium program",
    },
    "PREMIUM_PROGRESS_SETUP": {
        "ru": (
            "⭐ Premium активен, но программа ещё не настроена.\n"
            "Настрой профиль: /premium"
        ),
        "en": (
            "⭐ Premium is active, but the program isn't set up yet.\n"
            "Set up your profile: /premium"
        ),
    },
    "PREMIUM_PROGRESS_PROGRAM": {
        "ru": "🎯 {goal} · {level} · {minutes} мин/день",
        "en": "🎯 {goal} · {level} · {minutes} min/day",
    },
    "PREMIUM_PROGRESS_MODULE": {
        "ru": (
            "📘 {module}\n"
            "   Уроки: {completed}/{total} · {status}"
        ),
        "en": (
            "📘 {module}\n"
            "   Lessons: {completed}/{total} · {status}"
        ),
    },
    "PREMIUM_PROGRESS_CURRENT_LESSON": {
        "ru": "   ▶️ Сейчас: {lesson}",
        "en": "   ▶️ Now: {lesson}",
    },
    "PREMIUM_PROGRESS_SKILLS": {
        "ru": "📊 Навыки:\n{profile}",
        "en": "📊 Skills:\n{profile}",
    },
    "PREMIUM_PROGRESS_NO_DIAG": {
        "ru": "📊 Диагностика не пройдена — /premium",
        "en": "📊 Diagnostic not completed — /premium",
    },
    "PREMIUM_PROGRESS_SRS": {
        "ru": (
            "🔄 Фразы SRS: на повторении {due} · "
            "в работе {learning} · освоено {mastered}"
        ),
        "en": (
            "🔄 SRS phrases: due {due} · "
            "learning {learning} · mastered {mastered}"
        ),
    },
    "PREMIUM_PROGRESS_SCORES": {
        "ru": (
            "✏️ Уроки: MCQ {ex_correct}/{ex_total} · "
            "Writing {apply_passed}/{apply_total}"
        ),
        "en": (
            "✏️ Lessons: MCQ {ex_correct}/{ex_total} · "
            "Writing {apply_passed}/{apply_total}"
        ),
    },
    "PREMIUM_PROGRESS_WEAK_SKILL": {
        "ru": "⚠️ Фокус: {skill}",
        "en": "⚠️ Focus: {skill}",
    },
    "PREMIUM_MODULE_STATUS": {
        "ru": {
            "not_started": "не начат",
            "in_progress": "в процессе",
            "completed": "завершён",
        },
        "en": {
            "not_started": "not started",
            "in_progress": "in progress",
            "completed": "completed",
        },
    },
    # --- Premium gate & sales ---
    "PREMIUM_UPSELL": {
        "ru": (
            "⭐ Premium скоро — персональный план под твою цель и больше практики. "
            "Подробнее: /premium"
        ),
        "en": (
            "⭐ Premium coming soon — a personal plan for your goal and more practice. "
            "Details: /premium"
        ),
    },
    "PREMIUM_UPSELL_SALES": {
        "ru": (
            "⭐ Premium — персональный план обучения, уроки под цель и без дневных лимитов. "
            "Подробнее: /premium"
        ),
        "en": (
            "⭐ Premium — personal learning plan, goal-based lessons, no daily limits. "
            "Details: /premium"
        ),
    },
    "PREMIUM_SETUP_REQUIRED_SHORT": {
        "ru": "Сначала настрой программу: /premium",
        "en": "Set up your program first: /premium",
    },
    "PREMIUM_PROGRAM_ONLY": {
        "ru": "Уроки Premium доступны после активации подписки. /premium",
        "en": "Premium lessons require an active subscription. /premium",
    },
    "PREMIUM_PROGRAM_ONLY_SALES": {
        "ru": "Ежедневные уроки — в Premium. Оформи подписку: /premium",
        "en": "Daily lessons are in Premium. Subscribe: /premium",
    },
    "PREMIUM_WORD_HINT": {
        "ru": (
            "📚 Сохранение слов в словарь — функция Premium. "
            "Подробнее: /premium"
        ),
        "en": (
            "📚 Saving words to your vocabulary is a Premium feature. "
            "Details: /premium"
        ),
    },
    "PREMIUM_WORD_HINT_SALES": {
        "ru": (
            "📚 Сохранение слов в словарь доступно в Premium. "
            "Оформи подписку: /premium"
        ),
        "en": (
            "📚 Saving words is available in Premium. "
            "Subscribe: /premium"
        ),
    },
    "ADDWORD_PREMIUM_ONLY": {
        "ru": "Команда /addword доступна в Premium.\nПодробнее: /premium",
        "en": "/addword is available in Premium.\nDetails: /premium",
    },
    "ADDWORD_PREMIUM_ONLY_SALES": {
        "ru": "Команда /addword — только для Premium.\nОформи подписку: /premium",
        "en": "/addword is Premium only.\nSubscribe: /premium",
    },
    "PREMIUM_COMING_SOON": {
        "ru": (
            "⭐ Premium — скоро\n\n"
            "Сейчас бот бесплатный: диалог, слова, грамматика и все инструменты — "
            "в рамках дневных лимитов. Темы и задания можно выбирать свободно.\n\n"
            "Premium в разработке. Главное — не «просто больше запросов», "
            "а продуманное обучение:\n\n"
            "• План под твою цель (работа, экзамены, путешествия…)\n"
            "• Задания связаны с целью — понятная траектория, а не случайные темы\n"
            "• Подготовка к экзаменам и структура для роста уровня\n"
            "• Расширенные лимиты на практику с AI\n\n"
            "Оплата пока недоступна — сообщим, когда запустим.\n"
            "Хочешь узнать первым или предложить идею: /feedback"
        ),
        "en": (
            "⭐ Premium — coming soon\n\n"
            "The bot is free now: chat, words, grammar and all tools — "
            "within daily limits. You can pick topics freely.\n\n"
            "Premium is in development. It's not just «more requests» — "
            "it's structured learning:\n\n"
            "• A plan for your goal (work, exams, travel…)\n"
            "• Goal-linked tasks — a clear path, not random topics\n"
            "• Exam prep and a path to level up\n"
            "• Higher limits for AI practice\n\n"
            "Payment isn't available yet — we'll let you know when we launch.\n"
            "Want early access or have ideas: /feedback"
        ),
    },
    "PREMIUM_INTRO": {
        "ru": (
            "⭐ Premium\n\n"
            "• Персональный план обучения под твою цель\n"
            "• Задания связаны с целью — не случайные темы\n"
            "• Подготовка к экзаменам и траектория роста уровня\n"
            "• Расширенные лимиты на диалог, слова и грамматику\n"
            "• Словарь: слова из чата и /addword\n\n"
            "Выбери тариф:"
        ),
        "en": (
            "⭐ Premium\n\n"
            "• Personal learning plan for your goal\n"
            "• Goal-linked tasks — not random topics\n"
            "• Exam prep and a path to level up\n"
            "• Higher limits for chat, words and grammar\n"
            "• Vocabulary: words from chat and /addword\n\n"
            "Choose a plan:"
        ),
    },
    "PREMIUM_BTN_MONTH": {"ru": "Месяц — {price} ₽", "en": "Month — {price} ₽"},
    "PREMIUM_BTN_YEAR": {"ru": "Год — {price} ₽", "en": "Year — {price} ₽"},
    "PREMIUM_BTN_PAY": {"ru": "💳 Оплатить", "en": "💳 Pay"},
    "PREMIUM_PAY_LINK": {
        "ru": "Оплата {plan} — {amount} ₽.\nНажми кнопку ниже:",
        "en": "Payment {plan} — {amount} ₽.\nTap the button below:",
    },
    "PREMIUM_PAY_ERROR": {
        "ru": "Не удалось создать платёж. Попробуй позже или напиши /feedback.",
        "en": "Couldn't create payment. Try later or send /feedback.",
    },
    "PREMIUM_ALREADY": {
        "ru": "Premium уже активен.",
        "en": "Premium is already active.",
    },
    "PREMIUM_ACTIVATED_USER": {
        "ru": (
            "🎉 Premium активирован на {days} дней!\n\n"
            "Следующий шаг — настроить персональную программу. "
            "Нажми кнопку ниже или открой /premium"
        ),
        "en": (
            "🎉 Premium activated for {days} days!\n\n"
            "Next step — set up your personal program. "
            "Tap the button below or open /premium"
        ),
    },
    "PREMIUM_ACTIVE": {
        "ru": "У тебя активен Premium до {until}.",
        "en": "Premium is active until {until}.",
    },
    "PREMIUM_ACTIVE_SETUP": {
        "ru": (
            "⭐ Premium до {until}\n\n"
            "Чтобы начать персональную программу, настрой профиль — "
            "это займёт пару минут."
        ),
        "en": (
            "⭐ Premium until {until}\n\n"
            "To start your personal program, set up your profile — "
            "it takes a couple of minutes."
        ),
    },
    "PREMIUM_ACTIVE_READY": {
        "ru": (
            "⭐ Premium до {until}\n\n"
            "Программа настроена. Начни урок дня или посмотри фразу дня."
        ),
        "en": (
            "⭐ Premium until {until}\n\n"
            "Program is set up. Start today's lesson or view the phrase of the day."
        ),
    },
    "PREMIUM_ACTIVE_NEED_DIAG": {
        "ru": (
            "⭐ Premium до {until}\n\n"
            "Профиль настроен. Осталось пройти короткую диагностику навыков (~5 мин)."
        ),
        "en": (
            "⭐ Premium until {until}\n\n"
            "Profile is set up. Complete a short skills diagnostic (~5 min)."
        ),
    },
    "PREMIUM_UNLIMITED": {"ru": "без срока", "en": "no expiry"},
    "PREMIUM_UPSELL_BTN": {"ru": "⭐ Premium (скоро)", "en": "⭐ Premium (soon)"},
    "PREMIUM_UPSELL_BTN_SALES": {"ru": "⭐ Premium", "en": "⭐ Premium"},
    # --- Daily phrase ---
    "BTN_DAILY_PHRASE": {"ru": "💬 Фраза дня", "en": "💬 Phrase of the day"},
    "DAILY_PHRASE_UNAVAILABLE": {
        "ru": "Фраза дня доступна после настройки Premium-программы. /premium",
        "en": "Phrase of the day is available after Premium setup. /premium",
    },
    # --- Lessons ---
    "BTN_LESSON_START": {"ru": "📖 Урок дня", "en": "📖 Today's lesson"},
    "BTN_LESSON_RESUME": {"ru": "▶️ Продолжить урок", "en": "▶️ Resume lesson"},
    "BTN_LESSON_CONTINUE": {"ru": "Дальше →", "en": "Next →"},
    "BTN_LESSON_STOP": {"ru": "Остановить урок", "en": "Stop lesson"},
    "LESSON_HEADER": {
        "ru": "📘 {module}\n{lesson} · день {day}",
        "en": "📘 {module}\n{lesson} · day {day}",
    },
    "LESSON_STARTED": {
        "ru": "Урок начался. Один шаг за раз — нажимай «Дальше» или отвечай на задание.",
        "en": "Lesson started. One step at a time — tap «Next» or answer the task.",
    },
    "LESSON_RESUMED": {
        "ru": "Продолжаем урок с того места, где остановились.",
        "en": "Resuming the lesson where you left off.",
    },
    "LESSON_NONE": {
        "ru": "Сейчас нет доступного урока. Модуль завершён или контент ещё не добавлен.",
        "en": "No lesson available now. Module completed or content not added yet.",
    },
    "LESSON_EXPIRED": {
        "ru": "Урок прервался. Начни заново: /premium",
        "en": "Lesson interrupted. Start again: /premium",
    },
    "LESSON_STOPPED": {
        "ru": "Урок остановлен. Продолжить: /premium → «Урок дня».",
        "en": "Lesson stopped. Continue: /premium → «Today's lesson».",
    },
    "LESSON_COMPLETE": {
        "ru": (
            "✅ Урок завершён!\n"
            "Упражнения: {correct} из {total} верно.\n"
            "Writing: {apply_passed} из {apply_total} зачтено.\n\n"
            "Следующий урок — завтра или позже из /premium."
        ),
        "en": (
            "✅ Lesson complete!\n"
            "Exercises: {correct} of {total} correct.\n"
            "Writing: {apply_passed} of {apply_total} passed.\n\n"
            "Next lesson — tomorrow or later from /premium."
        ),
    },
    "LESSON_STEP_REVIEW": {
        "ru": (
            "🔄 Повторение ({current} из {total})\n\n"
            "Как будет по-английски?\n\n{phrase_ru}"
        ),
        "en": (
            "🔄 Review ({current} of {total})\n\n"
            "How do you say it in English?\n\n{phrase_ru}"
        ),
    },
    "LESSON_REVIEW_HINT": {"ru": "💡 {phrase_en}", "en": "💡 {phrase_en}"},
    "LESSON_REVIEW_CORRECT": {
        "ru": "✅ Отлично! Следующая фраза…",
        "en": "✅ Great! Next phrase…",
    },
    "LESSON_REVIEW_WRONG": {
        "ru": "❌ Правильно:\n\n{phrase_en}",
        "en": "❌ Correct:\n\n{phrase_en}",
    },
    "LESSON_REVIEW_DONE": {
        "ru": "🔄 Повторение завершено. Переходим к уроку.",
        "en": "🔄 Review complete. Moving to the lesson.",
    },
    "BTN_LESSON_REVIEW_KNEW": {"ru": "✅ Помню", "en": "✅ I remember"},
    "BTN_LESSON_REVIEW_HINT": {"ru": "💡 Подсказка", "en": "💡 Hint"},
    "BTN_LESSON_REVIEW_FORGOT": {"ru": "❌ Не помню", "en": "❌ Don't remember"},
    "BTN_LESSON_REVIEW_NEXT": {"ru": "Дальше →", "en": "Next →"},
    "LESSON_STEP_PHRASE": {
        "ru": "💬 Фраза дня\n\n{phrase_en}\n\n{phrase_ru}",
        "en": "💬 Phrase of the day\n\n{phrase_en}\n\n{phrase_ru}",
    },
    "LESSON_STEP_EXPLAIN": {
        "ru": "📖 {title}\n\n{body}",
        "en": "📖 {title}\n\n{body}",
    },
    "LESSON_STEP_EXERCISE": {
        "ru": "✏️ {question}",
        "en": "✏️ {question}",
    },
    "LESSON_STEP_APPLY": {"ru": "✍️ {prompt}", "en": "✍️ {prompt}"},
    "LESSON_STEP_APPLY_DEFAULT": {
        "ru": "Напиши ответ на английском (1–2 предложения).",
        "en": "Write your answer in English (1–2 sentences).",
    },
    "LESSON_STEP_UNKNOWN": {
        "ru": "Шаг урока.",
        "en": "Lesson step.",
    },
    "LESSON_EXERCISE_CORRECT": {"ru": "✅ Верно!", "en": "✅ Correct!"},
    "LESSON_EXERCISE_WRONG": {
        "ru": "❌ Правильный ответ: {answer}",
        "en": "❌ Correct answer: {answer}",
    },
    "LESSON_YOUR_ANSWER": {
        "ru": "Твой ответ: {answer}",
        "en": "Your answer: {answer}",
    },
    "LESSON_APPLY_TOO_SHORT": {
        "ru": "Маловато — нужно минимум {min_words} слов.",
        "en": "Too short — need at least {min_words} words.",
    },
    "LESSON_APPLY_CHECKING": {
        "ru": "Проверяю ответ…",
        "en": "Checking your answer…",
    },
    "LESSON_APPLY_PASSED": {"ru": "✅ {feedback}", "en": "✅ {feedback}"},
    "LESSON_APPLY_FAILED": {
        "ru": "💡 {feedback}\n\nВариант:\n{corrected}",
        "en": "💡 {feedback}\n\nSuggested:\n{corrected}",
    },
    "LESSON_APPLY_AI_UNAVAILABLE": {
        "ru": "Записала ответ. AI-проверка временно недоступна — попробуем позже.",
        "en": "Answer saved. AI check temporarily unavailable — we'll try later.",
    },
    # --- Diagnostic ---
    "BTN_DIAGNOSTIC_START": {
        "ru": "📊 Пройти диагностику",
        "en": "📊 Start diagnostic",
    },
    "DIAG_INTRO": {
        "ru": (
            "Диагностика из 12 вопросов — определим сильные и слабые навыки.\n"
            "Grammar, Vocabulary, Reading, Listening, Writing, Speaking."
        ),
        "en": (
            "12-question diagnostic — we'll find your strong and weak skills.\n"
            "Grammar, Vocabulary, Reading, Listening, Writing, Speaking."
        ),
    },
    "DIAG_QUESTION": {
        "ru": "Вопрос {n} из {total}",
        "en": "Question {n} of {total}",
    },
    "DIAG_CORRECT": {"ru": "✅ Верно!", "en": "✅ Correct!"},
    "DIAG_WRONG": {
        "ru": "❌ Правильный ответ: {answer}",
        "en": "❌ Correct answer: {answer}",
    },
    "DIAG_RESULT": {
        "ru": "Готово! Твой профиль навыков:\n\n{profile}",
        "en": "Done! Your skill profile:\n\n{profile}",
    },
    "DIAG_NOT_PREMIUM": {
        "ru": "Диагностика доступна в Premium. /premium",
        "en": "Diagnostic is available in Premium. /premium",
    },
    "DIAG_SETUP_REQUIRED": {
        "ru": "Сначала настрой программу: /premium",
        "en": "Set up your program first: /premium",
    },
    "DIAG_ALREADY_DONE": {
        "ru": "Диагностика уже пройдена. Повтор будет позже.",
        "en": "Diagnostic already completed. Retake will be available later.",
    },
    "DIAG_UNAVAILABLE": {
        "ru": "Диагностика сейчас недоступна.",
        "en": "Diagnostic is unavailable now.",
    },
    "DIAG_EXPIRED": {
        "ru": "Диагностика прервалась. Начни заново: /premium",
        "en": "Diagnostic interrupted. Start again: /premium",
    },
    "DIAG_AFTER_SETUP": {
        "ru": "Можно сразу пройти диагностику — так точнее подберём программу.",
        "en": "You can take the diagnostic now — it helps tailor your program.",
    },
    "DIAG_AFTER_SETUP_LESSON": {
        "ru": (
            "Диагностику можно пройти позже в /premium. "
            "Когда будешь готов(а) — нажми «Урок дня»."
        ),
        "en": (
            "You can take the diagnostic later in /premium. "
            "When ready — tap «Today's lesson»."
        ),
    },
    "DIAG_YOUR_ANSWER": {
        "ru": "Твой ответ: {answer}",
        "en": "Your answer: {answer}",
    },
    # --- Premium setup ---
    "BTN_PREMIUM_SETUP": {
        "ru": "📋 Настроить программу",
        "en": "📋 Set up program",
    },
    "BTN_PREMIUM_SKIP": {"ru": "Пропустить", "en": "Skip"},
    "PREMIUM_SETUP_INTRO": {
        "ru": (
            "Настроим программу под тебя.\n"
            "Отвечай по одному шагу — можно вернуться позже через /premium."
        ),
        "en": (
            "Let's set up your program.\n"
            "One step at a time — you can return later via /premium."
        ),
    },
    "PREMIUM_SETUP_PROFESSION": {
        "ru": (
            "Кем ты работаешь или чем занимаешься?\n"
            "Напиши текстом или нажми «Пропустить»."
        ),
        "en": (
            "What do you do for work or study?\n"
            "Type your answer or tap «Skip»."
        ),
    },
    "PREMIUM_SETUP_PROFESSION_TOO_LONG": {
        "ru": "Слишком длинно — до 120 символов.",
        "en": "Too long — max 120 characters.",
    },
    "PREMIUM_SETUP_SAVED_PROFESSION": {
        "ru": "Записала: {value}",
        "en": "Saved: {value}",
    },
    "PREMIUM_SETUP_MINUTES": {
        "ru": "Сколько минут в день готов(а) заниматься?",
        "en": "How many minutes per day can you study?",
    },
    "BTN_PREMIUM_MINUTES": {
        "ru": {"5": "5 минут", "10": "10 минут", "15": "15 минут", "20": "20 минут"},
        "en": {"5": "5 minutes", "10": "10 minutes", "15": "15 minutes", "20": "20 minutes"},
    },
    "PREMIUM_SETUP_EXAM_TYPE": {
        "ru": "К какому экзамену готовишься?",
        "en": "Which exam are you preparing for?",
    },
    "BTN_EXAM_TYPES": {
        "ru": {"toefl": "TOEFL", "det": "Duolingo English Test", "other": "Другой"},
        "en": {"toefl": "TOEFL", "det": "Duolingo English Test", "other": "Other"},
    },
    "PREMIUM_SETUP_EXAM_DATE": {
        "ru": (
            "Когда экзамен?\n"
            "Напиши дату или месяц (например: декабрь 2026) — или «Пропустить»."
        ),
        "en": (
            "When is the exam?\n"
            "Type a date or month (e.g. December 2026) — or tap «Skip»."
        ),
    },
    "PREMIUM_SETUP_EXAM_DATE_TOO_LONG": {
        "ru": "Слишком длинно — до 80 символов.",
        "en": "Too long — max 80 characters.",
    },
    "PREMIUM_SETUP_SAVED_EXAM_DATE": {
        "ru": "Дата экзамена: {value}",
        "en": "Exam date: {value}",
    },
    "PREMIUM_SETUP_WEAK_SKILL": {
        "ru": "Какой навык хочешь прокачать в первую очередь?",
        "en": "Which skill do you want to improve first?",
    },
    "BTN_WEAK_SKILLS": {
        "ru": {
            "grammar": "Грамматика",
            "vocabulary": "Лексика",
            "reading": "Чтение",
            "listening": "Аудирование",
            "writing": "Письмо",
            "speaking": "Говорение",
        },
        "en": {
            "grammar": "Grammar",
            "vocabulary": "Vocabulary",
            "reading": "Reading",
            "listening": "Listening",
            "writing": "Writing",
            "speaking": "Speaking",
        },
    },
    "PREMIUM_SETUP_INTERESTS": {
        "ru": "Что тебе интересно? (для подбора примеров)",
        "en": "What interests you? (for example selection)",
    },
    "BTN_PREMIUM_INTERESTS": {
        "ru": {
            "movies": "Фильмы и сериалы",
            "books": "Книги",
            "tech": "Технологии",
            "travel": "Путешествия",
            "psychology": "Психология",
            "news": "Новости",
            "daily": "Повседневная жизнь",
        },
        "en": {
            "movies": "Movies & TV",
            "books": "Books",
            "tech": "Technology",
            "travel": "Travel",
            "psychology": "Psychology",
            "news": "News",
            "daily": "Daily life",
        },
    },
    "PREMIUM_SETUP_DONE": {
        "ru": (
            "✅ Программа настроена!\n\n"
            "Цель: {goal}\n"
            "Время в день: {minutes} мин\n\n"
            "Ежедневные уроки подключим на следующем этапе."
        ),
        "en": (
            "✅ Program set up!\n\n"
            "Goal: {goal}\n"
            "Time per day: {minutes} min\n\n"
            "Daily lessons will be enabled in the next stage."
        ),
    },
    "PREMIUM_SETUP_NOT_PREMIUM": {
        "ru": "Premium не активен. Подробнее: /premium",
        "en": "Premium is not active. Details: /premium",
    },
    "PREMIUM_SETUP_ALREADY": {
        "ru": "Профиль уже настроен. Изменить цель и уровень: /settings",
        "en": "Profile already set up. Change goal and level: /settings",
    },
    "PREMIUM_SETUP_EXPIRED": {
        "ru": "Настройка прервалась. Начни заново: /premium",
        "en": "Setup interrupted. Start again: /premium",
    },
    "PREMIUM_SETUP_USE_BUTTONS": {
        "ru": "На этом шаге выбери вариант кнопкой или напиши текст, если бот просит.",
        "en": "On this step, choose with a button or type text if the bot asks.",
    },
    "PREMIUM_EXPIRED": {
        "ru": (
            "Срок Premium истёк — снова действуют бесплатные лимиты.\n"
            "Продлить: /premium"
        ),
        "en": (
            "Premium expired — free limits apply again.\n"
            "Renew: /premium"
        ),
    },
}
