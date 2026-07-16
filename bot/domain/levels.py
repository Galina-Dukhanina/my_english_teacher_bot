"""CEFR, цели обучения и соотношение core/target контента."""

from enum import StrEnum

MVP_CEFR_LEVELS = frozenset({"A1", "A2", "B1"})


class CEFRLevel(StrEnum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"


class DisplayLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LearningGoal(StrEnum):
    WORK = "work"
    TRAVEL = "travel"
    EXAMS = "exams"
    SPEAKING = "speaking"
    SELF = "self"


DISPLAY_TO_CEFR: dict[str, CEFRLevel] = {
    DisplayLevel.BEGINNER: CEFRLevel.A1,
    DisplayLevel.INTERMEDIATE: CEFRLevel.A2,
    DisplayLevel.ADVANCED: CEFRLevel.B1,
}

CORE_TARGET_RATIO: dict[str, tuple[float, float]] = {
    DisplayLevel.BEGINNER: (0.7, 0.3),
    DisplayLevel.INTERMEDIATE: (0.5, 0.5),
    DisplayLevel.ADVANCED: (0.3, 0.7),
}


def display_level_to_cefr(level: str | None) -> str:
    """UI-уровень → стартовый CEFR для MVP."""
    if not level or level == "unknown":
        return CEFRLevel.A1
    mapped = DISPLAY_TO_CEFR.get(level)
    if mapped:
        return mapped.value
    return CEFRLevel.A1


def core_target_ratio(display_level: str | None) -> tuple[float, float]:
    """Доля языкового ядра и целевого трека (0..1, сумма = 1)."""
    if not display_level or display_level == "unknown":
        return CORE_TARGET_RATIO[DisplayLevel.BEGINNER]
    return CORE_TARGET_RATIO.get(display_level, CORE_TARGET_RATIO[DisplayLevel.BEGINNER])


def is_mvp_cefr(level: str | None) -> bool:
    return level in MVP_CEFR_LEVELS
