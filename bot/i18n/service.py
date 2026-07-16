"""UI localization: Russian (default) and English."""

from __future__ import annotations

from bot.i18n.locales import CATALOG
from database.db import get_user, update_user

SUPPORTED = ("ru", "en")
DEFAULT_LANG = "ru"

_TOOLBAR_KEYS = {
    "BTN_MENU": "menu",
    "BTN_MAIN": "main",
    "BTN_PRONOUNCE": "pronounce",
    "BTN_MEANING": "meaning",
    "BTN_LANG": "lang",
}


def get_ui_language(user_id: int | None) -> str:
    if user_id is None:
        return DEFAULT_LANG
    user = get_user(user_id)
    if user:
        lang = user.get("ui_language")
        if lang in SUPPORTED:
            return lang
    return DEFAULT_LANG


def set_ui_language(user_id: int, lang: str) -> None:
    if lang not in SUPPORTED:
        lang = DEFAULT_LANG
    update_user(user_id, ui_language=lang)
    try:
        from bot.repositories.learning_profile_repo import LearningProfileRepository

        repo = LearningProfileRepository()
        if repo.get(user_id):
            repo.update_fields(user_id, ui_language=lang)
    except Exception:
        pass


def _fallback_text(key: str, **kwargs) -> str:
    from bot import texts

    val = getattr(texts, key, key)
    if isinstance(val, str) and kwargs:
        return val.format(**kwargs)
    return val


def t(key: str, user_id: int | None = None, lang: str | None = None, **kwargs) -> str:
    """Translate a string key for the user's UI language."""
    lang = lang or get_ui_language(user_id)
    entry = CATALOG.get(key)
    if entry is None:
        return _fallback_text(key, **kwargs)
    val = entry.get(lang) or entry.get(DEFAULT_LANG, key)
    if isinstance(val, str) and kwargs:
        return val.format(**kwargs)
    return val


def td(key: str, user_id: int | None = None, lang: str | None = None) -> dict:
    """Translate a dict of option labels (code -> label)."""
    lang = lang or get_ui_language(user_id)
    entry = CATALOG.get(key)
    if entry and isinstance(entry.get(lang), dict):
        return entry[lang]
    if entry and isinstance(entry.get(DEFAULT_LANG), dict):
        return entry[DEFAULT_LANG]
    from bot import texts

    val = getattr(texts, key, {})
    return val if isinstance(val, dict) else {}


def lang_label(lang: str) -> str:
    return t("UI_LANG_NAME_RU" if lang == "ru" else "UI_LANG_NAME_EN", lang=DEFAULT_LANG)


def all_labels(key: str) -> set[str]:
    """All localized variants of a string key (for matching keyboard buttons)."""
    entry = CATALOG.get(key)
    if not entry:
        from bot import texts

        val = getattr(texts, key, None)
        return {val} if isinstance(val, str) else set()
    labels = set()
    for lang in SUPPORTED:
        val = entry.get(lang)
        if isinstance(val, str):
            labels.add(val)
    return labels


def is_toolbar_button(text: str) -> bool:
    return resolve_toolbar_action(text) is not None


def resolve_toolbar_action(text: str) -> str | None:
    for btn_key, action in _TOOLBAR_KEYS.items():
        if text in all_labels(btn_key):
            return action
    return None
