import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def seeded_work_module(monkeypatch):
    db_path = ROOT / "tests" / "tmp_lesson_engine.db"
    if db_path.exists():
        db_path.unlink()
    monkeypatch.setenv("DB_PATH", str(db_path))

    from database.db import init_db, migrate_db, create_user, update_user
    from bot.repositories.curriculum_repo import CurriculumRepository
    from bot.repositories.learning_profile_repo import LearningProfileRepository

    init_db()
    migrate_db()

    create_user(1, "u", "User")
    update_user(1, onboarding_done=1, goal="work", level="beginner", is_premium=1)

    repo = LearningProfileRepository()
    repo.upsert_from_user(
        1, cefr_level="A1", display_level="beginner", goal="work", ui_language="ru"
    )
    repo.update_fields(1, premium_setup_done=1, daily_minutes=15)

    content = json.loads(
        (ROOT / "content" / "dev" / "work_a1_module.json").read_text(encoding="utf-8")
    )
    cur = CurriculumRepository()
    module_id = cur.insert_module(content["module"])
    for lesson in content["lessons"]:
        steps = lesson.pop("steps")
        lesson_id = cur.insert_lesson(
            {
                "module_id": module_id,
                "day_number": lesson["day_number"],
                "title": lesson["title"],
                "estimated_minutes": lesson.get("estimated_minutes", 15),
            }
        )
        for step in steps:
            cur.insert_step(
                {
                    "lesson_id": lesson_id,
                    "sort_order": step["sort_order"],
                    "step_type": step["step_type"],
                    "payload": step.get("payload", {}),
                }
            )

    second_id = cur.insert_lesson(
        {
            "module_id": module_id,
            "day_number": 2,
            "title": "Day 2",
            "estimated_minutes": 15,
        }
    )
    cur.insert_step(
        {
            "lesson_id": second_id,
            "sort_order": 1,
            "step_type": "phrase",
            "payload": {"phrase_en": "Nice to meet you."},
        }
    )

    return module_id, second_id


def test_get_next_lesson(seeded_work_module, monkeypatch):
    monkeypatch.setattr("bot.services.lesson_engine.is_premium", lambda uid: uid == 1)

    from bot.services.lesson_engine import lesson_engine

    plan = lesson_engine.get_next_lesson(1)
    assert plan is not None
    assert plan.module_title == "Introduce yourself at work"
    assert plan.day_number == 1
    assert plan.weak_skill_focus is None
    active_steps = [s for s in plan.steps if not s.skipped]
    assert all(s.step_type not in {"listen", "voice"} for s in active_steps)
    assert any(s.skipped and s.step_type == "listen" for s in plan.steps)


def test_lesson_prerequisite(seeded_work_module, monkeypatch):
    monkeypatch.setattr("bot.services.lesson_engine.is_premium", lambda uid: uid == 1)

    from bot.services.lesson_engine import lesson_engine

    _, second_id = seeded_work_module
    blocked = lesson_engine.start_lesson(1, second_id)
    assert blocked is None

    first = lesson_engine.get_next_lesson(1)
    assert first is not None
    lesson_engine.complete_lesson(1, first.lesson_id)

    next_plan = lesson_engine.get_next_lesson(1)
    assert next_plan is not None
    assert next_plan.day_number == 2


def test_module_completed_after_all_lessons(seeded_work_module, monkeypatch):
    monkeypatch.setattr("bot.services.lesson_engine.is_premium", lambda uid: uid == 1)

    from bot.repositories.progress_repo import ProgressRepository
    from bot.services.lesson_engine import lesson_engine

    while True:
        plan = lesson_engine.get_next_lesson(1)
        if not plan:
            break
        lesson_engine.complete_lesson(1, plan.lesson_id)

    progress = ProgressRepository().get_module_progress(1, seeded_work_module[0])
    assert progress["status"] == "completed"
