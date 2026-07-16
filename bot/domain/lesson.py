"""Типы шагов ежедневного урока."""

from enum import StrEnum

# Шаги, реализация которых отложена (этапы 13–14).
DEFERRED_STEP_TYPES = frozenset({"listen", "voice"})

# Шаги, где нужен DeepSeek (этап 8+).
AI_STEP_TYPES = frozenset({"apply", "voice"})


class LessonStepType(StrEnum):
    REVIEW = "review"
    PHRASE = "phrase"
    EXPLAIN = "explain"
    EXERCISE = "exercise"
    APPLY = "apply"
    FEEDBACK = "feedback"
    LISTEN = "listen"
    VOICE = "voice"


def is_deferred_step(step_type: str) -> bool:
    return step_type in DEFERRED_STEP_TYPES


def is_ai_step(step_type: str) -> bool:
    return step_type in AI_STEP_TYPES
