"""Отчёт о прогрессе Premium-программы."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from bot.repositories.curriculum_repo import CurriculumRepository
from bot.repositories.learning_item_repo import LearningItemRepository
from bot.repositories.learning_profile_repo import LearningProfileRepository
from bot.repositories.progress_repo import ProgressRepository
from bot.services.curriculum_service import CurriculumService
from bot.services.diagnostic_service import SKILLS, format_skill_profile
from bot.services.profile_service import profile_service
from bot.services.subscription import is_premium

logger = logging.getLogger(__name__)


@dataclass
class PremiumProgressReport:
    goal: str
    goal_label: str
    cefr_level: str
    daily_minutes: int
    module_title: str | None = None
    module_status: str | None = None
    lessons_completed: int = 0
    lessons_total: int = 0
    current_lesson_title: str | None = None
    weak_skill: str | None = None
    skills: dict[str, str] = field(default_factory=dict)
    srs_due: int = 0
    srs_mastered: int = 0
    srs_learning: int = 0
    exercise_correct: int = 0
    exercise_total: int = 0
    apply_passed: int = 0
    apply_total: int = 0
    setup_required: bool = False


class ProgressReportService:
    def __init__(self):
        self._profiles = LearningProfileRepository()
        self._progress = ProgressRepository()
        self._curriculum = CurriculumRepository()
        self._catalog = CurriculumService()
        self._items = LearningItemRepository()

    def build_report(self, user_id: int) -> PremiumProgressReport | None:
        if not is_premium(user_id):
            return None

        profile = self._profiles.get(user_id) or {}
        goal = profile.get("goal") or "self"
        from bot import texts

        report = PremiumProgressReport(
            goal=goal,
            goal_label=texts.BTN_GOALS.get(goal, goal),
            cefr_level=profile.get("cefr_level") or "A1",
            daily_minutes=int(profile.get("daily_minutes") or 15),
            weak_skill=profile.get("weak_skill"),
            setup_required=profile_service.needs_premium_setup(user_id),
        )

        if report.setup_required:
            return report

        skills_row = self._profiles.get_skill_profile(user_id)
        if skills_row:
            report.skills = {k: skills_row[k] for k in SKILLS if skills_row.get(k)}

        status_counts = self._items.count_by_status(user_id)
        report.srs_due = self._items.count_due(user_id)
        report.srs_mastered = status_counts.get("mastered", 0)
        report.srs_learning = sum(
            status_counts.get(s, 0)
            for s in ("new", "learning", "weak", "active")
        )

        module = self._catalog.resolve_active_module(user_id)
        if not module:
            return report

        report.module_title = module.get("title")
        lessons = self._curriculum.list_lessons(module["id"])
        report.lessons_total = len(lessons)
        lesson_rows = self._progress.list_lesson_progress_for_module(
            user_id, module["id"]
        )
        completed_ids = {
            row["lesson_id"]
            for row in lesson_rows
            if row.get("status") == "completed"
        }
        report.lessons_completed = len(completed_ids)

        mod_progress = self._progress.get_module_progress(user_id, module["id"])
        report.module_status = (mod_progress or {}).get("status") or "not_started"

        in_progress = next(
            (row for row in lesson_rows if row.get("status") == "in_progress"),
            None,
        )
        if in_progress:
            lesson = self._curriculum.get_lesson(in_progress["lesson_id"])
            if lesson:
                report.current_lesson_title = lesson.get("title")

        for row in lesson_rows:
            if row.get("status") != "completed":
                continue
            raw = row.get("score_summary_json")
            if not raw:
                continue
            try:
                summary = json.loads(raw)
            except json.JSONDecodeError:
                continue
            report.exercise_correct += int(summary.get("exercise_correct") or 0)
            report.exercise_total += int(summary.get("exercise_total") or 0)
            report.apply_passed += int(summary.get("apply_passed") or 0)
            report.apply_total += int(summary.get("apply_total") or 0)

        return report

    def format_block(self, user_id: int) -> str | None:
        report = self.build_report(user_id)
        if not report:
            return None

        from bot import texts

        if report.setup_required:
            return texts.PREMIUM_PROGRESS_SETUP

        lines = [
            texts.PREMIUM_PROGRESS_HEADER,
            texts.PREMIUM_PROGRESS_PROGRAM.format(
                goal=report.goal_label,
                level=report.cefr_level,
                minutes=report.daily_minutes,
            ),
        ]

        if report.module_title:
            status_label = texts.PREMIUM_MODULE_STATUS.get(
                report.module_status or "", report.module_status or "—"
            )
            lines.append(
                texts.PREMIUM_PROGRESS_MODULE.format(
                    module=report.module_title,
                    completed=report.lessons_completed,
                    total=report.lessons_total,
                    status=status_label,
                )
            )
            if report.current_lesson_title:
                lines.append(
                    texts.PREMIUM_PROGRESS_CURRENT_LESSON.format(
                        lesson=report.current_lesson_title
                    )
                )

        if report.skills:
            lines.append(
                texts.PREMIUM_PROGRESS_SKILLS.format(
                    profile=format_skill_profile(report.skills)
                )
            )
        elif not report.setup_required:
            lines.append(texts.PREMIUM_PROGRESS_NO_DIAG)

        lines.append(
            texts.PREMIUM_PROGRESS_SRS.format(
                due=report.srs_due,
                learning=report.srs_learning,
                mastered=report.srs_mastered,
            )
        )

        if report.exercise_total or report.apply_total:
            lines.append(
                texts.PREMIUM_PROGRESS_SCORES.format(
                    ex_correct=report.exercise_correct,
                    ex_total=report.exercise_total,
                    apply_passed=report.apply_passed,
                    apply_total=report.apply_total,
                )
            )

        if report.weak_skill:
            skill_label = texts.DIAG_SKILL_LABELS.get(
                report.weak_skill, report.weak_skill
            )
            lines.append(
                texts.PREMIUM_PROGRESS_WEAK_SKILL.format(skill=skill_label)
            )

        return "\n".join(lines)


progress_report_service = ProgressReportService()
