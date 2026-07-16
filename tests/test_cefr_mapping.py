import pytest

from bot.domain.levels import (
    core_target_ratio,
    display_level_to_cefr,
    is_mvp_cefr,
)


def test_display_level_to_cefr():
    assert display_level_to_cefr("beginner") == "A1"
    assert display_level_to_cefr("intermediate") == "A2"
    assert display_level_to_cefr("advanced") == "B1"
    assert display_level_to_cefr("unknown") == "A1"
    assert display_level_to_cefr(None) == "A1"


def test_core_target_ratio():
    assert core_target_ratio("beginner") == (0.7, 0.3)
    assert core_target_ratio("intermediate") == (0.5, 0.5)
    assert core_target_ratio("advanced") == (0.3, 0.7)
    assert sum(core_target_ratio("beginner")) == pytest.approx(1.0)


def test_is_mvp_cefr():
    assert is_mvp_cefr("A1")
    assert is_mvp_cefr("B1")
    assert not is_mvp_cefr("B2")
