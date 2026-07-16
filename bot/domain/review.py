"""Интервальное повторение (SRS) — чистая логика без БД."""

from dataclasses import dataclass
from enum import StrEnum


class LearningItemStatus(StrEnum):
    NEW = "new"
    LEARNING = "learning"
    WEAK = "weak"
    ACTIVE = "active"
    MASTERED = "mastered"


class ReviewResult(StrEnum):
    CORRECT = "correct"
    CORRECT_WITH_HINT = "correct_with_hint"
    INCORRECT = "incorrect"


MIN_INTERVAL_DAYS = 1
MAX_INTERVAL_DAYS = 60
MASTERED_STREAK = 3


@dataclass(frozen=True)
class ReviewState:
    status: str
    interval_days: int
    correct_streak: int
    error_count: int


def initial_interval_days() -> int:
    return MIN_INTERVAL_DAYS


def apply_review(state: ReviewState, result: ReviewResult) -> ReviewState:
    """Обновить статус и интервал после попытки."""
    status = state.status
    interval = max(state.interval_days, MIN_INTERVAL_DAYS)
    streak = state.correct_streak
    errors = state.error_count

    if result == ReviewResult.INCORRECT:
        errors += 1
        streak = 0
        status = LearningItemStatus.WEAK
        interval = MIN_INTERVAL_DAYS
    elif result == ReviewResult.CORRECT_WITH_HINT:
        streak += 1
        errors = max(0, errors - 1)
        status = _promote(status, streak, mastered=False)
        interval = min(max(interval, MIN_INTERVAL_DAYS) + 1, MAX_INTERVAL_DAYS)
    else:
        streak += 1
        errors = max(0, errors - 1)
        mastered = streak >= MASTERED_STREAK and status != LearningItemStatus.NEW
        status = _promote(status, streak, mastered=mastered)
        if mastered:
            interval = MAX_INTERVAL_DAYS
        else:
            interval = min(max(interval * 2, MIN_INTERVAL_DAYS + 1), MAX_INTERVAL_DAYS)

    return ReviewState(
        status=status,
        interval_days=interval,
        correct_streak=streak,
        error_count=errors,
    )


def _promote(status: str, streak: int, *, mastered: bool) -> str:
    if mastered:
        return LearningItemStatus.MASTERED
    if status == LearningItemStatus.NEW:
        return LearningItemStatus.LEARNING
    if status == LearningItemStatus.WEAK and streak >= 2:
        return LearningItemStatus.ACTIVE
    if streak >= 2:
        return LearningItemStatus.ACTIVE
    return status
