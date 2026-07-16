"""Tests for UI i18n layer."""

from bot.i18n import t, td, set_ui_language, resolve_toolbar_action, get_ui_language


def test_t_russian_default():
    assert "Чем займемся?" in t("BTN_MENU", lang="ru")
    assert "What shall we do?" in t("BTN_MENU", lang="en")


def test_td_goals():
    goals_en = td("BTN_GOALS", lang="en")
    assert goals_en["work"] == "Work"
    goals_ru = td("BTN_GOALS", lang="ru")
    assert goals_ru["work"] == "Работа"


def test_toolbar_match_both_languages():
    assert resolve_toolbar_action("Чем займемся?") == "menu"
    assert resolve_toolbar_action("What shall we do?") == "menu"
    assert resolve_toolbar_action("Hello") is None


def test_set_ui_language_persists(tmp_path, monkeypatch):
    db_path = tmp_path / "i18n_test.db"
    monkeypatch.setenv("DB_PATH", str(db_path))

    from database.db import init_db, migrate_db, get_user, create_user, update_user

    init_db()
    migrate_db()
    create_user(42, "test", "Test")
    update_user(42, onboarding_done=1)
    set_ui_language(42, "en")
    user = get_user(42)
    assert user["ui_language"] == "en"
    assert get_ui_language(42) == "en"
