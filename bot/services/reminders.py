"""Отправка напоминаний пользователям."""

import logging
import re
from datetime import datetime

import pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot import texts, keyboards
from bot.services.challenge import get_challenge_status
from database.db import (
    get_progress,
    get_user,
    get_users_for_reminders,
    log_event,
    reminder_sent_today,
    record_reminder_sent,
    set_pending_action,
    update_user,
)

logger = logging.getLogger(__name__)

CUSTOM_TIME_KEY = "custom"
_TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")


def parse_reminder_time(text: str) -> str | None:
    """Распознать время HH:MM или H:MM, вернуть нормализованное HH:MM."""
    match = _TIME_RE.match(text.strip())
    if not match:
        return None
    hours, minutes = int(match.group(1)), int(match.group(2))
    if hours > 23 or minutes > 59:
        return None
    return f"{hours:02d}:{minutes:02d}"


def reminder_time_label(value: str) -> str:
    return texts.BTN_TIMES.get(value, value)


def reminder_time_keyboard(prefix: str = "remtime") -> InlineKeyboardMarkup:
    presets = [
        (value, label)
        for value, label in texts.BTN_TIMES.items()
        if value != CUSTOM_TIME_KEY
    ]
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(label, callback_data=f"{prefix}:{value}")
                for value, label in presets
            ],
            [
                InlineKeyboardButton(
                    texts.BTN_TIMES[CUSTOM_TIME_KEY],
                    callback_data=f"{prefix}:{CUSTOM_TIME_KEY}",
                )
            ],
        ]
    )


async def prompt_custom_reminder_time(message, user_id: int):
    set_pending_action(user_id, "wait_reminder_time")
    await message.reply_text(texts.ASK_CUSTOM_TIME)


async def submit_custom_reminder_time(update, context, user_id: int, text: str):
    parsed = parse_reminder_time(text)
    if not parsed:
        await update.message.reply_text(texts.INVALID_CUSTOM_TIME)
        return

    user = get_user(user_id)
    fields = {
        "reminder_time": parsed,
        "reminder_enabled": 1,
    }
    if user.get("onboarding_step") == "time" and not user["onboarding_done"]:
        fields["onboarding_step"] = "streakgoal"
    update_user(user_id, **fields)
    set_pending_action(user_id, None)
    log_event(user_id, "reminder_time_custom")

    await update.message.reply_text(
        texts.REMINDER_TIME_SAVED.format(time=parsed),
        reply_markup=keyboards.main_keyboard(user_id),
    )

    if fields.get("onboarding_step") == "streakgoal":
        from bot.services.challenge import challenge_goal_keyboard

        await update.message.reply_text(
            texts.ASK_CHALLENGE,
            reply_markup=challenge_goal_keyboard(user_id),
        )


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
