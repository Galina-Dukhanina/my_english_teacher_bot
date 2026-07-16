"""Фраза дня — ручной запрос и callback."""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot import texts
from bot.handlers.premium_lesson import premium_lesson_keyboard
from bot.services.daily_phrase_service import daily_phrase_service
from database.db import log_event

logger = logging.getLogger(__name__)


def _phrase_keyboard(user_id: int) -> InlineKeyboardMarkup | None:
    lesson_kb = premium_lesson_keyboard(user_id)
    if lesson_kb:
        return lesson_kb
    return None


async def send_daily_phrase(message, user_id: int) -> bool:
    phrase = daily_phrase_service.get_phrase(user_id)
    if not phrase:
        await message.reply_text(texts.DAILY_PHRASE_UNAVAILABLE)
        return False
    await message.reply_text(
        daily_phrase_service.format_message(phrase),
        reply_markup=_phrase_keyboard(user_id),
    )
    log_event(user_id, "daily_phrase_manual")
    return True


async def handle_phrase_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action = query.data.split(":")[1]

    if action != "today":
        return

    phrase = daily_phrase_service.get_phrase(user_id)
    if not phrase:
        await query.message.reply_text(texts.DAILY_PHRASE_UNAVAILABLE)
        return

    await query.message.reply_text(
        daily_phrase_service.format_message(phrase),
        reply_markup=_phrase_keyboard(user_id),
    )
    log_event(user_id, "daily_phrase_manual")


def premium_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    rows = []
    lesson_kb = premium_lesson_keyboard(user_id)
    if lesson_kb:
        rows.extend(lesson_kb.inline_keyboard)
    rows.append(
        [InlineKeyboardButton(texts.BTN_DAILY_PHRASE, callback_data="phrase:today")]
    )
    return InlineKeyboardMarkup(rows)
