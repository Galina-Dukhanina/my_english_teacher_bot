"""Тесты domain и репозиториев Premium."""

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ["DB_PATH"] = str(ROOT / "tests" / "tmp_test.db")


@pytest.fixture(autouse=True)
def clean_db():
    db_path = Path(os.environ["DB_PATH"])
    if db_path.exists():
        db_path.unlink()
    from database.db import init_db, migrate_db

    init_db()
    migrate_db()
    yield
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def curriculum_repo():
    from bot.repositories.curriculum_repo import CurriculumRepository

    return CurriculumRepository()


@pytest.fixture
def profile_repo():
    from bot.repositories.learning_profile_repo import LearningProfileRepository

    return LearningProfileRepository()
