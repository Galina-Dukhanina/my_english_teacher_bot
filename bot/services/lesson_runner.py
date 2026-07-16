"""Запуск и прохождение Premium-урока (без Telegram)."""

from __future__ import annotations

import logging

from bot.repositories.progress_repo import ProgressRepository
from bot.services.lesson_engine import LessonPlan, StepPlan, lesson_engine
from bot.services.review_engine import review_engine
from bot.services.session_store import clear_session, get_session, save_session

logger = logging.getLogger(__name__)

KIND_LESSON = "lesson"


def _active_steps(plan: LessonPlan) -> list[StepPlan]:
    return [s for s in plan.steps if not s.skipped]


def _step_to_dict(step: StepPlan) -> dict:
    return {
        "step_id": step.step_id,
        "sort_order": step.sort_order,
        "step_type": step.step_type,
        "payload": step.payload,
    }


class LessonRunner:
    def __init__(self):
        self._progress = ProgressRepository()

    def has_active_session(self, user_id: int) -> bool:
        return get_session(user_id, KIND_LESSON) is not None

    def get_session(self, user_id: int) -> dict | None:
        return get_session(user_id, KIND_LESSON)

    def can_offer_lesson(self, user_id: int) -> tuple[bool, str]:
        if self.has_active_session(user_id):
            return True, "resume"
        allowed, reason = lesson_engine.can_access_lessons(user_id)
        if not allowed:
            return False, reason
        if lesson_engine.get_next_lesson(user_id):
            return True, "start"
        return False, "no_lesson"

    def begin_next_lesson(self, user_id: int) -> dict | None:
        plan = lesson_engine.get_next_lesson(user_id)
        if not plan:
            return None
        lesson_engine.start_lesson(user_id, plan.lesson_id)
        session = self._plan_to_session(plan)
        save_session(user_id, KIND_LESSON, session)
        return session

    def resume_lesson(self, user_id: int) -> dict | None:
        session = get_session(user_id, KIND_LESSON)
        if session:
            return session
        return self._restore_from_progress(user_id)

    def current_step(self, session: dict) -> dict | None:
        steps = session.get("steps") or []
        index = session.get("step_index", 0)
        if index >= len(steps):
            return None
        return steps[index]

    def advance(self, user_id: int, session: dict) -> dict | None:
        session["step_index"] = session.get("step_index", 0) + 1
        step = self.current_step(session)
        if step:
            self._progress.mark_lesson_started(
                user_id, session["lesson_id"], step["step_id"]
            )
        save_session(user_id, KIND_LESSON, session)
        return session

    def record_exercise_result(
        self, user_id: int, session: dict, *, correct: bool
    ) -> dict:
        scores = session.setdefault("scores", {"exercise_correct": 0, "exercise_total": 0})
        scores["exercise_total"] = scores.get("exercise_total", 0) + 1
        if correct:
            scores["exercise_correct"] = scores.get("exercise_correct", 0) + 1
        else:
            module_id = session.get("module_id")
            if module_id:
                review_engine.register_exercise_miss(user_id, module_id, session)
        return session

    def on_step_completed(self, user_id: int, session: dict, step: dict) -> dict:
        step_type = step.get("step_type")
        module_id = session.get("module_id")
        if step_type == "phrase" and module_id:
            review_engine.register_phrase(
                user_id, module_id, step.get("payload") or {}
            )
        return session

    def record_review_response(
        self, user_id: int, session: dict, item_id: int, result_code: str
    ) -> dict | None:
        from bot.domain.review import ReviewResult

        mapping = {
            "0": ReviewResult.INCORRECT,
            "1": ReviewResult.CORRECT,
            "2": ReviewResult.CORRECT_WITH_HINT,
        }
        result = mapping.get(result_code)
        if result is None:
            return None
        return review_engine.submit_review(user_id, item_id, result)

    def advance_review(self, user_id: int, session: dict) -> dict:
        step = self.current_step(session)
        if not step or step.get("step_type") != "review":
            return session

        payload = step.setdefault("payload", {})
        items = payload.get("items") or []
        payload["index"] = payload.get("index", 0) + 1
        if payload["index"] >= len(items):
            return self.advance(user_id, session)
        save_session(user_id, KIND_LESSON, session)
        return session

    def finish_lesson(self, user_id: int, session: dict) -> dict:
        scores = session.get("scores") or {}
        summary = {
            "exercise_correct": scores.get("exercise_correct", 0),
            "exercise_total": scores.get("exercise_total", 0),
            "lesson_id": session.get("lesson_id"),
            "module_id": session.get("module_id"),
        }
        lesson_engine.complete_lesson(
            user_id,
            session["lesson_id"],
            score_summary=summary,
        )
        clear_session(user_id, KIND_LESSON)
        return summary

    def cancel_lesson(self, user_id: int):
        clear_session(user_id, KIND_LESSON)

    def _plan_to_session(self, plan: LessonPlan) -> dict:
        steps = [_step_to_dict(s) for s in _active_steps(plan)]
        review_items = review_engine.get_due_batch(plan.user_id) if plan.include_review else []
        if review_items:
            steps.insert(
                0,
                {
                    "step_id": 0,
                    "sort_order": 0,
                    "step_type": "review",
                    "payload": {"items": review_items, "index": 0},
                },
            )
        return {
            "user_id": plan.user_id,
            "lesson_id": plan.lesson_id,
            "module_id": plan.module_id,
            "module_title": plan.module_title,
            "lesson_title": plan.lesson_title,
            "day_number": plan.day_number,
            "estimated_minutes": plan.estimated_minutes,
            "is_week_check": plan.is_week_check,
            "weak_skill_focus": plan.weak_skill_focus,
            "step_index": 0,
            "steps": steps,
            "scores": {"exercise_correct": 0, "exercise_total": 0},
            "awaiting_text": False,
        }

    def _restore_from_progress(self, user_id: int) -> dict | None:
        allowed, _ = lesson_engine.can_access_lessons(user_id)
        if not allowed:
            return None

        from bot.services.curriculum_service import CurriculumService

        module = CurriculumService().resolve_active_module(user_id)
        if not module:
            return None

        rows = self._progress.list_lesson_progress_for_module(user_id, module["id"])
        in_progress = next((r for r in rows if r.get("status") == "in_progress"), None)
        if not in_progress:
            return None

        plan = lesson_engine.get_next_lesson(user_id)
        if not plan or plan.lesson_id != in_progress["lesson_id"]:
            return None

        session = self._plan_to_session(plan)
        step_id = in_progress.get("current_step_id")
        if step_id:
            for i, step in enumerate(session["steps"]):
                if step["step_id"] == step_id:
                    session["step_index"] = i
                    break
        save_session(user_id, KIND_LESSON, session)
        return session


lesson_runner = LessonRunner()
