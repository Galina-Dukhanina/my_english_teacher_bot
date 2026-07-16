from bot.services.profile_service import SETUP_STEPS_BY_GOAL, ProfileService


def test_setup_steps_by_goal():
    assert SETUP_STEPS_BY_GOAL["work"] == ("profession", "daily_minutes")
    assert "exam_type" in SETUP_STEPS_BY_GOAL["exams"]
    assert "interests" in SETUP_STEPS_BY_GOAL["self"]


def test_complete_setup_writes_profile(profile_repo, monkeypatch):
    from database.db import create_user, update_user

    create_user(99, "tester", "Test")
    update_user(
        99,
        onboarding_done=1,
        level="beginner",
        goal="work",
        is_premium=1,
    )

    monkeypatch.setattr(
        "bot.services.profile_service.is_premium",
        lambda user_id: user_id == 99,
    )

    service = ProfileService()
    service.start_setup(99)
    session = service.get_setup_session(99)
    service.save_answer(99, session, "profession", "Designer")
    session = service.get_setup_session(99)
    service.save_answer(99, session, "daily_minutes", 15)
    session = service.get_setup_session(99)

    profile = service.complete_setup(99, session)
    assert profile["premium_setup_done"] == 1
    assert profile["cefr_level"] == "A1"
    assert profile["profession"] == "Designer"
    assert profile["daily_minutes"] == 15
    assert service.needs_premium_setup(99) is False
