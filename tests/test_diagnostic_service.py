from bot.services.diagnostic_service import (
    QUESTIONS,
    build_skill_profile,
    score_skill_level,
)


def test_question_count():
    assert len(QUESTIONS) == 12
    skills = {q.skill for q in QUESTIONS}
    assert skills == {
        "grammar",
        "vocabulary",
        "reading",
        "listening",
        "writing",
        "speaking",
    }


def test_score_skill_level():
    assert score_skill_level(0, 3) == "A1"
    assert score_skill_level(1, 3) == "A2"
    assert score_skill_level(3, 3) == "B1"


def test_build_skill_profile_all_correct():
    answers = [True] * len(QUESTIONS)
    profile = build_skill_profile(answers)
    assert all(level == "B1" for level in profile.values())


def test_build_skill_profile_all_wrong():
    answers = [False] * len(QUESTIONS)
    profile = build_skill_profile(answers)
    assert all(level == "A1" for level in profile.values())
