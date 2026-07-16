from bot.domain.lesson import is_ai_step, is_deferred_step


def test_deferred_steps():
    assert is_deferred_step("listen")
    assert is_deferred_step("voice")
    assert not is_deferred_step("exercise")


def test_ai_steps():
    assert is_ai_step("apply")
    assert is_ai_step("voice")
    assert not is_ai_step("phrase")


def test_curriculum_roundtrip(curriculum_repo):
    module_id = curriculum_repo.insert_module(
        {
            "goal": "work",
            "cefr_level": "A1",
            "title": "Test module",
            "outcome_ru": "Тест",
        }
    )
    lesson_id = curriculum_repo.insert_lesson(
        {
            "module_id": module_id,
            "day_number": 1,
            "title": "Day 1",
        }
    )
    curriculum_repo.insert_step(
        {
            "lesson_id": lesson_id,
            "sort_order": 1,
            "step_type": "phrase",
            "payload": {"phrase_en": "Hello"},
        }
    )

    modules = curriculum_repo.find_modules(goal="work", cefr_level="A1")
    assert len(modules) == 1
    steps = curriculum_repo.list_steps(lesson_id)
    assert len(steps) == 1
    assert steps[0]["step_type"] == "phrase"
    assert steps[0]["payload"]["phrase_en"] == "Hello"


def test_learning_profile_upsert(profile_repo):
    profile_repo.upsert_from_user(
        42,
        cefr_level="A1",
        display_level="beginner",
        goal="work",
        ui_language="ru",
    )
    profile = profile_repo.get(42)
    assert profile["cefr_level"] == "A1"
    assert profile["ui_language"] == "ru"

    profile_repo.update_fields(42, profession="designer", premium_setup_done=1)
    profile = profile_repo.get(42)
    assert profile["profession"] == "designer"
    assert profile["premium_setup_done"] == 1
