"""Прогресс пользователя и вызов на дни без пропусков."""

from datetime import datetime

import pytz

from database.db import (
    count_challenge_active_days,
    get_progress,
    get_user,
    get_vocab_stats,
    count_words_to_review,
    update_progress,
    sync_progress_words,
)
from bot.services.challenge import format_challenge_line, mark_active_today
from bot.services.limits import format_daily_limits_block

ACTIVITY_DIALOG = "dialog"
ACTIVITY_TOOL = "tool"
ACTIVITY_WORDS = "words_session"
ACTIVITY_REVIEW = "review_session"
ACTIVITY_GRAMMAR = "grammar"
ACTIVITY_MENU = "activity"


def _today_in_tz(timezone: str) -> str:
    tz = pytz.timezone(timezone or "Europe/Moscow")
    return datetime.now(tz).date().isoformat()


def record_activity(user_id: int, activity_type: str):
    """Обновить счётчики и отметить активный день вызова."""
    user = get_user(user_id)
    if not user:
        return

    tz = user.get("timezone") or "Europe/Moscow"
    today = _today_in_tz(tz)

    progress = get_progress(user_id) or {}
    updates = {"last_active": today}

    # streak_days = активные дни в текущем вызове (для напоминаний и совместимости)
    if user.get("challenge_days") and user.get("challenge_start"):
        mark_active_today(user_id)
        updates["streak_days"] = count_challenge_active_days(
            user_id, user["challenge_start"], today
        )

    if activity_type == ACTIVITY_DIALOG:
        updates["total_messages"] = (progress.get("total_messages") or 0) + 1
    elif activity_type in (ACTIVITY_WORDS, ACTIVITY_REVIEW, ACTIVITY_GRAMMAR, ACTIVITY_MENU):
        updates["total_dialogs"] = (progress.get("total_dialogs") or 0) + 1
    elif activity_type == ACTIVITY_TOOL:
        pass  # только last_active и день вызова

    update_progress(user_id, **updates)

    if activity_type in (ACTIVITY_WORDS, ACTIVITY_REVIEW):
        sync_progress_words(user_id)


def get_progress_summary(user_id: int) -> dict:
    """Сводка для команды /progress."""
    user = get_user(user_id)
    if not user:
        return {}

    progress = get_progress(user_id) or {}
    vocab = get_vocab_stats(user_id)

    return {
        "streak_days": progress.get("streak_days") or 0,
        "new_words": vocab.get("total") or 0,
        "mastered_words": vocab.get("learned") or 0,
        "to_review": count_words_to_review(user_id),
        "has_challenge": bool(user.get("challenge_days") and user.get("challenge_start")),
    }


def format_progress_text(user_id: int) -> str:
    """Форматированный блок прогресса."""
    from bot import texts
    from bot.services.progress_report_service import progress_report_service

    summary = get_progress_summary(user_id)
    challenge_line = format_challenge_line(user_id)
    if challenge_line:
        streak_block = challenge_line
    elif summary.get("has_challenge"):
        streak_block = "🎯 Вызов: данные обновляются..."
    else:
        streak_block = texts.CHALLENGE_NONE

    base = texts.PROGRESS.format(
        streak_block=streak_block,
        new_words=summary.get("new_words", 0),
        mastered_words=summary.get("mastered_words", 0),
        to_review=summary.get("to_review", 0),
        limits_block=format_daily_limits_block(user_id),
    )

    premium_block = progress_report_service.format_block(user_id)
    if premium_block:
        return f"{base}\n\n{texts.PROGRESS_LIMITS_SEPARATOR}\n\n{premium_block}"
    return base


def format_welcome_back(user_id: int) -> str:
    """Приветствие при /start с блоком прогресса."""
    from bot import texts

    return f"{texts.WELCOME_BACK}\n\n{format_progress_text(user_id)}"


def streak_label(days: int) -> str:
    """Склонение «день / дня / дней»."""
    n = abs(days) % 100
    n1 = n % 10
    if 11 <= n <= 14:
        return "дней"
    if n1 == 1:
        return "день"
    if 2 <= n1 <= 4:
        return "дня"
    return "дней"
