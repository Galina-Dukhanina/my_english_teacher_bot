"""Доступ к данным Premium-обучения."""

from bot.repositories.content_asset_repo import ContentAssetRepository
from bot.repositories.curriculum_repo import CurriculumRepository
from bot.repositories.learning_item_repo import LearningItemRepository
from bot.repositories.learning_profile_repo import LearningProfileRepository
from bot.repositories.progress_repo import ProgressRepository

__all__ = [
    "ContentAssetRepository",
    "CurriculumRepository",
    "LearningItemRepository",
    "LearningProfileRepository",
    "ProgressRepository",
]
