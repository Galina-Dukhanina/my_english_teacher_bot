"""Прогресс и streak (задел под Этап 6 — удержание)."""

from database.db import get_user


def record_activity(user_id: int, activity_type: str):
    """Отметить активность пользователя. Реализация — в Этапе 6."""
    del user_id, activity_type


def get_progress_summary(user_id: int) -> dict:
    """Сводка прогресса для /progress. Реализация — в Этапе 6."""
    user = get_user(user_id)
    if not user:
        return {}
    return {
        "streak_days": 0,
        "new_words": 0,
        "mastered_words": 0,
        "total_messages": 0,
    }
