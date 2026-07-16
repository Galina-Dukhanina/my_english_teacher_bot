"""Дневные лимиты бесплатного тарифа."""

from dataclasses import dataclass

from config import (
    FREE_LIMIT_MESSAGES,
    FREE_LIMIT_WORDS_SESSIONS,
    FREE_LIMIT_GRAMMAR_EXERCISES,
)
from bot.i18n import t
from bot.services.subscription import is_premium
from database.db import get_user_local_date, get_usage_limits, increment_usage

ACTION_MESSAGES = "messages"
ACTION_WORDS_SESSION = "words_session"
ACTION_GRAMMAR_EXERCISE = "grammar_exercise"

_LIMITS = {
    ACTION_MESSAGES: ("messages_used", FREE_LIMIT_MESSAGES),
    ACTION_WORDS_SESSION: ("words_sessions_used", FREE_LIMIT_WORDS_SESSIONS),
    ACTION_GRAMMAR_EXERCISE: (
        "grammar_exercises_used",
        FREE_LIMIT_GRAMMAR_EXERCISES,
    ),
}


@dataclass
class LimitResult:
    allowed: bool
    action: str
    used: int
    limit: int


def check_and_consume(user_id: int, action: str) -> LimitResult:
    """Проверить лимит и списать одну единицу, если разрешено."""
    if is_premium(user_id):
        field, limit = _LIMITS.get(action, ("messages_used", 999999))
        date_str = get_user_local_date(user_id)
        usage = get_usage_limits(user_id, date_str)
        used = usage.get(field, 0)
        return LimitResult(allowed=True, action=action, used=used, limit=limit)

    mapping = _LIMITS.get(action)
    if not mapping:
        return LimitResult(allowed=True, action=action, used=0, limit=0)

    field, limit = mapping
    date_str = get_user_local_date(user_id)
    usage = get_usage_limits(user_id, date_str)
    used = usage.get(field, 0) or 0

    if used >= limit:
        return LimitResult(allowed=False, action=action, used=used, limit=limit)

    increment_usage(user_id, date_str, field)
    return LimitResult(allowed=True, action=action, used=used + 1, limit=limit)


def get_limit_message(result: LimitResult, user_id: int | None = None) -> str:
    """Текст upsell при исчерпанном лимите."""
    templates = {
        ACTION_MESSAGES: "LIMIT_MESSAGES",
        ACTION_WORDS_SESSION: "LIMIT_WORDS",
        ACTION_GRAMMAR_EXERCISE: "LIMIT_GRAMMAR",
    }
    key = templates.get(result.action, "LIMIT_GENERIC")
    return t(key, user_id=user_id, used=result.used, limit=result.limit)


def format_daily_limits_block(user_id: int) -> str:
    """Блок дневных лимитов для /progress."""
    if is_premium(user_id):
        return (
            f"{t('PROGRESS_LIMITS_SEPARATOR', user_id=user_id)}\n\n"
            f"{t('PROGRESS_LIMITS_PREMIUM', user_id=user_id)}"
        )

    date_str = get_user_local_date(user_id)
    usage = get_usage_limits(user_id, date_str)

    lines = [
        t("PROGRESS_LIMITS_SEPARATOR", user_id=user_id),
        "",
        t("PROGRESS_LIMITS_HEADER", user_id=user_id),
        t(
            "PROGRESS_LIMIT_MESSAGES",
            user_id=user_id,
            used=usage.get("messages_used") or 0,
            limit=FREE_LIMIT_MESSAGES,
        ),
        t(
            "PROGRESS_LIMIT_WORDS",
            user_id=user_id,
            used=usage.get("words_sessions_used") or 0,
            limit=FREE_LIMIT_WORDS_SESSIONS,
        ),
        t(
            "PROGRESS_LIMIT_GRAMMAR",
            user_id=user_id,
            used=usage.get("grammar_exercises_used") or 0,
            limit=FREE_LIMIT_GRAMMAR_EXERCISES,
        ),
        "",
        t("PROGRESS_LIMITS_SEPARATOR", user_id=user_id),
        t("PROGRESS_LIMITS_FOOTNOTE", user_id=user_id),
    ]
    return "\n".join(lines)
