import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.db import get_user, set_activity, log_event
from bot import texts, keyboards, grammar_topics
from bot.services.ai import explain_grammar_topic

logger = logging.getLogger(__name__)


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
        # Заглушка упражнений (Этап 4B)
        await query.message.reply_text(
            texts.GRAMMAR_EXERCISE_SOON,
            reply_markup=keyboards.main_keyboard(),
        )

    elif action == "exit":
        set_activity(user_id, None)
        await query.edit_message_text(texts.GRAMMAR_EXIT)
