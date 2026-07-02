import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.db import get_user, set_activity, log_event, set_pending_action
from bot import texts

logger = logging.getLogger(__name__)


def _activity_menu_keyboard():
    """Кнопки выбора режима (inline)."""
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"activity:{code}")]
        for code, label in texts.BTN_ACTIVITIES.items()
    ]
    return InlineKeyboardMarkup(keyboard)


async def show_activity_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню 'Чем займемся?'."""
    await update.message.reply_text(
        texts.ACTIVITY_MENU,
        reply_markup=_activity_menu_keyboard(),
    )


async def handle_activity_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора режима из меню."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    _, activity = query.data.split(":", 1)

    log_event(user_id, f"activity_{activity}")

    if activity == "talk":
        set_activity(user_id, "talk")
        # Показываем темы для разговора
        keyboard = [
            [InlineKeyboardButton(label, callback_data=f"topic:{code}")]
            for code, label in texts.TALK_TOPICS.items()
        ]
        await query.edit_message_text(
            texts.TALK_START,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif activity == "words":
        from bot.handlers.cards import start_words

        # Запускаем через query.message (start_words ждет объект с reply_text)
        await query.edit_message_text("Учим слова!")
        await start_words(query, context, user_id)

    elif activity == "review":
        from bot.handlers.cards import start_review

        await query.edit_message_text("Повторяем слова!")
        await start_review(query, context, user_id)

    elif activity == "grammar":
        from bot.handlers.grammar import start_grammar

        await query.edit_message_text("Разбираем грамматику!")
        await start_grammar(query, context, user_id)


async def handle_topic_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора темы для разговора."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    _, topic = query.data.split(":", 1)

    from database.db import set_topic, set_activity, set_pending_action

    if topic == "free":
        set_pending_action(user_id, "wait_topic")
        await query.edit_message_text(texts.ASK_FREE_TOPIC)
        return

    topic_name = texts.TALK_TOPICS[topic]
    set_activity(user_id, "talk")
    set_topic(user_id, topic_name)
    await query.edit_message_text(f"Тема: {topic_name}")
    await query.message.reply_text(
        f"Давай поговорим про «{topic_name}». Начинай — напиши что-нибудь по-английски."
    )
