"""Учебный движок: выбор следующего урока и план шагов."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from bot.domain.lesson import is_deferred_step
from bot.repositories.curriculum_repo import CurriculumRepository
from bot.repositories.learning_profile_repo import LearningProfileRepository
from bot.repositories.progress_repo import ProgressRepository
from bot.services.curriculum_service import CurriculumService
from bot.services.premium_gate import check_program

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StepPlan:
    step_id: int
    sort_order: int
    step_type: str
    payload: dict
    deferred: bool = False
    skipped: bool = False


@dataclass
class LessonPlan:
    user_id: int
    module_id: int
    module_title: str
    lesson_id: int
    lesson_title: str
    day_number: int
    estimated_minutes: int
    core_ratio: float
    target_ratio: float
    weak_skill_focus: str | None
    is_week_check: bool
    include_review: bool
    steps: list[StepPlan] = field(default_factory=list)


class LessonEngine:
    def __init__(self):
        self._curriculum = CurriculumRepository()
        self._progress = ProgressRepository()
        self._profiles = LearningProfileRepository()
        self._catalog = CurriculumService()

    def can_access_lessons(self, user_id: int) -> tuple[bool, str]:
        access = check_program(user_id)
        if not access.allowed:
            return False, access.reason
        module = self._catalog.resolve_active_module(user_id)
        if not module:
            return False, "no_module"
        return True, "ok"

    def get_next_lesson(self, user_id: int) -> LessonPlan | None:
        allowed, reason = self.can_access_lessons(user_id)
        if not allowed:
            logger.debug("get_next_lesson blocked user=%s reason=%s", user_id, reason)
            return None

        module = self._catalog.resolve_active_module(user_id)
        if not module:
            return None

        self._progress.ensure_module_progress(user_id, module["id"])
        lesson = self._pick_next_lesson(user_id, module["id"])
        if not lesson:
            self._progress.set_module_status(user_id, module["id"], "completed")
            return None

        steps_raw = self._curriculum.list_steps(lesson["id"])
        steps = self._build_step_plans(steps_raw)
        core_ratio, target_ratio = self._catalog.module_ratios(user_id, module)
        include_review = self._progress.count_due_review_items(user_id) > 0

        return LessonPlan(
            user_id=user_id,
            module_id=module["id"],
            module_title=module["title"],
            lesson_id=lesson["id"],
            lesson_title=lesson["title"],
            day_number=lesson["day_number"],
            estimated_minutes=lesson.get("estimated_minutes") or 15,
            core_ratio=core_ratio,
            target_ratio=target_ratio,
            weak_skill_focus=self._catalog.weak_skill_focus(user_id),
            is_week_check=self._is_week_check(lesson["day_number"]),
            include_review=include_review,
            steps=steps,
        )

    def start_lesson(self, user_id: int, lesson_id: int) -> LessonPlan | None:
        plan = self.get_next_lesson(user_id)
        if not plan or plan.lesson_id != lesson_id:
            return None
        first_step = next((s for s in plan.steps if not s.skipped), None)
        self._progress.mark_lesson_started(
            user_id, lesson_id, first_step.step_id if first_step else None
        )
        return plan

    def complete_lesson(
        self,
        user_id: int,
        lesson_id: int,
        *,
        score_summary: dict | None = None,
    ) -> bool:
        module = self._catalog.resolve_active_module(user_id)
        if not module:
            return False

        summary_json = json.dumps(score_summary or {}, ensure_ascii=False)
        self._progress.mark_lesson_completed(
            user_id, lesson_id, score_summary_json=summary_json
        )

        remaining = self._pick_next_lesson(user_id, module["id"])
        if not remaining:
            self._progress.set_module_status(user_id, module["id"], "completed")
        return True

    def _pick_next_lesson(self, user_id: int, module_id: int) -> dict | None:
        lessons = self._curriculum.list_lessons(module_id)
        completed_ids = {
            row["lesson_id"]
            for row in self._progress.list_lesson_progress_for_module(user_id, module_id)
            if row.get("status") == "completed"
        }

        for lesson in lessons:
            if lesson["id"] in completed_ids:
                continue
            if not self._previous_lessons_done(lesson, lessons, completed_ids):
                continue
            return lesson
        return None

    @staticmethod
    def _previous_lessons_done(
        lesson: dict, all_lessons: list[dict], completed_ids: set[int]
    ) -> bool:
        for other in all_lessons:
            if other["day_number"] < lesson["day_number"]:
                if other["id"] not in completed_ids:
                    return False
        return True

    @staticmethod
    def _build_step_plans(steps_raw: list[dict]) -> list[StepPlan]:
        plans: list[StepPlan] = []
        for step in steps_raw:
            step_type = step["step_type"]
            deferred = is_deferred_step(step_type)
            plans.append(
                StepPlan(
                    step_id=step["id"],
                    sort_order=step["sort_order"],
                    step_type=step_type,
                    payload=step.get("payload") or {},
                    deferred=deferred,
                    skipped=deferred,
                )
            )
        return plans

    @staticmethod
    def _is_week_check(day_number: int) -> bool:
        return day_number > 0 and day_number % 7 == 0


lesson_engine = LessonEngine()
