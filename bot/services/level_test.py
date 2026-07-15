"""Тест на определение уровня английского."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from bot.services.subscription import is_premium
from database.db import get_user, update_user

KIND_LEVEL_TEST = "level_test"
PREMIUM_RETEST_DAYS = 30

VALID_LEVELS = ("beginner", "intermediate", "advanced")


@dataclass(frozen=True)
class LevelQuestion:
    text: str
    options: tuple[str, ...]
    correct: int
    weight: int  # 1 — beginner, 2 — intermediate, 3 — advanced


QUESTIONS: tuple[LevelQuestion, ...] = (
    LevelQuestion(
        "I ___ a student.",
        ("am", "is", "are", "be"),
        0,
        1,
    ),
    LevelQuestion(
        "She ___ to work every day.",
        ("go", "goes", "going", "went"),
        1,
        1,
    ),
    LevelQuestion(
        "If I ___ more time, I would travel.",
        ("have", "had", "have had", "will have"),
        1,
        2,
    ),
    LevelQuestion(
        "The report ___ by Friday.",
        ("will finish", "will be finished", "finished", "finishes"),
        1,
        2,
    ),
    LevelQuestion(
        "Not only ___ he apologize, but he also offered compensation.",
        ("did", "does", "do", "was"),
        0,
        3,
    ),
    LevelQuestion(
        "There ___ many people at the party last night.",
        ("was", "were", "is", "are"),
        1,
        1,
    ),
    LevelQuestion(
        "They ___ TV right now.",
        ("watch", "watches", "are watching", "watched"),
        2,
        1,
    ),
    LevelQuestion(
        "I have lived here ___ 2019.",
        ("for", "since", "from", "during"),
        1,
        2,
    ),
    LevelQuestion(
        "She suggested ___ earlier to avoid traffic.",
        ("leave", "leaving", "to leave", "left"),
        1,
        2,
    ),
    LevelQuestion(
        "Hardly ___ the door when the phone rang.",
        ("had he closed", "he had closed", "did he close", "he closed"),
        0,
        3,
    ),
)


def score_to_level(score: int) -> str:
    if score <= 4:
        return "beginner"
    if score <= 10:
        return "intermediate"
    return "advanced"


def can_take_level_test(user_id: int, *, during_onboarding: bool = False) -> tuple[bool, str]:
    """Можно ли начать тест. Возвращает (allowed, reason_code)."""
    user = get_user(user_id)
    if not user:
        return False, "no_user"

    if during_onboarding:
        if user.get("level_test_at"):
            return False, "already_tested"
        return True, "ok"

    if is_premium(user_id):
        last = user.get("level_test_at")
        if not last:
            return True, "ok"
        try:
            last_dt = datetime.fromisoformat(last)
        except ValueError:
            return True, "ok"
        if datetime.now() - last_dt >= timedelta(days=PREMIUM_RETEST_DAYS):
            return True, "ok"
        days_left = PREMIUM_RETEST_DAYS - (datetime.now() - last_dt).days
        return False, f"premium_wait:{max(days_left, 1)}"

    if user.get("level_test_at"):
        return False, "free_once"
    return True, "ok"


def days_until_retest(user_id: int) -> int | None:
    user = get_user(user_id)
    if not user or not user.get("level_test_at") or not is_premium(user_id):
        return None
    try:
        last_dt = datetime.fromisoformat(user["level_test_at"])
    except ValueError:
        return None
    left = PREMIUM_RETEST_DAYS - (datetime.now() - last_dt).days
    return max(left, 0)


def save_level_result(user_id: int, level: str):
    update_user(
        user_id,
        level=level,
        level_test_at=datetime.now().isoformat(timespec="seconds"),
    )
