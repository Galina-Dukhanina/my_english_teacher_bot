import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.db import get_user, set_activity, log_event
from bot import texts, keyboards, grammar_topics
from bot.services.ai import explain_grammar_topic, generate_grammar_exercises

logger = logging.getLogger(__name__)

# Сессии упражнений в памяти
_exercise_sessions = {}


async def start_grammar(source, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Запуск режима грамматики — показываем каталог тем по уровню."""
    set_activity(user_id, "grammar")
    message = source.message if hasattr(source, "message") else source

    user = get_user(user_id)
    level = user["level"] or "unknown"
    topics = grammar_topics.get_topics_for_level(level)

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"gtopic:{code}")]
        for code, name in topics.items()
    ]
    await message.reply_text(
        texts.GRAMMAR_CHOOSE_TOPIC,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_grammar_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбрана тема — генерируем объяснение через AI."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    _, topic_code = query.data.split(":", 1)
    await _explain_topic(query, user_id, topic_code)


async def _explain_topic(query, user_id, topic_code):
    """Показать объяснение темы (используется и при выборе, и при повторе)."""
    user = get_user(user_id)
    level = user["level"] or "unknown"
    topic_name = grammar_topics.get_topic_name(level, topic_code)

    # Показываем "готовлю"
    await query.edit_message_text(texts.GRAMMAR_EXPLAINING.format(topic=topic_name))

    # Генерируем объяснение
    explanation = explain_grammar_topic(
        topic=topic_name,
        level=level,
        style=user["style"],
        language=user["explanation_language"],
    )

    log_event(user_id, "grammar_topic")

    if not explanation:
        await query.message.reply_text(
            "Не получилось подготовить объяснение. Попробуй другую тему.",
            reply_markup=keyboards.main_keyboard(),
        )
        return

    # Отправляем объяснение + меню "что дальше"
    from bot.handlers.dialog import _strip_markdown

    clean = _strip_markdown(explanation)
    await query.message.reply_text(clean)

    # Меню после объяснения
    keyboard = [
        [InlineKeyboardButton(texts.BTN_GRAMMAR_ANOTHER, callback_data="gnav:another")],
        [
            InlineKeyboardButton(
                texts.BTN_GRAMMAR_EXERCISE, callback_data=f"gnav:exercise:{topic_code}"
            )
        ],
        [InlineKeyboardButton(texts.BTN_GRAMMAR_EXIT, callback_data="gnav:exit")],
    ]
    await query.message.reply_text(
        texts.GRAMMAR_AFTER_EXPLANATION,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_grammar_nav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Навигация после объяснения: другая тема / упражнения / выход."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    parts = query.data.split(":")
    action = parts[1]

    if action == "another":
        # Показываем каталог снова
        await start_grammar(query, context, user_id)

    elif action == "exercise":
        topic_code = parts[2] if len(parts) > 2 else None
        await start_exercises(query, context, user_id, topic_code)

    elif action == "exit":
        set_activity(user_id, None)
        await query.edit_message_text(texts.GRAMMAR_EXIT)
    elif action == "menu":
        set_activity(user_id, None)
        from bot.handlers.activities import show_activity_menu

        class _Wrap:
            def __init__(self, msg):
                self.message = msg

        await show_activity_menu(_Wrap(query.message), context)


async def start_exercises(source, context, user_id, topic_code):
    """Запуск упражнений по теме."""
    message = source.message if hasattr(source, "message") else source
    user = get_user(user_id)
    level = user["level"] or "unknown"
    topic_name = grammar_topics.get_topic_name(level, topic_code)

    await message.reply_text(texts.GRAMMAR_EX_GENERATING.format(topic=topic_name))

    exercises = generate_grammar_exercises(topic_name, level, count=5)
    if not exercises:
        await message.reply_text(
            texts.GRAMMAR_EX_ERROR, reply_markup=keyboards.main_keyboard()
        )
        return

    log_event(user_id, "grammar_exercise")
    _exercise_sessions[user_id] = {
        "exercises": exercises,
        "index": 0,
        "correct": 0,
        "topic_code": topic_code,
        "topic_name": topic_name,
    }
    await _show_exercise(message, user_id)


async def _show_exercise(message, user_id):
    """Показать текущее упражнение."""
    session = _exercise_sessions.get(user_id)
    if not session:
        return

    index = session["index"]
    exercises = session["exercises"]

    if index >= len(exercises):
        await _finish_exercises(message, user_id)
        return

    ex = exercises[index]
    sentence = ex.get("sentence", "?")
    options = ex.get("options", [])
    correct = ex.get("correct", "")

    import random

    shuffled = options[:]
    random.shuffle(shuffled)

    keyboard = [
        [
            InlineKeyboardButton(
                opt, callback_data=f"gex:{'1' if opt == correct else '0'}:{opt}"
            )
        ]
        for opt in shuffled
    ]
    keyboard.append(
        [InlineKeyboardButton(texts.BTN_GRAMMAR_STOP, callback_data="gexstop:1")]
    )
    intro = texts.GRAMMAR_EX_INTRO.format(
        topic=session["topic_name"], num=index + 1, total=len(exercises)
    )
    await message.reply_text(
        f"{intro}\n\n{sentence}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_exercise_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа на упражнение."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    parts = query.data.split(":", 2)
    is_correct = parts[1] == "1"

    session = _exercise_sessions.get(user_id)
    if not session:
        await query.message.reply_text(
            "Упражнения прерваны. Начни заново через «Грамматика».",
            reply_markup=keyboards.main_keyboard(),
        )
        return

    ex = session["exercises"][session["index"]]
    explanation = ex.get("explanation", "")
    correct = ex.get("correct", "")

    if is_correct:
        session["correct"] += 1
        feedback = texts.GRAMMAR_EX_CORRECT.format(explanation=explanation)
    else:
        feedback = texts.GRAMMAR_EX_WRONG.format(
            correct=correct, explanation=explanation
        )
    try:
        await query.edit_message_text(feedback)
    except Exception:
        pass

    session["index"] += 1
    _exercise_sessions[user_id] = session
    await _show_exercise(query.message, user_id)


async def _finish_exercises(message, user_id):
    """Итог упражнений + меню."""
    session = _exercise_sessions.get(user_id, {})
    total = len(session.get("exercises", []))
    correct = session.get("correct", 0)
    topic_code = session.get("topic_code")

    _exercise_sessions.pop(user_id, None)

    keyboard = [
        [
            InlineKeyboardButton(
                texts.BTN_GRAMMAR_REPEAT, callback_data=f"greexplain:{topic_code}"
            )
        ],
        [InlineKeyboardButton(texts.BTN_GRAMMAR_ANOTHER, callback_data="gnav:another")],
        [InlineKeyboardButton(texts.BTN_GRAMMAR_MENU, callback_data="gnav:menu")],
    ]
    await message.reply_text(
        texts.GRAMMAR_EX_DONE.format(correct=correct, total=total),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_grammar_reexplain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Повторить тему — показать объяснение заново."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    _, topic_code = query.data.split(":", 1)
    await _explain_topic(query, user_id, topic_code)


async def handle_exercise_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Досрочное завершение упражнений."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    try:
        await query.edit_message_text("Упражнения завершены.")
    except Exception:
        pass
    await _finish_exercises(query.message, user_id)
