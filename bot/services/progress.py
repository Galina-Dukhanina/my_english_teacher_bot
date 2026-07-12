"""Прогресс пользователя и streak."""

from datetime import datetime, timedelta

import pytz

from database.db import (
    get_progress,
    get_user,
    get_vocab_stats,
    count_words_to_review,
    update_progress,
    sync_progress_words,
)

ACTIVITY_DIALOG = "dialog"
ACTIVITY_WORDS = "words_session"
ACTIVITY_REVIEW = "review_session"
ACTIVITY_GRAMMAR = "grammar"
ACTIVITY_MENU = "activity"


def _today_in_tz(timezone: str) -> str:
    tz = pytz.timezone(timezone or "Europe/Moscow")
    return datetime.now(tz).date().isoformat()


def _yesterday_in_tz(timezone: str) -> str:
    tz = pytz.timezone(timezone or "Europe/Moscow")
    return (datetime.now(tz).date() - timedelta(days=1)).isoformat()


def _calc_streak(current_streak: int, last_active: str | None, today: str, yesterday: str) -> int:
    if last_active == today:
        return current_streak
    if last_active == yesterday:
        return max(current_streak, 0) + 1
    return 1


def record_activity(user_id: int, activity_type: str):
    """Обновить streak и счётчики после осмысленной активности."""
    user = get_user(user_id)
    if not user:
        return

    tz = user.get("timezone") or "Europe/Moscow"
    today = _today_in_tz(tz)
    yesterday = _yesterday_in_tz(tz)

    progress = get_progress(user_id) or {}
    streak = _calc_streak(
        progress.get("streak_days") or 0,
        progress.get("last_active"),
        today,
        yesterday,
    )

    updates = {"last_active": today, "streak_days": streak}

    if activity_type == ACTIVITY_DIALOG:
        updates["total_messages"] = (progress.get("total_messages") or 0) + 1
    elif activity_type in (ACTIVITY_WORDS, ACTIVITY_REVIEW, ACTIVITY_GRAMMAR, ACTIVITY_MENU):
        updates["total_dialogs"] = (progress.get("total_dialogs") or 0) + 1

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
        "total_messages": progress.get("total_messages") or 0,
    }


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
