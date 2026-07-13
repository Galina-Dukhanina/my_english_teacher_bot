"""Отправка напоминаний пользователям."""

import logging
from datetime import datetime

import pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot import texts
from bot.services.challenge import get_challenge_status
from database.db import (
    get_progress,
    get_users_for_reminders,
    reminder_sent_today,
    record_reminder_sent,
    update_user,
)

logger = logging.getLogger(__name__)


def _today_in_tz(timezone: str) -> str:
    tz = pytz.timezone(timezone or "Europe/Moscow")
    return datetime.now(tz).date().isoformat()


def _now_hm_in_tz(timezone: str) -> str:
    tz = pytz.timezone(timezone or "Europe/Moscow")
    return datetime.now(tz).strftime("%H:%M")


def get_users_due_for_reminder() -> list[dict]:
    """Пользователи, которым пора отправить напоминание прямо сейчас."""
    due = []
    for user in get_users_for_reminders():
        tz = user.get("timezone") or "Europe/Moscow"
        today = _today_in_tz(tz)
        if _now_hm_in_tz(tz) != user.get("reminder_time", "19:00"):
            continue

        progress = get_progress(user["user_id"])
        if progress and progress.get("last_active") == today:
            continue

        if reminder_sent_today(user["user_id"], today):
            continue

        due.append(user)
    return due


def build_reminder_text(user_id: int) -> str:
    status = get_challenge_status(user_id)
    if status.get("status") == "active" and status.get("active_days", 0) > 0:
        return texts.REMINDER_STREAK.format(
            active=status["active_days"],
            goal=status["goal_days"],
        )
    return texts.REMINDER_DEFAULT


def reminder_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(texts.BTN_REMINDER_OFF, callback_data="reminder:off")]]
    )


async def send_reminders(app) -> int:
    """Отправить напоминания всем, кому пора. Возвращает число отправленных."""
    sent = 0
    for user in get_users_due_for_reminder():
        user_id = user["user_id"]
        tz = user.get("timezone") or "Europe/Moscow"
        today = _today_in_tz(tz)
        try:
            await app.bot.send_message(
                chat_id=user_id,
                text=build_reminder_text(user_id),
                reply_markup=reminder_keyboard(),
            )
            record_reminder_sent(user_id)
            sent += 1
        except Exception as e:
            logger.error(f"Не удалось отправить напоминание user {user_id}: {e}")
    return sent


async def handle_reminder_off(update, context):
    """Inline-кнопка «Отключить» под напоминанием."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    update_user(user_id, reminder_enabled=0)
    try:
        await query.edit_message_text(texts.REMINDER_DISABLED)
    except Exception:
        pass
