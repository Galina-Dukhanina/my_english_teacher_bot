"""Статус подписки (задел под Этап 5 — монетизация)."""

from datetime import datetime

from database.db import get_user


def is_premium(user_id: int) -> bool:
    """True, если у пользователя активный premium."""
    user = get_user(user_id)
    if not user or not user.get("is_premium"):
        return False
    until = user.get("premium_until")
    if not until:
        return True
    try:
        return datetime.fromisoformat(until) > datetime.now()
    except ValueError:
        return bool(user.get("is_premium"))
