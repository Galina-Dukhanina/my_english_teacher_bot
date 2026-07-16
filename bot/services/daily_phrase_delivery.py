"""Доставка фразы дня через scheduler."""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot import texts
from bot.handlers.premium_lesson import premium_lesson_keyboard
from bot.services.daily_phrase_service import daily_phrase_service
from database.db import log_event

logger = logging.getLogger(__name__)


def daily_phrase_keyboard(user_id: int) -> InlineKeyboardMarkup | None:
    lesson_kb = premium_lesson_keyboard(user_id)
    if lesson_kb:
        return lesson_kb
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(texts.BTN_DAILY_PHRASE, callback_data="phrase:today")]]
    )


async def send_daily_phrases(app) -> int:
    sent = 0
    for user in daily_phrase_service.get_users_due_for_push():
        user_id = user["user_id"]
        phrase_date = user["phrase_date"]
        try:
            phrase = daily_phrase_service.get_phrase(user_id, phrase_date)
            if not phrase:
                continue
            await app.bot.send_message(
                chat_id=user_id,
                text=daily_phrase_service.format_message(phrase),
                reply_markup=daily_phrase_keyboard(user_id),
            )
            log_event(user_id, "daily_phrase_push")
            sent += 1
        except Exception as exc:
            logger.error("Daily phrase push failed user=%s: %s", user_id, exc)
    return sent
