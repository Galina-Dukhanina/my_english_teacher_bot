"""Подбор модуля curriculum под профиль пользователя."""

from bot.domain.levels import core_target_ratio
from bot.repositories.curriculum_repo import CurriculumRepository
from bot.repositories.learning_profile_repo import LearningProfileRepository
from bot.repositories.progress_repo import ProgressRepository

CEFR_RANK = {"A1": 1, "A2": 2, "B1": 3}


class CurriculumService:
    def __init__(self):
        self._curriculum = CurriculumRepository()
        self._profiles = LearningProfileRepository()
        self._progress = ProgressRepository()

    def resolve_active_module(self, user_id: int) -> dict | None:
        profile = self._profiles.get(user_id)
        if not profile:
            return None

        goal = profile.get("goal")
        cefr = profile.get("cefr_level") or "A1"
        if not goal:
            return None

        modules = self._curriculum.find_modules(goal=goal, cefr_level=cefr)
        if not modules:
            return None

        for module in modules:
            progress = self._progress.get_module_progress(user_id, module["id"])
            if not progress or progress.get("status") != "completed":
                return module

        return modules[-1]

    def weak_skill_focus(self, user_id: int) -> str | None:
        profile = self._profiles.get(user_id)
        if profile and profile.get("weak_skill"):
            return profile["weak_skill"]

        skills = self._profiles.get_skill_profile(user_id)
        if not skills:
            return None

        skill_names = (
            "grammar",
            "vocabulary",
            "reading",
            "listening",
            "writing",
            "speaking",
        )
        weakest = None
        weakest_rank = 999
        for name in skill_names:
            level = skills.get(name)
            if not level:
                continue
            rank = CEFR_RANK.get(level, 1)
            if rank < weakest_rank:
                weakest_rank = rank
                weakest = name
        return weakest

    def module_ratios(self, user_id: int, module: dict) -> tuple[float, float]:
        profile = self._profiles.get(user_id)
        if module.get("core_ratio") is not None and module.get("target_ratio") is not None:
            return float(module["core_ratio"]), float(module["target_ratio"])
        display = profile.get("display_level") if profile else None
        return core_target_ratio(display)
