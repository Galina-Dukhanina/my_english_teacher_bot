"""Premium-профиль обучения: setup и синхронизация с users."""

import json
import logging

from bot.domain.levels import display_level_to_cefr
from bot.repositories.learning_profile_repo import LearningProfileRepository
from bot.services.session_store import clear_session, get_session, save_session
from bot.services.subscription import is_premium
from database.db import get_user, log_event

logger = logging.getLogger(__name__)

KIND_PREMIUM_SETUP = "premium_setup"

STEP_PROFESSION = "profession"
STEP_DAILY_MINUTES = "daily_minutes"
STEP_EXAM_TYPE = "exam_type"
STEP_EXAM_DATE = "exam_date"
STEP_WEAK_SKILL = "weak_skill"
STEP_INTERESTS = "interests"

SETUP_STEPS_BY_GOAL: dict[str, tuple[str, ...]] = {
    "work": (STEP_PROFESSION, STEP_DAILY_MINUTES),
    "travel": (STEP_PROFESSION, STEP_DAILY_MINUTES),
    "speaking": (STEP_PROFESSION, STEP_DAILY_MINUTES),
    "exams": (
        STEP_PROFESSION,
        STEP_DAILY_MINUTES,
        STEP_EXAM_TYPE,
        STEP_EXAM_DATE,
        STEP_WEAK_SKILL,
    ),
    "self": (STEP_PROFESSION, STEP_DAILY_MINUTES, STEP_INTERESTS),
}


class ProfileService:
    def __init__(self):
        self._repo = LearningProfileRepository()

    def needs_premium_setup(self, user_id: int) -> bool:
        if not is_premium(user_id):
            return False
        profile = self._repo.get(user_id)
        if not profile:
            return True
        return not profile.get("premium_setup_done")

    def get_profile(self, user_id: int) -> dict | None:
        return self._repo.get(user_id)

    def start_setup(self, user_id: int) -> str:
        user = get_user(user_id)
        if not user:
            raise ValueError("user not found")
        goal = user.get("goal") or "self"
        steps = SETUP_STEPS_BY_GOAL.get(goal, SETUP_STEPS_BY_GOAL["self"])
        save_session(
            user_id,
            KIND_PREMIUM_SETUP,
            {"step_index": 0, "steps": list(steps), "answers": {}},
        )
        log_event(user_id, "premium_setup_start")
        return steps[0]

    def get_setup_session(self, user_id: int) -> dict | None:
        return get_session(user_id, KIND_PREMIUM_SETUP)

    def current_step(self, session: dict) -> str | None:
        steps = session.get("steps") or []
        index = session.get("step_index", 0)
        if index >= len(steps):
            return None
        return steps[index]

    def save_answer(self, user_id: int, session: dict, key: str, value) -> str | None:
        answers = session.setdefault("answers", {})
        answers[key] = value
        session["step_index"] = session.get("step_index", 0) + 1
        save_session(user_id, KIND_PREMIUM_SETUP, session)
        return self.current_step(session)

    def complete_setup(self, user_id: int, session: dict) -> dict:
        user = get_user(user_id)
        if not user:
            raise ValueError("user not found")

        answers = session.get("answers") or {}
        display_level = user.get("level")
        cefr = display_level_to_cefr(display_level)
        goal = user.get("goal")

        self._repo.upsert_from_user(
            user_id,
            cefr_level=cefr,
            display_level=display_level,
            goal=goal,
            ui_language=(user.get("ui_language") or "ru"),
        )

        fields = {
            "profession": answers.get("profession"),
            "daily_minutes": answers.get("daily_minutes"),
            "exam_type": answers.get("exam_type"),
            "exam_date": answers.get("exam_date"),
            "weak_skill": answers.get("weak_skill"),
            "premium_setup_done": 1,
        }
        interests = answers.get("interests")
        if interests:
            fields["interests_json"] = json.dumps(
                interests if isinstance(interests, list) else [interests],
                ensure_ascii=False,
            )

        self._repo.update_fields(user_id, **fields)
        clear_session(user_id, KIND_PREMIUM_SETUP)
        log_event(user_id, "premium_setup_done")
        return self._repo.get(user_id) or {}

    def cancel_setup(self, user_id: int):
        clear_session(user_id, KIND_PREMIUM_SETUP)


profile_service = ProfileService()
