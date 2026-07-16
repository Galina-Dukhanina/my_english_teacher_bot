"""Доступ к данным Premium-обучения."""

from bot.repositories.content_asset_repo import ContentAssetRepository
from bot.repositories.curriculum_repo import CurriculumRepository
from bot.repositories.learning_profile_repo import LearningProfileRepository

__all__ = [
    "ContentAssetRepository",
    "CurriculumRepository",
    "LearningProfileRepository",
]
