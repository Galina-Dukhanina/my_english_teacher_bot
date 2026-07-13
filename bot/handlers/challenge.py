"""Выбор и обновление вызова на дни без пропусков."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot import texts
from bot.services.challenge import (
    VALID_CHALLENGE_DAYS,
    challenge_goal_keyboard,
    format_completion_message,
    start_challenge,
    try_finalize_challenge,
)
from database.db import get_user, log_event, update_user

logger = logging.getLogger(__name__)


async def maybe_send_challenge_completion(
    update: Update, user_id: int
) -> bool:
    """Если вызов завершён — отправить итог и кнопки нового вызова."""
    completion = try_finalize_challenge(user_id)
    if not completion:
        return False

    message = update.message or update.callback_query.message
    await message.reply_text(
        format_completion_message(completion),
        reply_markup=challenge_goal_keyboard(),
    )
    return True


async def handle_streak_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор 5 / 7 / 14 / 30 дней — онбординг или новый вызов."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    _, value = query.data.split(":", 1)
    try:
        days = int(value)
    except ValueError:
        return
    if days not in VALID_CHALLENGE_DAYS:
        return

    user = get_user(user_id)
    start_challenge(user_id, days)
    label = texts.BTN_CHALLENGE_DAYS.get(str(days), f"{days} дней")

    if user and not user.get("onboarding_done") and user.get("onboarding_step") == "streakgoal":
        update_user(user_id, onboarding_step="done", onboarding_done=1)
        log_event(user_id, "onboarding_done")
        await query.edit_message_text(f"{texts.ASK_CHALLENGE}\n\n✅ {label}")
        from bot.keyboards import main_keyboard

        await query.message.reply_text(
            texts.ONBOARDING_DONE,
            reply_markup=main_keyboard(),
        )
        return

    log_event(user_id, "challenge_started")
    text = texts.CHALLENGE_STARTED.format(days=days, label=label)
    try:
        await query.edit_message_text(text)
    except Exception:
        await query.message.reply_text(text)
