"""Вызов на N дней без пропусков — прогресс, завершение, тексты."""

from datetime import datetime, timedelta

import pytz

from database.db import (
    count_challenge_active_days,
    get_user,
    mark_challenge_active_day,
    update_user,
)

VALID_CHALLENGE_DAYS = (5, 7, 14, 30)


def _today_in_tz(timezone: str) -> str:
    tz = pytz.timezone(timezone or "Europe/Moscow")
    return datetime.now(tz).date().isoformat()


def _parse_date(value: str):
    return datetime.strptime(value, "%Y-%m-%d").date()


def days_label(n: int) -> str:
    """Склонение «день / дня / дней»."""
    n = abs(n) % 100
    n1 = n % 10
    if 11 <= n <= 14:
        return "дней"
    if n1 == 1:
        return "день"
    if 2 <= n1 <= 4:
        return "дня"
    return "дней"


def skip_label(n: int) -> str:
    """Склонение для «день пропуска / дня пропуска / дней пропуска»."""
    return days_label(n)


def start_challenge(user_id: int, days: int):
    """Начать новый вызов с сегодняшнего дня (в часовом поясе пользователя)."""
    if days not in VALID_CHALLENGE_DAYS:
        return
    user = get_user(user_id)
    if not user:
        return
    tz = user.get("timezone") or "Europe/Moscow"
    today = _today_in_tz(tz)
    update_user(user_id, challenge_days=days, challenge_start=today)


def mark_active_today(user_id: int):
    """Отметить сегодня как активный день в текущем вызове."""
    user = get_user(user_id)
    if not user or not user.get("challenge_days") or not user.get("challenge_start"):
        return
    tz = user.get("timezone") or "Europe/Moscow"
    today = _today_in_tz(tz)
    mark_challenge_active_day(user_id, today)


def _encouragement(missed_days: int) -> str:
    if missed_days == 0:
        return "Отлично идем! 🔥"
    if missed_days == 1:
        return "Неплохо. 👍"
    return "Еще можно успеть — продолжай! 💪"


def _completion_feedback(percent: int) -> str:
    from bot import texts

    if percent < 50:
        return texts.CHALLENGE_FEEDBACK_UNDER_50
    if percent < 70:
        return texts.CHALLENGE_FEEDBACK_50_69
    if percent < 80:
        return texts.CHALLENGE_FEEDBACK_70_79
    if percent < 90:
        return texts.CHALLENGE_FEEDBACK_80_89
    if percent < 100:
        return texts.CHALLENGE_FEEDBACK_90_99
    return texts.CHALLENGE_FEEDBACK_100


def get_challenge_status(user_id: int) -> dict:
    """Статус текущего вызова: none | active | completed."""
    user = get_user(user_id)
    if not user:
        return {"status": "none"}

    goal_days = user.get("challenge_days")
    start_str = user.get("challenge_start")
    if not goal_days or not start_str:
        return {"status": "none"}

    tz = user.get("timezone") or "Europe/Moscow"
    today = _parse_date(_today_in_tz(tz))
    start = _parse_date(start_str)
    end = start + timedelta(days=goal_days - 1)

    if today > end:
        active_days = count_challenge_active_days(user_id, start_str, end.isoformat())
        percent = min(100, round(active_days / goal_days * 100))
        return {
            "status": "completed",
            "active_days": active_days,
            "goal_days": goal_days,
            "percent": percent,
            "feedback": _completion_feedback(percent),
        }

    active_days = count_challenge_active_days(
        user_id, start_str, today.isoformat()
    )
    days_before_today = (today - start).days
    if days_before_today > 0:
        yesterday = (today - timedelta(days=1)).isoformat()
        active_before = count_challenge_active_days(user_id, start_str, yesterday)
        missed_days = max(0, days_before_today - active_before)
    else:
        missed_days = 0

    remaining_days = (end - today).days + 1

    return {
        "status": "active",
        "active_days": active_days,
        "goal_days": goal_days,
        "missed_days": missed_days,
        "remaining_days": remaining_days,
        "encouragement": _encouragement(missed_days),
    }


def try_finalize_challenge(user_id: int) -> dict | None:
    """Если период вызова закончился — вернуть итог и сбросить вызов."""
    status = get_challenge_status(user_id)
    if status.get("status") != "completed":
        return None
    update_user(user_id, challenge_days=None, challenge_start=None)
    return status


def format_challenge_line(user_id: int) -> str | None:
    """Строка прогресса вызова для /progress и welcome back."""
    status = get_challenge_status(user_id)
    if status.get("status") != "active":
        return None

    active = status["active_days"]
    goal = status["goal_days"]
    missed = status["missed_days"]
    remaining = max(0, goal - active)
    encouragement = status["encouragement"]

    if missed == 0:
        return (
            f"🎯 Активных дней: {active} из {goal}. "
            f"Осталось {remaining} {days_label(remaining)}. {encouragement}"
        )
    return (
        f"🎯 Активных дней: {active} из {goal}. "
        f"{missed} {skip_label(missed)} пропуска — "
        f"ещё нужно {remaining} {days_label(remaining)}. {encouragement}"
    )


def format_completion_message(status: dict) -> str:
    """Итог вызова с процентом и обратной связью."""
    from bot import texts

    return texts.CHALLENGE_COMPLETE.format(
        active_days=status["active_days"],
        goal_days=status["goal_days"],
        percent=status["percent"],
        feedback=status["feedback"],
    )


def challenge_goal_keyboard(user_id: int | None = None):
    """Кнопки выбора длительности вызова."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from bot.i18n import td

    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"streakgoal:{code}")]
        for code, label in td("BTN_CHALLENGE_DAYS", user_id=user_id).items()
    ]
    return InlineKeyboardMarkup(keyboard)
