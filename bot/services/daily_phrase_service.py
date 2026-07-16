"""Фраза дня из curriculum Premium-программы."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import pytz
from datetime import datetime

from bot.repositories.curriculum_repo import CurriculumRepository
from bot.repositories.daily_phrase_repo import DailyPhraseRepository
from bot.repositories.learning_profile_repo import LearningProfileRepository
from bot.services.curriculum_service import CurriculumService
from bot.services.profile_service import profile_service
from bot.services.subscription import is_premium
from database.db import get_premium_users_for_daily_phrase

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DailyPhrase:
    phrase_id: str
    phrase_en: str
    phrase_ru: str
    module_id: int
    module_title: str
    lesson_title: str
    day_number: int


class DailyPhraseService:
    def __init__(self):
        self._log = DailyPhraseRepository()
        self._curriculum = CurriculumRepository()
        self._catalog = CurriculumService()

    def can_receive(self, user_id: int) -> bool:
        if not is_premium(user_id):
            return False
        if profile_service.needs_premium_setup(user_id):
            return False
        profile = LearningProfileRepository().get(user_id)
        return bool(profile and profile.get("premium_setup_done"))

    @staticmethod
    def today_for_timezone(timezone: str) -> str:
        tz = pytz.timezone(timezone or "Europe/Moscow")
        return datetime.now(tz).date().isoformat()

    @staticmethod
    def now_hm_for_timezone(timezone: str) -> str:
        tz = pytz.timezone(timezone or "Europe/Moscow")
        return datetime.now(tz).strftime("%H:%M")

    def get_phrase(self, user_id: int, phrase_date: str | None = None) -> DailyPhrase | None:
        if not self.can_receive(user_id):
            return None

        user_tz = self._user_timezone(user_id)
        phrase_date = phrase_date or self.today_for_timezone(user_tz)

        logged = self._log.get_log(user_id, phrase_date)
        if logged:
            return self._load_from_log(logged)

        phrase = self._pick_phrase(user_id)
        if phrase:
            self._log.log_phrase(
                user_id,
                phrase_date,
                phrase.phrase_id,
                phrase.module_id,
            )
        return phrase

    def get_users_due_for_push(self) -> list[dict]:
        due: list[dict] = []
        for user in get_premium_users_for_daily_phrase():
            tz = user.get("timezone") or "Europe/Moscow"
            today = self.today_for_timezone(tz)
            if not user.get("reminder_enabled"):
                continue
            if self.now_hm_for_timezone(tz) != user.get("reminder_time", "19:00"):
                continue
            if self._log.was_sent_today(user["user_id"], today):
                continue
            due.append({**user, "phrase_date": today})
        return due

    def _pick_phrase(self, user_id: int) -> DailyPhrase | None:
        module = self._catalog.resolve_active_module(user_id)
        if not module:
            return None

        lesson = self._pick_next_lesson(user_id, module["id"])
        if not lesson:
            return self._last_lesson_phrase(module)

        payload = self._phrase_payload_from_steps_raw(lesson["id"])
        if not payload:
            return self._last_lesson_phrase(module)
        return DailyPhrase(
            phrase_id=payload.get("phrase_id") or f"lesson_{lesson['id']}",
            phrase_en=payload.get("phrase_en", ""),
            phrase_ru=payload.get("phrase_ru", ""),
            module_id=module["id"],
            module_title=module.get("title", ""),
            lesson_title=lesson.get("title", ""),
            day_number=lesson.get("day_number") or 0,
        )

    def _pick_next_lesson(self, user_id: int, module_id: int) -> dict | None:
        from bot.repositories.progress_repo import ProgressRepository

        progress = ProgressRepository()
        lessons = self._curriculum.list_lessons(module_id)
        completed_ids = {
            row["lesson_id"]
            for row in progress.list_lesson_progress_for_module(user_id, module_id)
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

    def _load_from_log(self, logged: dict) -> DailyPhrase | None:
        module_id = logged.get("module_id")
        phrase_id = logged.get("phrase_id")
        if not module_id or not phrase_id:
            return None
        payload = self._find_phrase_in_module(module_id, phrase_id)
        if not payload:
            return None
        module = self._curriculum.get_module(module_id) or {}
        return DailyPhrase(
            phrase_id=phrase_id,
            phrase_en=payload.get("phrase_en", ""),
            phrase_ru=payload.get("phrase_ru", ""),
            module_id=module_id,
            module_title=module.get("title", ""),
            lesson_title=payload.get("lesson_title", ""),
            day_number=int(payload.get("day_number") or 0),
        )

    def _last_lesson_phrase(self, module: dict) -> DailyPhrase | None:
        lessons = self._curriculum.list_lessons(module["id"])
        if not lessons:
            return None
        lesson = lessons[-1]
        payload = self._phrase_payload_from_steps_raw(lesson["id"])
        if not payload:
            return None
        return DailyPhrase(
            phrase_id=payload.get("phrase_id") or f"lesson_{lesson['id']}",
            phrase_en=payload.get("phrase_en", ""),
            phrase_ru=payload.get("phrase_ru", ""),
            module_id=module["id"],
            module_title=module.get("title", ""),
            lesson_title=lesson.get("title", ""),
            day_number=lesson.get("day_number") or 0,
        )

    def _find_phrase_in_module(self, module_id: int, phrase_id: str) -> dict | None:
        for lesson in self._curriculum.list_lessons(module_id):
            for step in self._curriculum.list_steps(lesson["id"]):
                if step.get("step_type") != "phrase":
                    continue
                payload = step.get("payload") or {}
                if payload.get("phrase_id") == phrase_id:
                    return {
                        **payload,
                        "lesson_title": lesson.get("title", ""),
                        "day_number": lesson.get("day_number") or 0,
                    }
        return None

    @staticmethod
    def _phrase_payload_from_steps(steps) -> dict | None:
        for step in steps:
            step_type = getattr(step, "step_type", step.get("step_type") if isinstance(step, dict) else None)
            payload = getattr(step, "payload", None) if not isinstance(step, dict) else step.get("payload")
            if step_type == "phrase":
                return payload or {}
        return None

    def _phrase_payload_from_steps_raw(self, lesson_id: int) -> dict | None:
        for step in self._curriculum.list_steps(lesson_id):
            if step.get("step_type") == "phrase":
                return step.get("payload") or {}
        return None

    @staticmethod
    def _user_timezone(user_id: int) -> str:
        from database.db import get_user

        user = get_user(user_id) or {}
        return user.get("timezone") or "Europe/Moscow"

    @staticmethod
    def format_message(phrase: DailyPhrase) -> str:
        from bot import texts

        return texts.DAILY_PHRASE_MESSAGE.format(
            phrase_en=phrase.phrase_en,
            phrase_ru=phrase.phrase_ru,
            module=phrase.module_title,
            lesson=phrase.lesson_title,
            day=phrase.day_number,
        )


daily_phrase_service = DailyPhraseService()
